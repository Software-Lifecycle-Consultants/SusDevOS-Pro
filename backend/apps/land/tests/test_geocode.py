"""
Place-name search behind the land-parcel map.

The endpoint proxies Nominatim so the provider sees our User-Agent and cache
rather than the tenant's browser. Every test stubs the HTTP call: the suite must
never depend on a third-party service being reachable.
"""
from unittest.mock import patch

import pytest
import requests

from apps.land.integrations import search_places

GEOCODE_URL = "/api/land-parcels/geocode/"

NOMINATIM_ROW = {
    "lat": "51.5073219",
    "lon": "-0.1276474",
    "display_name": "London, Greater London, England, United Kingdom",
    "boundingbox": ["51.2867601", "51.6918741", "-0.5103751", "0.3340155"],
    "type": "city",
}


@pytest.fixture(autouse=True)
def _isolated_cache(settings):
    """A private in-process cache per test.

    search_places() caches results, so without this a stubbed response would leak
    into the next test and the assertions would pass for the wrong reason.
    """
    from django.core.cache import cache

    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "geocode-tests",
        }
    }
    cache.clear()
    yield
    cache.clear()


def _response(payload, status_code=200):
    class _Resp:
        def raise_for_status(self):
            if status_code >= 400:
                raise requests.HTTPError(f"{status_code}")

        def json(self):
            return payload

    return _Resp()


# ── The integration ──────────────────────────────────────────────────────────


class TestSearchPlaces:
    def test_maps_a_provider_row_to_our_shape(self):
        with patch("apps.land.integrations.requests.get",
                   return_value=_response([NOMINATIM_ROW])):
            results = search_places("London")

        assert len(results) == 1
        assert results[0]["Latitude"] == pytest.approx(51.5073219)
        assert results[0]["Longitude"] == pytest.approx(-0.1276474)
        assert results[0]["DisplayName"].startswith("London")
        assert results[0]["BoundingBox"] == pytest.approx(
            [51.2867601, 51.6918741, -0.5103751, 0.3340155]
        )

    def test_sends_an_identifying_user_agent(self):
        """Nominatim's usage policy rejects requests without one."""
        with patch("apps.land.integrations.requests.get",
                   return_value=_response([])) as mock_get:
            search_places("London")

        assert "User-Agent" in mock_get.call_args.kwargs["headers"]
        assert mock_get.call_args.kwargs["headers"]["User-Agent"].strip()

    def test_empty_query_never_calls_the_provider(self):
        with patch("apps.land.integrations.requests.get") as mock_get:
            assert search_places("   ") == []
        mock_get.assert_not_called()

    def test_repeat_query_is_served_from_cache(self):
        with patch("apps.land.integrations.requests.get",
                   return_value=_response([NOMINATIM_ROW])) as mock_get:
            first = search_places("Cambridge")
            second = search_places("Cambridge")

        assert first == second
        assert mock_get.call_count == 1

    def test_network_failure_returns_empty_not_an_exception(self):
        with patch("apps.land.integrations.requests.get",
                   side_effect=requests.ConnectionError("down")):
            assert search_places("London") == []

    def test_http_error_returns_empty(self):
        with patch("apps.land.integrations.requests.get",
                   return_value=_response([], status_code=503)):
            assert search_places("London") == []

    def test_malformed_rows_are_skipped_not_fatal(self):
        rows = [{"no": "coords"}, {"lat": "abc", "lon": "def"}, NOMINATIM_ROW]
        with patch("apps.land.integrations.requests.get", return_value=_response(rows)):
            results = search_places("London")

        assert len(results) == 1

    def test_missing_bounding_box_is_none_not_an_error(self):
        row = {k: v for k, v in NOMINATIM_ROW.items() if k != "boundingbox"}
        with patch("apps.land.integrations.requests.get", return_value=_response([row])):
            results = search_places("London")

        assert results[0]["BoundingBox"] is None

    def test_limit_is_clamped(self):
        with patch("apps.land.integrations.requests.get",
                   return_value=_response([])) as mock_get:
            search_places("London", limit=999)

        assert mock_get.call_args.kwargs["params"]["limit"] <= 8


# ── The endpoint ─────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestGeocodeEndpoint:
    def test_returns_matches(self, auth_client, entity):
        with patch("apps.land.integrations.requests.get",
                   return_value=_response([NOMINATIM_ROW])):
            resp = auth_client.get(f"{GEOCODE_URL}?q=London")

        assert resp.status_code == 200, resp.data
        assert resp.data[0]["DisplayName"].startswith("London")

    def test_requires_authentication(self, entity):
        from rest_framework.test import APIClient

        resp = APIClient().get(f"{GEOCODE_URL}?q=London")
        assert resp.status_code in (401, 403), resp.data

    def test_missing_query_returns_an_empty_list(self, auth_client, entity):
        with patch("apps.land.integrations.requests.get") as mock_get:
            resp = auth_client.get(GEOCODE_URL)

        assert resp.status_code == 200, resp.data
        assert resp.data == []
        mock_get.assert_not_called()

    def test_provider_outage_is_an_empty_list_not_a_500(self, auth_client, entity):
        """A search box that finds nothing beats a broken page."""
        with patch("apps.land.integrations.requests.get",
                   side_effect=requests.Timeout("slow")):
            resp = auth_client.get(f"{GEOCODE_URL}?q=London")

        assert resp.status_code == 200, resp.data
        assert resp.data == []

    def test_non_numeric_limit_falls_back_to_the_default(self, auth_client, entity):
        with patch("apps.land.integrations.requests.get",
                   return_value=_response([])) as mock_get:
            resp = auth_client.get(f"{GEOCODE_URL}?q=London&limit=abc")

        assert resp.status_code == 200, resp.data
        assert mock_get.call_args.kwargs["params"]["limit"] == 5
