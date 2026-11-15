"""Place names <-> coordinates with OpenStreetMap Nominatim (cached, used by Home and Compare)."""
import requests
import streamlit as st

USER_AGENT = {"User-Agent": "GeoSleuth (NASA Space Apps 2026)"}


@st.cache_data(show_spinner=False)
def geocode(query):
    """Find a place by name with OpenStreetMap Nominatim. Returns (name, lat, lon) or None."""
    r = requests.get(
        "https://nominatim.openstreetmap.org/search",
        params={"q": query, "format": "json", "limit": 1, "accept-language": "en"},
        headers=USER_AGENT,
        timeout=15,
    )
    r.raise_for_status()
    hits = r.json()
    if not hits:
        return None
    h = hits[0]
    parts = [p.strip() for p in h["display_name"].split(",")]
    name = parts[0] if len(parts) == 1 else f"{parts[0]}, {parts[-1]}"
    return name, round(float(h["lat"]), 2), round(float(h["lon"]), 2)


@st.cache_data(show_spinner=False)
def reverse_geocode(lat, lon):
    """Turn coordinates into a readable name, e.g. 'Madrid, Spain'. Returns None if unknown."""
    try:
        r = requests.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={"lat": lat, "lon": lon, "format": "json", "zoom": 10, "accept-language": "en"},
            headers=USER_AGENT,
            timeout=15,
        )
        r.raise_for_status()
        addr = r.json().get("address", {})
    except (requests.RequestException, ValueError):
        return None
    local = (addr.get("city") or addr.get("town") or addr.get("village")
             or addr.get("county") or addr.get("state"))
    parts = [p for p in (local, addr.get("country")) if p]
    return ", ".join(parts) if parts else None


def normalize_lon(lon):
    """Keep longitude between -180 and 180 even if the map was scrolled sideways."""
    return round(((lon + 180) % 360) - 180, 2)
