import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import folium
import streamlit as st
from streamlit_folium import st_folium

st.set_page_config(page_title="GeoSleuth", layout="wide")
st.title("GeoSleuth")
st.subheader("When does climate change become undeniable where you live?")
st.write(
    "Pick a place, and GeoSleuth scans 24 years of NASA data to show which changes have "
    "already stood out from normal year-to-year variation, and which are still hidden."
)

# --- quick picks ---
PLACES = {"Prishtina": (42.66, 21.17), "Tirana": (41.33, 19.82)}
cols = st.columns(len(PLACES) + 1)
for col, (name, (plat, plon)) in zip(cols, PLACES.items()):
    if col.button(name):
        st.session_state.update(lat=plat, lon=plon, place_name=name)

# --- map ---
lat = st.session_state.get("lat", 42.66)
lon = st.session_state.get("lon", 21.17)
m = folium.Map(location=[lat, lon], zoom_start=6)
folium.Marker([lat, lon], tooltip="Selected place").add_to(m)
out = st_folium(m, height=420, width=900, key="map")

if out and out.get("last_clicked"):
    new_lat = round(out["last_clicked"]["lat"], 2)
    new_lon = round(out["last_clicked"]["lng"], 2)
    if (new_lat, new_lon) != (lat, lon):
        st.session_state.update(lat=new_lat, lon=new_lon,
                                place_name=f"{new_lat:.2f}, {new_lon:.2f}")
        st.rerun()

st.write(f"**Selected:** {st.session_state.get('place_name', 'Prishtina')} "
         f"({st.session_state.get('lat', lat):.2f}, {st.session_state.get('lon', lon):.2f})")

# --- topics ---
TOPICS = {"Heat": "heat", "Water": "water", "Air": "air"}
chosen = st.multiselect("What do you care about?", list(TOPICS), default=["Heat", "Water"])

if st.button("Start investigation", type="primary", disabled=not chosen):
    st.session_state["topics"] = [TOPICS[c] for c in chosen]
    st.switch_page("pages/1_Timeline.py")