import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd

from src.catalog import load_catalog
from src.detect import scan_region
from src.sonify import sonify
from src.stats import analyze


def fake_series():
    idx = pd.date_range("2001-01-01", "2024-12-01", freq="MS")
    t = np.arange(len(idx))
    return pd.Series(10 + 8 * np.sin(2 * np.pi * t / 12) + 0.003 * t, index=idx)


def test_catalog():
    assert len(load_catalog()) >= 1


def test_analyze():
    r = analyze(fake_series())
    assert r["n_years"] == 24
    assert r["status"] in ("emerged", "emerging", "no_signal")


def test_scan():
    assert len(scan_region(42.66, 21.17, ["heat"])) > 0


def test_sonify():
    assert sonify([2001], [0.0])[:4] == b"RIFF"