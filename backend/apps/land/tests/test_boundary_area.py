"""
Area derivation from a drawn boundary.

``LandParcels.BoundaryGeoJSON`` is a plain JSONField, not a PostGIS geometry
column, so there is no ST_Area and the figure is computed in Python by
apps/land/geo.py. These tests pin the maths against hand-checkable shapes and
then pin the serializer policy that decides when it is applied.
"""
from decimal import Decimal

import pytest

from apps.land.geo import area_hectares

PARCELS_URL = "/api/land-parcels/"

# 0.01 degrees square with its south-west corner on the equator/prime meridian.
# 0.01 deg of latitude is ~1111.95 m; at the equator 0.01 deg of longitude is
# ~1113.19 m, so the enclosed area is ~1.2392 km2 == ~123.92 ha.
EQUATOR_SQUARE = {
    "type": "Polygon",
    "coordinates": [[[0.0, 0.0], [0.01, 0.0], [0.01, 0.01], [0.0, 0.01], [0.0, 0.0]]],
}
EQUATOR_SQUARE_HA = 123.92


# ── The maths ────────────────────────────────────────────────────────────────


class TestAreaHectares:
    def test_square_at_the_equator(self):
        assert area_hectares(EQUATOR_SQUARE) == pytest.approx(EQUATOR_SQUARE_HA, abs=0.05)

    def test_same_square_is_smaller_at_high_latitude(self):
        """Meridians converge, so a fixed-degree box shrinks towards the poles."""
        north = {
            "type": "Polygon",
            "coordinates": [[
                [0.0, 60.0], [0.01, 60.0], [0.01, 60.01], [0.0, 60.01], [0.0, 60.0],
            ]],
        }
        # cos(60 degrees) == 0.5, so roughly half the equatorial area.
        assert area_hectares(north) == pytest.approx(EQUATOR_SQUARE_HA / 2, rel=0.01)

    def test_unclosed_ring_measures_the_same_as_a_closed_one(self):
        """GeoJSON requires closure, but a drawing client may omit the repeat."""
        unclosed = {
            "type": "Polygon",
            "coordinates": [[[0.0, 0.0], [0.01, 0.0], [0.01, 0.01], [0.0, 0.01]]],
        }
        assert area_hectares(unclosed) == pytest.approx(EQUATOR_SQUARE_HA, abs=0.05)

    def test_winding_order_does_not_change_the_result(self):
        reversed_ring = {
            "type": "Polygon",
            "coordinates": [[list(reversed(EQUATOR_SQUARE["coordinates"][0]))][0]],
        }
        assert area_hectares(reversed_ring) == pytest.approx(EQUATOR_SQUARE_HA, abs=0.05)

    def test_hole_is_subtracted(self):
        with_hole = {
            "type": "Polygon",
            "coordinates": [
                EQUATOR_SQUARE["coordinates"][0],
                # Inner ring covering a quarter of the box.
                [[0.0, 0.0], [0.005, 0.0], [0.005, 0.005], [0.0, 0.005], [0.0, 0.0]],
            ],
        }
        assert area_hectares(with_hole) == pytest.approx(EQUATOR_SQUARE_HA * 0.75, rel=0.01)

    def test_multipolygon_sums_its_parts(self):
        multi = {
            "type": "MultiPolygon",
            "coordinates": [
                EQUATOR_SQUARE["coordinates"],
                [[[1.0, 0.0], [1.01, 0.0], [1.01, 0.01], [1.0, 0.01], [1.0, 0.0]]],
            ],
        }
        assert area_hectares(multi) == pytest.approx(EQUATOR_SQUARE_HA * 2, abs=0.1)

    def test_feature_wrapper_is_unwrapped(self):
        feature = {"type": "Feature", "properties": {}, "geometry": EQUATOR_SQUARE}
        assert area_hectares(feature) == pytest.approx(EQUATOR_SQUARE_HA, abs=0.05)

    @pytest.mark.parametrize("geom", [
        None,
        {},
        {"type": "Point", "coordinates": [0.0, 0.0]},
        {"type": "LineString", "coordinates": [[0.0, 0.0], [0.01, 0.01]]},
        {"type": "Polygon", "coordinates": [[[0.0, 0.0], [0.01, 0.0]]]},   # 2 points
        {"type": "Polygon", "coordinates": "nonsense"},
        {"type": "Polygon"},
        "a string",
        42,
    ])
    def test_shapes_that_enclose_nothing_return_none(self, geom):
        """None, not 0.0 - so a caller can leave a typed-in area untouched."""
        assert area_hectares(geom) is None


