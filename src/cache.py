from pathlib import Path

import pandas as pd

CACHE_DIR = Path(__file__).resolve().parents[1] / "data" / "cache"


def _path(key):
    return CACHE_DIR / f"{key}.parquet"


def load(key):
    p = _path(key)
    if p.exists():
        return pd.read_parquet(p)["value"]
    return None


def save(key, series):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    series.rename("value").to_frame().to_parquet(_path(key))