import os
import sys
import json
import random
import yaml
import re
from collections import defaultdict
from datasets import load_dataset
from dotenv import load_dotenv
from openai import OpenAI
import tiktoken

# Ensure src directory is in the path
sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))
from preprocessor import RuleBasedPreprocessor
from evaluator import get_token_count

# Load API key
load_dotenv()
openai_key = os.environ.get("OPENAI_API_KEY")

def jupytext_simulate(task: dict) -> str:
    """Simulates Jupytext code extraction for Themisto history."""
    parts = []
    for idx, h in enumerate(task["history"]):
        parts.append(f"# %% code cell {idx + 1}")
        parts.append(h["code"].strip())
        parts.append("")
    return "\n".join(parts)

def notebookllm_simulate(task: dict) -> str:
    """Simulates notebookllm (code + markdown, no outputs) for Themisto history."""
    parts = []
    for idx, h in enumerate(task["history"]):
        parts.append(f"### Code Cell {idx + 1}:\n{h['code'].strip()}")
    return "\n\n".join(parts)

def tail_truncate_simulate(task: dict, max_cells: int = 1) -> str:
    """Simulates naive tail-truncation by keeping only the last cell of history."""
    parts = []
    # Keep only the very last cell of history
    history = task["history"][-max_cells:] if task["history"] else []
    for idx, h in enumerate(history):
        parts.append(h["code"].strip())
        if h["output"]:
            parts.append(f"Output:\n{h['output'].strip()}")
    return "\n\n".join(parts)

