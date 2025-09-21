import json
import asyncio
import os
import datetime
import argparse
import yaml
import pathlib
import cmtbench
from datasets import load_dataset

def load_config():
    with open('scripts/config/query_config.yaml', 'r') as f:
        return yaml.load(f, Loader=yaml.FullLoader)

def get_model_list(config):
    model_dict = config['models']
    model_list = [model for model in model_dict.keys() if model_dict[model]]
    if cmtbench.validate_models(model_list):
        return model_list
    else:
        raise ValueError(f"Unsupported model: {model_list}")

def parse_args():
    parser = argparse.ArgumentParser(description='Query models')
    parser.add_argument('--model_idx', type=int, default=None, help='Restrict to a single model by index')
    parser.add_argument('--prompt_idx', type=int, default=None, help='Restrict to a single prompt by index')
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    config = load_config()
    dataset = load_dataset(config['huggingface_dataset_name'], split="train")

    prompt_list = dataset["prompt"]
    if args.prompt_idx is not None:
        prompt_list = [prompt_list[args.prompt_idx]]
        print(f"Restricted to prompt {args.prompt_idx}", flush=True)

    model_list = get_model_list(config)
    print(f"Loaded {len(model_list)} models from config", flush=True)
    if args.model_idx is not None:
        model_list = [model_list[args.model_idx]]
        print(f"Restricted to model {model_list[0]}")
    print(f"Running query for {len(prompt_list)} prompts with {len(model_list)} models")
    query_results = asyncio.run(cmtbench.bulk_query(prompt_list, model_list, verbose=False))
    
    print(f"Number of query results: {len(query_results)}", flush=True)
    query_results_dir = pathlib.Path(config['query_results_dir'])
    current_time = datetime.datetime.now().strftime("%m%d%H%M%S")
    os.makedirs(query_results_dir, exist_ok=True)

    for model in model_list:
        try:
            serializable_results = [
                {
                    "prompt_idx": prompt_idx,
                    "model_name": model,
                    "response": response,
                    "error": error,
                    "prompt": prompt_list[prompt_idx],
                    "solution": dataset["solution"][prompt_idx],
                    "parameters": dataset["parameters"][prompt_idx],
                    "function": dataset["functions"][prompt_idx],
                    "type": dataset["type"][prompt_idx],
                    "date": current_time
                }
                for response, prompt_idx, model_name, error in query_results
                if model_name == model
                ]
            model_name = model.replace(" ", "_").replace("-", "_").replace(".", "_").lower()
            with open(query_results_dir / f"{model_name}_{current_time}.json", "w") as f:
                json.dump(serializable_results, f, indent=2)
            print(f"Serialized and saved query results for model {model} at {current_time}", flush=True)
        except Exception as e:
            print(f"Error serializing query results for model {model}: {e}", flush=True)
            continue
