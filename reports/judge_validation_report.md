# Judge Validation: Independent Manual Audit of the gpt-4o-mini Grader

Motivated by the internal review's recommendation to validate the automated
three-way judge (TRUTH/DECOY/NEITHER) used in `tests/run_real_state_eval.py`.
This is **not** a human inter-rater study (no human annotator was used) — it
is an independent second-pass re-grading performed by the reviewing agent,
reading each transcript against the stored ground-truth candidates without
calling any LLM classifier. It catches judge *bugs*, not subtler disagreement
patterns a trained human annotator might also miss.

## Method
- Stratified random sample: 25 of 123 answer rows (41 items × 3 conditions,
  minus 25 OVERFLOW rows excluded from judging), seed=42.
- For each row, independently compared the recorded model answer against
  both ground-truth candidates (`ec_order_value` = TRUTH candidate,
  `visual_order_value` = DECOY candidate) from `tests/real_state_groundtruth.json`
  and assigned TRUTH / DECOY / NEITHER using a literal-match standard.

## Result
- **19/25 (76%) agreement** with the recorded automated-judge outcome.
- **6/25 (24%) disagreement**, all in one direction: the automated judge
  assigned TRUTH or DECOY to answers that, on literal comparison, matched
  **neither** stored candidate and should have been NEITHER.

## The bug, isolated
All 6 disagreements share a structure: one ground-truth candidate is `None`
(rendered to the judge as the sentence *"the variable was NEVER successfully
defined..."*), and the model's answer is some other concrete, plausible-looking
value that matches neither candidate's actual content. The judge appears to
treat "the answer is not literally the *other* (defined) candidate's value" as
sufficient evidence to credit the *first* candidate, without checking whether
the answer's specific content agrees with that candidate at all.

Confirmed, reproducible example (`numpy_1.ipynb`, variable `device`; truth
candidate = NEVER-DEFINED, decoy candidate = `cpu`):

| Condition | Answer | Automated judge | Correct (literal-match) |
| :--- | :--- | :--- | :--- |
| `plain_strip` | `torch.device(type='cuda')` | **DECOY** | NEITHER (`cuda` ≠ `cpu`) |
| `ours` | `cuda` | **TRUTH** | NEITHER (`cuda` ≠ "never defined") |

The identical underlying answer content (`cuda`) was graded in *opposite*
directions for two conditions — direct evidence the judge is not reliably
comparing content, only reacting to "did the model produce a concrete answer."

Other confirmed instances: `pandas_3/j` (answer `8`, candidates
NEVER-DEFINED/`1`, graded TRUTH); `numpy_1/num_epochs` (answer `30`,
candidates NEVER-DEFINED/`50`, graded TRUTH); `NBspecific_15/fig` (answer a
different-sized Figure, candidates a specific-sized Figure/NEVER-DEFINED,
graded DECOY); `torch_4/device` (answer `cuda`, candidates NEVER-DEFINED/`cpu`,
graded TRUTH).

## Why this matters for §5.4
36 of 41 real ground-truth items (88%) are `phantom_in_visual` /
`missing_in_visual` "existence divergences" — exactly the shape where one
candidate is `None` and this bug applies. This is not a marginal edge case;
it is the dominant item type in the newly expanded (n=41) ground-truth set.
The bug inflates both TRUTH and DECOY counts (at NEITHER's expense) roughly
symmetrically across conditions in this sample, so it is not obviously a
one-sided confound for `raw` vs. `ours` — but it substantially reduces
confidence in the exact tallies reported before this fix, on top of the
already-reported non-significance between conditions.

## Fix applied
`tests/run_real_state_eval.py`'s judge prompt was tightened to require a
literal/close value match to a candidate before crediting it, with an
explicit instruction that "not matching the other candidate" is not
sufficient evidence, and to default to NEITHER when uncertain. Full,
untruncated model answers are now also persisted to
`tests/real_state_eval_raw_answers.json` for future audits (previously only
a 160-character truncated snippet was saved in the markdown report). The full
evaluation (`tests/run_real_state_eval.py`) was re-run with the fixed judge;
see `reports/real_state_eval_report.md` for the corrected numbers.
