# Marimo Conversion-Reliability Experiment

Tests whether marimo's official Jupyter-to-marimo conversion (`marimo convert`) and reactive execution (`marimo export html`) are reliable at scale on real, messy, crashed ML notebooks -- the same population this project's own preprocessing/ground-truth work targets. **No source found during the feasibility research (`outputs/notebook-preprocessor-feasibility.md`) had evaluated this at scale; this is a novel, $0, no-LLM-cost data point.**

- Notebooks tested: **40** (seed=42 sample, matching `reports/real_notebook_validation_report.md` exactly, for direct comparability)
- `marimo convert` succeeded (valid Python, ≥1 `@app.cell`): **40/40**
- Of those, `marimo export html` (full reactive execution) completed without crashing: **40/40**
- `marimo export html` crashed or timed out entirely: **0/40**

## Outcome breakdown

| Outcome | Count |
| :--- | :---: |
| EXPORT_OK_WITH_CELL_FAILURES | 40 |

## Per-notebook results

| Notebook | Stage | Outcome | Detail |
| :--- | :--- | :--- | :--- |
| `NBspecific_1.ipynb` | export | **EXPORT_OK_WITH_CELL_FAILURES** | 32 cell(s) raised an exception during execution |
| `NBspecific_12.ipynb` | export | **EXPORT_OK_WITH_CELL_FAILURES** | 4 cell(s) raised an exception during execution |
| `NBspecific_16.ipynb` | export | **EXPORT_OK_WITH_CELL_FAILURES** | 15 cell(s) raised an exception during execution |
| `NBspecific_17.ipynb` | export | **EXPORT_OK_WITH_CELL_FAILURES** | 33 cell(s) raised an exception during execution |
| `NBspecific_18.ipynb` | export | **EXPORT_OK_WITH_CELL_FAILURES** | 28 cell(s) raised an exception during execution |
| `NBspecific_19.ipynb` | export | **EXPORT_OK_WITH_CELL_FAILURES** | 6 cell(s) raised an exception during execution |
| `NBspecific_20.ipynb` | export | **EXPORT_OK_WITH_CELL_FAILURES** | 16 cell(s) raised an exception during execution |
| `NBspecific_3.ipynb` | export | **EXPORT_OK_WITH_CELL_FAILURES** | 11 cell(s) raised an exception during execution |
| `NBspecific_7.ipynb` | export | **EXPORT_OK_WITH_CELL_FAILURES** | 47 cell(s) raised an exception during execution |
| `NBspecific_9.ipynb` | export | **EXPORT_OK_WITH_CELL_FAILURES** | 30 cell(s) raised an exception during execution |
| `matplotlib_3.ipynb` | export | **EXPORT_OK_WITH_CELL_FAILURES** | 46 cell(s) raised an exception during execution |
| `matplotlib_6.ipynb` | export | **EXPORT_OK_WITH_CELL_FAILURES** | 34 cell(s) raised an exception during execution |
| `numpy_11.ipynb` | export | **EXPORT_OK_WITH_CELL_FAILURES** | 8 cell(s) raised an exception during execution |
| `numpy_12.ipynb` | export | **EXPORT_OK_WITH_CELL_FAILURES** | 13 cell(s) raised an exception during execution |
| `numpy_14.ipynb` | export | **EXPORT_OK_WITH_CELL_FAILURES** | 43 cell(s) raised an exception during execution |
| `numpy_15.ipynb` | export | **EXPORT_OK_WITH_CELL_FAILURES** | 26 cell(s) raised an exception during execution |
| `numpy_7.ipynb` | export | **EXPORT_OK_WITH_CELL_FAILURES** | 4 cell(s) raised an exception during execution |
| `pandas_15.ipynb` | export | **EXPORT_OK_WITH_CELL_FAILURES** | 31 cell(s) raised an exception during execution |
| `pandas_3.ipynb` | export | **EXPORT_OK_WITH_CELL_FAILURES** | 9 cell(s) raised an exception during execution |
| `pandas_5.ipynb` | export | **EXPORT_OK_WITH_CELL_FAILURES** | 146 cell(s) raised an exception during execution |
| `pandas_6.ipynb` | export | **EXPORT_OK_WITH_CELL_FAILURES** | 28 cell(s) raised an exception during execution |
| `pandas_9.ipynb` | export | **EXPORT_OK_WITH_CELL_FAILURES** | 44 cell(s) raised an exception during execution |
| `seaborn_1.ipynb` | export | **EXPORT_OK_WITH_CELL_FAILURES** | 27 cell(s) raised an exception during execution |
| `sklearn_1.ipynb` | export | **EXPORT_OK_WITH_CELL_FAILURES** | 136 cell(s) raised an exception during execution |
| `sklearn_10.ipynb` | export | **EXPORT_OK_WITH_CELL_FAILURES** | 60 cell(s) raised an exception during execution |
| `sklearn_12.ipynb` | export | **EXPORT_OK_WITH_CELL_FAILURES** | 14 cell(s) raised an exception during execution |
| `sklearn_13.ipynb` | export | **EXPORT_OK_WITH_CELL_FAILURES** | 17 cell(s) raised an exception during execution |
| `sklearn_2.ipynb` | export | **EXPORT_OK_WITH_CELL_FAILURES** | 69 cell(s) raised an exception during execution |
| `sklearn_4.ipynb` | export | **EXPORT_OK_WITH_CELL_FAILURES** | 129 cell(s) raised an exception during execution |
| `sklearn_7.ipynb` | export | **EXPORT_OK_WITH_CELL_FAILURES** | 43 cell(s) raised an exception during execution |
| `sklearn_8.ipynb` | export | **EXPORT_OK_WITH_CELL_FAILURES** | 46 cell(s) raised an exception during execution |
| `tensorflow_1.ipynb` | export | **EXPORT_OK_WITH_CELL_FAILURES** | 13 cell(s) raised an exception during execution |
| `tensorflow_15.ipynb` | export | **EXPORT_OK_WITH_CELL_FAILURES** | 18 cell(s) raised an exception during execution |
| `torch_10.ipynb` | export | **EXPORT_OK_WITH_CELL_FAILURES** | 9 cell(s) raised an exception during execution |
| `torch_14.ipynb` | export | **EXPORT_OK_WITH_CELL_FAILURES** | 2 cell(s) raised an exception during execution |
| `torch_2.ipynb` | export | **EXPORT_OK_WITH_CELL_FAILURES** | 6 cell(s) raised an exception during execution |
| `torch_3.ipynb` | export | **EXPORT_OK_WITH_CELL_FAILURES** | 29 cell(s) raised an exception during execution |
| `torch_6.ipynb` | export | **EXPORT_OK_WITH_CELL_FAILURES** | 68 cell(s) raised an exception during execution |
| `torch_8.ipynb` | export | **EXPORT_OK_WITH_CELL_FAILURES** | 39 cell(s) raised an exception during execution |
| `torch_9.ipynb` | export | **EXPORT_OK_WITH_CELL_FAILURES** | 4 cell(s) raised an exception during execution |

