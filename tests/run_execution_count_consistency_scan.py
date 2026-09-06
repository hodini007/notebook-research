"""
Execution-count consistency scan: a $0, no-LLM, corpus-wide check for the
edge case documented in reports/execution_count_reordering_limitation.md.

`.ipynb`'s `execution_count` records only a cell's LAST run, not a
mutually-consistent history. If a cell (e.g. an import) is re-run later
without re-running its dependents, sorting cells by `execution_count` --
exactly what src/preprocessor.py's "resolve" tier and the ground-truth
re-execution methodology both do -- can place that cell AFTER code that
already uses the names it defines. Replaying such a sequence in a fresh
kernel raises NameError on a name that the notebook's author never actually
had a problem with.

This script does NOT execute any code. For each notebook it statically:
  1. Sorts code cells by execution_count (the same order the preprocessor
     and ground-truth extractor use).
  2. Walks each cell's AST, tracking which names become defined at
     CELL-EXECUTION TIME (top-level assignments/imports/def-and-class names;
     decorator/base-class/default-arg expressions; class-body statements
     execute immediately, function/lambda BODIES do not and are skipped).
  3. Flags a "count-order dependency violation": a name used at
     cell-execution time that is not yet defined by any prior cell in the
     execution_count-sorted order, but IS defined by some cell later in that
     same order (so the notebook is internally consistent -- the name is
     real -- it's just the numeric reordering that breaks it).

This is a static heuristic (no dataflow/scoping is perfect -- comprehension
scoping, walrus operators, and `del` are not modeled precisely), so treat
counts as approximate signal, not exact ground truth. It intentionally
errs toward UNDER-counting violations (broad "defined" tracking) rather than
over-counting, since the goal is to establish whether this is a rare fluke
or common enough to require an algorithmic fix.

Usage:
    python3 tests/run_execution_count_consistency_scan.py
"""
import ast
import builtins
import json
import os
import keyword

HERE = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(HERE, "junobench_downloads")
REPORT_PATH = os.path.join(HERE, "../reports/execution_count_consistency_report.md")

BUILTIN_NAMES = set(dir(builtins)) | set(keyword.kwlist) | {
    "self", "cls", "__name__", "__file__", "__doc__", "True", "False", "None",
}


class CellTimeVisitor(ast.NodeVisitor):
    """Collects (used, defined) names that participate at CELL-EXECUTION
    time -- i.e. skips function/lambda bodies (deferred until called) but
    treats class bodies, decorators, base classes, and default arg
    expressions as immediate (they run when the def/class statement runs)."""

    def __init__(self):
        self.used = set()
        self.defined = set()
        self.defined_via_import = set()

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            self.used.add(node.id)
        elif isinstance(node.ctx, (ast.Store, ast.Del)):
            self.defined.add(node.id)

    def visit_AugAssign(self, node):
        # target is read-then-written: must already exist.
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
                self.visit(stmt)  # class body executes immediately
        else:
            args = node.args
            for d in list(args.defaults) + [d for d in args.kw_defaults if d]:
                self.visit(d)
            for a in list(args.args) + list(args.posonlyargs) + list(args.kwonlyargs):
                for dec in getattr(a, "annotation", None) and [a.annotation] or []:
                    self.visit(dec)
            # function BODY is deferred -- do not visit.

    def visit_FunctionDef(self, node):
        self._visit_def(node, is_class=False)

    def visit_AsyncFunctionDef(self, node):
        self._visit_def(node, is_class=False)

    def visit_ClassDef(self, node):
        self._visit_def(node, is_class=True)

    def visit_Lambda(self, node):
        pass  # opaque; body deferred, and a bare lambda expr binds no name

    def visit_Global(self, node):
        pass

    def visit_Nonlocal(self, node):
        pass


