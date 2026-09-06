"""
Notebook-NIAH v2 — a fair, context-bounded needle-in-a-haystack benchmark.

Supersedes the v1 benchmark (removed in commit bf6913e), whose baseline was
confounded: it let the raw condition overflow the context window and scored
that as a wrong answer.

Design goals:
  1. FAIR BASELINE: every condition is kept strictly under the model context
     limit. Context overflow is recorded as a SEPARATE outcome ("OVERFLOW"),
     never conflated with a wrong answer. A baseline can only "fail" by
     answering incorrectly while it fit in context.
  2. STATISTICAL POWER: many trials per grid cell (different seeds / needle
     values / decoys) -> we report an accuracy RATE, not a single pass/fail.
  3. DEPTH x LENGTH GRID: the classic NIAH sweep. Depth is the whole point of
     "lost in the middle"; we vary it instead of pinning it at 50%.
  4. TWO NEEDLE MODES that separate the two claims the paper makes:
       - "static"  : the variable is defined once. Tests pure RETRIEVAL under
                     noise. The literal string is identical across formats, so
                     any gain is attributable to noise/token reduction.
       - "stateful": the variable is reassigned OUT OF EXECUTION ORDER. The
                     visually-last assignment is a DECOY (low execution_count);
                     the true final value has the highest execution_count but
                     appears earlier visually. This is the only setting that
                     tests the preprocessor's unique claim (Root Cause A:
                     reconstruct execution order).
  5. A COMPRESSION CONTROL ("plain_strip"): base64 + HTML removed, code +
     text/plain kept in VISUAL order, NO reordering, NO variable table, NO
     YAML. It has ~the same low token count as "ours". If ours ~= plain_strip,
     the win is just compression. If ours > plain_strip on the stateful test,
     the structure (reordering + variable table) is what adds value.
  6. DATA-DRIVEN REPORT: the report prints the ACTUAL measured numbers and a
     neutral interpretation. No hardcoded "raw fails" narrative.

Default mode is a DRY RUN: it builds every notebook, computes real token counts,
verifies everything fits under the context limit, and prints a cost estimate --
WITHOUT calling the API. Pass --run to actually query the model.

Usage:
    python3 run_niah_v2.py                  # dry run: design + token/cost table
    python3 run_niah_v2.py --run            # execute against the API
    python3 run_niah_v2.py --run --trials 5 --mode stateful
"""

import os
import sys
import json
import argparse
import random
import re
import zlib
from statistics import mean

import yaml
import tiktoken

sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))
from preprocessor import RuleBasedPreprocessor  # noqa: E402

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# ----------------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------------
MODEL = os.environ.get("NIAH_MODEL", "gpt-4o")
MODEL_CONTEXT_LIMIT = int(os.environ.get("NIAH_CONTEXT_LIMIT", "128000"))
# Optional: point at an OpenAI-compatible third-party router (e.g. OpenRouter,
# https://openrouter.ai/api/v1) to test non-OpenAI vendors with the same
# client/prompt/grading code. Uses OPENROUTER_API_KEY when set; falls back to
# OPENAI_API_KEY + the default OpenAI endpoint otherwise.
NIAH_API_BASE = os.environ.get("NIAH_API_BASE")
# Reserve headroom for the system prompt, instructions, and the completion.
CONTEXT_RESERVE = 2000
PRICE_PER_M_INPUT = float(os.environ.get("NIAH_PRICE_PER_M", "2.50"))  # USD / 1M input tokens

# Grid axes (target RAW-JSON size in tokens x needle depth as a fraction).
TARGET_LENGTHS = [int(x) for x in os.environ["NIAH_LENGTHS"].split(",")] \
    if os.environ.get("NIAH_LENGTHS") else [8_000, 30_000, 60_000, 100_000]
DEPTHS = [float(x) for x in os.environ["NIAH_DEPTHS"].split(",")] \
    if os.environ.get("NIAH_DEPTHS") else [0.1, 0.5, 0.9]

