# Notebook-NIAH v2 Report

- **Mode:** `stateful` (state tracking: true value has highest execution_count; a decoy sits later in visual order)
- **Trials per grid cell:** 3
- **Model:** gpt-4.1-nano  |  context limit 128,000 (prompts capped at 126,000)
- **Conditions:** raw, plain_strip, ours

**Fairness rule:** any prompt exceeding the context cap is recorded as `OVERFLOW`, a distinct outcome from a wrong answer. A baseline is only scored 'incorrect' when it *fit in context and still answered wrong*.

## Token usage & context fit (avg prompt tokens)

| Length | raw | plain_strip | ours |
| :--- | :---: | :---: | :---: |
| ~8,000 | 9,454 | 282 | 683 |
| ~30,000 | 31,449 | 548 | 1,596 |
| ~60,000 | 62,028 | 922 | 2,921 |
| ~100,000 | 101,736 | 1,424 | 4,874 |

## Accuracy — `raw` (rows = depth, cols = length)

| depth \ length | 8k | 30k | 60k | 100k |
| :--- | :---: | :---: | :---: | :---: |
| 0.1 | 33% (1/3) | 67% (2/3) | 67% (2/3) | 67% (2/3) |
| 0.5 | 100% (3/3) | 33% (1/3) | 67% (2/3) | 67% (2/3) |
| 0.9 | 0% (0/3) | 0% (0/3) | 67% (2/3) | 67% (2/3) |

## Accuracy — `plain_strip` (rows = depth, cols = length)

| depth \ length | 8k | 30k | 60k | 100k |
| :--- | :---: | :---: | :---: | :---: |
| 0.1 | 0% (0/3) | 0% (0/3) | 33% (1/3) | 67% (2/3) |
| 0.5 | 0% (0/3) | 0% (0/3) | 0% (0/3) | 0% (0/3) |
| 0.9 | 0% (0/3) | 0% (0/3) | 0% (0/3) | 0% (0/3) |

## Accuracy — `ours` (rows = depth, cols = length)

| depth \ length | 8k | 30k | 60k | 100k |
| :--- | :---: | :---: | :---: | :---: |
| 0.1 | 100% (3/3) | 100% (3/3) | 100% (3/3) | 100% (3/3) |
| 0.5 | 100% (3/3) | 100% (3/3) | 100% (3/3) | 100% (3/3) |
| 0.9 | 100% (3/3) | 100% (3/3) | 100% (3/3) | 100% (3/3) |

## How to read this

- Compare `raw` vs `ours` **only where `raw` fit in context** — that is the fair comparison the earlier version lacked.
- `plain_strip` is the compression control: it has ~the same token count as `ours` but no reordering and no variable table. **If `ours` ≈ `plain_strip`, the gain is compression, not structure.** **If `ours` > `plain_strip` in `stateful` mode, execution-order reconstruction is doing real work.**
- In `stateful` mode, an answer equal to the *decoy* value means the model followed visual order instead of execution order (Root Cause A).
