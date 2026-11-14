import numpy as np
import pymannkendall as mk
from scipy import stats as st

EMERGENCE_SN = 2.0               # emerged when the trend is > 2x natural variation
EMERGING_P = 0.20                # "emerging" if p < 0.20 but not yet emerged
MAX_PROJECTION = 2060            # don't project further than this
ROBUST_START_SHIFTS = range(1, 6)  # re-run starting 1 to 5 years later


def _annual_anomalies(series):
    """Monthly values -> remove each month's average -> one value per year."""
    s = series.dropna()
    climatology = s.groupby(s.index.month).transform("mean")
    monthly_anom = s - climatology
    annual = monthly_anom.groupby(monthly_anom.index.year).mean()
    counts = monthly_anom.groupby(monthly_anom.index.year).count()
    return annual[counts >= 10]  # skip years with too many missing months


def analyze(series, check_robustness=True):
    annual = _annual_anomalies(series)
    years = [int(y) for y in annual.index]
    y = annual.values.astype(float)
    n = len(y)
    idx = np.arange(n)

    # 1. Trend size: Sen's slope (per year)
    sen = mk.sens_slope(y)
    slope = float(sen.slope)
    trend_line = sen.intercept + slope * idx

    # Significance: Mann-Kendall with trend-free pre-whitening (Yue et al., 2002),
    # which handles autocorrelation. Fall back to the original test if it fails.
    p_value = float(mk.trend_free_pre_whitening_modification_test(y).p)
    if not np.isfinite(p_value):
        p_value = float(mk.original_test(y).p)

    # 2. OLS t-test + 95% confidence interval for the slope
    ols = st.linregress(idx, y)
    tcrit = st.t.ppf(0.975, n - 2)
    ci_low = (ols.slope - tcrit * ols.stderr) * 10
    ci_high = (ols.slope + tcrit * ols.stderr) * 10

    # 3. Natural variation = spread of the values around the trend
    sigma = float(np.std(y - trend_line, ddof=1))

    # 4. Emergence: signal-to-noise = |change since the first year| / sigma
    status, emergence_year, projected_year = "no_signal", None, None
    if sigma > 0 and slope != 0:
        sn = np.abs(slope * idx) / sigma
        crossed = np.where(sn >= EMERGENCE_SN)[0]
        if p_value < 0.05 and len(crossed) > 0:
            status = "emerged"
            emergence_year = years[int(crossed[0])]
        elif p_value < EMERGING_P:
            proj = years[0] + EMERGENCE_SN * sigma / abs(slope)
            if proj <= MAX_PROJECTION:
                status = "emerging"
                projected_year = int(round(proj))

    result = {
        "years": years,
        "annual_anomaly": [round(float(v), 4) for v in y],
        "trend_line": [round(float(v), 4) for v in trend_line],
        "noise_sigma": round(sigma, 4),
        "slope_per_decade": round(slope * 10, 4),
        "ci95": [round(float(ci_low), 4), round(float(ci_high), 4)],
        "p_value": round(p_value, 4),
        "ttest_p": round(float(ols.pvalue), 4),
        "status": status,
        "emergence_year": emergence_year,
        "projected_year": projected_year,
        "robust": None,
        "robust_statuses": None,
        "n_years": n,
    }

    # 5. Robustness: does the verdict stay the same if we start a few years later?
    if check_robustness:
        first_year = years[0]
        statuses = {first_year: status}
        for shift in ROBUST_START_SHIFTS:
            start = first_year + shift
            sub = series[series.index.year >= start]
            statuses[start] = analyze(sub, check_robustness=False)["status"]
        result["robust"] = all(s == status for s in statuses.values())
        result["robust_statuses"] = statuses

    return result