import requests


def geocode_osm(place: str, user_agent="climate-app"):
    url = f"https://nominatim.openstreetmap.org/search"
    params = {"q": place, "format": "json", "limit": 1}
    headers = {"User-Agent": user_agent}
    r = requests.get(url, params=params, headers=headers, timeout=10)
    r.raise_for_status()
    arr = r.json()
    if not arr:
        return None, None
    return float(arr[0]["lat"]), float(arr[0]["lon"])
