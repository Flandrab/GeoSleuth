"""Shared look and feel for every GeoSleuth page: colours, type, headers, tags, small charts."""
import base64
from html import escape

import streamlit as st

# --- Colours: ink on paper, one accent. Each colour has one meaning everywhere. ---
INK = "#1B1F24"
MUTED = "#5E5A52"
RULE = "#D9D5CB"
BORDER = "#E2DFD6"
GRID = "#ECE9E1"
BAND = "#E6E2D8"          # natural-variation band
SIGNAL = "#C2461E"        # trends and "emerged"
YEARLY = "#8BA3BF"        # yearly values (the noise)
YEARLY_DARK = "#2D4A6B"   # yearly values outside natural variation
PLACE_A = "#C2461E"
PLACE_B = "#2D6CA8"

STATUS = {
    "emerged": {"label": "Emerged", "fg": "#A63A17", "bg": "#F6E5DD"},
    "emerging": {"label": "Emerging", "fg": "#855700", "bg": "#F5EAD2"},
    "no_signal": {"label": "No clear signal", "fg": "#5E5A52", "bg": "#ECEAE4"},
}

DEFAULT_PLACE = {"name": "Prishtina, Kosovo", "lat": 42.66, "lon": 21.17}

CSS = """
<style>
:root { --ink:#1B1F24; --muted:#5E5A52; --rule:#D9D5CB; --border:#E2DFD6; --signal:#C2461E;
  --serif:"Source Serif 4", Georgia, serif; --mono:"IBM Plex Mono", ui-monospace, monospace; }
[data-testid="stMainBlockContainer"] { padding-top: 4.5rem; padding-bottom: 4rem; max-width: 1160px; }
.gs-num, [data-testid="stMetricValue"], table { font-variant-numeric: tabular-nums; }
[data-testid="stMainBlockContainer"] h1, [data-testid="stMainBlockContainer"] h2,
[data-testid="stMainBlockContainer"] h3 { font-family: var(--serif); font-weight: 600; letter-spacing: -.005em; }

/* Page header */
.gs-title { font-family: var(--serif); font-weight: 600; font-size: clamp(1.9rem, 3vw, 2.5rem);
  line-height: 1.12; letter-spacing: -.012em; color: var(--ink); margin: 0 0 .55rem 0; }
.gs-lead { font-size: 1.05rem; line-height: 1.6; color: var(--muted); max-width: 44rem; margin: 0; }
.gs-meta { font-size: .86rem; color: var(--muted); margin-top: .8rem; }
.gs-meta b { color: var(--ink); font-weight: 600; }
.gs-meta .sep { margin: 0 .5rem; color: var(--rule); }

/* Small labels */
.gs-label { font-size: .74rem; letter-spacing: .06em; text-transform: uppercase; color: var(--muted); font-weight: 500; }
.gs-mono { font-family: var(--mono); font-size: .8rem; color: var(--muted); }
.gs-muted { color: var(--muted); font-size: .88rem; }

/* Status tag: colour + words, never colour alone */
.gs-tag { display: inline-flex; align-items: center; gap: .4rem; padding: .12rem .45rem; border-radius: 3px;
  font-size: .78rem; font-weight: 500; white-space: nowrap; }
.gs-tag i { width: .45rem; height: .45rem; background: currentColor; display: inline-block; }

/* Statement block (verdicts and conclusions) */
.gs-statement { display: grid; grid-template-columns: 1fr auto; gap: 1.5rem; align-items: end;
  border-top: 2px solid var(--ink); border-bottom: 1px solid var(--rule); padding: 1.1rem 0 1.25rem 0; }
.gs-statement h2 { font-family: var(--serif); font-weight: 600; font-size: clamp(1.5rem, 2.4vw, 1.95rem);
  line-height: 1.2; margin: .55rem 0 .35rem 0; padding: 0; color: var(--ink); }
.gs-statement p { margin: 0; color: var(--muted); line-height: 1.55; max-width: 44rem; }
.gs-statement .big { font-family: var(--serif); font-size: 2.9rem; font-weight: 600; line-height: 1; text-align: right; }
.gs-statement .cap { font-size: .8rem; color: var(--muted); text-align: right; margin-top: .3rem; }
@media (max-width: 640px) { .gs-statement { grid-template-columns: 1fr; } .gs-statement .big,
  .gs-statement .cap { text-align: left; } }

/* Summary sentence + proportion bar (Trend scanner) */
.gs-summary h2 { font-family: var(--serif); font-weight: 600; font-size: 1.55rem; margin: 0 0 .8rem 0; padding: 0;
  color: var(--ink); line-height: 1.3; }
.gs-bar { display: flex; height: 6px; gap: 2px; max-width: 34rem; }
.gs-bar span { display: block; height: 100%; }
.gs-legend { display: flex; flex-wrap: wrap; gap: 1.4rem; margin-top: .6rem; font-size: .86rem; color: var(--muted); }
.gs-legend b { color: var(--ink); font-weight: 600; margin-right: .25rem; }

/* Rule-separated rows (lists) and flat panels */
[class*="st-key-gs-list"] { border-bottom: 1px solid var(--rule); gap: 0; }
[class*="st-key-gs-row"] { border-top: 1px solid var(--rule); padding: .85rem 0; }
[class*="st-key-gs-panel"], .gs-panel { background: #fff; border: 1px solid var(--border); border-radius: 6px;
  padding: 1.15rem 1.35rem; }
[class*="st-key-gs-metrics"] { border-bottom: 1px solid var(--rule); padding: .2rem 0 .7rem 0; }

/* Home */
.gs-hero { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 3.5rem; align-items: center;
  padding: 1rem 0 2.5rem 0; border-bottom: 1px solid var(--rule); }
.gs-hero h1 { font-family: var(--serif); font-weight: 600; font-size: clamp(2.2rem, 4.2vw, 3.35rem); line-height: 1.06;
  letter-spacing: -.02em; margin: .7rem 0 1.1rem 0; padding: 0; color: var(--ink); }
.gs-hero h1 em { font-style: italic; color: var(--signal); }
.gs-hero p { font-size: 1.08rem; line-height: 1.62; color: var(--muted); margin: 0; max-width: 31rem; }
.gs-facts { display: flex; gap: 2.4rem; margin-top: 1.8rem; padding-top: 1rem; border-top: 1px solid var(--rule); }
.gs-facts div { font-size: .82rem; color: var(--muted); }
.gs-facts b { display: block; font-family: var(--serif); font-size: 1.55rem; font-weight: 600; color: var(--ink);
  font-variant-numeric: tabular-nums; }
.gs-hero figure { margin: 0; }
.gs-hero figcaption { font-size: .82rem; line-height: 1.5; color: var(--muted); margin-top: .7rem;
  padding-top: .6rem; border-top: 1px solid var(--rule); }
.gs-hero figcaption b { color: var(--ink); font-weight: 600; margin-right: .35rem; }
@media (max-width: 860px) { .gs-hero { grid-template-columns: 1fr; gap: 2rem; } .gs-facts { gap: 1.5rem; flex-wrap: wrap; } }

.gs-step { display: flex; align-items: baseline; gap: .7rem; margin: .2rem 0 .7rem 0; }
.gs-step .gs-mono { font-size: .82rem; }
.gs-step span:last-child { font-family: var(--serif); font-weight: 600; font-size: 1.2rem; color: var(--ink); }
.gs-place { font-family: var(--serif); font-weight: 600; font-size: 1.45rem; line-height: 1.2; color: var(--ink); margin: .2rem 0; }

.gs-method { display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 1.6rem; }
.gs-method div { border-top: 1px solid var(--ink); padding-top: .7rem; }
.gs-method h4 { font-size: 1rem; font-weight: 600; margin: .35rem 0 .3rem 0; padding: 0; color: var(--ink); }
.gs-method p { margin: 0; font-size: .92rem; line-height: 1.55; color: var(--muted); }

.gs-place-col { border-top: 3px solid var(--c); padding-top: .75rem; }
</style>
"""


