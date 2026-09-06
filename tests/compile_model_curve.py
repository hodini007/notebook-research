"""
Compile all stateful NIAH runs into a single cross-model capability curve.

Parses every reports/niah_v2_stateful*_report.md, extracts per-condition
"(correct/n)" cells, and aggregates them into one table:

    model | raw | plain_strip | ours   (aggregate over the depth x length grid)

Usage:
    python3 tests/compile_model_curve.py
"""
import os
import re
import glob

HERE = os.path.dirname(os.path.abspath(__file__))
REPORTS = os.path.join(HERE, "../reports")
OUT = os.path.join(REPORTS, "model_curve_report.md")

CELL_RE = re.compile(r"(\d+)%\s*\((\d+)/(\d+)\)")
COND_HDR_RE = re.compile(r"##+\s*Accuracy\s+—\s*`?(\w+)`?")


def parse_report(path):
    """Return {condition: (correct, n)} aggregated over the grid."""
    conds = {}
    current = None
    with open(path, encoding="utf-8") as f:
        for line in f:
            m = COND_HDR_RE.search(line)
            if m:
                current = m.group(1)
                conds.setdefault(current, [0, 0])
                continue
            if current and line.lstrip().startswith("|"):
                for _pct, c, n in CELL_RE.findall(line):
                    conds[current][0] += int(c)
                    conds[current][1] += int(n)
    return {k: tuple(v) for k, v in conds.items() if v[1] > 0}


def model_of(path):
    """Extract the model name from a niah_v2_{mode}[_conditions][_model]_report.md
    filename. Handles any model/vendor name (not just gpt-*), since non-OpenAI
    models (e.g. via OpenRouter) use arbitrary vendor/model-name strings."""
    base = os.path.basename(path)
    remainder = re.sub(r"^niah_v2_(?:stateful|static)", "", base)
    remainder = re.sub(r"_report\.md$", "", remainder)
    remainder = remainder.lstrip("_")
    known_cond_prefixes = ["raw-plain_strip-ours", "reorder_only-table_only"]
    for prefix in known_cond_prefixes:
        if remainder == prefix:
            return "gpt-4o"
        if remainder.startswith(prefix + "_"):
            remainder = remainder[len(prefix) + 1:]
            break
    return remainder if remainder else "gpt-4o"


def fmt(cell):
    if cell is None:
        return "—"
    c, n = cell
    return f"**{c / n * 100:.0f}%** ({c}/{n})"


def main():
    rows = {}
    for path in sorted(glob.glob(os.path.join(REPORTS, "niah_v2_stateful*_report.md"))):
        if "reorder_only" in path or "table_only" in path:
            continue  # ablations tracked separately
        conds = parse_report(path)
        if not conds:
            continue
        model = model_of(path)
        entry = rows.setdefault(model, {})
        for cond, cell in conds.items():
            # Prefer the run with more trials if a model appears twice
            if cond not in entry or cell[1] > entry[cond][1]:
                entry[cond] = cell

    order = sorted(rows, key=lambda m: (m != "gpt-4o", m))
    lines = [
        "# Cross-Model Capability Curve — Stateful Notebook-NIAH\n",
        "Aggregate accuracy over the full depth × length grid (fair, "
        "context-bounded; identical prompts across models). `raw` measures "
        "unaided out-of-order state resolution; `ours` measures it after "
        "execution-order reconstruction.\n",
        "| Model | raw | plain_strip | ours |",
        "| :--- | :---: | :---: | :---: |",
    ]
    for model in order:
        e = rows[model]
        lines.append(f"| {model} | {fmt(e.get('raw'))} | "
                     f"{fmt(e.get('plain_strip'))} | {fmt(e.get('ours'))} |")
    lines += [
        "",
        "_Compiled automatically from the per-model reports in this "
        "directory; per-cell grids and findings live there._",
    ]
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"{len(rows)} models compiled -> {OUT}")


if __name__ == "__main__":
    main()
