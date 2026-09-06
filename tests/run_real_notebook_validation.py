"""
Real-notebook validation — does the preprocessor's token reduction and
robustness hold on notebooks we did NOT synthesize?

Every prior token-reduction number came from either (a) programmatically
bloated notebooks (NIAH) or (b) already-clean datasets (Themisto). This
script pulls a sample of REAL, in-the-wild ML notebooks from JunoBench
(PELAB-LiU/JunoBench on Hugging Face — notebooks that actually crashed in
real projects) and measures, per notebook:

  - raw token count (the .ipynb JSON as an LLM would receive it)
  - preprocessed token count (our YAML output)
  - token reduction %
  - complexity route chosen
  - whether preprocessing crashed or produced empty output (robustness)

NO LLM CALLS. This measures compression + robustness only, which is exactly
the claim that should generalise off synthetic data. Cost: $0.

Usage:
    python3 tests/run_real_notebook_validation.py [--n 40] [--seed 42]
"""
import os
import sys
import json
import argparse
import random
import statistics

import tiktoken
from huggingface_hub import HfApi, hf_hub_download

sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))
from preprocessor import RuleBasedPreprocessor  # noqa: E402

REPO = "PELAB-LiU/JunoBench"
DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "junobench_downloads")
REPORT_PATH = os.path.join(os.path.dirname(__file__), "../reports/real_notebook_validation_report.md")
_ENC = tiktoken.get_encoding("cl100k_base")


def ntokens(text: str) -> int:
    return len(_ENC.encode(text, disallowed_special=()))


def list_original_notebooks():
    """Return the 'original' (crashing) notebook path per benchmark folder."""
    api = HfApi()
    files = api.list_repo_files(repo_id=REPO, repo_type="dataset")
    originals = []
    for f in files:
        if not (f.endswith(".ipynb") and f.startswith("benchmark/")):
            continue
        name = f.rsplit("/", 1)[-1]
        if name.endswith("_fixed.ipynb") or name.endswith("_reproduced.ipynb"):
            continue
        originals.append(f)
    return originals


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=40, help="how many real notebooks to sample")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    pre = RuleBasedPreprocessor()

    print("Listing real notebooks from JunoBench...")
    originals = list_original_notebooks()
    random.seed(args.seed)
    if len(originals) > args.n:
        originals = random.sample(originals, args.n)
    print(f"Sampled {len(originals)} real notebooks (seed={args.seed}).")

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    rows = []
    failures = []

    for i, remote in enumerate(originals, 1):
        short = remote.split("/", 1)[1] if "/" in remote else remote
        print(f"[{i}/{len(originals)}] {short}", end=" ... ")
        try:
            path = hf_hub_download(repo_id=REPO, filename=remote, repo_type="dataset",
                                   local_dir=DOWNLOAD_DIR)
            with open(path, "r", encoding="utf-8") as f:
                raw_json = f.read()
            data = json.loads(raw_json)

            n_cells = len(data.get("cells", []))
            raw_tok = ntokens(raw_json)

            route = pre.route_complexity(data)
            yaml_out = pre.preprocess_to_yaml(path)
            pre_tok = ntokens(yaml_out)

            if not yaml_out.strip():
                raise ValueError("preprocessor produced empty output")

            reduction = (raw_tok - pre_tok) / raw_tok * 100 if raw_tok else 0.0
            rows.append({
                "name": short, "cells": n_cells, "route": route,
                "raw": raw_tok, "pre": pre_tok, "reduction": reduction,
            })
            print(f"cells={n_cells} raw={raw_tok:,} pre={pre_tok:,} "
                  f"reduction={reduction:.1f}% route={route}")
        except Exception as e:
            failures.append({"name": short, "error": f"{type(e).__name__}: {e}"})
            print(f"FAILED: {type(e).__name__}: {e}")

    write_report(rows, failures, args)


def write_report(rows, failures, args):
    n_ok = len(rows)
    n_total = n_ok + len(failures)
    reductions = [r["reduction"] for r in rows]
    raws = [r["raw"] for r in rows]
    pres = [r["pre"] for r in rows]

    route_counts = {}
    for r in rows:
        route_counts[r["route"]] = route_counts.get(r["route"], 0) + 1

    lines = []
    lines.append("# Real-Notebook Validation Report\n")
    lines.append("Runs the rule-based preprocessor over a random sample of **real, "
                 "in-the-wild ML notebooks** from JunoBench (`PELAB-LiU/JunoBench`) — "
                 "notebooks that crashed in real projects, not synthesized by us. "
                 "Measures token reduction and robustness. **No LLM calls.**\n")
    lines.append(f"- Sample: {n_total} notebooks (seed={args.seed})")
    lines.append(f"- Preprocessed without error: **{n_ok}/{n_total}** "
                 f"({n_ok/n_total*100:.0f}%)" if n_total else "- (no notebooks)")
    if reductions:
        lines.append(f"- Total raw tokens: **{sum(raws):,}** → preprocessed **{sum(pres):,}** "
                     f"(**{(sum(raws)-sum(pres))/sum(raws)*100:.1f}%** aggregate reduction)")
        lines.append(f"- Per-notebook reduction: mean **{statistics.mean(reductions):.1f}%**, "
                     f"median **{statistics.median(reductions):.1f}%**, "
                     f"min **{min(reductions):.1f}%**, max **{max(reductions):.1f}%**")
        if len(reductions) > 1:
            lines.append(f"- Std dev of reduction: **{statistics.stdev(reductions):.1f}%**")
        lines.append(f"- Complexity routes: " +
                     ", ".join(f"`{k}`={v}" for k, v in sorted(route_counts.items())))
    lines.append("")

    lines.append("## Per-notebook results\n")
    lines.append("| Notebook | Cells | Route | Raw tokens | Preprocessed | Reduction |")
    lines.append("| :--- | :---: | :---: | ---: | ---: | :---: |")
    for r in sorted(rows, key=lambda x: -x["reduction"]):
        lines.append(f"| `{r['name']}` | {r['cells']} | {r['route']} | "
                     f"{r['raw']:,} | {r['pre']:,} | {r['reduction']:.1f}% |")
    lines.append("")

    if failures:
        lines.append("## Failures (robustness)\n")
        lines.append("| Notebook | Error |")
        lines.append("| :--- | :--- |")
        for f in failures:
            lines.append(f"| `{f['name']}` | {f['error']} |")
        lines.append("")
    else:
        lines.append("## Failures (robustness)\n")
        lines.append("None — every sampled notebook preprocessed without error.\n")

    lines.append("## Notes\n")
    lines.append("- **Negative reductions are real signal, not noise:** an already-lean "
                 "notebook (little output, no base64/HTML) can grow under YAML + the "
                 "variable-state table. The min/max range above shows whether that happens.")
    lines.append("- This validates **compression + robustness only**. Whether the "
                 "reconstructed state actually helps an LLM is a separate question, "
                 "measured under a fair, context-bounded design in "
                 "`reports/niah_v2_report.md`.")

    report = "\n".join(lines)
    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report)

    print("\n" + "=" * 70)
    print(f"Preprocessed OK: {n_ok}/{n_total}")
    if reductions:
        print(f"Aggregate token reduction: {(sum(raws)-sum(pres))/sum(raws)*100:.1f}%")
        print(f"Per-notebook mean reduction: {statistics.mean(reductions):.1f}%  "
              f"(min {min(reductions):.1f}%, max {max(reductions):.1f}%)")
    print(f"Report written to {REPORT_PATH}")


if __name__ == "__main__":
    main()
