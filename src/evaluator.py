import os
import sys
import json
import re
import tiktoken
from dotenv import load_dotenv
from preprocessor import RuleBasedPreprocessor


# Ensure the src directory is in Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables (for API keys)
load_dotenv()

def get_token_count(text: str, model: str = "gpt-4") -> int:
    """Estimates token count for a text string using tiktoken."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))

class Evaluator:
    """
    Evaluator to compare raw vs preprocessed notebook formats on QA tasks.
    Supports both offline prompt generation + token analysis and online LLM API execution.
    """
    def __init__(self, tasks_json_path: str):
        with open(tasks_json_path, "r", encoding="utf-8") as f:
            self.tasks = json.load(f)
        self.preprocessor = RuleBasedPreprocessor()

    def run_token_comparison(self):
        """Runs offline token size comparison and generates prompts."""
        print("=" * 80)
        print("RUNNING TOKEN SIZE & CONTEXT ANALYSIS (OFFLINE)")
        print("=" * 80)
        
        os.makedirs("tests/prompts", exist_ok=True)
        
        results = []
        for task in self.tasks:
            task_id = task["id"]
            nb_path = task["notebook_path"]
            question = task["question"]
            
            # Load raw notebook
            with open(nb_path, "r", encoding="utf-8") as f:
                raw_content = f.read()
                
            # Preprocess to YAML
            preprocessed_content = self.preprocessor.preprocess_to_yaml(nb_path)
            
            raw_tokens = get_token_count(raw_content)
            preprocessed_tokens = get_token_count(preprocessed_content)
            reduction = ((raw_tokens - preprocessed_tokens) / raw_tokens) * 100 if raw_tokens > 0 else 0
            
            # Save raw and preprocessed prompts to files for user manual testing
            raw_prompt = f"--- CONTEXT: RAW JUPYTER NOTEBOOK ---\n{raw_content}\n\n--- QUESTION ---\n{question}\n\nProvide a concise and accurate answer based on the context."
            preprocessed_prompt = f"--- CONTEXT: PREPROCESSED YAML NOTEBOOK ---\n{preprocessed_content}\n\n--- QUESTION ---\n{question}\n\nProvide a concise and accurate answer based on the context."
            
            with open(f"tests/prompts/task_{task_id}_raw.txt", "w", encoding="utf-8") as f:
                f.write(raw_prompt)
            with open(f"tests/prompts/task_{task_id}_preprocessed.txt", "w", encoding="utf-8") as f:
                f.write(preprocessed_prompt)
                
            print(f"Task {task_id:02d}: {os.path.basename(nb_path)}")
            print(f"  Raw Context Tokens:          {raw_tokens:,}")
            print(f"  Preprocessed Context Tokens: {preprocessed_tokens:,}")
            print(f"  Token Savings:               {reduction:.1f}%")
            print(f"  Prompts generated at tests/prompts/task_{task_id}_*.txt\n")
            
            results.append({
                "id": task_id,
                "raw_tokens": raw_tokens,
                "preprocessed_tokens": preprocessed_tokens,
                "reduction_pct": reduction
            })
            
        print("=" * 80)
        return results

    def _grade_response(self, client, provider: str, model: str, expected: str, response: str) -> bool:
        """Grades response against expected output. Uses strict exact matching for digits, and LLM-as-a-judge for text."""
        exp = expected.strip()
        resp = response.strip()
        
        # If expected is a simple digit (like Task 11 and 12)
        if exp.isdigit():
            # Find all numbers in the response
            numbers = re.findall(r'\b\d+\b', resp)
            return exp in numbers
            
        # For list tasks (like Task 3) where expected is formatted as a list representation
        if expected.strip().startswith("[") and expected.strip().endswith("]"):
            elements = expected.replace("[", "").replace("]", "").replace("'", "").replace('"', '').split(",")
            return all(el.strip().lower() in resp.lower() for el in elements)
            
        # Otherwise, use LLM-as-a-judge for semantic verification
        if response.startswith("API_ERROR:") or "NOT_FOUND" in response:
            return False
            
        judge_prompt = (
            f"You are an automated grader. Compare the Model Answer against the Ground Truth. "
            f"Determine if the Model Answer is semantically correct and contains the key factual numbers and terms from the Ground Truth.\n\n"
            f"Ground Truth: {expected}\n"
            f"Model Answer: {response}\n\n"
            f"Respond with only 'CORRECT' or 'INCORRECT'. Do not add any other words."
        )
        
        try:
            grade_raw = self._call_api(client, provider, model, judge_prompt)
            # Normalize response
            grade_clean = grade_raw.strip().upper().replace(".", "").replace('"', '').replace("'", "")
            return "CORRECT" in grade_clean
        except Exception:
            # Fallback to simple keyword/number subset match
            words = expected.lower().replace(",", "").replace("[", "").replace("]", "").replace("'", "").replace('"', '').split()
            keywords = [w for w in words if len(w) > 2 or w.isdigit()]
            response_lower = response.lower()
            matches = sum(1 for kw in keywords if kw in response_lower)
            return (matches / len(keywords)) >= 0.7 if keywords else True


    def run_llm_evaluation(self, provider: str = "openai", model: str = None):
        """Runs the online evaluation if API keys are set."""
        openai_key = os.environ.get("OPENAI_API_KEY")
        anthropic_key = os.environ.get("ANTHROPIC_API_KEY")

        
        if provider == "openai" and not openai_key:
            print("\n[WARNING] OPENAI_API_KEY not found in environment variables.")
            print("Please set it or use offline mode. Prompt files have been generated in tests/prompts/.")
            return
        elif provider == "anthropic" and not anthropic_key:
            print("\n[WARNING] ANTHROPIC_API_KEY not found in environment variables.")
            print("Please set it or use offline mode. Prompt files have been generated in tests/prompts/.")
            return

        print("\n" + "=" * 80)
        print(f"RUNNING LLM EVALUATION WITH PROVIDER: {provider.upper()}")
        print("=" * 80)

        # Initialize clients
        if provider == "openai":
            from openai import OpenAI
            client = OpenAI(api_key=openai_key)
            default_model = model or "gpt-4o-mini"
        else:
            from anthropic import Anthropic
            client = Anthropic(api_key=anthropic_key)
            default_model = model or "claude-3-5-sonnet-20241022"

        results = []
        raw_correct_count = 0
        preprocessed_correct_count = 0
        total_tasks = len(self.tasks)

        for task in self.tasks:
            task_id = task["id"]
            nb_path = task["notebook_path"]
            question = task["question"]
            expected = task["expected_answer"]
            
            print(f"\nEvaluating Task {task_id}: {os.path.basename(nb_path)}...")
            
            # Load raw prompt and preprocessed prompt
            with open(f"tests/prompts/task_{task_id}_raw.txt", "r", encoding="utf-8") as f:
                raw_prompt = f.read()
            with open(f"tests/prompts/task_{task_id}_preprocessed.txt", "r", encoding="utf-8") as f:
                preprocessed_prompt = f.read()

            # Execute Raw Prompt
            raw_response = self._call_api(client, provider, default_model, raw_prompt)
            
            # Execute Preprocessed Prompt
            preprocessed_response = self._call_api(client, provider, default_model, preprocessed_prompt)
            
            # Grade responses
            raw_correct = self._grade_response(client, provider, default_model, expected, raw_response)
            preprocessed_correct = self._grade_response(client, provider, default_model, expected, preprocessed_response)
            
            if raw_correct:
                raw_correct_count += 1
            if preprocessed_correct:
                preprocessed_correct_count += 1

            print(f"  Question:        {question}")
            print(f"  Expected:        {expected}")
            print(f"  Raw Answer:      {raw_response} [GRADE: {'CORRECT' if raw_correct else 'INCORRECT'}]")
            print(f"  Preprocessed:    {preprocessed_response} [GRADE: {'CORRECT' if preprocessed_correct else 'INCORRECT'}]")
            
            results.append({
                "id": task_id,
                "question": question,
                "expected": expected,
                "raw_response": raw_response,
                "raw_correct": raw_correct,
                "preprocessed_response": preprocessed_response,
                "preprocessed_correct": preprocessed_correct
            })
            
        # Write results log
        with open("tests/eval_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
            
        raw_accuracy = (raw_correct_count / total_tasks) * 100
        preprocessed_accuracy = (preprocessed_correct_count / total_tasks) * 100
        
        print("\n" + "=" * 80)
        print("EVALUATION ACCURACY REPORT")
        print("=" * 80)
        print(f"Raw Notebook Prompt Accuracy:        {raw_accuracy:.1f}% ({raw_correct_count}/{total_tasks})")
        print(f"Preprocessed Notebook Prompt Accuracy: {preprocessed_accuracy:.1f}% ({preprocessed_correct_count}/{total_tasks})")
        print("=" * 80)
        print(f"Evaluation complete. Detailed responses written to tests/eval_results.json")

    def _call_api(self, client, provider: str, model: str, prompt: str) -> str:
        """Helper to call OpenAI or Anthropic chat completion APIs."""
        try:
            if provider == "openai":
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "You are a precise data science assistant. Answer the question based on the provided Jupyter notebook context. Mentally execute the code cells chronologically if necessary to determine the values and state transitions of variables."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.0
                )
                return response.choices[0].message.content.strip()
            else:
                response = client.messages.create(
                    model=model,
                    max_tokens=1024,
                    system="You are a precise data science assistant. Answer the question based on the provided Jupyter notebook context. Mentally execute the code cells chronologically if necessary to determine the values and state transitions of variables.",
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.0
                )
                return response.content[0].text.strip()
        except Exception as e:
            return f"API_ERROR: {e}"


if __name__ == "__main__":
    evaluator = Evaluator("tests/evaluation_tasks.json")
    evaluator.run_token_comparison()
    
    # Check if there is an API key to run LLM evaluation
    if os.environ.get("OPENAI_API_KEY"):
        evaluator.run_llm_evaluation(provider="openai", model="gpt-4o")
    elif os.environ.get("ANTHROPIC_API_KEY"):
        evaluator.run_llm_evaluation(provider="anthropic", model="claude-3-5-sonnet-20241022")
    else:
        print("\nNote: Export OPENAI_API_KEY or ANTHROPIC_API_KEY to run the automated LLM evaluation.")
