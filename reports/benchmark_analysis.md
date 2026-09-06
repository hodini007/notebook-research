# Benchmark Analysis: What Should We Actually Use?

## The Big Discovery

**DABStep doesn't use `.ipynb` files.** It gives the LLM CSV/JSON data + a question. There's no notebook involved. So it tests "can the LLM do data analysis" — not "does the LLM understand notebooks better after preprocessing."

That's a problem, because your preprocessor specifically cleans **notebooks**. You need benchmarks that actually feed notebooks to LLMs.

---

## Every Benchmark We Found, Sorted by Relevance

### ✅ Actually Uses `.ipynb` Files (Best Fit)

| Benchmark | Size | What it tests | How answers are scored | Fit for you |
|---|---|---|---|---|
| **Themisto** | 1,453 steps | Give LLM a notebook execution trace → predict next cell's output | Exact match against ground truth | 🔥 Perfect — directly tests state understanding |
| **NbQA** (from Jupiter) | 38,635 pairs | Give LLM a notebook → answer a question about it | Factoid exact match | 🔥 Perfect — largest notebook QA dataset, ideal for A/B testing raw vs preprocessed |
| **BixBench** | 50+ scenarios, ~300 questions | Give LLM a real research notebook → answer science questions | Objective answers + MCQ | 🔥 Good — real-world complex notebooks |
| **PTC-Bench** (I-PTC Berkeley) | Production-style | Measures task completion AND token consumption in notebook-like environments | Task completion + token count | 🔥 Perfect — only benchmark that measures token efficiency |

### ⚠️ Tests Data Analysis but NOT Notebooks

| Benchmark | Size | What it tests | Why it's not ideal |
|---|---|---|---|
| **DABStep** | 450 tasks | Multi-step data reasoning from CSV files | No `.ipynb` input — tests analysis skill, not notebook understanding |
| **DA-Code** | 500 tasks | Code generation in Docker sandbox | No `.ipynb` — sandbox execution |
| **DSBench** | 540 tasks | Kaggle-style analysis + modeling | No `.ipynb` — competition data files |
| **InfiAgent-DABench** | 603 questions | Data analysis from CSVs | Earlier DABStep variant |
| **DS-1000** | 1,000 problems | Single-shot code generation | No multi-step, no notebook state |

### 💡 Not Notebook-Specific but Has Useful Methodology

| Benchmark/Method | What to borrow from it |
|---|---|
| **OckBench** | The **OckScore** metric: `accuracy / tokens_used`. Perfect composite metric for your paper |
| **Needle-In-A-Haystack (NIAH)** | Adapt to notebooks: hide a variable deep in a large notebook, test if LLM finds it |
| **Lost in the Middle** | Test if your preprocessor's output format avoids the "middle blind spot" problem |
| **RULER** | Has a "variable tracing" task (X1=5, X2=X1, X3=X2) — almost identical to notebook state tracking |
| **LLMLingua** | Methodology for measuring compression quality: KL-divergence between compressed vs full output |

---

## My Recommendation: The Evaluation Stack

### Layer 1 — Primary (must have for the paper)

| Benchmark | What it proves | Experiment |
|---|---|---|
| **NbQA** (38,635 pairs) | "Preprocessed notebooks → better LLM answers" | Feed raw `.ipynb` vs preprocessed → same LLM → compare accuracy |
| **Themisto** (1,453 steps) | "Preprocessed notebooks → better state understanding" | Feed raw trace vs preprocessed trace → compare output prediction |

**Why these two:** They're the only large benchmarks that actually use `.ipynb` as input. NbQA tests answer quality, Themisto tests state tracking. Together they cover both claims.

### Layer 2 — Token Efficiency (must have)

| What to measure | How |
|---|---|
| Token count reduction | `tiktoken` on raw vs preprocessed (your ~57% claim) |
| Cost reduction | Tokens × price per model |
| **Notebook OckScore** | `correct_answers / tokens_used` — borrowed from OckBench |

This doesn't need a benchmark — you measure it during NbQA and Themisto runs.

### Layer 3 — Custom Tests (novel, makes your paper stand out)

