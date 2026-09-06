"""
Generate the paper's figures from the measured reports (single source of
truth — figures parse report markdown rather than hardcoding numbers).

Outputs PDF (vector, for LaTeX) + PNG (300dpi, for preview) per figure.

    python3 paper/figures/make_figures.py
"""
import os
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
REPORTS = os.path.join(HERE, "../../reports")

# Reference dataviz palette (validated): categorical slots 1-2, status, ink
BLUE = "#2a78d6"      # ours
ORANGE = "#eb6834"    # raw
GOOD = "#0ca30c"      # TRUTH
CRITICAL = "#d03b3b"  # DECOY
MUTED = "#898781"     # NEITHER / axis ink
GRID = "#e1e0d9"
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 9,
    "axes.edgecolor": "#c3c2b7",
    "axes.labelcolor": INK2,
    "text.color": INK,
    "xtick.color": MUTED,
    "ytick.color": INK2,
    "axes.grid": False,
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE,
})


def save(fig, name):
    for ext, dpi in (("pdf", None), ("png", 300)):
        fig.savefig(os.path.join(HERE, f"{name}.{ext}"),
                    bbox_inches="tight", dpi=dpi)
    plt.close(fig)
    print(f"wrote {name}.pdf/.png")


# ---------------------------------------------------------------- figure 1
def fig_model_curve():
    text = open(os.path.join(REPORTS, "model_curve_report.md"), encoding="utf-8").read()
    rows = []
    # Model name: any non-pipe, non-asterisk run of chars (covers gpt-*,
    # vendor/model:tag style OpenRouter IDs, etc.) -- not just gpt-*, since
    # the curve now includes non-OpenAI models.
    for m in re.finditer(r"\|\s*([^\|\*\s][^\|]*?)\s*\|\s*\*\*(\d+)%\*\*\s*\((\d+)/(\d+)\)"
                         r"\s*\|\s*\*\*\d+%\*\*[^|]*\|\s*\*\*(\d+)%\*\*", text):
        name, rawpct, _c, n, ourspct = m.groups()
        label = name.replace("-2026-03-05", " (2026-03)").replace(
            "-2026-03-17", " (2026-03)").replace(":free", " (free)")
        label = label.replace("nvidia-nemotron-3-super-120b-a12b", "nemotron-3-super-120b")
        label = label.replace("minimax-minimax-m3", "minimax-m3")
        rows.append((label, int(rawpct), int(ourspct), int(n)))
    rows.sort(key=lambda r: r[1])

    fig, ax = plt.subplots(figsize=(5.2, 3.2))
    ys = range(len(rows))
    for y, (label, rawv, oursv, n) in zip(ys, rows):
        ax.plot([rawv, oursv], [y, y], color=GRID, lw=1.5, zorder=1)
        ax.scatter([rawv], [y], s=52, color=ORANGE, zorder=3,
                   edgecolors=SURFACE, linewidths=2)
        ax.scatter([oursv], [y], s=52, color=BLUE, zorder=3,
                   edgecolors=SURFACE, linewidths=2)
        ax.annotate(f"{rawv}%", (rawv, y), textcoords="offset points",
                    xytext=(0, -11), ha="center", fontsize=7.5, color=INK2)
    ax.set_yticks(list(ys))
    ax.set_yticklabels([r[0] for r in rows], fontsize=8.5)
    ax.set_xlim(-4, 104)
    ax.set_xlabel("Stateful Notebook-NIAH accuracy (%)")
    ax.xaxis.grid(True, color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    ax.scatter([], [], s=52, color=ORANGE, label="raw .ipynb JSON")
    ax.scatter([], [], s=52, color=BLUE, label="ours (execution-order YAML)")
    ax.legend(loc="upper left", frameon=False, fontsize=8,
              bbox_to_anchor=(0, 1.14), ncols=2)
    ax.annotate("100% on every model", (100, len(rows) - 1),
                textcoords="offset points", xytext=(-8, 10), ha="right",
                fontsize=8, color=INK2, style="italic")
    save(fig, "fig1_model_curve")


# ---------------------------------------------------------------- figure 2
def fig_token_reduction():
    text = open(os.path.join(REPORTS, "real_notebook_validation_report.md"),
                encoding="utf-8").read()
    vals = [float(v) for v in re.findall(
        r"\|\s*[\d,]+\s*\|\s*[\d,]+\s*\|\s*(-?\d+\.\d)%\s*\|", text)]
    vals.sort(reverse=True)

    fig, ax = plt.subplots(figsize=(5.2, 2.6))
    colors = [BLUE] * len(vals)
    ax.bar(range(len(vals)), vals, width=0.82, color=colors,
           edgecolor=SURFACE, linewidth=0.5)
    # canonical median from the report header (full precision), not from
    # the 1-decimal table values
    med = float(re.search(r"median \*\*([\d.]+)%\*\*", text).group(1))
    ax.axhline(0, color="#c3c2b7", lw=1)
    ax.axhline(med, color=MUTED, lw=1)
    ax.annotate(f"median {med:.1f}%", (len(vals) * 0.99, med),
                ha="right", va="bottom", fontsize=8, color=INK2)
    neg = [(i, v) for i, v in enumerate(vals) if v < 0]
    for i, v in neg:
        ax.annotate(f"{v:.1f}% (grew)", (i, v), textcoords="offset points",
                    xytext=(-4, -12), ha="right", fontsize=7.5, color=INK2)
    ax.set_xticks([])
    ax.set_xlabel(f"{len(vals)} real JunoBench notebooks (sorted)")
    ax.set_ylabel("Token reduction (%)")
    ax.set_ylim(min(-8, min(vals) - 5), 104)
    ax.yaxis.grid(True, color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    save(fig, "fig2_token_reduction")


# ---------------------------------------------------------------- figure 3
def fig_real_state_outcomes():
    text = open(os.path.join(REPORTS, "real_state_eval_report.md"),
                encoding="utf-8").read()
    rows = {}
    for m in re.finditer(r"\|\s*(raw|plain_strip|ours)\s*\|\s*(\d+)\s*\|\s*(\d+)"
                         r"\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|", text):
        cond, t, d, n, o = m.group(1), *map(int, m.groups()[1:])
        rows[cond] = [t, d, n, o]

    order = ["ours", "plain_strip", "raw"]
    cats = ["TRUTH", "DECOY", "NEITHER", "OVERFLOW"]
    colors = [GOOD, CRITICAL, MUTED, "#e1e0d9"]
    n_items = sum(rows[order[0]])
    fig, ax = plt.subplots(figsize=(5.2, 1.9))
    for y, cond in enumerate(order):
        left = 0
        for val, color, cat in zip(rows[cond], colors, cats):
            if val == 0:
                continue
            ax.barh(y, val, left=left, height=0.6, color=color,
                    edgecolor=SURFACE, linewidth=2)
            if val >= 2:
                ax.annotate(str(val), (left + val / 2, y), ha="center",
                            va="center", fontsize=8,
                            color=SURFACE if color in (GOOD, CRITICAL) else INK2,
                            fontweight="bold")
            left += val
    ax.set_yticks(range(len(order)))
    ax.set_yticklabels(order, fontsize=9)
    ax.set_xlim(0, n_items * 1.03)
    ax.set_xlabel(f"{n_items} order-divergent variables (real notebooks)")
    step = 5 if n_items > 20 else 2
    ax.set_xticks(range(0, n_items + 1, step))
    ax.xaxis.grid(True, color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in colors]
    ax.legend(handles, ["TRUTH (execution-order state)", "DECOY (visual-order state)",
                        "NEITHER", "OVERFLOW"],
              loc="upper left", frameon=False, fontsize=7.5,
              bbox_to_anchor=(0, 1.45), ncols=2)
    save(fig, "fig3_real_state_outcomes")


if __name__ == "__main__":
    fig_model_curve()
    fig_token_reduction()
    fig_real_state_outcomes()
