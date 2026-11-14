import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import streamlit as st

from src.catalog import load_catalog
from src.data import get_series

st.set_page_config(page_title="GeoSleuth", page_icon="🔍", layout="wide")
st.title("🔍 GeoSleuth")
st.write("When does climate change become undeniable where you live?")

# TEMPORARY test of real data – the partner replaces this with the map + topics
catalog = load_catalog()
var = st.selectbox("Variable", catalog, format_func=lambda v: v["name"])
if st.button("Test: load Prishtina data"):
    s = get_series(var["id"], 42.66, 21.17)
    st.line_chart(s)
    st.write(f"{len(s)} months loaded")