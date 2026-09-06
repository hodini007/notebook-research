# Themisto Failure-Mode Breakdown: Measured, Not Inferred

Follow-up to `reports/themisto_report.md`, which explained the honest negative
result there (`ours` 26.7% vs raw 40.0% on Themisto output-prediction) with an
**inferred, never-measured** mechanism: *"Because static analysis does not
execute code, it only registers the variable's existence and type, not its
runtime value. When the cell defining the value is truncated out,
JupPreprocessor cannot provide the value to the model."*

This report re-runs the same 15-item Themisto eval (`tests/run_themisto_eval.py`,
same `seed=42`, same items — reproduced the original 40.0%/26.7% aggregate
result exactly) with full prompts and answers persisted
(`tests/themisto_results.json`, now including `raw_prompt`,
`preprocessed_prompt`, `raw_answer`, `preprocessed_answer`), and directly
inspects why each preprocessed-wrong item failed. **The original explanation
turns out to be wrong for the items that actually decide the result.**

## Step 1: most of the "preprocessed-wrong" items don't discriminate anything

11 of 15 items are wrong under `preprocessed`. But cross-tabulating against
`raw_correct`:

| | preprocessed correct | preprocessed wrong |
|---|---:|---:|
| **raw correct** | 4 | **2** |
| **raw wrong** | 0 | 9 |

**9 of the 11 "preprocessed-wrong" items are also wrong under raw** — i.e.,
neither format contains enough information to answer correctly, regardless
of preprocessing. Concrete example (`dadf2497`, a `pd.read_pickle(...).shape`
task): the expected shapes `(5833, 32)`, `(1927, 32)`, `(1918, 21)` come from
pickle files never shown in either prompt's history; raw guessed
`(1000, 10)/(200, 10)/(300, 10)`, preprocessed guessed
`(1000, 20)/(200, 20)/(300, 20)` — both wrong, both guessing, for a question
neither format could possibly answer. Including these 9 items in an
"information loss" narrative is not supported; they are fundamentally
unanswerable-by-any-static-format items in a benchmark built from real,
disjoint session excerpts.

**Only 2 of 15 items decide the entire measured accuracy gap** (raw 6/15 =
40.0%, preprocessed 4/15 = 26.7%; the gap is exactly these 2 items — 2/15 =
13.3 percentage points, matching 40.0% − 26.7%). Any explanation of "why
preprocessing hurts on Themisto" should be about these 2 items specifically,
not the aggregate.

## Step 2: in both decisive items, the correct value is present in the preprocessed prompt too — it is not information loss

Direct inspection of both decisive items (kernel `29da7c56`):

**Item A** — `parsed = list(map(parse, lines)); len(parsed)`, expected `87572`.
`len(parsed) == len(lines)` by construction (`map` preserves length), and
`len(lines) == 87572` is shown verbatim as the stored output of an earlier
cell in **both** the raw and preprocessed prompts. Raw answered `87572`
(correct). Preprocessed answered `1218` — the stored output of a *different*,
unrelated earlier cell (`cnt = ...; cnt` → `1218`), not a value invented from
nowhere.

**Item B** — `session_num["@User112"]`, expected `1217`. The correct value
`1217` is visible verbatim inside a large DataFrame repr stored as the output
of the *immediately preceding* cell, in both raw and preprocessed prompts.
Raw answered `1217` (correct). Preprocessed answered `2435` — the stored
output of an *earlier* cell that performed the same dict lookup before a
later code edit changed the increment logic (the notebook's actual history
re-ran the same lookup twice, with different code each time — a real,
legitimate `execution_count`-style edit-and-rerun in the source data, not a
preprocessor bug).

**In neither case did the preprocessor strip, truncate, or fail to compute
the correct value.** The published explanation ("the cell defining the value
is truncated out... cannot provide the value") is not what happened here —
the value was present in the exact same words on both sides.

## Step 3: what actually differs — the correct value sits 3–8x farther from the query in the preprocessed prompt

Measuring the character distance from the correct value's last occurrence to
the end of the prompt (where "predict this code" is asked):

| Item | Raw: distance to query | Preprocessed: distance to query | Ratio |
|---|---:|---:|---:|
| A (expected 87572) | 810 chars | 2,205 chars | 2.7x farther |
| B (expected 1217) | 375 chars | 2,871 chars | 7.7x farther |

The preprocessor's variable-state table (11 variables listed for Item B, most
with duplicated/irrelevant `shape_hint`, `history`, and `status` fields that
carry no information relevant to the actual question) is inserted *between*
the code-history block and the "predict this code" prompt. This pushes the
correct evidence substantially farther from the point of prediction than in
the raw format, where the code and its output sit immediately before the
query. In both decisive cases, the model's wrong preprocessed answer matches
a *different, earlier, closer-to-the-query* number rather than the correct
but farther one — consistent with a lost-in-the-middle / anchoring effect,
not an information-loss effect.

## Corrected explanation

**Old (inferred, now shown incorrect for the decisive items):** "Static
analysis doesn't execute code, so when a defining cell is truncated out of
context, the value is unavailable."

**New (measured):** On Themisto specifically, (a) the large majority of the
accuracy gap's constituent items are unanswerable by either format and
contribute no real signal either way; (b) on the two items that actually
decide the result, the preprocessor did not lose or fail to compute the
correct value — it was present verbatim in both formats — but adding a
variable-state table when the underlying data is already short, clean, and
linear (Themisto's own authors already preprocessed the notebooks) pushes the
correct evidence farther from the query, which measurably correlates with
the model latching onto a closer-but-wrong number instead.

This is a more precise and more informative negative result than the
original: it says our "already-clean data" failure mode is not about
static analysis being blind to runtime values in general — it is specifically
about adding structural distance/clutter when there is no bloat to justify
it, i.e. exactly the state-annotation overhead this project already measures
(≈0.3%–1% extra tokens) becoming a net negative on distraction-sensitive,
short-context tasks rather than a positive on token-bloat-heavy ones.

## Caveats

- n=2 for the decisive comparison — this is a case study explaining the
  exact mechanism behind a small, specific gap, not a statistically powered
  general claim. The 9-item "both wrong" population is a much larger,
  separate finding (most of Themisto's difficulty is unrelated to
  serialization format at all).
- This does not revisit or contradict the real-notebook findings elsewhere
  in this project (§5.4 of the paper) — those already conclude no
  distinguishable per-item accuracy advantage for `ours`, for an unrelated
  reason (judge-bug-corrected null result on messy real notebooks). This
  report is specific to Themisto's already-clean, short-context setting.
- Grading here is strict exact-match (Themisto's own methodology); a looser
  grading scheme was not tested and could change which items count as
  "wrong," though it would not change the character-distance measurement in
  Step 3.
