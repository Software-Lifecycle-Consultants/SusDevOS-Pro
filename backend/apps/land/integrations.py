"""
Place-name geocoding for the land-parcel map.

Backed by Nominatim (OpenStreetMap) by default, which needs no API key. Proxied
through the backend rather than called from the browser for three reasons:

  * Nominatim's usage policy requires a descriptive User-Agent identifying the
    application, which a browser cannot set on a cross-origin request;
  * results are cached here, so repeat lookups of the same city cost nothing and
    the 1 request/second policy is easy to honour;
  * the tenant's browser never talks to a third party, so no user IP or search
    term leaves our infrastructure.

Defensive throughout, like apps/ecosystem/integrations.py: network or parse
failures return an empty list rather than raising into the request path. A map
search box that finds nothing is a much better failure than a 500.
"""
import logging

from django.conf import settings
from django.core.cache import cache

import requests

logger = logging.getLogger(__name__)

TIMEOUT = 8
CACHE_TTL = 60 * 60 * 24  # a city does not move; a day is conservative
MAX_RESULTS = 8


def _cache_key(query: str, limit: int) -> str:
    from hashlib import sha256

    digest = sha256(query.encode("utf-8")).hexdigest()[:32]
    return f"geocode:v1:{limit}:{digest}"


def search_places(query: str, limit: int = 5) -> list[dict]:
    """
    Look up places by name. Returns a list of
    {DisplayName, Latitude, Longitude, BoundingBox, Type}.

    BoundingBox is [south, north, west, east] in degrees when the provider
    supplies one, so the caller can fit the map to a city rather than dropping a
    pin at its centroid. Empty list on any failure or empty query.
    """
    query = (query or "").strip()
    if not query:
        return []

    limit = max(1, min(int(limit or 5), MAX_RESULTS))
    key = _cache_key(query, limit)

    try:
        cached = cache.get(key)
    except Exception as exc:  # cache backend down — degrade to a live lookup
        logger.warning("Geocode cache read failed: %s", exc)
        cached = None
    if cached is not None:
        return cached

    url = getattr(
        settings, "NOMINATIM_URL", "https://nominatim.openstreetmap.org/search"
    )
    user_agent = getattr(settings, "GEOCODER_USER_AGENT", "SusDevOS")

    try:
        resp = requests.get(
            url,
            params={"q": query, "format": "jsonv2", "limit": limit, "addressdetails": 0},
            headers={"User-Agent": user_agent, "Accept": "application/json"},
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        rows = resp.json()
    except (requests.RequestException, ValueError) as exc:
        logger.warning("Geocoder lookup failed for %r: %s", query, exc)
        return []

    if not isinstance(rows, list):
        logger.warning("Geocoder returned %s, expected a list", type(rows).__name__)
        return []

    results = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        try:
            lat = float(row["lat"])
            lon = float(row["lon"])
        except (KeyError, TypeError, ValueError):
            continue

        bbox = row.get("boundingbox")
        # Nominatim gives boundingbox as four strings: [south, north, west, east].
        if isinstance(bbox, list | tuple) and len(bbox) == 4:
            try:
                bbox = [float(v) for v in bbox]
            except (TypeError, ValueError):
                bbox = None
        else:
            bbox = None

        results.append({
            "DisplayName": row.get("display_name") or query,
            "Latitude": lat,
            "Longitude": lon,
            "BoundingBox": bbox,
            "Type": row.get("type") or row.get("category"),
        })

    # Cache even an empty result: a misspelt query should not re-hit the provider
    # on every keystroke-triggered retry.
    try:
        cache.set(key, results, CACHE_TTL)
    except Exception as exc:
        logger.warning("Geocode cache write failed: %s", exc)
    return results
