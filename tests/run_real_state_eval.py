"""
Real-notebook state evaluation — the first LLM accuracy measurement on
REAL out-of-order notebooks with EXECUTABLE ground truth.

For each order-divergent variable found by run_real_state_groundtruth.py,
ask gpt-4o for the variable's final state after the notebook's ACTUAL
execution, under three serializations of the same real notebook:

    raw          — the .ipynb JSON as-is
    plain_strip  — visual order, noise stripped (compression control)
    ours         — preprocessed YAML (execution-order reconstruction)

Grading is three-way, mirroring the NIAH decoy design but with real data:
    TRUTH   — answer matches the execution-order (ec) final state
    DECOY   — answer matches the visual-order state (naive reading)
    NEITHER — anything else
A gpt-4o-mini judge classifies each answer against the two candidate
states; every raw answer is also recorded in the report for inspection.

Fairness: prompts over the context cap are recorded OVERFLOW and excluded
from accuracy for that condition (same rule as NIAH v2).

Usage:
    python3 tests/run_real_state_eval.py [--dry]
"""
import os
import sys
import json
import math
import argparse
from collections import defaultdict

import yaml
import tiktoken
from dotenv import load_dotenv

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(HERE, "../src"))
from preprocessor import RuleBasedPreprocessor  # noqa: E402

ITEMS_PATH = os.path.join(HERE, "real_state_groundtruth.json")
DOWNLOAD_DIR = os.path.join(HERE, "junobench_downloads")
REPORT_PATH = os.path.join(HERE, "../reports/real_state_eval_report.md")
RAW_ANSWERS_PATH = os.path.join(HERE, "real_state_eval_raw_answers.json")

MODEL = "gpt-4o"
JUDGE_MODEL = "gpt-4o-mini"
CONTEXT_LIMIT = 128_000
RESERVE = 2_000
_ENC = tiktoken.get_encoding("cl100k_base")


def ntok(text):
    return len(_ENC.encode(text, disallowed_special=()))


def find_notebook(name):
    for root, _dirs, files in os.walk(DOWNLOAD_DIR):
        if name in files:
            return os.path.join(root, name)
    raise FileNotFoundError(name)


def to_plain_strip(nb):
    parts = []
    for cell in nb.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        src = cell.get("source", "")
        src = "".join(src) if isinstance(src, list) else src
        block = [src.rstrip()]
        for out in cell.get("outputs", []):
            ot = out.get("output_type")
            if ot == "stream":
                txt = out.get("text", "")
                block.append("".join(txt) if isinstance(txt, list) else txt)
            elif ot in ("execute_result", "display_data"):
                data = out.get("data", {})
                if "text/plain" in data:
                    tp = data["text/plain"]
                    block.append("".join(tp) if isinstance(tp, list) else tp)
        parts.append("\n".join(b for b in block if b).rstrip())
    return "\n\n".join(parts)


def state_description(summary):
    """Human-readable description of a captured state (or its absence)."""
    if summary is None:
        return "the variable was NEVER successfully defined (its defining code failed or never ran)"
    return summary.split(":", 1)[1] if ":" in summary else summary


QUESTION = (
    "The Jupyter notebook below was saved after a real interactive session. "
    "Cells may have been executed OUT OF the visual order — the "
    "execution_count metadata records the actual order, and some cells may "
    "have failed.\n\n"
    "Question: after the session's ACTUAL execution, what was the final "
    "state of the variable `{var}`?\n"
    "- If it was successfully assigned, describe its final value/"
    "configuration concisely.\n"
    "- If its defining code failed or never ran successfully, reply exactly: "
    "NEVER-DEFINED.\n"
    "Reply with only the final state, no explanation."
)


def ask(client, model, system, user):
    res = client.chat.completions.create(
        model=model, temperature=0.0,
        messages=[{"role": "system", "content": system},
                  {"role": "user", "content": user}])
    return (res.choices[0].message.content or "").strip()


