import sys
from pathlib import Path

APP = Path(__file__).resolve().parent
sys.path.append(str(APP.parent))

import streamlit as st

st.set_page_config(
    page_title="GeoSleuth",
    page_icon=str(APP / "static" / "icon.svg"),
    layout="wide",
)
st.logo(str(APP / "static" / "logo.svg"), icon_image=str(APP / "static" / "icon.svg"), size="large")

# Top navigation. Page files live in app/views/ (not app/pages/, which would switch on
# Streamlit's older automatic navigation). A new page only shows up once it is added here.
pages = [
    st.Page("views/0_Home.py", title="Home", default=True),
    st.Page("views/1_Timeline.py", title="Trend scanner"),
    st.Page("views/2_Investigate.py", title="Investigate"),
    st.Page("views/3_Compare.py", title="Compare"),
    st.Page("views/4_Case_Files.py", title="Case files"),
    st.Page("views/6_Validation.py", title="Validation"),
    st.Page("views/5_Glossary.py", title="Glossary"),
]
st.navigation(pages, position="top").run()
