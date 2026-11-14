import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import streamlit as st

st.title(" Case files")
st.info("Coming soon: ready-made investigations.")