def setup():
    """Call once at the top of every page: loads the shared styles."""
    st.html(CSS)


@st.cache_data(show_spinner=False)
def analysis(variable_id, lat, lon):
    """analyze() for one variable and place, remembered so revisiting a page is instant."""
    from src.data import get_series
    from src.stats import analyze
    return analyze(get_series(variable_id, lat, lon))


@st.cache_data(show_spinner=False)
def scan(lat, lon, topics):
    """scan_region(), remembered so going back to the Trend scanner is instant."""
    from src.detect import scan_region
    return scan_region(lat, lon, list(topics))


def html(body):
    st.html(body)


def coords(lat, lon):
    """42.66, 21.17 -> '42.66° N, 21.17° E'."""
    return f"{abs(lat):.2f}° {'N' if lat >= 0 else 'S'}, {abs(lon):.2f}° {'E' if lon >= 0 else 'W'}"


def meta(*parts, top=False):
    """A quiet line of facts separated by dots. Parts may contain simple HTML.
    top=True drops the space above it (when it opens a panel)."""
    sep = '<span class="sep">·</span>'
    style = ' style="margin-top:0"' if top else ""
    return f'<div class="gs-meta"{style}>{sep.join(p for p in parts if p)}</div>'


def page_header(title, lead=None, meta_html=""):
    lead_html = f'<p class="gs-lead">{lead}</p>' if lead else ""
    st.html(f'<header><h1 class="gs-title">{title}</h1>{lead_html}{meta_html}</header>')


