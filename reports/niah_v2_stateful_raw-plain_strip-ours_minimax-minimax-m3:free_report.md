# Notebook-NIAH v2 Report

- **Mode:** `stateful` (state tracking: true value has highest execution_count; a decoy sits later in visual order)
- **Trials per grid cell:** 2
- **Model:** minimax/minimax-m3:free  |  context limit 128,000 (prompts capped at 126,000)
- **Conditions:** raw, plain_strip, ours

**Fairness rule:** any prompt exceeding the context cap is recorded as `OVERFLOW`, a distinct outcome from a wrong answer. A baseline is only scored 'incorrect' when it *fit in context and still answered wrong*.

## Token usage & context fit (avg prompt tokens)

| Length | raw | plain_strip | ours |
| :--- | :---: | :---: | :---: |
| ~30,000 | 31,176 | 539 | 1,559 |

## Accuracy — `raw` (rows = depth, cols = length)

| depth \ length | 30k |
| :--- | :---: |
| 0.1 | 0% (0/2) |
| 0.5 | 0% (0/2) |
| 0.9 | 0% (0/2) |

## Accuracy — `plain_strip` (rows = depth, cols = length)

| depth \ length | 30k |
| :--- | :---: |
| 0.1 | 0% (0/2) |
| 0.5 | 0% (0/2) |
| 0.9 | 0% (0/2) |

## Accuracy — `ours` (rows = depth, cols = length)

| depth \ length | 30k |
| :--- | :---: |
| 0.1 | 100% (2/2) |
| 0.5 | 100% (2/2) |
| 0.9 | 100% (2/2) |

## How to read this

- Compare `raw` vs `ours` **only where `raw` fit in context** — that is the fair comparison the earlier version lacked.
- `plain_strip` is the compression control: it has ~the same token count as `ours` but no reordering and no variable table. **If `ours` ≈ `plain_strip`, the gain is compression, not structure.** **If `ours` > `plain_strip` in `stateful` mode, execution-order reconstruction is doing real work.**
- In `stateful` mode, an answer equal to the *decoy* value means the model followed visual order instead of execution order (Root Cause A).
