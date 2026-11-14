import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd

from src.stats import analyze


def make_series(trend_per_year, noise, seed=0):
    idx = pd.date_range("2001-01-01", "2024-12-01", freq="MS")
    t = np.arange(len(idx))
    rng = np.random.default_rng(seed)
    seasonal = 10 * np.sin(2 * np.pi * t / 12)
    trend = trend_per_year * t / 12
    return pd.Series(15 + seasonal + trend + rng.normal(0, noise, len(idx)), index=idx)


def test_strong_trend_emerges():
    r = analyze(make_series(0.05, 0.3))
    assert r["status"] == "emerged"
    assert 0.35 < r["slope_per_decade"] < 0.65   # true value: 0.5 per decade
    assert r["p_value"] < 0.05
    assert r["emergence_year"] is not None


def test_no_trend_does_not_emerge():
    r = analyze(make_series(0.0, 0.3, seed=1))
    assert r["status"] != "emerged"


def test_seasons_removed():
    r = analyze(make_series(0.0, 0.0))
    assert max(abs(v) for v in r["annual_anomaly"]) < 0.01

def test_p_value_is_never_nan():
    import math
    for trend in (0.0, 0.02, 0.05, 0.1):
        r = analyze(make_series(trend, 0.3, seed=3))
        assert math.isfinite(r["p_value"])