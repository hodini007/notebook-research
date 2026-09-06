# Cross-Model Capability Curve — Stateful Notebook-NIAH

Aggregate accuracy over the full depth × length grid (fair, context-bounded; identical prompts across models). `raw` measures unaided out-of-order state resolution; `ours` measures it after execution-order reconstruction.

| Model | raw | plain_strip | ours |
| :--- | :---: | :---: | :---: |
| gpt-4o | **61%** (22/36) | **0%** (0/36) | **100%** (36/36) |
| cohere-north-mini-code:free | **0%** (0/3) | **0%** (0/3) | **100%** (3/3) |
| glm-5.3-flash | **100%** (3/3) | **33%** (1/3) | **100%** (3/3) |
| gpt-4.1-mini | **19%** (7/36) | **0%** (0/36) | **100%** (36/36) |
| gpt-4.1-nano | **53%** (19/36) | **8%** (3/36) | **100%** (36/36) |
| gpt-4o-mini | **3%** (1/36) | **0%** (0/36) | **100%** (36/36) |
| gpt-5 | **97%** (35/36) | **8%** (3/36) | **100%** (36/36) |
| gpt-5-mini | **83%** (30/36) | **0%** (0/36) | **100%** (36/36) |
| gpt-5-nano | **69%** (25/36) | **0%** (0/36) | **100%** (36/36) |
| gpt-5.4-2026-03-05 | **92%** (11/12) | **0%** (0/12) | **100%** (12/12) |
| gpt-5.4-mini-2026-03-17 | **42%** (5/12) | **0%** (0/12) | **100%** (12/12) |
| inclusionai-ling-3.0-flash-fin:free | **33%** (1/3) | **0%** (0/3) | **100%** (3/3) |
| minimax-minimax-m3:free | **0%** (0/6) | **0%** (0/6) | **100%** (6/6) |
| nvidia-nemotron-3-super-120b-a12b:free | **50%** (3/6) | **0%** (0/6) | **100%** (6/6) |
| poolside-laguna-s-2.1:free | **67%** (2/3) | **0%** (0/3) | **100%** (3/3) |

_Compiled automatically from the per-model reports in this directory; per-cell grids and findings live there._
