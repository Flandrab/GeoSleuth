import sys
from pathlib import Path

sys.path.append(str(Path(file).resolve().parents[2]))

import streamlit as st

from src.detect import scan_region

st.title(" Emergence timeline")

lat = st.session_state.get("lat", 42.66)
lon = st.session_state.get("lon", 21.17)
topics = st.session_state.get("topics", ["heat", "water"])
place = st.session_state.get("place_name", f"{lat:.2f}, {lon:.2f}")

st.write(f"Place: {place}  ·  Topics: {', '.join(topics)}")
st.caption("First scan of a new place downloads NASA data for each variable and can take a minute.")

with st.spinner("Scanning NASA data..."):
    results = scan_region(lat, lon, topics)

if not results:
    st.error("No data could be loaded for this place. Try another point.")
    st.stop()

ICON = {"emerged": "✅", "emerging": "⏳", "no_signal": "⚪"}

for row in results:
    if row["status"] == "emerged":
        verdict = f"Emerged around {row['emergence_year']}"
    elif row["status"] == "emerging":
        verdict = (f"Likely clear around {row['projected_year']}"
                   if row["projected_year"] else "Emerging, not yet clear")
    else:
        verdict = "No clear signal"

    c1, c2, c3, c4 = st.columns([3, 3, 2, 1.4])
    c1.markdown(f"{ICON[row['status']]} {row['name']}")
    c2.markdown(verdict)
    c3.markdown(f"{row['slope_perdecade']:+.2f} {row['unit']}/decade")
    if c4.button("Investigate", key=f"inv{row['variable_id']}"):
        st.session_state["variable_id"] = row["variable_id"]
        st.switch_page("pages/2_Investigate.py")

st.caption(
    f"We tested {len(results)} variables and corrected for testing many at once "
    "(Benjamini–Hochberg). 'Likely clear around' assumes the current rate continues."
)