# Execution-Count Consistency Scan (corpus-wide, $0, no LLM calls)

Static check for the edge case in `reports/execution_count_reordering_limitation.md`: does sorting a notebook's cells by `execution_count` (the paper's core "resolve" mechanism for Root Cause A) produce a sequence where some cell uses a name before any earlier cell (in that sorted order) defines it, even though the name IS defined somewhere in the notebook? This is a static def-before-use heuristic; see the script docstring for scoping caveats.

**Two counts are reported.** The broad count includes every flagged name and is dominated by noise: generic short identifiers (`i`, `x`, `column`, `c`, `f`) are legitimately reused for unrelated purposes across different cells, and a static def-before-use scan cannot tell that apart from a genuine reordering hazard. The **import-specific** count restricts to names that are (ever) bound via an `import`/`from...import` statement somewhere in the notebook — import names are almost never coincidentally reused for something unrelated, so this subset is a much cleaner signal for the exact mechanism verified in `numpy_1.ipynb` (a re-run-late import cell), at the cost of missing non-import instances of the same mechanism.

- Notebooks scanned: **111**
- Successfully analyzed (≥2 parseable executed cells): **109**
- Broad count (noisy, includes generic-name collisions): 95/109 notebooks (87.2%), 927 instances
- **Import-specific count (cleaner signal): 29/109 notebooks (26.6%), 134 instances**

## Per-notebook results (import-violations first, then broad violations)

