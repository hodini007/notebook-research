import json

def create_hard_notebook(output_path: str):
    """
    Creates a notebook with highly complex state tracking scenarios:
    1. Out-of-order execution where variables are mutated and read out of visual sequence.
    2. DataFrame mutations where in-place modification order dictates the final shape.
    3. Ghost variables that are referenced but their creating cells are missing.
    """
    notebook = {
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.10.0"}
        },
        "nbformat": 4,
        "nbformat_minor": 2,
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "# Hard Test 1: Out-of-Order Math\n",
                    "We define x, then read y (which depends on x), but x is mutated in between out of order."
                ]
            },
            {
                "cell_type": "code",
                "execution_count": 1,
                "metadata": {},
                "source": [
                    "x = 10"
                ],
                "outputs": []
            },
            {
                "cell_type": "code",
                "execution_count": 3,
                "metadata": {},
                "source": [
                    "y = x + 5"
                ],
                "outputs": []
            },
            {
                "cell_type": "code",
                "execution_count": 2,
                "metadata": {},
                "source": [
                    "x = 15"
                ],
                "outputs": []
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "# Hard Test 2: In-place DataFrame Mutation Order\n",
                    "A DataFrame with a NaN value is filled before dropna runs, but dropna appears earlier visually."
                ]
            },
            {
                "cell_type": "code",
                "execution_count": 4,
                "metadata": {},
                "source": [
                    "import pandas as pd\n",
                    "df = pd.DataFrame({'a': [1, None, 3]})"
                ],
                "outputs": []
            },
            {
                "cell_type": "code",
                "execution_count": 6,
                "metadata": {},
                "source": [
                    "df.dropna(inplace=True)\n",
                    "row_count = len(df)"
                ],
                "outputs": []
            },
            {
                "cell_type": "code",
                "execution_count": 5,
                "metadata": {},
                "source": [
                    "df['a'] = df['a'].fillna(0)"
                ],
                "outputs": []
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "# Hard Test 3: Ghost Variable Reference\n",
                    "Variable 'ghost_factor' is used in cell below, but its definition cell (ec=7) has been deleted."
                ]
            },
            {
                "cell_type": "code",
                "execution_count": 8,
                "metadata": {},
                "source": [
                    "final_score = 100 * ghost_factor"
                ],
                "outputs": []
            }
        ]
    }
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(notebook, f, indent=2)

if __name__ == "__main__":
    create_hard_notebook("tests/test_hard.ipynb")
    print("Created tests/test_hard.ipynb")
