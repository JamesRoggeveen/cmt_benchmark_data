import json
import pathlib
import datasets
import yaml
import matplotlib.pyplot as plt

plt.rcParams.update({
    'font.family': 'serif',
    'font.size': 16,
    'axes.labelsize': 16,
    'axes.titlesize': 16,
    'xtick.labelsize': 16,
    'ytick.labelsize': 16,
    'legend.fontsize': 16,
    'figure.titlesize': 24
})

def get_eval_directory(config):
    eval_results_dir = pathlib.Path(config['eval_results_dir'])
    if config['eval_directory'] == 'latest':
        all_dirs = [d for d in eval_results_dir.iterdir() if d.is_dir()]
        
        if not all_dirs:
            raise FileNotFoundError(f"No directories found in {eval_results_dir}")
        
        target_dir = max(all_dirs, key=lambda d: d.name)
    else:
        target_dir = eval_results_dir / config['eval_directory']
    config["eval_directory"] = target_dir

def load_config():
    with open('scripts/config/summary_config.yaml', 'r') as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    get_eval_directory(config)
    return config

def load_eval_results(config):
    target_dir = config["eval_directory"]
    success_results = json.load(open(target_dir / 'success_results.json'))
    failed_results = json.load(open(target_dir / 'failed_results.json'))
    success_copy = success_results.copy()
    for model_name, results in failed_results.items():
        for result in results:
            if result['success']:
                success_copy[model_name].append(result)
    return {"success_results": success_copy, "failed_results": failed_results, "original_success_results": success_results}
    
def dataset_distribution_chart(config):
    dataset = datasets.load_dataset(config['huggingface_dataset_name'],split="train")

    df = dataset.to_pandas()

    type_counts = df['type'].value_counts()
    colors = ['#cce5ff', '#ffcce5', '#e5ccff', '#ffffcc', '#ffcccc', '#ccffcc']

    plt.figure(figsize=(8, 8)) 
    plt.pie(
        type_counts,
        labels=type_counts.index,
        autopct='%1.1f%%',             
        startangle=100,               
        colors=colors,                 
        wedgeprops={'edgecolor': 'white', 'linewidth': 2}
    )

    plt.title(f'Problem type distribution ({len(df)} problems)', pad=40)
    plt.axis('equal')
    plt.savefig(config['eval_directory'] / 'problem_type_distribution.png')
    plt.close()

def parser_success_rate_chart(config, eval_results):
    model_list = eval_results["success_results"].keys()
    success_rate = {}
    for model_name in model_list:
        num_success = len(eval_results["original_success_results"][model_name])
        num_failed = len(eval_results["failed_results"][model_name])
        success_rate[model_name] = num_success / (num_success + num_failed) * 100
    plt.figure(figsize=(10, 6))
    models = list(success_rate.keys())
    rates = list(success_rate.values())
    plt.bar(models, rates, color='skyblue', edgecolor='navy', alpha=0.7)
    plt.ylabel('Success Rate')
    plt.title('Parser Success Rate by Model')
    plt.ylim(0, 100)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(config['eval_directory'] / 'parser_success_rate.png')
    plt.close()

def pass_at_1_rate_chart(config, eval_results):
    model_list = eval_results["success_results"].keys()
    pass_at_1_rate = {}
    results = eval_results["success_results"]
    for model_name in model_list:
        total_successful_evals = len(results[model_name])
        total_pass_at_1 = sum(1 for eval in results[model_name] if eval["is_equivalent"])
        if total_successful_evals == 0:
            pass_at_1_rate[model_name] = 0
        else:
            pass_at_1_rate[model_name] = total_pass_at_1 / total_successful_evals * 100
    plt.figure(figsize=(10, 6))
    models = list(pass_at_1_rate.keys())
    rates = list(pass_at_1_rate.values())
    plt.bar(models, rates, color='skyblue', edgecolor='navy', alpha=0.7)
    plt.ylabel('Overall Success Rate')
    plt.title('Overal Rate by Model')
    plt.ylim(0, 100)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(config['eval_directory'] / 'pass_at_1_rate.png')
    plt.close()

