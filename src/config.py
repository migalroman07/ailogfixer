import json
import os

# Dynamically calculate absolute path to the project root.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CONFIG_PATH = os.path.join(BASE_DIR, "config.json")


def load_config():
    with open("config.json") as f:
        return json.load(f)


def save_config(updated_config):
    with open("config.json", "w", encoding="utf-8") as f:
        json.dump(updated_config, f, indent=4, ensure_ascii=False)