_ENC = tiktoken.get_encoding("cl100k_base")


def ntok(text: str) -> int:
    return len(_ENC.encode(text))


# ----------------------------------------------------------------------------
# Haystack construction
# ----------------------------------------------------------------------------
_B64_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"


def _base64_bloat(rng: random.Random, size_kb: int = 4) -> str:
    body = "".join(rng.choice(_B64_CHARS) for _ in range(size_kb * 1024))
    return f"data:image/png;base64,{body}"


def _html_bloat(rows: int = 20, cols: int = 8) -> str:
    parts = ["<table><thead><tr>"]
    parts += [f"<th>column_{c}</th>" for c in range(cols)]
    parts.append("</tr></thead><tbody>")
    for r in range(rows):
        parts.append("<tr>")
        parts += [f"<td>value_{r}_{c}</td>" for c in range(cols)]
        parts.append("</tr>")
    parts.append("</tbody></table>")
    return "".join(parts)


def _filler_code_cell(idx: int, ec: int, rng: random.Random) -> dict:
    """A noisy code cell carrying a base64 plot or an HTML table (never a needle)."""
    roll = rng.random()
    if roll < 0.5:
        outputs = [{
            "output_type": "display_data",
            "data": {"image/png": _base64_bloat(rng), "text/plain": "<Figure size 640x480 with 1 Axes>"},
            "metadata": {},
        }]
        source = [f"x_{idx} = np.random.randn(100)\n", "plt.plot(x_{})\nplt.show()\n".format(idx)]
    elif roll < 0.85:
        outputs = [{
            "output_type": "execute_result",
            "execution_count": ec,
            "data": {"text/html": _html_bloat(), "text/plain": "DataFrame shape: (20, 8)"},
            "metadata": {},
        }]
        source = [f"df_{idx} = build_frame({idx})\n", f"df_{idx}.head(20)\n"]
    else:
        outputs = [{"output_type": "stream", "name": "stdout", "text": f"Finished operation {idx}\n"}]
        source = [f"z_{idx} = transform({idx})\n", f"print('Finished operation {idx}')\n"]
    return {"cell_type": "code", "execution_count": ec, "metadata": {}, "source": source, "outputs": outputs}