def cell_statements(code):
    """Returns a list of (used, defined) per TOP-LEVEL STATEMENT (preserving
    intra-cell order), or None if the cell doesn't parse (magics, shell
    escapes, etc. -- excluded from this scan, same as the preprocessor's
    AST-rejection fallback).

    Statement-level granularity matters: aggregating a whole cell's used/
    defined names loses ordering WITHIN the cell, which would wrongly flag
    the extremely common pattern `x = f(); x.method()` as a violation (x is
    both used and defined in the same cell -- defined first, used second --
    but a whole-cell aggregate can't see that ordering)."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return None
    out = []
    for stmt in tree.body:
        v = CellTimeVisitor()
        v.visit(stmt)
        out.append((v.used, v.defined, v.defined_via_import))
    return out


def clean_source(source):
    return "".join(source) if isinstance(source, list) else str(source)


def scan_notebook(path):
    with open(path, encoding="utf-8") as f:
        nb = json.load(f)
    cells = []
    for cell in nb.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        ec = cell.get("execution_count")
        if ec is None:
            continue
        try:
            ec = int(ec)
        except (TypeError, ValueError):
            continue
        cells.append((ec, clean_source(cell.get("source", ""))))
    cells.sort(key=lambda c: c[0])

    parsed = [(ec, cell_statements(code)) for ec, code in cells]
    unparsed = sum(1 for _, r in parsed if r is None)
    parsed = [(ec, r) for ec, r in parsed if r is not None]
    if len(parsed) < 2:
        return None

    all_defined_anywhere = set()
    all_defined_via_import = set()
    for _, stmts in parsed:
        for stmt in stmts:
            used, defined, defined_via_import = stmt
            all_defined_anywhere |= defined
            all_defined_via_import |= defined_via_import

    defined_so_far = set()
    violations = []
    for ec, stmts in parsed:
        for used, defined, _defined_via_import in stmts:
            # Statement-level: check against defined_so_far BEFORE this
            # statement, then immediately fold this statement's own
            # definitions in -- so `x = f(); x.method()` is correctly seen
            # as define-then-use within the same cell, not a violation.
            missing = used - defined_so_far - BUILTIN_NAMES
            for name in missing:
                if name in all_defined_anywhere and not cell_flagged_name(violations, ec, name):
                    violations.append((ec, name))
            defined_so_far |= defined

    # Stricter subset: violations on names that are (ever) bound via an
    # import statement somewhere in the notebook. Import names are
    # essentially never coincidentally reused for a different, unrelated
    # purpose (unlike generic short identifiers like `i`, `x`, `column`),
    # so this subset is a much cleaner signal for the specific mechanism in
    # reports/execution_count_reordering_limitation.md (a re-run-late import
    # cell), at the cost of missing non-import cases of the same mechanism.
    import_violations = [(ec, n) for ec, n in violations if n in all_defined_via_import]

    return {
        "n_code_cells_executed": len(cells),
        "n_parsed": len(parsed),
        "n_unparsed": unparsed,
        "n_violations": len(violations),
        "violating_names": sorted({n for _, n in violations}),
        "has_violation": len(violations) > 0,
        "n_import_violations": len(import_violations),
        "import_violating_names": sorted({n for _, n in import_violations}),
        "has_import_violation": len(import_violations) > 0,
    }


def cell_flagged_name(violations, ec, name):
    """Avoid double-counting the same name flagged twice within one cell
    across multiple statements (e.g. used in two separate lines before its
    defining statement runs later in the notebook)."""
    return any(v_ec == ec and v_name == name for v_ec, v_name in violations)


def main():
    results = []
    for root, _dirs, files in os.walk(DOWNLOAD_DIR):
        for fn in sorted(files):
            if not fn.endswith(".ipynb") or fn.endswith(("_fixed.ipynb", "_reproduced.ipynb", "_fixed2.ipynb")):
                continue
            path = os.path.join(root, fn)
            try:
                r = scan_notebook(path)
            except Exception as e:
                results.append({"name": fn, "status": f"error: {e}"})
                continue
            if r is None:
                results.append({"name": fn, "status": "skipped (too few parseable cells)"})
                continue
            r["name"] = fn
            r["status"] = "ok"
            results.append(r)

    ok = [r for r in results if r["status"] == "ok"]
    affected = [r for r in ok if r["has_violation"]]
    total_violations = sum(r["n_violations"] for r in ok)
    import_affected = [r for r in ok if r["has_import_violation"]]
    total_import_violations = sum(r["n_import_violations"] for r in ok)

    lines = [
        "# Execution-Count Consistency Scan (corpus-wide, $0, no LLM calls)\n",
        "Static check for the edge case in "
        "`reports/execution_count_reordering_limitation.md`: does sorting a "
        "notebook's cells by `execution_count` (the paper's core "
        "\"resolve\" mechanism for Root Cause A) produce a sequence where "
        "some cell uses a name before any earlier cell (in that sorted "
        "order) defines it, even though the name IS defined somewhere in "
        "the notebook? This is a static def-before-use heuristic; see the "
        "script docstring for scoping caveats.\n",
        "**Two counts are reported.** The broad count includes every "
        "flagged name and is dominated by noise: generic short "
        "identifiers (`i`, `x`, `column`, `c`, `f`) are legitimately "
        "reused for unrelated purposes across different cells, and a "
        "static def-before-use scan cannot tell that apart from a genuine "
        "reordering hazard. The **import-specific** count restricts to "
        "names that are (ever) bound via an `import`/`from...import` "
        "statement somewhere in the notebook — import names are almost "
        "never coincidentally reused for something unrelated, so this "
        "subset is a much cleaner signal for the exact mechanism verified "
        "in `numpy_1.ipynb` (a re-run-late import cell), at the cost of "
        "missing non-import instances of the same mechanism.\n",
        f"- Notebooks scanned: **{len(results)}**",
        f"- Successfully analyzed (≥2 parseable executed cells): **{len(ok)}**",
        f"- Broad count (noisy, includes generic-name collisions): "
        f"{len(affected)}/{len(ok)} notebooks ({len(affected) / len(ok):.1%}), "
        f"{total_violations} instances" if ok else "- No notebooks analyzable",
        f"- **Import-specific count (cleaner signal): {len(import_affected)}/{len(ok)} "
        f"notebooks ({len(import_affected) / len(ok):.1%}), "
        f"{total_import_violations} instances**" if ok else "",
        "",
        "## Per-notebook results (import-violations first, then broad violations)\n",
        "| Notebook | Status | Executed cells | Parsed | Unparsed | Import violations | Broad violations | Import-violating names |",
        "| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |",
    ]

    def sort_key(r):
        if r["status"] != "ok":
            return (2, r["name"])
        return (0 if r["has_import_violation"] else 1,
                -r.get("n_import_violations", 0), -r.get("n_violations", 0), r["name"])
    for r in sorted(results, key=sort_key):
        if r["status"] != "ok":
            lines.append(f"| `{r['name']}` | {r['status']} | — | — | — | — | — | — |")
            continue
        names = ", ".join(f"`{n}`" for n in r["import_violating_names"][:6])
        if len(r["import_violating_names"]) > 6:
            names += f" (+{len(r['import_violating_names']) - 6} more)"
        lines.append(
            f"| `{r['name']}` | ok | {r['n_code_cells_executed']} | "
            f"{r['n_parsed']} | {r['n_unparsed']} | {r['n_import_violations']} | "
            f"{r['n_violations']} | {names} |")

    lines += [
        "",
        "## Interpretation",
        "",
        "- A violation means: reordering this notebook by `execution_count` "
        "(as both `src/preprocessor.py` and the ground-truth re-execution "
        "methodology do) produces a sequence where a name is used before "
        "any prior cell (in that order) defines it, even though some cell "
        "does define it eventually. Replaying such a sequence in a fresh "
        "kernel would raise `NameError` at that point, independent of any "
        "other data/dependency issue.",
        "- This does not necessarily mean the *notebook* is broken -- it "
        "means the *execution_count-sort assumption* breaks for it, most "
        "plausibly because an early cell (import, config) was re-run later "
        "(e.g. after a kernel restart) without re-running its dependents.",
        "- **Use the import-specific count as the headline number**; the "
        "broad count is reported for transparency but should not be cited "
        "on its own -- an earlier, uncorrected version of this scan (before "
        "statement-level ordering was implemented) spuriously flagged "
        "100% of notebooks due to a bug that treated ordinary "
        "define-then-use-in-the-same-cell code as a violation; that bug is "
        "fixed, but generic-identifier collision noise remains in the "
        "broad count by design (it is not separable without deeper "
        "semantic/dataflow analysis than this static scan performs).",
        "- Static heuristic caveats: comprehension-scope leakage, `del`, "
        "and walrus operators are not modeled precisely; this scan "
        "deliberately over-counts a cell's `defined` set (permissive) to "
        "avoid over-counting violations, so true prevalence may be "
        "slightly higher than reported here.",
    ]

    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    if ok:
        print(f"Scanned {len(results)} notebooks; {len(ok)} analyzable.")
        print(f"Broad (noisy): {len(affected)}/{len(ok)} ({len(affected)/len(ok):.1%}) "
              f"notebooks, {total_violations} instances.")
        print(f"Import-specific (cleaner signal): {len(import_affected)}/{len(ok)} "
              f"({len(import_affected)/len(ok):.1%}) notebooks, "
              f"{total_import_violations} instances.")
    else:
        print("No notebooks analyzable.")
    print(f"Report -> {REPORT_PATH}")


if __name__ == "__main__":
    main()
