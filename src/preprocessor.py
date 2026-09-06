import json
import re
import yaml
from typing import Dict, List, Any, Tuple, Optional, Union

# ANSI escape sequence regex
ANSI_ESCAPE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

def strip_ansi(text: str) -> str:
    """Removes ANSI escape codes (colors, formatting) from text."""
    return ANSI_ESCAPE.sub('', text)

def clean_source(source: Union[str, List[str]]) -> str:
    """Joins a source string list into a single string."""
    if isinstance(source, list):
        return "".join(source)
    return str(source)

class RuleBasedPreprocessor:
    """
    Stage 1: Rule-Based Preprocessor (Zero LLM Cost)
    Deterministic Python preprocessor to clean .ipynb files.
    """

    def __init__(self, keep_markdown: bool = True):
        self.keep_markdown = keep_markdown

    def preprocess_notebook_data(self, notebook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Preprocesses raw Jupyter Notebook JSON data.
        Strips cell/notebook metadata, base64 images, deduplicates MIME types,
        keeps latest outputs, sorts by execution count, and converts to flat format.
        """
        raw_cells = notebook_data.get("cells", [])
        processed_cells = []
        execution_order = []

        # First pass: Clean each cell and collect execution counts
        for idx, cell in enumerate(raw_cells):
            cell_type = cell.get("cell_type", "")
            
            if cell_type == "markdown":
                if self.keep_markdown:
                    source = clean_source(cell.get("source", ""))
                    processed_cells.append({
                        "type": "markdown",
                        "markdown": source,
                        "_orig_idx": idx
                    })
            elif cell_type == "code":
                ec = cell.get("execution_count")
                # Make sure ec is an integer if present
                if ec is not None:
                    try:
                        ec = int(ec)
                    except (ValueError, TypeError):
                        ec = None
                
                code = clean_source(cell.get("source", ""))
                
                # Process outputs
                output_text, output_type = self._process_outputs(cell.get("outputs", []))
                
                cell_dict = {
                    "type": "code",
                    "ec": ec,
                    "code": code,
                    "output": output_text,
                    "output_type": output_type,
                    "_orig_idx": idx
                }
                processed_cells.append(cell_dict)
                
                if ec is not None:
                    execution_order.append(ec)

        # Sort execution order list for metadata
        execution_order = sorted(list(set(execution_order)))

        # Sort cells chronologically based on execution count
        sorted_cells = self._sort_cells(processed_cells)

        # Root Cause E: distinguish tolerated errors from terminal ones.
        # If cells with a HIGHER execution_count exist, the user saw this error
        # and deliberately kept going — the LLM should not treat the notebook
        # as broken at this point.
        self._annotate_error_status(sorted_cells)

        # Root Cause D: flag cells whose output may not reproduce on re-run
        try:
            from state_extractor import VariableStateExtractor as _VSE
            for cell in sorted_cells:
                if cell.get("type") == "code" and cell.get("code"):
                    risks = _VSE.detect_divergence_risks(cell["code"])
                    if risks:
                        cell["divergence_risk"] = risks
        except ImportError:
            pass

        # Root Cause A (edge case): `execution_count` records only a cell's
        # LAST run, so sorting by it can place an import cell AFTER code
        # that already uses it (e.g. after a kernel restart re-ran the
        # import without re-running its dependents) -- a sequence that
        # would not actually run in a fresh kernel. Measured at 26.6% of
        # JunoBench notebooks (import-specific signal; see
        # reports/execution_count_consistency_report.md). Flag it rather
        # than silently emit a possibly-non-runnable order (Tier 2:
        # detect and flag, not resolve -- we cannot know from the file
        # alone whether the import genuinely happened earlier too).
        try:
            from state_extractor import VariableStateExtractor as _VSE2
            code_cell_indices = [i for i, c in enumerate(sorted_cells) if c.get("type") == "code"]
            code_sources = [sorted_cells[i].get("code", "") for i in code_cell_indices]
            violations = _VSE2.detect_execution_order_violations(code_sources)
            for local_idx, names in violations.items():
                cell = sorted_cells[code_cell_indices[local_idx]]
                cell["execution_order_risk"] = (
                    f"uses {', '.join(sorted(names))} before any earlier cell (in this "
                    f"execution_count order) imports it; this notebook's execution_count "
                    f"values may reflect a re-run (e.g. kernel restart) rather than a "
                    f"single consistent history -- treat this cell's position as "
                    f"uncertain, not necessarily broken"
                )
        except ImportError:
            pass

        # Determine Complexity Route
        complexity_route = self.route_complexity(notebook_data)
        
        # Stage 2: Extract variable state map (uses temporary keys like 'type')
        variables = {}
        if complexity_route != "simple":
            try:
                from state_extractor import VariableStateExtractor
                state_extractor = VariableStateExtractor()
                mode = "full" if complexity_route == "complex" else "basic"
                variables = state_extractor.extract_state(sorted_cells, mode=mode)
            except Exception as e:
                variables = {"error": f"Failed to extract variable state: {e}"}

        # Clean temporary internal keys before returning
        for cell in sorted_cells:
            cell.pop("_orig_idx", None)
            if cell.get("type") == "markdown":
                cell.pop("type", None)
            elif cell.get("type") == "code":
                cell.pop("type", None)

        return {
            "complexity_route": complexity_route,
            "execution_order": execution_order,
            "cells": sorted_cells,
            "variables": variables
        }


    def _annotate_error_status(self, cells: List[Dict[str, Any]]) -> None:
        """
        Root Cause E (silenced errors): a cell with an error output followed by
        later-executed cells was TOLERATED — the user continued past it, often
        working around the failure. Only an error in the final executed cell is
        TERMINAL. Annotates error cells in place.
        """
        error_ecs = [c.get("ec") for c in cells
                     if c.get("output_type") == "error" and c.get("ec") is not None]
        if not error_ecs:
            return
        all_ecs = [c.get("ec") for c in cells if c.get("ec") is not None]
        max_ec = max(all_ecs)
        for cell in cells:
            if cell.get("output_type") != "error" or cell.get("ec") is None:
                continue
            later = sum(1 for ec in all_ecs if ec > cell["ec"])
            if later > 0:
                cell["error_status"] = (
                    f"tolerated: {later} cell(s) executed after this error — "
                    "user continued past it; do not assume the notebook is broken here")
            else:
                cell["error_status"] = f"terminal: last executed cell (ec={max_ec}) — execution stopped here"

    def _process_outputs(self, outputs: List[Dict[str, Any]]) -> Tuple[Optional[str], Optional[str]]:
        """
        Cleans and aggregates cell outputs.
        - Strips base64 image data.
        - Deduplicates MIME types (keeping text/plain, discarding text/html, text/latex).
        - Keeps the latest execute_result if multiple are present.
        - Strips ANSI escape codes from tracebacks.
        """
        if not outputs:
            return None, None

        has_error = False
        error_info = []
        text_outputs = []
        
        # Track execute_results to keep the one with the highest execution_count
        execute_results = []
        display_data_items = []
        stream_outputs = []

        for out in outputs:
            out_type = out.get("output_type", "")
            
            if out_type == "error":
                has_error = True
                ename = out.get("ename", "Error")
                evalue = out.get("evalue", "")
                traceback = out.get("traceback", [])
                # Clean ANSI escape sequences
                cleaned_tb = [strip_ansi(line) for line in traceback]
                error_info.append((ename, evalue, cleaned_tb))
                
            elif out_type == "stream":
                stream_text = clean_source(out.get("text", ""))
                stream_outputs.append(strip_ansi(stream_text))
                
            elif out_type == "execute_result":
                ec = out.get("execution_count")
                data = out.get("data", {})
                cleaned_data = self._clean_mime_bundle(data)
                if cleaned_data:
                    execute_results.append((ec, cleaned_data))
                    
            elif out_type == "display_data":
                data = out.get("data", {})
                cleaned_data = self._clean_mime_bundle(data)
                if cleaned_data:
                    display_data_items.append(cleaned_data)

        # Deduplicate execute_results: keep the latest one (highest execution count)
        latest_execute_result = None
        if execute_results:
            # Sort by execution_count (handles None by sorting it to the end or using a default)
            execute_results.sort(key=lambda x: (x[0] if x[0] is not None else -1))
            latest_execute_result = execute_results[-1][1]

        # Combine text-like outputs
        # 1. Add all streams
        text_outputs.extend(stream_outputs)
        
        # 2. Add all display_data
        for dd in display_data_items:
            text_outputs.append(dd)
            
        # 3. Add latest execute_result
        if latest_execute_result:
            text_outputs.append(latest_execute_result)

        # Format final output
        if has_error:
            # If an error occurred, format traceback
            tb_strings = []
            for ename, evalue, tb in error_info:
                tb_strings.append(f"{ename}: {evalue}\n" + "\n".join(tb))
            return "\n".join(tb_strings).strip(), "error"
            
        elif text_outputs:
            return "\n".join(text_outputs).strip(), "text"
            
        return None, None

    def _clean_mime_bundle(self, data: Dict[str, Any]) -> Optional[str]:
        """
        Cleans data MIME bundles:
        - Removes image/png, image/jpeg (base64)
        - Keeps text/plain only if available, dropping text/html, text/latex, etc.
        """
        # If text/plain is available, keep only that
        if "text/plain" in data:
            return clean_source(data["text/plain"])
        
        # Otherwise, look for other text types (excluding images/plots)
        for mime, content in data.items():
            if not mime.startswith("image/") and mime not in ("text/html", "text/latex"):
                return clean_source(content)
        
        return None

    def _sort_cells(self, cells: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Sorts cells chronologically using execution_count (ec).
        Associates markdown cells with the executed code cells that follow them.
        """
        # Compute sort key for each cell
        cells_with_keys = []
        
        for idx, cell in enumerate(cells):
            orig_idx = cell["_orig_idx"]
            
            if cell.get("type") == "code":
                ec = cell.get("ec")
                if ec is not None:
                    # Executed code cell: key is execution count plus tiny offset for index
                    key = float(ec) + 0.00001 * orig_idx
                else:
                    # Unexecuted code cell: pushed to the end
                    key = 1000000.0 + float(orig_idx)
            else:  # markdown
                # Find the next executed code cell in original order
                next_ec = None
                for future_cell in cells[idx+1:]:
                    if future_cell.get("type") == "code" and future_cell.get("ec") is not None:
                        next_ec = future_cell["ec"]
                        break
                
                if next_ec is not None:
                    # Associated with the next executed cell (precedes it by 0.5)
                    key = float(next_ec) - 0.5 + 0.00001 * orig_idx
                else:
                    # No future executed cell: pushed to the end
                    key = 1000000.0 + float(orig_idx)
            
            cells_with_keys.append((key, cell))

        # Sort by key
        cells_with_keys.sort(key=lambda x: x[0])
        
        return [cell for _, cell in cells_with_keys]

    def route_complexity(self, notebook_data: Dict[str, Any]) -> str:
        """
        Routes the notebook to the appropriate preprocessing depth:
        - simple: <= 10 cells, linear execution, no plots, no mutations.
        - medium: <= 30 cells, some out-of-order, but no heavy mutations or ghost variables.
        - complex: > 30 cells, OR heavy mutations, OR ghost variables.
        """
        raw_cells = notebook_data.get("cells", [])
        num_cells = len(raw_cells)
        
        # Check cell count
        if num_cells > 30:
            return "complex"
            
        # Analyze code text for mutations, plots, and execution order
        has_plots = False
        has_mutations = False
        is_linear = True
        
        execution_counts = []
        
        # Simple keywords to detect plots and mutations
        mutation_keywords = {"inplace=True", "dropna", "fillna", "replace", "append", "update", "pop", "insert"}
        plot_keywords = {"plt.", "sns.", "plot(", "subplots", "figure(", "show()"}
        
        for cell in raw_cells:
            cell_type = cell.get("cell_type", "")
            if cell_type == "code":
                source = "".join(cell.get("source", ""))
                # Check keywords
                if any(kw in source for kw in mutation_keywords):
                    has_mutations = True
                if any(kw in source for kw in plot_keywords):
                    has_plots = True
                    
                ec = cell.get("execution_count")
                if ec is not None:
                    try:
                        ec = int(ec)
                        execution_counts.append(ec)
                    except (ValueError, TypeError):
                        pass
                        
        # Check linearity
        if execution_counts:
            # Check if strictly monotonically increasing
            for i in range(len(execution_counts) - 1):
                if execution_counts[i+1] <= execution_counts[i]:
                    is_linear = False
                    break
        else:
            is_linear = True # No execution yet
            
        # Classify complexity
        if num_cells <= 10 and is_linear and not has_plots and not has_mutations:
            return "simple"
        elif num_cells <= 30 and not has_mutations:
            return "medium"
        else:
            return "complex"

    def preprocess(self, ipynb_path: str) -> Dict[str, Any]:
        """Loads a notebook file and returns the preprocessed dict structure."""
        with open(ipynb_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return self.preprocess_notebook_data(data)

    def preprocess_to_yaml(self, ipynb_path: str, output_path: Optional[str] = None) -> str:
        """Preprocesses a notebook and converts the result to YAML."""
        preprocessed = self.preprocess(ipynb_path)
        # Convert to YAML format
        # Using default_flow_style=False to keep it human-readable and clean
        yaml_str = yaml.dump(preprocessed, default_flow_style=False, sort_keys=False, allow_unicode=True)
        
        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(yaml_str)
                
        return yaml_str

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python3 preprocessor.py <input.ipynb> [output.yaml]")
        sys.exit(1)
        
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    preprocessor = RuleBasedPreprocessor()
    result_yaml = preprocessor.preprocess_to_yaml(input_file, output_file)
    
    if not output_file:
        print(result_yaml)
