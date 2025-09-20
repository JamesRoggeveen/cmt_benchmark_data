import pandas as pd
import yaml
import os
from datetime import datetime

def find_csv_files(csv_dir):
    csv_list = []
    for file in os.listdir(csv_dir):
        if file.endswith(".csv"):
            csv_list.append(file[:-4])
    return csv_list

def convert_csv_to_yaml_fmt(csv_name, config):
    csv_file = f"{config['csv_dir']}/{csv_name}.csv"
    df = pd.read_csv(csv_file)
    # Find the verified column
    verified_col = df.columns[df.columns.str.contains(config['approval_column'], case=False)][0]
    
    # Filter rows where verified is 'yes' (case insensitive)
    df_filtered = df[df[verified_col].str.lower() == 'y']
    # Select required columns
    problems = df_filtered[config['columns']].rename(columns=str.lower)
    key_list = config['columns']
    # Convert to YAML
    yaml_data = []
    for _, row in problems.iterrows():
        problem = {key.lower(): row[key.lower()] for key in key_list}
        problem['prompt'] = problem['prompt'] + ' ' + config['global_prompt']
        yaml_data.append(problem)
    return yaml_data

def write_yaml_file(yaml_data, csv_name, config):
    # Create YAML structure matching boundary_layers.yaml format
    yaml_dir = config['yaml_dir']
    yaml_name = config['yaml_name']
    output_file = f"{yaml_dir}/{yaml_name}.yaml"
    yaml_doc = {
        'meta': {
            'name': csv_name.replace('_',' ').title(),
            'date': datetime.now().strftime('%Y-%m-%d')
        },
        'type': csv_name.lower(),
        'problems': yaml_data
    }
    
    # Reorder keys to put type before problems
    ordered_doc = {
        'meta': yaml_doc['meta'],
        'type': yaml_doc['type'], 
        'problems': yaml_doc['problems'],
    }
    
    with open(output_file, 'w') as f:
        yaml.dump(ordered_doc, f, sort_keys=False, default_flow_style=False, indent=2)

def read_csv_config():
    with open('scripts/csv_config.yaml', 'r') as f:
        return yaml.load(f, Loader=yaml.FullLoader)

if __name__ == "__main__":
    csv_config = read_csv_config()
    csv_dir = csv_config['csv_dir']
    yaml_dir = csv_config['yaml_dir']
    yaml_name = csv_config['yaml_name']
    csv_list = find_csv_files(csv_dir)
    for csv_name in csv_list:
        yaml_data = convert_csv_to_yaml_fmt(csv_name, csv_config)
        write_yaml_file(yaml_data, csv_name, csv_config)




