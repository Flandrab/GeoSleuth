import numpy as np

from src.catalog import load_catalog
from src.data import get_series
from src.stats import analyze

STATUS_ORDER = {"emerged": 0, "emerging": 1, "no_signal": 2}


def _benjamini_hochberg(pvals):
    """False-discovery-rate correction: q-values for many tests at once."""
    p = np.asarray(pvals, dtype=float)
    n = len(p)
    order = np.argsort(p)
    q = np.empty(n)
    prev = 1.0
    for rank in range(n, 0, -1):
        i = order[rank - 1]
        prev = min(prev, p[i] * n / rank)
        q[i] = prev
    return q


def scan_region(lat, lon, topics=None):
    """Analyze every catalog variable (optionally filtered by topic) for one place."""
    catalog = load_catalog()
    selected = [v for v in catalog if not topics or v["topic"] in topics]

    results = []
    for v in selected:
        try:
            r = analyze(get_series(v["id"], lat, lon))
        except Exception as e:  # one failing variable shouldn't break the scan
            print(f"Skipping {v['id']}: {e}")
            continue
        results.append({
            "variable_id": v["id"],
            "name": v["name"],
            "unit": v["unit"],
            "status": r["status"],
            "emergence_year": r["emergence_year"],
            "projected_year": r["projected_year"],
            "slope_per_decade": r["slope_per_decade"],
            "p_value": r["p_value"],
            # for the small charts on the Trend scanner page
            "years": r["years"],
            "annual_anomaly": r["annual_anomaly"],
            "trend_line": r["trend_line"],
            "noise_sigma": r["noise_sigma"],
        })

    if results:
        q = _benjamini_hochberg([x["p_value"] for x in results])
        for x, qv in zip(results, q):
            x["q_value"] = round(float(qv), 4)
            # after correcting for many tests, a weak "emerged" becomes "emerging"
            if x["status"] == "emerged" and qv >= 0.05:
                x["status"] = "emerging"
                x["emergence_year"] = None

    results.sort(key=lambda x: (STATUS_ORDER[x["status"]], x["emergence_year"] or 9999))
    return results