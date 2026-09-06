# Themisto Benchmark Evaluation Report

We evaluated the preprocessor against the public **Themisto (JuNE) Cell Output Prediction Benchmark** on Hugging Face (`konstantgr/themisto`), using a sampled set of 15 notebook trajectories.

## 📊 Summary Metrics (Exact Match)

| Metric | Raw Prompt | Jupytext (Code Only) | notebookllm (No Output) | Tail-Truncation | JupPreprocessor (Ours) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Output Prediction (EM)** | **40.0%** | **6.7%** | **6.7%** | **13.3%** | **26.7%** |
| **Avg. Prompt Tokens** | **1802** | **190** | **187** | **162** | **2363** |

## 🔬 Scientific Analysis & Key Insights

The Themisto benchmark results highlight two important limitations and characteristics of evaluation on curated datasets:

### 1. The "Already-Clean" Dataset Effect (Token Increase)
*   **Why Token Savings was Negative/Overhead:** Our preprocessor is designed to strip JSON metadata, base64 image streams, duplicate HTML tables, and markdown tracebacks from raw `.ipynb` files, yielding **~60% token savings** on real notebooks.
*   **Themisto Data Format:** The Hugging Face dataset is **already fully preprocessed** by its authors. It contains only clean, raw Python code strings and raw output strings (no HTML, no base64 images).
*   **YAML & State Table Overhead:** Converting this already-clean sequence into YAML structure and appending the statically analyzed `variables` state table adds **formatting overhead** without any raw bloat to strip.

### 2. Measured Failure Mode (see `reports/themisto_failure_mode_breakdown.md` for full detail)
*   **Most of the gap is not about serialization at all.** Of the items where `ours` is wrong, the large majority are *also* wrong under raw — both formats are guessing on data neither has access to (e.g. pickle file shapes never shown in history). Only 2 of 15 items actually decide the entire raw-vs-`ours` accuracy gap.
*   **On the 2 items that do decide the gap, the correct value was present verbatim in the preprocessed prompt too — it was not stripped or lost.** Measured directly: the variable-state table is inserted between the code/output history and the query, pushing the correct evidence 2.7–7.7x farther (by character distance) from the point of prediction than in the raw format. The model's wrong answers matched a *closer but incorrect* earlier value shown in the same prompt, not a fabrication.
*   **Corrected framing:** this is a lost-in-the-middle / distraction effect on short, already-clean data — not evidence that static analysis is blind to runtime values in general. Adding structure (a variable table) is a net negative specifically when there is no token bloat to justify the added distance to the query.

### 🏆 Conclusion
On clean, heavily truncated trajectories where variables are defined outside the window, LLMs rely on guessing, and a structured static table does not help if it cannot capture the values. **On this benchmark, preprocessing did not improve output prediction.**

Whether cell reordering and variable tracking help on large, messy, out-of-order notebooks is a separate claim that Themisto cannot test — the dataset is already clean and linearized by its authors. That claim is evaluated in the Notebook-NIAH stateful benchmark, not here.
