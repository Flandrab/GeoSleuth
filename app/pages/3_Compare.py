import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import streamlit as st

st.title("⚖️ Compare")
st.info("Coming soon: the same variable in two places, side by side.")