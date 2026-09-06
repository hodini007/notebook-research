# A Real Limitation of "Reorder by `execution_count`" (Root Cause A, Tier 1 "Resolve")

Found while investigating why `ours` produces confident-but-wrong answers on
`numpy_1.ipynb` (8 of `ours`'s 16 DECOY outcomes in the n=41 real-notebook
eval come from this single notebook — see
`reports/real_state_eval_report.md`).

## The mechanism

`.ipynb`'s `execution_count` records only the **last** time a cell was run,
not a complete, mutually-consistent execution history. If a user re-runs an
early cell (e.g. the import cell, perhaps after a kernel restart) **without**
re-running the cells that depend on it, that cell's `execution_count`
advances far past its dependents' counts — even though, in the
kernel's actual running memory, the dependency was satisfied earlier and
never became invalid.

`numpy_1.ipynb` is a concrete, verified example. Its import cell (`import
torch`, `import numpy`, etc.) carries `execution_count=27`, while a cell that
uses `torch` (`device = torch.device("cuda" if torch.cuda.is_available()
else "cpu")`, plus five other hyperparameters) carries `execution_count=2`.
Sorting all cells by `execution_count` — exactly what both
`src/preprocessor.py` (the paper's "resolve" tier) and
`tests/run_out_of_order_scan.py` / `ground_truth_extractor.py` (the
executable-ground-truth methodology) do — places the import cell **10th of
15**, after six cells that reference the names it imports:

```
execution_count-sorted order (ec, original cell index):
(2, 1)  device = torch.device(...); batch_size = 32; ...      <- needs torch
(3, 2)  transformer = transforms.Compose([...])                <- needs torchvision
(4, 3)  dataset = ImageFolder(root="/kaggle/input/...", ...)   <- needs torchvision
(6, 5)  train_features_batch, ... = next(iter(train_dataloader))
(7, 8)  def initialize_weights(model): ...
(21, 4) train_dataloader = DataLoader(dataset, batch_size=batch_size, ...)
(23, 9) class Generator(nn.Module): ...                        <- needs torch.nn
(24, 10) def test(): ...
(25, 14) class Gen(nn.Module): ...
(27, 0) import numpy, pandas, torch, torch.nn, ImageFolder, DataLoader, ...  <- FINALLY
(28, 11) ...
```

A fresh-kernel replay in this order raises `NameError: name 'torch' is not
defined` on the very first cell. **This is exactly why `device`,
`batch_size`, `z_dim`, `transformer`, and five other hyperparameters have
`ec_order_value = None` ("never successfully defined") in
`tests/real_state_groundtruth.json`** — not because the original user's
session genuinely never defined them (it almost certainly did — they are
ordinary hyperparameters used throughout the rest of the notebook), but
because a **kernel restart plus partial re-run** broke the numeric ordering
invariant that "sort by `execution_count`" assumes.

## Why this matters

1. **It contaminates part of the n=41 real-notebook ground truth.** At least
   8 of the 41 items (all from `numpy_1.ipynb`) may be measuring "does the
   model correctly guess that a kernel-restart artifact makes this variable
   look undefined" rather than "does the model correctly resolve genuine
   out-of-order execution." These items are not necessarily wrong to include
   (the divergence is real — visual and execution-count order genuinely
   disagree here) but the *reason* differs from the paper's stated
   mechanism, and both `ours` and the ground-truth extractor make the same
   `NameError`-triggering assumption, so this is not a bug our preprocessor
   introduces alone — it inherits it from the underlying re-execution
   methodology.
2. **It is a real edge case in the "resolve" tier's core claim.** The paper
   states execution-order reconstruction is a Tier-1, statically
   *resolvable* fix. This example shows `execution_count` sorting can itself
   produce a sequence that is not runnable in a fresh kernel and does not
   correspond to any real moment in the notebook's history — a case the
   three-tier framework does not currently name. It is a milder, previously
   undocumented sibling of Root Causes B–D (the "detect and flag" tier),
   not fully covered by the current `divergence_risk` annotations (which
   flag randomness/time/file/network/input calls, not import-after-use from
   count-only reordering).
3. **It is common corpus-wide, not a one-off.** A follow-up corpus-wide
   static scan (`tests/run_execution_count_consistency_scan.py`, $0, no LLM
   calls) confirms this: restricting to names that are (ever) bound via an
   `import` statement somewhere in the notebook (a subset chosen because
   import names are almost never coincidentally reused for something
   unrelated, unlike generic identifiers like `i`/`x`/`column`, which
   dominate a noisier broad count and are not a reliable signal for this
   specific mechanism), **29 of 109 analyzable JunoBench notebooks (26.6%)
   exhibit at least one count-order dependency violation** — a case where
   `execution_count`-sorting places code that uses an imported name before
   the cell that imports it. Full detail: `reports/execution_count_consistency_report.md`.

   (An earlier draft of this scan had a bug that aggregated used/defined
   names at the whole-cell level, losing intra-cell statement order; this
   spuriously flagged the ordinary `x = f(); x.method()` pattern as a
   violation and inflated the naive count to 100% of notebooks. Fixed by
   processing statements in order and updating the "defined so far" set
   incrementally within each cell — confirmed against a known-monotonic
   notebook, `seaborn_6.ipynb`, which correctly shows 0 violations after the
   fix.)

## What was and was not done

- Verified via direct inspection of `numpy_1.ipynb`'s raw JSON (not
  simulation): confirmed the `execution_count` values, confirmed the
  `torch`-dependent cell precedes the import cell after sorting, confirmed
  no fix currently detects this.
