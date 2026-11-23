"""Loads the human-editable YAML files from the repo-level config/ folder."""
import os
from functools import lru_cache
from pathlib import Path

import yaml

# backend/app/core/config.py -> parents[3] is the repo root
CONFIG_DIR = Path(os.environ.get("FRAUDSHIELD_CONFIG_DIR", Path(__file__).resolve().parents[3] / "config"))


@lru_cache(maxsize=None)
def load_config(name: str) -> dict:
    """Read config/<name>.yaml. Cached; restart the process to pick up edits."""
    with open(CONFIG_DIR / f"{name}.yaml", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}
