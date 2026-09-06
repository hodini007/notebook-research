import unittest
import sys
import os

# Ensure src directory is in the path
sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))
from notebook_sandbox import NotebookSandbox
from agent_verifier import VerifierAgent
from agent_orchestrator import OrchestratorAgent

class TestMultiAgentLayer(unittest.TestCase):
    def test_sandbox_stateful_execution(self):
        sandbox = NotebookSandbox()
        
        # Run cell 1
        stdout, stderr, exception = sandbox.execute_cell("x = 10\nprint('hello output')")
        self.assertEqual(stdout.strip(), "hello output")
        self.assertIsNone(stderr)
        self.assertIsNone(exception)
        
        # Run cell 2 (uses variable x defined in cell 1)
        stdout, stderr, exception = sandbox.execute_cell("y = x + 5")
        self.assertIsNone(stdout)
        self.assertIsNone(stderr)
        self.assertIsNone(exception)
        
        # Verify variable state
        var_state = sandbox.get_variables_state()
        self.assertIn("x", var_state)
        self.assertIn("y", var_state)
        self.assertEqual(var_state["x"]["type"], "int")
        self.assertEqual(var_state["y"]["type"], "int")

    def test_verifier_divergence_detection(self):
        verifier = VerifierAgent()
        
        # Scenario: Expected var 'df' to be DataFrame and shape (100, 2)
        expected_vars = {
            "df": {
                "type": "DataFrame",
                "defined_in": "ec1",
                "shape_hint": "(100, 2)",
                "status": "active"
            }
        }
        
        # Actual state has type 'list' and shape None
        actual_vars = {
            "df": {
                "type": "list",
                "shape": None,
                "value_repr": "[1, 2, 3]"
            }
        }
        
        is_div, div_rep, has_warn, warn_rep = verifier.verify_step(
            ec=1,
            actual_vars=actual_vars,
            expected_vars=expected_vars,
            stdout="",
            stderr="",
            exception=None
        )
        
        self.assertTrue(is_div)
        self.assertFalse(has_warn)
        # Should report type divergence
        self.assertTrue(any("Type Divergence" in r for r in div_rep))

    def test_verifier_warning_detection(self):
        verifier = VerifierAgent()
        
        # Simulate SettingWithCopyWarning in stderr
        is_div, div_rep, has_warn, warn_rep = verifier.verify_step(
            ec=1,
            actual_vars={},
            expected_vars={},
            stdout="",
            stderr="SettingWithCopyWarning: A value is trying to be set on a copy of a slice from a DataFrame",
            exception=None
        )
        
        self.assertFalse(is_div)
        self.assertTrue(has_warn)
        self.assertTrue(any("SettingWithCopyWarning" in r for r in warn_rep))

    def test_orchestrator_execution_flow(self):
        # Build mock preprocessed notebook dict
        preprocessed_nb = {
            "complexity_route": "medium",
            "cells": [
                {
                    "ec": 1,
                    "code": "a = 100",
                    "output": None
                },
                {
                    "ec": 2,
                    "code": "b = a * 2",
                    "output": None
                }
            ],
            "variables": {
                "a": {
                    "type": "int",
                    "defined_in": "ec1",
                    "status": "active"
                },
                "b": {
                    "type": "int",
                    "defined_in": "ec2",
                    "status": "active"
                }
            }
        }
        
        # Run orchestrator in offline mode (no API key)
        orchestrator = OrchestratorAgent(preprocessed_nb, openai_key=None)
        res = orchestrator.execute_notebook()
        
        self.assertTrue(res["success"])
        self.assertEqual(res["complexity"], "medium")
        self.assertEqual(len(res["steps"]), 2)
        # Check variables in final sandbox state
        final_vars = orchestrator.sandbox.get_variables_state()
        self.assertEqual(final_vars["a"]["type"], "int")
        self.assertEqual(final_vars["b"]["type"], "int")

if __name__ == "__main__":
    unittest.main()
