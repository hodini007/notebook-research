import os
from typing import Dict, Any, List, Optional
from openai import OpenAI
from notebook_sandbox import NotebookSandbox
from agent_verifier import VerifierAgent

class OrchestratorAgent:
    """
    Stage 4: Orchestrator Agent
    Manages the multi-agent cell-by-cell execution loop, coordinates with the
    Verifier Agent to monitor state, and queries the LLM to handle divergences or silenced warnings.
    """
    def __init__(self, preprocessed_notebook: Dict[str, Any], openai_key: Optional[str] = None):
        self.notebook = preprocessed_notebook
        self.sandbox = NotebookSandbox()
        self.verifier = VerifierAgent()
        self.client = OpenAI(api_key=openai_key) if openai_key else None
        self.execution_log = []

    def execute_notebook(self) -> Dict[str, Any]:
        """
        Executes the preprocessed notebook cell by cell chronologically.
        Verifies variables and state after each step.
        """
        cells = self.notebook.get("cells", [])
        expected_vars = self.notebook.get("variables", {})
        
        print(f"\n[ORCHESTRATOR] Starting execution of notebook containing {len(cells)} cells.")
        print(f"[ORCHESTRATOR] Complexity Route determined: {self.notebook.get('complexity_route', 'unknown').upper()}")
        
        all_passed = True
        step_logs = []

        for idx, cell in enumerate(cells):
            ec = cell.get("ec")
            code = cell.get("code", "")
            
            # Skip unexecuted or empty code cells
            if ec is None or not code.strip():
                continue
                
            print(f"\n[ORCHESTRATOR] Executing Cell {idx+1} (Execution Count: {ec})...")
            
            # 1. Execute cell in sandbox
            stdout, stderr, exception = self.sandbox.execute_cell(code)
            actual_vars = self.sandbox.get_variables_state()
            
            # 2. Verify state with Verifier Agent
            is_diverged, div_report, has_warnings, warn_report = self.verifier.verify_step(
                ec=ec,
                actual_vars=actual_vars,
                expected_vars=expected_vars,
                stdout=stdout,
                stderr=stderr,
                exception=exception
            )
            
            step_log = {
                "cell_index": idx,
                "ec": ec,
                "code": code,
                "stdout": stdout,
                "stderr": stderr,
                "exception": exception,
                "is_diverged": is_diverged,
                "divergence_report": div_report,
                "has_warnings": has_warnings,
                "warning_report": warn_report
            }
            step_logs.append(step_log)

            # 3. Handle divergence/warnings
            if is_diverged or has_warnings:
                all_passed = False
                print(f"  [VERIFIER WARNING] State or execution anomaly detected in ec={ec}!")
                for dr in div_report:
                    print(f"    - {dr}")
                for wr in warn_report:
                    print(f"    - {wr}")

                # Query LLM to resolve divergence (if client exists)
                if self.client:
                    resolution = self._resolve_divergence_via_llm(cell, div_report, warn_report)
                    print(f"  [ORCHESTRATOR] LLM Resolution: {resolution}")
                    step_log["llm_resolution"] = resolution
                else:
                    print("  [ORCHESTRATOR] Offline mode: Halting execution on warning.")
                    break

        return {
            "success": all_passed,
            "complexity": self.notebook.get("complexity_route"),
            "steps": step_logs
        }

    def _resolve_divergence_via_llm(self, cell: Dict[str, Any], div_report: List[str], warn_report: List[str]) -> str:
        """Queries GPT-4o to resolve state discrepancies or warnings."""
        prompt = (
            f"You are the Orchestrator Agent. The Verifier Agent has reported execution warnings in the notebook cell below.\n\n"
            f"--- CRASHING/DIVERGING CELL ---\n"
            f"Execution Count: {cell.get('ec')}\n"
            f"Code:\n{cell.get('code')}\n\n"
            f"--- VERIFIER REPORTS ---\n"
            f"Divergence Report: {', '.join(div_report) if div_report else 'None'}\n"
            f"Warning Report: {', '.join(warn_report) if warn_report else 'None'}\n\n"
            f"Identify if this discrepancy is a fatal execution error (like a NameError/SyntaxError or severe mismatch) or a non-fatal warning.\n"
            f"Provide a concise summary of the issue and state whether we should: 'HALT', 'PROCEED_WITH_WARNING', or 'INJECT_FIX'."
        )
        try:
            res = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a senior data science orchestrator. Decide on execution strategy based on verifier feedback."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0
            )
            return res.choices[0].message.content.strip()
        except Exception as e:
            return f"Failed to query LLM for resolution: {e}"
