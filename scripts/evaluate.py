import yaml
import json
import pathlib
from cmtbench import evaluate_solution, evaluate_numeric_solution, evaluate_functional_solution, parse_numeric_solution
import datetime

def load_config():
    with open('scripts/config/eval_config.yaml', 'r') as f:
        return yaml.load(f, Loader=yaml.FullLoader)

def find_query_result_files(config):
    query_results_dir = pathlib.Path(config['query_results_dir'])
    model_files = {}
    for model_name, setting in config['models'].items():
        if setting is False or setting == 'skip':
            continue
        filename_base = model_name.replace('-', '_').replace(' ', '_').replace('.', '_').lower()
        if setting == 'latest':
            pattern = f"{filename_base}_*.json"
            matching_files = list(query_results_dir.glob(pattern))
            
            if not matching_files:
                raise FileNotFoundError(f"No files found matching pattern: {pattern}")

            def extract_timestamp(filepath):
                stem = filepath.stem 
                return stem.split('_')[-1]
            
            latest_file = max(matching_files, key=extract_timestamp)
            model_files[model_name] = latest_file
            
        else:
            target_file = query_results_dir / f"{filename_base}_{setting}.json"
            if not target_file.exists():
                raise FileNotFoundError(f"File not found: {target_file}")
            model_files[model_name] = target_file
    return model_files

def load_data(config):
    result_files = find_query_result_files(config)
    full_data = {}
    for model_name, result_file in result_files.items():
        with open(result_file, 'r') as f:
            data = json.load(f)
        full_data[model_name] = data
    return full_data

def evaluate_response(response_data):
    parameter_str = response_data['parameters']
    function_str = response_data['function']
    solution_str = response_data['solution']
    query_str = response_data['response']
    model_name = response_data['model_name']
    prompt_idx = response_data['prompt_idx']
    type = response_data['type']
    try:
        if parameter_str=='' and function_str=='':
            numeric_parse_attempt = parse_numeric_solution(solution_str)
            if numeric_parse_attempt.success:
                result = evaluate_numeric_solution(query_str, solution_string=solution_str)
            else:
                result = evaluate_solution(query_str, solution_string=solution_str, parameter_string=parameter_str)
        elif parameter_str!='' and function_str=='' and 'NC' not in parameter_str:
            result = evaluate_solution(query_str, solution_string=solution_str, parameter_string=parameter_str)
        else:
            result = evaluate_functional_solution(query_str, solution_string=solution_str, parameter_string=parameter_str, function_string=function_str)
        result = result.to_dict()
    except Exception as e:
        print(f"Error evaluating {model_name} for prompt {prompt_idx}: {e}", flush=True)
        result = {"success": False, "is_equivalent": None, "error_message": str(e)}
    
    eval_result = {
        "success": result['success'],
        "is_equivalent": result['is_equivalent'] if result['success'] is True else None,
        "model_name": model_name,
        "prompt_idx": prompt_idx,
        "type": type,
        "response": query_str,
        "solution": solution_str,
        "parameter": parameter_str,
        "function": function_str,
        "error": result.get('error_message', '')
    }
    return eval_result

if __name__ == "__main__":
    config = load_config()
    model_data = load_data(config)
    eval_results = {"success_results": {}, "failed_results": {}}
    for model_name, data in model_data.items():
        success_results = []
        failed_results = []
        for response_data in data:
            result = evaluate_response(response_data)
            if result['success']:
                success_results.append(result)
            else:
                failed_results.append(result)
        eval_results['success_results'][model_name] = success_results
        eval_results['failed_results'][model_name] = failed_results

    eval_results_dir = pathlib.Path(config['eval_results_dir'])
    current_time = datetime.datetime.now().strftime("%m%d%H%M%S")
    eval_results_dir = eval_results_dir / f'{current_time}'
    eval_results_dir.mkdir(parents=True, exist_ok=True)
    with open(eval_results_dir / 'success_results.json', 'w') as f:
        json.dump(eval_results['success_results'], f, indent=4)
    with open(eval_results_dir / 'failed_results.json', 'w') as f:
        json.dump(eval_results['failed_results'], f, indent=4)
    print(f"Saved {len(eval_results['success_results'])} success results to {eval_results_dir / 'success_results.json'}")
    print(f"Saved {len(eval_results['failed_results'])} failed results to {eval_results_dir / 'failed_results.json'}")