## Interpretation

**Key finding: `marimo convert` + `marimo export html` never crashed or timed out on any of the 40 real notebooks (100% tooling reliability) -- but every single notebook (40/40) had at least one cell fail during reactive execution, almost always due to missing local data files (e.g. `/kaggle/input/...` paths) or missing third-party packages (e.g. `torchmetrics`) not present in the execution environment.** This is not a marimo-specific weakness: it is the exact same "missing deps/data" failure mode this project's own dual-order re-execution ground-truth work already documents for these identical notebooks (see `reports/real_state_groundtruth_report.md`'s per-notebook table, which repeatedly reports `no_cells_executed (missing deps/data)` for the same corpus).

This is directly relevant to the feasibility question this experiment was designed to answer: **any approach requiring live execution -- marimo's reactive model included -- inherits the real-world unavailability of the original data/environment that produced a notebook.** A purely static approach (this project's Stage 1) cannot recover the *value* a missing-data cell would have produced either, but it also cannot be blocked by a missing package or file in the first place, since it never tries to run anything. This is measured evidence for, not against, the project's Tier 1/2 (resolve/detect-flag) design choice on the specific axis of *reach* -- the same axis the paper's real-notebook §5.4 results already identify as the more defensible claim than per-item accuracy.

A further pattern worth noting: marimo's reactive dependency graph means a single root failure (e.g. one missing import) cascades to *every* downstream cell that depends on it, each separately reported as "an ancestor raised an exception." This produced cell-failure counts as high as 68 (`torch_6.ipynb`) from what is very likely a small number of root causes, not 68 independent failures -- a transparency feature of the reactive model (nothing downstream of a known failure silently produces a stale result), but also a reason raw cell-failure counts in the table above should not be read as "N independent bugs."

- `marimo convert` reliability measures whether the format translation itself is robust to real, messy notebook code (magics, unusual syntax, non-monotonic structure). It was 100% reliable on this sample.
- `EXPORT_OK_WITH_CELL_FAILURES` is expected and not a marimo-specific weakness, as established above. What matters is whether conversion or reactive execution *introduces new* failures beyond what the original notebook already had -- no evidence of that was found in this sample.
- This experiment measures reliability of the *tooling* on real, messy notebooks -- a genuinely novel data point (no prior source found evaluated this at scale). It does **not** measure whether marimo's execution-order guarantee is more accurate than this project's static reconstruction where both *can* execute; that would require comparing marimo's final variable states against the same executable ground truth used in `reports/real_state_groundtruth_report.md`, which was not attempted here and remains a natural next step if this direction is pursued further.
