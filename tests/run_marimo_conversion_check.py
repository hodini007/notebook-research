"""
Marimo conversion-reliability experiment.

Question: is converting existing, messy, real-world .ipynb files to marimo's
reactive format (as an alternative to this project's static preprocessing
approach) reliable at scale on the population this project actually targets
(real crashed ML notebooks), or does it introduce its own failure modes?

No source found during the feasibility research (outputs/notebook-preprocessor-
feasibility.md) had evaluated marimo's Jupyter-to-marimo conversion at scale on
messy/crashed real-world notebooks -- this is a novel, cheap, directly
testable data point using tooling already in hand ($0, no LLM calls, marimo's
own official CLI: `marimo convert` and `marimo export html`).

Method, per notebook:
  1. `marimo convert <nb>.ipynb -o <nb>.py`  (bounded timeout)
     -> CONVERT_FAILED (nonzero exit / exception) or CONVERT_OK
  2. If CONVERT_OK: verify the output is syntactically valid Python (ast.parse)
     and contains at least one `@app.cell` marker (i.e. real conversion, not
     a silent no-op).
  3. `marimo export html <nb>.py -o <nb>.html`  (bounded timeout) -- this
     actually EXECUTES the notebook reactively and is the closest marimo-native
     equivalent to this project's own dual-order re-execution ground-truth
     step.
     -> EXPORT_CRASHED (nonzero exit / no html produced)
     -> EXPORT_OK_WITH_CELL_FAILURES (html produced, but marimo reports one or
        more cells raised an exception during the reactive run -- most
        commonly missing local data files, the same "missing deps/data"
        failure mode this project's own ground-truth extractor already
        documents for the identical notebooks)
     -> EXPORT_OK_CLEAN (html produced, no reported cell failures)

Uses the same deterministic 40-notebook sample (seed=42) as
reports/real_notebook_validation_report.md for direct comparability.

Usage:
    python3 tests/run_marimo_conversion_check.py [--limit N] [--timeout SECS]
"""
import argparse
import ast
import os
import random
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(HERE, "junobench_downloads", "benchmark")
REPORT_PATH = os.path.join(HERE, "../reports/marimo_conversion_report.md")

CONVERT_TIMEOUT_S = 45
EXPORT_TIMEOUT_S = 90


def sample_notebooks(limit=None):
    """Same seed=42 sampling logic as run_real_notebook_validation.py, over
    all .ipynb files under junobench_downloads/benchmark, so the notebook set
    matches reports/real_notebook_validation_report.md exactly."""
    all_nbs = []
    for root, _dirs, files in os.walk(DOWNLOAD_DIR):
        for fn in sorted(files):
            if fn.endswith(".ipynb") and not fn.endswith(("_fixed.ipynb", "_fixed2.ipynb", "_reproduced.ipynb")):
                all_nbs.append(os.path.join(root, fn))
    random.seed(42)
    sample = random.sample(all_nbs, min(40, len(all_nbs)))
    sample.sort()
    if limit:
        sample = sample[:limit]
    return sample


def run(cmd, cwd, timeout):
    try:
        proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                               timeout=timeout)
        return proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired:
        return None, "", "TIMEOUT"


