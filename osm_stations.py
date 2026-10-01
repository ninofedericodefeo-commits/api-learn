"""Look up real fuel station locations from OpenStreetMap Overpass."""

import json
from math import asin, cos, isfinite, radians, sin, sqrt
from urllib.parse import urlencode
from urllib.request import Request, urlopen

OVERPASS_URL = "https://overpass.openstreetmap.fr/api/interpreter"
USER_AGENT = "GasFinder-local/0.1 (personal gas station lookup)"


def normalize_station(element: dict) -> dict | None:
    if not isinstance(element, dict) or element.get("type") not in {"node", "way", "relation"}:
        return None
    identifier = element.get("id")
    center = element if element.get("type") == "node" else element.get("center", {})
    tags = element.get("tags", {})
    if not isinstance(identifier, int) or not isinstance(center, dict) or not isinstance(tags, dict):
        return None
    latitude, longitude = center.get("lat"), center.get("lon")
    if not isinstance(latitude, (int, float)) or not isinstance(longitude, (int, float)):
        return None
    if not isfinite(latitude) or not isfinite(longitude) or not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
        return None
    if tags.get("amenity") != "fuel":
        return None
    name = tags.get("name") or tags.get("brand") or tags.get("operator") or "Gas station"
    if not isinstance(name, str):
        name = "Gas station"
    street = " ".join(str(tags.get(field, "")).strip() for field in ("addr:housenumber", "addr:street")).strip()
    address = street or "Address not mapped"
    return {
        "id": f"osm-{element['type']}-{identifier}",
        "name": name[:120],
        "brand": str(tags.get("brand", ""))[:120],
        "latitude": float(latitude),
        "longitude": float(longitude),
        "address": address,
        "city": str(tags.get("addr:city", ""))[:100],
        "state": str(tags.get("addr:state", ""))[:100],
        "zipCode": str(tags.get("addr:postcode", ""))[:20],
        "prices": [],
        "attributions": [{"provider": "© OpenStreetMap contributors", "providerUri": "https://www.openstreetmap.org/copyright"}],
    }


def search_stations(latitude: float, longitude: float, radius_miles: float) -> list[dict]:
    radius_meters = min(40000, round(radius_miles * 1609.344))
    query = (f'[out:json][timeout:15];nwr["amenity"="fuel"]'
             f'(around:{radius_meters},{latitude:.6f},{longitude:.6f});out center;')
    request = Request(
        OVERPASS_URL,
        data=urlencode({"data": query}).encode("utf-8"),
        headers={"User-Agent": USER_AGENT, "Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urlopen(request, timeout=20) as response:
        payload = json.load(response)
    if not isinstance(payload, dict) or not isinstance(payload.get("elements"), list):
        raise ValueError("Overpass returned an invalid response")
    stations = [station for element in payload["elements"] if (station := normalize_station(element))]

    def miles_away(station: dict) -> float:
        lat1, lat2 = radians(latitude), radians(station["latitude"])
        delta_lat = lat2 - lat1
        delta_lon = radians(station["longitude"] - longitude)
        arc = sin(delta_lat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(delta_lon / 2) ** 2
        return 3958.8 * 2 * asin(min(1, sqrt(arc)))

    return sorted(stations, key=miles_away)[:200]