def pass_rate_per_problem_type_chart(config, eval_results):
    model_list = eval_results["success_results"].keys()
    pass_rate_per_problem_type = {}
    results = eval_results["success_results"]
    for model_name in model_list:
        model_equivalent_by_type = {}
        model_count_by_type = {}
        pass_rate_per_problem_type[model_name] = {}
        for result in results[model_name]:
            problem_type = result["type"]
            model_equivalent_by_type[problem_type] = int(result["is_equivalent"]) + model_equivalent_by_type.get(problem_type, 0)
            model_count_by_type[problem_type] = model_count_by_type.get(problem_type, 0) + 1
        for problem_type in model_equivalent_by_type.keys():
            if model_count_by_type[problem_type] == 0:
                pass_rate_per_problem_type[model_name][problem_type] = 0
            else:
                pass_rate_per_problem_type[model_name][problem_type] = model_equivalent_by_type[problem_type] / model_count_by_type[problem_type] * 100
    plt.figure(figsize=(10, 6))
    models = list(pass_rate_per_problem_type.keys())
    # Collect all problem types across all models
    all_problem_types = set()
    for model_name in models:
        all_problem_types.update(pass_rate_per_problem_type[model_name].keys())
    problem_types = sorted(list(all_problem_types))
    
    # Dynamic color allocation from a list of colors
    color_list = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
    color_lookup = {problem_type: color_list[i % len(color_list)] for i, problem_type in enumerate(problem_types)}
    
    plt.figure(figsize=(12, 6))
    x = range(len(models))
    width = 0.8 / len(problem_types)
    
    for i, problem_type in enumerate(problem_types):
        rates = []
        for model in models:
            rates.append(pass_rate_per_problem_type[model].get(problem_type, 0))
        
        color = color_lookup[problem_type]
        plt.bar([pos + i * width for pos in x], rates, width, 
                label=problem_type, color=color, alpha=0.8)
    
    plt.xlabel('Models')
    plt.xticks([pos + width * (len(problem_types) - 1) / 2 for pos in x], models)
    plt.legend()
    plt.ylabel('Pass Rate')
    plt.title('Pass Rate per Problem Type by Model')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(config['eval_directory'] / 'pass_rate_per_problem_type.png')
    plt.close()

def parser_success_rate_per_prompt_chart(config, eval_results):
    success_per_prompt = {}
    queries_per_prompt = {}
    success_results = eval_results["success_results"]
    failed_results = eval_results["failed_results"]
    model_list = success_results.keys()
    for model_name in model_list:
        for result in failed_results[model_name]:
            prompt_idx = result["prompt_idx"]
            queries_per_prompt[prompt_idx] = queries_per_prompt.get(prompt_idx, 0) + 1
        for result in success_results[model_name]:
            prompt_idx = result["prompt_idx"]
            success_per_prompt[prompt_idx] = success_per_prompt.get(prompt_idx, 0) + 1
            queries_per_prompt[prompt_idx] = queries_per_prompt.get(prompt_idx, 0) + 1
    
    success_rate_per_prompt = {}
    for prompt_idx in success_per_prompt.keys():
        if queries_per_prompt[prompt_idx] == 0:
            success_rate_per_prompt[prompt_idx] = 0
        else:
            success_rate_per_prompt[prompt_idx] = success_per_prompt[prompt_idx] / queries_per_prompt[prompt_idx] * 100
    plt.figure(figsize=(10, 6))
    plt.bar([prompt_idx for prompt_idx in success_rate_per_prompt.keys()], [success_rate_per_prompt[prompt_idx] for prompt_idx in success_rate_per_prompt.keys()], label='Success')
    plt.ylabel('Success Rate')
    plt.title('Parser Success Rate per Prompt by Model')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(config['eval_directory'] / 'parser_success_rate_per_prompt.png')
    plt.close()

def eval_success_rate_per_prompt_chart(config, eval_results):
    success_per_prompt = {}
    queries_per_prompt = {}
    success_results = eval_results["success_results"]
    model_list = success_results.keys()
    for model_name in model_list:
        for result in success_results[model_name]:
            prompt_idx = result["prompt_idx"]
            queries_per_prompt[prompt_idx] = queries_per_prompt.get(prompt_idx, 0) + 1
            success_per_prompt[prompt_idx] = success_per_prompt.get(prompt_idx, 0) + int(result["is_equivalent"])
    success_rate_per_prompt = {}
    for prompt_idx in success_per_prompt.keys():
        if queries_per_prompt[prompt_idx] == 0:
            success_rate_per_prompt[prompt_idx] = 0
        else:
            success_rate_per_prompt[prompt_idx] = success_per_prompt[prompt_idx] / queries_per_prompt[prompt_idx] * 100
    plt.figure(figsize=(10, 6))
    plt.bar([prompt_idx for prompt_idx in success_rate_per_prompt.keys()], [success_rate_per_prompt[prompt_idx] for prompt_idx in success_rate_per_prompt.keys()], label='Success')
    plt.ylabel('Success Rate')
    plt.title('Success Rate per Prompt by Model')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(config['eval_directory'] / 'eval_success_rate_per_prompt.png')
    plt.close()

if __name__ == "__main__":
    config = load_config()
    dataset_distribution_chart(config)
    eval_results = load_eval_results(config)
    parser_success_rate_chart(config, eval_results)
    parser_success_rate_per_prompt_chart(config, eval_results)
    pass_at_1_rate_chart(config, eval_results)
    pass_rate_per_problem_type_chart(config, eval_results)
    eval_success_rate_per_prompt_chart(config, eval_results)