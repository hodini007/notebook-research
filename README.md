# JupPreprocessor

**The Notebook You Read Is Not the Notebook That Ran: Execution-Order Reconstruction for LLM Understanding of Jupyter Notebooks**

MD. Raiyan Bin Rafique — Department of Computer Science and Engineering, Rajshahi University of Engineering and Technology, Rajshahi, Bangladesh (`raiyanrohit10@gmail.com`)

Manuscript submitted to *Empirical Software Engineering* (Springer). The full manuscript source is at [`paper/main.tex`](paper/main.tex) / [`paper/main.pdf`](paper/main.pdf).

## One-line summary

Jupyter `.ipynb` files store cells in *visual* order, which routinely diverges from the *execution* order they actually ran in, and their raw JSON wastes most of its tokens on base64 images, redundant MIME bundles, and metadata. This repository contains **JupPreprocessor** — a deterministic, zero-LLM-cost serializer that reconstructs execution order and strips token waste while flagging (not guessing at) the state information that genuinely cannot be recovered from a cold file — and every script and measured result behind the paper's empirical claims.

## Research Questions

This project is organized around five research questions, each mapped to a specific experiment, script, and section of the manuscript:

| # | Research Question | Manuscript section | Reproducing script(s) | Result artifact |
|---|---|---|---|---|
| **RQ1** | How prevalent are non-linear execution and other state hazards in real, crashed machine-learning Jupyter notebooks — the population most likely to be handed to an LLM for debugging? | §5.3 *State hazards are the norm in the debugging population* | `tests/run_out_of_order_scan.py` | `reports/out_of_order_scan_report.md` |
| **RQ2** | Does execution-order reconstruction measurably improve LLM state-tracking accuracy on a fair, context-bounded synthetic benchmark, isolated from mere retrieval-under-noise and from token-count confounds? | §5.2 *Fair Notebook-NIAH* | `tests/run_niah_v2.py`, `tests/compile_model_curve.py` | `reports/niah_v2_*_report.md`, `reports/model_curve_report.md`, `paper/figures/fig1_model_curve.*` |
| **RQ3** | Does this synthetic-benchmark advantage transfer to real, messy notebooks, when measured against *executable* ground truth rather than assumed correctness? | §5.4 *Executable ground truth on real notebooks*, §5.5 *Judge validation* | `tests/run_real_state_groundtruth.py`, `tests/run_real_state_eval.py` | `reports/real_state_groundtruth_report.md`, `reports/real_state_eval_report.md`, `reports/judge_validation_report.md`, `paper/figures/fig3_real_state_outcomes.*` |
| **RQ4** | What is the token-cost/robustness profile of the preprocessing pipeline on real notebooks, and does adding state-safety annotations erode the token savings? | §5.1 *Compression and robustness on real notebooks* | `tests/run_real_notebook_validation.py`, `src/measure_token_reduction.py` | `reports/real_notebook_validation_report.md`, `reports/token_reduction_report.md` |
| **RQ5** | Where does the approach fail or reach its limits — on already-clean data (Themisto), in the preprocessor's own core execution-order-sort mechanism, and relative to alternative architectures (reactive/dataflow notebooks)? | §5.6 *Honest negatives*, §6 *Threats to Validity*, §7 *Related Work* (marimo comparison) | `tests/run_themisto_eval.py`, `tests/run_execution_count_consistency_scan.py`, `tests/run_marimo_conversion_check.py` | `reports/themisto_report.md`, `reports/themisto_failure_mode_breakdown.md`, `reports/execution_count_consistency_report.md`, `reports/execution_count_reordering_limitation.md`, `reports/environment_branching_check.md`, `reports/marimo_conversion_report.md` |

**Headline answers** (full nuance, confidence intervals, and correction history are in the manuscript, not just this table):
- RQ1: **59.8%** of 112 real crashed notebooks are saved out of visual order; **92.0%** carry at least one state hazard.
- RQ2: Yes, decisively, on the synthetic benchmark — unaided accuracy ranges 0–97% across fifteen models/seven vendors; our reordering fix scores **100% on every model**.
- RQ3: **No** measurable per-item accuracy advantage on real notebooks once an answer is reached (23–27% overall-TRUTH across all three conditions, overlapping 95% CIs) — a null result that survived, not reversed, a corrected grading-bug re-analysis. The real, defensible advantage is **reach**: raw JSON overflows context on 62% of real divergent items versus 15–17% for compressed serializations.
- RQ4: **96.4%** aggregate / **91.2%** median token reduction across 40 real notebooks, 40/40 robust, with well under 1% overhead for the state-safety annotations.
- RQ5: The preprocessor *reduces* accuracy on the already-clean Themisto benchmark (a lost-in-the-middle effect, not information loss); the core `execution_count`-sort mechanism has a verified edge case affecting 26.6% of real notebooks (now detected and flagged, not silently ignored); marimo's reactive execution model is equally blocked by missing real-world data/dependencies, supporting the paper's reach argument rather than contradicting it.

