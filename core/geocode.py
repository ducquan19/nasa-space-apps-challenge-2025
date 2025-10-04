import requests
from typing import Tuple, Dict

import geocoder
from opencage.geocoder import OpenCageGeocode

def geocode_osm(place: str, user_agent: str = "climate-app") -> Tuple[float, float]:
    url = f"https://nominatim.openstreetmap.org/search"
    params = {"q": place, "format": "json", "limit": 1}
    headers = {"User-Agent": user_agent}

    r = requests.get(url, params=params, headers=headers, timeout=10)
    r.raise_for_status()
    arr = r.json()

    if not arr:
        raise ValueError(f"Can not find place {place}")

    return float(arr[0]["lat"]), float(arr[0]["lon"])


def get_current_coordinate() -> Tuple[float, float]:
    return geocoder.ip("me").latlng


def get_current_place() -> Dict[str, str]:
    key = "a62ac1641535410e9621cdfadbc9f614"
    geocoder = OpenCageGeocode(key)
    latitude, longitude = get_current_coordinate()

    results = geocoder.reverse_geocode(latitude, longitude)
    return {"current_place": results[0]["formatted"]}