# ── The serializer policy ────────────────────────────────────────────────────


@pytest.mark.django_db
class TestAreaDerivedOnWrite:
    def test_polygon_without_an_area_derives_one(self, auth_client, entity):
        resp = auth_client.post(
            PARCELS_URL,
            {"ParcelName": "Drawn field", "BoundaryGeoJSON": EQUATOR_SQUARE},
            format="json",
        )
        assert resp.status_code == 201, resp.data
        assert float(resp.data["AreaHectares"]) == pytest.approx(EQUATOR_SQUARE_HA, abs=0.05)

    def test_null_area_alongside_a_polygon_still_derives(self, auth_client, entity):
        """The create form always sends the key, as null when the input is blank."""
        resp = auth_client.post(
            PARCELS_URL,
            {"ParcelName": "Blank area", "AreaHectares": None, "BoundaryGeoJSON": EQUATOR_SQUARE},
            format="json",
        )
        assert resp.status_code == 201, resp.data
        assert float(resp.data["AreaHectares"]) == pytest.approx(EQUATOR_SQUARE_HA, abs=0.05)

    def test_explicit_area_overrides_the_polygon(self, auth_client, entity):
        """Legal title area can differ from the mapped shape - the user wins."""
        resp = auth_client.post(
            PARCELS_URL,
            {"ParcelName": "Title area", "AreaHectares": "5.0000",
             "BoundaryGeoJSON": EQUATOR_SQUARE},
            format="json",
        )
        assert resp.status_code == 201, resp.data
        assert Decimal(resp.data["AreaHectares"]) == Decimal("5.0000")

    def test_point_pin_leaves_area_empty(self, auth_client, entity):
        resp = auth_client.post(
            PARCELS_URL,
            {"ParcelName": "Just a pin",
             "BoundaryGeoJSON": {"type": "Point", "coordinates": [-0.09, 51.5]}},
            format="json",
        )
        assert resp.status_code == 201, resp.data
        assert resp.data["AreaHectares"] is None

    def test_redrawing_the_boundary_updates_the_area(self, auth_client, entity):
        created = auth_client.post(
            PARCELS_URL, {"ParcelName": "Redrawn"}, format="json",
        )
        assert created.status_code == 201, created.data
        parcel_id = created.data["LandParcelId"]

        patched = auth_client.patch(
            f"{PARCELS_URL}{parcel_id}/",
            {"BoundaryGeoJSON": EQUATOR_SQUARE},
            format="json",
        )
        assert patched.status_code == 200, patched.data
        assert float(patched.data["AreaHectares"]) == pytest.approx(
            EQUATOR_SQUARE_HA, abs=0.05
        )

    def test_editing_an_unrelated_field_leaves_the_area_alone(self, auth_client, entity):
        created = auth_client.post(
            PARCELS_URL,
            {"ParcelName": "Stable", "AreaHectares": "7.5000"},
            format="json",
        )
        parcel_id = created.data["LandParcelId"]

        patched = auth_client.patch(
            f"{PARCELS_URL}{parcel_id}/", {"Tenure": "Freehold"}, format="json",
        )
        assert patched.status_code == 200, patched.data
        assert Decimal(patched.data["AreaHectares"]) == Decimal("7.5000")

    def test_non_geojson_boundary_is_rejected(self, auth_client, entity):
        resp = auth_client.post(
            PARCELS_URL,
            {"ParcelName": "Garbage", "BoundaryGeoJSON": {"lat": 51.5, "lng": -0.09}},
            format="json",
        )
        assert resp.status_code == 400, resp.data
        # custom_exception_handler nests field errors under "errors".
        assert "BoundaryGeoJSON" in resp.data["errors"]
