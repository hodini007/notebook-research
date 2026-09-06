# Real-Notebook State Evaluation

First LLM state-accuracy measurement on real out-of-order notebooks with executable ground truth. Model: gpt-4o; three-way grading (TRUTH = execution-order state, DECOY = visual-order state, NEITHER) by gpt-4o-mini judge; all answers recorded below.

- Items: 52 divergent variables across 16 real JunoBench notebooks (see `real_state_groundtruth_report.md`)
- Fairness: prompts over 126,000 tokens are OVERFLOW, excluded from that condition's accuracy

## Outcome tallies

| Condition | TRUTH | DECOY | NEITHER | OVERFLOW |
| :--- | :---: | :---: | :---: | :---: |
| raw | 12 | 2 | 6 | 32 |
| plain_strip | 14 | 14 | 15 | 9 |
| ours | 14 | 15 | 15 | 8 |

## Statistical summary (95% Wilson CI)

| Condition | Reached | TRUTH overall | TRUTH \| reached |
| :--- | :---: | :---: | :---: |
| raw | 20/52 (38%) | 23% [14%, 36%] | 60% [39%, 78%] |
| plain_strip | 43/52 (83%) | 27% [17%, 40%] | 33% [20%, 47%] |
| ours | 44/52 (85%) | 27% [17%, 40%] | 32% [20%, 47%] |

_Wilson score intervals at n=52; overlapping intervals mean the difference between conditions is not statistically distinguishable at this sample size — read the interpretation notes below before citing a single winner.

## Per-item answers

