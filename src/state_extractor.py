import ast
import re
from typing import Dict, List, Any, Set, Tuple, Optional

class ASTVisitor(ast.NodeVisitor):
    """AST Visitor to extract variable definitions (assignments) and references (uses) from a code block."""
    def __init__(self):
        self.defined_names: Set[str] = set()
        self.used_names: Set[str] = set()
        self.imported_names: Set[str] = set()
        # Root Cause B: (var_name, method_name) pairs for in-place mutations,
        # so the state table can show a mutation timeline instead of just last_modified
        self.mutations: List[Tuple[str, str]] = []

    def visit_Name(self, node: ast.Name):
        if isinstance(node.ctx, ast.Store):
            self.defined_names.add(node.id)
        elif isinstance(node.ctx, ast.Load):
            # Only count as used if it wasn't defined earlier in the same block
            if node.id not in self.defined_names and node.id not in self.imported_names:
                self.used_names.add(node.id)
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign):
        # Handle assignment target extraction
        for target in node.targets:
            self._extract_targets(target)
        self.visit(node.value)

    def visit_AnnAssign(self, node: ast.AnnAssign):
        self._extract_targets(node.target)
        if node.value:
            self.visit(node.value)

    def visit_AugAssign(self, node: ast.AugAssign):
        self._extract_targets(node.target)
        self.visit(node.value)

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            name = alias.asname or alias.name.split('.')[0]
            self.imported_names.add(name)
            self.defined_names.add(name)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        for alias in node.names:
            name = alias.asname or alias.name
            self.imported_names.add(name)
            self.defined_names.add(name)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self.defined_names.add(node.name)
        # We don't visit the body to avoid treating local function variables as global definitions,
        # but we do visit default arguments.
        for arg in node.args.defaults:
            self.visit(arg)

    def visit_ClassDef(self, node: ast.ClassDef):
        self.defined_names.add(node.name)
        # Visit bases and decorators
        for base in node.bases:
            self.visit(base)

    def visit_Call(self, node: ast.Call):
        # Check if this is a method call on a name, e.g., obj.method()
        if isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                var_name = node.func.value.id
                method_name = node.func.attr
                
                # Check for standard mutating methods or inplace=True argument
                is_mutation = False
                if method_name in ("append", "extend", "update", "pop", "insert", "clear", "dropna", "fillna", "replace", "reset_index"):
                    is_mutation = True
                else:
                    for kw in node.keywords:
                        if kw.arg == "inplace":
                            # Check for True constant (supports NameConstant and Constant)
                            if hasattr(kw.value, "value") and kw.value.value is True:
                                is_mutation = True
                            elif isinstance(kw.value, ast.NameConstant) and kw.value.value is True:
                                is_mutation = True
                                
                if is_mutation:
                    self.defined_names.add(var_name)
                    self.mutations.append((var_name, method_name))

        self.generic_visit(node)

    def _extract_targets(self, node: ast.AST):
        if isinstance(node, ast.Name):
            self.defined_names.add(node.id)
        elif isinstance(node, (ast.Tuple, ast.List)):
            for elt in node.elts:
                self._extract_targets(elt)
        elif isinstance(node, ast.Attribute):
            # e.g., obj.attr = val -> 'obj' is modified
            if isinstance(node.value, ast.Name):
                self.defined_names.add(node.value.id)