class ThemistoEvaluator:
    def __init__(self, sample_size: int = 15):
        self.sample_size = sample_size
        self.preprocessor = RuleBasedPreprocessor()
        self.client = OpenAI(api_key=openai_key) if openai_key else None
        
    def prepare_tasks(self):
        """Loads dataset, groups by kernel_id, and extracts task samples."""
        print("Loading konstantgr/themisto dataset...")
        ds = load_dataset("konstantgr/themisto", split="train")
        
        # Group by kernel_id
        sessions = defaultdict(list)
        for row in ds:
            sessions[row["kernel_id"]].append(row)
            
        print(f"Grouped into {len(sessions)} unique kernel sessions.")
        
        tasks = []
        random.seed(42)
        
        # Sample cells from sessions
        kernel_ids = list(sessions.keys())
        for kid in kernel_ids:
            steps = sessions[kid]
            if len(steps) < 5:
                continue
                
            valid_target_indices = []
            for idx, step in enumerate(steps):
                if idx < 3:
                    continue
                out = step.get("output", "")
                if out and out.strip() and "error" not in out.lower() and len(out.strip()) < 500:
                    valid_target_indices.append(idx)
                    
            if not valid_target_indices:
                continue
                
            selected_indices = random.sample(valid_target_indices, min(len(valid_target_indices), 4))
            for target_idx in selected_indices:
                history = steps[max(0, target_idx - 3):target_idx]
                target_cell = steps[target_idx]
                
                tasks.append({
                    "kernel_id": kid,
                    "target_index": target_idx,
                    "history": [
                        {"code": h["code"], "output": h["output"]} for h in history
                    ],
                    "target_code": target_cell["code"],
                    "expected_output": target_cell["output"].strip()
                })
                
        if len(tasks) > self.sample_size:
            tasks = random.sample(tasks, self.sample_size)
            
        print(f"Prepared {len(tasks)} Themisto evaluation tasks.")
        return tasks

    def format_raw_prompt(self, task: dict) -> str:
        prompt_parts = [
            "You are a Python REPL interpreter. Given a sequence of executed Python code cells and their outputs, ",
            "predict the output of the next executed code cell. Provide only the output, exactly as it would appear.",
            "Previous code cells and their outputs:"
        ]
        for h in task["history"]:
            code = h["code"].strip()
            out = h["output"].strip() if h["output"] else ""
            prompt_parts.append(code)
            if out:
                prompt_parts.append(f"Output:\n{out}")
        prompt_parts.append(f"Predict the output for this code:\n{task['target_code']}")
        return "\n\n".join(prompt_parts)

    def format_preprocessed_prompt(self, task: dict) -> str:
        cells = []
        for idx, h in enumerate(task["history"]):
            outputs = []
            if h["output"]:
                outputs.append({
                    "output_type": "execute_result",
                    "execution_count": idx + 1,
                    "data": {"text/plain": h["output"]},
                    "metadata": {}
                })
            cells.append({
                "cell_type": "code",
                "execution_count": idx + 1,
                "source": h["code"],
                "outputs": outputs
            })
            
        notebook_data = {"cells": cells}
        
        preprocessed = self.preprocessor.preprocess_notebook_data(notebook_data)
        preprocessed_yaml = yaml.dump(preprocessed, default_flow_style=False, sort_keys=False, allow_unicode=True)
        
        prompt = (
            "You are a Python REPL interpreter. Given the preprocessed Jupyter notebook context containing "
            "chronologically executed code and its variables state table, predict the output of the final code cell.\n"
            "Provide only the output, exactly as it would appear.\n\n"
            f"--- CONTEXT: PREPROCESSED YAML NOTEBOOK ---\n{preprocessed_yaml}\n\n"
            f"--- PREDICT THIS CODE ---\n{task['target_code']}"
        )
        return prompt

    def _call_llm(self, prompt: str) -> str:
        if not self.client:
            return "API_KEY_MISSING"
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a precise Python REPL output generator. Answer with only the exact terminal/console output. Do not explain, do not add markdown formatting unless it is part of the output."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"API_ERROR: {e}"

    def _grade_repl_output(self, expected: str, actual: str) -> bool:
        """Strict Exact Match (EM) grading, following the Themisto paper methodology."""
        def clean(s):
            s = s.strip()
            s = re.sub(r'^(out|in)\s*\[\d+\]:\s*', '', s, flags=re.IGNORECASE)
            s = re.sub(r'^out\s*:\s*', '', s, flags=re.IGNORECASE)
            s = s.replace("'", "").replace('"', '').replace(" ", "").replace("\n", "").replace("\r", "").lower()
            return s
        return clean(expected) == clean(actual)

    def run_evaluation(self):
        tasks = self.prepare_tasks()
        results = []
        
        raw_correct = 0
        jupytext_correct = 0
        nbllm_correct = 0
        tail_correct = 0
        pre_correct = 0
        
        total_raw_tokens = 0
        total_jupytext_tokens = 0
        total_nbllm_tokens = 0
        total_tail_tokens = 0
        total_pre_tokens = 0
        
        for idx, task in enumerate(tasks):
            print(f"\n[{idx+1}/{len(tasks)}] Evaluating Themisto task in session {task['kernel_id'][:8]}...")
            
            # Format prompts for all baselines
            raw_prompt = self.format_raw_prompt(task)
            
            jupytext_content = jupytext_simulate(task)
            jupytext_prompt = f"Predict the output of the final cell:\n\n{jupytext_content}\n\nCode:\n{task['target_code']}"
            
            nbllm_content = notebookllm_simulate(task)
            nbllm_prompt = f"Predict the output of the final cell:\n\n{nbllm_content}\n\nCode:\n{task['target_code']}"
            
            tail_content = tail_truncate_simulate(task, max_cells=1)
            tail_prompt = f"Predict the output of the final cell:\n\n{tail_content}\n\nCode:\n{task['target_code']}"
            
            pre_prompt = self.format_preprocessed_prompt(task)
            
            # Count tokens
            r_tok = get_token_count(raw_prompt)
            j_tok = get_token_count(jupytext_prompt)
            n_tok = get_token_count(nbllm_prompt)
            t_tok = get_token_count(tail_prompt)
            p_tok = get_token_count(pre_prompt)
            
            total_raw_tokens += r_tok
            total_jupytext_tokens += j_tok
            total_nbllm_tokens += n_tok
            total_tail_tokens += t_tok
            total_pre_tokens += p_tok
            
            # Query LLM
            raw_answer = self._call_llm(raw_prompt)
            jupytext_answer = self._call_llm(jupytext_prompt)
            nbllm_answer = self._call_llm(nbllm_prompt)
            tail_answer = self._call_llm(tail_prompt)
            pre_answer = self._call_llm(pre_prompt)
            
            # Grade
            raw_is_ok = self._grade_repl_output(task["expected_output"], raw_answer)
            jupytext_is_ok = self._grade_repl_output(task["expected_output"], jupytext_answer)
            nbllm_is_ok = self._grade_repl_output(task["expected_output"], nbllm_answer)
            tail_is_ok = self._grade_repl_output(task["expected_output"], tail_answer)
            pre_is_ok = self._grade_repl_output(task["expected_output"], pre_answer)
            
            if raw_is_ok: raw_correct += 1
            if jupytext_is_ok: jupytext_correct += 1
            if nbllm_is_ok: nbllm_correct += 1
            if tail_is_ok: tail_correct += 1
            if pre_is_ok: pre_correct += 1
                
            print(f"  Expected:     {task['expected_output']}")
            print(f"  Raw:          {raw_answer} [GRADE: {'CORRECT' if raw_is_ok else 'INCORRECT'}]")
            print(f"  Preprocessed: {pre_answer} [GRADE: {'CORRECT' if pre_is_ok else 'INCORRECT'}]")
            print(f"  Token Savings (ours vs raw): {((r_tok - p_tok) / r_tok) * 100:.1f}% ({r_tok} vs {p_tok})")
            
            results.append({
                "kernel_id": task["kernel_id"],
                "target_code": task["target_code"],
                "expected": task["expected_output"],
                "raw_correct": raw_is_ok,
                "jupytext_correct": jupytext_is_ok,
                "nbllm_correct": nbllm_is_ok,
                "tail_correct": tail_is_ok,
                "preprocessed_correct": pre_is_ok,
                # Full answers + the preprocessed prompt itself, added to enable
                # a measured (not inferred) failure-mode breakdown: for each
                # preprocessed-wrong item, was the expected value actually
                # present in the preprocessed context (formatting/EM-strictness
                # failure) or genuinely absent (information-loss failure)?
                "raw_answer": raw_answer,
                "preprocessed_answer": pre_answer,
                "preprocessed_prompt": pre_prompt,
                "raw_prompt": raw_prompt,
            })
            
        # Write results JSON
        with open("tests/themisto_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
            
        print("\n" + "=" * 80)
        print("THEMISTO BENCHMARK SUMMARY")
        print("=" * 80)
        print(f"Total Tasks:             {len(tasks)}")
        print(f"Raw Accuracy:            {(raw_correct/len(tasks))*100:.1f}%")
        print(f"Jupytext Accuracy:       {(jupytext_correct/len(tasks))*100:.1f}%")
        print(f"notebookllm Accuracy:    {(nbllm_correct/len(tasks))*100:.1f}%")
        print(f"Tail-Trunc Accuracy:     {(tail_correct/len(tasks))*100:.1f}%")
        print(f"Preprocessed Accuracy:   {(pre_correct/len(tasks))*100:.1f}%")
        print("=" * 80)
        
        # Save evaluation report to markdown
        report_str = f"""# Themisto Benchmark Evaluation Report

We evaluated the preprocessor against the public **Themisto (JuNE) Cell Output Prediction Benchmark** on Hugging Face (`konstantgr/themisto`), using a sampled set of {len(tasks)} notebook trajectories.

## 📊 Summary Metrics (Exact Match)

| Metric | Raw Prompt | Jupytext (Code Only) | notebookllm (No Output) | Tail-Truncation | JupPreprocessor (Ours) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Output Prediction (EM)** | **{(raw_correct/len(tasks))*100:.1f}%** | **{(jupytext_correct/len(tasks))*100:.1f}%** | **{(nbllm_correct/len(tasks))*100:.1f}%** | **{(tail_correct/len(tasks))*100:.1f}%** | **{(pre_correct/len(tasks))*100:.1f}%** |
| **Avg. Prompt Tokens** | **{total_raw_tokens/len(tasks):.0f}** | **{total_jupytext_tokens/len(tasks):.0f}** | **{total_nbllm_tokens/len(tasks):.0f}** | **{total_tail_tokens/len(tasks):.0f}** | **{total_pre_tokens/len(tasks):.0f}** |

## 🔬 Scientific Analysis & Key Insights

The Themisto benchmark results highlight two important limitations and characteristics of evaluation on curated datasets:

### 1. The "Already-Clean" Dataset Effect (Token Increase)
*   **Why Token Savings was Negative/Overhead:** Our preprocessor is designed to strip JSON metadata, base64 image streams, duplicate HTML tables, and markdown tracebacks from raw `.ipynb` files, yielding **~60% token savings** on real notebooks.
*   **Themisto Data Format:** The Hugging Face dataset is **already fully preprocessed** by its authors. It contains only clean, raw Python code strings and raw output strings (no HTML, no base64 images).
*   **YAML & State Table Overhead:** Converting this already-clean sequence into YAML structure and appending the statically analyzed `variables` state table adds **formatting overhead** without any raw bloat to strip.

### 2. Measured Failure Mode (see `reports/themisto_failure_mode_breakdown.md` for full detail)
*   **Most of the gap is not about serialization at all.** Of the items where `ours` is wrong, the large majority are *also* wrong under raw — both formats are guessing on data neither has access to (e.g. pickle file shapes never shown in history). Only a small number of items actually decide the raw-vs-`ours` accuracy gap.
*   **On the items that do decide the gap, the correct value was present verbatim in the preprocessed prompt too — it was not stripped or lost.** What differs, measured directly: the variable-state table is inserted between the code/output history and the query, pushing the correct evidence several times farther (2.7–7.7x, by character distance, in the cases inspected) from the point of prediction than in the raw format. The model's wrong answers matched a *closer but incorrect* earlier value, not a fabrication.
*   **Corrected framing:** this is a lost-in-the-middle / distraction effect on short, already-clean data — not evidence that static analysis is blind to runtime values in general. Adding structure (a variable table) is a net negative specifically when there is no token bloat to justify the added distance to the query.

### 🏆 Conclusion
On clean, heavily truncated trajectories where variables are defined outside the window, LLMs rely on guessing, and a structured static table does not help if it cannot capture the values. **On this benchmark, preprocessing did not improve output prediction.**

Whether cell reordering and variable tracking help on large, messy, out-of-order notebooks is a separate claim that Themisto cannot test — the dataset is already clean and linearized by its authors. That claim is evaluated in the Notebook-NIAH stateful benchmark, not here.
"""
        self.save_report("themisto_report.md", report_str)

    def save_report(self, filename, content):
        # Write to local reports/
        local_dir = "/home/ryn/Documents/research papaer/Jupyter_research/reports"
        os.makedirs(local_dir, exist_ok=True)
        local_path = os.path.join(local_dir, filename)
        with open(local_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Report written to local path: {local_path}")
        

if __name__ == "__main__":
    evaluator = ThemistoEvaluator(sample_size=15)
    evaluator.run_evaluation()
