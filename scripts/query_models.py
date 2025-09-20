import json
import asyncio
import os
import hashlib
import datetime
import shutil
import argparse
import yaml

from datasets import load_dataset

def load_config():
    with open('scripts/config/query_config.yaml', 'r') as f:
        return yaml.load(f, Loader=yaml.FullLoader)

if __name__ == "__main__":
    config = load_config()
    print(config)
    dataset = load_dataset(config['huggingface_dataset_name'])
    print(dataset)