## Repository structure

```
code/
├── README.md                  — this file
├── requirements.txt           — Python dependencies
├── problem.md                 — the ten root-cause taxonomy (A–J) and the Coupling Problem
├── gaps_analysis.md           — root causes vs. existing mitigations vs. remaining gaps
├── CHANGELOG.md               — full dated methodology log, including every correction
│                                 (the grading-bug fix, the execution_count-sort edge case,
│                                 the corrected Themisto explanation, the model-curve expansion)
├── docs/
│   └── GUIDE.md                — usage guide for the preprocessor
├── src/                        — JupPreprocessor implementation
│   ├── preprocessor.py         — Stage 1 rule-based transform (entry point)
│   ├── state_extractor.py      — AST-based VariableStateExtractor + state annotations
│   ├── ground_truth_extractor.py — dual-order re-execution for executable ground truth
│   ├── notebook_sandbox.py     — isolated per-cell-timeout execution sandbox
│   ├── agent_orchestrator.py / agent_verifier.py — optional runtime-verification layer
│   │                             (Tier 3; not exercised by any benchmark in the paper)
│   ├── evaluator.py             — shared evaluation utilities
│   └── measure_token_reduction.py
├── tests/                      — every experiment script + the unit test suite
│   ├── test_*.py                — unit tests (`python3 -m unittest discover -s tests`)
│   ├── run_niah_v2.py            — the fair Notebook-NIAH synthetic benchmark (RQ2)
│   ├── compile_model_curve.py    — aggregates per-model NIAH reports into the cross-model table
│   ├── run_out_of_order_scan.py  — RQ1's JunoBench-wide hazard scan
│   ├── run_real_state_groundtruth.py / run_real_state_eval.py — RQ3's executable ground truth + LLM eval
│   ├── run_real_notebook_validation.py — RQ4's token-reduction/robustness measurement
│   ├── run_themisto_eval.py / run_execution_count_consistency_scan.py / run_marimo_conversion_check.py — RQ5
│   └── *.json                    — small, committed measured-result artifacts (ground truth,
│                                    raw LLM answers, evaluation outputs)
├── reports/                     — every measured report cited in the manuscript, in Markdown
└── paper/
    ├── main.tex / main.pdf      — the submitted manuscript (canonical; supersedes any other draft)
    └── figures/                 — figure-generation script + rendered PDF/PNG figures
```

**Not included in this repository:** the 135MB JunoBench raw-notebook download cache
(`tests/junobench_downloads/`, re-fetched on demand from Hugging Face by the scripts
above — see `docs/GUIDE.md`), Python virtual environments, and API keys/secrets
(`.env` is never committed — see `.gitignore`).

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

The core preprocessor (`src/preprocessor.py`, `src/state_extractor.py`) has **zero
LLM dependency** and only needs `PyYAML` and `tiktoken`. Reproducing the LLM-backed
evaluations (RQ2, RQ3, RQ5) additionally requires an `OPENAI_API_KEY` (and, for the
non-OpenAI models in the cross-vendor curve, an `OPENROUTER_API_KEY` and/or a
Zhipu/GLM API key — see `reports/model_curve_report.md` for exactly which models were
tested and via which provider). Set these in a local `.env` file (gitignored, never
committed) or as environment variables.

Reproducing the widened real-notebook ground truth (RQ3) for `torch`/`torchvision`-backed
notebooks needs those packages installed (CPU wheels are sufficient — see the comments
in `requirements.txt`); reproducing the TensorFlow-backed subset requires a **separate**
Python 3.12 environment, since no `tensorflow` wheel exists for Python 3.14 at the time
of writing (see `requirements.txt` and `CHANGELOG.md` for the exact environment recipe
used).

## Running the test suite

```bash
python3 -m unittest discover -s tests -p "test_*.py"
```

## Data availability

All notebook data used in this study is drawn from **JunoBench**, a publicly available,
pre-existing benchmark of crashed machine-learning Jupyter notebooks
(Wang et al., 2025; arXiv:2510.18013; `https://huggingface.co/datasets/PELAB-LiU/JunoBench`).
No new notebook data was collected for this study. All measured reports in `reports/`
are the complete, unedited outputs of the scripts in `tests/`, run against this public
dataset.

## Citation

If you use this code or reference this work, please cite the manuscript (full citation
to be added once the DOI/venue is assigned):

```
Rafique, M. R. B. (2026). The Notebook You Read Is Not the Notebook That Ran:
Execution-Order Reconstruction for LLM Understanding of Jupyter Notebooks.
[Manuscript submitted to Empirical Software Engineering.]
```