def judge(client, item, answer):
    a_desc = state_description(item["ec_order_value"])
    b_desc = state_description(item["visual_order_value"])
    # NOTE (2026-09-05, post judge-validation audit): the original prompt
    # asked "which candidate does RESPONSE describe" with no requirement
    # that the match be literal/close. This let the judge credit ANY
    # concrete-looking answer to whichever candidate was NOT "never
    # defined", even when that answer's specific value did not match
    # either candidate (e.g. answer "cuda" credited as TRUTH against a
    # NEVER-DEFINED/"cpu" pair, in which "cuda" matches neither). A manual
    # audit of 25 sampled rows found 24% disagreement, concentrated
    # entirely in this failure mode. See reports/judge_validation_report.md.
    # The prompt below requires an explicit literal/close value match and
    # instructs the judge NOT to infer a match merely because the response
    # differs from the other candidate.
    prompt = (
        "Two candidate final states for a variable are given below. Decide "
        "which candidate (if either) the RESPONSE's specific value/content "
        "actually matches.\n\n"
        f"Candidate A: {a_desc}\n"
        f"Candidate B: {b_desc}\n"
        f"RESPONSE: {answer}\n\n"
        "Rules:\n"
        "- Choose A only if the RESPONSE's specific value/content closely "
        "matches Candidate A (or, if Candidate A says the variable was never "
        "defined, only if the RESPONSE itself states the variable was never "
        "defined / does not exist / undefined / an error prevented its "
        "creation).\n"
        "- Choose B only if the RESPONSE's specific value/content closely "
        "matches Candidate B under the same standard.\n"
        "- Do NOT choose A merely because the RESPONSE fails to match B, and "
        "do NOT choose B merely because the RESPONSE fails to match A. A "
        "concrete value that matches NEITHER candidate's specific content "
        "(even if plausible-sounding) must be graded NEITHER.\n"
        "- If uncertain, prefer NEITHER over guessing.\n\n"
        "Reply with exactly one word: A, B, or NEITHER."
    )
    verdict = ask(client, JUDGE_MODEL,
                  "You are a strict, literal-match grader. Reply A, B, or "
                  "NEITHER only.", prompt).upper()
    if verdict.startswith("A"):
        return "truth"
    if verdict.startswith("B"):
        return "decoy"
    return "neither"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true", help="no API calls; token accounting only")
    args = ap.parse_args()

    load_dotenv()
    client = None
    if not args.dry:
        from openai import OpenAI
        client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    with open(ITEMS_PATH, encoding="utf-8") as f:
        items = json.load(f)
    by_nb = defaultdict(list)
    for it in items:
        by_nb[it["notebook"]].append(it)
    print(f"{len(items)} divergent items across {len(by_nb)} notebooks")

    pre = RuleBasedPreprocessor()
    limit = CONTEXT_LIMIT - RESERVE
    rows, tallies = [], defaultdict(lambda: defaultdict(int))
    raw_answers = []
    est_tokens = 0

    for nb_name, nb_items in sorted(by_nb.items()):
        path = find_notebook(nb_name)
        with open(path, encoding="utf-8") as f:
            nb = json.load(f)
        contexts = {
            "raw": json.dumps(nb),
            "plain_strip": to_plain_strip(nb),
            "ours": yaml.dump(pre.preprocess_notebook_data(nb),
                              default_flow_style=False, sort_keys=False,
                              allow_unicode=True),
        }
        toks = {c: ntok(body) for c, body in contexts.items()}
        print(f"\n{nb_name}: tokens raw={toks['raw']:,} "
              f"plain_strip={toks['plain_strip']:,} ours={toks['ours']:,}")

        for item in nb_items:
            for cond, body in contexts.items():
                q = QUESTION.format(var=item["variable"])
                prompt = f"{q}\n\n--- NOTEBOOK ({cond}) ---\n{body}"
                ptok = ntok(prompt)
                if ptok > limit:
                    tallies[cond]["overflow"] += 1
                    rows.append({"notebook": nb_name, "variable": item["variable"],
                                 "kind": item["kind"], "condition": cond,
                                 "outcome": "OVERFLOW", "answer": f"(prompt {ptok:,} tokens)"})
                    continue
                est_tokens += ptok
                if args.dry:
                    tallies[cond]["planned"] += 1
                    continue
                answer = ask(client, MODEL,
                             "You are a precise program-state analyst.", prompt)
                outcome = judge(client, item, answer)
                tallies[cond][outcome] += 1
                rows.append({"notebook": nb_name, "variable": item["variable"],
                             "kind": item["kind"], "condition": cond,
                             "outcome": outcome.upper(), "answer": answer[:160]})
                raw_answers.append({"notebook": nb_name, "variable": item["variable"],
                                    "kind": item["kind"], "condition": cond,
                                    "outcome": outcome.upper(), "answer_full": answer,
                                    "ec_order_value": item["ec_order_value"],
                                    "visual_order_value": item["visual_order_value"]})
                print(f"  {item['variable']:<14} {cond:<12} -> {outcome.upper()}")

    # ---- report ----
    lines = [
        "# Real-Notebook State Evaluation\n",
        f"First LLM state-accuracy measurement on real out-of-order notebooks "
        f"with executable ground truth. Model: {MODEL}; three-way grading "
        f"(TRUTH = execution-order state, DECOY = visual-order state, NEITHER) "
        f"by {JUDGE_MODEL} judge; all answers recorded below.\n",
        f"- Items: {len(items)} divergent variables across {len(by_nb)} real "
        f"JunoBench notebooks (see `real_state_groundtruth_report.md`)",
        f"- Fairness: prompts over {limit:,} tokens are OVERFLOW, excluded "
        f"from that condition's accuracy",
        "",
        "## Outcome tallies\n",
        "| Condition | TRUTH | DECOY | NEITHER | OVERFLOW |",
        "| :--- | :---: | :---: | :---: | :---: |",
    ]
    for cond in ("raw", "plain_strip", "ours"):
        t = tallies[cond]
        lines.append(f"| {cond} | {t.get('truth', 0)} | {t.get('decoy', 0)} | "
                     f"{t.get('neither', 0)} | {t.get('overflow', 0)} |")

    if not args.dry:
        def wilson(k, n, z=1.96):
            if n == 0:
                return (0.0, 0.0, 0.0)
            p = k / n
            denom = 1 + z * z / n
            center = (p + z * z / (2 * n)) / denom
            half = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / denom
            return (p, max(0.0, center - half), min(1.0, center + half))

        n_items = len(items)
        lines += ["", "## Statistical summary (95% Wilson CI)\n",
                  "| Condition | Reached | TRUTH overall | TRUTH \\| reached |",
                  "| :--- | :---: | :---: | :---: |"]
        for cond in ("raw", "plain_strip", "ours"):
            t = tallies[cond]
            truth = t.get("truth", 0)
            overflow = t.get("overflow", 0)
            reached = n_items - overflow
            p_o, lo_o, hi_o = wilson(truth, n_items)
            p_r, lo_r, hi_r = wilson(truth, reached) if reached else (0.0, 0.0, 0.0)
            lines.append(
                f"| {cond} | {reached}/{n_items} ({reached / n_items:.0%}) | "
                f"{p_o:.0%} [{lo_o:.0%}, {hi_o:.0%}] | "
                f"{p_r:.0%} [{lo_r:.0%}, {hi_r:.0%}] |")
        lines += ["", "_Wilson score intervals at n={}; overlapping intervals mean the "
                  "difference between conditions is not statistically distinguishable "
                  "at this sample size — read the interpretation notes below before "
                  "citing a single winner.".format(n_items)]

    lines += ["", "## Per-item answers\n",
              "| Notebook | Variable | Kind | Condition | Outcome | Model answer |",
              "| :--- | :--- | :--- | :--- | :--- | :--- |"]
    for r in rows:
        ans = r["answer"].replace("|", "\\|").replace("\n", " ")
        lines.append(f"| `{r['notebook']}` | `{r['variable']}` | {r['kind']} | "
                     f"{r['condition']} | **{r['outcome']}** | {ans} |")
    lines += ["", "## Notes\n",
              "- n is small (this is the full population of order-divergent "
              "variables recoverable in our environment, not a sample); treat "
              "as a case-study result, not a definitive rate.",
              "- DECOY outcomes are the interesting failure: the model "
              "confidently reports the state a naive visual reading implies, "
              "which re-execution proves wrong."]

    if args.dry:
        lines += ["", f"_(Dry run — est. answer-input tokens {est_tokens:,}, "
                  f"≈${est_tokens / 1e6 * 2.5:.2f} at $2.5/M.)_"]
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    if not args.dry and raw_answers:
        with open(RAW_ANSWERS_PATH, "w", encoding="utf-8") as f:
            json.dump(raw_answers, f, indent=1)
        print(f"Full untruncated answers written to {RAW_ANSWERS_PATH}")
    print(f"\nReport written to {REPORT_PATH}")
    if args.dry:
        print(f"Estimated answer-input tokens: {est_tokens:,} "
              f"(~${est_tokens / 1e6 * 2.5:.2f})")


if __name__ == "__main__":
    main()