| Notebook | Variable | Kind | Condition | Outcome | Model answer |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `NBspecific_10.ipynb` | `physical_devices` | phantom_in_visual | raw | **OVERFLOW** | (prompt 14,990,819 tokens) |
| `NBspecific_10.ipynb` | `physical_devices` | phantom_in_visual | plain_strip | **NEITHER** | [PhysicalDevice(name='/physical_device:GPU:0', device_type='GPU'), PhysicalDevice(name='/physical_device:GPU:1', device_type='GPU')] |
| `NBspecific_10.ipynb` | `physical_devices` | phantom_in_visual | ours | **NEITHER** | [PhysicalDevice(name='/physical_device:GPU:0', device_type='GPU'), PhysicalDevice(name='/physical_device:GPU:1', device_type='GPU')] |
| `NBspecific_11.ipynb` | `adv` | phantom_in_visual | raw | **OVERFLOW** | (prompt 288,079 tokens) |
| `NBspecific_11.ipynb` | `adv` | phantom_in_visual | plain_strip | **NEITHER** | The final state of the variable `adv` is: An array of shape (224, 224, 3) with dtype `uint8`. |
| `NBspecific_11.ipynb` | `adv` | phantom_in_visual | ours | **NEITHER** | (224, 224, 3) |
| `NBspecific_11.ipynb` | `o_bestattack` | phantom_in_visual | raw | **OVERFLOW** | (prompt 288,081 tokens) |
| `NBspecific_11.ipynb` | `o_bestattack` | phantom_in_visual | plain_strip | **DECOY** | o_bestattack = np.array with shape (1, 3, 224, 224) |
| `NBspecific_11.ipynb` | `o_bestattack` | phantom_in_visual | ours | **DECOY** | o_bestattack = array with shape (1, 3, 224, 224) |
| `NBspecific_15.ipynb` | `src_images` | value_divergence | raw | **OVERFLOW** | (prompt 2,814,116 tokens) |
| `NBspecific_15.ipynb` | `src_images` | value_divergence | plain_strip | **OVERFLOW** | (prompt 1,033,163 tokens) |
| `NBspecific_15.ipynb` | `src_images` | value_divergence | ours | **NEITHER** | src_images = np.array([...]) |
| `matplotlib_1.ipynb` | `conv2d` | value_divergence | raw | **OVERFLOW** | (prompt 1,013,845 tokens) |
| `matplotlib_1.ipynb` | `conv2d` | value_divergence | plain_strip | **NEITHER** | NEVER-DEFINED |
| `matplotlib_1.ipynb` | `conv2d` | value_divergence | ours | **NEITHER** | TensorFlow Keras Conv2D layer with filters=8, kernel_size=3, activation="relu", input_shape=(28, 28, 3), padding="same", strides=(2, 2) |
| `matplotlib_1.ipynb` | `inp` | value_divergence | raw | **OVERFLOW** | (prompt 1,013,843 tokens) |
| `matplotlib_1.ipynb` | `inp` | value_divergence | plain_strip | **NEITHER** | NEVER-DEFINED |
| `matplotlib_1.ipynb` | `inp` | value_divergence | ours | **NEITHER** | Tensor("random_normal:0", shape=(4, 28, 28, 3), dtype=float32) |
| `matplotlib_1.ipynb` | `out` | value_divergence | raw | **OVERFLOW** | (prompt 1,013,843 tokens) |
| `matplotlib_1.ipynb` | `out` | value_divergence | plain_strip | **NEITHER** | NEVER-DEFINED |
| `matplotlib_1.ipynb` | `out` | value_divergence | ours | **NEITHER** | (4, 26, 26, 8) |
| `matplotlib_1.ipynb` | `pool2d` | value_divergence | raw | **OVERFLOW** | (prompt 1,013,845 tokens) |
| `matplotlib_1.ipynb` | `pool2d` | value_divergence | plain_strip | **NEITHER** | NEVER-DEFINED |
| `matplotlib_1.ipynb` | `pool2d` | value_divergence | ours | **NEITHER** | `pool2d = keras.layers.MaxPool2D(pool_size=(2, 2), strides=(2, 2))` |
| `numpy_1.ipynb` | `batch_size` | phantom_in_visual | raw | **OVERFLOW** | (prompt 725,156 tokens) |
| `numpy_1.ipynb` | `batch_size` | phantom_in_visual | plain_strip | **TRUTH** | NEVER-DEFINED |
| `numpy_1.ipynb` | `batch_size` | phantom_in_visual | ours | **DECOY** | 32 |
| `numpy_1.ipynb` | `d` | phantom_in_visual | raw | **OVERFLOW** | (prompt 725,155 tokens) |
| `numpy_1.ipynb` | `d` | phantom_in_visual | plain_strip | **TRUTH** | NEVER-DEFINED |
| `numpy_1.ipynb` | `d` | phantom_in_visual | ours | **TRUTH** | NEVER-DEFINED |
| `numpy_1.ipynb` | `device` | phantom_in_visual | raw | **OVERFLOW** | (prompt 725,155 tokens) |
| `numpy_1.ipynb` | `device` | phantom_in_visual | plain_strip | **NEITHER** | torch.device(type='cuda') |
| `numpy_1.ipynb` | `device` | phantom_in_visual | ours | **NEITHER** | cuda |
| `numpy_1.ipynb` | `disc` | phantom_in_visual | raw | **OVERFLOW** | (prompt 725,155 tokens) |
| `numpy_1.ipynb` | `disc` | phantom_in_visual | plain_strip | **TRUTH** | NEVER-DEFINED |
| `numpy_1.ipynb` | `disc` | phantom_in_visual | ours | **TRUTH** | NEVER-DEFINED |
| `numpy_1.ipynb` | `g` | phantom_in_visual | raw | **OVERFLOW** | (prompt 725,155 tokens) |
| `numpy_1.ipynb` | `g` | phantom_in_visual | plain_strip | **DECOY** | Gen(     (net): Sequential(       (0): Sequential(         (0): ConvTranspose2d(100, 1024, kernel_size=(4, 4), stride=(1, 1))         (1): ReLU()       )        |
| `numpy_1.ipynb` | `g` | phantom_in_visual | ours | **DECOY** | Gen(     (net): Sequential(       (0): Sequential(         (0): ConvTranspose2d(100, 1024, kernel_size=(4, 4), stride=(1, 1))         (1): ReLU()       )        |
| `numpy_1.ipynb` | `gen` | phantom_in_visual | raw | **OVERFLOW** | (prompt 725,155 tokens) |
| `numpy_1.ipynb` | `gen` | phantom_in_visual | plain_strip | **TRUTH** | NEVER-DEFINED |
| `numpy_1.ipynb` | `gen` | phantom_in_visual | ours | **NEITHER** | Gen(100,3,64).to(device) |
| `numpy_1.ipynb` | `img_size` | phantom_in_visual | raw | **OVERFLOW** | (prompt 725,156 tokens) |
| `numpy_1.ipynb` | `img_size` | phantom_in_visual | plain_strip | **DECOY** | 64 |
| `numpy_1.ipynb` | `img_size` | phantom_in_visual | ours | **DECOY** | 64 |
| `numpy_1.ipynb` | `learning_rate` | phantom_in_visual | raw | **OVERFLOW** | (prompt 725,156 tokens) |
| `numpy_1.ipynb` | `learning_rate` | phantom_in_visual | plain_strip | **DECOY** | 3e-4 |
| `numpy_1.ipynb` | `learning_rate` | phantom_in_visual | ours | **DECOY** | 3e-4 |
| `numpy_1.ipynb` | `num_channels` | phantom_in_visual | raw | **OVERFLOW** | (prompt 725,156 tokens) |
| `numpy_1.ipynb` | `num_channels` | phantom_in_visual | plain_strip | **DECOY** | 3 |
| `numpy_1.ipynb` | `num_channels` | phantom_in_visual | ours | **DECOY** | 3 |
| `numpy_1.ipynb` | `num_epochs` | phantom_in_visual | raw | **OVERFLOW** | (prompt 725,156 tokens) |
| `numpy_1.ipynb` | `num_epochs` | phantom_in_visual | plain_strip | **TRUTH** | NEVER-DEFINED |
| `numpy_1.ipynb` | `num_epochs` | phantom_in_visual | ours | **TRUTH** | NEVER-DEFINED |
| `numpy_1.ipynb` | `transformer` | phantom_in_visual | raw | **OVERFLOW** | (prompt 725,156 tokens) |
| `numpy_1.ipynb` | `transformer` | phantom_in_visual | plain_strip | **DECOY** | transforms.Compose([     transforms.Resize(64),     transforms.ToTensor(),     transforms.Normalize(mean = [0.5, 0.5, 0.5], std = [0.5, 0.5, 0.5]) ]) |
| `numpy_1.ipynb` | `transformer` | phantom_in_visual | ours | **DECOY** | transforms.Compose([transforms.Resize(64), transforms.ToTensor(), transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])]) |
| `numpy_1.ipynb` | `z_dim` | phantom_in_visual | raw | **OVERFLOW** | (prompt 725,156 tokens) |
| `numpy_1.ipynb` | `z_dim` | phantom_in_visual | plain_strip | **DECOY** | 100 |
| `numpy_1.ipynb` | `z_dim` | phantom_in_visual | ours | **DECOY** | 100 |
| `numpy_11.ipynb` | `decision` | phantom_in_visual | raw | **OVERFLOW** | (prompt 306,034 tokens) |
| `numpy_11.ipynb` | `decision` | phantom_in_visual | plain_strip | **OVERFLOW** | (prompt 275,151 tokens) |
| `numpy_11.ipynb` | `decision` | phantom_in_visual | ours | **OVERFLOW** | (prompt 312,321 tokens) |
| `numpy_11.ipynb` | `discriminator` | phantom_in_visual | raw | **OVERFLOW** | (prompt 306,035 tokens) |
| `numpy_11.ipynb` | `discriminator` | phantom_in_visual | plain_strip | **OVERFLOW** | (prompt 275,152 tokens) |
| `numpy_11.ipynb` | `discriminator` | phantom_in_visual | ours | **OVERFLOW** | (prompt 312,322 tokens) |
| `numpy_11.ipynb` | `generated_image` | phantom_in_visual | raw | **OVERFLOW** | (prompt 306,035 tokens) |
| `numpy_11.ipynb` | `generated_image` | phantom_in_visual | plain_strip | **OVERFLOW** | (prompt 275,152 tokens) |
| `numpy_11.ipynb` | `generated_image` | phantom_in_visual | ours | **OVERFLOW** | (prompt 312,322 tokens) |
| `numpy_11.ipynb` | `generator` | phantom_in_visual | raw | **OVERFLOW** | (prompt 306,034 tokens) |
| `numpy_11.ipynb` | `generator` | phantom_in_visual | plain_strip | **OVERFLOW** | (prompt 275,151 tokens) |
| `numpy_11.ipynb` | `generator` | phantom_in_visual | ours | **OVERFLOW** | (prompt 312,321 tokens) |
| `numpy_11.ipynb` | `image_shape` | phantom_in_visual | raw | **OVERFLOW** | (prompt 306,035 tokens) |
| `numpy_11.ipynb` | `image_shape` | phantom_in_visual | plain_strip | **OVERFLOW** | (prompt 275,152 tokens) |
| `numpy_11.ipynb` | `image_shape` | phantom_in_visual | ours | **OVERFLOW** | (prompt 312,322 tokens) |
| `numpy_11.ipynb` | `noise` | phantom_in_visual | raw | **OVERFLOW** | (prompt 306,034 tokens) |
| `numpy_11.ipynb` | `noise` | phantom_in_visual | plain_strip | **OVERFLOW** | (prompt 275,151 tokens) |
| `numpy_11.ipynb` | `noise` | phantom_in_visual | ours | **OVERFLOW** | (prompt 312,321 tokens) |
| `numpy_11.ipynb` | `start` | value_divergence | raw | **OVERFLOW** | (prompt 306,034 tokens) |
| `numpy_11.ipynb` | `start` | value_divergence | plain_strip | **OVERFLOW** | (prompt 275,151 tokens) |
| `numpy_11.ipynb` | `start` | value_divergence | ours | **OVERFLOW** | (prompt 312,321 tokens) |
| `numpy_11.ipynb` | `train_dataset` | phantom_in_visual | raw | **OVERFLOW** | (prompt 306,035 tokens) |
| `numpy_11.ipynb` | `train_dataset` | phantom_in_visual | plain_strip | **OVERFLOW** | (prompt 275,152 tokens) |
| `numpy_11.ipynb` | `train_dataset` | phantom_in_visual | ours | **OVERFLOW** | (prompt 312,322 tokens) |
| `pandas_3.ipynb` | `j` | phantom_in_visual | raw | **NEITHER** | 8 |
| `pandas_3.ipynb` | `j` | phantom_in_visual | plain_strip | **NEITHER** | 8 |
| `pandas_3.ipynb` | `j` | phantom_in_visual | ours | **NEITHER** | 8 |
| `pandas_3.ipynb` | `kf` | phantom_in_visual | raw | **NEITHER** | KFold() |
| `pandas_3.ipynb` | `kf` | phantom_in_visual | plain_strip | **DECOY** | KFold(n_splits=5, random_state=None, shuffle=False) |
| `pandas_3.ipynb` | `kf` | phantom_in_visual | ours | **TRUTH** | NEVER-DEFINED |
| `pandas_3.ipynb` | `parametros` | phantom_in_visual | raw | **TRUTH** | NEVER-DEFINED |
| `pandas_3.ipynb` | `parametros` | phantom_in_visual | plain_strip | **TRUTH** | NEVER-DEFINED |
| `pandas_3.ipynb` | `parametros` | phantom_in_visual | ours | **TRUTH** | NEVER-DEFINED |
| `pandas_3.ipynb` | `preds` | phantom_in_visual | raw | **NEITHER** | ```               0         1         2         3         4 0      0.023550  0.174854  0.273220  0.195170  0.333207 1      0.024977  0.219745  0.280006  0.21704 |
| `pandas_3.ipynb` | `preds` | phantom_in_visual | plain_strip | **NEITHER** | 0         1         2         3         4 0      0.023550  0.174854  0.273220  0.195170  0.333207 1      0.024977  0.219745  0.280006  0.217043  0.258229 2      |
| `pandas_3.ipynb` | `preds` | phantom_in_visual | ours | **NEITHER** | 0         1         2         3         4 0      0.023550  0.174854  0.273220  0.195170  0.333207 1      0.024977  0.219745  0.280006  0.217043  0.258229 2      |
| `pandas_3.ipynb` | `resultados` | phantom_in_visual | raw | **DECOY** | The final state of the variable `resultados` is:  ```                                            algoritmo  \ 1  <class 'sklearn.ensemble._forest.RandomForestC. |
| `pandas_3.ipynb` | `resultados` | phantom_in_visual | plain_strip | **DECOY** | The final state of the variable `resultados` is:  ```                                            algoritmo  \ 6  <class 'sklearn.linear_model._logistic.Logisti. |
| `pandas_3.ipynb` | `resultados` | phantom_in_visual | ours | **DECOY** | algoritmo  \ 1  <class 'sklearn.ensemble._forest.RandomForestC...    2  <class 'sklearn.ensemble._forest.RandomForestC...    3  <class 'sklearn.ensemble._forest |
| `sklearn_7.ipynb` | `grid_search` | phantom_in_visual | raw | **OVERFLOW** | (prompt 396,208 tokens) |
| `sklearn_7.ipynb` | `grid_search` | phantom_in_visual | plain_strip | **DECOY** | The final state of the variable `grid_search` was: - A `GridSearchCV` object with best parameters: `{'max_depth': 5, 'min_samples_leaf': 2, 'min_samples_split': |
| `sklearn_7.ipynb` | `grid_search` | phantom_in_visual | ours | **DECOY** | Best Parameters: {'max_depth': 5, 'min_samples_leaf': 2, 'min_samples_split': 10, 'n_estimators': 100} Best Score: 28.133670388354844 |
| `sklearn_9.ipynb` | `log_reg` | value_divergence | raw | **NEITHER** | NEVER-DEFINED |
| `sklearn_9.ipynb` | `log_reg` | value_divergence | plain_strip | **NEITHER** | NEVER-DEFINED |
| `sklearn_9.ipynb` | `log_reg` | value_divergence | ours | **TRUTH** | LogisticRegression() |
| `sklearn_9.ipynb` | `log_reg2` | phantom_in_visual | raw | **TRUTH** | NEVER-DEFINED |
| `sklearn_9.ipynb` | `log_reg2` | phantom_in_visual | plain_strip | **TRUTH** | NEVER-DEFINED |
| `sklearn_9.ipynb` | `log_reg2` | phantom_in_visual | ours | **TRUTH** | NEVER-DEFINED |
| `sklearn_9.ipynb` | `logreg_grid` | phantom_in_visual | raw | **DECOY** | GridSearchCV(cv=5, error_score='raise-deprecating',        estimator=LogisticRegression(C=1.0, class_weight=None, dual=False, fit_intercept=True,           inte |
| `sklearn_9.ipynb` | `logreg_grid` | phantom_in_visual | plain_strip | **NEITHER** | {'C': 10.0} |
| `sklearn_9.ipynb` | `logreg_grid` | phantom_in_visual | ours | **DECOY** | GridSearchCV(cv=5, error_score='raise-deprecating',       estimator=LogisticRegression(C=1.0, class_weight=None, dual=False, fit_intercept=True,          interc |
| `torch_10.ipynb` | `output` | value_divergence | raw | **NEITHER** | NEVER-DEFINED |
| `torch_10.ipynb` | `output` | value_divergence | plain_strip | **NEITHER** | NEVER-DEFINED |
| `torch_10.ipynb` | `output` | value_divergence | ours | **NEITHER** | torch.Size([64, 10]) |
| `torch_11.ipynb` | `out` | value_divergence | raw | **TRUTH** | NEVER-DEFINED |
| `torch_11.ipynb` | `out` | value_divergence | plain_strip | **TRUTH** | NEVER-DEFINED |
| `torch_11.ipynb` | `out` | value_divergence | ours | **TRUTH** | NEVER-DEFINED |
| `torch_3.ipynb` | `input` | phantom_in_visual | raw | **TRUTH** | NEVER-DEFINED |
| `torch_3.ipynb` | `input` | phantom_in_visual | plain_strip | **TRUTH** | NEVER-DEFINED |
| `torch_3.ipynb` | `input` | phantom_in_visual | ours | **TRUTH** | NEVER-DEFINED |
| `torch_3.ipynb` | `loss` | phantom_in_visual | raw | **TRUTH** | NEVER-DEFINED |
| `torch_3.ipynb` | `loss` | phantom_in_visual | plain_strip | **TRUTH** | NEVER-DEFINED |
| `torch_3.ipynb` | `loss` | phantom_in_visual | ours | **TRUTH** | NEVER-DEFINED |
| `torch_3.ipynb` | `m` | phantom_in_visual | raw | **TRUTH** | NEVER-DEFINED |
| `torch_3.ipynb` | `m` | phantom_in_visual | plain_strip | **TRUTH** | NEVER-DEFINED |
| `torch_3.ipynb` | `m` | phantom_in_visual | ours | **TRUTH** | NEVER-DEFINED |
| `torch_3.ipynb` | `output` | phantom_in_visual | raw | **TRUTH** | NEVER-DEFINED |
| `torch_3.ipynb` | `output` | phantom_in_visual | plain_strip | **TRUTH** | NEVER-DEFINED |
| `torch_3.ipynb` | `output` | phantom_in_visual | ours | **NEITHER** | tensor(1.9367, grad_fn=<NllLossBackward0>) |
| `torch_3.ipynb` | `target` | value_divergence | raw | **TRUTH** | tensor([[1, 0, 1]]) |
| `torch_3.ipynb` | `target` | value_divergence | plain_strip | **DECOY** | tensor([1, 0, 4]) |
| `torch_3.ipynb` | `target` | value_divergence | ours | **DECOY** | tensor([1, 0, 4]) |
| `torch_3.ipynb` | `x` | phantom_in_visual | raw | **TRUTH** | NEVER-DEFINED |
| `torch_3.ipynb` | `x` | phantom_in_visual | plain_strip | **NEITHER** | tensor([[-2.7306, -0.6359, -1.3550, -3.3509, -2.1861],         [-0.6840, -1.9918, -1.9863, -2.6024, -1.9128],         [-2.3826, -1.7353, -0.8766, -2.3844, -1.50 |
| `torch_3.ipynb` | `x` | phantom_in_visual | ours | **NEITHER** | tensor([[-2.7306, -0.6359, -1.3550, -3.3509, -2.1861],         [-0.6840, -1.9918, -1.9863, -2.6024, -1.9128],         [-2.3826, -1.7353, -0.8766, -2.3844, -1.50 |
| `torch_4.ipynb` | `device` | phantom_in_visual | raw | **NEITHER** | 'cuda' |
| `torch_4.ipynb` | `device` | phantom_in_visual | plain_strip | **NEITHER** | 'cuda' if torch.cuda.is_available() else 'cpu' |
| `torch_4.ipynb` | `device` | phantom_in_visual | ours | **NEITHER** | 'cuda' |
| `torch_6.ipynb` | `e` | phantom_in_visual | raw | **TRUTH** | NEVER-DEFINED |
| `torch_6.ipynb` | `e` | phantom_in_visual | plain_strip | **TRUTH** | NEVER-DEFINED |
| `torch_6.ipynb` | `e` | phantom_in_visual | ours | **TRUTH** | NEVER-DEFINED |
| `torch_6.ipynb` | `model` | phantom_in_visual | raw | **TRUTH** | NEVER-DEFINED |
| `torch_6.ipynb` | `model` | phantom_in_visual | plain_strip | **DECOY** | AnswerModel(   (norm0): LayerNorm((1536,), eps=1e-05, elementwise_affine=True)   (dropout0): Dropout(p=0.5, inplace=False)   (linear1): Linear(in_features=1536, |
| `torch_6.ipynb` | `model` | phantom_in_visual | ours | **DECOY** | AnswerModel(   (norm0): LayerNorm((1536,), eps=1e-05, elementwise_affine=True)   (dropout0): Dropout(p=0.5, inplace=False)   (linear1): Linear(in_features=1536, |
| `torch_6.ipynb` | `optimizer` | phantom_in_visual | raw | **TRUTH** | NEVER-DEFINED |
| `torch_6.ipynb` | `optimizer` | phantom_in_visual | plain_strip | **TRUTH** | NEVER-DEFINED |
| `torch_6.ipynb` | `optimizer` | phantom_in_visual | ours | **TRUTH** | NEVER-DEFINED |
| `torch_7.ipynb` | `url` | value_divergence | raw | **OVERFLOW** | (prompt 2,833,517 tokens) |
| `torch_7.ipynb` | `url` | value_divergence | plain_strip | **NEITHER** | NEVER-DEFINED |
| `torch_7.ipynb` | `url` | value_divergence | ours | **TRUTH** | "https://download.pytorch.org/models/googlenet-1378be20.pth" |
| `torch_8.ipynb` | `criterion` | phantom_in_visual | raw | **OVERFLOW** | (prompt 7,522,134 tokens) |
| `torch_8.ipynb` | `criterion` | phantom_in_visual | plain_strip | **DECOY** | `torch.nn.CrossEntropyLoss()` |
| `torch_8.ipynb` | `criterion` | phantom_in_visual | ours | **DECOY** | `torch.nn.CrossEntropyLoss()` |
| `torch_8.ipynb` | `model_urls` | phantom_in_visual | raw | **OVERFLOW** | (prompt 7,522,134 tokens) |
| `torch_8.ipynb` | `model_urls` | phantom_in_visual | plain_strip | **DECOY** | ```python {     "convnext_tiny_1k": "https://dl.fbaipublicfiles.com/convnext/convnext_tiny_1k_224_ema.pth",     "convnext_small_1k": "https://dl.fbaipublicfiles |
| `torch_8.ipynb` | `model_urls` | phantom_in_visual | ours | **DECOY** | ```json {     "convnext_tiny_1k": "https://dl.fbaipublicfiles.com/convnext/convnext_tiny_1k_224_ema.pth",     "convnext_small_1k": "https://dl.fbaipublicfiles.c |

## Notes

- **This is the fourth version of this report, and the conclusion has now been replicated at increasing n.** v1: 13 items (torch/torchvision not installed). v2: 41 items (torch/torchvision installed on Python 3.14). v3: 41 items, judge bug found and fixed (`reports/judge_validation_report.md`) — removed `ours`'s apparent edge. **v4 (this version): 52 items**, using a dedicated Python 3.12 virtual environment (`.venv312/`) with TensorFlow installed (TensorFlow has no Python 3.14 wheel), which let 2 more notebooks execute usefully and added 11 new ground-truth items (`matplotlib_1.ipynb`, `NBspecific_10.ipynb`, plus more divergences in already-included notebooks). Same judge fix from v3 carried forward.
- **The n=52 result replicates the n=41 conclusion, strengthening confidence in it.** Overall-TRUTH: raw 23% [14%,36%], plain_strip 27% [17%,40%], ours 27% [17%,40%] — still fully overlapping, still no distinguishable per-item accuracy advantage for `ours`. The reach/coverage gap also replicates and is if anything larger at this n: raw reaches only 38% of items (was 49% at n=41) vs. plain_strip 83% and ours 85% — raw's overflow rate got worse as more large, real notebooks were added, which is exactly the coverage argument this paper stands behind.
- **One TensorFlow notebook (`tensorflow_15.ipynb`) remains unexecutable, and this is now a documented flaky-network case, not a missing-dependency case.** With TensorFlow installed, the notebook's own code downloads a 94MB Keras weights file from Google Cloud Storage mid-execution; this succeeded in one standalone diagnostic run but failed under the batch harness's stricter per-notebook timeout in two other runs. Other TensorFlow notebooks (`tensorflow_1/5/6/8/9/13`) now execute successfully (this was previously impossible on Python 3.14) but happened not to contribute new divergent items in this run.
- **Run-to-run variance of 52–55 items was observed** across repeated runs of the $0 ground-truth extraction step, traced to genuine network-dependent notebook code (weight/dataset downloads with timing-sensitive per-cell timeouts, e.g. in `torch_7.ipynb`, `torchvision_1.ipynb`), not a bug in the extraction script. The n=52 run was used as the canonical dataset for this LLM evaluation (not cherry-picked as the highest of the observed range).
- n=52 is still a case study (the full population recoverable in this environment, not a random sample of JunoBench).
- DECOY outcomes are the interesting failure: the model confidently reports the state a naive visual reading implies, which re-execution proves wrong.
