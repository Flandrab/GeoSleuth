def scan_region(lat, lon, topics):
    """FAKE for now."""
    return [
        {"variable_id": "t2m", "status": "emerged", "emergence_year": 2012,
         "projected_year": None, "slope_per_decade": 0.6, "q_value": 0.01},
        {"variable_id": "precip", "status": "no_signal", "emergence_year": None,
         "projected_year": None, "slope_per_decade": 0.02, "q_value": 0.6},
    ]