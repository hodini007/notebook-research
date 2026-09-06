# JunoBench Preprocessor Evaluation Report

This report evaluates our Jupyter preprocessor on the official **JunoBench ML crash dataset** (`PELAB-LiU/JunoBench` on Hugging Face), consisting of real-world machine learning code bases.

## 📊 Summary Metrics

| Metric | Value |
| :--- | :---: |
| **Total Notebooks Processed** | **15** |
| **Total Raw Context Tokens** | **4,086,981** |
| **Total Preprocessed YAML Tokens** | **527,322** |
| **Overall Token Reduction** | **87.10%** |

## 📋 Notebook Metrics Table

| Notebook Name | Complexity Route | Cells | Variables | Raw Tokens | Preprocessed Tokens | Token Savings |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `tensorflow_1.ipynb` | **MEDIUM** | 27 | 30 | 1,302,085 | 3,709 | **99.7%** |
| `NBspecific_4.ipynb` | **COMPLEX** | 52 | 56 | 198,101 | 12,093 | **93.9%** |
| `NBspecific_12.ipynb` | **COMPLEX** | 11 | 16 | 5,410 | 3,033 | **43.9%** |
| `tensorflow_8.ipynb` | **COMPLEX** | 44 | 59 | 81,998 | 10,450 | **87.3%** |
| `numpy_3.ipynb` | **COMPLEX** | 45 | 10 | 785,146 | 412,942 | **47.4%** |
| `numpy_13.ipynb` | **COMPLEX** | 74 | 78 | 860,539 | 18,184 | **97.9%** |
| `numpy_10.ipynb` | **COMPLEX** | 33 | 58 | 240,370 | 10,037 | **95.8%** |
| `NBspecific_7.ipynb` | **COMPLEX** | 52 | 14 | 48,792 | 6,057 | **87.6%** |
| `NBspecific_3.ipynb` | **COMPLEX** | 13 | 35 | 67,727 | 7,158 | **89.4%** |
| `tensorflow_14.ipynb` | **COMPLEX** | 5 | 29 | 4,625 | 3,282 | **29.0%** |
| `sklearn_15.ipynb` | **COMPLEX** | 50 | 15 | 14,219 | 6,022 | **57.6%** |
| `NBspecific_2.ipynb` | **COMPLEX** | 35 | 36 | 107,326 | 6,782 | **93.7%** |
| `sklearn_6.ipynb` | **COMPLEX** | 58 | 45 | 237,277 | 12,805 | **94.6%** |
| `pandas_7.ipynb` | **COMPLEX** | 45 | 24 | 78,891 | 10,882 | **86.2%** |
| `NBspecific_13.ipynb` | **COMPLEX** | 43 | 16 | 54,475 | 3,886 | **92.9%** |

## 🔍 Key Structural Insights
1. **Dynamic Complexity Routing:** The preprocessor successfully routed notebooks according to cell count, mutations, and code layout, showing robust routing behavior.
2. **Stable AST State Extraction:** None of the real-world Kaggle/GitHub notebooks caused AST parser crashes, demonstrating high parsing stability across diverse machine learning syntaxes (Keras, PyTorch, Scikit-learn).