def build_haystack(target_tokens: int, depth: float, mode: str, seed: int):
    """
    Build a synthetic notebook whose raw-JSON size ~= target_tokens, with the
    needle placed at `depth` (fraction of cell count).

    Returns (notebook_dict, ground_truth_value, info_dict).

    mode == "static":  one assignment `target_metric_score = V`. Ground truth V.
    mode == "stateful": true assignment (highest execution_count) = V placed at
                        `depth`; a DECOY assignment (lower execution_count) with a
                        different value is placed LATER in visual order. A reader
                        that ignores execution_count and takes the visually-last
                        value gets the decoy. Ground truth is V (highest ec).
    """
    rng = random.Random(seed)
    needle_value = round(rng.uniform(0.1000, 0.9999), 4)
    decoy_value = round(rng.uniform(0.1000, 0.9999), 4)
    while abs(decoy_value - needle_value) < 1e-3:
        decoy_value = round(rng.uniform(0.1000, 0.9999), 4)

    # Grow the filler pool until we hit the target raw-JSON token budget.
    header = {
        "cell_type": "code", "execution_count": 1, "metadata": {},
        "source": ["import numpy as np\n", "import pandas as pd\n", "import matplotlib.pyplot as plt\n"],
        "outputs": [],
    }
    fillers = []
    ec = 2
    # Each filler is ~4KB base64 (~1.4k tokens) or small; overshoot then trim.
    while True:
        fillers.append(_filler_code_cell(len(fillers), ec, rng))
        ec += 1
        approx = ntok(json.dumps({"cells": [header] + fillers}))
        if approx >= target_tokens or len(fillers) > 400:
            break

    n = len(fillers)
    needle_pos = min(max(int(round(depth * n)), 0), n)  # index into filler list

    max_ec = ec  # next unused execution count; needle(s) get the highest ec values

    def assign_cell(value, ec_val, tag):
        return {
            "cell_type": "code", "execution_count": ec_val, "metadata": {},
            "source": [f"target_metric_score = {value}  # {tag}\n",
                       "print(f'Metric logged: {target_metric_score}')\n"],
            "outputs": [{"output_type": "stream", "name": "stdout",
                         "text": f"Metric logged: {value}\n"}],
        }

    cells = [header]
    if mode == "static":
        # Single assignment; highest execution count so "final" is unambiguous.
        true_cell = assign_cell(needle_value, max_ec, "final")
        for i, fc in enumerate(fillers):
            if i == needle_pos:
                cells.append(true_cell)
            cells.append(fc)
        if needle_pos >= n:
            cells.append(true_cell)
        ground_truth = needle_value

    elif mode == "stateful":
        # True final value: highest execution_count, placed at `depth`.
        # Decoy: lower execution_count, placed LATER in visual order.
        true_cell = assign_cell(needle_value, max_ec + 1, "true-final ec-high")
        decoy_cell = assign_cell(decoy_value, max_ec, "decoy ec-low")
        decoy_pos = min(needle_pos + max(1, n // 4), n)  # visually after the true cell
        for i, fc in enumerate(fillers):
            if i == needle_pos:
                cells.append(true_cell)
            if i == decoy_pos:
                cells.append(decoy_cell)
            cells.append(fc)
        if needle_pos >= n:
            cells.append(true_cell)
        if decoy_pos >= n:
            cells.append(decoy_cell)
        ground_truth = needle_value  # the highest-execution-count value
    else:
        raise ValueError(f"unknown mode {mode!r}")

    nb = {
        "cells": cells,
        "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}},
        "nbformat": 4, "nbformat_minor": 2,
    }
    info = {"needle_value": needle_value, "decoy_value": decoy_value,
            "n_cells": len(cells), "depth": depth}
    return nb, ground_truth, info


# ----------------------------------------------------------------------------
# Format transforms (the conditions under test)
# ----------------------------------------------------------------------------
def to_raw(nb: dict) -> str:
    return json.dumps(nb)


def to_plain_strip(nb: dict) -> str:
    """Compression control: base64/HTML removed, code + text/plain kept in VISUAL
    order. No reordering, no variable table, no YAML. Same token budget as ours,
    minus the structure -- so it isolates 'structure' from 'compression'."""
    parts = []
    for cell in nb.get("cells", []):
        ctype = cell.get("cell_type")
        src = cell.get("source", "")
        src = "".join(src) if isinstance(src, list) else src
        if ctype == "markdown":
            parts.append(f"# (markdown) {src.strip()}")
            continue
        if ctype != "code":
            continue
        block = [src.rstrip()]
        for out in cell.get("outputs", []):
            ot = out.get("output_type")
            if ot == "stream":
                txt = out.get("text", "")
                block.append("".join(txt) if isinstance(txt, list) else txt)
            elif ot in ("execute_result", "display_data"):
                data = out.get("data", {})
                if "text/plain" in data:  # drop image/png and text/html
                    tp = data["text/plain"]
                    block.append("".join(tp) if isinstance(tp, list) else tp)
        parts.append("\n".join(b for b in block if b).rstrip())
    return "\n\n".join(parts)


def to_ours(nb: dict, preprocessor: RuleBasedPreprocessor) -> str:
    d = preprocessor.preprocess_notebook_data(nb)
    return yaml.dump(d, default_flow_style=False, sort_keys=False, allow_unicode=True)


def to_reorder_only(nb: dict, preprocessor: RuleBasedPreprocessor) -> str:
    """Ablation: full preprocessing WITHOUT the variables table.
    ours vs reorder_only isolates the table's contribution;
    reorder_only vs plain_strip isolates reordering's contribution."""
    d = preprocessor.preprocess_notebook_data(nb)
    d.pop("variables", None)
    return yaml.dump(d, default_flow_style=False, sort_keys=False, allow_unicode=True)


def to_table_only(nb: dict, preprocessor: RuleBasedPreprocessor) -> str:
    """Ablation: variables table appended to VISUAL-order stripped cells.
    Tests whether the table's execution-count references alone can overcome
    a misleading visual order without any cell reordering."""
    d = preprocessor.preprocess_notebook_data(nb)
    table = yaml.dump({"variables": d.get("variables", {})},
                      default_flow_style=False, sort_keys=False, allow_unicode=True)
    return to_plain_strip(nb) + "\n\n" + table


_ALL_CONDITIONS = {
    "raw": to_raw,
    "plain_strip": to_plain_strip,
    "ours": to_ours,
    "reorder_only": to_reorder_only,
    "table_only": to_table_only,
}
# Optional: restrict which conditions are run (comma-separated), to cut call
# volume for rate-limited/free-tier providers. Default: all 5 (unchanged
# behavior for existing OpenAI runs).
if os.environ.get("NIAH_CONDITIONS"):
    _wanted = [c.strip() for c in os.environ["NIAH_CONDITIONS"].split(",")]
    CONDITIONS = {k: v for k, v in _ALL_CONDITIONS.items() if k in _wanted}
else:
    CONDITIONS = _ALL_CONDITIONS
NEEDS_PREPROCESSOR = {"ours", "reorder_only", "table_only"}


# ----------------------------------------------------------------------------
# Model + grading
# ----------------------------------------------------------------------------
QUESTION = (
    "A Jupyter notebook is provided below. After the notebook has been fully "
    "executed (respecting execution order, not visual top-to-bottom order), what "
    "is the final numeric value of the variable `target_metric_score`? "
    "Reply with ONLY the number."
)

SYSTEM = ("You are a precise program-state retriever. Answer with only the exact "
          "numeric value requested -- no words, no code, no explanation.")


def build_prompt(context_body: str, condition: str) -> str:
    return f"{QUESTION}\n\n--- NOTEBOOK CONTEXT ({condition}) ---\n{context_body}"


_FLOAT_RE = re.compile(r"[-+]?\d*\.\d+|\d+")


def grade(expected: float, answer: str) -> bool:
    m = _FLOAT_RE.search(answer or "")
    if not m:
        return False
    try:
        return abs(float(expected) - float(m.group())) < 1e-4
    except ValueError:
        return False


_TEMPERATURE_OK = True  # reasoning-family models only accept the default


def ask_model(client, prompt: str) -> str:
    global _TEMPERATURE_OK
    import time
    for attempt in range(6):
        kwargs = {"temperature": 0.0} if _TEMPERATURE_OK else {}
        if NIAH_API_BASE:
            # Some free-tier OpenRouter models default to reasoning enabled
            # and can exhaust a small implicit token budget on internal
            # reasoning before ever writing the answer -- give plenty of room.
            kwargs["max_tokens"] = 1024
        try:
            res = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "system", "content": SYSTEM},
                          {"role": "user", "content": prompt}],
                **kwargs,
            )
            if not res.choices:
                # OpenRouter quirk: some upstream failures (observed:
                # "Upstream error from Nvidia: Service temporarily
                # overloaded", HTTP 502) come back as a 200 response with
                # choices=None and an embedded top-level `error` field
                # instead of a raised exception. Treat this as retryable,
                # same backoff as a rate limit, rather than crashing.
                err = getattr(res, "error", None)
                time.sleep(min(15 * (2 ** attempt), 120))
                continue
            return (res.choices[0].message.content or "").strip()
        except Exception as e:
            msg = str(e)
            if _TEMPERATURE_OK and "temperature" in msg:
                _TEMPERATURE_OK = False
                continue
            # TPM rate limits: exponential backoff (100k-token prompts hit
            # per-minute caps quickly)
            if "429" in msg or "rate_limit" in msg or "RateLimit" in type(e).__name__:
                time.sleep(min(15 * (2 ** attempt), 120))
                continue
            # Google's Gemini OpenAI-compatible endpoint has a confirmed quirk:
            # hitting the free-tier requests-per-minute cap returns HTTP 400
            # "Please pass a valid API key" instead of a proper 429 -- verified
            # directly (same key succeeded immediately before and after a 60s
            # cooldown, with no change to the key or request). Treat this exact
            # message as retryable with the same backoff, not a real auth failure.
            if "Please pass a valid API key" in msg:
                time.sleep(min(20 * (2 ** attempt), 120))
                continue
            # Also observed directly: HTTP 503 "This model is currently
            # experiencing high demand" (status UNAVAILABLE) for brand-new
            # Gemini releases under free-tier load -- same treatment.
            if "UNAVAILABLE" in msg or "high demand" in msg or "503" in msg:
                time.sleep(min(20 * (2 ** attempt), 120))
                continue
            raise
    raise RuntimeError(f"ask_model: exhausted retries for {MODEL}")


