import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import plotly.graph_objects as go
import streamlit as st

from src.catalog import load_catalog
from src.data import get_series
from src.stats import analyze

st.title("⚖️ Compare two places")
st.write(
    "The same kind of change can look very different in two places, "
    "even when the same global process drives both."
)

PLACES = {
    "Prishtina": (42.66, 21.17),
    "Tirana": (41.33, 19.82),
    "Skopje": (42.00, 21.43),
    "Athens": (37.98, 23.73),
    "Rome": (41.90, 12.50),
    "Vienna": (48.21, 16.37),
}

catalog = load_catalog()
var = st.selectbox("Variable", catalog, format_func=lambda v: v["name"])

names = list(PLACES)
c1, c2 = st.columns(2)
a = c1.selectbox("Place A", names, index=0)
b = c2.selectbox("Place B", names, index=1)

if a == b:
    st.warning("Pick two different places.")
    st.stop()

results = {}
with st.spinner("Loading NASA data..."):
    for name in (a, b):
        lat, lon = PLACES[name]
        results[name] = analyze(get_series(var["id"], lat, lon))

# --- Chart: both places on the same axes ---
colors = {a: "#e4572e", b: "#2e86de"}
fig = go.Figure()
for name, r in results.items():
    fig.add_trace(go.Scatter(
        x=r["years"], y=r["annual_anomaly"], mode="markers", name=f"{name}: yearly",
        marker=dict(color=colors[name], size=7, opacity=0.45),
    ))
    fig.add_trace(go.Scatter(
        x=r["years"], y=r["trend_line"], mode="lines", name=f"{name}: trend",
        line=dict(color=colors[name], width=3),
    ))
fig.update_layout(
    xaxis_title="Year",
    yaxis_title=f"Difference from average ({var['unit']})",
    height=450, margin=dict(t=30),
)
st.plotly_chart(fig, use_container_width=True)

# --- Side-by-side verdicts ---
LABEL = {"emerged": " Emerged", "emerging": " Emerging", "no_signal": " No clear signal"}
cols = st.columns(2)
for col, (name, r) in zip(cols, results.items()):
    with col:
        st.subheader(name)
        status = LABEL[r["status"]]
        if r["emergence_year"]:
            status += f" ({r['emergence_year']})"
        elif r["projected_year"]:
            status += f" (likely around {r['projected_year']})"
        st.markdown(f"**{status}**")
        st.metric("Rate of change", f"{r['slope_per_decade']:+.2f} {var['unit']} / decade")
        st.metric("Chance it's random (p)", f"{r['p_value']:.3f}")

# --- Explain what the comparison shows ---
sa, sb = results[a]["slope_per_decade"], results[b]["slope_per_decade"]
if sa * sb < 0:
    st.info(
        f"**Opposite directions.** {var['name']} is going up in one place and down in the other. "
        "A warming climate shifts winds, storm tracks and rainfall, so its effects are uneven."
    )
elif results[a]["status"] != results[b]["status"]:
    st.info(
        "**Same direction, different certainty.** The change is clearer in one place than "
        "the other, because natural year-to-year variation differs from place to place."
    )