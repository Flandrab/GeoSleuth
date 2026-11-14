from src import cache
from src.catalog import get_variable
from src.fetch_power import fetch_power_monthly


def get_series(variable_id, lat, lon, start=2001, end=2024):
    """Monthly values for one variable at one place, cached as Parquet."""
    var = get_variable(variable_id)
    key = f"{variable_id}_{lat:.2f}_{lon:.2f}_{start}_{end}"

    s = cache.load(key)
    if s is not None:
        return s

    if var["source"] == "power":
        s = fetch_power_monthly(var["source_param"], lat, lon, start, end)
    else:
        raise NotImplementedError(f"Source '{var['source']}' not added yet")

    cache.save(key, s)
    return s