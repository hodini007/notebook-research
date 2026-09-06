import os
import sys
import json
import tiktoken


# Ensure the src directory is in Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from preprocessor import RuleBasedPreprocessor


def get_token_count(text: str, model: str = "gpt-4") -> int:
    """Estimates token count for a text string using tiktoken."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))

def format_percentage(saved: float) -> str:
    return f"{saved:.1f}%"

def run_evaluation(notebook_dirs: list):
    preprocessor = RuleBasedPreprocessor()
    results = []

    # Collect all notebooks
    notebook_paths = []
    for directory in notebook_dirs:
        if not os.path.exists(directory):
            continue
        for file in os.listdir(directory):
            if file.endswith(".ipynb"):
                notebook_paths.append(os.path.join(directory, file))

    if not notebook_paths:
        print("No notebooks found to evaluate.")
        return

    print(f"Found {len(notebook_paths)} notebooks for token reduction evaluation.\n")

    total_raw_tokens = 0
    total_cleaned_tokens = 0

    for path in notebook_paths:
        filename = os.path.basename(path)
        try:
            # Read raw notebook
            with open(path, "r", encoding="utf-8") as f:
                raw_content = f.read()
                raw_json = json.loads(raw_content)

            raw_tokens = get_token_count(raw_content)

            # Preprocess
            preprocessed_dict = preprocessor.preprocess(path)
            import yaml
            cleaned_yaml = yaml.dump(preprocessed_dict, default_flow_style=False, sort_keys=False, allow_unicode=True)
            cleaned_tokens = get_token_count(cleaned_yaml)
            complexity = preprocessed_dict.get("complexity_route", "unknown")

            token_saved = raw_tokens - cleaned_tokens
            pct_saved = (token_saved / raw_tokens) * 100 if raw_tokens > 0 else 0

            results.append({
                "filename": filename,
                "raw_size_kb": len(raw_content) / 1024,
                "yaml_size_kb": len(cleaned_yaml) / 1024,
                "raw_tokens": raw_tokens,
                "yaml_tokens": cleaned_tokens,
                "saved_pct": pct_saved,
                "complexity": complexity
            })

            total_raw_tokens += raw_tokens
            total_cleaned_tokens += cleaned_tokens

        except Exception as e:
            print(f"Error processing {filename}: {e}")

    # Sort results by raw tokens descending
    results.sort(key=lambda x: x["raw_tokens"], reverse=True)

    # Print results table
    header = ["Notebook Name", "Complexity", "Raw Size (KB)", "YAML Size (KB)", "Raw Tokens", "YAML Tokens", "Reduction %"]
    rows = []
    for r in results:
        rows.append([
            r["filename"],
            r["complexity"].upper(),
            f"{r['raw_size_kb']:.1f}",
            f"{r['yaml_size_kb']:.1f}",
            f"{r['raw_tokens']:,}",
            f"{r['yaml_tokens']:,}",
            format_percentage(r["saved_pct"])
        ])


    # Print nicely formatted ASCII table
    col_widths = [max(len(str(item)) for item in col) for col in zip(header, *rows)]
    col_widths[0] = max(col_widths[0], 25) # min width for filename
    
    border = "+" + "+".join("=" * (w + 2) for w in col_widths) + "+"
    header_row = "|" + "|".join(f" {h:<{w}} " for h, w in zip(header, col_widths)) + "|"
    
    print(border)
    print(header_row)
    print(border)
    for row in rows:
        print("|" + "|".join(f" {str(val):<{w}} " for val, w in zip(row, col_widths)) + "|")
    print(border)

    avg_saved = ((total_raw_tokens - total_cleaned_tokens) / total_raw_tokens) * 100 if total_raw_tokens > 0 else 0
    print(f"\nSummary Evaluation:")
    print(f"Total Raw Tokens:     {total_raw_tokens:,}")
    print(f"Total Cleaned Tokens: {total_cleaned_tokens:,}")
    print(f"Overall Reduction:    {avg_saved:.2f}% (Target: ~57%)")

if __name__ == "__main__":
    notebook_dirs = [
        "/home/ryn/Desktop/codes/ml_notebook",
        "/home/ryn/Desktop/codes/machine learning",
        "/home/ryn/Documents/research papaer/Jupyter_research"
    ]
    run_evaluation(notebook_dirs)
