---
language: 
- en
license: mit
---

# CMT Benchmark Dataset

This repository contains a collection of condensed matter physics benchmark problems designed for evaluating Large Language Models (LLMs) on scientific reasoning tasks.

## Building
Save `.csv` file exported from Google Sheet to `raw_csv` folder and run `csv_to_yaml.py` to convert all of the `.csv` file sto `.yaml`. Then push the changes to remote and the `.yaml` file will automatically be converted to `.jsonl` and pushed to an anonymized HF repository.

The `.csv` file should have a descriptive name for the types of problems in the file, with underscores instead of spaces.

## Data Format

Each benchmark problem in the dataset is structured as a JSON object containing the following fields:

### Fields

- **Prompt**: The input string that is fed to the LLM
- **Solution**: A LaTeX-formatted string representing the mathematical formula that solves the question posed in the prompt
- **Parameters**: A list of independent tokens that should be treated as single variables in the LaTeX response string. These include:
  - Single variables (e.g., `$A$`, `$x$`)
  - Greek letters (e.g., `$\epsilon$`)
  - Complex strings with subscripts (e.g., `$\delta_{i,j}$`)
  
  Each parameter should be separated by a semicolon (;).
- **Functions**: A list of tokens that should be treated as a general function in the results string. These functions should act on some object, i.e. if `y` is in the list of functions, we interpret `y(x)` as `y` applied to `x` rather than `y*x`. The function data should be a single string with functions separated by semi-colons. Note that common functions like `sin`, etc. need not be declared. They may take the following forms
  - Single letters (e.g., `$A$`, `$x$`)
  - Greek letters (e.g., `$\epsilon$`)
  - Complex strings with subscripts (e.g., `$\delta_{i,j}$`)

## Example

```json
{
  "prompt": "What is the derivative of f(x) = x^2?",
  "solution": "\\frac{d}{dx}(x^2) = 2x",
  "parameters": "x",
  "functions": ""
}
```