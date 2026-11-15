import sys
from html import escape
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import folium
import plotly.graph_objects as go
import requests
import streamlit as st
from streamlit_folium import st_folium

from src import ui
from src.catalog import load_catalog
from src.geocode import geocode, normalize_lon, reverse_geocode

ui.setup()

ui.page_header(
    "Compare two places",
    "The same kind of change can look very different in two places, even when the same global "
    "process drives both.",
)

# --- Default places ---
st.session_state.setdefault("cmp_A", {"name": "Prishtina, Kosovo", "lat": 42.66, "lon": 21.17})
st.session_state.setdefault("cmp_B", {"name": "Tirana, Albania", "lat": 41.33, "lon": 19.82})

catalog = load_catalog()
ids = [v["id"] for v in catalog]
default_var = st.session_state.get("cmp_variable_id", "t2m")

# --- Controls: variable, which place to set, search ---
st.space("small")
c1, c2, c3 = st.columns([1.2, 1, 1.6], vertical_alignment="bottom")
var = c1.selectbox(
    "Variable", catalog, index=ids.index(default_var) if default_var in ids else 0,
    format_func=lambda v: v["name"],
)
st.session_state["cmp_variable_id"] = var["id"]
target = c2.segmented_control(
    "Place to set", ["Place A", "Place B"], default="Place A", required=True, key="cmp_target",
)
key = "cmp_A" if target == "Place A" else "cmp_B"
with c3.form("cmp_search", border=False):
    f1, f2 = st.columns([3, 1], vertical_alignment="bottom")
    query = f1.text_input(f"Search for {target}", placeholder="Madrid, Nairobi, Lima ...")
    searched = f2.form_submit_button("Search", width="stretch")
if searched and query.strip():
    try:
        hit = geocode(query.strip())
    except requests.RequestException:
        st.error("Search is not available right now. Click on the map instead.")
    else:
        if hit:
            name, lat, lon = hit
            st.session_state[key] = {"name": name, "lat": lat, "lon": lon}
            st.rerun()
        else:
            st.warning("Place not found. Try another name or click on the map.")

# --- Map with both places ---
a = st.session_state["cmp_A"]
b = st.session_state["cmp_B"]
ui.html(ui.meta(
    f'<b style="color:{ui.PLACE_A}">A</b> {escape(a["name"])}',
    f'<b style="color:{ui.PLACE_B}">B</b> {escape(b["name"])}',
    f"Click the map to move {target}",
))
m = folium.Map(location=[(a["lat"] + b["lat"]) / 2, (a["lon"] + b["lon"]) / 2], zoom_start=3)
folium.Marker([a["lat"], a["lon"]], tooltip=f"A: {a['name']}", icon=folium.Icon(color="red")).add_to(m)
folium.Marker([b["lat"], b["lon"]], tooltip=f"B: {b['name']}", icon=folium.Icon(color="blue")).add_to(m)
# zoom so both places are visible and apart, whether they are neighbours or on two continents
m.fit_bounds([[a["lat"], a["lon"]], [b["lat"], b["lon"]]], padding=(60, 60), max_zoom=7)
ui.quiet_map(m)
out = st_folium(m, height=360, use_container_width=True, key="cmp_map", returned_objects=["last_clicked"])

# Only react to a NEW click, so switching between A and B doesn't reuse an old click
click = out.get("last_clicked") if out else None
if click:
    point = (round(click["lat"], 2), normalize_lon(click["lng"]))
    if point != st.session_state.get("cmp_last_click"):
        st.session_state["cmp_last_click"] = point
        name = reverse_geocode(point[0], point[1]) or f"Unnamed area ({ui.coords(*point)})"
        st.session_state[key] = {"name": name, "lat": point[0], "lon": point[1]}
        st.rerun()

st.caption("Place search by OpenStreetMap Nominatim. New places download NASA data and can take a few seconds.")

if (a["lat"], a["lon"]) == (b["lat"], b["lon"]):
    st.warning("Pick two different places.")
    st.stop()

# --- Analysis ---
places = [("A", a, ui.PLACE_A), ("B", b, ui.PLACE_B)]
results = {}
with st.spinner("Loading NASA data..."):
    for letter, p, _ in places:
        results[letter] = ui.analysis(var["id"], p["lat"], p["lon"])

# --- Side-by-side verdicts (answer first) ---
st.space("medium")
cols = st.columns(2, gap="large")
for col, (letter, p, color) in zip(cols, places):
    r = results[letter]
    col.html(
        f'<div class="gs-place-col" style="--c:{color}">'
        f'<div class="gs-label" style="color:{color}">Place {letter}</div>'
        f'<div class="gs-place">{escape(p["name"])}</div>'
        f'<div class="gs-muted gs-num">{ui.coords(p["lat"], p["lon"])}</div>'
        f'<div style="margin:.75rem 0 .9rem 0">{ui.tag(r["status"], ui.verdict_text(r))}</div>'
        f'<div style="display:flex;gap:2.5rem;flex-wrap:wrap">'
        f'<div><div class="gs-label">Change per decade</div><div class="gs-num" style="font-size:1.3rem;'
        f'font-weight:600">{r["slope_per_decade"]:+.2f} <span class="gs-muted">{var["unit"]}</span></div></div>'
        f'<div><div class="gs-label">Chance it\'s random (p)</div><div class="gs-num" style="font-size:1.3rem;'
        f'font-weight:600">{ui.format_p(r["p_value"])}</div></div></div></div>'
    )

# --- Explain what the comparison shows ---
sa = results["A"]["slope_per_decade"]
sb = results["B"]["slope_per_decade"]
note = None
if sa * sb < 0:
    note = (f"**Opposite directions.** {var['name']} is going up in one place and down in the other. "
            "A warming climate shifts winds, storm tracks and rainfall, so its effects are uneven.")
elif results["A"]["status"] != results["B"]["status"]:
    note = ("**Same direction, different certainty.** The change is clearer in one place than "
            "the other, because natural year-to-year variation differs from place to place.")
if note:
    st.space("small")
    st.markdown(note)

# --- Chart: both places on the same axes ---
st.space("small")
fig = go.Figure()
for letter, p, color in places:
    r = results[letter]
    label = f"{letter}: {p['name']}"
    fig.add_trace(go.Scatter(
        x=r["years"], y=r["annual_anomaly"], mode="markers", name=f"{label}, yearly",
        marker=dict(color=color, size=6, opacity=0.4),
        hovertemplate=f"{escape(p['name'])} %{{x}}: %{{y:+.2f}} {var['unit']}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=r["years"], y=r["trend_line"], mode="lines", name=f"{label}, trend",
        line=dict(color=color, width=2.5), hoverinfo="skip",
    ))
fig.update_layout(xaxis_title="Year", yaxis_title=f"Difference from average ({var['unit']})")
ui.style_fig(fig, height=430)
st.plotly_chart(fig, theme=None, config=ui.PLOTLY_CONFIG,
                alt=f"Chart comparing {var['name']} in {a['name']} and {b['name']}. "
                    "The verdicts are written out above.")
