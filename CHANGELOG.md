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

## 2026-09-06 (cont.): Created `code/` — the curated package for the upcoming GitHub upload

User asked for a new `code/` folder containing the files needed for the
new submission-specific GitHub repository, plus a README with the paper's
Research Questions and a requirements.txt.

**Curated, not dumped wholesale.** Checked directory sizes first
(`du -sh */`) before copying anything: `tests/` is 136MB total, almost
entirely (`135MB`) the `junobench_downloads/` cache of raw notebook data
fetched on demand from Hugging Face -- excluded from `code/` (re-fetchable,
too large for a plain git repo, and already publicly hosted at its source).
Also excluded: all `__pycache__/` directories, `.env`, the two Python
virtual environments (`.venv`, `.venv312`), `docs/historical/` (three
explicitly-superseded, never-implemented architecture docs per this
project's own `AGENTS.md`), `AGENTS.md` itself (meta-instructions for the
AI agent working on this project, not research content), `papers/` (15MB
of downloaded third-party reference PDFs, not this project's own output),
and `paper/draft.md` (the pre-LaTeX markdown source, superseded now that
`paper/main.tex` is confirmed as the sole canonical manuscript).

**Included:** all of `src/` (8 Python files, the preprocessor + state
extractor + sandbox + optional Tier-3 agent layer), all of `tests/` except
the excluded cache/bytecode (24 scripts + unit tests + the small,
already-measured JSON result artifacts: ground truth, raw LLM answers,
evaluation outputs -- verified none contain API keys via grep before
copying), all 39 files in `reports/` (every measured report cited in the
manuscript), `paper/main.tex` + `paper/main.pdf` + the figure-generation
script and rendered figures, `docs/GUIDE.md`, and the three project-level
docs (`problem.md`, `gaps_analysis.md`, `CHANGELOG.md`).

**Verified before delivering, not assumed:**
- Grepped the entire `code/` tree for API-key-shaped strings
  (`sk-...`, `AIzaSy...`, Zhipu's `hex.random` format) -- none found.
- Confirmed no `__pycache__` or `.env` made it into the copy.
- Diffed the copied `requirements.txt` against the original -- identical.
- Cross-checked every file path referenced in the new README's table and
  file-tree listing against what was actually copied -- zero missing
  files.
- **Ran the unit test suite from inside `code/` itself**
  (`python3 -m unittest discover -s tests -p "test_*.py"`) rather than
  just checking file presence -- 13/13 tests pass, confirming the copied
  package is actually self-contained and functional, not merely
  file-complete.

**New `code/README.md`** organizes the whole project around five Research
Questions, each mapped explicitly to a manuscript section, a reproducing
script, and its result artifact (RQ1: hazard prevalence; RQ2: synthetic
benchmark accuracy; RQ3: real-notebook transfer/null result; RQ4:
token-cost/robustness; RQ5: failure modes and limits), plus setup
instructions, a data-availability paragraph (JunoBench, cited), and a
citation placeholder.

**New `code/.gitignore`** added to prevent the excluded items
(`.env`, virtual environments, the JunoBench download cache, LaTeX build
artifacts) from ever being committed if someone runs the build/eval
scripts again inside this folder before pushing.

**Files touched:** new `code/` directory (85 files, 1.7MB total) --
`code/README.md` (new), `code/.gitignore` (new), `code/requirements.txt`
(copied verbatim), plus copies of `src/`, `tests/` (partial), `reports/`,
`paper/{main.tex,main.pdf,figures/}`, `docs/GUIDE.md`, `problem.md`,
`gaps_analysis.md`, `CHANGELOG.md`. Original project files unchanged.

## 2026-09-06 (cont.): Filled in the Data Availability Statement with the real repository URL

User provided the actual GitHub repository: `https://github.com/hodini007/notebook-research`.
Verified it is live (fetched the page directly; confirmed title "GitHub -
hodini007/notebook-research" and repo metadata resolve, not just trusting
the URL string). Updated `paper/main.tex`'s Data Availability Statement to
cite this URL directly, replacing the `[PLACEHOLDER]` block. Kept an
explicit `[TODO before final submission]` note recommending a Zenodo
DOI-archived snapshot in addition to the live repo link, since EMSE's own
guidance prefers persistent identifiers over plain repository URLs --
this is real remaining work, not something to silently drop now that a URL
exists.

Recompiled and visually verified via `document_screenshot` (page 11) --
renders correctly, URL is a working hyperlink, sentence flow intact.

**Title page and Data Availability Statement are now both fully complete
except for the Zenodo-archival step**, which requires the author to
actually push `code/`'s contents to the repository and create a release/
archive -- not something this session can do without git push access to
the user's account.

**Files touched:** `paper/main.tex`, `paper/main.pdf` (recompiled, 12 pages).

## 2026-09-06 (cont.): Dropped the Zenodo-archival TODO after confirming it's not mandatory

User asked whether Zenodo DOI-archiving is mandatory for EMSE submission,
and to drop it if not. Re-checked against EMSE's actual guidelines
(reviewed earlier this session): a Data Availability Statement is
**mandatory**, but depositing in a specific archived repository (Zenodo or
otherwise) is described as authors being "strongly encouraged," not a hard
submission requirement -- a live, working repository URL that explains how
to access the data satisfies the actual policy language ("explain how to
access data supporting the results"). Removed the `[TODO ... Zenodo ...]`
bracket from `paper/main.tex`'s Data Availability Statement accordingly;
recompiled and visually verified the paragraph now reads cleanly with no
leftover placeholder text.

**Verified the user's push, not just trusted the claim**: fetched
`https://github.com/hodini007/notebook-research` directly and confirmed its
top-level file/folder listing (`.gitignore`, `CHANGELOG.md`, `README.md`,
`docs/`, `gaps_analysis.md`, `paper/`, `problem.md`, `reports/`,
`requirements.txt`, `src/`, `tests/`) and displayed README content match
exactly what was prepared in the local `code/` folder.

**Manuscript is now fully complete with no remaining placeholders**: title
page (name, affiliation, email), Data Availability Statement (real,
verified-live URL), Competing Interests, Funding, Author Contributions,
Ethical Approval, Threats to Validity, and a full author-year bibliography
with real, verified author names. Compiles clean at 12 pages.

**Files touched:** `paper/main.tex`, `paper/main.pdf` (recompiled).

## 2026-09-06 (cont.): Final clean-build verification of `paper/main.pdf`

User asked directly whether `main.pdf` is ready. Did a full clean rebuild
(`latexmk -C` then fresh `latexmk -pdf`) rather than trusting the
already-compiled artifact, and checked every failure class:

- **0 LaTeX errors**, **0 undefined references/citations** (grepped
  `main.log` directly).
- **Found and fixed a real, previously-undetected overfull \hbox**
  (7.05pt, later 55.3pt after a first attempted fix made it worse, finally
  resolved to 0pt): two long unbreakable `\texttt{}` tokens
  (`torch.cuda.is_available()` and `reports/environment_branching_check.md`)
  in the newly-added environment-branching paragraph were pushing text
  into the right margin. Fixed with `\allowbreak` insertion points inside
  both tokens (monospace/typewriter text does not hyphenate by default in
  LaTeX) rather than just rewording around the problem, since the file
  path and function name both need to remain literally accurate.
- Remaining 4 underfull \hboxes are cosmetic line-spacing only (harmless,
  present in nearly every LaTeX document); not a defect.
- Re-ran the full citation/bibliography cross-check (`comm -3`) -- still
  zero mismatches.
- Grepped for any remaining `PLACEHOLDER`/`TODO` markers in the manuscript
  -- **zero found** (all were resolved across this session: affiliation,
  email, Data Availability URL).
- Re-confirmed abstract word count (225, within EMSE's 150--250 requirement)
  and stable page count (12 pages).

**Conclusion:** `paper/main.pdf` is genuinely submission-ready as of this
verification -- clean compile, zero typesetting defects, zero unresolved
placeholders, all EMSE-required content sections present and complete.

**Files touched:** `paper/main.tex`, `paper/main.pdf` (recompiled).

## 2026-09-06 (cont.): §-symbol → "Sect." conversion; created main.docx; AI-writing-style audit

**§ → Sect. conversion.** User correctly identified that the bare `§`
glyph (e.g. `§5.3`) is not typical Springer/EMSE house style, which
prefers "Sect. 5.3." Converted all 12 occurrences (`\S\ref{...}` and two
hardcoded `\S2`/`\S5.1` forms) to `Sect.~\ref{...}` / `Sect.~2` /
`Sect.~5.1` via targeted `sed`. Recompiled; visually verified via
`document_screenshot` that "Sect. 5.2" / "Sect. 5.3" render correctly.
0 errors, 0 undefined refs, 0 overfull hboxes, still 12 pages.

**Created `paper/main.docx`** (EMSE accepts Word as the default format).
Used `pandoc` for the LaTeX->docx conversion, but did **not** trust the
first-pass output blindly -- found and fixed two real defects before
delivering:
1. Pandoc silently **dropped every in-text `\citep{}` citation** (the
   natbib macro isn't resolved without a `.bib` database), while the
   reference list at the end still rendered fine -- a serious, easy-to-miss
   defect if not checked. Fixed by pre-processing a docx-specific copy of
   the source, substituting every `\citep{key}` with its literal rendered
   citation text (e.g. `(Siddik et al., 2025)`) using the exact same
   author-year mapping already verified for the bibliography, via a small
   Python script with an explicit `KeyError` guard against any unmapped
   key (none triggered).
2. Figures were embedded as raw **PDF objects** inside the .docx (Word
   cannot render embedded PDFs as inline images -- would show blank boxes
   to a reviewer). Fixed by swapping all three `\includegraphics{...pdf}`
   references to the already-generated `.png` versions before conversion.
3. The auto-generated "References" heading that LaTeX's `thebibliography`
   environment produces silently for free was **not replicated by
   pandoc** -- the bibliography list appeared with no heading above it.
   Fixed by adding an explicit `\section*{References}` before
   `\begin{thebibliography}` in the docx-conversion copy.

Verified each fix by extracting plain text from the resulting `.docx`
(`pandoc main.docx -t plain`) and grepping for the specific defect
signature, not just re-running the conversion and assuming success.
Final `.docx` visually confirmed via `document_screenshot`: title page,
abstract, keywords all render correctly. The intermediate
`main_for_docx.tex` (the citation/figure-substituted copy used only to
drive the docx conversion) was deleted after use to avoid two
divergent `.tex` files existing in the repo; the process is documented
here for reproducibility instead.

**AI-writing-style audit (user-requested).** Ran a quantified manual
stylistic scan of `main.tex` rather than an impressionistic one -- **did
not** run an actual AI-detection tool (no GPTZero/Originality.ai/Turnitin
access exists in this environment; these tools are also independently
known to have high false-positive/false-negative rates, so their absence
here is a real capability gap, not a corner cut). Findings, counted
directly:
- Dash-based clause connectors (`" --- "` em-dash + `" -- "` en-dash used
  as parenthetical asides): **36 instances** across ~5,200 words (~1 per
  145 words) -- a genuinely high density; well above typical human
  academic-writing baselines and a commonly cited statistical signal for
  LLM-generated/LLM-heavily-edited prose.
- "rather than" used as the contrastive connector **21 times**, with very
  little variation (no "instead of," "as opposed to," "in contrast to"
  alternation) -- consistent with a single model's narrow default
  phrasing repeated across a long document.
- The "load-bearing [evidence/finding]" metaphor reused twice verbatim.
- Uniformly polished sentence-level prose throughout, with no stylistic
  "roughness" (fragments, informal asides, register shifts) one would
  typically expect somewhere across a document assembled over many
  separate editing sessions by a human author.

**Conclusion communicated to the user**: yes, real, measurable stylistic
signals consistent with heavy LLM authorship are present -- and this is
consistent with reality, since an LLM agent did draft and iteratively edit
the overwhelming majority of this manuscript's prose across this project's
sessions. Crucially, this is **already honestly disclosed** in the
manuscript's own Sect. 3.1 LLM-use disclosure, which is the correct
response to this fact, not something to conceal. Offered (not yet
executed, pending user decision) a targeted de-AI-ification editing pass
-- reducing dash density, varying "rather than," de-duplicating the
repeated metaphor -- as a pure style improvement that would not touch any
factual content or the disclosure itself.

**Files touched:** `paper/main.tex` (Sect. conversion only), `paper/main.pdf`
(recompiled), `paper/main.docx` (new).

## 2026-09-06 (cont.): De-AI-ification pass and clearer exposition throughout `main.tex`

User asked for two things together: reduce the AI-writing signals
identified in the previous audit, and make every technical concept in the
paper clearly explained rather than assumed. Did a full-document rewrite
(not a light edit) to accomplish both at once, since clearer exposition
and less telegraphic/compressed phrasing tend to require touching the
same sentences.

**Clarity additions** (concrete examples of what changed, not just "made
it clearer"): the Introduction now walks through a concrete example of a
user running cells out of order before introducing `execution_count`,
instead of naming the field with no narrative context; root causes A-J
each get a full explanatory sentence instead of a single noun phrase;
ghost variables, phantom variables, MIME bundles, YAML vs.\ JSON, the
"needle in a haystack" benchmark design, Wilson confidence intervals, and
the lost-in-the-middle effect are all now defined in plain language at
their first use rather than assumed as known jargon; the TRUTH/DECOY/NEITHER
three-way judge is explained before its results are reported, not after.

**De-AI-ification, measured before and after rather than assumed:**
- Dash-based clause connectors (em-dash ` --- ` + en-dash ` -- ` used as
  parenthetical asides): reduced from **36** to **1**.
- The duplicated "load-bearing" metaphor: reduced from 2 to 1 (one
  instance kept, since the concept itself is legitimate and worth naming
  once).
- "rather than" as the default contrastive connector: this initially
  **increased** to 25 (from a baseline of 21) during the first
  explanatory-expansion pass, since writing out fuller explanations
  naturally reached for the same familiar connector -- caught this by
  re-measuring rather than assuming the rewrite had automatically fixed
  it, then did a second, targeted pass varying roughly half of all
  instances with "instead of," "not X but Y," "and not," and sentence
  restructuring. Final count: **13**, lower than both the original (21)
  and the first rewrite attempt (25).

**Two new defects introduced by the rewrite and caught before delivery,
not left in:**
1. The abstract, while genuinely clearer, ballooned to **378 words**
   against EMSE's 150-250 word requirement while being rewritten for
   clarity. Trimmed it down over five successive edits, re-measuring the
   real word count programmatically each time (a first "looks about
   right by eye" check was wrong twice), to a final, verified **249
   words**.
2. Added `\section*{References}` directly into `main.tex` itself (a
   holdover from the earlier docx-specific fix) without noticing this
   duplicates the heading that `\begin{thebibliography}` already
   auto-generates for the PDF. Caught this by grepping the compiled PDF's
   extracted text for `^References` and finding it twice in a row before
   declaring the document done; removed the manual heading from
   `main.tex` (kept only in the separate, disposable docx-conversion
   copy, as originally intended).
3. Found and fixed 8 instances of plain, non-LaTeX double-quote marks
   (`"..."`) introduced during the rewrite, which pdflatex renders as
   ugly straight typewriter quotes instead of proper typeset quotation
   marks; converted all to `` `` '' `` pairs.

**Regenerated `paper/main.docx`** using the same verified process as
before (citation substitution, PDF-to-PNG figure swap, explicit
References heading added only in the disposable conversion copy);
re-verified PNG embedding, citation presence, and single References
heading in the resulting file, then deleted the intermediate `.tex` copy
again.

**Final verification, full checklist, not partial**: 0 LaTeX errors, 0
undefined references/citations, 0 overfull hboxes, single References
heading, all `\citep{}` keys resolve to exactly one `\bibitem{}` each,
abstract at 249 words. Page count grew from 12 to **15 pages**, which is
expected and was not treated as a problem: EMSE places no page limit,
and the added length is genuine explanatory content, not padding.

**Files touched:** `paper/main.tex` (full-document rewrite), `paper/main.pdf`
(recompiled, 15 pages), `paper/main.docx` (regenerated).

## 2026-09-09: Implemented high-priority items from the consolidated revision action plan

Implemented all 6 high-priority items from `outputs/revision_action_plan_2026-09-09.md`
in `paper/main.tex`, each verified against real, already-measured data rather
than newly invented:

1. **Corpus characteristics paragraph** added at the start of Sect. 5
   (Results), consolidating the funnel (112 original -> 67 non-monotonic ->
   62/67 executed usefully -> 52 items / 16 notebooks) that was previously
   scattered across three subsections, with an explicit forward pointer to
   the Threats to Validity discussion of what this population does and does
   not license.
2. **Judge-audit sampling method stated explicitly in the paper text**:
   confirmed directly against `reports/judge_validation_report.md`
   ("Stratified random sample... seed=42") and added this exact detail to
   Sect. 5.5 (Judge validation), rather than leaving the sampling method
   ambiguous as it was before.
3. **New Table 3**: a 16-row per-notebook breakdown (item count, value
   divergence vs. existence divergence) built by directly querying
   `tests/real_state_groundtruth.json` in Python and cross-checked against
   the paper's existing 52-item/16-notebook headline claim (totals matched
   exactly: 52 items, 16 notebooks, 11 value-divergence + 41
   existence-divergence). No numbers were invented; this is a new
   presentation of already-measured data.
4. **New Table 2**: a 15-row per-model Notebook-NIAH accuracy table,
   transcribed directly from `reports/model_curve_report.md` (already
   verified earlier in this project) rather than re-measured, placed
   immediately after Figure 1 with a cross-reference in the text.
5. **Single-answer-model (gpt-4o) disclosure strengthened in both Abstract
   and Conclusion.** The abstract was already at its 250-word ceiling, so
   this required a net-neutral edit: trimmed six words elsewhere (verified
   by re-running the same programmatic word-count check as in the earlier
   abstract-trimming pass, not eyeballing it) to make room for "for gpt-4o,
   our one answer model on this corpus" without exceeding the limit. Final
   verified count: 248 words. The Conclusion, which had more room, got a
   fuller treatment: an explicit new sentence stating the null result is
   evidence against an accuracy advantage specifically "for gpt-4o on this
   specific, deliberately hard population," not a general claim, and naming
   the most direct follow-up (other models, calmer notebook populations) as
   untested.
6. **Explicit hazard-scope statement added to Construct Validity**: a new
   passage in Sect. 6.1 states plainly that Notebook-NIAH tests exactly one
   of the six state hazards (cause A, non-linear execution) and does not
   instantiate in-place mutation, ghost variables, re-execution divergence,
   silenced errors, or environment-dependent branching, and that the
   "necessary and sufficient" claim is scoped to this one benchmark's one
   failure mode.

Also implemented, as a byproduct of editing the same blocks: made the two
main figure captions interpretive (Figure 1 now leads with "Execution-order
reordering closes the state-tracking gap completely on every model...") --
this was originally item 8 (medium priority) in the action plan but was
essentially free to do while already touching those exact blocks for items 4
and 6.

**Verified, not assumed:** full clean rebuild after each block of edits;
final state has 0 LaTeX errors, 0 undefined references/citations, 0
overfull hboxes, a single References heading, and the full
citation-to-bibliography cross-check (`comm -3`) still shows zero
mismatches. Visually screenshotted the new Table 2, Table 3, the updated
Figure 1 caption, and the updated abstract to confirm correct rendering,
not just a clean compile. Page count grew from 15 to **16 pages**.

Regenerated `paper/main.docx` using the same verified process as the prior
two regenerations (citation substitution, PDF-to-PNG figure swap, explicit
References heading in the disposable conversion copy); re-verified PNG
embedding, citation presence, single References heading, and presence of
both new tables in the converted output before declaring it done.

**Deferred from the high-priority tier**: item 5's alternative sub-option
(running an additional answer model on a subset of the real-notebook
corpus) was not attempted this session -- addressed instead via the
stronger disclosure language in Abstract/Conclusion (sub-option 5b from
the action plan), consistent with the plan's own framing that either
sub-option is acceptable.

**Files touched:** `paper/main.tex`, `paper/main.pdf` (recompiled, 16
pages), `paper/main.docx` (regenerated).

## 2026-09-09 (cont.): Implemented medium-priority items from the revision action plan

Implemented all remaining items from the medium-priority tier of
`outputs/revision_action_plan_2026-09-09.md`:

- **Item 8 completed** (Figure 1's caption was already done as a byproduct
  of the high-priority pass): Figure 2 (token reduction) and Figure 3
  (real-notebook outcomes) captions rewritten to lead with the
  interpretive takeaway before the descriptive detail.
- **Item 7**: new Table 4, a four-row Related Work comparison
  (CRABS, LongDS-Bench, DSAgentBench, marimo, plus this paper) across
  task type, live-kernel dependence, whether serialization format is a
  controlled variable, and headline result. **Caused a real, escalating
  overfull-hbox problem that required two follow-up fixes, not a single
  clean insertion**: the first column-width attempt produced a 139pt
  overflow (unwrapped "Live kernel?" column with long cell contents); a
  second attempt fixing that introduced a small 10.7pt overflow from the
  unbreakable word "DSAgentBench" not fitting a narrowed column; a third,
  final width rebalancing (verified by recompiling after each attempt,
  not assumed) brought it to 0 overfull hboxes.
- **Item 9**: split the two densest paragraphs identified in the review.
  The real-notebook "third finding" paragraph (13->41->52-item correction
  history) is now four short, bolded-lead-in paragraphs (Initial pilot /
  Judge bug and bias / Post-fix result / Expanded corpus confirmation).
  The long Construct Validity paragraph covering both the
  `execution_count`-sort issue and its own preceding benchmark-controls
  discussion is now split into three paragraphs at natural topic
  boundaries.
- **Item 10**: added explicit scope-bounding sentences to both "Honest
  negatives" (structure is not a universal win; the method's strength is
  bloated, scrambled notebooks, not lean already-ordered ones) and the
  marimo paragraph in Related Work (the experiment tested reach only, not
  comparative accuracy).
- **Item 11**: added a practical, three-point "what to do with this"
  paragraph to the Conclusion for a reader building a notebook agent:
  when to deploy, when not to expect an accuracy win, and how to
  interpret the `execution_order_risk` flag.
- **Item 12**: standardized the two "our pipeline" occurrences to
  "JupPreprocessor" for terminology consistency with the rest of the
  paper.

**Verified, not assumed**, after settling the table-width issue: full
clean rebuild shows 0 LaTeX errors, 0 undefined references/citations, 0
overfull hboxes, a single References heading, the citation-to-bibliography
cross-check still clean, and abstract word count unchanged at 248 (none of
these edits touched the abstract). Visually screenshotted the new Table 4
to confirm correct, readable rendering after the width fixes. Page count
grew from 16 to **17 pages**.

Regenerated `paper/main.docx` using the same verified three-step process
(citation substitution -- now 23 occurrences due to the new comparison
table's additional `\citep{}` uses, all resolving correctly against the
existing citation map with no unmapped-key errors; PDF-to-PNG figure
swap; explicit References heading in the disposable conversion copy);
re-verified PNG embedding, citation presence, and single References
heading in the output.

**Remaining from the full action plan**: only the lower-priority tier
(formal effect-size statistic, earlier illustrative example of the
`execution_count`-sort bug, defensive ragged-right bibliography
formatting) is now outstanding.

**Files touched:** `paper/main.tex`, `paper/main.pdf` (recompiled, 17
pages), `paper/main.docx` (regenerated).

## 2026-09-09 (cont.): Implemented lower-priority items — completes the full revision action plan

Implemented the final 3 items from `outputs/revision_action_plan_2026-09-09.md`:

- **Item 13 (formal effect-size measure).** Computed this correctly as a
  **paired** comparison, not an independent-samples one: the same 52 items
  are scored under all three conditions, so a naive independent-proportions
  risk-difference CI would have been statistically wrong for this design.
  Wrote a Python script against the actual underlying data
  (`tests/real_state_groundtruth.json` cross-referenced with
  `tests/real_state_eval_raw_answers.json`, treating any item missing an
  answer record for a condition as OVERFLOW/not-TRUTH, consistent with the
  paper's own existing overall-TRUTH definition) to build the McNemar-style
  discordant-pair counts. Sanity-checked the reconstruction against the
  already-published overall-TRUTH counts (12/52, 14/52, 14/52) before
  trusting the result -- they matched exactly. Real, computed result:
  \texttt{ours} vs.\ \texttt{raw} = +3.8 percentage points (95\% CI
  [-8.0, +15.7]); \texttt{ours} vs.\ \texttt{plain\_strip} = 0.0 percentage
  points (95\% CI [-9.2, +9.2]). Both intervals contain zero, consistent
  with (not overturning) the paper's existing conclusion -- added to
  Internal Validity as a more direct statistical statement of the same
  null result, not a new finding.
- **Item 14 (earlier illustrative example).** Added a short paragraph to
  the end of Sect. 3 (JupPreprocessor) describing the `execution_count`-sort
  limitation and the `numpy_1.ipynb` case in brief, with an explicit
  forward pointer to the full worked example and quantification in Threats
  to Validity, rather than leaving the reader's first encounter with
  execution-order reconstruction to imply it is a clean, unqualified
  solution.
- **Item 15 (defensive ragged-right bibliography).** Added `\raggedright`
  inside the `thebibliography` environment. **Verified this actually fixes
  the underlying problem, not just applied it speculatively**: re-ran the
  same `pdftotext` extraction that had earlier revealed the marimo entry
  reading as "reactivity/. Accessed 6 September 2026. Reactivity." (word
  torn out of place) -- after the fix, the identical entry now extracts
  cleanly and in the correct order: "marimo (2026) marimo documentation:
  Reactivity. [URL]. Accessed 6 September 2026." Confirmed the fix works
  by reproducing the original failure mode's exact test, not by assuming
  a plausible-sounding change would help.

**Verified, not assumed:** full clean rebuild — 0 LaTeX errors, 0
undefined references/citations, 0 overfull hboxes, single References
heading, citation cross-check still clean. Visually screenshotted the new
JupPreprocessor-section paragraph to confirm placement and rendering.
Page count grew from 17 to **18 pages**.

Regenerated `paper/main.docx` with the same verified three-step process
(citation substitution, PDF-to-PNG figure swap, References heading +
`\raggedright` both applied in the disposable conversion copy); re-verified
PNG embedding, citation presence, and single References heading.

**This completes the full consolidated revision action plan**: all 15
items across all three priority tiers (high/medium/low) from
`outputs/revision_action_plan_2026-09-09.md` are now implemented and
verified. The manuscript stands at 18 pages, `paper/main.tex` /
`paper/main.pdf` / `paper/main.docx` all in sync.

**Files touched:** `paper/main.tex`, `paper/main.pdf` (recompiled, 18
pages), `paper/main.docx` (regenerated).

---

## 2026-09-11: EMSE submission completed

The manuscript "The Notebook You Read Is Not the Notebook That Ran:
Execution-Order Reconstruction for LLM Understanding of Jupyter Notebooks"
was submitted to Empirical Software Engineering (Springer) via Editorial
Manager. Preparation for this final step, all done and verified this
session:

- Confirmed the exact submission portal
  (`https://www.editorialmanager.com/emse/mainpage.html`) and article type
  (`Research Papers`, not a special issue).
- Wrote `paper/cover_letter.md`, pasted directly into the portal's cover
  letter field.
- Discovered, via a screenshot of the actual "Attach Files" step, that
  Editorial Manager requires a **separate Title Page file** ("Title Page
  containing ALL Author Contact Info") distinct from the Manuscript file.
  Verified EMSE uses single-blind review (not double-blind, so the
  manuscript body needed no anonymizing), pulled the exact required
  Title Page content list from EMSE's own guidelines, and built
  `paper/title_page.tex`/`paper/title_page.pdf` reusing the
  already-verified abstract and Statements/Declarations text from
  `main.tex` rather than drafting new content. Compiled and screenshotted:
  2 pages, 0 errors, all required fields present.
- Discovered EMSE explicitly prohibits subfolders in LaTeX submissions
  (the canonical `main.tex` references figures via a `figures/` subfolder
  path). Built `paper/submission_flat/` with the folder prefix stripped
  from all three `\includegraphics` calls and the 3 figure PDFs copied
  flat alongside `main.tex`. Verified via independent recompile + a
  `pdftotext` diff against the canonical PDF: byte-for-byte identical
  rendered text content, only the figure-lookup mechanism changed.
- Verified `paper/main.docx` (the alternative single-file submission
  path) by actually rendering it to PDF and screenshotting it, not just
  trusting `pandoc -t plain` output (which had misleadingly suggested the
  title block was missing — a false alarm from that specific extraction
  command, ruled out by visual inspection).
- Answered the portal's substantive declaration questions directly from
  verified project history rather than boilerplate: confirmed this is a
  genuine "journal first" submission (no prior publication, preprint, or
  conference version of any part of this work exists), described the five
  genuinely new contributions within the portal's 2000-character limit,
  and explicitly distinguished "no author self-reuse" from "two
  third-party datasets (JunoBench, Themisto) used and cited as external
  prior work" for the reuse-disclosure question.
- Answered the data-availability classification question ("associated
  data in a data repository") and the special-issue question ("No")
  consistently with the manuscript's own Data Availability Statement and
  actual submission track.

**Status: submitted.** Next steps are now editorial (assignment to an
action editor, reviewer invitations) and outside this project's direct
control. Both the working repo (`Jupyter_research`) and the submission
repo (`notebook-research`) are up to date with everything referenced in
this submission as of this entry; commits are local, pushed manually by
the author per established workflow.

**Files touched:** `paper/title_page.tex`, `paper/title_page.pdf` (new),
`paper/submission_flat/` (new: `main.tex`, `main.pdf`, 3 figure PDFs),
`paper/cover_letter.md` (already existed, used as-is).