| Custom Test | What it proves | How to build it |
|---|---|---|
| **Notebook-NIAH** | Preprocessor preserves critical state info even in large notebooks | Take 50+ cell notebooks, inject a variable mutation at depth X, ask LLM "what is the value of this variable?". Compare raw vs preprocessed at different depths |
| **State Fidelity Test** | Preprocessor doesn't lose important information | For 100 notebooks: ask 5 state questions each (variable type, shape, value, origin, mutation history). Score: how many does the LLM get right with raw vs preprocessed? |

These don't exist yet — **you create them**. Custom benchmarks that test exactly what your tool does are stronger than adapting generic benchmarks.

### Layer 4 — Ablation (which preprocessing step matters most)

| Configuration | Run on NbQA + Themisto |
|---|---|
| Full preprocessor | Baseline "ours" |
| No execution reordering | How much does sorting by `execution_count` help? |
| No MIME deduplication | How much does stripping HTML/LaTeX help? |
| No base64 stripping | How much does removing images help? |
| No YAML conversion (keep JSON) | How much does format change help? |
| No variable table | How much does state extraction help? |
| Strip everything (notebookllm-style) | Aggressive baseline — fewer tokens but loses state |
| Raw `.ipynb` | Lower bound baseline |

---

## What I'd Drop from Your Current Plan

| Original plan | Recommendation | Why |
|---|---|---|
| DABStep as primary | Demote to secondary/optional | Doesn't use `.ipynb` — tests analysis skill, not notebook preprocessing |
| PTC-Bench | Keep if accessible | Great for token efficiency but may be hard to get (Berkeley technical report) |
| Themisto | ✅ Keep as primary | Perfect fit |
| NbQA | ⬆️ Promote to primary | 38K pairs, uses real notebooks, largest dataset |

---

## The Paper's Results Section Would Look Like

### Table 1: Main Results (NbQA subset — 1,000 tasks)
```
Method              │ Accuracy │ Avg Tokens │ OckScore │ Cost/task
────────────────────┼──────────┼────────────┼──────────┼──────────
Raw .ipynb → GPT-4  │  48.2%   │  14,800    │   3.26   │  $0.074
notebookllm → GPT-4 │  44.1%   │   4,200    │  10.50   │  $0.021
Ours → GPT-4        │  61.5%   │   6,400    │   9.61   │  $0.032
────────────────────┼──────────┼────────────┼──────────┼──────────
Raw .ipynb → Claude  │  51.0%   │  14,800    │   3.45   │  $0.044
Ours → Claude        │  64.8%   │   6,400    │  10.13   │  $0.019
```

> **Key insight:** notebookllm has a high OckScore (very few tokens) but LOW accuracy — it strips too much. We achieve almost as few tokens but MUCH higher accuracy.

### Table 2: State Understanding (Themisto — 1,453 steps)
```
Method              │ Output Prediction │ State Questions
────────────────────┼───────────────────┼────────────────
Raw .ipynb → GPT-4  │     35.2%         │    28.0%
Ours → GPT-4        │     48.7%         │    52.3%
```

### Table 3: Notebook-NIAH (Custom — 200 tests)
```
Depth of state info │ Raw .ipynb │ Preprocessed
────────────────────┼────────────┼─────────────
Top (cells 1-5)     │   82%      │    88%
Middle (cells 15-25)│   41%      │    76%      ← biggest win
Bottom (cells 35-40)│   71%      │    85%
```

> **Key insight:** Raw notebooks suffer from "lost in the middle" — LLMs miss state info buried in the middle. Our preprocessor fixes this by restructuring the output.

### Table 4: Ablation (NbQA subset — 500 tasks)
```
Configuration            │ Accuracy │ Tokens │ Δ Accuracy
─────────────────────────┼──────────┼────────┼───────────
Full preprocessor        │  61.5%   │  6,400 │  baseline
 − execution reordering  │  53.2%   │  6,400 │  −8.3%
 − MIME deduplication     │  58.1%   │  9,800 │  −3.4%
 − base64 stripping      │  59.8%   │  9,200 │  −1.7%
 − YAML (keep JSON)      │  58.9%   │  8,500 │  −2.6%
 − variable table        │  55.7%   │  5,800 │  −5.8%
Strip everything         │  44.1%   │  4,200 │  −17.4%
Raw .ipynb               │  48.2%   │ 14,800 │  −13.3%
```

*(All numbers are hypothetical — you'll get real ones from experiments)*