| Notebook | Status | Executed cells | Parsed | Unparsed | Import violations | Broad violations | Import-violating names |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| `torch_6.ipynb` | ok | 37 | 36 | 1 | 23 | 57 | `DataLoader`, `Dataset`, `Image`, `OneHotEncoder`, `clip`, `np` (+4 more) |
| `statsmodels_2.ipynb` | ok | 18 | 18 | 0 | 23 | 33 | `MultipleLocator`, `SARIMAX`, `mean_squared_error`, `pd`, `plt`, `seasonal_decompose` |
| `NBspecific_11.ipynb` | ok | 20 | 19 | 1 | 11 | 26 | `Variable`, `cv2`, `models`, `np`, `torch` |
| `torch_8.ipynb` | ok | 28 | 28 | 0 | 9 | 14 | `models`, `nn`, `optim`, `timm`, `torch` |
| `torch_2.ipynb` | ok | 5 | 5 | 0 | 8 | 14 | `DataLoader`, `ImageFolder`, `MulticlassAccuracy`, `ViT_B_16_Weights`, `read_image`, `torch` (+2 more) |
| `pandas_5.ipynb` | ok | 103 | 99 | 4 | 7 | 15 | `plt`, `sns` |
| `NBspecific_13.ipynb` | ok | 17 | 17 | 0 | 7 | 13 | `accuracy_score`, `pd`, `train_test_split` |
| `numpy_1.ipynb` | ok | 15 | 15 | 0 | 6 | 21 | `DataLoader`, `ImageFolder`, `nn`, `torch`, `transforms` |
| `sklearn_9.ipynb` | ok | 17 | 17 | 0 | 4 | 18 | `LogisticRegression`, `f1_score` |
| `sklearn_7.ipynb` | ok | 26 | 26 | 0 | 3 | 22 | `RandomForestRegressor`, `mean_squared_error`, `sns` |
| `torch_10.ipynb` | ok | 7 | 7 | 0 | 3 | 14 | `DataLoader`, `Image` |
| `seaborn_1.ipynb` | ok | 26 | 25 | 1 | 3 | 9 | `tf` |
| `NBspecific_3.ipynb` | ok | 12 | 12 | 0 | 3 | 8 | `mean_absolute_error`, `mean_squared_error`, `median_absolute_error` |
| `NBspecific_10.ipynb` | ok | 187 | 181 | 6 | 2 | 31 | `tf` |
| `torchvision_1.ipynb` | ok | 24 | 24 | 0 | 2 | 20 | `torch` |
| `matplotlib_3.ipynb` | ok | 37 | 36 | 1 | 2 | 18 | `Bidirectional`, `LSTM` |
| `pandas_12.ipynb` | ok | 35 | 35 | 0 | 2 | 14 | `KElbowVisualizer`, `KMeans` |
| `pandas_3.ipynb` | ok | 11 | 10 | 1 | 2 | 12 | `KFold`, `pd` |
| `torch_12.ipynb` | ok | 14 | 14 | 0 | 2 | 11 | `pd` |
| `NBspecific_4.ipynb` | ok | 31 | 31 | 0 | 2 | 10 | `plt`, `sns` |
| `torch_4.ipynb` | ok | 13 | 12 | 1 | 2 | 2 | `np`, `pd` |
| `torch_13.ipynb` | ok | 16 | 16 | 0 | 1 | 21 | `nn` |
| `NBspecific_17.ipynb` | ok | 19 | 18 | 1 | 1 | 15 | `pd` |
| `sklearn_12.ipynb` | ok | 14 | 14 | 0 | 1 | 15 | `RandomForestClassifier` |
| `torch_3.ipynb` | ok | 31 | 31 | 0 | 1 | 12 | `nn` |
| `NBspecific_19.ipynb` | ok | 8 | 7 | 1 | 1 | 10 | `torch` |
| `lightgbm_1.ipynb` | ok | 26 | 26 | 0 | 1 | 8 | `TSNE` |
| `NBspecific_6.ipynb` | ok | 19 | 19 | 0 | 1 | 4 | `plt` |
| `torch_1.ipynb` | ok | 16 | 16 | 0 | 1 | 2 | `nn` |
| `pandas_8.ipynb` | ok | 42 | 42 | 0 | 0 | 26 |  |
| `pandas_9.ipynb` | ok | 40 | 40 | 0 | 0 | 25 |  |
| `torch_9.ipynb` | ok | 8 | 8 | 0 | 0 | 23 |  |
| `numpy_9.ipynb` | ok | 16 | 16 | 0 | 0 | 22 |  |
| `numpy_11.ipynb` | ok | 18 | 18 | 0 | 0 | 18 |  |
| `torch_15.ipynb` | ok | 24 | 24 | 0 | 0 | 18 |  |
| `torch_11.ipynb` | ok | 37 | 37 | 0 | 0 | 16 |  |
| `matplotlib_6.ipynb` | ok | 30 | 26 | 4 | 0 | 15 |  |
| `numpy_10.ipynb` | ok | 19 | 16 | 3 | 0 | 15 |  |
| `numpy_13.ipynb` | ok | 33 | 32 | 1 | 0 | 14 |  |
| `numpy_8.ipynb` | ok | 83 | 83 | 0 | 0 | 13 |  |
| `matplotlib_2.ipynb` | ok | 12 | 11 | 1 | 0 | 12 |  |
| `numpy_7.ipynb` | ok | 6 | 5 | 1 | 0 | 12 |  |
| `pandas_13.ipynb` | ok | 30 | 30 | 0 | 0 | 11 |  |
| `pandas_2.ipynb` | ok | 51 | 51 | 0 | 0 | 11 |  |
| `sklearn_10.ipynb` | ok | 53 | 53 | 0 | 0 | 11 |  |
| `sklearn_8.ipynb` | ok | 21 | 21 | 0 | 0 | 10 |  |
| `sklearn_4.ipynb` | ok | 136 | 98 | 38 | 0 | 9 |  |
| `torch_14.ipynb` | ok | 2 | 2 | 0 | 0 | 9 |  |
| `NBspecific_1.ipynb` | ok | 33 | 32 | 1 | 0 | 8 |  |
| `numpy_6.ipynb` | ok | 11 | 11 | 0 | 0 | 7 |  |
| `tensorflow_13.ipynb` | ok | 17 | 17 | 0 | 0 | 7 |  |
| `tensorflow_4.ipynb` | ok | 16 | 16 | 0 | 0 | 7 |  |
| `tensorflow_9.ipynb` | ok | 41 | 41 | 0 | 0 | 7 |  |
| `NBspecific_12.ipynb` | ok | 7 | 6 | 1 | 0 | 6 |  |
| `pandas_14.ipynb` | ok | 38 | 38 | 0 | 0 | 6 |  |
| `seaborn_2.ipynb` | ok | 32 | 31 | 1 | 0 | 6 |  |
| `sklearn_2.ipynb` | ok | 73 | 73 | 0 | 0 | 6 |  |
| `tensorflow_5.ipynb` | ok | 19 | 17 | 2 | 0 | 6 |  |
| `NBspecific_15.ipynb` | ok | 25 | 25 | 0 | 0 | 5 |  |
| `NBspecific_2.ipynb` | ok | 21 | 21 | 0 | 0 | 5 |  |
| `sklearn_6.ipynb` | ok | 46 | 46 | 0 | 0 | 5 |  |
| `tensorflow_3.ipynb` | ok | 11 | 10 | 1 | 0 | 5 |  |
| `tensorflow_7.ipynb` | ok | 57 | 57 | 0 | 0 | 5 |  |
| `tensorflow_8.ipynb` | ok | 28 | 27 | 1 | 0 | 5 |  |
| `matplotlib_4.ipynb` | ok | 24 | 24 | 0 | 0 | 4 |  |
| `pandas_6.ipynb` | ok | 29 | 29 | 0 | 0 | 4 |  |
| `tensorflow_1.ipynb` | ok | 18 | 18 | 0 | 0 | 4 |  |
| `tensorflow_14.ipynb` | ok | 5 | 5 | 0 | 0 | 4 |  |
| `NBspecific_16.ipynb` | ok | 22 | 22 | 0 | 0 | 3 |  |
| `NBspecific_18.ipynb` | ok | 27 | 27 | 0 | 0 | 3 |  |
| `NBspecific_5.ipynb` | ok | 23 | 23 | 0 | 0 | 3 |  |
| `NBspecific_8.ipynb` | ok | 22 | 22 | 0 | 0 | 3 |  |
| `numpy_2.ipynb` | ok | 22 | 22 | 0 | 0 | 3 |  |
| `numpy_4.ipynb` | ok | 21 | 20 | 1 | 0 | 3 |  |
| `pandas_11.ipynb` | ok | 24 | 24 | 0 | 0 | 3 |  |
| `pandas_4.ipynb` | ok | 17 | 17 | 0 | 0 | 3 |  |
| `sklearn_1.ipynb` | ok | 44 | 44 | 0 | 0 | 3 |  |
| `sklearn_5.ipynb` | ok | 16 | 16 | 0 | 0 | 3 |  |
| `tensorflow_12.ipynb` | ok | 12 | 12 | 0 | 0 | 3 |  |
| `numpy_14.ipynb` | ok | 19 | 19 | 0 | 0 | 2 |  |
| `pandas_1.ipynb` | ok | 41 | 35 | 6 | 0 | 2 |  |
| `pandas_15.ipynb` | ok | 32 | 32 | 0 | 0 | 2 |  |
| `tensorflow_11.ipynb` | ok | 16 | 16 | 0 | 0 | 2 |  |
| `tensorflow_15.ipynb` | ok | 18 | 18 | 0 | 0 | 2 |  |
| `torch_5.ipynb` | ok | 7 | 7 | 0 | 0 | 2 |  |
| `torch_7.ipynb` | ok | 32 | 29 | 3 | 0 | 2 |  |
| `matplotlib_1.ipynb` | ok | 24 | 24 | 0 | 0 | 1 |  |
| `numpy_15.ipynb` | ok | 36 | 35 | 1 | 0 | 1 |  |
| `seaborn_3.ipynb` | ok | 16 | 16 | 0 | 0 | 1 |  |
| `seaborn_4.ipynb` | ok | 17 | 16 | 1 | 0 | 1 |  |
| `seaborn_5.ipynb` | ok | 17 | 16 | 1 | 0 | 1 |  |
| `sklearn_15.ipynb` | ok | 9 | 9 | 0 | 0 | 1 |  |
| `statsmodels_1.ipynb` | ok | 50 | 49 | 1 | 0 | 1 |  |
| `tensorflow_10.ipynb` | ok | 20 | 20 | 0 | 0 | 1 |  |
| `tensorflow_2.ipynb` | ok | 12 | 12 | 0 | 0 | 1 |  |
| `NBspecific_7.ipynb` | ok | 39 | 39 | 0 | 0 | 0 |  |
| `NBspecific_9.ipynb` | ok | 32 | 32 | 0 | 0 | 0 |  |
| `matplotlib_5.ipynb` | ok | 9 | 9 | 0 | 0 | 0 |  |
| `numpy_12.ipynb` | ok | 15 | 15 | 0 | 0 | 0 |  |
| `numpy_3.ipynb` | ok | 9 | 7 | 2 | 0 | 0 |  |
| `numpy_5.ipynb` | ok | 6 | 6 | 0 | 0 | 0 |  |
| `pandas_10.ipynb` | ok | 47 | 47 | 0 | 0 | 0 |  |
| `pandas_7.ipynb` | ok | 9 | 9 | 0 | 0 | 0 |  |
| `seaborn_6.ipynb` | ok | 20 | 20 | 0 | 0 | 0 |  |
| `sklearn_11.ipynb` | ok | 7 | 7 | 0 | 0 | 0 |  |
| `sklearn_13.ipynb` | ok | 9 | 9 | 0 | 0 | 0 |  |
| `sklearn_14.ipynb` | ok | 15 | 15 | 0 | 0 | 0 |  |
| `sklearn_3.ipynb` | ok | 17 | 17 | 0 | 0 | 0 |  |
| `tensorflow_6.ipynb` | ok | 26 | 26 | 0 | 0 | 0 |  |
| `NBspecific_14.ipynb` | skipped (too few parseable cells) | — | — | — | — | — | — |
| `NBspecific_20.ipynb` | skipped (too few parseable cells) | — | — | — | — | — | — |

## Interpretation

- A violation means: reordering this notebook by `execution_count` (as both `src/preprocessor.py` and the ground-truth re-execution methodology do) produces a sequence where a name is used before any prior cell (in that order) defines it, even though some cell does define it eventually. Replaying such a sequence in a fresh kernel would raise `NameError` at that point, independent of any other data/dependency issue.
- This does not necessarily mean the *notebook* is broken -- it means the *execution_count-sort assumption* breaks for it, most plausibly because an early cell (import, config) was re-run later (e.g. after a kernel restart) without re-running its dependents.
- **Use the import-specific count as the headline number**; the broad count is reported for transparency but should not be cited on its own -- an earlier, uncorrected version of this scan (before statement-level ordering was implemented) spuriously flagged 100% of notebooks due to a bug that treated ordinary define-then-use-in-the-same-cell code as a violation; that bug is fixed, but generic-identifier collision noise remains in the broad count by design (it is not separable without deeper semantic/dataflow analysis than this static scan performs).
- Static heuristic caveats: comprehension-scope leakage, `del`, and walrus operators are not modeled precisely; this scan deliberately over-counts a cell's `defined` set (permissive) to avoid over-counting violations, so true prevalence may be slightly higher than reported here.
