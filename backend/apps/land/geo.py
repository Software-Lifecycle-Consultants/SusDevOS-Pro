"""Geometry helpers for land parcels.

``LandParcels.BoundaryGeoJSON`` is a plain ``JSONField``, not a PostGIS geometry
column, so there is no ``ST_Area`` to call. Area is therefore computed here in
Python from the raw GeoJSON.

The formula is the spherical-excess approximation Leaflet's
``L.GeometryUtil.geodesicArea`` uses, so the figure the user watches update while
drawing matches the one the server stores. It treats the earth as a sphere of
radius 6378137 m (the WGS84 semi-major axis); for parcel-scale polygons the error
against a true ellipsoidal computation is well under a tenth of a percent, far
finer than boundary-drawing precision.
"""
from __future__ import annotations

from math import pi, sin

# WGS84 semi-major axis, metres.
EARTH_RADIUS_M = 6378137.0
_DEG_TO_RAD = pi / 180.0
SQUARE_METRES_PER_HECTARE = 10_000.0


def _ring_area_m2(ring) -> float:
    """Signed-magnitude area of one linear ring, in square metres.

    ``ring`` is a GeoJSON coordinate list: [[lng, lat], ...]. A closed ring
    (first point repeated last) is fine — the closing edge contributes zero.
    """
    if not isinstance(ring, list | tuple) or len(ring) < 3:
        return 0.0

    total = 0.0
    count = len(ring)
    for i in range(count):
        p1 = ring[i]
        p2 = ring[(i + 1) % count]
        try:
            lng1, lat1 = float(p1[0]), float(p1[1])
            lng2, lat2 = float(p2[0]), float(p2[1])
        except (TypeError, ValueError, IndexError):
            return 0.0
        total += (
            (lng2 - lng1) * _DEG_TO_RAD
            * (2 + sin(lat1 * _DEG_TO_RAD) + sin(lat2 * _DEG_TO_RAD))
        )
    return abs(total * EARTH_RADIUS_M * EARTH_RADIUS_M / 2.0)


def _polygon_area_m2(rings) -> float:
    """Exterior ring minus any interior rings (holes)."""
    if not isinstance(rings, list | tuple) or not rings:
        return 0.0
    exterior = _ring_area_m2(rings[0])
    holes = sum(_ring_area_m2(r) for r in rings[1:])
    return max(exterior - holes, 0.0)


def _geometry_area_m2(geom) -> float:
    if not isinstance(geom, dict):
        return 0.0
    gtype = geom.get("type")

    if gtype == "Polygon":
        return _polygon_area_m2(geom.get("coordinates"))
    if gtype == "MultiPolygon":
        polys = geom.get("coordinates")
        if not isinstance(polys, list | tuple):
            return 0.0
        return sum(_polygon_area_m2(p) for p in polys)
    if gtype == "GeometryCollection":
        geoms = geom.get("geometries")
        if not isinstance(geoms, list | tuple):
            return 0.0
        return sum(_geometry_area_m2(g) for g in geoms)
    if gtype == "Feature":
        return _geometry_area_m2(geom.get("geometry"))
    if gtype == "FeatureCollection":
        feats = geom.get("features")
        if not isinstance(feats, list | tuple):
            return 0.0
        return sum(_geometry_area_m2(f) for f in feats)

    # Point / LineString / unknown / None — no enclosed area.
    return 0.0


def area_hectares(geojson) -> float | None:
    """Area of a GeoJSON boundary in hectares, or None if it encloses none.

    Returns None rather than 0.0 for point pins and line geometry, so callers can
    tell "this shape has no area" apart from "this shape is vanishingly small".
    Never raises on malformed input: a boundary that cannot be measured yields
    None, leaving any user-entered area untouched.
    """
    square_metres = _geometry_area_m2(geojson)
    if square_metres <= 0:
        return None
    return square_metres / SQUARE_METRES_PER_HECTARE
