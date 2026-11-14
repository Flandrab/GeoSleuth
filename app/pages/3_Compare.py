import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import folium
import plotly.graph_objects as go
import requests
import streamlit as st
from streamlit_folium import st_folium

from src.catalog import load_catalog
from src.data import get_series
from src.stats import analyze

USER_AGENT = {"User-Agent": "GeoSleuth (NASA Space Apps 2026)"}

st.title("Compare two places")
st.write(
    "The same kind of change can look very different in two places, "
    "even when the same global process drives both."
)

# --- Default places ---
st.session_state.setdefault("cmp_A", {"name": "Prishtina, Kosovo", "lat": 42.66, "lon": 21.17})
st.session_state.setdefault("cmp_B", {"name": "Tirana, Albania", "lat": 41.33, "lon": 19.82})


@st.cache_data(show_spinner=False)
def geocode(query):
    """Find a place by name with OpenStreetMap Nominatim. Returns (name, lat, lon) or None."""
    r = requests.get(
        "https://nominatim.openstreetmap.org/search",
        params={"q": query, "format": "json", "limit": 1, "accept-language": "en"},
        headers=USER_AGENT,
        timeout=15,
    )
    r.raise_for_status()
    hits = r.json()
    if not hits:
        return None
    h = hits[0]
    parts = [p.strip() for p in h["display_name"].split(",")]
    name = parts[0] if len(parts) == 1 else f"{parts[0]}, {parts[-1]}"
    return name, round(float(h["lat"]), 2), round(float(h["lon"]), 2)


@st.cache_data(show_spinner=False)
def reverse_geocode(lat, lon):
    """Turn coordinates into a readable name, e.g. 'Madrid, Spain'. Returns None if unknown."""
    try:
        r = requests.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={"lat": lat, "lon": lon, "format": "json", "zoom": 10, "accept-language": "en"},
            headers=USER_AGENT,
            timeout=15,
        )
        r.raise_for_status()
        addr = r.json().get("address", {})
    except (requests.RequestException, ValueError):
        return None
    local = (addr.get("city") or addr.get("town") or addr.get("village")
             or addr.get("county") or addr.get("state"))
    parts = [p for p in (local, addr.get("country")) if p]
    return ", ".join(parts) if parts else None


def normalize_lon(lon):
    """Keep longitude between -180 and 180 even if the map was scrolled sideways."""
    return round(((lon + 180) % 360) - 180, 2)


catalog = load_catalog()
var = st.selectbox("Variable", catalog, format_func=lambda v: v["name"])

# --- Choose which place to set ---
target = st.radio("Set which place?", ["Place A", "Place B"], horizontal=True)
key = "cmp_A" if target == "Place A" else "cmp_B"

# --- Search by name ---
s1, s2 = st.columns([4, 1])
query = s1.text_input("Search for a city or place", placeholder="e.g. Madrid, Nairobi, Lima")
if s2.button("Search", use_container_width=True) and query.strip():
    try:
        hit = geocode(query.strip())
    except requests.RequestException:
        hit = None
        st.error("Search is not available right now. Click on the map instead.")
    else:
        if hit:
            name, lat, lon = hit
            st.session_state[key] = {"name": name, "lat": lat, "lon": lon}
        else:
            st.warning("Place not found. Try another name or click on the map.")

# --- Map with both places ---
a = st.session_state["cmp_A"]
b = st.session_state["cmp_B"]
m = folium.Map(location=[(a["lat"] + b["lat"]) / 2, (a["lon"] + b["lon"]) / 2], zoom_start=3)
folium.Marker([a["lat"], a["lon"]], tooltip=f"A: {a['name']}", icon=folium.Icon(color="red")).add_to(m)
folium.Marker([b["lat"], b["lon"]], tooltip=f"B: {b['name']}", icon=folium.Icon(color="blue")).add_to(m)
out = st_folium(m, height=400, width=900, key="cmp_map")

# Only react to a NEW click, so switching between A and B doesn't reuse an old click
click = out.get("last_clicked") if out else None
if click:
    point = (round(click["lat"], 2), normalize_lon(click["lng"]))
    if point != st.session_state.get("cmp_last_click"):
        st.session_state["cmp_last_click"] = point
        name = reverse_geocode(point[0], point[1]) or f"Unnamed area ({point[0]:.2f}, {point[1]:.2f})"
        st.session_state[key] = {"name": name, "lat": point[0], "lon": point[1]}
        st.rerun()

# --- Name boxes for A and B ---
pa, pb = st.columns(2)
with pa:
    with st.container(border=True):
        st.caption("Place A (red marker)")
        st.markdown(f"### {a['name']}")
        st.caption(f"{a['lat']:.2f}, {a['lon']:.2f}")
with pb:
    with st.container(border=True):
        st.caption("Place B (blue marker)")
        st.markdown(f"### {b['name']}")
        st.caption(f"{b['lat']:.2f}, {b['lon']:.2f}")

st.caption("Place search by OpenStreetMap Nominatim. New places download NASA data and can take a few seconds.")

if (a["lat"], a["lon"]) == (b["lat"], b["lon"]):
    st.warning("Pick two different places.")
    st.stop()

# --- Analysis ---
label_a, label_b = f"A: {a['name']}", f"B: {b['name']}"
results = {}
with st.spinner("Loading NASA data..."):
    results[label_a] = analyze(get_series(var["id"], a["lat"], a["lon"]))
    results[label_b] = analyze(get_series(var["id"], b["lat"], b["lon"]))

# --- Chart: both places on the same axes ---
colors = {label_a: "#e4572e", label_b: "#2e86de"}
fig = go.Figure()
for label, r in results.items():
    fig.add_trace(go.Scatter(
        x=r["years"], y=r["annual_anomaly"], mode="markers", name=f"{label} (yearly)",
        marker=dict(color=colors[label], size=7, opacity=0.45),
    ))
    fig.add_trace(go.Scatter(
        x=r["years"], y=r["trend_line"], mode="lines", name=f"{label} (trend)",
        line=dict(color=colors[label], width=3),
    ))
fig.update_layout(
    xaxis_title="Year",
    yaxis_title=f"Difference from average ({var['unit']})",
    height=450, margin=dict(t=30),
)
st.plotly_chart(fig, use_container_width=True)

# --- Side-by-side verdicts ---
LABEL = {
    "emerged": "**Emerged**",
    "emerging": "**Emerging**",
    "no_signal": "**No clear signal**",
}
cols = st.columns(2)
for col, (label, r) in zip(cols, results.items()):
    with col:
        st.subheader(label)
        status = LABEL[r["status"]]
        if r["emergence_year"]:
            status += f" ({r['emergence_year']})"
        elif r["projected_year"]:
            status += f" (likely around {r['projected_year']})"
        st.markdown(status)
        st.metric("Rate of change", f"{r['slope_per_decade']:+.2f} {var['unit']} / decade")
        st.metric("Chance it's random (p)", f"{r['p_value']:.3f}")

# --- Explain what the comparison shows ---
sa = results[label_a]["slope_per_decade"]
sb = results[label_b]["slope_per_decade"]
if sa * sb < 0:
    st.info(
        f"**Opposite directions.** {var['name']} is going up in one place and down in the other. "
        "A warming climate shifts winds, storm tracks and rainfall, so its effects are uneven."
    )
elif results[label_a]["status"] != results[label_b]["status"]:
    st.info(
        "**Same direction, different certainty.** The change is clearer in one place than "
        "the other, because natural year-to-year variation differs from place to place."
    )