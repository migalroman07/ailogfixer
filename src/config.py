import json


def load_config():
    with open("config.json") as f:
        return json.load(f)


def save_config(updated_config):
    with open("config.json", "w", encoding="utf-8") as f:
        json.dump(updated_config, f, indent=4, ensure_ascii=False)
