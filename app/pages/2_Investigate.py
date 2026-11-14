import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.catalog import load_catalog
from src.data import get_series
from src.sonify import describe_sound, listening_guide, outside_band, sonify
from src.stats import analyze


def format_p(p):
    """Show very small p-values as '< 0.001' instead of '0.000'."""
    return "< 0.001" if p < 0.001 else f"{p:.3f}"


st.title("Investigate")

catalog = load_catalog()
ids = [v["id"] for v in catalog]
default_id = st.session_state.get("variable_id", "t2m")
var = st.selectbox(
    "Variable",
    catalog,
    index=ids.index(default_id) if default_id in ids else 0,
    format_func=lambda v: v["name"],
)
c1, c2 = st.columns(2)
lat = c1.number_input("Latitude", value=st.session_state.get("lat", 42.66), format="%.2f")
lon = c2.number_input("Longitude", value=st.session_state.get("lon", 21.17), format="%.2f")

with st.spinner("Loading NASA data..."):
    series = get_series(var["id"], lat, lon)
r = analyze(series)

st.caption(f"{var['definition']} Source: {var['mission']}.")

# --- Chart: yearly anomalies, trend, natural-variation band, emergence year ---
base = r["trend_line"][0]
band = 2 * r["noise_sigma"]
fig = go.Figure()
fig.add_hrect(
    y0=base - band, y1=base + band, fillcolor="lightgray", opacity=0.35, line_width=0,
    annotation_text="Natural variation (±2σ)", annotation_position="top left",
)
fig.add_trace(go.Scatter(
    x=r["years"], y=r["annual_anomaly"], mode="markers+lines", name="Yearly value",
    line=dict(color="#7aa6d6", width=1), marker=dict(size=8),
))
fig.add_trace(go.Scatter(
    x=r["years"], y=r["trend_line"], mode="lines", name="Trend",
    line=dict(color="#e4572e", width=3),
))
if r["emergence_year"]:
    fig.add_vline(
        x=r["emergence_year"], line_dash="dash", line_color="#e4572e",
        annotation_text=f"Emerged {r['emergence_year']}",
    )
fig.update_layout(
    xaxis_title="Year",
    yaxis_title=f"Difference from average ({var['unit']})",
    height=450, margin=dict(t=30),
)
st.plotly_chart(fig, use_container_width=True)

# --- Text alternative to the chart: the same numbers as a table ---
outside = (outside_band(r["annual_anomaly"], r["trend_line"], r["noise_sigma"])
           or [False] * len(r["years"]))
with st.expander("Show the chart as a table"):
    st.table(pd.DataFrame({
        "Year": [str(y) for y in r["years"]],
        f"Difference from average ({var['unit']})": [f"{v:+.2f}" for v in r["annual_anomaly"]],
        f"Trend ({var['unit']})": [f"{v:+.2f}" for v in r["trend_line"]],
        "Outside natural variation": ["Yes" if o else "No" for o in outside],
    }))

# --- Listen to the trend (guide first, so screen readers read it before the player) ---
st.subheader("Listen to the trend")
st.write(listening_guide(r["years"], r["emergence_year"], has_band=r["noise_sigma"] > 0))
st.audio(
    sonify(r["years"], r["annual_anomaly"], r["emergence_year"], r["trend_line"], r["noise_sigma"]),
    format="audio/wav",
)
st.write(describe_sound(
    r["years"], r["annual_anomaly"], r["emergence_year"], r["trend_line"], r["noise_sigma"],
    unit=var["unit"],
))

# --- Verdict card ---
unit = var["unit"]
slope = r["slope_per_decade"]
lo, hi = r["ci95"]
direction = "rising" if slope > 0 else "falling"

if r["status"] == "emerged":
    st.success(
        f"**Emerged in {r['emergence_year']}.** {var['name']} is {direction}, and the change "
        "is now clearly bigger than normal year-to-year variation."
    )
elif r["status"] == "emerging":
    msg = (f"**Emerging.** {var['name']} seems to be {direction}, but the change is still "
           "inside normal year-to-year variation.")
    if r["projected_year"]:
        msg += f" If the current rate continues, it would stand out around {r['projected_year']}."
    st.warning(msg)
else:
    st.info(f"**No clear signal.** {var['name']} shows no clear long-term change here.")

m1, m2, m3 = st.columns(3)
m1.metric(f"Rate of change ({unit} per decade)", f"{slope:+.2f}")
m2.metric(f"95% range ({unit} per decade)", f"{lo:+.2f} to {hi:+.2f}")
m3.metric("Chance it's random (p)", format_p(r["p_value"]))

# --- Robustness check ---
if r["robust"] is not None:
    years_checked = list(r["robust_statuses"])
    span = f"{years_checked[0]} to {years_checked[-1]}"
    if r["robust"]:
        st.write(
            f"**Robustness check: passed.** The verdict stays the same when the analysis "
            f"starts in any year from {span}."
        )
    else:
        changed = [str(yr) for yr, s in r["robust_statuses"].items() if s != r["status"]]
        st.write(
            f"**Robustness check: not passed.** The verdict changes when the analysis starts "
            f"in {', '.join(changed)}. Treat this result with care."
        )

st.caption(
    "Method: seasons removed, then the Mann–Kendall test with trend-free pre-whitening "
    "(Yue et al., 2002) to account for autocorrelation. 'Emerged' = significant (p < 0.05) "
    "and the trend is more than twice the normal year-to-year variation. Robustness: the "
    "analysis is repeated with start years shifted by up to 5 years."
)