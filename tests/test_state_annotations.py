"""
Unit tests for the Root Cause B/C/D/E/F static annotations.

Covers:
  B — mutation timeline (`history`) in the variables table
  C — ghost variable last-observed-value recovery from output history
  D — divergence-risk flagging (unseeded randomness, file reads, time)
  E — tolerated vs terminal error status
  F — Series length/dtype parsing from output text

Run: python3 tests/test_state_annotations.py
"""
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))
from preprocessor import RuleBasedPreprocessor  # noqa: E402


def code_cell(ec, source, outputs=None):
    return {"cell_type": "code", "execution_count": ec,
            "source": source, "outputs": outputs or [], "metadata": {}}


def stream(text):
    return {"output_type": "stream", "name": "stdout", "text": text}


def error(ename, evalue):
    return {"output_type": "error", "ename": ename, "evalue": evalue,
            "traceback": [f"{ename}: {evalue}"]}


def execute_result(text, ec):
    return {"output_type": "execute_result", "execution_count": ec,
            "data": {"text/plain": text}, "metadata": {}}


NOTEBOOK = {
    "cells": [
        # C: ghost variable — `mystery_model` is displayed but never defined
        code_cell(1, "print(mystery_model)", [stream("RandomForestClassifier(n_estimators=100)\n")]),
        # B: created + mutated in-place across cells
        code_cell(2, "df = pd.read_csv('data.csv')\ndf.head()",
                  [execute_result("   a  b\n0  1  2\n\n[100 rows x 5 columns]", 2)]),
        # E: tolerated error — cells with higher ec exist below
        code_cell(3, "1 / 0", [error("ZeroDivisionError", "division by zero")]),
        code_cell(4, "df.dropna(inplace=True)"),
        # D: unseeded split + randomness
        code_cell(5, "train, test = train_test_split(df, test_size=0.2)\n"
                     "noise = np.random.randn(10)"),
        # B: reassignment (not mutation)
        code_cell(6, "df = df[df['a'] > 0]"),
        # F: Series repr with Length/dtype footer
        code_cell(7, "s = df['a']\ns",
                  [execute_result("0    1\n1    2\nName: a, Length: 100, dtype: int64", 7)]),
        # E: terminal error — highest execution count
        code_cell(8, "raise RuntimeError('boom')", [error("RuntimeError", "boom")]),
    ],
    "metadata": {}, "nbformat": 4, "nbformat_minor": 2,
}


def main():
    pre = RuleBasedPreprocessor()
    result = pre.preprocess_notebook_data(NOTEBOOK)
    cells = result["cells"]
    variables = result["variables"]
    by_ec = {c.get("ec"): c for c in cells if c.get("ec") is not None}
    failures = []

    def check(name, cond, detail=""):
        status = "PASS" if cond else "FAIL"
        print(f"[{status}] {name}" + (f"  ({detail})" if detail and not cond else ""))
        if not cond:
            failures.append(name)

    # --- E: tolerated vs terminal ---
    check("E: ec=3 error marked tolerated",
          "tolerated" in by_ec[3].get("error_status", ""),
          f"got {by_ec[3].get('error_status')!r}")
    check("E: ec=8 error marked terminal",
          "terminal" in by_ec[8].get("error_status", ""),
          f"got {by_ec[8].get('error_status')!r}")

    # --- D: divergence risks ---
    risks5 = by_ec[5].get("divergence_risk", [])
    check("D: unseeded train_test_split flagged",
          any("train_test_split" in r for r in risks5), f"got {risks5}")
    check("D: np.random flagged",
          any("random" in r for r in risks5), f"got {risks5}")
    risks2 = by_ec[2].get("divergence_risk", [])
    check("D: read_csv flagged as external read",
          any("external" in r for r in risks2), f"got {risks2}")
    check("D: pure cells not flagged", "divergence_risk" not in by_ec[6])

    # --- B: mutation timeline ---
    df_hist = variables.get("df", {}).get("history", [])
    check("B: df has a history", bool(df_hist), f"df entry: {variables.get('df')}")
    check("B: history records in-place mutation (dropna)",
          any("mutated" in h and "dropna" in h for h in df_hist), f"got {df_hist}")
    check("B: history records reassignment at ec6",
          any("reassigned ec6" in h for h in df_hist), f"got {df_hist}")

    # --- C: ghost last-observed value ---
    ghost = variables.get("mystery_model", {})
    check("C: mystery_model detected as ghost", ghost.get("status") == "ghost",
          f"got {ghost}")
    check("C: ghost value recovered from output",
          "RandomForestClassifier" in ghost.get("last_observed_value", ""),
          f"got {ghost.get('last_observed_value')!r}")
    check("C: no origin invented", ghost.get("defined_in") == "unknown",
          f"got {ghost.get('defined_in')!r}")

    # --- F: Series shape parsing ---
    s_entry = variables.get("s", {})
    check("F: Series length+dtype parsed",
          "100" in s_entry.get("shape_hint", "") and "int64" in s_entry.get("shape_hint", ""),
          f"got {s_entry.get('shape_hint')!r}")

    print()
    if failures:
        print(f"{len(failures)} FAILURE(S): {failures}")
        sys.exit(1)
    print("All annotation tests passed.")


if __name__ == "__main__":
    main()
