import pandas as pd
import requests

URL = "https://power.larc.nasa.gov/api/temporal/monthly/point"


def fetch_power_monthly(param, lat, lon, start=2001, end=2024):
    params = {
        "parameters": param,
        "community": "AG",
        "latitude": lat,
        "longitude": lon,
        "start": start,
        "end": end,
        "format": "JSON",
    }
    r = requests.get(URL, params=params, timeout=60)
    r.raise_for_status()
    values = r.json()["properties"]["parameter"][param]

    rows = {}
    for key, val in values.items():
        year, month = int(key[:4]), int(key[4:])
        if month == 13:  # yearly average, skip
            continue
        rows[pd.Timestamp(year, month, 1)] = None if val == -999 else val

    s = pd.Series(rows, name=param, dtype="float64").sort_index()
    s.index.name = "date"
    return s