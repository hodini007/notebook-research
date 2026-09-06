import sys
import io
import traceback
import contextlib
from typing import Dict, Any, Tuple, Optional

class NotebookSandbox:
    """
    A stateful Python execution environment for running code cells sequentially.
    Preserves variables, imports, and state across runs in a persistent namespace.
    """
    def __init__(self):
        self.namespace: Dict[str, Any] = {
            "__builtins__": __builtins__
        }
        # Pre-import common packages to simulate notebook environment
        try:
            import pandas as pd
            import numpy as np
            self.namespace["pd"] = pd
            self.namespace["np"] = np
        except ImportError:
            pass

    def execute_cell(self, code: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Executes a block of code within the persistent namespace.
        Returns:
            stdout: Standard output string
            stderr: Standard error string
            exception_tb: Exception traceback string if an error occurred, else None
        """
        stdout_buf = io.StringIO()
        stderr_buf = io.StringIO()
        exception_tb = None

        # Redirect standard outputs
        with contextlib.redirect_stdout(stdout_buf), contextlib.redirect_stderr(stderr_buf):
            try:
                # Compile code in "exec" mode to capture multi-line statements
                compiled_code = compile(code, "<notebook_cell>", "exec")
                exec(compiled_code, self.namespace)
            except Exception as e:
                # Capture traceback
                tb_lines = traceback.format_exception(type(e), e, e.__traceback__)
                exception_tb = "".join(tb_lines)

        stdout_val = stdout_buf.getvalue()
        stderr_val = stderr_buf.getvalue()

        return (
            stdout_val if stdout_val else None,
            stderr_val if stderr_val else None,
            exception_tb
        )

    def get_variables_state(self) -> Dict[str, Dict[str, Any]]:
        """
        Extracts metadata of all user-defined variables currently in the namespace.
        """
        var_state = {}
        for name, value in self.namespace.items():
            # Exclude built-ins, modules, and library aliases
            if name.startswith("_") or sys.modules.get(name) or name in ("pd", "np", "plt", "sns", "tf", "keras"):
                continue
                
            var_type = type(value).__name__
            shape = None
            
            # Extract shape or length metadata
            if hasattr(value, "shape") and isinstance(value.shape, tuple):
                shape = str(value.shape)
            elif hasattr(value, "__len__"):
                try:
                    shape = f"({len(value)},)"
                except Exception:
                    pass
                    
            var_state[name] = {
                "type": var_type,
                "shape": shape,
                "value_repr": repr(value)[:100] # Truncated representation
            }
        return var_state
