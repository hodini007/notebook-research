import json

def create_messy_notebook(output_path: str):
    """
    Creates a messy Jupyter notebook (.ipynb) to test all preprocessor capabilities:
    1. Redundant MIME outputs (text/plain, text/html)
    2. Base64 image outputs
    3. Notebook and cell metadata (id, tags, collapsed)
    4. Out-of-order execution counts (2, 1, 3, 5, 4)
    5. Traceback with ANSI escape codes
    6. Markdown cells
    """
    notebook = {
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "codemirror_mode": {
                    "name": "ipython",
                    "version": 3
                },
                "file_extension": ".py",
                "mimetype": "text/x-python",
                "name": "python",
                "nbconvert_exporter": "python",
                "pygments_lexer": "ipython3",
                "version": "3.10.0"
            },
            "redundant_notebook_meta": "should be stripped"
        },
        "nbformat": 4,
        "nbformat_minor": 2,
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {
                    "collapsed": False,
                    "id": "cell-markdown-1"
                },
                "source": [
                    "# Test Notebook\n",
                    "This documents cell with execution count 2."
                ]
            },
            {
                "cell_type": "code",
                "execution_count": 2,
                "metadata": {
                    "id": "cell-code-2",
                    "tags": ["data-loading"]
                },
                "source": [
                    "import pandas as pd\n",
                    "print('Loading data...')"
                ],
                "outputs": [
                    {
                        "output_type": "stream",
                        "name": "stdout",
                        "text": [
                            "Loading data...\n"
                        ]
                    }
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {
                    "id": "cell-markdown-2"
                },
                "source": [
                    "## Section 1\n",
                    "This cell executes first (ec=1)."
                ]
            },
            {
                "cell_type": "code",
                "execution_count": 1,
                "metadata": {
                    "id": "cell-code-1"
                },
                "source": [
                    "import numpy as np"
                ],
                "outputs": []
            },
            {
                "cell_type": "markdown",
                "metadata": {
                    "id": "cell-markdown-3"
                },
                "source": [
                    "## Plotting section\n",
                    "This cell has redundant MIME types and base64 image data (ec=3)."
                ]
            },
            {
                "cell_type": "code",
                "execution_count": 3,
                "metadata": {
                    "id": "cell-code-3"
                },
                "source": [
                    "import matplotlib.pyplot as plt\n",
                    "plt.plot([1, 2], [3, 4])"
                ],
                "outputs": [
                    {
                        "output_type": "display_data",
                        "data": {
                            "text/plain": [
                                "[<matplotlib.lines.Line2D at 0x7f8d68ef5a80>]"
                            ],
                            "text/html": [
                                "<div>Matplotlib Plot Object</div>"
                            ],
                            "image/png": "iVBORw0KGgoAAAANSUhEUgAAASAAAAEgCAYAAAAOC9...[BASE64_STUFF]...rkJggg=="
                        },
                        "metadata": {}
                    }
                ]
            },
            {
                "cell_type": "code",
                "execution_count": 5,
                "metadata": {
                    "id": "cell-code-5"
                },
                "source": [
                    "x = 10\n",
                    "x"
                ],
                "outputs": [
                    {
                        "output_type": "execute_result",
                        "execution_count": 5,
                        "data": {
                            "text/plain": [
                                "10"
                            ]
                        },
                        "metadata": {}
                    }
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {
                    "id": "cell-markdown-4"
                },
                "source": [
                    "This cell should fail with traceback (ec=4)."
                ]
            },
            {
                "cell_type": "code",
                "execution_count": 4,
                "metadata": {
                    "id": "cell-code-4"
                },
                "source": [
                    "raise ValueError('Something went wrong!')"
                ],
                "outputs": [
                    {
                        "output_type": "error",
                        "ename": "ValueError",
                        "evalue": "Something went wrong!",
                        "traceback": [
                            "\u001b[0;31m---------------------------------------------------------------------------\u001b[0m",
                            "\u001b[0;31mValueError\u001b[0m                                Traceback (most recent call last)",
                            "\u001b[0;32m/tmp/ipykernel_123/456.py\u001b[0m in \u001b[0;36m<module>\u001b[0;34m()\u001b[0m",
                            "\u001b[1;32m----> 1\u001b[0m \u001b[0mraise\u001b[0m \u001b[0mValueError\u001b[0m\u001b[0;34m(\u001b[0m\u001b[0;31m'Something went wrong!'\u001b[0m\u001b[0;34m)\u001b[0m",
                            "\u001b[0;31mValueError\u001b[0m: Something went wrong!"
                        ]
                    }
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {
                    "id": "cell-code-unexecuted"
                },
                "source": [
                    "# Unexecuted cell\n",
                    "y = 20"
                ],
                "outputs": []
            }
        ]
    }
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(notebook, f, indent=2)

if __name__ == "__main__":
    create_messy_notebook("test_messy.ipynb")
    print("Created test_messy.ipynb")
