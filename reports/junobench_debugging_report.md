# JunoBench Debugging Evaluation Report (Full-Context)

This report evaluates our Jupyter preprocessor against the **JunoBench ML crash debugging benchmark** (`PELAB-LiU/JunoBench` on Hugging Face). 

Rather than truncating the history, this test feeds the **entire visual execution context** (up to the point of failure) in both Raw and Preprocessed formats to **GPT-4o**, measuring bug-repair success rates and token footprint.

## 📊 Summary Metrics

| Metric | Raw Prompt (Standard JSON) | Preprocessed Prompt (Ours) | Change / Savings |
| :--- | :---: | :---: | :---: |
| **Bug Repair Accuracy** | **100.0%** (8/8) | **100.0%** (8/8) | **+0.0%** |
| **Avg. Context Prompt Tokens** | **292229** | **61120** | **-79.1%** |
| **Overall Token Reduction** | Baseline | **-79.1%** | **-79.1%** |

## 📋 Task Breakdown Table

| Notebook Name | Raw Tokens | Preprocessed Tokens | Raw Bug Fix Grade | Preprocessed Bug Fix Grade |
| :--- | :---: | :---: | :---: | :---: |
| `tensorflow_10.ipynb` | 29,132 | 14,584 | **CORRECT** | **CORRECT** |
| `NBspecific_4.ipynb` | 198,141 | 12,150 | **CORRECT** | **CORRECT** |
| `NBspecific_12.ipynb` | 5,450 | 3,090 | **CORRECT** | **CORRECT** |
| `tensorflow_9.ipynb` | 170,104 | 11,692 | **CORRECT** | **CORRECT** |
| `numpy_3.ipynb` | 785,186 | 412,999 | **CORRECT** | **CORRECT** |
| `numpy_13.ipynb` | 860,578 | 18,241 | **CORRECT** | **CORRECT** |
| `numpy_10.ipynb` | 240,410 | 10,094 | **CORRECT** | **CORRECT** |
| `NBspecific_7.ipynb` | 48,832 | 6,114 | **CORRECT** | **CORRECT** |

## 🔬 Scientific Analysis

1. **Context Size Cost Savings:** Running debugging agents over raw notebooks consumes large token counts (averaging **292229 tokens** per notebook). Preprocessing compresses this context by **79.1%**, bringing prompt size down to an average of **61120 tokens**.

**Scope caveat:** this run compares two formats on 8 notebooks in a single pass, with no repeated trials and no variance estimate. It measures *whether* accuracy differs, not *why*. Explanations such as attention dilution, format familiarity, or prompt-length effects are not separated by this design and should not be inferred from these numbers.
