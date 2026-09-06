import os
import sys
import json
import yaml
import re
from huggingface_hub import HfApi, hf_hub_download
from dotenv import load_dotenv
from openai import OpenAI

# Ensure src directory is in the path
sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))
from preprocessor import RuleBasedPreprocessor
from evaluator import get_token_count

load_dotenv()
openai_key = os.environ.get("OPENAI_API_KEY")

class JunoBenchDebugEvaluator:
    def __init__(self, sample_size: int = 8):
        self.sample_size = sample_size
        self.preprocessor = RuleBasedPreprocessor()
        self.api = HfApi()
        self.client = OpenAI(api_key=openai_key) if openai_key else None

    def get_eval_tasks(self):
        """Lists folders that contain both the base and fixed notebook versions."""
        print("Fetching JunoBench repository file listing from Hugging Face...")
        files = self.api.list_repo_files(repo_id="PELAB-LiU/JunoBench", repo_type="dataset")
        
        # Group files by notebook ID
        # Folder structure is benchmark/category_X/category_X.ipynb and category_X_fixed.ipynb
        notebook_folders = {}
        for f in files:
            if f.endswith(".ipynb") and f.startswith("benchmark/"):
                parts = f.split("/")
                if len(parts) >= 3:
                    folder = "/".join(parts[:-1])
                    filename = parts[-1]
                    if folder not in notebook_folders:
                        notebook_folders[folder] = {}
                    if filename.endswith("_fixed.ipynb"):
                        notebook_folders[folder]["fixed"] = f
                    elif not filename.endswith("_reproduced.ipynb"):
                        notebook_folders[folder]["original"] = f

        # Filter folders that have both original and fixed notebooks
        valid_folders = {k: v for k, v in notebook_folders.items() if "original" in v and "fixed" in v}
        print(f"Found {len(valid_folders)} valid JunoBench debug tasks (original + fixed notebooks).")
        return list(valid_folders.values())

    def extract_ground_truth_fix(self, original_path, fixed_path):
        """Identifies and extracts code differences between original and fixed notebooks."""
        try:
            with open(original_path, "r", encoding="utf-8") as f:
                orig = json.load(f)
            with open(fixed_path, "r", encoding="utf-8") as f:
                fixed = json.load(f)
                
            orig_cells = orig.get("cells", [])
            fixed_cells = fixed.get("cells", [])
            
            diffs = []
            for idx, f_cell in enumerate(fixed_cells):
                if f_cell.get("cell_type") != "code":
                    continue
                if idx >= len(orig_cells):
                    diffs.append(f"Added code:\n" + "".join(f_cell.get("source", [])))
                    continue
                    
                o_cell = orig_cells[idx]
                o_source = "".join(o_cell.get("source", [])).strip()
                f_source = "".join(f_cell.get("source", [])).strip()
                
                if o_source != f_source:
                    diffs.append(f"Original Code:\n{o_source}\n\nFixed Code:\n{f_source}")
                    
            return "\n\n".join(diffs) if diffs else "No differences identified."
        except Exception as e:
            return f"Error extracting diff: {e}"

    def query_llm(self, prompt: str) -> str:
        if not self.client:
            return "API_KEY_MISSING"
        try:
            res = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a precise Python debugging expert. Analyze the Jupyter notebook context to locate the bug causing the crash, and write a correct Python code fix. Output only the fixed code inside a single standard ```python block."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0
            )
            return res.choices[0].message.content.strip()
        except Exception as e:
            return f"API_ERROR: {e}"

    def judge_fix(self, expected_fix: str, suggested_fix: str) -> bool:
        if not self.client:
            return False
        judge_prompt = (
            f"Determine if the Model's Suggested Fix is semantically equivalent to the Ground Truth Fix for the Jupyter notebook crash. "
            f"The suggested fix is correct if it solves the same bug (e.g. adding missing imports, correcting data types, fixing execution order) using equivalent logic.\n\n"
            f"Ground Truth Fix:\n{expected_fix}\n\n"
            f"Model's Suggested Fix:\n{suggested_fix}\n\n"
            f"Respond with only 'CORRECT' or 'INCORRECT'. Do not add any other explanation or text."
        )
        try:
            res = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": judge_prompt}],
                temperature=0.0
            ).choices[0].message.content.strip().upper()
            return "CORRECT" in res
        except Exception:
            return False

    def run_evaluation(self):
        tasks = self.get_eval_tasks()
        
        # Sample tasks
        import random
        random.seed(42)
        if len(tasks) > self.sample_size:
            tasks = random.sample(tasks, self.sample_size)
            
        print(f"Selected {len(tasks)} JunoBench debug tasks for full-context LLM evaluation.")
        
        results = []
        raw_correct = 0
        pre_correct = 0
        
        total_raw_tokens = 0
        total_pre_tokens = 0
        
        os.makedirs("tests/junobench_downloads", exist_ok=True)
        
        for idx, task in enumerate(tasks):
            orig_filename = os.path.basename(task["original"])
            print(f"\n[{idx+1}/{len(tasks)}] Evaluating task: {orig_filename}")
            
            try:
                # Download original notebook
                orig_path = hf_hub_download(
                    repo_id="PELAB-LiU/JunoBench",
                    filename=task["original"],
                    repo_type="dataset",
                    local_dir="tests/junobench_downloads"
                )
                
                # Download fixed notebook
                fixed_path = hf_hub_download(
                    repo_id="PELAB-LiU/JunoBench",
                    filename=task["fixed"],
                    repo_type="dataset",
                    local_dir="tests/junobench_downloads"
                )
                
                # Extract ground-truth fix
                expected_fix = self.extract_ground_truth_fix(orig_path, fixed_path)
                
                # Load raw notebook
                with open(orig_path, "r", encoding="utf-8") as f:
                    raw_content = f.read()
                
                # Preprocess to YAML
                preprocessed_dict = self.preprocessor.preprocess(orig_path)
                preprocessed_yaml = yaml.dump(preprocessed_dict, default_flow_style=False, sort_keys=False, allow_unicode=True)
                
                # Format prompts
                raw_prompt = (
                    "Here is a Jupyter notebook that crashes. Locate the bug and suggest the exact Python code fix to resolve it.\n\n"
                    f"--- NOTEBOOK JSON ---\n{raw_content}\n\n"
                    "Provide your suggested fix inside a single python code block."
                )
                
                pre_prompt = (
                    "Here is a preprocessed YAML Jupyter notebook context and its active variable state table. "
                    "The notebook crashes at the end. Locate the bug and suggest the exact Python code fix to resolve it.\n\n"
                    f"--- PREPROCESSED NOTEBOOK ---\n{preprocessed_yaml}\n\n"
                    "Provide your suggested fix inside a single python code block."
                )
                
                # Count tokens
                r_tok = get_token_count(raw_prompt)
                p_tok = get_token_count(pre_prompt)
                
                total_raw_tokens += r_tok
                total_pre_tokens += p_tok
                
                # Query LLM
                raw_suggestion = self.query_llm(raw_prompt)
                pre_suggestion = self.query_llm(pre_prompt)
                
                # Judge
                raw_is_ok = self.judge_fix(expected_fix, raw_suggestion)
                pre_is_ok = self.judge_fix(expected_fix, pre_suggestion)
                
                if raw_is_ok:
                    raw_correct += 1
                if pre_is_ok:
                    pre_correct += 1
                    
                print(f"  Raw Tokens:        {r_tok:,}")
                print(f"  Preprocessed:      {p_tok:,} ({((r_tok - p_tok)/r_tok)*100:.1f}% savings)")
                print(f"  Raw Grade:         {'CORRECT' if raw_is_ok else 'INCORRECT'}")
                print(f"  Preprocessed Grade:{'CORRECT' if pre_is_ok else 'INCORRECT'}")
                
                results.append({
                    "filename": orig_filename,
                    "raw_tokens": r_tok,
                    "preprocessed_tokens": p_tok,
                    "expected_fix": expected_fix,
                    "raw_suggestion": raw_suggestion,
                    "raw_correct": raw_is_ok,
                    "preprocessed_suggestion": pre_suggestion,
                    "preprocessed_correct": pre_is_ok
                })
                
            except Exception as e:
                print(f"  Error processing task {orig_filename}: {e}")
                
        # Write results JSON
        with open("tests/junobench_debug_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
            
        print("\n" + "=" * 80)
        print("JUNOBENCH FULL-CONTEXT DEBUGGING EVALUATION SUMMARY")
        print("=" * 80)
        print(f"Total Debugging Tasks Evaluated: {len(results)}")
        print(f"Raw Notebook Accuracy:           {(raw_correct/len(results))*100:.1f}% ({raw_correct}/{len(results)})")
        print(f"Preprocessed Notebook Accuracy:  {(pre_correct/len(results))*100:.1f}% ({pre_correct}/{len(results)})")
        print(f"Raw Avg Tokens:                  {total_raw_tokens/len(results):.0f}")
        print(f"Preprocessed Avg Tokens:         {total_pre_tokens/len(results):.0f}")
        print(f"Overall Token Savings:           {((total_raw_tokens - total_pre_tokens) / total_raw_tokens) * 100:.1f}%")
        print("=" * 80)
        
        # Save markdown report
        local_dir = "/home/ryn/Documents/research papaer/Jupyter_research/reports"
        os.makedirs(local_dir, exist_ok=True)
        report_path = os.path.join(local_dir, "junobench_debugging_report.md")
        
        rows = []
        for r in results:
            rows.append(
                f"| `{r['filename']}` | {r['raw_tokens']:,} | {r['preprocessed_tokens']:,} | **{'CORRECT' if r['raw_correct'] else 'INCORRECT'}** | **{'CORRECT' if r['preprocessed_correct'] else 'INCORRECT'}** |"
            )
        rows_str = "\n".join(rows)
        
        report_content = f"""# JunoBench Debugging Evaluation Report (Full-Context)

This report evaluates our Jupyter preprocessor against the **JunoBench ML crash debugging benchmark** (`PELAB-LiU/JunoBench` on Hugging Face). 

Rather than truncating the history, this test feeds the **entire visual execution context** (up to the point of failure) in both Raw and Preprocessed formats to **GPT-4o**, measuring bug-repair success rates and token footprint.

## 📊 Summary Metrics

| Metric | Raw Prompt (Standard JSON) | Preprocessed Prompt (Ours) | Change / Savings |
| :--- | :---: | :---: | :---: |
| **Bug Repair Accuracy** | **{(raw_correct/len(results))*100:.1f}%** ({raw_correct}/{len(results)}) | **{(pre_correct/len(results))*100:.1f}%** ({pre_correct}/{len(results)}) | **{((pre_correct - raw_correct)/len(results))*100:+.1f}%** |
| **Avg. Context Prompt Tokens** | **{total_raw_tokens/len(results):.0f}** | **{total_pre_tokens/len(results):.0f}** | **-{((total_raw_tokens - total_pre_tokens)/total_raw_tokens)*100:.1f}%** |
| **Overall Token Reduction** | Baseline | **-{((total_raw_tokens - total_pre_tokens)/total_raw_tokens)*100:.1f}%** | **-{((total_raw_tokens - total_pre_tokens)/total_raw_tokens)*100:.1f}%** |

## 📋 Task Breakdown Table

| Notebook Name | Raw Tokens | Preprocessed Tokens | Raw Bug Fix Grade | Preprocessed Bug Fix Grade |
| :--- | :---: | :---: | :---: | :---: |
{rows_str}

## 🔬 Scientific Analysis

1. **Context Size Cost Savings:** Running debugging agents over raw notebooks consumes large token counts (averaging **{total_raw_tokens/len(results):.0f} tokens** per notebook). Preprocessing compresses this context by **{((total_raw_tokens - total_pre_tokens)/total_raw_tokens)*100:.1f}%**, bringing prompt size down to an average of **{total_pre_tokens/len(results):.0f} tokens**.

**Scope caveat:** this run compares two formats on {len(results)} notebooks in a single pass, with no repeated trials and no variance estimate. It measures *whether* accuracy differs, not *why*. Explanations such as attention dilution, format familiarity, or prompt-length effects are not separated by this design and should not be inferred from these numbers.
"""
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_content)
        print(f"Debugging report successfully written to {report_path}")
        

if __name__ == "__main__":
    evaluator = JunoBenchDebugEvaluator(sample_size=8)
    evaluator.run_evaluation()