class _CellTimeVisitor(ast.NodeVisitor):
    """
    Root Cause A (edge case): collects (used, defined, defined_via_import)
    names that participate at CELL-EXECUTION time for ONE top-level
    statement -- skips function/lambda bodies (deferred until called) but
    treats class bodies, decorators, base classes, and default-argument
    expressions as immediate.

    This backs `VariableStateExtractor.detect_execution_order_violations`,
    which flags the edge case documented in
    `reports/execution_count_reordering_limitation.md`: sorting cells by
    `execution_count` (this preprocessor's own Root-Cause-A "resolve"
    mechanism) can place a cell that imports a name AFTER cells that already
    use it, if the import cell was re-run later (e.g. after a kernel
    restart) without re-running its dependents. Measured on the JunoBench
    corpus at 26.6% of notebooks (import-specific signal; see
    `reports/execution_count_consistency_report.md`) -- common enough to
    warrant a Tier-2 detect-and-flag annotation rather than a silent,
    potentially non-runnable reordering.

    IMPORTANT: must be applied per-statement, in order, updating the
    caller's running "defined so far" set incrementally within a cell --
    NOT aggregated at the whole-cell level. An earlier version of this
    check (in the standalone corpus scan) aggregated at the cell level and
    spuriously flagged the ordinary `x = f(); x.method()` pattern (define
    then use within the same cell) as a violation, inflating a validation
    run to 100% of notebooks flagged. Fixed there and ported here with the
    per-statement discipline preserved; do not regress this.
    """

    def __init__(self):
        self.used: Set[str] = set()
        self.defined: Set[str] = set()
        self.defined_via_import: Set[str] = set()

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            self.used.add(node.id)
        elif isinstance(node.ctx, (ast.Store, ast.Del)):
            self.defined.add(node.id)

    def visit_AugAssign(self, node):
        if isinstance(node.target, ast.Name):
            self.used.add(node.target.id)
            self.defined.add(node.target.id)
        self.visit(node.value)

    def visit_Import(self, node):
        for alias in node.names:
            name = alias.asname or alias.name.split(".")[0]
            self.defined.add(name)
            self.defined_via_import.add(name)

    def visit_ImportFrom(self, node):
        for alias in node.names:
            name = alias.asname or alias.name
            if name != "*":
                self.defined.add(name)
                self.defined_via_import.add(name)

    def _visit_def(self, node, is_class):
        self.defined.add(node.name)
        for dec in node.decorator_list:
            self.visit(dec)
        if is_class:
            for base in node.bases:
                self.visit(base)
            for kw in node.keywords:
                self.visit(kw.value)
            for stmt in node.body:
                self.visit(stmt)
        else:
            args = node.args
            for d in list(args.defaults) + [d for d in args.kw_defaults if d]:
                self.visit(d)
            # function BODY is deferred -- do not visit.

    def visit_FunctionDef(self, node):
        self._visit_def(node, is_class=False)

    def visit_AsyncFunctionDef(self, node):
        self._visit_def(node, is_class=False)

    def visit_ClassDef(self, node):
        self._visit_def(node, is_class=True)

    def visit_Lambda(self, node):
        pass

    def visit_Global(self, node):
        pass

    def visit_Nonlocal(self, node):
        pass


