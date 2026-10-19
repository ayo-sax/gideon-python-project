"""Shared JSON load/save helpers."""
import json
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"


def load(filename, default):
    path = DATA_DIR / filename
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default
    except json.JSONDecodeError:
        backup = path.with_suffix(".bak")
        os.replace(path, backup)
        print(f"Warning: {filename} was corrupted. Saved a copy as {backup.name}.")
        return default


def save(filename, data):
    DATA_DIR.mkdir(exist_ok=True)
    tmp = DATA_DIR / (filename + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    os.replace(tmp, DATA_DIR / filename)  # atomic: no half-written files
