import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import streamlit as st

st.title("Glossary")
st.write(
    "Simple explanations of the words GeoSleuth uses. "
    "Open any term to read what it means and why it matters."
)

SECTIONS = {
    "The basics": [
        ("Variable",
         "Something that is measured, like air temperature, rainfall or soil moisture. "
         "GeoSleuth uses nine variables from NASA data."),
        ("Anomaly",
         "How different a value is from the usual value for that time of year. "
         "A July that is 1.5 °C warmer than an average July has an anomaly of +1.5 °C."),
        ("Seasonal cycle",
         "The regular pattern of summer and winter that repeats every year. GeoSleuth "
         "removes it first, so it does not hide slower, long-term change."),
        ("Trend",
         "The long-term direction of a variable over many years: rising, falling or flat. "
         "On the charts it is the straight red line."),
        ("Rate of change",
         "How fast the trend changes, given per decade (10 years). "
         "+0.5 °C per decade means about half a degree warmer every ten years."),
    ],
    "Is the change real?": [
        ("Natural variation",
         "The normal ups and downs from one year to the next, even without any long-term "
         "change. Some years are simply warmer or wetter than others. On the Investigate "
         "chart it is the grey band."),
        ("Statistically significant",
         "A result that is very unlikely to be caused by random ups and downs alone. "
         "GeoSleuth calls a trend significant when p is below 0.05."),
        ("p-value (chance it's random)",
         "How likely it is to see a trend this strong if there were really no trend at all. "
         "p = 0.01 means about a 1% chance. Smaller is more convincing."),
        ("95% range (confidence interval)",
         "The range where the true rate of change most likely lies. If the whole range is "
         "above zero, the variable is very likely rising."),
        ("Mann–Kendall test",
         "A standard test in climate science that checks whether values tend to go up or "
         "down over time. It does not assume the data follow a perfect straight line."),
        ("Autocorrelation and pre-whitening",
         "Climate values often look like the year before, which can make a trend seem more "
         "certain than it is. Pre-whitening (Yue et al., 2002) corrects for this before the "
         "test is run."),
        ("Sen's slope",
         "A robust way to measure the rate of change. One unusual year does not pull it off "
         "course the way it can with a simple average."),
        ("Robustness check",
         "GeoSleuth repeats each analysis starting one to five years later. If the verdict "
         "stays the same, the result does not depend on one lucky choice of start year."),
        ("Testing many variables at once",
         "When you test many things, a few can look significant just by chance. GeoSleuth "
         "corrects for this on the Timeline page (Benjamini–Hochberg method)."),
    ],
    "Emergence": [
        ("Emerged",
         "The change is significant and is now more than twice the size of normal "
         "year-to-year variation. It has clearly stood out from the noise."),
        ("Emergence year",
         "The first year in which the trend became larger than twice the natural variation. "
         "On the chart it is the dashed line, and in the sound it is the bell."),
        ("Emerging",
         "There are signs of a trend, but it is still hidden inside natural variation. "
         "If the current rate continues, GeoSleuth estimates the year it would stand out."),
        ("No clear signal",
         "No convincing long-term change was found. This can mean nothing is changing, or "
         "that more years of data are needed to tell."),
        ("Signal and noise",
         "The signal is the long-term change; the noise is the natural ups and downs. "
         "A change emerges when the signal becomes clearly bigger than the noise."),
    ],
    "Data sources": [
        ("NASA POWER",
         "A free NASA service that provides weather and climate data for any place on Earth. "
         "GeoSleuth uses its monthly data from 2001 to 2024."),
        ("MERRA-2",
         "A NASA model that combines satellite and ground measurements into a complete "
         "picture of the atmosphere. Most NASA POWER variables are based on it."),
        ("CERES",
         "NASA satellite instruments that measure sunlight and heat. GeoSleuth's sunlight "
         "variable is based on CERES data."),
        ("GPM IMERG",
         "A NASA rainfall record built from many satellites and rain gauges. GeoSleuth uses "
         "it on the Validation page as an independent check."),
        ("Giovanni",
         "A NASA web tool for making time series from Earth science data. GeoSleuth used it "
         "to get the GPM IMERG rainfall for Kosovo."),
    ],
    "Sound": [
        ("Sonification",
         "Turning data into sound. In GeoSleuth each year becomes a note: higher values give "
         "higher notes, years outside natural variation are louder, and a bell marks the "
         "emergence year."),
        ("Pentatonic scale",
         "A set of five notes per octave that always sound pleasant together. It is used so "
         "the melody sounds musical whatever the data do."),
    ],
}

for section, terms in SECTIONS.items():
    st.subheader(section)
    for term, explanation in terms:
        with st.expander(term):
            st.write(explanation)