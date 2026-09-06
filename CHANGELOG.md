# CHANGELOG / Lab Notebook

Durable log of research progress on JupPreprocessor. Newest entries first.
See `outputs/project_assessment_2026-09-04.md` for the full project review
that motivated this session's work.

## 2026-09-06 (final, marimo) — Marimo conversion-reliability experiment: novel data point, closes the last open feasibility question

**Motivation:** the user's explicit follow-up request after the Python
3.12/TensorFlow work ("after that test marimo") and Open Question 4 from
`outputs/notebook-preprocessor-feasibility.md`: no source found during the
earlier deep-research cycle had evaluated marimo's Jupyter-to-marimo
conversion at scale on messy, real-world notebooks.

**What was done:** installed marimo 0.24.0 in `.venv312`. Wrote
`tests/run_marimo_conversion_check.py`, a $0/no-LLM-cost experiment using
marimo's own official CLI (`marimo convert`, `marimo export html`, which
actually executes a notebook reactively and is the closest marimo-native
equivalent to this project's own dual-order re-execution ground truth). Ran
it against the exact same 40-notebook seed=42 sample used in
`reports/real_notebook_validation_report.md`, for direct comparability. Did
a 3-notebook smoke test first, then verified one "cell failure" result by
hand (confirmed a genuine missing `torchmetrics` import, not a detection
bug) before trusting the full-scale 100% figure.

**Result:** conversion + reactive execution were **100% tooling-reliable**
(40/40, zero crashes or timeouts) -- but **100% of notebooks (40/40) also had
at least one cell fail during execution**, almost always from missing local
data files (e.g. Kaggle input paths) or missing third-party packages. This
is not a marimo weakness: it is the identical "missing deps/data" failure
mode this project's own `src/ground_truth_extractor.py` already reports for
the same corpus. Noted a secondary pattern: marimo's reactive dependency
graph cascades a single root failure to every downstream dependent cell
(e.g. `torch_6.ipynb` reported 68 "cell failures" from what is very likely a
small number of root causes) -- a transparency feature, but a reason not to
read raw failure counts as independent bug counts.

**Interpretation, stated carefully (not oversold):** this is evidence *for*
a static, execution-free approach on the specific axis of *reach* -- any
method requiring live execution, marimo's reactive model included, inherits
the real-world unavailability of a notebook's original data/environment,
while static analysis cannot be blocked by a missing file or package since
it never attempts to run anything. This does **not** test or claim that
marimo is less *accurate* than this project's static reconstruction where
both approaches can execute -- that would require comparing marimo's
recovered variable states against the same executable ground truth used in
`reports/real_state_groundtruth_report.md`, which was not attempted and is
noted as a natural next step if this direction is pursued further.

**Propagated to:** `paper/draft.md`, `paper/main.tex` (new paragraph in
Related Work, right after the CRABS/LongDS-Bench/DSAgentBench discussion --
recompiled, builds clean, still 9 pages, no undefined references),
`README.md` (new results-table row), `outputs/notebook-preprocessor-feasibility.md`
(Open Question 4 marked tested with the result, not deleted).

**Files touched:** `tests/run_marimo_conversion_check.py` (new),
`reports/marimo_conversion_report.md` (new), `paper/draft.md`,
`paper/main.tex`, `README.md`, `outputs/notebook-preprocessor-feasibility.md`.

**This closes every open item from the feasibility research's Open
Questions list that was directly actionable without new credentials or a
human rater** (#1 CRABS citation, #2 Tier-3 framing, #3 environment-branching
test, #4 marimo experiment, #5 LongDS-Bench/DSAgentBench citations -- all
done this session). Remaining: #6 (two ACM papers blocked by 403s), which is
a minor confidence-strengthening item, not load-bearing for any claim made.

---

## 2026-09-06 — Python 3.12 + TensorFlow environment: 41→52 real-notebook items, null result replicated

**Motivation:** the last blocked backlog item requiring real setup work:
tensorflow-backed JunoBench notebooks (`tensorflow_*.ipynb`) were excluded
from the real-notebook ground truth because TensorFlow has no Python 3.14
wheel. User requested a dedicated virtual environment with a suitable Python
version, to be followed by a marimo experiment.

**What was done:**
1. Found Python 3.12 already available on the system
   (`/home/ryn/.local/bin/python3.12`), confirmed TensorFlow publishes
   wheels for it, created `.venv312/` (added to `.gitignore`, was missing
   before -- confirmed not tracked after the fix).
2. Installed the full ML stack needed to execute real notebook code:
   numpy, pandas, scikit-learn, scipy, matplotlib, seaborn, statsmodels,
   lightgbm, torch/torchvision (CPU wheels via PyTorch's own index --
   generic PyPI stalls on large wheels, a lesson already learned earlier
   this session and reapplied here), tensorflow, huggingface_hub, datasets,
   openai, pyyaml, tiktoken, python-dotenv. **Installing packages one at a
   time with `--retries 5 --timeout 60` was reliable; batching many
   packages into one `pip install` call reliably stalled/timed out** --
   documented as a working pattern for future environment setup in this
   repo.
3. Re-ran `tests/run_real_state_groundtruth.py` ($0, no LLM calls) from
   inside `.venv312`. TensorFlow notebooks began executing (previously
   100% blocked on Python 3.14): coverage rose from 60/67 to 62/67 usable
   notebooks, and total ground-truth items rose from 41 to **52** across
   **16** notebooks (up from 14).
4. **Found and partially fixed a real bug while integrating**:
   `tensorflow_15.ipynb` crashed with a CUDA `cuInit` error inside the
   subprocess harness. Investigated properly rather than accepting the
   surface error: confirmed no `libcuda.so` or nvidia-* packages exist
   anywhere on the system, so the crash is TensorFlow's own internal GPU-probe
   routine misfiring, not a real GPU/driver conflict. Added
   `CUDA_VISIBLE_DEVICES="-1"` to the sandboxed subprocess environment as a
   defensive fix (documented in code with a comment). This did not fully fix
   `tensorflow_15.ipynb` specifically: running it standalone succeeded (the
   notebook downloads a 94MB Keras weights file mid-execution, which
   completed that time), but two other attempts inside the stricter batch
   harness timeout failed -- diagnosed as a genuine flaky-network case (a
   large download racing a per-cell timeout), not a fixable bug, and
   documented honestly as such rather than claimed fixed.
5. **Observed and documented real run-to-run variance (52--55 items)**
   across repeated re-runs of the $0 extraction step, traced to
   network-dependent notebook code (weight/dataset downloads with
   timing-sensitive per-cell timeouts in `torch_7.ipynb`,
   `torchvision_1.ipynb`, etc.), not a bug in the extraction script itself.
   Used the n=52 run as the canonical dataset going forward -- explicitly
   not cherry-picked as the highest of the observed range (55 was seen once).
6. Re-ran `tests/run_real_state_eval.py` (gpt-4o answers + gpt-4o-mini
   judge, ~$3.69 estimated cost, judge-bug-fixed prompt already in place
   from the previous correction) on the expanded 52-item set.

**Result: the n=41 null result replicated at n=52, strengthening rather than
reversing it.**
- Overall-TRUTH: raw 23% [14,36], plain_strip 27% [17,40], ours 27% [17,40]
  -- still fully overlapping, same conclusion as n=41 (no distinguishable
  per-item accuracy advantage for `ours`).
