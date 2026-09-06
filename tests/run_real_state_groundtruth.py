"""
Real-notebook state ground truth: execute each out-of-order JunoBench
notebook TWICE — once in execution_count order (what really happened), once
in visual order (what a naive reader simulates) — and diff the final states.

Variables whose final value differs between the two orders are REAL-DATA
state decoys: a reader (human or LLM) following visual order gets a
provably wrong value. These become benchmark items with executable ground
truth, replacing the synthetic needle/decoy construction of NIAH stateful
mode with divergences real users actually created.

Each execution runs in a subprocess (crash isolation) inside a fresh temp
cwd (file-write containment), with per-cell timeouts (see
src/ground_truth_extractor.py). NO LLM calls. Cost: $0.

Outputs:
  tests/real_state_groundtruth.json      — benchmark items
  reports/real_state_groundtruth_report.md

Usage:
    python3 tests/run_real_state_groundtruth.py [--limit N]
"""
import os
import sys
import json
import argparse
import subprocess
import tempfile

sys.path.append(os.path.dirname(__file__))
from run_out_of_order_scan import analyze  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(HERE, "junobench_downloads")
WORKER = os.path.join(HERE, "../src/ground_truth_extractor.py")
ITEMS_PATH = os.path.join(HERE, "real_state_groundtruth.json")
REPORT_PATH = os.path.join(HERE, "../reports/real_state_groundtruth_report.md")
NOTEBOOK_TIMEOUT_S = 180
SYNTH_FLAG = [False]  # set from --synth; read by the report writer

# Volatile summaries that differ for incidental reasons (memory addresses)
def is_comparable(summary: str) -> bool:
    return " at 0x" not in summary and "<unreprable" not in summary


def find_candidates():
    """All downloaded original notebooks that are saved out of visual order."""
    candidates = []
    for root, _dirs, files in os.walk(DOWNLOAD_DIR):
        for fn in sorted(files):
            if not fn.endswith(".ipynb"):
                continue
            if fn.endswith("_fixed.ipynb") or fn.endswith("_reproduced.ipynb"):
                continue
            path = os.path.join(root, fn)
            try:
                info = analyze(path)
            except Exception:
                continue
            if info["non_monotonic"]:
                candidates.append((fn, path))
    return sorted(candidates)


def run_worker(path, order, synth=False):
    with tempfile.TemporaryDirectory(prefix="gt_run_") as tmp:
        # CUDA_VISIBLE_DEVICES=-1 forces TF/torch to skip GPU probing --
        # without it, TF's cuInit() can hard-crash (not just warn) on a
        # machine with no GPU/driver, which cost tensorflow_15.ipynb an
        # entire notebook's worth of ground truth for a fixable reason.
        env = dict(os.environ, MPLBACKEND="Agg", PYTHONHASHSEED="0",
                   CUDA_VISIBLE_DEVICES="-1")
        if synth:
            env["GT_SYNTH"] = "1"
        try:
            proc = subprocess.run(
                [sys.executable, os.path.abspath(WORKER), os.path.abspath(path), order],
                capture_output=True, text=True, timeout=NOTEBOOK_TIMEOUT_S,
                cwd=tmp, env=env)
        except subprocess.TimeoutExpired:
            return None, "notebook_timeout"
    for line in proc.stdout.splitlines():
        if line.startswith("GT_JSON:"):
            return json.loads(line[len("GT_JSON:"):]), None
    return None, f"no_output (rc={proc.returncode}, stderr tail: {proc.stderr[-200:]!r})"


