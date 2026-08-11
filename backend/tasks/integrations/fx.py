"""
ECB FX rate sync — daily 17:00 UTC.

Fetches EUR-based daily rates from the ECB Data Portal API, converts to
USD base (since emission factor spend calculations use USD), and upserts
into ExchangeRates. Falls back to Open Exchange Rates on ECB failure.
"""
import logging
from datetime import date
from decimal import Decimal

import requests
from celery import shared_task
from django.conf import settings

logger = logging.getLogger(__name__)

CURRENCIES = ["GBP", "EUR", "AUD", "CAD", "NZD", "ZAR", "INR", "BRL", "MXN", "SGD"]
ECB_BASE = "https://data-api.ecb.europa.eu/service/data/EXR"
TIMEOUT = 10


@shared_task(
    name="tasks.integrations.sync_ecb_fx_rates",
    bind=True,
    max_retries=3,
    default_retry_delay=300,
)
def sync_ecb_fx_rates(self):
    """
    Fetch daily FX rates from ECB and upsert into ExchangeRates.
    Strategy: get currency/EUR rates from ECB, cross-multiply via EUR/USD to get currency/USD.
    """
    from apps.emissions.models import ExchangeRates

    today = date.today().isoformat()
    created = 0
    errors = []

    # Get EUR/USD first (needed to cross all rates to USD)
    try:
        eur_per_usd = _fetch_ecb_rate("USD", today)
    except Exception as exc:
        logger.warning("ECB EUR/USD fetch failed, falling back to OER: %s", exc)
        sync_oer_fx_rates.delay()
        return {"skipped": "ECB EUR/USD unavailable, OER triggered"}

    for currency in CURRENCIES:
        if currency == "USD":
            rate_to_usd = Decimal("1")
        else:
            try:
                eur_per_currency = _fetch_ecb_rate(currency, today)
                # currency → USD = (EUR/USD) / (EUR/currency)
                rate_to_usd = Decimal(str(eur_per_usd)) / Decimal(str(eur_per_currency))
            except Exception as exc:
                errors.append(f"{currency}: {exc}")
                continue

        try:
            ExchangeRates.objects.update_or_create(
                FromCurrency=currency,
                ToCurrency="USD",
                RateDate=date.today(),
                defaults={"Rate": rate_to_usd, "Source": "ECB"},
            )
            created += 1
        except Exception as exc:
            errors.append(f"DB upsert {currency}: {exc}")

    if errors:
        logger.warning("ECB FX sync partial failure: %s", "; ".join(errors))

    logger.info("ECB FX sync: %d rates upserted, %d errors", created, len(errors))
    return {"created": created, "errors": len(errors)}


def _fetch_ecb_rate(currency: str, date_str: str) -> float:
    """Return EUR-per-currency rate from ECB API (raises on any error)."""
    url = (
        f"{ECB_BASE}/D.{currency}.EUR.SP00.A"
        f"?startPeriod={date_str}&endPeriod={date_str}&format=jsondata"
    )
    resp = requests.get(url, timeout=TIMEOUT)
    if resp.status_code == 404:
        raise ValueError(f"No ECB data for {currency} on {date_str}")
    resp.raise_for_status()
    observations = resp.json()["dataSets"][0]["series"]["0:0:0:0:0"]["observations"]
    if not observations:
        raise ValueError(f"Empty ECB observations for {currency}")
    return float(list(observations.values())[0][0])


@shared_task(
    name="tasks.integrations.sync_oer_fx_rates",
    bind=True,
    max_retries=2,
    default_retry_delay=600,
)
def sync_oer_fx_rates(self):
    """Fallback: sync from Open Exchange Rates when ECB is unavailable."""
    from apps.emissions.models import ExchangeRates

    api_key = getattr(settings, "OPEN_EXCHANGE_RATES_API_KEY", "")
    if not api_key:
        logger.warning("OPEN_EXCHANGE_RATES_API_KEY not set — skipping OER fallback")
        return {"skipped": "no API key"}

    try:
        resp = requests.get(
            f"https://openexchangerates.org/api/latest.json?app_id={api_key}",
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        rates = data.get("rates", {})
        created = 0
        for currency in CURRENCIES:
            if currency not in rates:
                continue
            # OER's default base is USD, so rates[currency] is units of `currency`
            # per 1 USD. ExchangeRates.Rate is consumed as USD-per-FromCurrency
            # (usd_amount = amount * Rate), matching the ECB path — so invert.
            oer_rate = Decimal(str(rates[currency]))
            if oer_rate <= 0:
                logger.warning("OER returned non-positive rate for %s: %s", currency, oer_rate)
                continue
            usd_per_currency = Decimal("1") / oer_rate
            ExchangeRates.objects.update_or_create(
                FromCurrency=currency,
                ToCurrency="USD",
                RateDate=date.today(),
                defaults={"Rate": usd_per_currency, "Source": "OpenExchangeRates"},
            )
            created += 1
        logger.info("OER FX sync: %d rates upserted", created)
        return {"created": created}
    except Exception as exc:
        raise self.retry(exc=exc)
