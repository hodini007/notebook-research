# Environment-Dependent Branching vs. Static-Analysis Failures: A Test (Inconclusive)

Follow-up to `reports/execution_count_reordering_limitation.md` and the
feasibility research in `outputs/notebook-preprocessor-feasibility.md`, which
flagged this project's working theory — that environment-dependent branching
(e.g. `torch.cuda.is_available()`-style checks) is a specific static-analysis
blind spot distinct from the `execution_count` edge case — as an **unconfirmed
inference**, not something found stated in any external source. This is a
cheap, $0, no-LLM static check against this project's own real-notebook
ground truth (`tests/real_state_groundtruth.json`, `tests/real_state_eval_raw_answers.json`)
to see whether the project's own data supports or weakens that inference.

## Method

For each of the 41 real-notebook ground-truth items, scanned the source
notebook for any cell that assigns the target variable and also matches an
environment-dependent-branching regex (`torch.cuda.is_available()`,
`torch.device(`, `os.environ`, `sys.platform`, `platform.system()`,
`is_available()`, `CUDA_VISIBLE_DEVICES`, `device_count()`). Cross-tabulated
the LLM eval outcomes (TRUTH/DECOY/NEITHER, all 3 conditions, 98 answer
records) against this flag.

## Result

**8 of 41 items** matched the environment-branching pattern:
`numpy_1.ipynb`'s `batch_size`, `device`, `img_size`, `learning_rate`,
`num_channels`, `num_epochs`, `z_dim`, and `torch_4.ipynb`'s `device`.

Raw correlation looked strong at first: env-flagged items had an 88.2% wrong
(DECOY+NEITHER) rate (15/17 answer instances) vs. 48.1% for non-flagged items
(39/81) — a large apparent gap.

**This correlation does not support the hypothesis as an independent
finding.** Checking `tests/real_state_groundtruth.json` directly: **all 8 of
8** environment-branching-flagged items are `phantom_in_visual` with
`ec_order_value = None` — the exact same signature as the items already
explained by the `execution_count`-sort edge case (an import cell reordered
after code that uses it, per `reports/execution_count_reordering_limitation.md`).
`torch_4.ipynb` independently confirms this: it has 2 documented
import-specific `execution_count` violations (`np`, `pd`) per
`reports/execution_count_consistency_report.md`, and its flagged `device`
item is `ec_order_value = None` for the same reason as `numpy_1.ipynb`'s
items — not because environment-dependent branching itself defeated static
analysis, but because the cell chain leading to `device`'s assignment was
never reachable in the reconstructed execution order.

**Zero of the 8 flagged items are independent of the already-documented
mechanism.** This dataset cannot confirm or refute "environment-dependent
branching is a distinct static-analysis blind spot" — every candidate
instance is fully explained by the prior, already-quantified cause instead.

## Conclusion

This is an honest negative/inconclusive result, not a confirmation. The
project's inference about environment-dependent branching remains
**unconfirmed** — not because it's wrong, but because this specific corpus
(41 items, 14 notebooks) happens to contain zero cases that would let it be
tested independently of the execution_count confound. Testing this properly
would require either a larger real-notebook sample with environment-branching
cases *not* also affected by execution_count reordering, or a targeted
synthetic benchmark cell (analogous to the Notebook-NIAH design) that isolates
environment-dependent branching as the sole manipulated variable.

**Recommendation:** the paper's existing hedge ("this connection is an
inference, not a directly documented finding") should be strengthened to
note that a direct internal test was attempted and found inconclusive due to
confounding, rather than left as an untested inference. Do not claim this
project's evidence supports the environment-branching hypothesis — it
neither confirms nor refutes it.