class VariableStateExtractor:
    """
    Stage 2: LLM-Assisted/Static Hybrid State Extractor
    Builds the variable dependency graph, type hints, shapes, and flags ghost/stale status.
    """
    
    # Common type pattern matching in Python code
    DF_CREATION = re.compile(r'\b(read_csv|read_excel|DataFrame|read_sql|read_json|pivot_table|groupby)\b')
    NP_CREATION = re.compile(r'\b(array|zeros|ones|arange|linspace|empty|random|get_dummies)\b')
    FIG_CREATION = re.compile(r'\b(plot|subplots|figure|scatter|bar|hist|imshow)\b')
    
    # Output pattern matching for DataFrame shapes
    DF_SHAPE_OUT = re.compile(r'\[(\d+)\s+rows\s+x\s+(\d+)\s+columns\]')
    SHAPE_TUPLE_OUT = re.compile(r'shape:\s*\((\d+),\s*(\d+)\)|\((\d+),\s*(\d+)\)')

    # Root Cause D: patterns whose output can change between executions.
    # Detection is regex-based so it also works on cells the AST parser rejects
    # (magic commands, shell escapes).
    DIVERGENCE_PATTERNS = [
        (re.compile(r'\b(?:np\.random|random)\.\w+'), "random number generation"),
        (re.compile(r'\btorch\.(?:rand|randn|randint|randperm)\b'), "random tensor generation"),
        (re.compile(r'\bdatetime\.now\(|\btime\.time\(|\bdate\.today\('), "current time/date"),
        (re.compile(r'\bread_(?:csv|excel|sql|json|parquet)\('), "external file/DB read (source may change)"),
        (re.compile(r'\brequests\.\w+\(|\burlopen\(|\burlretrieve\('), "network request"),
        (re.compile(r'\binput\('), "interactive user input"),
    ]
    # Sampling/splitting calls are only divergent when no seed is pinned
    SEEDABLE_CALL = re.compile(r'\b(train_test_split|\.sample)\s*\(([^)]*)\)')

    def __init__(self):
        pass

    @classmethod
    def detect_divergence_risks(cls, code: str) -> List[str]:
        """
        Root Cause D (re-execution divergence): statically flags calls whose
        output may differ if the cell is re-run. Cannot detect that divergence
        HAS happened (the .ipynb stores only one output) — only that the cell
        is susceptible, so the LLM knows the stored output may be stale.
        """
        risks = []
        for pattern, reason in cls.DIVERGENCE_PATTERNS:
            if pattern.search(code):
                risks.append(reason)
        for m in cls.SEEDABLE_CALL.finditer(code):
            args = m.group(2)
            if "random_state" not in args and "seed" not in args:
                risks.append(f"unseeded {m.group(1).lstrip('.')}()")
        return risks

    @classmethod
    def detect_execution_order_violations(cls, sorted_code_cells: List[str]) -> Dict[int, List[str]]:
        """
        Root Cause A (edge case, not the common case): `execution_count`
        records only a cell's LAST run, not a mutually-consistent history.
        If an early cell (e.g. an import) is re-run later (e.g. after a
        kernel restart) without re-running its dependents, sorting cells by
        `execution_count` -- this preprocessor's own "resolve" mechanism --
        can place that cell AFTER code that already uses the names it
        defines, producing a sequence that would raise NameError on replay
        in a fresh kernel and does not correspond to any real moment in the
        notebook's history. See `reports/execution_count_reordering_limitation.md`.

        Restricted to names (ever) bound via `import`/`from...import`
        somewhere in the notebook: import names are essentially never
        coincidentally reused for something unrelated, unlike generic
        identifiers (`i`, `x`, `column`), which produce too much noise to be
        a useful per-cell annotation (measured on the JunoBench corpus; see
        `reports/execution_count_consistency_report.md` for the broad vs.
        import-specific comparison). This intentionally UNDER-flags (misses
        non-import instances of the same mechanism) to keep the annotation
        trustworthy rather than noisy.

        Args:
            sorted_code_cells: code cell sources, already sorted by
                `execution_count` (the same order emitted in the output).

        Returns:
            {cell_index: [violating_import_names]} for cells (0-based index
            into `sorted_code_cells`) that use an import-bound name before
            any earlier cell in this order imports it, where some cell in
            the list does import it eventually.
        """
        parsed = []
        for code in sorted_code_cells:
            try:
                tree = ast.parse(code)
            except SyntaxError:
                parsed.append(None)
                continue
            stmts = []
            for stmt in tree.body:
                v = _CellTimeVisitor()
                v.visit(stmt)
                stmts.append((v.used, v.defined, v.defined_via_import))
            parsed.append(stmts)

        all_defined_via_import: Set[str] = set()
        for stmts in parsed:
            if stmts is None:
                continue
            for _used, _defined, defined_via_import in stmts:
                all_defined_via_import |= defined_via_import

        builtin_names = set(__builtins__.keys()) if isinstance(__builtins__, dict) \
            else set(dir(__builtins__))
        builtin_names |= {"self", "cls", "True", "False", "None"}

        defined_so_far: Set[str] = set()
        violations: Dict[int, List[str]] = {}
        for idx, stmts in enumerate(parsed):
            if stmts is None:
                continue
            for used, defined, _defined_via_import in stmts:
                missing = used - defined_so_far - builtin_names
                for name in missing:
                    if name in all_defined_via_import:
                        violations.setdefault(idx, [])
                        if name not in violations[idx]:
                            violations[idx].append(name)
                defined_so_far |= defined
        return violations

    def extract_state(self, cells: List[Dict[str, Any]], mode: str = "full") -> Dict[str, Any]:
        """
        Analyzes preprocessed cells to construct the variables state map.
        Identifies active, stale, and ghost variables, inferring types and shapes.
        Supports basic and full extraction modes.
        """
        variables: Dict[str, Dict[str, Any]] = {}
        defined_so_far: Set[str] = set()
        
        # Sort cells chronologically by execution count to track variable state flow
        # Code cells with execution count first, then unexecuted/markdown cells
        executed_cells = [c for c in cells if c.get("ec") is not None]
        executed_cells.sort(key=lambda x: x["ec"])

        # 1. Track definition and usage flow cell by cell
        for cell in executed_cells:
            ec = cell["ec"]
            code = cell.get("code", "")
            output = cell.get("output", "") or ""
            
            # Static parse of Python code
            try:
                tree = ast.parse(code)
                visitor = ASTVisitor()
                visitor.visit(tree)

                # Root Cause B: which variables were mutated in-place (vs. reassigned)
                mutation_map: Dict[str, List[str]] = {}
                for mvar, mmeth in visitor.mutations:
                    mutation_map.setdefault(mvar, []).append(mmeth)

                # Check for ghost variables (only in full mode)
                if mode == "full":
                    for used in visitor.used_names:
                        # Ignore common builtins, keywords, or libraries
                        if used in (__builtins__ if isinstance(__builtins__, dict) else dir(__builtins__)) or used in ("pd", "np", "plt", "sns", "tf", "keras", "self"):
                            continue
                        
                        if used not in defined_so_far:
                            # We found a variable referenced but not defined yet -> Ghost variable!
                            if used not in variables:
                                variables[used] = {
                                    "type": "unknown",
                                    "defined_in": "unknown",
                                    "last_modified": "unknown",
                                    "status": "ghost",
                                    "confidence": "low",
                                    "note": f"Referenced in ec{ec} but no defining cell found prior."
                                }
                
                # Register defined variables
                for defined in visitor.defined_names:
                    # Ignore library aliases
                    if defined in ("pd", "np", "plt", "sns", "tf", "keras"):
                        continue
                        
                    # Infer type and shape (only in full mode)
                    inferred_type = self._infer_type_from_code(defined, code) if mode == "full" else "unknown"
                    inferred_shape = self._infer_shape_from_output(output) if mode == "full" else None
                    
                    if defined in variables:
                        # Existing variable being modified/re-defined
                        var_entry = variables[defined]
                        var_entry["last_modified"] = f"ec{ec}"
                        if mode == "full":
                            # Root Cause B: record HOW the variable changed, not just when
                            hist = var_entry.setdefault(
                                "history", [f"created {var_entry.get('defined_in', '?')}"])
                            if defined in mutation_map:
                                for meth in mutation_map[defined]:
                                    hist.append(f"mutated ec{ec} ({meth})")
                            else:
                                hist.append(f"reassigned ec{ec}")
                            if inferred_type != "unknown":
                                var_entry["type"] = inferred_type
                            if inferred_shape:
                                var_entry["shape_hint"] = inferred_shape
                            if var_entry["status"] == "ghost":
                                # It was marked as ghost, but now defined -> Resolve to active (or mark warning)
                                var_entry["status"] = "active"
                                var_entry["confidence"] = "medium"
                                var_entry["note"] = f"Ghost resolved: defined late in ec{ec}"
                    else:
                        # New variable creation
                        variables[defined] = {
                            "type": inferred_type,
                            "defined_in": f"ec{ec}",
                            "last_modified": f"ec{ec}",
                            "status": "active",
                            "confidence": "high" if mode == "full" else "medium"
                        }
                        if inferred_shape:
                            variables[defined]["shape_hint"] = inferred_shape
                        # Created and mutated in the same cell (e.g. read_csv then dropna(inplace))
                        if mode == "full" and defined in mutation_map:
                            variables[defined]["history"] = (
                                [f"created ec{ec}"] +
                                [f"mutated ec{ec} ({m})" for m in mutation_map[defined]])
                            
                    defined_so_far.add(defined)
                    
            except SyntaxError:
                # Fallback to simple regex parsing if code contains ipython magic commands or has syntax errors
                if mode == "full":
                    self._fallback_regex_parse(code, output, ec, variables, defined_so_far)
                else:
                    # Basic mode: just look for standard LHS assignments
                    for word in re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*=', code):
                        if word not in ("pd", "np", "plt", "sns", "tf", "keras"):
                            if word not in variables:
                                variables[word] = {
                                    "type": "unknown",
                                    "defined_in": f"ec{ec}",
                                    "last_modified": f"ec{ec}",
                                    "status": "active",
                                    "confidence": "medium"
                                }
                            else:
                                variables[word]["last_modified"] = f"ec{ec}"
                            defined_so_far.add(word)

        # 2. Check outputs of cells to refine DataFrame shape hints (only in full mode)
        if mode == "full":
            self._refine_types_and_shapes(executed_cells, variables)
            self._recover_ghost_observations(executed_cells, variables)

        # 3. Compact histories: drop single-entry histories (they duplicate
        #    defined_in) and cap long ones so the table stays token-lean
        for var_entry in variables.values():
            hist = var_entry.get("history")
            if hist is None:
                continue
            if len(hist) <= 1:
                del var_entry["history"]
            elif len(hist) > 6:
                var_entry["history"] = hist[:1] + [f"... {len(hist) - 6} steps omitted ..."] + hist[-5:]

        return variables

    def _recover_ghost_observations(self, executed_cells: List[Dict[str, Any]],
                                    variables: Dict[str, Dict[str, Any]]):
        """
        Root Cause C: a ghost variable's ORIGIN is unrecoverable from a cold
        .ipynb, but its VALUE may survive in output history — a cell whose code
        displays the variable (`x`, `print(x)`, `display(x)`) stores its repr.
        We report that observation verbatim; we never invent an origin.
        """
        ghosts = [name for name, v in variables.items() if v.get("status") == "ghost"]
        if not ghosts:
            return
        for name in ghosts:
            display_re = re.compile(
                r'^\s*(?:print\(\s*%s\s*\)|display\(\s*%s\s*\)|%s)\s*$'
                % (re.escape(name), re.escape(name), re.escape(name)))
            best = None  # (ec, output)
            for cell in executed_cells:
                code_lines = [ln for ln in (cell.get("code") or "").splitlines() if ln.strip()]
                output = cell.get("output") or ""
                if not code_lines or not output:
                    continue
                if display_re.match(code_lines[-1]):
                    ec = cell.get("ec")
                    if best is None or (ec is not None and best[0] is not None and ec > best[0]):
                        best = (ec, output)
            if best is not None:
                snippet = best[1].strip().replace("\n", " ")
                if len(snippet) > 120:
                    snippet = snippet[:120] + "..."
                variables[name]["last_observed_value"] = snippet
                variables[name]["observed_in"] = f"ec{best[0]}"


    def _infer_type_from_code(self, var_name: str, code: str) -> str:
        """Statically infers variable type by examining variable assignment statements."""
        # Search for lines where var_name is assigned
        lines = code.split('\n')
        for line in lines:
            if '=' in line:
                parts = line.split('=', 1)
                lhs, rhs = parts[0].strip(), parts[1].strip()
                # Check if var_name is on left side
                if var_name in lhs:
                    if self.DF_CREATION.search(rhs):
                        return "DataFrame"
                    elif self.NP_CREATION.search(rhs):
                        return "ndarray"
                    elif self.FIG_CREATION.search(rhs):
                        return "Figure/Axes"
                    # Constant literals
                    if rhs.isdigit():
                        return "int"
                    if rhs.replace('.', '', 1).isdigit() and '.' in rhs:
                        return "float"
                    if (rhs.startswith('"') and rhs.endswith('"')) or (rhs.startswith("'") and rhs.endswith("'")):
                        return "str"
                    if rhs.startswith('[') and rhs.endswith(']'):
                        return "list"
                    if rhs.startswith('{') and rhs.endswith('}'):
                        return "dict"
        return "unknown"

    def _infer_shape_from_output(self, output: str) -> Optional[str]:
        """Extracts shape information from text plain outputs."""
        if not output:
            return None
            
        # Check for standard Pandas shape footer: [208 rows x 61 columns]
        df_match = self.DF_SHAPE_OUT.search(output)
        if df_match:
            rows, cols = df_match.group(1), df_match.group(2)
            return f"({rows}, {cols})"
            
        # Check for standard NumPy .shape tuple e.g. (208, 61) or shape: (208, 61)
        shape_match = self.SHAPE_TUPLE_OUT.search(output)
        if shape_match:
            # Get the non-empty matching group
            groups = [g for g in shape_match.groups() if g is not None]
            if len(groups) >= 2:
                return f"({groups[0]}, {groups[1]})"

        # Pandas Series repr footer: "Name: col, Length: 100, dtype: float64"
        series_match = re.search(r'Length:\s*(\d+),\s*dtype:\s*(\w+)', output)
        if series_match:
            return f"({series_match.group(1)},) dtype={series_match.group(2)}"

        return None

    def _fallback_regex_parse(self, code: str, output: str, ec: int, variables: Dict[str, Any], defined_so_far: Set[str]):
        """Simple regex fallback if ast parsing fails (e.g. on syntax error or magic commands)."""
        # Find potential assignments using regex: var_name = value
        assign_pattern = re.compile(r'^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*=[^=]', re.MULTILINE)
        for match in assign_pattern.finditer(code):
            defined = match.group(1)
            if defined in ("pd", "np", "plt", "sns", "tf", "keras"):
                continue
                
            inferred_type = "unknown"
            inferred_shape = self._infer_shape_from_output(output)
            
            if defined in variables:
                variables[defined]["last_modified"] = f"ec{ec}"
                if inferred_shape:
                    variables[defined]["shape_hint"] = inferred_shape
            else:
                variables[defined] = {
                    "type": inferred_type,
                    "defined_in": f"ec{ec}",
                    "last_modified": f"ec{ec}",
                    "status": "active",
                    "confidence": "medium"
                }
                if inferred_shape:
                    variables[defined]["shape_hint"] = inferred_shape
                    
            defined_so_far.add(defined)

    def _refine_types_and_shapes(self, executed_cells: List[Dict[str, Any]], variables: Dict[str, Dict[str, Any]]):
        """
        Cross-references variables with subsequent cell calls.
        For example: if cell has `df.shape` and output `(100, 5)`, it sets `df` shape_hint to `(100, 5)`.
        """
        for cell in executed_cells:
            code = cell.get("code", "").strip()
            output = cell.get("output", "") or ""
            
            if not output:
                continue
                
            # If code is variable name followed by .shape, e.g. df.shape or print(df.shape)
            shape_call_match = re.search(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\.shape\b', code)
            if shape_call_match:
                var_name = shape_call_match.group(1)
                if var_name in variables:
                    inferred_shape = self._infer_shape_from_output(output)
                    if inferred_shape:
                        variables[var_name]["shape_hint"] = inferred_shape
                        if variables[var_name]["type"] == "unknown":
                            variables[var_name]["type"] = "DataFrame"  # Usually DataFrame or ndarray
                            
            # If code is variable name followed by .head(), describe(), or columns, e.g. df.head()
            df_call_match = re.search(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\.(head|describe|columns|info|dropna)\b', code)
            if df_call_match:
                var_name = df_call_match.group(1)
                if var_name in variables:
                    variables[var_name]["type"] = "DataFrame"
                    inferred_shape = self._infer_shape_from_output(output)
                    if inferred_shape:
                        variables[var_name]["shape_hint"] = inferred_shape
