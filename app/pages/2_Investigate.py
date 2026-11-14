import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import plotly.graph_objects as go
import streamlit as st

from src.catalog import load_catalog
from src.data import get_series
from src.stats import analyze

st.title(" Investigate")

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
m1.metric("Rate of change", f"{slope:+.2f} {unit} / decade")
m2.metric("95% range", f"{lo:+.2f} to {hi:+.2f}")
m3.metric("Chance it's random (p)", f"{r['p_value']:.3f}")
st.caption(
    "Method: seasons removed, then Mann–Kendall test with Hamed–Rao correction for "
    "autocorrelation. 'Emerged' = significant (p < 0.05) and the trend is more than "
    "twice the normal year-to-year variation."
)