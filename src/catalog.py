import json
from pathlib import Path

CATALOG_PATH = Path(__file__).resolve().parents[1] / "data" / "catalog.json"


def load_catalog():
    with open(CATALOG_PATH, encoding="utf-8") as f:
        return json.load(f)


def get_variable(variable_id):
    for v in load_catalog():
        if v["id"] == variable_id:
            return v
    raise KeyError(f"Unknown variable: {variable_id}")