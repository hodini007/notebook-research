# Real-Notebook State Ground Truth Report

Each out-of-order JunoBench notebook is executed twice in a sandboxed subprocess — in `execution_count` order (truth) and in visual order (what a naive reader simulates) — with identical RNG seeds. Divergent final variables are real-data state decoys with executable ground truth. **No LLM calls.**

- Out-of-order candidates processed: **67**
- Executed usefully under both orders (≥1 cell ok): **62**
- **Notebooks with ≥1 order-divergent variable: 16**
- **Total divergent variables (benchmark items): 52** — 11 value divergences, 41 existence divergences

A divergent variable means: reading this real notebook top-to-bottom yields a provably wrong value for it. Items: `tests/real_state_groundtruth.json`.

## Per-notebook results

| Notebook | Status | Cells | ok (ec) | ok (visual) | Divergent vars |
| :--- | :--- | :---: | :---: | :---: | :---: |
| `NBspecific_1.ipynb` | ok | 33 | 8 | 8 | 0 |
| `NBspecific_10.ipynb` | ok | 187 | 30 | 32 | 1 |
| `NBspecific_11.ipynb` | ok | 20 | 3 | 6 | 2 |
| `NBspecific_12.ipynb` | ok | 7 | 2 | 2 | 0 |
| `NBspecific_13.ipynb` | ok | 17 | 4 | 4 | 0 |
| `NBspecific_15.ipynb` | ok | 25 | 11 | 10 | 1 |
| `NBspecific_16.ipynb` | ok | 22 | 11 | 11 | 0 |
| `NBspecific_17.ipynb` | ok | 19 | 3 | 3 | 0 |
| `NBspecific_19.ipynb` | ok | 8 | 2 | 2 | 0 |
| `NBspecific_2.ipynb` | ok | 21 | 7 | 7 | 0 |
| `NBspecific_3.ipynb` | ok | 12 | 1 | 1 | 0 |
| `NBspecific_4.ipynb` | ok | 31 | 2 | 2 | 0 |
| `NBspecific_6.ipynb` | ok | 19 | 2 | 2 | 0 |
| `NBspecific_9.ipynb` | ok | 32 | 2 | 2 | 0 |
| `lightgbm_1.ipynb` | ok | 26 | 8 | 8 | 0 |
| `matplotlib_1.ipynb` | ok | 24 | 8 | 8 | 4 |
| `matplotlib_2.ipynb` | ok | 12 | 1 | 1 | 0 |
| `matplotlib_3.ipynb` | failed (no_output (rc=0, stderr tail: ' cuda drivers on your machine, GPU will not be used.\nE0000 00:00:1788623025.244918  193783 cuda_platform.cc:52] failed call to cuInit: INTERNAL: CUDA error: Failed call to cuInit: UNKNOWN ERROR (303)\n')) | — | — | — | — |
| `numpy_1.ipynb` | ok | 15 | 3 | 8 | 12 |
| `numpy_11.ipynb` | ok | 18 | 9 | 12 | 8 |
| `numpy_14.ipynb` | ok | 19 | 5 | 5 | 0 |
| `numpy_15.ipynb` | ok | 36 | 9 | 9 | 0 |
| `numpy_6.ipynb` | ok | 11 | 2 | 2 | 0 |
| `numpy_7.ipynb` | ok | 6 | 2 | 2 | 0 |
| `numpy_8.ipynb` | ok | 83 | 5 | 5 | 0 |
| `numpy_9.ipynb` | ok | 16 | 3 | 3 | 0 |
| `pandas_10.ipynb` | ok | 47 | 3 | 3 | 0 |
| `pandas_12.ipynb` | ok | 35 | 5 | 6 | 0 |
| `pandas_15.ipynb` | ok | 32 | 1 | 1 | 0 |
| `pandas_2.ipynb` | ok | 51 | 2 | 2 | 0 |
| `pandas_3.ipynb` | ok | 11 | 1 | 5 | 5 |
| `pandas_5.ipynb` | ok | 103 | 7 | 7 | 0 |
| `pandas_6.ipynb` | ok | 29 | 2 | 2 | 0 |
| `pandas_7.ipynb` | ok | 9 | 1 | 1 | 0 |
| `pandas_8.ipynb` | ok | 42 | 3 | 3 | 0 |
| `pandas_9.ipynb` | ok | 40 | 1 | 1 | 0 |
| `seaborn_2.ipynb` | ok | 32 | 2 | 2 | 0 |
| `sklearn_10.ipynb` | ok | 53 | 1 | 1 | 0 |
| `sklearn_12.ipynb` | ok | 14 | 2 | 2 | 0 |
| `sklearn_2.ipynb` | ok | 73 | 14 | 14 | 0 |
| `sklearn_4.ipynb` | ok | 136 | 14 | 14 | 0 |
| `sklearn_7.ipynb` | ok | 26 | 1 | 1 | 1 |
| `sklearn_8.ipynb` | ok | 21 | 2 | 2 | 0 |
| `sklearn_9.ipynb` | ok | 17 | 1 | 1 | 3 |
| `statsmodels_2.ipynb` | no_cells_executed | 18 | 0 | 0 | — |
| `tensorflow_1.ipynb` | ok | 18 | 5 | 5 | 0 |
| `tensorflow_13.ipynb` | ok | 17 | 3 | 7 | 0 |
| `tensorflow_15.ipynb` | failed (no_output (rc=0, stderr tail: ' cuda drivers on your machine, GPU will not be used.\nE0000 00:00:1788623225.024398  208981 cuda_platform.cc:52] failed call to cuInit: INTERNAL: CUDA error: Failed call to cuInit: UNKNOWN ERROR (303)\n')) | — | — | — | — |
| `tensorflow_3.ipynb` | no_cells_executed | 11 | 0 | 0 | — |
| `tensorflow_5.ipynb` | ok | 19 | 1 | 1 | 0 |
| `tensorflow_6.ipynb` | ok | 26 | 2 | 2 | 0 |
| `tensorflow_8.ipynb` | ok | 28 | 5 | 5 | 0 |
| `tensorflow_9.ipynb` | ok | 41 | 7 | 7 | 0 |
| `torch_1.ipynb` | ok | 16 | 6 | 7 | 0 |
| `torch_10.ipynb` | ok | 7 | 1 | 1 | 1 |
| `torch_11.ipynb` | ok | 37 | 21 | 21 | 1 |
| `torch_12.ipynb` | no_cells_executed | 14 | 0 | 0 | — |
| `torch_13.ipynb` | ok | 16 | 5 | 6 | 0 |
| `torch_15.ipynb` | ok | 24 | 1 | 1 | 0 |
| `torch_2.ipynb` | ok | 5 | 1 | 1 | 0 |
| `torch_3.ipynb` | ok | 31 | 11 | 15 | 6 |
| `torch_4.ipynb` | ok | 13 | 5 | 7 | 1 |
| `torch_6.ipynb` | ok | 37 | 4 | 7 | 3 |
| `torch_7.ipynb` | ok | 32 | 12 | 12 | 1 |
| `torch_8.ipynb` | ok | 28 | 9 | 11 | 2 |
| `torch_9.ipynb` | ok | 8 | 4 | 4 | 0 |
| `torchvision_1.ipynb` | ok | 24 | 4 | 5 | 0 |

