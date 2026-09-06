import sys
import os
import json
import yaml
from dotenv import load_dotenv

# Ensure src directory is in the path
sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))
from preprocessor import RuleBasedPreprocessor
from agent_orchestrator import OrchestratorAgent

load_dotenv()
openai_key = os.environ.get("OPENAI_API_KEY")

def run_integration_test():
    print("=" * 80)
    # 1. Preprocess the hard test notebook
    ipynb_path = "tests/test_hard.ipynb"
    print(f"Preprocessing notebook: {ipynb_path}")
    preprocessor = RuleBasedPreprocessor()
    preprocessed_nb = preprocessor.preprocess(ipynb_path)
    
    # 2. Instantiate Orchestrator Agent
    # Runs in full LLM-guided mode if key is available
    orchestrator = OrchestratorAgent(preprocessed_nb, openai_key=openai_key)
    
    # 3. Execute cell by cell
    result = orchestrator.execute_notebook()
    
    print("\n" + "=" * 80)
    print("MULTI-AGENT ENVIRONMENT INTEGRATION RESULTS")
    print("=" * 80)
    print(f"Overall Execution Success: {result['success']}")
    print(f"Total executed steps:      {len(result['steps'])}")
    
    # Trace steps
    for step in result["steps"]:
        print(f"\nStep ec={step['ec']}: {step['code'].strip()}")
        if step["stdout"]:
            print(f"  Stdout: {step['stdout'].strip()}")
        if step["exception"]:
            print(f"  Verifier Caught Exception: {step['exception'].splitlines()[-1]}")
        if step["is_diverged"]:
            print(f"  Verifier Detected State Divergence:")
            for d in step["divergence_report"]:
                print(f"    - {d}")
        if "llm_resolution" in step:
            print(f"  Orchestrator LLM Decision: {step['llm_resolution']}")
            
    print("=" * 80)

if __name__ == "__main__":
    run_integration_test()
