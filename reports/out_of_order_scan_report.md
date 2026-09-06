# Out-of-Order Execution Scan — Real JunoBench Notebooks

Scans every original (crashing) notebook in `PELAB-LiU/JunoBench` for divergence between visual order and execution order, and for execution-count gaps (the re-execution / ghost-variable precondition). **No LLM calls.**

- Notebooks analyzed: **112** (of 112 listed; 0 failed to parse)
- **Non-monotonic (saved out of visual order): 67/112 (59.8%)**
- **Execution-count gaps (re-executed or deleted cells): 100/112 (89.3%)**
- **Either state hazard present: 103/112 (92.0%)**
- Duplicate execution counts (multi-session saves): 19/112

These are notebooks that real users saved after real crashed sessions — the exact population an LLM debugging assistant receives.

## Per-notebook detail (state-hazard notebooks first)

| Notebook | Code cells | Executed | Inversions | Missing ECs | Max EC |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `sklearn_4.ipynb` | 140 | 136 | 15 | 13 | 99 |
| `pandas_12.ipynb` | 62 | 35 | 9 | 54 | 89 |
| `pandas_9.ipynb` | 47 | 40 | 8 | 150 | 190 |
| `torch_3.ipynb` | 32 | 31 | 8 | 83 | 114 |
| `sklearn_7.ipynb` | 26 | 26 | 8 | 34 | 60 |
| `NBspecific_10.ipynb` | 192 | 187 | 7 | 238 | 425 |
| `pandas_8.ipynb` | 42 | 42 | 7 | 66 | 108 |
| `torch_6.ipynb` | 37 | 37 | 7 | 42 | 75 |
| `torch_7.ipynb` | 51 | 32 | 6 | 83 | 113 |
| `statsmodels_2.ipynb` | 20 | 18 | 6 | 39 | 57 |
| `numpy_11.ipynb` | 26 | 18 | 5 | 56 | 72 |
| `sklearn_12.ipynb` | 16 | 14 | 4 | 78 | 92 |
| `sklearn_9.ipynb` | 24 | 17 | 4 | 56 | 73 |
| `NBspecific_13.ipynb` | 40 | 17 | 4 | 33 | 50 |
| `pandas_6.ipynb` | 29 | 29 | 4 | 29 | 58 |
| `torch_8.ipynb` | 29 | 28 | 4 | 27 | 55 |
| `numpy_15.ipynb` | 37 | 36 | 4 | 19 | 55 |
| `torch_12.ipynb` | 14 | 14 | 4 | 7 | 17 |
| `NBspecific_1.ipynb` | 41 | 33 | 4 | 5 | 36 |
| `torch_11.ipynb` | 43 | 37 | 3 | 174 | 211 |
| `numpy_1.ipynb` | 16 | 15 | 3 | 119 | 134 |
| `torch_1.ipynb` | 16 | 16 | 3 | 74 | 90 |
| `matplotlib_3.ipynb` | 41 | 37 | 3 | 67 | 104 |
| `NBspecific_9.ipynb` | 33 | 32 | 3 | 43 | 75 |
| `torch_15.ipynb` | 38 | 24 | 3 | 31 | 51 |
| `tensorflow_6.ipynb` | 32 | 26 | 3 | 27 | 53 |
| `lightgbm_1.ipynb` | 46 | 26 | 3 | 23 | 47 |
| `tensorflow_13.ipynb` | 18 | 17 | 3 | 23 | 40 |
| `NBspecific_16.ipynb` | 32 | 22 | 3 | 3 | 23 |
| `sklearn_8.ipynb` | 27 | 21 | 2 | 225 | 246 |
| `pandas_3.ipynb` | 13 | 11 | 2 | 83 | 94 |
| `tensorflow_5.ipynb` | 34 | 19 | 2 | 59 | 78 |
| `torchvision_1.ipynb` | 24 | 24 | 2 | 49 | 72 |
| `numpy_6.ipynb` | 26 | 11 | 2 | 46 | 57 |
| `seaborn_2.ipynb` | 32 | 32 | 2 | 41 | 73 |
| `torch_10.ipynb` | 8 | 7 | 2 | 40 | 46 |
| `torch_2.ipynb` | 6 | 5 | 2 | 34 | 39 |
| `NBspecific_11.ipynb` | 22 | 20 | 2 | 20 | 40 |
| `tensorflow_8.ipynb` | 35 | 28 | 2 | 14 | 38 |
| `NBspecific_4.ipynb` | 35 | 31 | 2 | 9 | 38 |
| `pandas_7.ipynb` | 22 | 9 | 2 | 7 | 16 |
| `torch_13.ipynb` | 16 | 16 | 2 | 6 | 22 |
| `matplotlib_1.ipynb` | 25 | 24 | 2 | 5 | 19 |
| `NBspecific_19.ipynb` | 9 | 8 | 2 | 3 | 10 |
| `NBspecific_15.ipynb` | 26 | 25 | 2 | 2 | 21 |
| `NBspecific_17.ipynb` | 39 | 19 | 1 | 68 | 87 |
| `sklearn_10.ipynb` | 62 | 53 | 1 | 59 | 112 |
| `tensorflow_1.ipynb` | 18 | 18 | 1 | 47 | 65 |
| `NBspecific_12.ipynb` | 9 | 7 | 1 | 39 | 46 |
| `pandas_5.ipynb` | 104 | 103 | 1 | 25 | 128 |
| `pandas_15.ipynb` | 32 | 32 | 1 | 23 | 55 |
| `numpy_8.ipynb` | 83 | 83 | 1 | 21 | 104 |
| `torch_4.ipynb` | 25 | 13 | 1 | 19 | 32 |
| `NBspecific_3.ipynb` | 13 | 12 | 1 | 14 | 26 |
| `pandas_2.ipynb` | 52 | 51 | 1 | 11 | 62 |
| `tensorflow_3.ipynb` | 16 | 11 | 1 | 11 | 22 |
| `numpy_7.ipynb` | 6 | 6 | 1 | 10 | 16 |
| `pandas_10.ipynb` | 72 | 47 | 1 | 9 | 56 |
| `tensorflow_15.ipynb` | 19 | 18 | 1 | 6 | 24 |
| `matplotlib_2.ipynb` | 23 | 12 | 1 | 4 | 16 |
| `numpy_14.ipynb` | 28 | 19 | 1 | 4 | 23 |
| `torch_9.ipynb` | 9 | 8 | 1 | 2 | 10 |
| `NBspecific_6.ipynb` | 35 | 19 | 1 | 1 | 19 |
| `tensorflow_9.ipynb` | 41 | 41 | 1 | 1 | 40 |
| `NBspecific_2.ipynb` | 24 | 21 | 1 | 0 | 20 |
| `numpy_9.ipynb` | 92 | 16 | 1 | 0 | 16 |
| `sklearn_2.ipynb` | 85 | 73 | 1 | 0 | 73 |
| `tensorflow_7.ipynb` | 64 | 57 | 0 | 207 | 264 |
| `seaborn_6.ipynb` | 21 | 20 | 0 | 168 | 188 |
| `seaborn_5.ipynb` | 26 | 17 | 0 | 155 | 172 |
| `statsmodels_1.ipynb` | 52 | 50 | 0 | 148 | 198 |
| `torch_5.ipynb` | 7 | 7 | 0 | 123 | 130 |
| `pandas_4.ipynb` | 20 | 17 | 0 | 94 | 111 |
| `NBspecific_7.ipynb` | 49 | 39 | 0 | 69 | 108 |
| `numpy_13.ipynb` | 44 | 33 | 0 | 65 | 98 |
| `tensorflow_12.ipynb` | 13 | 12 | 0 | 62 | 74 |
| `sklearn_3.ipynb` | 18 | 17 | 0 | 50 | 67 |
| `tensorflow_2.ipynb` | 12 | 12 | 0 | 43 | 55 |
| `sklearn_5.ipynb` | 17 | 16 | 0 | 38 | 54 |
| `tensorflow_10.ipynb` | 22 | 20 | 0 | 35 | 55 |
| `pandas_13.ipynb` | 32 | 30 | 0 | 31 | 61 |
| `numpy_10.ipynb` | 19 | 19 | 0 | 29 | 48 |
| `matplotlib_4.ipynb` | 25 | 24 | 0 | 27 | 51 |
| `NBspecific_8.ipynb` | 23 | 22 | 0 | 21 | 43 |
| `seaborn_3.ipynb` | 18 | 16 | 0 | 20 | 36 |
| `sklearn_1.ipynb` | 47 | 44 | 0 | 18 | 62 |
| `sklearn_13.ipynb` | 19 | 9 | 0 | 18 | 27 |
| `numpy_12.ipynb` | 15 | 15 | 0 | 12 | 27 |
| `pandas_14.ipynb` | 38 | 38 | 0 | 11 | 49 |
| `seaborn_4.ipynb` | 17 | 17 | 0 | 11 | 28 |
| `numpy_2.ipynb` | 79 | 22 | 0 | 10 | 32 |
| `NBspecific_5.ipynb` | 23 | 23 | 0 | 9 | 32 |
| `matplotlib_5.ipynb` | 9 | 9 | 0 | 9 | 18 |
| `matplotlib_6.ipynb` | 32 | 30 | 0 | 9 | 39 |
| `seaborn_1.ipynb` | 27 | 26 | 0 | 7 | 33 |
| `numpy_3.ipynb` | 31 | 9 | 0 | 5 | 14 |
| `tensorflow_4.ipynb` | 16 | 16 | 0 | 5 | 21 |
| `numpy_4.ipynb` | 43 | 21 | 0 | 4 | 25 |
| `tensorflow_14.ipynb` | 5 | 5 | 0 | 4 | 9 |
| `sklearn_14.ipynb` | 20 | 15 | 0 | 3 | 18 |
| `pandas_1.ipynb` | 54 | 41 | 0 | 2 | 43 |
| `pandas_11.ipynb` | 25 | 24 | 0 | 2 | 26 |
| `NBspecific_18.ipynb` | 30 | 27 | 0 | 1 | 28 |
| `NBspecific_14.ipynb` | 7 | 1 | 0 | 0 | 1 |
| `NBspecific_20.ipynb` | 19 | 0 | 0 | 0 | 0 |
| `numpy_5.ipynb` | 15 | 6 | 0 | 0 | 6 |
| `sklearn_11.ipynb` | 10 | 7 | 0 | 0 | 7 |
| `sklearn_15.ipynb` | 24 | 9 | 0 | 0 | 9 |
| `sklearn_4_fixed2.ipynb` | 140 | 10 | 0 | 0 | 10 |
| `sklearn_6.ipynb` | 46 | 46 | 0 | 0 | 46 |
| `tensorflow_11.ipynb` | 21 | 16 | 0 | 0 | 16 |
| `torch_14.ipynb` | 3 | 2 | 0 | 0 | 2 |