- **Reach/coverage gap got *larger*, not smaller, as more (and bigger) real
  notebooks entered the corpus**: raw now reaches only 38% of items (was 49%
  at n=41) vs. plain_strip 83% and ours 85%. This is the paper's core
  surviving real-notebook claim, and it just got stronger with more data.

**Propagated to:** `paper/draft.md`, `paper/main.tex` (abstract, §5.4 table +
findings, Limitations, Conclusion -- recompiled, builds clean, 9 pages, no
undefined references), `README.md` (3 rows/paragraphs updated),
`reports/real_state_eval_report.md` (v4, full correction history preserved
in Notes), `reports/real_state_groundtruth_report.md`, `requirements.txt`
(documents the `.venv312` setup recipe for future reproduction),
`paper/figures/fig3_real_state_outcomes.pdf/png` (regenerated, dynamic item
count already supported from an earlier fix).

**Files touched:** `.venv312/` (new, gitignored), `.gitignore` (added
`.venv312/`, was previously missing), `tests/run_real_state_groundtruth.py`
(added `CUDA_VISIBLE_DEVICES="-1"` to the sandbox env), `requirements.txt`,
`reports/real_state_groundtruth_report.md`, `reports/real_state_eval_report.md`,
`tests/real_state_groundtruth.json`, `tests/real_state_eval_raw_answers.json`,
`paper/draft.md`, `paper/main.tex`, `README.md`, figures.

**Not done / still open:** `tensorflow_15.ipynb` remains unexecutable in the
batch harness (flaky network download, not pursued further -- diminishing
returns for one notebook); no attempt made to increase the per-cell timeout
specifically for large-download cells, which might fix it but wasn't tried
given the honest "network flakiness" framing was judged sufficient.

**Next: marimo experiment**, per the user's explicit request to do this
after the tensorflow environment work.

---

## 2026-09-06 — Non-OpenAI models on the stateful NIAH grid, via OpenRouter's free tier

