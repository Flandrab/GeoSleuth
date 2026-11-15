import sys
from html import escape
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import plotly.graph_objects as go
import streamlit as st

from src import ui

ui.setup()

name, lat, lon = ui.current_place()
topics = st.session_state.get("topics", ["heat", "water"])

ui.page_header(
    f"What has changed in {escape(name)}?",
    "Every climate variable for this place, tested on 24 years of NASA data. Changes that have "
    "already left normal year-to-year variation are listed first.",
    ui.meta(f"<b>{escape(name)}</b>", ui.coords(lat, lon),
            "Topics: " + ", ".join(t.capitalize() for t in topics)),
)
st.page_link("views/0_Home.py", label="Change place or topics")

with st.spinner("Scanning NASA data. The first scan of a new place can take a minute."):
    results = ui.scan(lat, lon, tuple(topics))

if not results:
    st.error("No data could be loaded for this place. Try another point.")
    st.stop()

# --- The answer in one sentence ---
st.space("medium")
counts = {s: sum(r["status"] == s for r in results) for s in ui.STATUS}
ui.summary(counts)

# --- When did (or will) each change stand out? ---
st.space("medium")
st.subheader("Emergence timeline")
st.caption("Filled dots: the year a change stood out. Open diamonds: the year it would stand out if "
           "the current rate continues.")
last_year = max(r["years"][-1] for r in results)
first_year = min(r["years"][0] for r in results)
future = [r["projected_year"] for r in results if r["projected_year"]]
x_end = max([last_year + 2] + [y + 2 for y in future])
names = [r["name"] for r in results]

fig = go.Figure()
fig.add_vrect(x0=last_year + 0.5, x1=x_end, fillcolor=ui.GRID, opacity=0.7, line_width=0, layer="below",
              annotation_text="projection", annotation_position="top left",
              annotation_font=dict(size=11, color=ui.MUTED))
fig.add_trace(go.Scatter(
    x=sum([[first_year, last_year, None] for _ in results], []),
    y=sum([[n, n, None] for n in names], []),
    mode="lines", line=dict(color=ui.RULE, width=2), hoverinfo="skip", showlegend=False,
))
groups = {
    "emerged": dict(symbol="circle", size=11, color=ui.STATUS["emerged"]["fg"]),
    "emerging": dict(symbol="diamond-open", size=11, color=ui.STATUS["emerging"]["fg"], line=dict(width=2)),
    "no_signal": dict(symbol="line-ew", size=10, color=ui.MUTED, line=dict(width=2, color=ui.MUTED)),
}
for status, marker in groups.items():
    rows = [r for r in results if r["status"] == status]
    if not rows:
        continue
    xs, labels = [], []
    for r in rows:
        if status == "emerged":
            xs.append(r["emergence_year"])
            labels.append(str(r["emergence_year"]))
        elif r["projected_year"]:
            xs.append(r["projected_year"])
            labels.append(f"~{r['projected_year']}")
        else:
            xs.append(last_year)
            labels.append("not yet" if status == "emerging" else "no signal")
    if status == "emerged":
        fig.add_trace(go.Scatter(
            x=sum([[first_year, x, None] for x in xs], []),
            y=sum([[r["name"], r["name"], None] for r in rows], []),
            mode="lines", line=dict(color=ui.STATUS["emerged"]["fg"], width=2), hoverinfo="skip",
            showlegend=False,
        ))
    fig.add_trace(go.Scatter(
        x=xs, y=[r["name"] for r in rows], mode="markers+text", text=labels, textposition="middle right",
        textfont=dict(size=12, color=ui.INK), marker=marker, name=ui.STATUS[status]["label"],
        customdata=[[ui.verdict_text(r), f"{r['slope_per_decade']:+.2f} {r['unit']}"] for r in rows],
        hovertemplate="<b>%{y}</b><br>%{customdata[0]}<br>%{customdata[1]} per decade<extra></extra>",
        showlegend=False,
    ))
fig.update_yaxes(categoryorder="array", categoryarray=names[::-1], showgrid=False, zeroline=False)
fig.update_xaxes(range=[first_year - 0.5, x_end], dtick=5, showgrid=True, gridcolor=ui.GRID)
ui.style_fig(fig, height=70 + 40 * len(results))
fig.update_layout(margin=dict(t=24))
st.plotly_chart(fig, theme=None, config=ui.PLOTLY_CONFIG,
                alt="Emergence timeline chart. The same results are listed as a table below.")

# --- All results as a ruled table ---
st.space("medium")
st.subheader("All results")
WIDTHS = [2.6, 1.6, 1.5, 1.3, 0.9]
with st.container(key="gs-list-results"):
    head = st.columns(WIDTHS, vertical_alignment="bottom")
    for col, text in zip(head, ["Variable", f"{first_year} to {last_year}", "Stands out",
                                "Change per decade", ""]):
        col.html(f'<div class="gs-label">{text}</div>')
    for r in results:
        with st.container(key=f"gs-row-{r['variable_id']}"):
            c1, c2, c3, c4, c5 = st.columns(WIDTHS, vertical_alignment="center")
            c1.html(f'<div style="font-weight:600;margin-bottom:.3rem">{r["name"]}</div>{ui.tag(r["status"])}')
            e_idx = r["years"].index(r["emergence_year"]) if r["emergence_year"] in r["years"] else None
            c2.html(ui.sparkline(r["annual_anomaly"], r["trend_line"], r["noise_sigma"], e_idx))
            if r["status"] == "emerged":
                when, sub = str(r["emergence_year"]), "emerged"
            elif r["projected_year"]:
                when, sub = f"~{r['projected_year']}", "if the rate continues"
            else:
                when, sub = "Not yet", "no clear signal" if r["status"] == "no_signal" else "not yet clear"
            c3.html(f'<div class="gs-num" style="font-weight:600;font-size:1.05rem">{when}</div>'
                    f'<div class="gs-muted">{sub}</div>')
            c4.html(f'<div class="gs-num" style="font-weight:600;font-size:1.05rem">'
                    f'{r["slope_per_decade"]:+.2f}</div><div class="gs-muted">{r["unit"]}</div>')
            if c5.button("Open", key=f"inv_{r['variable_id']}", width="stretch",
                         help=f"Investigate {r['name']}"):
                st.session_state["variable_id"] = r["variable_id"]
                st.switch_page("views/2_Investigate.py")

st.caption(
    f"{len(results)} variables tested, corrected for testing many at once (Benjamini–Hochberg). "
    "Projected years assume the current rate continues."
)
