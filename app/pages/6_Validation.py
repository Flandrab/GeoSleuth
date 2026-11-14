import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.data import get_series
from src.stats import analyze

GIOVANNI_FILE = ROOT / "data" / "validation" / "giovanni_imerg_kosovo.csv"

# Four points inside the same Kosovo box Giovanni averaged over (20.0-21.8 E, 41.85-43.27 N)
KOSOVO_POINTS = [(42.30, 20.60), (42.30, 21.40), (42.90, 20.60), (42.90, 21.40)]


def format_p(p):
    return "< 0.001" if p < 0.001 else f"{p:.3f}"


def load_giovanni_csv(path):
    """Read a Giovanni area-averaged time series CSV into a monthly pandas Series."""
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()
    start = next(i for i, line in enumerate(lines) if line.lower().startswith("time"))
    df = pd.read_csv(path, skiprows=start)
    df.columns = ["date", "value"]
    df["date"] = pd.to_datetime(df["date"])
    s = df.set_index("date")["value"].astype(float)
    return s.where(s > -9000)  # Giovanni marks missing values as -9999.9


st.title("Validation")
st.write(
    "How do we know our results are right? We compare NASA POWER rainfall, which comes from "
    "a weather model, with GPM IMERG, an independent record built from satellites and rain "
    "gauges. Both are averaged over Kosovo for 2001 to 2024."
)

# --- Load both datasets ---
with st.spinner("Loading both datasets..."):
    imerg = load_giovanni_csv(GIOVANNI_FILE) * 24  # mm/hour -> mm/day
    power_points = [get_series("precip", lat, lon) for lat, lon in KOSOVO_POINTS]
    power = pd.concat(power_points, axis=1).mean(axis=1)

r_power = analyze(power)
r_imerg = analyze(imerg)

# --- Chart: yearly anomalies from both sources ---
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=r_power["years"], y=r_power["annual_anomaly"], mode="markers+lines",
    name="NASA POWER (model)", line=dict(color="#e4572e"),
))
fig.add_trace(go.Scatter(
    x=r_imerg["years"], y=r_imerg["annual_anomaly"], mode="markers+lines",
    name="GPM IMERG (satellites + gauges)", line=dict(color="#2e86de"),
))
fig.update_layout(
    xaxis_title="Year",
    yaxis_title="Rainfall difference from average (mm/day)",
    height=420, margin=dict(t=30),
)
st.plotly_chart(fig, use_container_width=True)

# --- Agreement numbers ---
common = sorted(set(r_power["years"]) & set(r_imerg["years"]))
a = pd.Series(r_power["annual_anomaly"], index=r_power["years"]).loc[common]
b = pd.Series(r_imerg["annual_anomaly"], index=r_imerg["years"]).loc[common]
correlation = float(np.corrcoef(a, b)[0, 1])

STATUS = {"emerged": "Emerged", "emerging": "Emerging", "no_signal": "No clear signal"}
table = pd.DataFrame(
    {
        "NASA POWER (model)": [
            f"{r_power['slope_per_decade']:+.3f}",
            format_p(r_power["p_value"]),
            STATUS[r_power["status"]],
        ],
        "GPM IMERG (satellites + gauges)": [
            f"{r_imerg['slope_per_decade']:+.3f}",
            format_p(r_imerg["p_value"]),
            STATUS[r_imerg["status"]],
        ],
    },
    index=["Rate of change (mm/day per decade)", "Chance it's random (p)", "Verdict"],
)
st.table(table)
st.metric("Correlation between the yearly values", f"{correlation:.2f}")

# --- Plain-language conclusion ---
same_direction = r_power["slope_per_decade"] * r_imerg["slope_per_decade"] > 0
same_verdict = r_power["status"] == r_imerg["status"]
if correlation >= 0.7 and same_verdict:
    st.success(
        "**The two independent datasets agree.** Wet and dry years line up closely, and both "
        "give the same verdict. This supports the results GeoSleuth shows."
    )
elif correlation >= 0.5:
    st.info(
        "**The two datasets broadly agree** on which years were wet or dry. "
        + ("They also agree on the direction of the trend. " if same_direction
           else "They differ on the direction of the small long-term trend. ")
        + "Small differences are expected, because one is a model and the other is based on "
        "satellite and gauge measurements."
    )
else:
    st.warning(
        "**The two datasets disagree noticeably.** Results for rainfall here should be treated "
        "with care."
    )

st.caption(
    "Sources: NASA POWER (PRECTOTCORR), averaged over four points in Kosovo; GPM IMERG Final "
    "Run monthly precipitation (GPM_3IMERGM v07), area-averaged over Kosovo with NASA Giovanni. "
    "Both analysed with exactly the same GeoSleuth method."
)