def diff_states(ec_res, vis_res):
    """Return divergent variables between ec-order and visual-order finals."""
    ec_vars, vis_vars = ec_res["variables"], vis_res["variables"]
    items = []
    for name in sorted(set(ec_vars) | set(vis_vars)):
        a, b = ec_vars.get(name), vis_vars.get(name)
        if a == b:
            continue
        if a is not None and b is not None:
            if not (is_comparable(a) and is_comparable(b)):
                continue
            items.append({"variable": name, "kind": "value_divergence",
                          "ec_order_value": a, "visual_order_value": b})
        elif a is not None:
            if not is_comparable(a):
                continue
            items.append({"variable": name, "kind": "missing_in_visual",
                          "ec_order_value": a, "visual_order_value": None})
        else:
            if not is_comparable(b):
                continue
            items.append({"variable": name, "kind": "phantom_in_visual",
                          "ec_order_value": None, "visual_order_value": b})
    return items


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None,
                    help="only process the first N candidates (smoke test)")
    ap.add_argument("--synth", action="store_true",
                    help="substitute schema-inferred synthetic data for missing "
                         "files (identical input to both orders) to unblock "
                         "data-starved cells")
    args = ap.parse_args()

    SYNTH_FLAG[0] = args.synth
    candidates = find_candidates()
    if args.limit:
        candidates = candidates[:args.limit]
    print(f"Out-of-order candidates: {len(candidates)}  (synth={args.synth})")

    results, benchmark_items = [], []
    for i, (name, path) in enumerate(candidates, 1):
        print(f"[{i}/{len(candidates)}] {name} ... ", end="", flush=True)
        ec_res, ec_err = run_worker(path, "ec", synth=args.synth)
        vis_res, vis_err = run_worker(path, "visual", synth=args.synth)
        if ec_err or vis_err:
            results.append({"name": name, "status": f"failed ({ec_err or vis_err})"})
            print(f"FAILED ({ec_err or vis_err})")
            continue
        if ec_res["n_ok"] == 0 or vis_res["n_ok"] == 0:
            results.append({"name": name, "status": "no_cells_executed",
                            "ec_ok": ec_res["n_ok"], "vis_ok": vis_res["n_ok"],
                            "n_cells": ec_res["n_cells"]})
            print("no cells executed (missing deps/data)")
            continue

        items = diff_states(ec_res, vis_res)
        results.append({
            "name": name, "status": "ok", "n_cells": ec_res["n_cells"],
            "ec_ok": ec_res["n_ok"], "vis_ok": vis_res["n_ok"],
            "n_divergent": len(items),
        })
        for it in items:
            it["notebook"] = name
            benchmark_items.append(it)
        print(f"cells={ec_res['n_cells']} ok(ec)={ec_res['n_ok']} "
              f"ok(vis)={vis_res['n_ok']} divergent_vars={len(items)}")

    ok = [r for r in results if r["status"] == "ok"]
    with_div = [r for r in ok if r["n_divergent"] > 0]
    value_div = [b for b in benchmark_items if b["kind"] == "value_divergence"]

    with open(ITEMS_PATH, "w", encoding="utf-8") as f:
        json.dump(benchmark_items, f, indent=2)

    lines = [
        "# Real-Notebook State Ground Truth Report\n",
        "Each out-of-order JunoBench notebook is executed twice in a sandboxed "
        "subprocess — in `execution_count` order (truth) and in visual order "
        "(what a naive reader simulates) — with identical RNG seeds. Divergent "
        "final variables are real-data state decoys with executable ground "
        "truth. **No LLM calls.**\n",
        f"- Out-of-order candidates processed: **{len(results)}**",
        f"- Executed usefully under both orders (≥1 cell ok): **{len(ok)}**",
        f"- **Notebooks with ≥1 order-divergent variable: {len(with_div)}**",
        f"- **Total divergent variables (benchmark items): {len(benchmark_items)}**"
        f" — {len(value_div)} value divergences, "
        f"{len(benchmark_items) - len(value_div)} existence divergences",
        "",
        "A divergent variable means: reading this real notebook top-to-bottom "
        "yields a provably wrong value for it. Items: "
        "`tests/real_state_groundtruth.json`.\n",
        "## Per-notebook results\n",
        "| Notebook | Status | Cells | ok (ec) | ok (visual) | Divergent vars |",
        "| :--- | :--- | :---: | :---: | :---: | :---: |",
    ]
    for r in results:
        lines.append(
            f"| `{r['name']}` | {r['status']} | {r.get('n_cells', '—')} | "
            f"{r.get('ec_ok', '—')} | {r.get('vis_ok', '—')} | "
            f"{r.get('n_divergent', '—')} |")

    if value_div:
        lines += ["", "## Sample value divergences\n",
                  "| Notebook | Variable | EC-order (truth) | Visual-order (naive) |",
                  "| :--- | :--- | :--- | :--- |"]
        for b in value_div[:15]:
            ec_v = b["ec_order_value"].replace("|", "\\|")[:60]
            vi_v = b["visual_order_value"].replace("|", "\\|")[:60]
            lines.append(f"| `{b['notebook']}` | `{b['variable']}` | {ec_v} | {vi_v} |")

    lines += ["", "## Scope notes\n"]
    if SYNTH_FLAG[0]:
        lines += [
            "- **Data substitution is ON (`--synth`).** Real ML notebooks die at "
            "the first `read_csv` of a file that isn't bundled, and everything "
            "downstream depends on it. We monkeypatch the common pandas/numpy "
            "loaders to return a deterministic, schema-inferred synthetic frame "
            "when the real file is missing (columns inferred from the notebook's "
            "own `df['col']` subscripting).",
            "- **The substitution cannot manufacture a divergence.** The *same* "
            "synthetic input feeds *both* execution orders, so it can only "
            "*enable* a cell to run — every measured divergence is still caused "
            "by cell execution order, not by the substituted data. The divergent "
            "*value* is not the user's original value; the divergent *code path* "
            "(column reordering, type change, phantom variable) is a real "
            "property of the notebook's execution graph.",
        ]
    lines += [
        "- torch / tensorflow are not installed in the eval environment; "
        "cells importing them fail identically under both orders, which "
        "cannot create spurious divergence but does reduce coverage.",
        "- RNGs are seeded identically in both runs; remaining divergence "
        "is attributable to execution order (including order-dependent "
        "RNG stream consumption, which is itself an order effect)."]

    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print("\n" + "=" * 70)
    print(f"Usable notebooks: {len(ok)}/{len(results)}; "
          f"with divergence: {len(with_div)}; items: {len(benchmark_items)}")
    print(f"Items -> {ITEMS_PATH}")
    print(f"Report -> {REPORT_PATH}")


if __name__ == "__main__":
    main()