def current_place():
    """The place chosen anywhere in the app (name, lat, lon), with Prishtina as default."""
    s = st.session_state
    lat, lon = s.get("lat", DEFAULT_PLACE["lat"]), s.get("lon", DEFAULT_PLACE["lon"])
    name = s.get("place_name")
    if not name:
        is_default = (lat, lon) == (DEFAULT_PLACE["lat"], DEFAULT_PLACE["lon"])
        name = DEFAULT_PLACE["name"] if is_default else coords(lat, lon)
    return name, lat, lon


def tag(status, text=None):
    s = STATUS[status]
    label = escape(text) if text else s["label"]
    return f'<span class="gs-tag" style="color:{s["fg"]};background:{s["bg"]}"><i></i>{label}</span>'


def statement(label, title, body, big=None, cap=None, color=INK):
    """Answer-first block: small label, one-line statement, explanation, optional key number."""
    side = (f'<div><div class="big gs-num" style="color:{color}">{big}</div>'
            f'<div class="cap">{cap or ""}</div></div>') if big else "<div></div>"
    st.html(f'<section class="gs-statement"><div>{label}<h2>{title}</h2><p>{body}</p></div>{side}</section>')


def verdict_text(r):
    """One short line for a result from analyze() or scan_region()."""
    if r["status"] == "emerged":
        return f"Emerged around {r['emergence_year']}"
    if r["status"] == "emerging":
        if r.get("projected_year"):
            return f"Likely clear around {r['projected_year']}"
        return "Emerging, not yet clear"
    return "No clear signal"


def format_p(p):
    """Show very small p-values as '< 0.001' instead of '0.000'."""
    return "< 0.001" if p < 0.001 else f"{p:.3f}"


def summary(counts):
    """One sentence plus a proportion bar: how many changes have emerged here."""
    total = sum(counts.values())
    n = counts["emerged"]
    if n == 0:
        sentence = f"None of the {total} changes tested here has clearly emerged yet."
    elif n == 1:
        sentence = f"1 of the {total} changes tested here has already emerged."
    else:
        sentence = f"{n} of the {total} changes tested here have already emerged."
    bar = "".join(f'<span style="flex:{counts[s]};background:{STATUS[s]["fg"]}"></span>'
                  for s in STATUS if counts[s])
    legend = "".join(f'<span><b class="gs-num">{counts[s]}</b>{STATUS[s]["label"].lower()}</span>'
                     for s in STATUS)
    st.html(f'<div class="gs-summary"><h2>{sentence}</h2><div class="gs-bar" aria-hidden="true">{bar}</div>'
            f'<div class="gs-legend">{legend}</div></div>')


