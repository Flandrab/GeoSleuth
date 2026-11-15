import sys
from html import escape
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src import ui
from src.catalog import load_catalog
from src.geocode import reverse_geocode
from src.sonify import describe_sound, listening_guide, outside_band, sonify

ui.setup()

header = st.container()  # filled in once the variable is known

# --- Controls: variable and place ---
catalog = load_catalog()
ids = [v["id"] for v in catalog]
default_id = st.session_state.get("variable_id", "t2m")
name, lat, lon = ui.current_place()

with st.container(horizontal=True, vertical_alignment="bottom"):
    var = st.selectbox(
        "Variable", catalog, index=ids.index(default_id) if default_id in ids else 0,
        format_func=lambda v: v["name"], width=320,
    )
    with st.popover("Change place"):
        with st.form("place_form", border=False):
            new_lat = st.number_input("Latitude", value=float(lat), min_value=-90.0, max_value=90.0,
                                      format="%.2f")
            new_lon = st.number_input("Longitude", value=float(lon), min_value=-180.0, max_value=180.0,
                                      format="%.2f")
            if st.form_submit_button("Apply", type="primary"):
                p = (round(new_lat, 2), round(new_lon, 2))
                st.session_state.update(lat=p[0], lon=p[1], place_name=reverse_geocode(*p) or ui.coords(*p))
                st.rerun()
        st.page_link("views/0_Home.py", label="Or pick it on the map")
    st.page_link("views/1_Timeline.py", label="All results for this place")
st.session_state["variable_id"] = var["id"]

with header:
    ui.page_header(
        f"{var['name']} in {escape(name)}",
        f"{var['definition']} {var['why_it_matters']}",
        ui.meta(ui.coords(lat, lon), f"Source: {var['mission']}"),
    )
    st.space("small")

with st.spinner("Loading NASA data..."):
    r = ui.analysis(var["id"], lat, lon)

unit = var["unit"]
slope = r["slope_per_decade"]
lo, hi = r["ci95"]
direction = "rising" if slope > 0 else "falling"
s = ui.STATUS[r["status"]]

# --- Verdict first ---
if r["status"] == "emerged":
    title = f"The change stood out in {r['emergence_year']}."
    body = (f"{var['name']} is {direction}, and the change is now clearly bigger than normal "
            "year-to-year variation.")
    big, cap = str(r["emergence_year"]), "year of emergence"
elif r["status"] == "emerging":
    title = "Changing, but still hidden in the noise."
    body = (f"{var['name']} seems to be {direction}, but the change is still inside normal "
            "year-to-year variation.")
    if r["projected_year"]:
        body += f" If the current rate continues, it would stand out around {r['projected_year']}."
        big, cap = f"~{r['projected_year']}", "projected emergence"
    else:
        big, cap = None, None
else:
    title = "No clear long-term change."
    body = f"{var['name']} shows no change here that stands out from normal year-to-year variation."
    big, cap = None, None

st.space("small")
ui.statement(ui.tag(r["status"]), title, body, big, cap, color=s["fg"])

st.space("small")
with st.container(key="gs-metrics"):
    m1, m2, m3, m4 = st.columns(4)
    m1.metric(f"Change per decade ({unit})", f"{slope:+.2f}",
              help="How much the value changes every ten years (Sen's slope, which is not thrown off by "
                   "a single unusual year).")
    m2.metric(f"95% range ({unit} / decade)", f"{lo:+.2f} to {hi:+.2f}",
              help="The rate is very likely somewhere in this range. If the range includes zero, there "
                   "may be no real change.")
    m3.metric("Chance it's random (p)", ui.format_p(r["p_value"]),
              help="How likely a trend this strong would appear by chance if nothing were really "
                   "changing. Below 0.05 counts as significant.")
    m4.metric(f"Normal variation ({unit})", f"±{2 * r['noise_sigma']:.2f}",
              help="How far a normal year can stray from the trend (2 standard deviations). "
                   "This is the grey band on the chart.")

# --- Chart: yearly values, natural-variation band, trend, emergence year ---
outside = (outside_band(r["annual_anomaly"], r["trend_line"], r["noise_sigma"])
           or [False] * len(r["years"]))
