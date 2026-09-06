import unittest
import sys
import os
import json
import ast

# Ensure src directory is in the path
sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))

from preprocessor import strip_ansi, clean_source, RuleBasedPreprocessor
from state_extractor import VariableStateExtractor, ASTVisitor

class TestPreprocessorStage1(unittest.TestCase):
    """Unit tests for Stage 1 Preprocessor (Rule-Based)."""

    def test_strip_ansi(self):
        ansi_text = "\u001b[0;31mValueError\u001b[0m: Something went wrong!"
        self.assertEqual(strip_ansi(ansi_text), "ValueError: Something went wrong!")

    def test_clean_source(self):
        self.assertEqual(clean_source(["a = 1\n", "b = 2"]), "a = 1\nb = 2")
        self.assertEqual(clean_source("x = 10"), "x = 10")

    def test_mime_bundle_cleaning(self):
        preprocessor = RuleBasedPreprocessor()
        
        # Test bundle with redundant MIME and base64 image
        data = {
            "text/plain": "DataFrame Description",
            "text/html": "<table>DataFrame</table>",
            "image/png": "iVBORw0KGgoAAAANS..."
        }
        cleaned = preprocessor._clean_mime_bundle(data)
        # Should only keep text/plain
        self.assertEqual(cleaned, "DataFrame Description")
        
        # Test bundle without text/plain but with other types (excluding images)
        data_no_plain = {
            "text/html": "<table>DataFrame</table>",
            "application/json": '{"a": 1}'
        }
        cleaned_no_plain = preprocessor._clean_mime_bundle(data_no_plain)
        # Should fall back to non-html/latex text representations
        self.assertEqual(cleaned_no_plain, '{"a": 1}')

    def test_process_outputs(self):
        preprocessor = RuleBasedPreprocessor()
        
        # 1. Test error output processing
        error_output = [
            {
                "output_type": "error",
                "ename": "TypeError",
                "evalue": "unsupported operand type",
                "traceback": ["\u001b[1;31mTypeError\u001b[0m: unsupported operand type"]
            }
        ]
        text, out_type = preprocessor._process_outputs(error_output)
        self.assertEqual(out_type, "error")
        self.assertIn("TypeError: unsupported operand type", text)

        # 2. Test execute_result outputs
        execute_outputs = [
            {
                "output_type": "execute_result",
                "execution_count": 5,
                "data": {"text/plain": "Result Value"},
                "metadata": {}
            }
        ]
        text, out_type = preprocessor._process_outputs(execute_outputs)
        self.assertEqual(out_type, "text")
        self.assertEqual(text, "Result Value")

    def test_sort_cells(self):
        preprocessor = RuleBasedPreprocessor()
        
        cells = [
            {"type": "markdown", "markdown": "Header 2", "_orig_idx": 0},
            {"type": "code", "ec": 2, "code": "y = 20", "_orig_idx": 1},
            {"type": "markdown", "markdown": "Header 1", "_orig_idx": 2},
            {"type": "code", "ec": 1, "code": "x = 10", "_orig_idx": 3},
            {"type": "code", "ec": None, "code": "z = 30", "_orig_idx": 4}
        ]
        
        sorted_cells = preprocessor._sort_cells(cells)
        
        # Expected sorted sequence (indices):
        # 1. Cell at original index 2 (Markdown Associated with ec=1)
        # 2. Cell at original index 3 (Code, ec=1)
        # 3. Cell at original index 0 (Markdown Associated with ec=2)
        # 4. Cell at original index 1 (Code, ec=2)
        # 5. Cell at original index 4 (Code, ec=None, unexecuted at the end)
        expected_indices = [2, 3, 0, 1, 4]
        actual_indices = [c["_orig_idx"] for c in sorted_cells]
        self.assertEqual(actual_indices, expected_indices)


