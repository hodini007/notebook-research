"""
Out-of-order execution scan over ALL real JunoBench notebooks.

Two purposes:
  1. A descriptive statistic of our own: what fraction of real, in-the-wild
     crashing ML notebooks are saved with a visual order that diverges from
     their execution order? (Companion to the ~36% GitHub-wide figure in
     arXiv:2504.16180 — ours is measured on notebooks that actually crashed.)
  2. Feasibility gate for a real-notebook STATE benchmark: notebooks that are
     genuinely out-of-order are the candidate pool where raw-vs-preprocessed
     state questions have different answers.

Per notebook (visual order of executed code cells):
  - n_code / n_executed cells
  - non_monotonic: any adjacent pair where ec decreases (out-of-order save)
  - n_inversions: count of adjacent decreasing pairs
  - has_gaps: ec sequence has missing numbers (re-execution or deleted cells
    — deleted executed cells are the ghost-variable precondition)
  - max_ec vs n_executed (how much re-execution history is invisible)

NO LLM calls. Cost: $0.

Usage:
    python3 tests/run_out_of_order_scan.py
"""
import os
import sys
import json

from huggingface_hub import HfApi, hf_hub_download

REPO = "PELAB-LiU/JunoBench"
DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "junobench_downloads")
REPORT_PATH = os.path.join(os.path.dirname(__file__),
                           "../reports/out_of_order_scan_report.md")


def list_original_notebooks():
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
    return sorted(originals)


def analyze(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    cells = data.get("cells", [])
    code_cells = [c for c in cells if c.get("cell_type") == "code"]
    ecs = []
    for c in code_cells:
        ec = c.get("execution_count")
        if ec is None:
            continue
        try:
            ecs.append(int(ec))
        except (TypeError, ValueError):
            continue

    n_inversions = sum(1 for a, b in zip(ecs, ecs[1:]) if b < a)
    duplicates = len(ecs) != len(set(ecs))
    # Gaps: executed ecs missing from [1..max] means cells were re-executed
    # elsewhere or deleted after execution (ghost-variable precondition)
    missing = (max(ecs) - len(set(ecs))) if ecs else 0

    return {
        "n_code": len(code_cells),
        "n_executed": len(ecs),
        "non_monotonic": n_inversions > 0,
        "n_inversions": n_inversions,
        "has_gaps": missing > 0,
        "n_missing_ecs": missing,
        "max_ec": max(ecs) if ecs else 0,
        "duplicate_ecs": duplicates,
    }


def main():
    print("Listing original notebooks from JunoBench...")
    originals = list_original_notebooks()
    print(f"Found {len(originals)} original (crashing) notebooks.")
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    rows, failures = [], []
    for i, remote in enumerate(originals, 1):
        short = remote.split("/")[-1]
        try:
            path = hf_hub_download(repo_id=REPO, filename=remote,
                                   repo_type="dataset", local_dir=DOWNLOAD_DIR)
            info = analyze(path)
            info["name"] = short
            rows.append(info)
            flag = "OOO" if info["non_monotonic"] else ("gap" if info["has_gaps"] else "lin")
            print(f"[{i}/{len(originals)}] {short}: {flag} "
                  f"(inv={info['n_inversions']}, missing_ecs={info['n_missing_ecs']})")
        except Exception as e:
            failures.append((short, f"{type(e).__name__}: {e}"))
            print(f"[{i}/{len(originals)}] {short}: FAILED {e}")

    n = len(rows)
    ooo = [r for r in rows if r["non_monotonic"]]
    gaps = [r for r in rows if r["has_gaps"]]
    either = [r for r in rows if r["non_monotonic"] or r["has_gaps"]]
    dupes = [r for r in rows if r["duplicate_ecs"]]

    lines = [
        "# Out-of-Order Execution Scan — Real JunoBench Notebooks\n",
        "Scans every original (crashing) notebook in `PELAB-LiU/JunoBench` for "
        "divergence between visual order and execution order, and for execution-"
        "count gaps (the re-execution / ghost-variable precondition). "
        "**No LLM calls.**\n",
        f"- Notebooks analyzed: **{n}** (of {len(originals)} listed; "
        f"{len(failures)} failed to parse)",
        f"- **Non-monotonic (saved out of visual order): {len(ooo)}/{n} "
        f"({len(ooo)/n*100:.1f}%)**" if n else "",
        f"- **Execution-count gaps (re-executed or deleted cells): {len(gaps)}/{n} "
        f"({len(gaps)/n*100:.1f}%)**" if n else "",
        f"- **Either state hazard present: {len(either)}/{n} "
        f"({len(either)/n*100:.1f}%)**" if n else "",
        f"- Duplicate execution counts (multi-session saves): {len(dupes)}/{n}" if n else "",
        "",
        "These are notebooks that real users saved after real crashed sessions — "
        "the exact population an LLM debugging assistant receives.\n",
        "## Per-notebook detail (state-hazard notebooks first)\n",
        "| Notebook | Code cells | Executed | Inversions | Missing ECs | Max EC |",
        "| :--- | :---: | :---: | :---: | :---: | :---: |",
    ]
    ordered = sorted(rows, key=lambda r: (-(r["non_monotonic"] or r["has_gaps"]),
                                          -r["n_inversions"], -r["n_missing_ecs"]))
    for r in ordered:
        lines.append(f"| `{r['name']}` | {r['n_code']} | {r['n_executed']} | "
                     f"{r['n_inversions']} | {r['n_missing_ecs']} | {r['max_ec']} |")
    if failures:
        lines += ["", "## Parse failures\n"]
        lines += [f"- `{name}`: {err}" for name, err in failures]

    report = "\n".join(lines) + "\n"
    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report)

    print("\n" + "=" * 70)
    if n:
        print(f"Non-monotonic: {len(ooo)}/{n} ({len(ooo)/n*100:.1f}%)")
        print(f"EC gaps:       {len(gaps)}/{n} ({len(gaps)/n*100:.1f}%)")
        print(f"Either hazard: {len(either)}/{n} ({len(either)/n*100:.1f}%)")
    print(f"Report written to {REPORT_PATH}")


if __name__ == "__main__":
    main()
