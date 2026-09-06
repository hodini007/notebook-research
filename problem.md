# Problems with LLMs and .ipynb Files

**See also:** [`gaps_analysis.md`](gaps_analysis.md) for existing mitigations per root cause,
[`AGENTS.md`](AGENTS.md) for the current preprocessor architecture,
[`README.md`](README.md) for project overview.

## Problem 1: Dynamic Variable States

The `.ipynb` format is **not a program — it's a non-deterministic execution log**. This creates six distinct failure mechanisms:

### Root Cause A — Non-linear execution model

A `.py` file has one execution path (top to bottom). A `.ipynb` has `N!` possible paths. The `execution_count` metadata tells you the **actual** path, but the visual cell order in the JSON often diverges from it:

```
Visual order:   [Cell A (ec=1), Cell B (ec=4), Cell C (ec=2), Cell D (ec=3)]
Execution order: A → C → D → B
```

An LLM reading linearly sees `A → B → C → D` and computes a completely wrong intermediate state.

### Root Cause B — Mutable in-place mutations

DataFrames, dicts, lists, and class instances mutate in-place without any static trace:

```python
# Cell 2 (ec=2): df.dropna(inplace=True)
# Cell 5 (ec=5): df['x'] = df['x'].fillna(0)
```

The `df` seen by Cell 5 has already had rows silently removed by Cell 2. The `.ipynb` JSON gives **zero static indication** of this — only the live kernel knows. Once the kernel dies, this information is permanently lost from the serialized format.

### Root Cause C — Ghost variables (orphaned state)

A user can:
1. Create `model` in Cell 3
2. Execute Cell 3
3. Delete Cell 3 from the notebook
4. `model` still exists in the live kernel

The `.ipynb` JSON has **no record of this variable's origin**. If Cell 10 references `model`, an LLM sees an undefined variable and assumes a bug. The code is actually correct — the state simply has no surviving cell origin.

### Root Cause D — Re-execution divergence

Re-running a cell can produce different results (e.g., `train_test_split` with random seed, `pd.read_csv` after the data file changed, or API calls returning updated data). The `.ipynb` stores only the **first** output. The LLM receives stale state and reasons from incorrect premises.

### Root Cause E — Silenced errors

A cell with an `execution_count` but an error output may have been intentionally allowed to fail, with subsequent cells written to work around the failure. The LLM sees the error traceback and assumes the notebook is broken, when in reality the user designed around it.

### Root Cause F — Type erasure

`.ipynb` stores outputs as `text/plain` strings. `df.describe()` output is just formatted text:

```
       col1      col2
count  100.0  100.000
mean     0.5    0.200
```

The LLM cannot structurally distinguish "this is a DataFrame with 100 rows × 2 columns" from "this is a plain text string" — all structural type information is erased during serialization.

---

## Problem 2: Token Costing

Measured on a real 40-cell Kaggle notebook (~15,000 tokens raw):

| Component | Raw .ipynb tokens | % of total | Useful? |
|-----------|-------------------|------------|---------|
| Cell metadata (ids, tags, collapsed) | ~1,200 | 8% | No |
| Code (actual logic) | ~3,500 | 23% | Yes |
| Output: text/plain | ~4,800 | 32% | Partial |
| Output: text/html (rich tables) | ~3,200 | 21% | Redundant with text/plain |
| Output: image/png (base64) | ~1,500 | 10% | No |
| Notebook metadata (kernelspec, etc.) | ~800 | 5% | No |
| **Total** | **~15,000** | **100%** | **~23% useful** |

### Root Cause G — Redundant MIME bundling

Every output stores multiple MIME representations. A single `display(df)` creates:
- `text/plain` → repr string
- `text/html` → HTML table
- `text/latex` (sometimes)

These are 80%+ semantically overlapping but each is independently tokenized. This effectively triples the cost for no information gain.

### Root Cause H — Base64 encoded as text

A small matplotlib figure encoded as base64 PNG requires ~3,000 tokens of base64 characters:

```
iVBORw0KGgoAAAANSUhEUg...
```

LLMs cannot "see" images from tokenized base64 — it is pure noise that consumes context budget and degrades attention quality. The model must attend to base64 characters one-by-one with no semantic benefit.

### Root Cause I — Accumulated outputs on re-run

If a user executes Cell 5 ten times while debugging, the `.ipynb` appends ten output blocks. Each contains the full repr of `df.head()`. The nine stale outputs are structurally indistinguishable from the current one, forcing the LLM to process all of them.

### Root Cause J — Deeply nested JSON overhead

Each cell is wrapped in 3–4 levels of nesting:

```
notebook.cells[].outputs[].data[].text/plain[]
```

The tokenizer pays for every key name (`"output_type"`, `"execution_count"`, `"metadata"`) on every cell. For a 40-cell notebook, `"execution_count"` appears 40+ times as tokens, each incurring full key + colon + value overhead.

---

## The Coupling Problem

The two problems are coupled — fixing one often worsens the other:

| Approach | State Problem | Token Problem |
|---|---|---|
| Serialize all variables (Themisto) | ✅ Resolved | ❌ Catastrophic |
| Strip all outputs | ❌ State lost | ✅ |
| Keep only text/plain outputs | ❌ Type erased | ✅ Partial |
| Live kernel query (CRANE-LLM) | ✅ | ❌ Heavy JSON |
| Dependency graph pruning (StateSync-MCP) | ✅ Partial | ✅ Partial |
| Static AST analysis only (JupOtter) | ❌ No runtime info | ✅ |

**The fundamental tension**: accurate state understanding requires **more** context (variable values, types, shapes, execution history), but token budgets are **squeezed** by structural noise from the serialization format itself.

An effective solution must **deliver maximum state signal per token spent** — not by compressing, but by structurally separating signal from noise and presenting it in a form the LLM can efficiently process without attending to irrelevant content.

---

## Auxiliary Obstacle K — Magics and shell escapes break static analysis

Not a root cause of LLM misunderstanding, but an obstacle to any static solution: cells containing IPython magics (`%%time`, `%matplotlib inline`) or shell escapes (`!pip install`) are **not valid Python** and crash AST parsers. Any static state extractor must degrade gracefully on these cells (regex-level parsing) rather than losing the whole notebook. Empirically these appear in a large fraction of real notebooks.

---

## The Three-Tier Treatment Framework

Three of the state causes are **information-theoretically unsolvable** from a cold `.ipynb`: the values produced by in-place mutation (B), a ghost variable's origin (C), and whether stored outputs have diverged from reality (D) are simply **not in the file**. No serialization can recover information the format never stored.

An honest solution therefore assigns each root cause one of three treatments:

| Tier | Treatment | Root causes | Mechanism |
|---|---|---|---|
| 1 | **Resolve** — reconstruct the truth statically | A, G, H, I, J | Execution-order sorting; MIME dedup; base64 strip; latest-output-only; YAML |
| 2 | **Detect & flag** — mark exactly where knowledge is unreliable | B, C, D, E, F | Mutation timeline; ghost last-observed value; divergence-risk flags; tolerated/terminal error status; type/shape inference with confidence |
| 3 | **Runtime verification** — recover ground truth by re-executing | B, C, D, E (full fidelity) | Sandboxed re-execution with static-vs-runtime divergence checking (when a kernel is permissible) |

Tier 2 is the key insight for the unsolvable causes: the LLM does not need the missing value to avoid errors — it needs to know **that** the value is uncertain and **where** that uncertainty was introduced. A flagged unknown prevents confident wrong reasoning; a silent unknown invites it.