base = r["trend_line"][0]
band = 2 * r["noise_sigma"]
fig = go.Figure()
fig.add_hrect(
    y0=base - band, y1=base + band, fillcolor=ui.BAND, opacity=0.7, line_width=0, layer="below",
    annotation_text="normal year-to-year variation (±2σ)", annotation_position="bottom left",
    annotation_font=dict(size=11, color=ui.MUTED),
)
fig.add_trace(go.Scatter(
    x=r["years"], y=r["annual_anomaly"], mode="lines", line=dict(color=ui.YEARLY, width=1.2),
    hoverinfo="skip", showlegend=False,
))
for is_out, label, color, size in ((False, "Year inside normal variation", ui.YEARLY, 7),
                                    (True, "Year outside normal variation", ui.YEARLY_DARK, 8)):
    xs = [y for y, o in zip(r["years"], outside) if o == is_out]
    ys = [v for v, o in zip(r["annual_anomaly"], outside) if o == is_out]
    if xs:
        fig.add_trace(go.Scatter(
            x=xs, y=ys, mode="markers", name=label, marker=dict(color=color, size=size),
            hovertemplate=f"%{{x}}: %{{y:+.2f}} {unit}<extra></extra>",
        ))
fig.add_trace(go.Scatter(
    x=r["years"], y=r["trend_line"], mode="lines", name="Trend",
    line=dict(color=ui.SIGNAL, width=2.5), hovertemplate=f"Trend %{{x}}: %{{y:+.2f}} {unit}<extra></extra>",
))
if r["emergence_year"]:
    fig.add_vline(x=r["emergence_year"], line_dash="dot", line_color=ui.INK, line_width=1)
    fig.add_annotation(x=r["emergence_year"], y=1, yref="paper", xanchor="left", yanchor="top", xshift=6,
                       text=f"<b>{r['emergence_year']}</b>  change stands out", showarrow=False,
                       font=dict(color=ui.INK, size=12))
fig.update_layout(xaxis_title="Year", yaxis_title=f"Difference from average ({unit})")
ui.style_fig(fig, height=440)

description = describe_sound(r["years"], r["annual_anomaly"], r["emergence_year"], r["trend_line"],
                             r["noise_sigma"], unit=unit)
st.plotly_chart(fig, theme=None, config=ui.PLOTLY_CONFIG, alt=f"Chart of yearly values. {description}")
# Text alternative to the chart: the same numbers as a table
with st.expander("Show the chart as a table"):
    st.table(pd.DataFrame({
        "Year": [str(y) for y in r["years"]],
        f"Difference from average ({unit})": [f"{v:+.2f}" for v in r["annual_anomaly"]],
        f"Trend ({unit})": [f"{v:+.2f}" for v in r["trend_line"]],
        "Outside natural variation": ["Yes" if o else "No" for o in outside],
    }))

# --- Listen to the trend (guide first, so screen readers read it before the player) ---
st.space("medium")
with st.container(key="gs-panel-listen"):
    st.subheader("Listen to the trend", anchor="listen")
    st.write(listening_guide(r["years"], r["emergence_year"], has_band=r["noise_sigma"] > 0))
    st.audio(
        sonify(r["years"], r["annual_anomaly"], r["emergence_year"], r["trend_line"], r["noise_sigma"]),
        format="audio/wav",
    )
    st.write(description)

# --- How the verdict was made ---
st.space("medium")
st.subheader("How this verdict was made")
if r["robust"] is not None:
    years_checked = list(r["robust_statuses"])
    span = f"{years_checked[0]} to {years_checked[-1]}"
    if r["robust"]:
        st.markdown(f"**Robustness check: passed.** The verdict stays the same when the analysis "
                    f"starts in any year from {span}.")
    else:
        changed = [str(yr) for yr, st_ in r["robust_statuses"].items() if st_ != r["status"]]
        st.markdown(f"**Robustness check: not passed.** The verdict changes when the analysis starts "
                    f"in {', '.join(changed)}. Treat this result with care.")
st.markdown(
    "1. **Seasons removed.** Each month is compared with its own average, then averaged to one value per year.\n"
    "2. **Trend.** Sen's slope gives the rate of change; an ordinary regression gives the 95% range.\n"
    "3. **Significance.** The Mann–Kendall test with trend-free pre-whitening (Yue et al., 2002) "
    "accounts for autocorrelation.\n"
    "4. **Emerged** means significant (p < 0.05) **and** the trend is more than twice the normal "
    "year-to-year variation.\n"
    "5. **Robustness.** The analysis is repeated with start years shifted by up to 5 years."
)