# --- Small charts as SVG ---
# Streamlit's HTML sanitizer removes inline <svg>, so charts are embedded as images.
def svg_img(svg, alt="", style="display:block;max-width:100%"):
    data = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f'<img src="data:image/svg+xml;base64,{data}" alt="{escape(alt)}" style="{style}">'


def _scaler(lo, hi, size, pad, invert=False):
    span = (hi - lo) or 1.0

    def f(v):
        frac = (v - lo) / span
        return pad + (1 - frac if invert else frac) * (size - 2 * pad)
    return f


def sparkline(values, trend=None, sigma=None, emergence_index=None, width=150, height=36):
    """Tiny chart: natural-variation band, yearly line, trend line, emergence tick."""
    v = [float(x) for x in values]
    if len(v) < 2:
        return ""
    lows, highs = [min(v)], [max(v)]
    if trend is not None:
        lows.append(min(trend))
        highs.append(max(trend))
    base = trend[0] if trend is not None else None
    if sigma and base is not None:
        lows.append(base - 2 * sigma)
        highs.append(base + 2 * sigma)
    fx = _scaler(0, len(v) - 1, width, 2)
    fy = _scaler(min(lows), max(highs), height, 3, invert=True)
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">']
    if sigma and base is not None:
        y1, y2 = fy(base + 2 * sigma), fy(base - 2 * sigma)
        p.append(f'<rect x="0" y="{y1:.1f}" width="{width}" height="{y2 - y1:.1f}" fill="{BAND}"/>')
    pts = " ".join(f"{fx(i):.1f},{fy(y):.1f}" for i, y in enumerate(v))
    p.append(f'<polyline points="{pts}" fill="none" stroke="{YEARLY}" stroke-width="1.2" stroke-linejoin="round"/>')
    if trend is not None:
        p.append(f'<line x1="{fx(0):.1f}" y1="{fy(trend[0]):.1f}" x2="{fx(len(v) - 1):.1f}" '
                 f'y2="{fy(trend[-1]):.1f}" stroke="{SIGNAL}" stroke-width="1.8"/>')
    if emergence_index is not None:
        ex = fx(emergence_index)
        p.append(f'<line x1="{ex:.1f}" y1="0" x2="{ex:.1f}" y2="{height}" stroke="{INK}" '
                 f'stroke-width="1" stroke-dasharray="2 2"/>')
    p.append("</svg>")
    return svg_img("".join(p), alt="", style=f"display:block;max-width:100%;width:{width}px")


