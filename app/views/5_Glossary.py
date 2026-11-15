import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import streamlit as st

from src import ui

ui.setup()
ui.page_header("Glossary", "The science words used in GeoSleuth, explained simply.")
st.space("small")
st.caption("Coming soon.")