class TestPreprocessorStage2(unittest.TestCase):
    """Unit tests for Stage 2 Preprocessor (State Extraction)."""

    def test_ast_visitor(self):
        code = "import pandas as pd\nfrom numpy import array\nx = 10\ny, z = 20, 30\nprint(x + y)"
        tree = ast.parse(code)
        visitor = ASTVisitor()
        visitor.visit(tree)
        
        # Verify imports
        self.assertIn("pd", visitor.imported_names)
        self.assertIn("array", visitor.imported_names)
        
        # Verify definitions
        self.assertIn("x", visitor.defined_names)
        self.assertIn("y", visitor.defined_names)
        self.assertIn("z", visitor.defined_names)
        
        # Verify uses (should refer to names read but not defined previously in the block)
        # pd, numpy/array, and print are either imported or builtins, so not local reads.
        # x and y are assigned before read, so they are not in visitor.used_names.
        # If we read an unassigned variable 'unbound':
        code_unbound = "print(unbound)"
        tree_unbound = ast.parse(code_unbound)
        visitor_unbound = ASTVisitor()
        visitor_unbound.visit(tree_unbound)
        self.assertIn("unbound", visitor_unbound.used_names)

    def test_state_extractor(self):
        extractor = VariableStateExtractor()
        
        # Mock cells representing chronologically executed notebook
        cells = [
            {
                "ec": 1,
                "code": "df = pd.read_csv('dataset.csv')",
                "output": "   col1\n0     1\n1     2\n[2 rows x 1 columns]",
                "output_type": "text",
                "type": "code"
            },
            {
                "ec": 2,
                "code": "df.dropna(inplace=True)\nprint(df.shape)",
                "output": "(1, 1)",
                "output_type": "text",
                "type": "code"
            },
            {
                "ec": 3,
                "code": "model.predict(df)  # model is not defined!",
                "output": None,
                "output_type": None,
                "type": "code"
            }
        ]
        
        variables = extractor.extract_state(cells)
        
        # Verify df state
        self.assertIn("df", variables)
        self.assertEqual(variables["df"]["type"], "DataFrame")
        self.assertEqual(variables["df"]["defined_in"], "ec1")
        self.assertEqual(variables["df"]["last_modified"], "ec2")
        self.assertEqual(variables["df"]["shape_hint"], "(1, 1)")
        self.assertEqual(variables["df"]["status"], "active")
        
        # Verify ghost detection for 'model'
        self.assertIn("model", variables)
        self.assertEqual(variables["model"]["status"], "ghost")
        self.assertEqual(variables["model"]["confidence"], "low")

    def test_complexity_routing(self):
        preprocessor = RuleBasedPreprocessor()
        
        # 1. Simple notebook
        nb_simple = {
            "cells": [
                {"cell_type": "code", "execution_count": 1, "source": ["x = 10"]},
                {"cell_type": "code", "execution_count": 2, "source": ["y = x + 5"]}
            ]
        }
        self.assertEqual(preprocessor.route_complexity(nb_simple), "simple")

        # 2. Medium notebook (out-of-order execution, cell count <= 30, no mutations)
        nb_medium = {
            "cells": [
                {"cell_type": "code", "execution_count": 2, "source": ["y = x + 5"]},
                {"cell_type": "code", "execution_count": 1, "source": ["x = 10"]}
            ]
        }
        self.assertEqual(preprocessor.route_complexity(nb_medium), "medium")

        # 3. Complex notebook (has mutations)
        nb_complex = {
            "cells": [
                {"cell_type": "code", "execution_count": 1, "source": ["df = pd.DataFrame()"]},
                {"cell_type": "code", "execution_count": 2, "source": ["df.dropna(inplace=True)"]}
            ]
        }
        self.assertEqual(preprocessor.route_complexity(nb_complex), "complex")

    def test_basic_vs_full_mode(self):
        extractor = VariableStateExtractor()
        cells = [
            {
                "ec": 1,
                "code": "df = pd.read_csv('data.csv')",
                "output": "   col1\n0     1\n[1 rows x 1 columns]",
                "output_type": "text",
                "type": "code"
            },
            {
                "ec": 2,
                "code": "print(ghost_var)",
                "output": None,
                "output_type": None,
                "type": "code"
            }
        ]
        
        # Test basic mode
        vars_basic = extractor.extract_state(cells, mode="basic")
        self.assertIn("df", vars_basic)
        self.assertEqual(vars_basic["df"]["defined_in"], "ec1")
        self.assertEqual(vars_basic["df"]["type"], "unknown")  # Skipped type inference
        self.assertNotIn("shape_hint", vars_basic["df"])       # Skipped shape inference
        self.assertNotIn("ghost_var", vars_basic)             # Skipped ghost variable tracking
        
        # Test full mode
        vars_full = extractor.extract_state(cells, mode="full")
        self.assertIn("df", vars_full)
        self.assertEqual(vars_full["df"]["type"], "DataFrame")
        self.assertEqual(vars_full["df"]["shape_hint"], "(1, 1)")
        self.assertIn("ghost_var", vars_full)
        self.assertEqual(vars_full["ghost_var"]["status"], "ghost")

if __name__ == "__main__":
    unittest.main()