- Did **not** re-run the n=41 ground-truth extraction or LLM evaluation
  after this finding — fixing it properly requires deciding how the
  preprocessor and ground-truth extractor *should* handle a
  detected-out-of-numeric-order dependency violation (e.g., detect and flag
  it rather than silently sort by raw `execution_count`; or fall back to a
  hybrid using static import/def-before-use analysis to break ties). That
  is a design decision, not a one-line fix, and changing it would alter
  both the preprocessor's core reordering logic and the ground-truth
  methodology used throughout §5.1–§5.4 — out of scope for this pass without
  a decision on direction.
- Did **not** quantify how many of the 112 JunoBench notebooks (or the 41
  ground-truth items) are affected by this specific mechanism versus other
  execution-order phenomena.

## Fix: implemented

The corpus-wide rate is measured (26.6% import-specific) and the detect-
and-flag mechanism is now implemented, not just recommended:

- `src/state_extractor.py::VariableStateExtractor.detect_execution_order_violations`
  reuses the corrected, statement-ordered visitor from
  `tests/run_execution_count_consistency_scan.py` (see that report for why
  statement-level ordering matters and what bug it fixes) and the same
  import-specific filter (generic identifiers are too noisy for a
  per-cell annotation).
- `src/preprocessor.py` calls it after cells are sorted by `execution_count`
  and adds a new per-cell field, `execution_order_risk`, alongside the
  existing `divergence_risk` annotation, with wording that explicitly does
  NOT claim the cell is broken (Tier 2 discipline: flag uncertainty, don't
  invent a resolution) — e.g. for `numpy_1.ipynb`'s `device` cell:
  *"uses torch before any earlier cell (in this execution\_count order)
  imports it; this notebook's execution\_count values may reflect a re-run
  (e.g. kernel restart) rather than a single consistent history — treat
  this cell's position as uncertain, not necessarily broken."*
- Verified directly against `numpy_1.ipynb`: fires on exactly the 6 cells
  identified by manual inspection (ec=2, 3, 4, 21, 23, 25), naming `torch`,
  `transforms`, `ImageFolder`, `DataLoader`, and `nn`.
- All existing unit tests (`tests/test_pipeline.py`,
  `tests/test_state_annotations.py`) still pass unmodified.
- Token-overhead re-measured on the same 40-notebook validation sample
  (`tests/run_real_notebook_validation.py`, $0, no LLM calls): aggregate
  reduction unchanged at 96.4%; median dropped 0.3 percentage points
  (91.5% → 91.2%) — negligible, consistent with the existing ~0.3%
  overhead budget for all B–F static annotations combined.

**Not attempted:** a hybrid reordering that moves a violating
import/definition earlier when safe to do so. The detect-and-flag approach
was chosen deliberately over a reordering fix because (a) it's lower-risk
(no chance of silently producing a *different* wrong order), (b) it's
consistent with the paper's own three-tier philosophy of flagging what
cannot be confidently resolved rather than guessing, and (c) a reordering
fix would need its own validation pass before being trusted. This remains
open as a possible future improvement, not a rejected one.
