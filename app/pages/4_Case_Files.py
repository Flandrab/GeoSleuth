import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))

import streamlit as st

from src.catalog import get_variable
from src.data import get_series
from src.stats import analyze

st.title("Case files")
st.write(
    "Ready-made investigations. Each case is calculated live from NASA data, "
    "and you can open it to explore the full chart."
)

with open(ROOT / "data" / "cases.json", encoding="utf-8") as f:
    cases = json.load(f)


def verdict_text(r):
    if r["status"] == "emerged":
        return f"Emerged around {r['emergence_year']}"
    if r["status"] == "emerging":
        if r["projected_year"]:
            return f"Likely clear around {r['projected_year']}"
        return "Emerging, not yet clear"
    return "No clear signal"


for case in cases:
    var = get_variable(case["variable_id"])
    with st.container(border=True):
        st.subheader(case["title"])
        st.caption(f"Variable: {var['name']}")
        st.write(case["story"])

        if case["type"] == "single":
            p = case["place"]
            with st.spinner("Loading NASA data..."):
                r = analyze(get_series(var["id"], p["lat"], p["lon"]))
            c1, c2, c3 = st.columns(3)
            c1.markdown(f"**Place**  \n{p['name']}")
            c2.markdown(f"**Verdict**  \n{verdict_text(r)}")
            c3.markdown(f"**Rate of change**  \n{r['slope_per_decade']:+.2f} {var['unit']} / decade")
            if st.button("Open this case", key=f"open_{case['id']}"):
                st.session_state.update(
                    lat=p["lat"], lon=p["lon"], place_name=p["name"], variable_id=var["id"]
                )
                st.switch_page("pages/2_Investigate.py")

        elif case["type"] == "compare":
            pa, pb = case["place_a"], case["place_b"]
            cols = st.columns(2)
            for col, p in zip(cols, (pa, pb)):
                with st.spinner("Loading NASA data..."):
                    r = analyze(get_series(var["id"], p["lat"], p["lon"]))
                col.markdown(
                    f"**{p['name']}**  \n{verdict_text(r)}  \n"
                    f"{r['slope_per_decade']:+.2f} {var['unit']} / decade"
                )
            if st.button("Open this comparison", key=f"open_{case['id']}"):
                st.session_state["cmp_A"] = dict(pa)
                st.session_state["cmp_B"] = dict(pb)
                st.session_state["cmp_variable_id"] = var["id"]
                st.switch_page("pages/3_Compare.py")