# ----------------------------------------------------------------------------
# Runner
# ----------------------------------------------------------------------------
def run(mode: str, trials: int, do_run: bool):
    preprocessor = RuleBasedPreprocessor()
    client = None
    if do_run:
        from openai import OpenAI
        if NIAH_API_BASE:
            # Generic third-party OpenAI-compatible endpoint support: try an
            # explicit override first (NIAH_API_KEY), then the vendor-specific
            # keys we know about, so the same --run path works for OpenRouter
            # and for Google's Gemini OpenAI-compatible endpoint without a
            # separate code path.
            key = (os.environ.get("NIAH_API_KEY")
                   or os.environ.get("OPENROUTER_API_KEY")
                   or os.environ.get("GEMINI_API_KEY"))
            if not key:
                print("ERROR: NIAH_API_BASE is set but no API key found "
                      "(checked NIAH_API_KEY, OPENROUTER_API_KEY, GEMINI_API_KEY); cannot --run.")
                sys.exit(1)
            client = OpenAI(api_key=key, base_url=NIAH_API_BASE)
        else:
            key = os.environ.get("OPENAI_API_KEY")
            if not key:
                print("ERROR: OPENAI_API_KEY not set; cannot --run.")
                sys.exit(1)
            client = OpenAI(api_key=key)

    # results[(condition, length, depth)] = {"correct": int, "overflow": int, "n": int}
    from collections import defaultdict
    results = defaultdict(lambda: {"correct": 0, "overflow": 0, "n": 0, "toks": []})
    total_input_tokens = 0
    n_calls = 0

    limit = MODEL_CONTEXT_LIMIT - CONTEXT_RESERVE

    print("=" * 78)
    print(f"Notebook-NIAH v2  |  mode={mode}  trials={trials}  model={MODEL}")
    print(f"Context budget: prompts must be <= {limit:,} tokens ({MODEL} limit "
          f"{MODEL_CONTEXT_LIMIT:,} - {CONTEXT_RESERVE:,} reserve)")
    print("Conditions:", ", ".join(CONDITIONS))
    print("=" * 78)

    for length in TARGET_LENGTHS:
        for depth in DEPTHS:
            for t in range(trials):
                # zlib.crc32 is deterministic across processes (unlike hash(),
                # which salts strings per interpreter run)
                seed = zlib.crc32(f"{length}|{depth}|{t}|{mode}".encode())
                nb, truth, info = build_haystack(length, depth, mode, seed)

                for cond, fn in CONDITIONS.items():
                    body = fn(nb, preprocessor) if cond in NEEDS_PREPROCESSOR else fn(nb)
                    prompt = build_prompt(body, cond)
                    ptok = ntok(SYSTEM) + ntok(prompt)
                    cell = results[(cond, length, depth)]
                    cell["n"] += 1
                    cell["toks"].append(ptok)

                    if ptok > limit:
                        cell["overflow"] += 1
                        continue  # fair: overflow is not a wrong answer

                    if do_run:
                        ans = ask_model(client, prompt)
                        if grade(truth, ans):
                            cell["correct"] += 1
                        total_input_tokens += ptok
                        n_calls += 1

    _report(mode, trials, do_run, results, total_input_tokens, n_calls)


