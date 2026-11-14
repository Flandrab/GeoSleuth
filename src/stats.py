def analyze(series):
    """FAKE for now: correct shape, example numbers."""
    annual = series.groupby(series.index.year).mean()
    years = annual.index.tolist()
    anomaly = (annual - annual.mean()).round(3).tolist()
    return {
        "years": years,
        "annual_anomaly": anomaly,
        "trend_line": [0.0] * len(years),
        "noise_sigma": 0.4,
        "slope_per_decade": 0.6,
        "ci95": [0.3, 0.9],
        "p_value": 0.004,
        "status": "emerged",
        "emergence_year": 2012,
        "projected_year": None,
        "robust": None,
        "n_years": len(years),
        "is_fake": True,
    }