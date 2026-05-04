import json
import os

# Dynamically calculate absolute path to the project root.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CONFIG_PATH = os.path.join(BASE_DIR, "config.json")


def load_config() -> dict:
    """Loads config file."""
    with open("config.json") as f:
        config = json.load(f)
        if "features" not in config:
            config["features"] = {
                "system_snapshot": True,
                "auto_capture": True,
                "autonomous_mode": False,
                "auto_summary": True,
                "circuit_breaker": True,
                "smart_placeholders": True,
                "pause_resume_hint": True,
            }
            save_config(config)
        return config


def save_config(updated_config):
    """Saves changes to the config file."""
    with open("config.json", "w", encoding="utf-8") as f:
        json.dump(updated_config, f, indent=4, ensure_ascii=False)