def _rate(cell):
    fit = cell["n"] - cell["overflow"]
    if fit == 0:
        return None
    return cell["correct"] / fit


def _report(mode, trials, do_run, results, total_input_tokens, n_calls):
    conds = list(CONDITIONS)

    # --- Token / fit table (always available, even in dry run) ---
    print("\n### Token usage & context-fit (avg prompt tokens per condition)\n")
    header = "| Length (raw target) | " + " | ".join(conds) + " |"
    print(header)
    print("| :--- | " + " | ".join([":---:"] * len(conds)) + " |")
    for length in TARGET_LENGTHS:
        cellvals = []
        for cond in conds:
            merged_tok = []
            overflow = 0
            n = 0
            for depth in DEPTHS:
                c = results[(cond, length, depth)]
                merged_tok += c["toks"]
                overflow += c["overflow"]
                n += c["n"]
            avg = int(mean(merged_tok)) if merged_tok else 0
            flag = "  ⚠OVERFLOW" if overflow else ""
            cellvals.append(f"{avg:,}{flag}")
        print(f"| ~{length:,} | " + " | ".join(cellvals) + " |")

    est_cost = total_input_tokens / 1e6 * PRICE_PER_M_INPUT if do_run else \
        _estimate_cost(results, trials)
    calls_planned = len(TARGET_LENGTHS) * len(DEPTHS) * trials * len(conds)
    print(f"\nPlanned model calls: {calls_planned}  "
          f"(minus any OVERFLOW-skipped)")
    print(f"Estimated input tokens billed: "
          f"{(total_input_tokens if do_run else _estimate_tokens(results, trials)):,}")
    print(f"Estimated cost @ ${PRICE_PER_M_INPUT}/M input: ${est_cost:,.2f}")

    if not do_run:
        print("\n(DRY RUN — no API calls made. Re-run with --run to measure accuracy.)")
        _write_report(mode, trials, do_run, results)
        return

    # --- Accuracy grid (depth x length) per condition ---
    for cond in conds:
        print(f"\n### Accuracy — {cond}  (rows=depth, cols=length)\n")
        print("| depth \\ length | " + " | ".join(f"{l//1000}k" for l in TARGET_LENGTHS) + " |")
        print("| :--- | " + " | ".join([":---:"] * len(TARGET_LENGTHS)) + " |")
        for depth in DEPTHS:
            cells = []
            for length in TARGET_LENGTHS:
                c = results[(cond, length, depth)]
                r = _rate(c)
                if r is None:
                    cells.append("OVERFLOW")
                else:
                    cells.append(f"{r*100:.0f}% ({c['correct']}/{c['n']-c['overflow']})")
            print(f"| {depth:.1f} | " + " | ".join(cells) + " |")

    _write_report(mode, trials, do_run, results)