## Sample value divergences

| Notebook | Variable | EC-order (truth) | Visual-order (naive) |
| :--- | :--- | :--- | :--- |
| `NBspecific_15.ipynb` | `src_images` | ndarray(shape=(0,),dtype=float64):[] | list(len=0):[] |
| `matplotlib_1.ipynb` | `conv2d` | Conv2D:<Conv2D name=conv2d_6, built=True> | Conv2D:<Conv2D name=conv2d_2, built=True> |
| `matplotlib_1.ipynb` | `inp` | EagerTensor:<tf.Tensor: shape=(4, 28, 28, 3), dtype=float32, | EagerTensor:<tf.Tensor: shape=(4, 28, 28, 3), dtype=float32, |
| `matplotlib_1.ipynb` | `out` | EagerTensor:<tf.Tensor: shape=(4, 26, 26, 8), dtype=float32, | EagerTensor:<tf.Tensor: shape=(4, 26, 26, 8), dtype=float32, |
| `matplotlib_1.ipynb` | `pool2d` | MaxPooling2D:<MaxPooling2D name=max_pooling2d_4, built=True> | MaxPooling2D:<MaxPooling2D name=max_pooling2d, built=True> |
| `numpy_11.ipynb` | `start` | float:1788623057.7811985 | float:1788623061.4710588 |
| `sklearn_9.ipynb` | `log_reg` | LogisticRegression:LogisticRegression() | LogisticRegression:LogisticRegression(solver='liblinear') |
| `torch_10.ipynb` | `output` | Tensor:tensor([[ 0.0389,  0.0009, -0.0496,  ...,  0.0808,  0 | Tensor:tensor([[-0.2213, -0.0731,  0.1451,  ..., -0.0115, -0 |
| `torch_11.ipynb` | `out` | Tensor:tensor([[-0.1262, -0.0444, -0.0565,  0.1568, -0.2175] | Tensor:tensor([[ 0.1080, -0.2852,  0.0243, -0.0452,  0.1174] |
| `torch_3.ipynb` | `target` | Tensor:tensor([[1, 0, 1]]) | Tensor:tensor([1, 0, 4]) |
| `torch_7.ipynb` | `url` | str:'https://download.pytorch.org/models/googlenet-1378be20. | str:'https://github.com/pytorch/hub/raw/master/images/dog.jp |

## Scope notes

- torch / tensorflow are not installed in the eval environment; cells importing them fail identically under both orders, which cannot create spurious divergence but does reduce coverage.
- RNGs are seeded identically in both runs; remaining divergence is attributable to execution order (including order-dependent RNG stream consumption, which is itself an order effect).
