# Notebook-NIAH v2 Report

- **Mode:** `stateful` (state tracking: true value has highest execution_count; a decoy sits later in visual order)
- **Trials per grid cell:** 3
- **Model:** gpt-4o  |  context limit 128,000 (prompts capped at 126,000)
- **Conditions:** reorder_only, table_only

**Fairness rule:** any prompt exceeding the context cap is recorded as `OVERFLOW`, a distinct outcome from a wrong answer. A baseline is only scored 'incorrect' when it *fit in context and still answered wrong*.

## Token usage & context fit (avg prompt tokens)

| Length | reorder_only | table_only |
| :--- | :---: | :---: |
| ~8,000 | 513 | 455 |
| ~30,000 | 1,101 | 1,046 |
| ~60,000 | 1,923 | 1,922 |
| ~100,000 | 3,024 | 3,276 |

## Accuracy — `reorder_only` (rows = depth, cols = length)

| depth \ length | 8k | 30k | 60k | 100k |
| :--- | :---: | :---: | :---: | :---: |
| 0.1 | 100% (3/3) | 100% (3/3) | 100% (3/3) | 100% (3/3) |
| 0.5 | 100% (3/3) | 100% (3/3) | 100% (3/3) | 100% (3/3) |
| 0.9 | 100% (3/3) | 100% (3/3) | 100% (3/3) | 100% (3/3) |

## Accuracy — `table_only` (rows = depth, cols = length)

| depth \ length | 8k | 30k | 60k | 100k |
| :--- | :---: | :---: | :---: | :---: |
| 0.1 | 0% (0/3) | 0% (0/3) | 0% (0/3) | 0% (0/3) |
| 0.5 | 0% (0/3) | 0% (0/3) | 0% (0/3) | 0% (0/3) |
| 0.9 | 0% (0/3) | 0% (0/3) | 0% (0/3) | 0% (0/3) |

## How to read this

- Compare `raw` vs `ours` **only where `raw` fit in context** — that is the fair comparison the earlier version lacked.
- `plain_strip` is the compression control: it has ~the same token count as `ours` but no reordering and no variable table. **If `ours` ≈ `plain_strip`, the gain is compression, not structure.** **If `ours` > `plain_strip` in `stateful` mode, execution-order reconstruction is doing real work.**
- In `stateful` mode, an answer equal to the *decoy* value means the model followed visual order instead of execution order (Root Cause A).

## Findings (measured — component ablation)

- **`reorder_only` = 100% (36/36):** execution-order reordering alone fully solves the stateful task. Combined with `ours` = 100% and `plain_strip` = 0% (main runs), the entire stateful win is attributable to **reordering — necessary and sufficient** for out-of-order value retrieval.
- **`table_only` = 0% (0/36):** the variables table appended to visual-order cells does not rescue the model, despite carrying `last_modified: ecN` references. The table stores types/shapes/uncertainty, not values — so a model reading visual-order code still lands on the decoy. **Reordering cannot be replaced by metadata.**
- Honest scoping: this task exercises value retrieval only. The table's contributions (mutation timelines, ghost/phantom flags, divergence risks, type hints) target hazards this benchmark does not measure; its value must be argued from those, not from this task.

_Measured with gpt-4o, 3 trials/cell, deterministic seeds (crc32), 2026-07-22._