def check_one(nb_path, tmpdir, convert_timeout, export_timeout):
    name = os.path.basename(nb_path)
    py_path = os.path.join(tmpdir, name.replace(".ipynb", ".py"))
    html_path = os.path.join(tmpdir, name.replace(".ipynb", ".html"))

    rc, out, err = run([sys.executable, "-m", "marimo", "convert", nb_path,
                        "-o", py_path], tmpdir, convert_timeout)
    if rc is None:
        return {"name": name, "stage": "convert", "outcome": "CONVERT_TIMEOUT"}
    if rc != 0 or not os.path.exists(py_path):
        return {"name": name, "stage": "convert", "outcome": "CONVERT_FAILED",
                "detail": (err or out)[-300:]}

    src = open(py_path, encoding="utf-8").read()
    try:
        ast.parse(src)
    except SyntaxError as e:
        return {"name": name, "stage": "convert", "outcome": "CONVERT_INVALID_SYNTAX",
                "detail": str(e)}
    n_cells = src.count("@app.cell")
    if n_cells == 0:
        return {"name": name, "stage": "convert", "outcome": "CONVERT_NO_CELLS"}

    rc, out, err = run([sys.executable, "-m", "marimo", "export", "html",
                        py_path, "-o", html_path], tmpdir, export_timeout)
    if rc is None:
        return {"name": name, "stage": "export", "outcome": "EXPORT_TIMEOUT",
                "n_cells": n_cells}
    combined = (out or "") + (err or "")
    if not os.path.exists(html_path):
        return {"name": name, "stage": "export", "outcome": "EXPORT_CRASHED",
                "n_cells": n_cells, "detail": combined[-300:]}
    n_failures = combined.count("MarimoExceptionRaisedError")
    if "some cells failed to execute" in combined or n_failures > 0:
        return {"name": name, "stage": "export", "outcome": "EXPORT_OK_WITH_CELL_FAILURES",
                "n_cells": n_cells, "n_cell_failures": n_failures}
    return {"name": name, "stage": "export", "outcome": "EXPORT_OK_CLEAN",
            "n_cells": n_cells}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--convert-timeout", type=int, default=CONVERT_TIMEOUT_S)
    ap.add_argument("--export-timeout", type=int, default=EXPORT_TIMEOUT_S)
    args = ap.parse_args()

    notebooks = sample_notebooks(args.limit)
    print(f"{len(notebooks)} notebooks (seed=42 sample, matching "
          f"real_notebook_validation_report.md)")

    results = []
    with tempfile.TemporaryDirectory(prefix="marimo_check_") as tmpdir:
        for i, nb in enumerate(notebooks, 1):
            print(f"[{i}/{len(notebooks)}] {os.path.basename(nb)} ... ", end="", flush=True)
            r = check_one(nb, tmpdir, args.convert_timeout, args.export_timeout)
            results.append(r)
            print(r["outcome"])

    from collections import Counter
    counts = Counter(r["outcome"] for r in results)

    convert_ok = sum(1 for r in results if r["outcome"] not in
                      ("CONVERT_FAILED", "CONVERT_TIMEOUT", "CONVERT_INVALID_SYNTAX", "CONVERT_NO_CELLS"))
    export_attempted = sum(1 for r in results if r["stage"] == "export")
    export_crashed = counts.get("EXPORT_CRASHED", 0) + counts.get("EXPORT_TIMEOUT", 0)
    export_ok_any = counts.get("EXPORT_OK_WITH_CELL_FAILURES", 0) + counts.get("EXPORT_OK_CLEAN", 0)

    lines = [
        "# Marimo Conversion-Reliability Experiment\n",
        "Tests whether marimo's official Jupyter-to-marimo conversion "
        "(`marimo convert`) and reactive execution (`marimo export html`) "
        "are reliable at scale on real, messy, crashed ML notebooks -- the "
        "same population this project's own preprocessing/ground-truth work "
        "targets. **No source found during the feasibility research "
        "(`outputs/notebook-preprocessor-feasibility.md`) had evaluated this "
        "at scale; this is a novel, $0, no-LLM-cost data point.**\n",
        f"- Notebooks tested: **{len(notebooks)}** (seed=42 sample, matching "
        "`reports/real_notebook_validation_report.md` exactly, for direct "
        "comparability)",
        f"- `marimo convert` succeeded (valid Python, ≥1 `@app.cell`): "
        f"**{convert_ok}/{len(notebooks)}**",
        f"- Of those, `marimo export html` (full reactive execution) "
        f"completed without crashing: **{export_ok_any}/{export_attempted}**",
        f"- `marimo export html` crashed or timed out entirely: "
        f"**{export_crashed}/{export_attempted}**",
        "",
        "## Outcome breakdown\n",
        "| Outcome | Count |",
        "| :--- | :---: |",
    ]
    for k in ("CONVERT_FAILED", "CONVERT_TIMEOUT", "CONVERT_INVALID_SYNTAX",
              "CONVERT_NO_CELLS", "EXPORT_TIMEOUT", "EXPORT_CRASHED",
              "EXPORT_OK_WITH_CELL_FAILURES", "EXPORT_OK_CLEAN"):
        if counts.get(k):
            lines.append(f"| {k} | {counts[k]} |")

    lines += ["", "## Per-notebook results\n",
              "| Notebook | Stage | Outcome | Detail |",
              "| :--- | :--- | :--- | :--- |"]
    for r in results:
        detail = r.get("detail", "").replace("|", "\\|").replace("\n", " ")[:120]
        n_fail = r.get("n_cell_failures")
        if n_fail:
            detail = f"{n_fail} cell(s) raised an exception during execution"
        lines.append(f"| `{r['name']}` | {r['stage']} | **{r['outcome']}** | {detail} |")

    lines += ["", "## Interpretation\n",
              "- `marimo convert` reliability measures whether the format "
              "translation itself is robust to real, messy notebook code "
              "(magics, unusual syntax, non-monotonic structure).",
              "- `EXPORT_OK_WITH_CELL_FAILURES` is expected and not a "
              "marimo-specific weakness: these notebooks are real crashed "
              "sessions, and the same cells fail for the same reasons "
              "(missing local data files, undefined names from deleted "
              "cells) whether executed via marimo's reactive graph or via "
              "this project's own dual-order re-execution "
              "(`src/ground_truth_extractor.py`). What matters is whether "
              "conversion or reactive execution *introduces new* failures "
              "beyond what the original notebook already had.",
              "- This experiment measures reliability of the *tooling*, not "
              "whether marimo's execution-order guarantee is more accurate "
              "than this project's static reconstruction -- that would "
              "require comparing marimo's final variable states against the "
              "same executable ground truth used in "
              "`reports/real_state_groundtruth_report.md`, which was not "
              "attempted here."]

    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print("\n" + "=" * 70)
    print(f"Convert OK: {convert_ok}/{len(notebooks)}; "
          f"Export OK (any): {export_ok_any}/{export_attempted}; "
          f"Export crashed/timeout: {export_crashed}/{export_attempted}")
    print(f"Report -> {REPORT_PATH}")


if __name__ == "__main__":
    main()