def hero_chart(years, values, trend, sigma, emergence_year, label):
    """Home page figure (real data). The yearly line and trend draw in once; nothing loops."""
    w, h, padx, pady = 560, 320, 30, 30
    base = trend[0]
    lo = min(min(values), min(trend), base - 2 * sigma)
    hi = max(max(values), max(trend), base + 2 * sigma)
    fx = _scaler(0, len(years) - 1, w, padx)
    fy = _scaler(lo, hi, h - 26, pady, invert=True)
    font = 'font-family="IBM Plex Sans, Segoe UI, Arial, sans-serif"'
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">',
         "<style>@keyframes d{to{stroke-dashoffset:0}}.d{stroke-dasharray:3000;stroke-dashoffset:3000;"
         "animation:d 1.6s ease-out forwards}.t{animation-delay:.9s}"
         "@media (prefers-reduced-motion:reduce){.d{animation:none;stroke-dashoffset:0}}</style>"]
    # zero line and band
    p.append(f'<line x1="{padx}" y1="{fy(0):.1f}" x2="{w - padx}" y2="{fy(0):.1f}" stroke="{RULE}"/>')
    y1, y2 = fy(base + 2 * sigma), fy(base - 2 * sigma)
    p.append(f'<rect x="{padx}" y="{y1:.1f}" width="{w - 2 * padx}" height="{y2 - y1:.1f}" fill="{BAND}" opacity=".8"/>')
    p.append(f'<text x="{padx + 6}" y="{y2 - 7:.1f}" fill="{MUTED}" font-size="11.5" {font}>'
             f'normal year-to-year variation</text>')
    pts = " ".join(f"{fx(i):.1f},{fy(v):.1f}" for i, v in enumerate(values))
    p.append(f'<polyline class="d" points="{pts}" fill="none" stroke="{YEARLY}" stroke-width="1.6" stroke-linejoin="round"/>')
    for i, v in enumerate(values):
        outside = abs(v - base) > 2 * sigma
        p.append(f'<circle cx="{fx(i):.1f}" cy="{fy(v):.1f}" r="{3.4 if outside else 2.6}" '
                 f'fill="{YEARLY_DARK if outside else YEARLY}"/>')
    p.append(f'<line class="d t" x1="{fx(0):.1f}" y1="{fy(trend[0]):.1f}" x2="{fx(len(years) - 1):.1f}" '
             f'y2="{fy(trend[-1]):.1f}" stroke="{SIGNAL}" stroke-width="2.6" stroke-linecap="round"/>')
    if emergence_year in years:
        i = years.index(emergence_year)
        ex = fx(i)
        p.append(f'<line x1="{ex:.1f}" y1="{pady - 6}" x2="{ex:.1f}" y2="{h - 26}" stroke="{INK}" '
                 f'stroke-width="1" stroke-dasharray="3 3"/>')
        p.append(f'<text x="{ex + 7:.1f}" y="{pady + 4}" fill="{INK}" font-size="12.5" font-weight="600" {font}>'
                 f'{emergence_year}</text>')
        p.append(f'<text x="{ex + 7:.1f}" y="{pady + 19}" fill="{MUTED}" font-size="11.5" {font}>'
                 f'change stands out</text>')
    for i in (0, len(years) - 1):
        anchor = "start" if i == 0 else "end"
        p.append(f'<text x="{fx(i):.1f}" y="{h - 4}" text-anchor="{anchor}" fill="{MUTED}" font-size="11.5" '
                 f'{font}>{years[i]}</text>')
    p.append("</svg>")
    return svg_img("".join(p), alt=label, style="display:block;width:100%;height:auto")


def style_fig(fig, height=420):
    """Same quiet chart style everywhere."""
    fig.update_layout(
        template="plotly_white", height=height,
        margin=dict(l=8, r=8, t=40, b=8),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="IBM Plex Sans, sans-serif", color=INK, size=12.5),
        hoverlabel=dict(bgcolor="#fff", bordercolor=BORDER, font=dict(family="IBM Plex Sans, sans-serif", color=INK)),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, bgcolor="rgba(0,0,0,0)",
                    font=dict(color=MUTED)),
    )
    fig.update_xaxes(showgrid=False, linecolor=RULE, ticks="outside", tickcolor=RULE, tickfont=dict(color=MUTED),
                     title_font=dict(color=MUTED))
    fig.update_yaxes(gridcolor=GRID, zeroline=True, zerolinecolor=RULE, zerolinewidth=1,
                     tickfont=dict(color=MUTED), title_font=dict(color=MUTED))
    return fig


def quiet_map(m):
    """Desaturate map tiles so they sit back and the markers stand out (styles live inside the map)."""
    import folium
    m.get_root().header.add_child(folium.Element(
        "<style>.leaflet-tile-pane{filter:saturate(.25) contrast(.92) brightness(1.04)}</style>"))
    return m


PLOTLY_CONFIG = {"displaylogo": False, "modeBarButtonsToRemove": ["lasso2d", "select2d", "autoScale2d"]}
