from typing import Dict, Any, List, Tuple

class VerifierAgent:
    """
    Stage 3: Verifier Agent
    Monitors execution state. Compares runtime variable states against the
    static preprocessor state expectations and flags state divergence or silenced warnings.
    """
    def __init__(self):
        # Keywords that indicate common warnings/silenced errors in data science
        self.warning_keywords = [
            "SettingWithCopyWarning",
            "RuntimeWarning",
            "UserWarning",
            "DeprecationWarning",
            "FutureWarning",
            "NaNs detected",
            "null values found",
            "divide by zero",
            "Precision loss",
            "ConvergenceWarning",
            "failed to converge"
        ]

    def verify_step(
        self,
        ec: int,
        actual_vars: Dict[str, Dict[str, Any]],
        expected_vars: Dict[str, Dict[str, Any]],
        stdout: str,
        stderr: str,
        exception: str
    ) -> Tuple[bool, List[str], bool, List[str]]:
        """
        Verifies the execution step.
        Returns:
            is_diverged: True if actual state differs from preprocessed static expectations.
            divergence_report: List of discrepancies.
            has_warnings: True if silenced warnings are detected in stdout/stderr.
            warning_report: List of warning descriptions.
        """
        divergence_report = []
        warning_report = []

        # 1. Check for runtime exception
        if exception:
            divergence_report.append(f"Cell ec={ec} raised an execution exception:\n{exception}")

        # 2. Check for State Divergence (Runtime namespace vs Static Table)
        for var_name, expected in expected_vars.items():
            # If the variable was expected to be defined by this cell or earlier
            exp_def = expected.get("defined_in", "unknown")
            if exp_def == "unknown":
                continue
                
            try:
                exp_ec = int(exp_def.replace("ec", ""))
            except ValueError:
                exp_ec = 0
                
            if ec < exp_ec:
                # Expected definition cell has not been run yet
                continue

            # Check if variable exists at runtime
            if var_name not in actual_vars:
                # If it's a ghost variable, it's expected to be missing
                if expected.get("status") != "ghost":
                    divergence_report.append(
                        f"State Divergence: Expected variable '{var_name}' to be defined (status: {expected.get('status')}), "
                        f"but it is missing from the active runtime namespace."
                    )
                continue

            actual = actual_vars[var_name]

            # Verify Type
            exp_type = expected.get("type", "unknown")
            act_type = actual.get("type", "unknown")
            if exp_type != "unknown" and exp_type != act_type:
                # Mismatch (e.g. static analyzer thought DataFrame, but runtime is ndarray)
                divergence_report.append(
                    f"Type Divergence on '{var_name}': Preprocessor expected type '{exp_type}', "
                    f"but runtime type is '{act_type}'."
                )

            # Verify Shape (if shape hint is present)
            exp_shape = expected.get("shape_hint")
            act_shape = actual.get("shape")
            if exp_shape and act_shape:
                # Clean spaces to compare shapes (e.g. (100, 5) vs (100,5))
                clean_exp = exp_shape.replace(" ", "")
                clean_act = act_shape.replace(" ", "")
                if clean_exp != clean_act:
                    divergence_report.append(
                        f"Shape Divergence on '{var_name}': Preprocessor expected shape '{exp_shape}', "
                        f"but runtime shape is '{act_shape}'."
                    )

        # 3. Check for Silenced Errors/Warnings in outputs
        combined_output = f"{stdout or ''}\n{stderr or ''}"
        for kw in self.warning_keywords:
            if kw in combined_output:
                warning_report.append(f"Silenced Warning Detected: Found '{kw}' in execution output.")

        is_diverged = len(divergence_report) > 0
        has_warnings = len(warning_report) > 0

        return is_diverged, divergence_report, has_warnings, warning_report
