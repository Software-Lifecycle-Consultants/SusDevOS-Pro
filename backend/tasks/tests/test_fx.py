"""
Tests for the FX sync tasks (tasks/integrations/fx.py).

Focus: the Open Exchange Rates fallback must store Rate as USD-per-FromCurrency
(matching the ECB path and how ExchangeRates.Rate is consumed), even though OER
quotes currency-per-USD off its USD base.
"""
from decimal import Decimal
from unittest.mock import patch

import pytest

pytestmark = pytest.mark.django_db


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def test_oer_rate_is_stored_inverted_to_usd_per_currency():
    from apps.emissions.models import ExchangeRates
    from tasks.integrations.fx import sync_oer_fx_rates

    # OER USD-base payload: 0.80 GBP per 1 USD.
    payload = {"base": "USD", "rates": {"GBP": 0.80}}

    with patch("tasks.integrations.fx.settings") as mock_settings, \
         patch("tasks.integrations.fx.requests.get", return_value=_FakeResponse(payload)):
        mock_settings.OPEN_EXCHANGE_RATES_API_KEY = "test-key"
        # getattr(settings, "OPEN_EXCHANGE_RATES_API_KEY", "") must resolve to the key
        result = sync_oer_fx_rates()

    assert result["created"] == 1
    rate = ExchangeRates.objects.get(FromCurrency="GBP", ToCurrency="USD")
    # USD per GBP = 1 / 0.80 = 1.25, NOT the raw 0.80.
    assert rate.Rate == Decimal("1") / Decimal("0.80")
    assert rate.Rate > Decimal("1")


def test_oer_skips_non_positive_rate():
    from apps.emissions.models import ExchangeRates
    from tasks.integrations.fx import sync_oer_fx_rates

    payload = {"base": "USD", "rates": {"GBP": 0}}

    with patch("tasks.integrations.fx.settings") as mock_settings, \
         patch("tasks.integrations.fx.requests.get", return_value=_FakeResponse(payload)):
        mock_settings.OPEN_EXCHANGE_RATES_API_KEY = "test-key"
        result = sync_oer_fx_rates()

    assert result["created"] == 0
    assert not ExchangeRates.objects.filter(FromCurrency="GBP").exists()
