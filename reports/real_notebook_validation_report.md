# Real-Notebook Validation Report

Runs the rule-based preprocessor over a random sample of **real, in-the-wild ML notebooks** from JunoBench (`PELAB-LiU/JunoBench`) — notebooks that crashed in real projects, not synthesized by us. Measures token reduction and robustness. **No LLM calls.**

- Sample: 40 notebooks (seed=42)
- Preprocessed without error: **40/40** (100%)
- Total raw tokens: **31,372,847** → preprocessed **1,132,881** (**96.4%** aggregate reduction)
- Per-notebook reduction: mean **77.5%**, median **91.2%**, min **-2.3%**, max **99.9%**
- Std dev of reduction: **26.8%**
- Complexity routes: `complex`=33, `medium`=7

## Per-notebook results

| Notebook | Cells | Route | Raw tokens | Preprocessed | Reduction |
| :--- | :---: | :---: | ---: | ---: | :---: |
| `torch_8/torch_8.ipynb` | 29 | complex | 7,521,333 | 11,162 | 99.9% |
| `seaborn_1/seaborn_1.ipynb` | 50 | complex | 11,321,145 | 21,167 | 99.8% |
| `tensorflow_1/tensorflow_1.ipynb` | 27 | medium | 1,302,085 | 3,729 | 99.7% |
| `tensorflow_11/tensorflow_11.ipynb` | 21 | medium | 1,084,829 | 7,406 | 99.3% |
| `torch_1/torch_1.ipynb` | 17 | complex | 686,686 | 6,863 | 99.0% |
| `torch_7/torch_7.ipynb` | 56 | complex | 2,831,044 | 34,363 | 98.8% |
| `numpy_1/numpy_1.ipynb` | 18 | medium | 724,420 | 9,543 | 98.7% |
| `lightgbm_1/lightgbm_1.ipynb` | 68 | complex | 685,045 | 10,781 | 98.4% |
| `numpy_13/numpy_13.ipynb` | 74 | complex | 860,539 | 18,657 | 97.8% |
| `NBspecific_9/NBspecific_9.ipynb` | 45 | complex | 284,601 | 7,716 | 97.3% |
| `sklearn_8/sklearn_8.ipynb` | 31 | complex | 693,999 | 20,192 | 97.1% |
| `pandas_10/pandas_10.ipynb` | 90 | complex | 277,745 | 10,094 | 96.4% |
| `numpy_10/numpy_10.ipynb` | 33 | complex | 240,370 | 10,241 | 95.7% |
| `statsmodels_1/statsmodels_1.ipynb` | 61 | complex | 165,589 | 8,298 | 95.0% |
| `matplotlib_5/matplotlib_5.ipynb` | 9 | medium | 50,065 | 2,728 | 94.6% |
| `sklearn_6/sklearn_6.ipynb` | 58 | complex | 237,277 | 13,157 | 94.5% |
| `NBspecific_4/NBspecific_4.ipynb` | 52 | complex | 198,101 | 12,369 | 93.8% |
| `NBspecific_2/NBspecific_2.ipynb` | 35 | complex | 107,326 | 6,926 | 93.5% |
| `sklearn_10/sklearn_10.ipynb` | 72 | complex | 206,548 | 15,830 | 92.3% |
| `torch_12/torch_12.ipynb` | 28 | complex | 80,085 | 6,994 | 91.3% |
| `NBspecific_13/NBspecific_13.ipynb` | 43 | complex | 54,475 | 4,870 | 91.1% |
| `NBspecific_3/NBspecific_3.ipynb` | 13 | complex | 67,727 | 7,523 | 88.9% |
| `pandas_6/pandas_6.ipynb` | 49 | complex | 112,059 | 13,265 | 88.2% |
| `NBspecific_7/NBspecific_7.ipynb` | 52 | complex | 48,792 | 6,202 | 87.3% |
| `tensorflow_8/tensorflow_8.ipynb` | 44 | complex | 81,998 | 10,600 | 87.1% |
| `pandas_7/pandas_7.ipynb` | 45 | complex | 78,891 | 11,052 | 86.0% |
| `tensorflow_6/tensorflow_6.ipynb` | 41 | complex | 56,153 | 13,762 | 75.5% |
| `torch_6/torch_6.ipynb` | 46 | complex | 66,796 | 23,112 | 65.4% |
| `sklearn_3/sklearn_3.ipynb` | 20 | medium | 25,647 | 9,422 | 63.3% |
| `NBspecific_1/NBspecific_1.ipynb` | 57 | complex | 18,161 | 7,776 | 57.2% |
| `sklearn_15/sklearn_15.ipynb` | 50 | complex | 14,219 | 6,146 | 56.8% |
| `torch_11/torch_11.ipynb` | 43 | complex | 29,192 | 13,031 | 55.4% |
| `torch_13/torch_13.ipynb` | 22 | complex | 21,873 | 10,566 | 51.7% |
| `numpy_3/numpy_3.ipynb` | 45 | complex | 785,146 | 413,012 | 47.4% |
| `torch_2/torch_2.ipynb` | 10 | medium | 12,666 | 6,824 | 46.1% |
| `NBspecific_12/NBspecific_12.ipynb` | 11 | complex | 5,410 | 3,085 | 43.0% |
| `torch_10/torch_10.ipynb` | 8 | medium | 10,606 | 6,904 | 34.9% |
| `tensorflow_14/tensorflow_14.ipynb` | 5 | complex | 4,625 | 3,302 | 28.6% |
| `torch_4/torch_4.ipynb` | 30 | complex | 14,243 | 12,003 | 15.7% |
| `numpy_11/numpy_11.ipynb` | 26 | complex | 305,336 | 312,208 | -2.3% |

## Failures (robustness)

None — every sampled notebook preprocessed without error.

## Notes

- **Negative reductions are real signal, not noise:** an already-lean notebook (little output, no base64/HTML) can grow under YAML + the variable-state table. The min/max range above shows whether that happens.
- This validates **compression + robustness only**. Whether the reconstructed state actually helps an LLM is a separate question, measured under a fair, context-bounded design in `reports/niah_v2_report.md`.