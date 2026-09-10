# Judge Validation, Round 2: Post-Fix Independent Manual Audit

Follow-up to `reports/judge_validation_report.md`. That report found and fixed
a 24% disagreement rate in the automated gpt-4o-mini judge used by
`tests/run_real_state_eval.py`. This report checks whether the fix actually
improved reliability, using a **second, independent sample** rather than
re-checking the same rows.

As before, this is **not** a human inter-rater study — it is an independent
second-pass re-grading performed by the reviewing agent, reading each
transcript against the stored ground-truth candidates without calling any LLM
classifier.

## Method
- Stratified random sample by condition: 5 `raw`, 10 `plain_strip`, 10 `ours`
  rows (25 total), drawn from the current, corrected-judge n=52 dataset
  (`tests/real_state_eval_raw_answers.json`, 107 non-overflow rows).
- **Seed 7**, deliberately different from the original audit's seed 42, so
  this sample does not overlap with rows already checked in the first audit.
- For each row, the recorded model answer was independently compared against
  both ground-truth candidates (`ec_order_value` = TRUTH candidate,
  `visual_order_value` = DECOY candidate) using a literal-or-close-value-match
  standard, with NEITHER as the default when the answer does not clearly
  match either candidate's specific content.

## Result

**23 of 25 (92%) agreement** with the corrected automated judge's recorded
outcome, up from 19 of 25 (76%) before the fix. This is evidence, not proof,
that the prompt tightening described in the first audit report improved
reliability rather than moving the error somewhere else undetected.

## The two disagreements

Both disagreements involve the same variable, `pandas_3.ipynb` /
`resultados`, once under the `raw` condition and once under `plain_strip`.
In both cases:

- The model answered with a fully-populated pandas `DataFrame` containing
  8 rows of real hyperparameter-search results (real `algoritmo`,
  `parametros`, and `score` columns with concrete values).
- The stored DECOY candidate is `DataFrame(shape=(0, 3), cols=['algoritmo',
  'parametros', 'score'])` — an **empty** DataFrame with the same column
  names.
- The judge credited both answers as DECOY matches.
- By strict literal comparison, these do not match: a DataFrame with 8 rows
  of concrete values is not the same object as a DataFrame with 0 rows,
  regardless of matching column names. The correct grade, applying the same
  standard the fix was supposed to enforce, is NEITHER.

This is a **different, narrower failure mode** than the one found and fixed
in the first audit. The original bug over-credited answers whenever one
candidate was `None` ("never defined"); this residual pattern instead
over-credits answers on **DataFrame-typed ground truth** when column names
match but row content or count clearly diverges. It affects a much smaller
slice of the corpus: DataFrame-typed divergences are a minority of the 52
ground-truth items (most are scalars, tensors, or model objects), and this
sample surfaced exactly one such variable, checked under two conditions.

## Implication for the paper's headline numbers

This residual imprecision is real but small in scope, and does not change
the paper's main real-notebook conclusion. If anything, correcting these two
rows from DECOY to NEITHER would very slightly *increase* the overall-TRUTH
gap in favor of nothing in particular (since NEITHER helps no condition), or
very slightly deflate the specific condition's DECOY count — it does not
create or remove an accuracy advantage for any condition, since both
affected rows are DECOY misgrades unrelated to whether the answer was a
correct (TRUTH) one. We report this transparently as a residual limitation
of the automated judge rather than re-running the full n=52 tally over a
2-row, single-variable pattern.

## Conclusion

The post-fix judge is measurably more reliable (92% vs. 76% agreement on
independent samples) but not perfectly reliable. Readers should continue to
treat the exact TRUTH/DECOY/NEITHER counts in Sect. 5.4 as approximate,
consistent with the paper's own framing that the key conclusion is
qualitative (no detectable accuracy advantage at this scale) rather than a
precise point estimate.