**Motivation:** the longest-standing blocked item on the backlog ("Non-OpenAI
model on the stateful NIAH grid") — previously blocked because only
`OPENAI_API_KEY` was configured. User provided an `OPENROUTER_API_KEY`.

**What was done:**
1. Added `OPENROUTER_API_KEY` to `.env` (gitignored; never echoed in any
   output). Verified `.env`'s gitignore coverage before proceeding.
2. Fetched OpenRouter's live model catalog directly
   (`https://openrouter.ai/api/v1/models`) rather than trusting
   training-data-era assumptions about free-tier availability, and filtered
   for `pricing.prompt == "0"`. Confirmed: **no OpenAI, Anthropic, or
   proprietary Google (Gemini) models are on the free tier** — free tier is
   open-weight/smaller-lab models only. Selected two candidates for genuine
   vendor diversity: NVIDIA Nemotron-3-Super-120B and MiniMax-M3.
3. **Verified reliability before committing to a real run**: `z-ai/glm-5.2:free`
   (initially the top candidate on paper) turned out to be congested/flaky on
   OpenRouter's shared free pool — hit a 429 and then a full timeout on
   retry, exactly the flakiness OpenRouter's own docs warn about for free
   variants. Dropped it rather than fighting it. Nemotron and MiniMax-M3 both
   answered correctly and quickly (0.6–2.3s) across 3 reliability-check
   trials each — used these two.
4. Extended `tests/run_niah_v2.py` to support an OpenAI-compatible
   third-party base URL (`NIAH_API_BASE` env var, falls back to
   `OPENROUTER_API_KEY`), a generous `max_tokens` for OpenRouter calls (some
   free models default to reasoning-enabled and can exhaust a small implicit
   budget on internal reasoning before writing an answer), and env-var
   overrides for `NIAH_LENGTHS`/`NIAH_DEPTHS`/`NIAH_CONDITIONS` so a reduced
   grid could be run without hacking the script.
5. **Sized the run to the free-tier rate limit**: OpenRouter's free-model
   budget (verified from their own docs) is 50 requests/day shared across
   the whole account (all free models combined) unless $10+ has been spent
   historically, plus a 20/min cap. Ran a reduced grid — 1 length (30k) × 3
   depths × 2 trials × 3 conditions (`raw`/`plain_strip`/`ours`, skipping
   the ablations since those are already covered by the OpenAI-model runs)
   — 18 calls per model, 36 total, safely under the 50/day shared cap with
   retry buffer.

**Result:** both non-OpenAI models replicate the pattern seen across all 9
OpenAI models exactly — `raw` imperfect and non-monotonic (MiniMax-M3 0%, the
worst in the entire 11-model curve; Nemotron-3-Super 50%, mid-pack), `ours`
100% on both. Neither vendor contradicted the finding.

**Fixed a latent bug while integrating**: `tests/compile_model_curve.py`'s
model-name extraction regex only matched `gpt-*` filenames, so it would have
silently mis-labeled both new non-OpenAI reports as `gpt-4o` (or dropped
them). Generalized `model_of()` to strip the known prefix/suffix/condition
tokens instead of pattern-matching on `gpt-`. Same latent bug existed in
`paper/figures/make_figures.py`'s `fig_model_curve()` regex — fixed there too
and verified the regenerated figure shows all 11 models correctly (visual
check via `Read` on the rendered PNG).

**Propagated to:** `paper/draft.md`, `paper/main.tex` (abstract, §5.2 table +
reading, Limitations — recompiled, builds clean, 9 pages, no undefined
references), `README.md`, `reports/model_curve_report.md` (auto-regenerated,
now 11 models), `paper/figures/fig1_model_curve.pdf/png` (regenerated).
Explicitly worded every addition as "n=2, reduced grid, spot check" — not
inflated into a broad cross-vendor generality claim, since 2 models on a
smaller grid is not that.

**Files touched:** `.env` (new key, not committed), `tests/run_niah_v2.py`,
`tests/compile_model_curve.py`, `paper/figures/make_figures.py`,
`reports/model_curve_report.md`, `reports/niah_v2_stateful_raw-plain_strip-ours_nvidia-nemotron-3-super-120b-a12b:free_report.md`
(new), `reports/niah_v2_stateful_raw-plain_strip-ours_minimax-minimax-m3:free_report.md`
(new), `paper/draft.md`, `paper/main.tex`, `README.md`, figures.

**Not done:** true broad cross-vendor validation (would need many more
non-OpenAI models and/or a paid tier to run the full 4-length grid without
rate-limit constraints) — this closes the blocked item honestly at
spot-check scale, not at the scale the original backlog item implicitly
envisioned.

---

## 2026-09-06 (later) — Themisto failure-mode breakdown: measured, and the published explanation was wrong

**Motivation:** the last item on the backlog list ("measure, don't infer, why
preprocessing hurts on Themisto") from several turns ago.

**What was done:** re-ran `tests/run_themisto_eval.py` (same 15 items, same
`seed=42`, small cost) with a modified script that persists full prompts and
answers (`raw_prompt`, `preprocessed_prompt`, `raw_answer`,
`preprocessed_answer`), not just correctness booleans as before. Reproduced
the original 40.0%/26.7% aggregate result exactly, then inspected every
preprocessed-wrong item directly.

**Result — the published explanation was factually wrong for the items that
actually matter:**
1. **9 of 11 "preprocessed-wrong" items are also wrong under raw** — both
   formats guessing on data neither has access to (e.g. pickle file shapes
   never shown in history). These don't discriminate anything about
   preprocessing and shouldn't be part of the explanation.
2. **Only 2 of 15 items decide the entire raw-vs-`ours` accuracy gap**
   (exactly matches 40.0% − 26.7% = 13.3pp = 2/15). Direct inspection of
   both: **the correct value was present verbatim in the preprocessed
   prompt in both cases** — not stripped, not lost, contradicting the old
   "static analysis can't provide truncated-out values" explanation.
3. **What actually differs, measured by character distance:** the
   variable-state table sits between the code/output history and the query,
   pushing the correct evidence 2.7x and 7.7x farther from the point of
   prediction (in the two decisive items respectively) than in raw. Both
   wrong preprocessed answers matched a closer-but-incorrect earlier value
   shown in the same prompt — a lost-in-the-middle/distraction effect, not
   an information-loss effect.

**Corrected framing:** structure (a variable-state table) is a net negative
specifically when there's no token bloat to justify the added distance to
the query — not evidence that static analysis is blind to runtime values in
general. This is a more precise, more defensible negative result than the
original.

**Propagated to:** `reports/themisto_failure_mode_breakdown.md` (new, full
analysis), `reports/themisto_report.md` (corrected explanation, both the
saved file and the eval script's report-generation template so future
re-runs stay accurate), `tests/run_themisto_eval.py` (now persists full
prompts/answers), `paper/draft.md`, `paper/main.tex` (recompiled, builds
clean, 9 pages, no undefined references), `README.md` (results table row +
roadmap item marked done).

**Files touched:** `tests/run_themisto_eval.py`, `tests/themisto_results.json`
(now includes full prompts/answers), `reports/themisto_report.md`,
`reports/themisto_failure_mode_breakdown.md` (new), `paper/draft.md`,
`paper/main.tex`, `README.md`.

---

## 2026-09-06 — Acted on the feasibility research's open questions: related work, Tier-3 framing, environment-branching test

**Motivation:** `outputs/notebook-preprocessor-feasibility.md` (a full deep-research
cycle: plan → 3 researcher subagents → lead-authored draft → verifier
citation pass → reviewer verification pass that found 2 FATAL + 9 MAJOR
issues → lead-authored revision fixing all of them) left several concrete,
actionable open questions. Acted on the three that were cheap and
direct (no new credentials, no new experiments beyond a static check).

**1. Added CRABS, LongDS-Bench, DSAgentBench to the paper's related work**
(`paper/draft.md`, `paper/main.tex` with 3 new `\bibitem`s and `\cite`s).
CRABS (COLM 2025) is explicitly framed as validating a static+LLM hybrid
approach class (closer to this project's optional Stage 2 than its
zero-cost Stage 1), evaluated on cleaner "highly-upvoted" notebooks than
this project's crashed-notebook corpus — both caveats carried over
faithfully from the feasibility research rather than smoothed into an
unqualified "prior work validates us" claim. LongDS-Bench and DSAgentBench
are added as independent 2026 evidence that state-tracking during notebook
analysis remains unsolved at the agent level (48.45% and 56.70% best-model
accuracy respectively).

**2. Added a Tier-3 cost note, not a correction** (the paper never actually
made the flawed "cheap kernel-free check" claim that an earlier draft of the
feasibility research briefly made and then walked back — the paper's
existing "runtime verify... when a kernel is permissible" framing was
already correctly scoped). Added FlowBook's ~70ms/cell dynamic-instrumentation
figure as supporting evidence that this existing restriction is the right
call, not overly conservative, in both `paper/draft.md` and `paper/main.tex`
Limitations sections.

**3. Tested the environment-branching inference directly against this
project's own real-notebook corpus — inconclusive, honestly reported.**
Wrote `tests` were not needed; a direct one-off analysis script cross-tabulated
the 41-item ground truth against a regex for environment-dependent branching
(`torch.cuda.is_available()`-style checks). Found a striking raw correlation
(88% vs. 48% wrong-answer rate) that **did not survive a confound check**:
all 8 flagged items turned out to be the exact same items already fully
explained by the `execution_count`-sort edge case (100% overlap by
`phantom_in_visual`/`ec_order_value=None` signature) — zero independent data
points existed in this corpus to test the hypothesis. Documented as an
honest negative/inconclusive result in `reports/environment_branching_check.md`,
and the corresponding Open Question in `outputs/notebook-preprocessor-feasibility.md`
was updated (struck through, marked tested-inconclusive) rather than left
open or silently deleted.

**Files touched:** `paper/draft.md`, `paper/main.tex` (recompiled, builds
clean, 8 pages, no undefined references), `reports/environment_branching_check.md`
(new), `outputs/notebook-preprocessor-feasibility.md` and its `-revised.md`
draft counterpart (Open Question 3 updated with the test result).

**Not done:** the marimo-conversion-reliability experiment (Open Question 4
from the feasibility research) — this is genuinely new experimental work
(would require installing marimo and running its Jupyter-to-marimo
conversion on a JunoBench sample), not a quick synthesis task, and was
flagged to the user as medium priority rather than executed unilaterally.

---

## 2026-09-05 (narrative pass) — Full read-through of `paper/main.pdf`; fixed drift introduced by piecemeal edits

**Motivation:** several sections were revised independently across this
session's corrections (real-notebook numbers, judge fix, execution-order
edge case). Read the fully compiled PDF end-to-end to check the pieces still
cohere, rather than trusting that section-local edits summed to a coherent
whole.

**Found and fixed, in order of severity:**
1. **Stale figure**: Figure 1 (token reduction chart) still showed the old
   "median 91.5%" baked into the image after the text was updated to 91.2%
   following the `execution_order_risk` annotation's token-overhead
   re-measurement -- I had updated the report and prose but forgotten to
   re-run `paper/figures/make_figures.py`. Fixed by regenerating all three
   figures from the current reports.
2. **Stale contribution/abstract counts**: the Introduction's contributions
   list and `draft.md`'s equivalent still said "five static state
   annotations" after a sixth (`execution_order_risk`) was added; the
   Limitations section correctly said "six" -- an internal inconsistency a
   careful reader would have caught immediately. Fixed both to "six" with
   the new annotation named.
3. **Softened conclusion that contradicted the paper's own honest
   findings**: the Conclusion section still read "transfers with an honest,
   quantified gap to real notebooks" -- true but vague enough to let a
   skimming reader miss that the *accuracy* claim doesn't transfer at all
   (only *reach/coverage* does), which is the paper's most important
   correction this session. Rewrote the conclusion in both `main.tex` and
   `draft.md` to state the reach-vs-accuracy split explicitly, matching the
   abstract's honesty rather than reverting to older, softer language.
4. **Minor rounding inconsistency**: a Wilson CI upper bound was written as
   both 49% and 50% in different places (raw/`ours` overall-TRUTH interval,
   true value 49.5%) depending on rounding method used when each passage
   was written. Standardized on 49% (matching the source report) in both
   `main.tex` and `draft.md`.
5. **Overloaded terminology**: "100% for all conditions at every cell" in
   the NIAH section used "cell" to mean "grid cell" (depth × length),
   which reads as "notebook cell" everywhere else in the paper. Clarified
   to "every grid cell (depth $\times$ length)".

**Verification:** recompiled `main.pdf` after each fix (final: 8 pages, up
from 7 -- the honest conclusion rewrite is longer than the vague original,
which is an acceptable tradeoff); re-ran the full test suite (still passes).

**Not done:** a copy-edit pass for prose style/typos beyond factual/
numerical consistency (out of scope for a "does it still cohere" pass); a
second read specifically of `docs/GUIDE.md` and `gaps_analysis.md`, which
may also reference numbers that changed this session and were not checked
in this pass.

---

## 2026-09-05 (final) — Implemented the fix: `execution_order_risk` detect-and-flag annotation

**Motivation:** the previous entry quantified the `execution_count`-sort
edge case at 26.6% of notebooks but deliberately stopped short of fixing
it, flagging the design decision (detect-and-flag vs. hybrid reordering) as
something to decide rather than do unilaterally. Chose detect-and-flag: the
lower-risk option, and consistent with the paper's existing three-tier
philosophy (flag what can't be confidently resolved rather than guess).

**What was implemented:**
1. `src/state_extractor.py`: added `_CellTimeVisitor` (a statement-ordered
   AST visitor, ported from the validated, bug-fixed logic in
   `tests/run_execution_count_consistency_scan.py` -- explicitly NOT
   re-deriving the whole-cell-aggregation bug that inflated that scan's
   first draft to 100%) and
   `VariableStateExtractor.detect_execution_order_violations`, restricted
   to the import-specific signal validated as low-noise.
2. `src/preprocessor.py`: wired this in after cells are sorted by
   `execution_count`, adding a new per-cell `execution_order_risk` field
   alongside the existing `divergence_risk` annotation. Wording is
   deliberately hedged ("treat this cell's position as uncertain, not
   necessarily broken") to avoid inventing a false resolution.

**Verification before declaring this done:**
- Ran directly against `numpy_1.ipynb`: fires on exactly the 6 cells
  identified by manual inspection in the earlier entry (ec=2, 3, 4, 21, 23,
  25), correctly naming `torch`, `transforms`, `ImageFolder`, `DataLoader`,
  `nn`.
- Ran the full existing test suite (`tests/test_pipeline.py` -- 13 tests,
  `tests/test_state_annotations.py` -- 13 checks, `tests/test_multi_agent.py`):
  all still pass unmodified.
- Re-ran `tests/run_real_notebook_validation.py` (the $0, no-LLM,
  40-notebook token-reduction measurement) to check the new annotation's
  real cost: aggregate reduction unchanged at 96.4%; median dropped 0.3
  percentage points (91.5% → 91.2%) -- negligible, and the drop is
  concentrated (as expected) in smaller/more-affected notebooks like
  `torch_6.ipynb` and `torch_4.ipynb` rather than spread evenly.

**Propagated the updated 91.2% median number everywhere it appeared:**
`paper/draft.md` (abstract + §5.1 + limitations), `paper/main.tex`
(same, plus a new `\label{sec:limitations}` for cross-referencing;
recompiled, builds clean, no undefined references, 7 pages), `README.md`
(token-reduction results row, edge-case results row, interpretation
guardrails paragraph, Preprocessing Workflow section).

**What was NOT done:** a hybrid reordering fix (moving a violating
import/definition earlier when safe). Left open as a possible future
improvement -- detect-and-flag was a deliberate choice, not a placeholder
for "couldn't figure out the real fix."

**Where this leaves the paper:** every major finding from this session's
investigation chain -- widen real-notebook ground truth, audit the judge,
investigate the dominant DECOY case, quantify the edge case corpus-wide --
now has a corresponding action taken (more data, a bug fix, a documented
limitation, or an implemented fix) rather than being left as an open
thread. The paper is narrower in its claims than at the start of this
session (real-notebook accuracy advantage is gone; reach/coverage is what
remains) but every claim that remains is now more heavily verified.

---

## 2026-09-05 — Corpus-wide quantification: 26.6% of notebooks have the execution_count-sort edge case

**Motivation:** the previous entry found a real edge case in
`execution_count`-sort (verified in `numpy_1.ipynb`) but explicitly did not
measure how common it is corpus-wide. Built the recommended $0, no-LLM
static scan.

**What was done:** wrote `tests/run_execution_count_consistency_scan.py` --
for each of the 111 JunoBench notebooks, sorts cells by `execution_count`
(same as the preprocessor and ground-truth methodology) and statically
checks whether any cell uses a name before any prior cell in that order
defines it, despite the name being defined somewhere in the notebook.

**A bug was found and fixed during this pass, before trusting the number:**
the first version aggregated used/defined names at the whole-cell level,
losing intra-cell statement order. This spuriously flagged the extremely
common pattern `x = f(); x.method()` (define then use within the same
cell) as a violation, inflating the naive result to **100% of notebooks
flagged** -- implausibly high. Fixed by processing statements in original
order and updating the "defined so far" set incrementally within each cell;
verified the fix against `seaborn_6.ipynb`, a notebook independently known
(from `reports/out_of_order_scan_report.md`) to be execution-monotonic,
which correctly dropped to 0 violations after the fix (it had shown a false
positive on `model` before).

**Even after the fix, a second confound remained:** many flagged names were
generic single-letter/common identifiers (`i`, `x`, `column`, `c`, `f`)
reused for unrelated purposes across different, unrelated cells -- a static
def-before-use scan cannot distinguish legitimate reuse from a genuine
reordering hazard. Added an import-specific filter (restricting to names
ever bound via `import`/`from...import`, which are essentially never
coincidentally reused for something unrelated) as the cleaner headline
signal, reporting both counts transparently rather than picking one.

**Final, corrected result:**
- Broad count (noisy, includes generic-identifier collisions): 95/109
  (87.2%) notebooks, 927 instances -- reported for transparency, not cited
  as the headline.
- **Import-specific count (cleaner signal): 29/109 (26.6%) notebooks, 134
  instances.** This is now the paper's quantified rate for this edge case.

**Documented in:** `reports/execution_count_consistency_report.md` (new,
full per-notebook detail), `reports/execution_count_reordering_limitation.md`
(updated with the corpus-wide rate), `paper/draft.md`, `paper/main.tex`
(recompiled, builds clean, 7 pages), `README.md` (new results-table row).

**What was NOT done:** did not implement the actual fix (detecting and
flagging these cells in `src/preprocessor.py`, or re-running any
affected evaluation). That is a design decision -- how should the
preprocessor represent "this cell's `execution_count` position may not be
runnable"? -- flagged for a deliberate choice, not made unilaterally, since
it changes core logic used throughout §5.1–§5.4.

**Recommended next step:** implement the Tier-2 "detect and flag"
annotation in `src/preprocessor.py` (surface a per-cell warning analogous to
the existing `divergence_risk` annotation), then decide whether to keep pure
`execution_count` ordering (with a visible warning) or attempt a hybrid
reordering that resolves detected violations where safe to do so.

---

## 2026-09-05 (later) — Investigated `ours`'s remaining DECOY cases; found a real edge case in `execution_count`-sort itself

**Motivation:** after the judge fix removed `ours`'s apparent accuracy edge,
the planned next step was to check whether the preprocessor's own
confidence/ghost-status annotations could reduce its DECOY rate (16/41, the
highest of any condition post-fix). Investigated the dominant contributor
first: 8 of `ours`'s 16 DECOY outcomes come from a single notebook,
`numpy_1.ipynb`.

**What was found:** not a preprocessor calibration bug, but a real,
verified edge case in the core "reorder by `execution_count`" mechanism
itself (the paper's Tier-1 "resolve" claim for Root Cause A).
`execution_count` records only a cell's *last* run. `numpy_1.ipynb`'s import
cell (`import torch`, etc.) carries `execution_count=27` because it was
re-run late (e.g. after a kernel restart), while a cell needing `torch`
(`device = torch.device(...)`, plus 5 other hyperparameters) carries
`execution_count=2` from before the restart. Sorting by `execution_count` —
which both `src/preprocessor.py` and the ground-truth
re-execution methodology (`tests/run_out_of_order_scan.py`,
`src/ground_truth_extractor.py`) do — places the import 10th of 15 cells,
after six cells that use it, producing a sequence that raises `NameError` on
replay in a fresh kernel. This is exactly why those 6 hyperparameters show
`ec_order_value = None` ("never defined") in the ground truth: not because
the real user's session never defined them, but because the reordering
assumption itself broke for this notebook. Full detail and one verified
example in `reports/execution_count_reordering_limitation.md`.

**Why this matters more than a simple calibration fix would have:** it
is a previously-undocumented failure mode of the paper's core Tier-1
mechanism, not just the preprocessor's variable-table confidence. It also
means some fraction of the n=41 real ground-truth items are contaminated by
this specific mechanism rather than measuring genuine out-of-order-execution
divergence (though the divergence itself — visual order disagreeing with
execution-count order — is still real; only the *interpretation*, "the user's
session never defined this," is what's affected).

**What was NOT done in this pass** (a deliberate scope boundary, not an
oversight): did not re-run the n=41 ground-truth extraction or LLM
evaluation after this finding, and did not quantify how many of the 112
JunoBench notebooks exhibit this pattern corpus-wide. Fixing it requires a
design decision (should the preprocessor detect and flag
count-order-dependency violations as a new Tier-2 annotation, or attempt a
hybrid reordering using static def-before-use analysis to break ties?) that
changes core logic used throughout §5.1–§5.4, and re-running everything
afterward would cost real money and time — flagged for a deliberate decision
rather than executed unilaterally.

**Documented in:** `reports/execution_count_reordering_limitation.md` (new),
added as a limitation to `paper/draft.md`, `paper/main.tex` (recompiled,
still builds clean, 7 pages), and `README.md`.

**Next recommended step:** run the cheap corpus-wide check described in
`reports/execution_count_reordering_limitation.md` (a lightweight
def-before-use AST scan over the `execution_count`-sorted order for all 112
JunoBench notebooks, no LLM calls, no re-execution needed) to learn whether
this is a rare fluke (one notebook) or common enough to need a real fix
before the next round of evaluation.

---

## 2026-09-05 — Judge-bug audit: found and fixed a 24%-disagreement grader bug; real-notebook §5.4 downgraded again

**Motivation:** continuing the prior entry's plan ("either accept the more
modest claim, or invest in a human-annotated subset to check judge
reliability"). Chose the second path: independently re-graded a sample of
the automated judge's outcomes before trusting the n=41 numbers further.

**What was done:**
1. Stratified-sampled 25 of 123 answer rows from `reports/real_state_eval_report.md`
   (seed=42) and independently classified each against the stored ground-truth
   candidates (`tests/real_state_groundtruth.json`), without calling any LLM
   classifier — a second-pass manual audit, not a human-subjects inter-rater
   study (the auditor is this agent, not an independent human).
2. Found **19/25 (76%) agreement**; all 6 disagreements shared one
   mechanism: whenever one ground-truth candidate was "never defined," the
   judge credited *any* concrete answer to the other candidate without
   checking the value actually matched. Confirmed with a reproducible
   example (`numpy_1.ipynb`/`device`: identical answer content `cuda` graded
   DECOY in one condition and TRUTH in another; correct answer is NEITHER
   for both, since `cuda` matches neither `cpu` nor "never defined").
   Full detail: `reports/judge_validation_report.md`.
3. Rewrote the judge prompt in `tests/run_real_state_eval.py` to require an
   explicit literal/close value match and default to NEITHER on
   uncertainty. Also added persistence of full untruncated model answers to
   `tests/real_state_eval_raw_answers.json` (previously only a 160-char
   truncated snippet was saved, which would have blocked any future
   judge-only re-audit).
4. Re-ran the full eval (`tests/run_real_state_eval.py`, same 41 items,
   same gpt-4o answer model) with the fixed judge.

**Result — the fix removed `ours`'s apparent edge entirely:**
- Before fix (previous entry, still judge-buggy): raw 34%, plain_strip 41%,
  ours 46% overall-TRUTH.
- After fix: **raw 34%, plain_strip 39%, ours 34%** — `ours` and `raw` are
  now tied, `plain_strip` nominally (not significantly) leads. All three
  95% Wilson intervals overlap heavily.
- Mechanism: `ours`'s variable table tends to produce more confident,
  concrete-looking guesses for phantom/never-defined variables than `raw`
  or `plain_strip`; the buggy judge disproportionately rewarded these
  guesses as TRUTH regardless of whether the specific value was correct.
- **What remains robust across all three passes (n=13, n=41 pre-fix, n=41
  post-fix): the reach/coverage gap.** raw JSON overflows context on ~51%
  of real divergent items; `ours`/`plain_strip` reach 93–98%. This is now
  the paper's only defensible real-notebook claim.

Updated (again) `paper/draft.md`, `paper/main.tex` (added a new "Judge
validation" subsection; recompiled `main.pdf` — builds clean, 7 pages),
`README.md`, and regenerated `paper/figures/fig3_real_state_outcomes.pdf/png`.

**Files touched:** `tests/run_real_state_eval.py` (judge prompt rewrite +
raw-answer persistence), `tests/real_state_eval_raw_answers.json` (new),
`reports/judge_validation_report.md` (new), `reports/real_state_eval_report.md`,
`paper/draft.md`, `paper/main.tex`, `README.md`.

**Why report three successive downgrades instead of just the final number:**
each correction (n=13→n=41, then judge audit) moved the conclusion in the
same direction — more modest — which is itself evidence the final number is
closer to the truth than the first, and a useful methodological cautionary
tale about small-n LLM-graded-by-LLM real-data evaluations. This is preserved
in the paper text rather than silently overwritten.

**Next recommended step:** the paper's real-notebook contribution is now
cleanly scoped to *reach/coverage*, which is well-supported. If a future pass
wants to re-establish a per-item accuracy claim, it would need either (a) a
true human-annotated ground truth (not just a second LLM or a second agent
pass) for a proper inter-rater reliability number, or (b) enough additional
items (likely 150+) for the current point-estimate gap, if real, to clear a
95% CI at this effect size.

---

## 2026-09-04 — Widen real-notebook ground truth (13 → 41 items); honest downgrade of §5.4

**Motivation:** internal review flagged the real-notebook state-accuracy
result (§5.4 of the paper) as the load-bearing evidence with the thinnest
sample (n=13, 6 notebooks), gated by `torch`/`tensorflow` not being installed
in the ground-truth sandbox.

**What was done:**
1. Installed `torch` 2.14.0 and `torchvision` 0.29.0 (CPU wheels) for
   Python 3.14. Note: the generic PyPI index's CUDA-enabled `torch` wheel
   (554 MB) reliably stalled mid-download; PyTorch's own CPU wheel index
   (`https://download.pytorch.org/whl/cpu`, ~196 MB) worked without issue.
   Also needed `sympy`, `networkx`, `fsspec`, and `mpmath<1.4` (PyPI's default
   `mpmath` 1.4.1 is incompatible with `sympy>=1.13.3`, torch's pin).
   `tensorflow` has **no published wheel for Python 3.14** at time of
   writing — `tensorflow_*` JunoBench notebooks remain excluded from ground
   truth; this is a real, documented coverage gap, not an oversight.
2. Re-ran `tests/run_real_state_groundtruth.py` (deterministic, subprocess
   sandbox re-execution, **$0 cost, no LLM calls**). Usable notebooks rose
   from 59/67 to 60/67; notebooks with ≥1 order-divergent variable rose from
   6 to 14; total ground-truth items rose from 13 to **41**.
3. Re-ran `tests/run_real_state_eval.py` (gpt-4o answers + gpt-4o-mini judge)
   on all 41 items. Dry-run cost estimate was ~$3.37; actual run completed
   without incident.
4. Added a Wilson-CI statistical summary to
   `reports/real_state_eval_report.md` and to the paper.

**Result — this changed the paper's headline claim, and the change itself is
now documented as a finding:**
- At n=13: `ours` looked like a clean win (6 TRUTH vs. raw's 3, i.e. 2x).
- At n=41: `ours` (46% overall-TRUTH), `plain_strip` (41%), and `raw` (34%)
  have **overlapping 95% Wilson intervals** — not statistically
  distinguishable. Raw JSON, when it fits in context, is actually the most
  accurate per item (70% TRUTH-when-reached) but only reaches 49% of items
  (context overflow). `ours` and `plain_strip` reach ~93–98% of items.
- **What survived the larger sample:** the *reach/coverage* gap (raw
  overflows on ~51% of real divergent items across both n=13 and n=41; the
  compressed formats almost always fit). **What did not survive:** the claim
  that `ours`'s reordering + variable table beats plain compression on
  per-item accuracy once an answer is reached — that comparison is now a
  coin flip within noise.
- Updated `paper/draft.md` (abstract, §5.4, limitations), `paper/main.tex`
  (same sections; recompiled `main.pdf` successfully), `README.md` results
  table, and regenerated `paper/figures/fig3_real_state_outcomes.pdf/png`
  (the figure script now reads `n` dynamically from the report instead of a
  hardcoded 13).

**Files touched:** `reports/real_state_groundtruth_report.md`,
`reports/real_state_eval_report.md`, `tests/real_state_groundtruth.json`,
`tests/run_real_state_eval.py` (added Wilson-CI summary block for future
reproducibility), `paper/figures/make_figures.py` (dynamic item count),
`paper/draft.md`, `paper/main.tex`, `README.md`, `requirements.txt` (new).

**Not done in this session (deferred):**
- Non-OpenAI model on the stateful NIAH grid (blocked: only `OPENAI_API_KEY`
  is configured in `.env`; no Anthropic/Google API key available even though
  the `anthropic` package is installed).
- Human validation of the gpt-4o-mini judge on a subset.
- Measured (not inferred) breakdown of the Themisto failure mode.
- tensorflow-backed notebooks remain unexecutable pending a tensorflow wheel
  for Python 3.14, or a separate older-Python environment for that subset.

**Next recommended step:** either accept the more modest, honest real-notebook
claim (reach, not per-item accuracy) as the paper's final position, or invest
in a human-annotated subset + a second answer model to see if the
`ours` vs. `plain_strip` gap becomes distinguishable with more power — do not
re-inflate the claim without new evidence.

## 2026-09-06: Cross-model curve expanded to 15 models / 7 vendors; two new failure modes found and fixed in `run_niah_v2.py`

**Motivation:** the paper's own Limitations section admitted the "3 vendors"
claim was a thin spot check (2 non-OpenAI models, reduced grid, free-tier
OpenRouter only). User asked to check more OpenRouter models given a
"free API, no budget ceiling" constraint, then separately supplied a second
OpenRouter key, a Google Gemini API key, and a Zhipu/GLM API key mid-session.

**Live-checked OpenRouter's actual free-model list** (`GET /api/v1/models`,
filtered `:free` suffix) rather than trusting generic secondhand summaries —
found 19 free models at the time of checking, notably **zero** free-tier
options from Anthropic, Meta, Mistral, DeepSeek, or Qwen/Alibaba (contradicting
some generic web-search summaries), only: Cohere, Google/Gemma, InclusionAI,
Poolside, NVIDIA (several variants), MiniMax, ThinkingMachines, Liquid, and
z-ai/glm-5.2:free (already dropped in an earlier session for reliability).

**Piloted 6 new-vendor candidates before committing to grid runs** (lesson
from the earlier z-ai/glm-5.2:free episode): `google/gemma-4-31b-it:free`,
`cohere/north-mini-code:free`, `thinkingmachines/inkling:free`,
`poolside/laguna-s-2.1:free`, `inclusionai/ling-3.0-flash-fin:free`,
`nvidia/nemotron-3-ultra-550b-a55b:free`. Found `thinkingmachines/inkling:free`
is not usable via the standard chat completions API at all (403, "only
available on agentic harnesses") — excluded immediately, no grid attempt.

**Ran the reduced stateful grid (1 length=30k x 3 depths x 1 trial x 3
conditions = 9 calls/model) on 4 successful new vendors:**
- `cohere/north-mini-code:free`: raw 0/3, plain_strip 0/3, ours 3/3.
- `inclusionai/ling-3.0-flash-fin:free`: raw 1/3, plain_strip 0/3, ours 3/3.
- `poolside/laguna-s-2.1:free`: raw 2/3, plain_strip 0/3, ours 3/3.
- `google/gemma-4-31b-it:free`: **dropped** — exhausted all 6 retries (up to
  120s backoff each) with persistent 429s; genuinely congested, not a fluke.

**`nvidia/nemotron-3-ultra-550b-a55b:free`: dropped after root-causing a
second OpenAI-SDK-invisible failure mode.** First attempt crashed the script
outright (`TypeError: 'NoneType' object is not subscriptable`) because
OpenRouter can return HTTP 200 with `choices: null` and an embedded top-level
`error` field instead of raising an exception — the SDK doesn't surface this
as an error, so `ask_model()` blew up on `res.choices[0]`. **Fixed**
`tests/run_niah_v2.py::ask_model` to detect `not res.choices` and retry with
the same backoff as a rate limit. Re-ran with the fix; got a clean, direct
`"Upstream error from Nvidia: Service temporarily overloaded"` (HTTP 502).
**Verified this is genuinely provider-side, not our account**, by testing the
identical call with a second, completely independent OpenRouter API key
(user-supplied) — same instant failure, ruling out any per-key rate-limit
explanation. Dropped, consistent with the project's "don't fight confirmed-
flaky providers" policy (same call made on z-ai/glm-5.2:free earlier).

**Compiled OpenRouter's key-info endpoint** (`/api/v1/auth/key`) to check the
account's actual daily-request-cap state before running more calls — found
`is_free_tier: true`, `usage_daily: 0` at the time of checking (fresh account,
no historical spend), consistent with the previously-documented 50 free-
requests/day shared cap still applying; sized the new-model grid accordingly
(9 calls/model instead of the earlier 18/model design, to fit 4-5 new models
in one day's budget) — an explicit, documented power tradeoff.

**Investigated whether this agent's own Claude subscription could be reused
for Anthropic API testing — concluded no, and explained why on the record:**
no `ANTHROPIC_API_KEY` exists anywhere in the environment or workbench config
(checked directly); a chat subscription (Pro/Max) is not the same product as
a portable Anthropic Developer API key, and there is no mechanism to extract
this agent's own runtime authentication for reuse in an external script.

**Checked Kimi/Moonshot AI on OpenRouter** (live query): 9 variants exist
(`kimi-k2` through `kimi-k3`), none free (`$0.45-$3.00/M input`). User chose
to skip it and stay free-tier-only rather than spend even a few cents.

**User supplied a Google Gemini API key** (`AIzaSyAKGE...`) for "the latest
models." Live-queried Gemini's own `/v1beta/models` endpoint (50 models found)
rather than guessing model names. Confirmed via Google's OpenAI-compatible
endpoint (`https://generativelanguage.googleapis.com/v1beta/openai/`) that
Pro-tier models (`gemini-3.1-pro-preview`, `gemini-2.5-pro`) have zero usable
free quota on this key (immediate 429/404), while Flash-tier models work.
**Root-caused a confusing, hard-to-diagnose intermittent failure** on the
newest Flash releases (`gemini-3.8-flash`, `gemini-3.7-flash`) and even the
established `gemini-2.5-flash`: the actual full-size (~31k-token) benchmark
prompt would intermittently fail inside the script with HTTP 400 "Please pass
a valid API key" (misleading — not an auth problem) or HTTP 503 "This model
is currently experiencing high demand" (UNAVAILABLE), while an ad-hoc retry
of the *identical* request moments later via raw `httpx` or a fresh Python
process would succeed cleanly. Diagnosed this as intermittent free-tier
capacity throttling on large requests specifically, mislabeled by Google's
OpenAI-compatibility shim rather than returned as a clean 429. **Fixed**
`ask_model()` to also retry on `"Please pass a valid API key"` and
`"UNAVAILABLE"/"high demand"/"503"` substrings, with the same exponential
backoff as a genuine rate limit. Despite the fix, repeated full-grid attempts
across three different Gemini Flash models (3.8, 3.7, 2.5) each still
exhausted all 6 retries (up to ~8 minutes of cumulative backoff) inside the
script, while isolated one-off follow-up calls kept succeeding — concluded
this is a real, currently-unresolved intermittent-capacity issue specific to
sustained/back-to-back large-prompt free-tier traffic on Gemini, not a script
bug, and the Gemini data point was **not completed this session** (open, not
fabricated or silently dropped from consideration).

**User supplied a Zhipu/Z.ai GLM API key**, restricted scope explicitly to
`glm-5.3-flash` only. Looked up the correct model code and both possible base
URLs (`https://api.z.ai/api/paas/v4` international vs.
`https://open.bigmodel.cn/api/paas/v4` China) via live web search rather than
guessing; both authenticated successfully with the supplied key. Piloted with
higher `max_tokens` after an initial empty-content result revealed the same
reasoning-token-budget pattern seen on other providers (~88-93 reasoning
tokens per simple question) — confirmed the script's existing `max_tokens:
1024` default gives adequate headroom. **Generalized the script's key
resolution** (previously hardcoded to `OPENROUTER_API_KEY` only) to a fallback
chain (`NIAH_API_KEY` -> `OPENROUTER_API_KEY` -> `GEMINI_API_KEY`), enabling
this and future third-party OpenAI-compatible endpoints without new code
paths. Ran the reduced grid successfully: **glm-5.3-flash: raw 3/3 (100%,
n=3 -- the only model in the entire 15-model curve where raw scored perfectly,
though on a sample too thin to treat as a genuine finding rather than noise),
plain_strip 1/3, ours 3/3.**

**Final model curve: 15 models, 7 vendors** (9 OpenAI + NVIDIA Nemotron-3-
Super-120B + MiniMax-M3 + Cohere North-Mini-Code + InclusionAI
Ling-3.0-Flash-Fin + Poolside Laguna-S-2.1 + Zhipu GLM-5.3-Flash). `ours` =
100% on every single model, no exceptions. `raw` ranges 0% (MiniMax-M3,
Cohere) to 97% (gpt-5, full-grid) with one thin (n=3) 100% outlier
(GLM-5.3-Flash) explicitly flagged as too small a sample to call a real
ceiling rather than noise.

**Propagated to:** `reports/model_curve_report.md` (recompiled via
`tests/compile_model_curve.py`, 15 rows), `paper/figures/fig1_model_curve.pdf/png`
(regenerated, visually checked -- GLM-5.3-Flash's raw dot correctly plots at
100% though its numeric label is crowded out at the very top of the chart,
a cosmetic issue not a correctness one), `paper/main.tex` (abstract, \S5.2 body
+ table + 5 readings + figure caption, Limitations -- recompiles clean, now
**10 pages**, no undefined references), `paper/draft.md` (abstract, \S5.2 table
and prose), `README.md`, `papers/notebook-execution-order-reconstruction.md`
(abstract, contributions list, \S5.3 full section + table, Limitations,
Conclusion -- the standalone from-scratch draft produced in the prior
session). Every instance of "eleven models" / "three vendors" / "two
non-OpenAI models" was searched for and updated; every new claim explicitly
distinguishes the adequately-sampled (full-grid, n=36) models from the
thinly-sampled (n=3-6) new ones, and flags GLM-5.3-Flash's 100% raw score as
unreliable-sample-size rather than folding it into the headline range
uncritically.

**Files touched:** `.env` (new: `OPENROUTER_API_KEY_2`, `GEMINI_API_KEY`,
`GLM_API_KEY` -- all gitignored, verified untracked), `tests/run_niah_v2.py`
(two new retryable-error patterns, generalized key-resolution fallback chain),
`tests/compile_model_curve.py` (no code change, re-run), `reports/
model_curve_report.md`, four new `reports/niah_v2_stateful_raw-plain_strip-
ours_<model>_report.md` files (cohere, inclusionai, poolside, glm-5.3-flash),
`paper/figures/fig1_model_curve.pdf/.png`, `paper/main.tex`, `paper/draft.md`,
`README.md`, `papers/notebook-execution-order-reconstruction.md`.

**Deferred / open:**
- Gemini (any variant) remains untested end-to-end due to unresolved
  intermittent free-tier capacity throttling on large prompts specifically;
  worth retrying at a different time of day or with explicit inter-call
  delays if a genuine Gemini data point is wanted later.
- GLM-5.3-Flash's n=3 sample is too thin to know whether its 100% raw score
  is a genuine capability difference or noise; would need the full 36-trial
  grid to resolve, not attempted this session (user scoped the request to
  "proceed" on the reduced grid, not to expand it further).

## 2026-09-06 (cont.): Restructured `paper/main.tex` into an EMSE-compliant manuscript

**Motivation:** user asked for a full manuscript per EMSE's own submission
guidelines (fetched and reviewed earlier this session at
https://link.springer.com/journal/10664/submission-guidelines).

**Verified real author names for every citation before switching to
author-year format** -- refused to fabricate names. Queried arXiv directly
(`feynman_science_database_search`, source=arxiv, batch `arxiv_get_papers`)
for all 10 arXiv-indexed citations, and web-searched the two non-arXiv
sources (JunoBench -- discovered it actually has a paper, arXiv:2510.18013,
previously cited only as a bare Hugging Face dataset link; and the I-PTC
UC Berkeley technical report, EECS-2026-176, single author Joseph Gonzalez
per Berkeley's own tech-report listing).

**Restructured `paper/main.tex`** (full-file rewrite, then compiled and
visually verified via `document_screenshot`):
- Added `natbib` (`round,authoryear`) and switched every `\cite{}` to
  `\citep{}`; converted the manual numbered `\bibitem` list to full
  author-year entries (`Author A, Author B (Year) Title. Venue/arXiv ID.
  URL/DOI`), alphabetized by first author surname, each including a real
  DOI where one exists (Siddik et al. 2025 -> `10.1016/j.jss.2025.112758`)
  or the canonical arXiv URL otherwise. Added two previously-uncited
  sources mentioned only by name in Related Work (Jupytext, notebookllm)
  as proper "Online document" style entries per EMSE's own reference
  format examples.
- Added title-page fields (author, affiliation, corresponding email, ORCID)
  with **honest bracketed placeholders** for affiliation/email/ORCID --
  explicitly not fabricated, flagged for the author to fill in before
  submission.
- Rewrote the abstract as EMSE's optional structured format
  (Context/Objective/Method/Results/Conclusions), cut from ~250 words
  (right at the boundary on first pass) to a verified 225 words (counted
  programmatically, not estimated).
- Added a Keywords line (6 keywords).
- Added a new `\subsection{Use of large language models and AI agents in
  this study}` inside the Method section, distinguishing LLMs as *answer
  models under test* from LLMs as *research/drafting assistance* (the judge,
  and the coding/drafting agent), per EMSE's explicit authorship-policy
  requirement that LLM use be documented in the Methods section, not
  omitted or buried in an acknowledgments footnote.
- Renamed/restructured the former single `Limitations` section into a
  formal **Threats to Validity** section with Construct/Internal/External
  Validity subsections (standard empirical-SE structure), redistributing
  all existing content rather than duplicating it alongside a separate
  Limitations section.
- Added a closing **Statements and Declarations** section: Funding (none),
  Competing Interests (none declared), Author Contributions, Ethical
  Approval (not applicable, public pre-existing dataset), and a Data
  Availability statement explicitly marked `[PLACEHOLDER]` pending the
  planned new submission-specific GitHub repository (per user's earlier
  explicit instruction to handle repo creation later) -- worded so it is
  obvious this must be completed with a real URL before actual submission,
  not silently left incomplete.

**Verified, not assumed:** recompiled with `latexmk` (12 pages, builds
clean, no errors); grepped the log for "undefined" -- none found; diffed
every `\citep{}` key used in the body against every `\bibitem{}` key
defined in the bibliography with `comm -3` -- zero mismatches in either
direction; screenshotted pages 1, 10, 11, 12 to visually confirm the title
page, Statements and Declarations, and References render correctly and the
structured abstract reads cleanly.

**What was NOT done:** did not create the new GitHub repository (explicitly
deferred by the user to a later step); did not fabricate author
affiliation/email/ORCID; did not attempt Springer's exact camera-ready
LaTeX class, since EMSE's own guidelines state this is unnecessary at
submission ("the compiled PDF will be used for peer-review purposes";
production reformats accepted manuscripts) -- content compliance was the
target, not template compliance.

**Files touched:** `paper/main.tex` (full rewrite), `paper/main.pdf`
(recompiled, 12 pages).

## 2026-09-06 (cont.): Filled in real author affiliation on the title page

User supplied real affiliation: Department of Computer Science and
Engineering, Rajshahi University of Engineering and Technology, Rajshahi,
Bangladesh; explicitly opted out of using an ORCID. Updated `paper/main.tex`
title-page block accordingly, removed the ORCID line entirely (rather than
leaving an empty/placeholder line), and updated the preamble comment
documenting title-page field status. Corresponding-author email remains the
only outstanding placeholder.

**Bug found and fixed during verification**: the first version of the
updated affiliation line overflowed the page's right margin (visually
confirmed via `document_screenshot` on page 1 -- text ran off the page
edge). Fixed by manually breaking the affiliation across two `\textit{}`
lines instead of one long line; recompiled and re-screenshotted to confirm
clean wrapping with no overflow.

**Files touched:** `paper/main.tex`, `paper/main.pdf` (recompiled, 12 pages).

## 2026-09-06 (cont.): Filled in corresponding-author email

User supplied `raiyanrohit10@gmail.com`. Updated `paper/main.tex` title
page and preamble comment. Recompiled, visually verified via
`document_screenshot` -- renders cleanly, no overflow. Title page is now
fully complete: name, affiliation, corresponding email all confirmed by the
author, no ORCID by author's choice.

**Remaining before submission**: only the Data Availability Statement's
repository URL, pending the new GitHub repo the author will create/provide
separately.

**Files touched:** `paper/main.tex`, `paper/main.pdf` (recompiled, 12 pages).

## 2026-09-06 (cont.): Full coherence/correctness proofread of `paper/main.tex`

User confirmed `paper/main.tex` is the sole submission target (not the
longer standalone `papers/notebook-execution-order-reconstruction.md`
draft, which is now treated as a superseded intermediate artifact). Did a
full read-through and structural check rather than assuming the earlier
restructure was error-free:

- **Verified all `\label{}`/`\ref{}` pairs** -- every reference resolves to
  a defined label; two labels (`sec:causes`, `sec:method`) are defined but
  unreferenced, which is harmless (not every anchor needs an inbound ref).
- **Verified both hardcoded section-number cross-references** (`\S2`,
  `\S5.1`) against the actual compiled section/subsection order -- both
  correct.
- **Found and fixed a real, pre-existing numeric error, not introduced this
  session but inherited across multiple prior drafts**: the Threats to
  Validity section claimed the `execution_count`-sort edge case "plausibly
  explain[ed] 8 of the 52 real ground-truth items," attributing all 8 to
  `numpy_1.ipynb`. Checked the primary sources directly
  (`reports/execution_count_reordering_limitation.md`,
  `reports/environment_branching_check.md`): the real figure is 8 of the
  **41-item** corpus (a superseded, smaller snapshot before the
  Python 3.12/TensorFlow expansion to n=52), and of those 8, only 7 are
  from `numpy_1.ipynb` -- the 8th is from `torch_4.ipynb`. Also checked
  directly against the current n=52 report (`reports/real_state_eval_report.md`)
  and found `numpy_1.ipynb` alone now contributes 12 distinct ground-truth
  items at n=52, not 8 -- confirming the old figure cannot simply be
  restated at the new corpus size. Rewrote the sentence to state only what
  is verified (the `execution_order_risk` annotation fires on exactly 6
  cells in `numpy_1.ipynb`) and to explicitly flag the "8 of 41" figure as
  an unverified-at-n=52 estimate from an earlier corpus snapshot, rather
  than silently restating a wrong denominator or a wrong single-notebook
  attribution.
- **Found and fixed a real content gap**: the environment-dependent-branching
  hypothesis test -- an honestly-reported *inconclusive* result documented
  in `reports/environment_branching_check.md` and present in the standalone
  Markdown draft's \S5.6 -- was never carried into `main.tex`, even before
  this session's restructuring. Added a concise paragraph to the Construct
  Validity subsection reporting it accurately: 8/41 items matched an
  environment-branching regex with a striking raw correlation (88.2\% vs.\
  48.1\% wrong-answer rate), but all 8 share the identical signature already
  explained by the `execution_count`-sort confound, so the corpus cannot
  separate the two hypotheses -- reported as a genuine null/inconclusive
  result, not as a finding either way.
- **Spot-checked other frequently-repeated figures** (29/109, 26.6\%, the
  60/67 vs.\ 62/67 executable-notebook counts) against their source reports
  -- all consistent, no further discrepancies found in this pass.

Recompiled after each fix; final state builds clean at 12 pages, no
undefined references or citations.

**Files touched:** `paper/main.tex`, `paper/main.pdf` (recompiled).
