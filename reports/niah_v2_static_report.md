# Notebook-NIAH v2 Report

- **Mode:** `static` (pure retrieval under noise; needle string identical across formats)
- **Trials per grid cell:** 3
- **Model:** gpt-4o  |  context limit 128,000 (prompts capped at 126,000)
- **Conditions:** raw, plain_strip, ours

**Fairness rule:** any prompt exceeding the context cap is recorded as `OVERFLOW`, a distinct outcome from a wrong answer. A baseline is only scored 'incorrect' when it *fit in context and still answered wrong*.

## Token usage & context fit (avg prompt tokens)

| Length | raw | plain_strip | ours |
| :--- | :---: | :---: | :---: |
| ~8,000 | 9,021 | 252 | 655 |
| ~30,000 | 31,663 | 521 | 1,568 |
| ~60,000 | 61,451 | 880 | 2,845 |
| ~100,000 | 101,317 | 1,374 | 4,743 |

## Accuracy — `raw` (rows = depth, cols = length)

| depth \ length | 8k | 30k | 60k | 100k |
| :--- | :---: | :---: | :---: | :---: |
| 0.1 | 100% (3/3) | 100% (3/3) | 100% (3/3) | 100% (3/3) |
| 0.5 | 100% (3/3) | 100% (3/3) | 100% (3/3) | 100% (3/3) |
| 0.9 | 100% (3/3) | 100% (3/3) | 100% (3/3) | 100% (3/3) |

## Accuracy — `plain_strip` (rows = depth, cols = length)

| depth \ length | 8k | 30k | 60k | 100k |
| :--- | :---: | :---: | :---: | :---: |
| 0.1 | 100% (3/3) | 100% (3/3) | 100% (3/3) | 100% (3/3) |
| 0.5 | 100% (3/3) | 100% (3/3) | 100% (3/3) | 100% (3/3) |
| 0.9 | 100% (3/3) | 100% (3/3) | 100% (3/3) | 100% (3/3) |

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

## Findings (measured)

- **All three conditions score 100% at every depth × length cell.** With the context bound enforced, gpt-4o retrieves a literal needle string perfectly from up to ~101k tokens of base64/HTML noise. **Pure retrieval under noise is not a failure mode at these scales.**
- This is the control result that gives the stateful benchmark its meaning: in stateful mode (`niah_v2_stateful_report.md`) `raw` drops to ~58–61% and `plain_strip` to 0% while `ours` stays at 100%. Since all conditions retrieve perfectly when only *finding* the value is required, the stateful failures are attributable to **state reconstruction (execution-order resolution), not retrieval or attention degradation**.
- It also corrects our own earlier narrative: the deleted v1 benchmark claimed raw JSON fails simple retrieval at scale ("0% accuracy"). Measured fairly, it does not. The real, replicated deficit is out-of-order state tracking.
- Practical implication: for pure lookup tasks the preprocessor's value is **cost, not accuracy** (~4.7k vs ~101k tokens at the largest scale — a 95% reduction at equal accuracy).

_Measured with gpt-4o, 3 trials/cell, 2026-07-22._
