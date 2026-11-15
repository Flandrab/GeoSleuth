import sys
from html import escape
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import folium
import requests
import streamlit as st
from streamlit_folium import st_folium

from src import ui
from src.catalog import load_catalog
from src.geocode import geocode, normalize_lon, reverse_geocode

ui.setup()

QUICK_PICKS = {
    "Prishtina": {"name": "Prishtina, Kosovo", "lat": 42.66, "lon": 21.17},
    "Tirana": {"name": "Tirana, Albania", "lat": 41.33, "lon": 19.82},
    "Rome": {"name": "Rome, Italy", "lat": 41.90, "lon": 12.50},
}
TOPICS = {"Heat": "heat", "Water": "water", "Air": "air"}


def set_place(name, lat, lon):
    st.session_state.update(lat=lat, lon=lon, place_name=name)


def step(number, title):
    ui.html(f'<div class="gs-step"><span class="gs-mono">{number:02d}</span><span>{title}</span></div>')


catalog = load_catalog()

# --- Opening: the question, and the answer for one real place (Prishtina air temperature) ---
try:
    demo = ui.analysis("t2m", 42.66, 21.17)
except Exception:  # no data available: show the opening without the figure
    demo = None

figure, facts = "", ""
if demo:
    years = demo["years"]
    chart = ui.hero_chart(
        years, demo["annual_anomaly"], demo["trend_line"], demo["noise_sigma"], demo["emergence_year"],
        label=(f"Chart of Prishtina air temperature from {years[0]} to {years[-1]}. The yearly values "
               f"rise out of the band of normal variation, and the change stands out from "
               f"{demo['emergence_year']}."),
    )
    figure = (f'<figure>{chart}<figcaption><b>Fig. 1</b>Prishtina, yearly air temperature compared with '
              f'its {years[0]} to {years[-1]} average. The grey band is normal year-to-year variation; '
              f'the trend leaves it in {demo["emergence_year"]}.</figcaption></figure>')
    facts = (f'<div class="gs-facts"><div><b>{len(catalog)}</b>climate variables</div>'
             f'<div><b>{years[0]} to {years[-1]}</b>monthly NASA data</div>'
             f'<div><b>{demo["slope_per_decade"]:+.2f} °C</b>per decade in Prishtina</div></div>')

ui.html(
    '<section class="gs-hero"><div>'
    '<div class="gs-muted">NASA Space Apps Challenge 2026 &middot; Earth System Trend Detective</div>'
    '<h1>When does climate change become <em>undeniable</em> where you live?</h1>'
    '<p>Pick a place. GeoSleuth tests 24 years of NASA data and shows which changes have already '
    'stood out from normal year-to-year variation, when that happened, and which are still hidden.</p>'
    f'{facts}</div>{figure}</section>'
)

st.space("medium")

# --- Start an investigation: place, topics, go ---
left, right = st.columns([1.5, 1], gap="large")

with left:
    step(1, "Choose a place")
    with st.form("search_place", border=False):
        c1, c2 = st.columns([4, 1], vertical_alignment="bottom")
        query = c1.text_input("Search for a city or place", placeholder="Madrid, Nairobi, Lima ...")
        searched = c2.form_submit_button("Search", width="stretch")
    if searched and query.strip():
        try:
            hit = geocode(query.strip())
        except requests.RequestException:
            st.error("Search is not available right now. Click on the map instead.")
        else:
            if hit:
                set_place(*hit)
                st.rerun()
            else:
                st.warning("Place not found. Try another name or click on the map.")

    with st.container(horizontal=True, vertical_alignment="center", gap="small"):
        st.caption("Or try", width="content")
        for label, p in QUICK_PICKS.items():
            if st.button(label, key=f"pick_{label}", type="tertiary"):
                set_place(p["name"], p["lat"], p["lon"])
                st.rerun()

    name, lat, lon = ui.current_place()
    m = folium.Map(location=[lat, lon], zoom_start=6)
    folium.Marker([lat, lon], tooltip=name, icon=folium.Icon(color="darkred", icon="info-sign")).add_to(m)
    ui.quiet_map(m)
    out = st_folium(m, height=380, use_container_width=True, key="map", returned_objects=["last_clicked"])

    # Only react to a NEW click, so a quick pick or search is not undone by an old click
    click = out.get("last_clicked") if out else None
    if click:
        point = (round(click["lat"], 2), normalize_lon(click["lng"]))
        if point != st.session_state.get("home_last_click"):
            st.session_state["home_last_click"] = point
            set_place(reverse_geocode(*point) or ui.coords(*point), *point)
            st.rerun()

with right:
    name, lat, lon = ui.current_place()
    with st.container(key="gs-panel-place"):
        ui.html(f'<div class="gs-label">Selected place</div><div class="gs-place">{escape(name)}</div>'
                f'<div class="gs-muted gs-num">{ui.coords(lat, lon)}</div>')

    st.space("small")
    step(2, "What do you care about?")
    chosen = st.pills("Topics", list(TOPICS), selection_mode="multi", default=["Heat", "Water"],
                      label_visibility="collapsed", key="home_topics")
    picked = [v["name"] for v in catalog if v["topic"] in [TOPICS[c] for c in chosen]]
    if picked:
        st.caption(f"{len(picked)} variables will be tested: {', '.join(picked)}.")
    else:
        st.caption("Pick at least one topic.")

    st.space("small")
    step(3, "Run the scan")
    if st.button("Start investigation", type="primary", width="stretch", disabled=not chosen):
        st.session_state["topics"] = [TOPICS[c] for c in chosen]
        st.switch_page("views/1_Timeline.py")
    st.page_link("views/4_Case_Files.py", label="Or open a ready-made case file")

st.space("large")

# --- How GeoSleuth decides ---
st.subheader("How GeoSleuth decides")
METHOD = [
    ("Remove the seasons",
     "Each month is compared with its own long-term average, so a hot summer never hides a trend."),
    ("Measure normal variation",
     "We measure how far a typical year strays from the trend. That is the grey band on every chart."),
    ("Call it when it stands out",
     "A change has emerged once it is statistically significant (p &lt; 0.05) and larger than twice "
     "normal variation."),
    ("Listen to it",
     "Every trend can be heard: one note per year, louder outside the band, and a bell when it emerges."),
]
ui.html('<div class="gs-method">' + "".join(
    f'<div><span class="gs-mono">{i + 1:02d}</span><h4>{title}</h4><p>{text}</p></div>'
    for i, (title, text) in enumerate(METHOD)
) + "</div>")
st.space("medium")
st.caption("Data: NASA POWER monthly point data, 2001 to 2024. Place search by OpenStreetMap Nominatim.")