def _estimate_tokens(results, trials):
    total = 0
    limit = MODEL_CONTEXT_LIMIT - CONTEXT_RESERVE
    for (cond, length, depth), c in results.items():
        total += sum(t for t in c["toks"] if t <= limit)
    return total


def _estimate_cost(results, trials):
    return _estimate_tokens(results, trials) / 1e6 * PRICE_PER_M_INPUT


def _write_report(mode, trials, do_run, results):
    conds = list(CONDITIONS)
    lines = [
        "# Notebook-NIAH v2 Report",
        "",
        f"- **Mode:** `{mode}` "
        + ("(pure retrieval under noise; needle string identical across formats)"
           if mode == "static" else
           "(state tracking: true value has highest execution_count; a decoy sits "
           "later in visual order)"),
        f"- **Trials per grid cell:** {trials}",
        f"- **Model:** {MODEL}  |  context limit {MODEL_CONTEXT_LIMIT:,} "
        f"(prompts capped at {MODEL_CONTEXT_LIMIT - CONTEXT_RESERVE:,})",
        f"- **Conditions:** {', '.join(conds)}",
        "",
        "**Fairness rule:** any prompt exceeding the context cap is recorded as "
        "`OVERFLOW`, a distinct outcome from a wrong answer. A baseline is only "
        "scored 'incorrect' when it *fit in context and still answered wrong*.",
        "",
        "## Token usage & context fit (avg prompt tokens)",
        "",
        "| Length | " + " | ".join(conds) + " |",
        "| :--- | " + " | ".join([":---:"] * len(conds)) + " |",
    ]
    for length in TARGET_LENGTHS:
        vals = []
        for cond in conds:
            toks, overflow = [], 0
            for depth in DEPTHS:
                c = results[(cond, length, depth)]
                toks += c["toks"]; overflow += c["overflow"]
            avg = int(mean(toks)) if toks else 0
            vals.append(f"{avg:,}" + (" ⚠OVERFLOW" if overflow else ""))
        lines.append(f"| ~{length:,} | " + " | ".join(vals) + " |")

    if do_run:
        for cond in conds:
            lines += ["", f"## Accuracy — `{cond}` (rows = depth, cols = length)", "",
                      "| depth \\ length | " + " | ".join(f"{l//1000}k" for l in TARGET_LENGTHS) + " |",
                      "| :--- | " + " | ".join([":---:"] * len(TARGET_LENGTHS)) + " |"]
            for depth in DEPTHS:
                cells = []
                for length in TARGET_LENGTHS:
                    c = results[(cond, length, depth)]
                    r = _rate(c)
                    cells.append("OVERFLOW" if r is None
                                 else f"{r*100:.0f}% ({c['correct']}/{c['n']-c['overflow']})")
                lines.append(f"| {depth:.1f} | " + " | ".join(cells) + " |")
        lines += [
            "",
            "## How to read this",
            "",
            "- Compare `raw` vs `ours` **only where `raw` fit in context** — that "
            "is the fair comparison the earlier version lacked.",
            "- `plain_strip` is the compression control: it has ~the same token "
            "count as `ours` but no reordering and no variable table. "
            "**If `ours` ≈ `plain_strip`, the gain is compression, not structure.** "
            "**If `ours` > `plain_strip` in `stateful` mode, execution-order "
            "reconstruction is doing real work.**",
            "- In `stateful` mode, an answer equal to the *decoy* value means the "
            "model followed visual order instead of execution order (Root Cause A).",
        ]
    else:
        lines += ["", "_(Dry run — accuracy not measured. Re-run with `--run`.)_"]

    # Mode-specific filename so static and stateful runs don't overwrite each
    # other; condition-subset runs (ablations) and non-default models get
    # their own files too
    suffix = "" if set(CONDITIONS) == {"raw", "plain_strip", "ours",
                                       "reorder_only", "table_only"} else \
        "_" + "-".join(CONDITIONS)
    if MODEL != "gpt-4o":
        suffix += "_" + MODEL.replace("/", "-")
    out = ("/home/ryn/Documents/research papaer/Jupyter_research/reports/"
           f"niah_v2_{mode}{suffix}_report.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"\nReport written to {out}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true", help="actually call the API (default: dry run)")
    ap.add_argument("--mode", choices=["static", "stateful"], default="static")
    ap.add_argument("--trials", type=int, default=3, help="trials per grid cell")
    ap.add_argument("--conditions", type=str, default=None,
                    help="comma-separated subset of conditions to run "
                         f"(available: {', '.join(CONDITIONS)})")
    args = ap.parse_args()
    if args.conditions:
        wanted = [c.strip() for c in args.conditions.split(",")]
        unknown = [c for c in wanted if c not in CONDITIONS]
        if unknown:
            print(f"ERROR: unknown condition(s): {unknown}")
            sys.exit(1)
        CONDITIONS = {k: CONDITIONS[k] for k in wanted}
    run(args.mode, args.trials, args.run)
