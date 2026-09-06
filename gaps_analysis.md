# Gaps Analysis: Mitigations for Root Causes A-J

**See also:** [`problem.md`](problem.md) for root cause details,
[`AGENTS.md`](AGENTS.md) for the current preprocessor architecture,
[`README.md`](README.md) for project overview.

## Our Treatment Status (implemented)

| RC | Tier (see problem.md) | Implementation | Validation |
|---|---|---|---|
| **A** | 1 — Resolve | `_sort_cells()` by `execution_count` | Stateful NIAH: ours 100% vs plain_strip 0% (12/12 cells) |
| **B** | 2 — Flag (3 — runtime for full fidelity) | Mutation timeline (`history`) in variables table | 13-check unit suite |
| **C** | 2 — Flag | Ghost status + last-observed-value recovery from output history | Unit suite; integration test caught `ghost_factor` |
| **D** | 2 — Flag (3 — runtime for full fidelity) | Per-cell `divergence_risk` (unseeded randomness, file/network reads, time) | Unit suite |
| **E** | 2 — Flag | `error_status: tolerated/terminal` via later-execution heuristic | Unit suite |
| **F** | 2 — Flag | Type/shape/dtype inference from code + output reprs, with confidence | Unit suite |
| **G** | 1 — Resolve | `_clean_mime_bundle()` keeps text/plain only | 40 real notebooks, 96.4% aggregate reduction |
| **H** | 1 — Resolve | base64 image stripping | Same (largest single case: 7.5M → 10.5K tokens) |
| **I** | 1 — Resolve | Latest `execute_result` only | Same |
| **J** | 1 — Resolve | YAML serialization | Same |
| **K** (aux) | Graceful degradation | Regex fallback parser when AST rejects magics/shell escapes | 40/40 real notebooks parsed without crash |

## Root Cause → Existing Mitigation → Remaining Gap

### Problem 1: Dynamic Variable States

| Root Cause | Existing Mitigations | Gaps |
|---|---|---|
| **A: Non-linear execution** | **Themisto**: serializes full runtime state per step (all variable values). **Marimo**: DAG-based execution prevents non-linearity entirely. **Jupyter Agent (HF)**: trains models on execution-order trajectories. **Jupiter/MCTS**: frames analysis as state-level search over execution tree. | Themisto's full-state serialization is prohibitively expensive. Marimo requires abandoning .ipynb format. No existing solution efficiently reconstructs execution order from .ipynb alone. |
| **B: In-place mutation** | **variable-inspector (mljar)**: live kernel tracking shows current values. **CRANE-LLM**: queries kernel for var state. **DatawiseAgent**: re-executes cells in kernel to see actual values. | No static analysis can detect mutations. Live kernel query is the only reliable approach, but adds latency. No existing solution caches mutation history across re-executions. |
| **C: Ghost variables** | **variable-inspector (mljar)**: shows all kernel variables regardless of origin. **jupyterlab-variableInspector (lckr)**: similar. | Neither works post-kernel-shutdown. No method recovers ghost variable origins from cold .ipynb. The variable exists in output history but its defining cell is gone. |
| **D: Re-execution divergence** | **Marimo**: prevents via reactive DAG (deterministic order). **DatawiseAgent**: self-debugging stage re-executes and checks outputs. | No system compares output snapshots across runs for drift detection. No versioned output tracking. |
| **E: Silenced errors** | **DatawiseAgent**: DFS-like planning with error recovery (continues past failures). **Jupiter/MCTS**: treats errors as terminal nodes in search tree. | No system distinguishes "intentionally tolerated" errors from bugs. Error context is lost — we don't know if a subsequent cell works around the failure. |
| **F: Type erasure** | **variable-inspector**: stores type metadata. **Themisto**: serializes full variable metadata | Both require live kernel. No static format preserves type info for LLM consumption. |

### Problem 2: Token Costing

| Root Cause | Existing Mitigations | Gaps |
|---|---|---|
| **G: Redundant MIME bundling** | **notebookllm (PyPI)**: strips to plain text (code + markdown only). **Jupytext**: converts to .py files. | Both discard ALL output, losing state signal. No selective MIME deduplication that preserves one representation. |
| **H: Base64 noise** | **notebookllm**: strips all outputs including images. | No system selectively extracts images → describes them → replaces. Image descriptions are not regenerated for LLM consumption. |
| **I: Accumulated outputs** | **nbformat** tools can deduplicate by execution_count. | No deduplication strategy that preserves the *latest* output while discarding stale ones. Stale vs. current indistinguishable in raw JSON. |
| **J: Deep JSON overhead** | **notebookllm**: strips JSON structure entirely. **YAML serialization** (research): ~30% token savings vs JSON. | No structured format designed specifically for LLM consumption. JSON's structural overhead is inherent to the format. |

### The Coupling Problem

| Tension Point | Existing Approaches | Our Insight |
|---|---|---|
| State accuracy requires more context ↔ Token budgets squeezed by noise | **DatawiseAgent**: re-executes in kernel (gets state, pays execution cost). **I-PTC (Berkeley)**: persistent notebook-like environment, reduces token consumption vs stateless. **CaveAgent**: persistent runtime, delegates context engineering. **QC-Opt**: tiered model routing by task difficulty. **DeltaBox**: 14ms checkpoint for agent state. | None combines format-level signal extraction with hybrid static-symbolic state reconstruction. Our key innovation: showing that deterministic rule-based output pruning combined with cheap LLM-assisted state extraction maximizes downstream task accuracy per token spent. |

## Benchmark Landscape

| Benchmark | Domain | Size | Key Metric | Relevance |
|---|---|---|---|---|
| **DABStep** | Data analysis | 450+ tasks | Multi-step accuracy (best: 16% hard) | ✅ Primary eval — tests end-to-end data reasoning |
| **Themisto** | Jupyter trajectories | 1,453 steps | Cell/output prediction | ✅ Tests runtime state utilization |
| **DS-1000** | Python data tasks | 1,000 | Code generation accuracy | Partial — single-shot, no multi-step |
| **SWE-bench** | Software engineering | 2,294 | Patch success rate | Partial — coding, not notebook state |
| **NbQA (Jupiter)** | Notebook QA | 38,635 pairs | Answer accuracy | ✅ Large-scale, notebook-specific |
| **InfiAgent-DABench** | Data analysis | ~350 tasks | Agent accuracy | ✅ DABStep variant (earlier) |
| **PTC-Bench** | Tool calling | Production-style | Task completion + token cost | ✅ Directly measures token efficiency |
| **BixBench** | Bioinformatics analysis | 53 scenarios | Research QA accuracy | Partial — domain-specific, open-ended |

## Candidate Evaluation Plan

1. **Primary**: DABStep (data analysis, multi-step, notebook-centric)
2. **State awareness**: Themisto (measures runtime state utilization)
3. **Token efficiency**: PTC-Bench (measures token consumption)
4. **Scale**: NbQA subset (38k pairs for ablation studies)
