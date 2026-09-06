import json

def add_tasks():
    with open("tests/evaluation_tasks.json", "r", encoding="utf-8") as f:
        tasks = json.load(f)
        
    # Check if they are already added to avoid duplicates
    if any(t["id"] == 11 for t in tasks):
        print("Hard tasks already present.")
        return

    hard_tasks = [
        {
            "id": 11,
            "notebook_path": "/home/ryn/Documents/research papaer/Jupyter_research/tests/test_hard.ipynb",
            "question": "What is the final value of variable 'y' in the notebook? Trace the value chronologically by execution_count (ec) sequence rather than visual layout order.",
            "expected_answer": "20 (x is set to 10 in ec1, mutated to 15 in ec2, and y is computed as x + 5 (15 + 5) in ec3)"
        },
        {
            "id": 12,
            "notebook_path": "/home/ryn/Documents/research papaer/Jupyter_research/tests/test_hard.ipynb",
            "question": "What is the final value of variable 'row_count' in the notebook? Trace the value chronologically by execution_count (ec) sequence.",
            "expected_answer": "3 (df is created with a None in ec4, the None is filled with 0 in ec5, and df.dropna(inplace=True) is executed in ec6, which drops no rows because there are no longer any NaN values. Thus row_count remains 3)"
        },
        {
            "id": 13,
            "notebook_path": "/home/ryn/Documents/research papaer/Jupyter_research/tests/test_hard.ipynb",
            "question": "Is variable 'ghost_factor' defined in any cell of the notebook? What is its status and will executing the final cell result in a NameError in the active session?",
            "expected_answer": "No, 'ghost_factor' is not defined in any cell. However, its status is 'ghost' (referenced but defining cell is missing). It exists in the active kernel state, so executing the final cell will not throw a NameError."
        }
    ]
    
    tasks.extend(hard_tasks)
    
    with open("tests/evaluation_tasks.json", "w", encoding="utf-8") as f:
        json.dump(tasks, f, indent=2)
    print("Added hard tasks to tests/evaluation_tasks.json")

if __name__ == "__main__":
    add_tasks()
