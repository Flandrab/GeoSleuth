import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import streamlit as st

st.title("Glossary")
st.info("Coming soon: simple explanations of the science words.")