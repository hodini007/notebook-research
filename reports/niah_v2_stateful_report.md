# Notebook-NIAH v2 Report

- **Mode:** `stateful` (state tracking: true value has highest execution_count; a decoy sits later in visual order)
- **Trials per grid cell:** 3
- **Model:** gpt-4o  |  context limit 128,000 (prompts capped at 126,000)
- **Conditions:** raw, plain_strip, ours

**Fairness rule:** any prompt exceeding the context cap is recorded as `OVERFLOW`, a distinct outcome from a wrong answer. A baseline is only scored 'incorrect' when it *fit in context and still answered wrong*.

## Token usage & context fit (avg prompt tokens)

| Length | raw | plain_strip | ours |
| :--- | :---: | :---: | :---: |
| ~8,000 | 9,728 | 284 | 687 |
| ~30,000 | 31,772 | 573 | 1,691 |
| ~60,000 | 61,401 | 936 | 3,038 |
| ~100,000 | 101,836 | 1,467 | 5,069 |

## Accuracy — `raw` (rows = depth, cols = length)

| depth \ length | 8k | 30k | 60k | 100k |
| :--- | :---: | :---: | :---: | :---: |
| 0.1 | 100% (3/3) | 100% (3/3) | 100% (3/3) | 67% (2/3) |
| 0.5 | 67% (2/3) | 100% (3/3) | 33% (1/3) | 0% (0/3) |
| 0.9 | 33% (1/3) | 33% (1/3) | 33% (1/3) | 67% (2/3) |

## Accuracy — `plain_strip` (rows = depth, cols = length)

| depth \ length | 8k | 30k | 60k | 100k |
| :--- | :---: | :---: | :---: | :---: |
| 0.1 | 0% (0/3) | 0% (0/3) | 0% (0/3) | 0% (0/3) |
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

## Findings (measured — second independent run, final preprocessor with B–F annotations)

- **`ours` = 100% (36/36) and `plain_strip` = 0% (0/36)** — exact replication of the first run (2026-07-21, commit `ba386e5`). Near-identical token counts, opposite outcomes: the gap is attributable to **execution-order reconstruction, not compression**.
- **`raw` = 22/36 (61%)** vs 21/36 (~58%) in run 1 — consistent within trial noise. Degradation with depth is clear in both runs (depth 0.9 row: 33/33/33/67% here). Raw JSON *contains* the `execution_count` metadata needed to resolve state; gpt-4o uses it **unreliably**.
- **Static-mode contrast (see `niah_v2_static_report.md`):** in static mode all three conditions score 100% everywhere — retrieval under noise is NOT the failure mode; state reconstruction is. The static run also rules out "compression helps by making strings findable" as an explanation for anything.
- **By-construction caveat:** this benchmark instantiates the exact visual-vs-execution discrepancy the preprocessor fixes; `ours` = 100% shows the transform is correct and complete, not that LLMs prefer our format. The load-bearing results are the `raw` unreliability (replicated twice) and the `plain_strip` control. Do not cite `ours` = 100% without both.

_Measured with gpt-4o, 3 trials/cell per run, two independent runs (2026-07-21, 2026-07-22)._
