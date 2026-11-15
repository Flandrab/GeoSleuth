import json
import sys
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))

import streamlit as st

from src import ui
from src.catalog import get_variable

ui.setup()

ui.page_header(
    "Case files",
    "Ready-made investigations, calculated live from NASA data. Open one to explore the full chart "
    "and listen to the trend.",
)

with open(ROOT / "data" / "cases.json", encoding="utf-8") as f:
    cases = json.load(f)


def place_result(p, r, var, color=None):
    """One place inside a case: name, verdict tag, small chart, rate of change."""
    e_idx = r["years"].index(r["emergence_year"]) if r["emergence_year"] in r["years"] else None
    marker = (f'<span style="display:inline-block;width:.55rem;height:.55rem;background:{color};'
              f'margin-right:.45rem"></span>') if color else ""
    return (
        f'<div style="display:flex;align-items:center;justify-content:space-between;gap:1rem;'
        f'flex-wrap:wrap;padding:.75rem 0;border-top:1px solid {ui.RULE}">'
        f'<div><div style="font-weight:600;margin-bottom:.3rem">{marker}{escape(p["name"])}</div>'
        f'{ui.tag(r["status"], ui.verdict_text(r))}</div>'
        f'<div style="display:flex;align-items:center;gap:1.1rem">'
        f'{ui.sparkline(r["annual_anomaly"], r["trend_line"], r["noise_sigma"], e_idx, width=120, height=34)}'
        f'<div style="text-align:right;min-width:5rem"><div class="gs-num" style="font-weight:600">'
        f'{r["slope_per_decade"]:+.2f}</div><div class="gs-muted">{var["unit"]} / decade</div></div>'
        f'</div></div>'
    )


st.space("medium")
cols = st.columns(2, gap="medium")
for i, case in enumerate(cases):
    var = get_variable(case["variable_id"])
    kind = "Comparison" if case["type"] == "compare" else "Single place"
    with cols[i % 2], st.container(key=f"gs-panel-case-{case['id']}"):
        ui.html(ui.meta(kind, var["name"], top=True))
        st.subheader(case["title"], anchor=False)
        st.write(case["story"])

        if case["type"] == "single":
            p = case["place"]
            with st.spinner("Loading NASA data..."):
                r = ui.analysis(var["id"], p["lat"], p["lon"])
            ui.html(place_result(p, r, var))
            if st.button("Open this case", key=f"open_{case['id']}", width="stretch"):
                st.session_state.update(
                    lat=p["lat"], lon=p["lon"], place_name=p["name"], variable_id=var["id"]
                )
                st.switch_page("views/2_Investigate.py")

        elif case["type"] == "compare":
            pa, pb = case["place_a"], case["place_b"]
            rows = []
            for p, color in ((pa, ui.PLACE_A), (pb, ui.PLACE_B)):
                with st.spinner("Loading NASA data..."):
                    r = ui.analysis(var["id"], p["lat"], p["lon"])
                rows.append(place_result(p, r, var, color))
            ui.html("".join(rows))
            if st.button("Open this comparison", key=f"open_{case['id']}", width="stretch"):
                st.session_state["cmp_A"] = dict(pa)
                st.session_state["cmp_B"] = dict(pb)
                st.session_state["cmp_variable_id"] = var["id"]
                st.switch_page("views/3_Compare.py")
