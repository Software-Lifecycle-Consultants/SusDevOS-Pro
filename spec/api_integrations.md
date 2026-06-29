# External API Integrations — SusDevOS

Integrations are split into two patterns:
- **On-demand** — called at request time (entity creation, EF lookup, offset validation). Result cached to DB.
- **Scheduled** — Celery beat tasks that sync reference data on a fixed cadence.

All external API keys are stored in environment variables (never in DB or code). See `.env.example` for the full list.

---

## Integration Overview

| Integration | Pattern | Cadence | Populates |
|------------|---------|---------|-----------|
| Climatiq | On-demand + scheduled refresh | Weekly | `EmissionFactors` |
| Companies House | On-demand | At entity creation | `Entities` |
| OpenCorporates | On-demand (non-UK fallback) | At entity creation | `Entities` |
| DEFRA | Scheduled download | Annual (March) | `EmissionFactors` |
| EPA eGRID | Scheduled download | Annual (Jan) | `EmissionFactors` |
| IEA Electricity | Scheduled download | Annual | `EmissionFactors` |
| SBTi Registry | Scheduled download | Monthly | `Targets` |
| ECB / Open Exchange Rates | Scheduled | Daily | `ExchangeRates` |
| Verra Registry | On-demand | At offset save | `EmissionsOffsets` |
| Gold Standard Registry | On-demand | At offset save | `EmissionsOffsets` |
| GBIF | On-demand | At species creation | `Species` |
| IUCN Red List | On-demand | At species creation | `Species` |

---

## 1. Climatiq — Emission Factor Lookup

**Purpose:** Query a unified EF database covering DEFRA, EPA, IPCC, EXIOBASE, and more by activity type. Reduces the need to maintain separate EF datasets for each source.

**Docs:** `https://www.climatiq.io/docs`

**Auth:** Bearer token — `CLIMATIQ_API_KEY` env var.

**Rate limits:** Starter plan 1,000 calls/month. Cache aggressively — one lookup per unique `(activity_id, region, year)` tuple.

### Key endpoints

#### Activity search (EF discovery)
```
GET https://api.climatiq.io/data/v1/search?query={activity}&region={ISO2}&year={year}
Authorization: Bearer {CLIMATIQ_API_KEY}
```

Response fields mapped to `EmissionFactors`:
```json
{
  "results": [{
    "activity_id": "electricity-supply_grid-source_residual_mix",
    "name": "Electricity supply from grid, residual mix",
    "category": "Energy",
    "sector": "Electricity",
    "source": "DEFRA",
    "source_dataset": "DEFRA 2024",
    "region": "GB",
    "year": 2024,
    "unit": "kWh",
    "factor": {
      "co2e": 0.207,
      "co2e_unit": "kg",
      "co2": 0.19341,
      "ch4": 0.00021,
      "n2o": 0.00038
    }
  }]
}
```

#### Estimate (calculate emissions, returns EF inline)
```
POST https://api.climatiq.io/data/v1/estimate
Content-Type: application/json
{
  "emission_factor": { "activity_id": "...", "region": "GB", "year": 2024 },
  "parameters": { "energy": 100, "energy_unit": "kWh" }
}
```

Use this endpoint as a **fallback** when computing emissions for a category where no `EmissionFactors` record exists locally. Cache the returned EF into `EmissionFactors` after the first call.

### Mapping to EmissionFactors

```python
# services/integrations/climatiq.py

import requests
from decimal import Decimal
from apps.emissions.models import EmissionFactors, EmissionFactorSets

CLIMATIQ_BASE = "https://api.climatiq.io/data/v1"

def sync_climatiq_ef(activity_id: str, region: str, year: int) -> EmissionFactors:
    """
    Fetch EF from Climatiq and upsert into EmissionFactors.
    Returns the EmissionFactors instance.
    """
    ef_set, _ = EmissionFactorSets.objects.get_or_create(
        Name="Climatiq Aggregated",
        Publisher="Climatiq",
        defaults={
            "SourceUrl": "https://www.climatiq.io",
            "IsDefault": False,
        }
    )
    ef_set.PublishedYear = year
    ef_set.save()

    resp = requests.get(
        f"{CLIMATIQ_BASE}/search",
        params={"query": activity_id, "region": region, "year": year},
        headers={"Authorization": f"Bearer {settings.CLIMATIQ_API_KEY}"},
        timeout=10,
    )
    resp.raise_for_status()
    results = resp.json().get("results", [])
    if not results:
        return None

    r = results[0]
    factor = r["factor"]

    obj, created = EmissionFactors.objects.update_or_create(
        EFSetId=ef_set,
        ClimatiqActivityId=r["activity_id"],
        CountryCode=region,
        ApplicableYear=year,
        defaults={
            "FuelOrActivityType": r["name"],
            "CO2FactorKg": Decimal(str(factor.get("co2", 0))),
            "CH4FactorKg": Decimal(str(factor.get("ch4", 0))),
            "N2OFactorKg": Decimal(str(factor.get("n2o", 0))),
            "TotalKgCO2ePerUnit": Decimal(str(factor["co2e"])),
            "ExternalSyncedAt": now(),
        }
    )
    return obj
```

### Caching strategy

- Results are stored in `EmissionFactors` with `ClimatiqActivityId` as the external key.
- Before calling Climatiq, check if a local record exists with the same `(ClimatiqActivityId, CountryCode, ApplicableYear)` and `ExternalSyncedAt` within the last 7 days.
- Stale records (>7 days old) are refreshed by the weekly Celery beat task `sync_climatiq_weekly`.

---

## 2. Companies House — Entity Auto-Population (UK)

**Purpose:** When a user creates a new `Entities` record with a UK company name or registration number, auto-populate registered name, address, SIC codes, and parent company.

**Docs:** `https://developer-specs.company-information.service.gov.uk`

**Auth:** Basic auth — `COMPANIES_HOUSE_API_KEY` env var as username, blank password.

**Rate limits:** 600 requests per 5 minutes.

### Key endpoints

#### Company search
```
GET https://api.company-information.service.gov.uk/search/companies?q={name}&items_per_page=5
```

#### Company profile
```
GET https://api.company-information.service.gov.uk/company/{company_number}
```

Response fields:
```json
{
  "company_number": "12345678",
  "company_name": "EXAMPLE LTD",
  "registered_office_address": {
    "address_line_1": "123 Street",
    "locality": "London",
    "postal_code": "EC1A 1AA",
    "country": "England"
  },
  "sic_codes": ["35110"],
  "type": "ltd",
  "date_of_creation": "2015-03-01",
  "accounts": { "last_accounts": { "period_end_on": "2023-12-31" } }
}
```

#### Officers (to find parent group)
```
GET https://api.company-information.service.gov.uk/company/{company_number}/persons-with-significant-control
```

### Integration flow

Triggered by `POST /api/entities/` when `CompaniesHouseNumber` is provided, or by a separate lookup endpoint:

```
POST /api/integrations/companies-house/lookup/
{ "query": "Example Ltd" }          # search by name
{ "company_number": "12345678" }    # lookup by number
```

Returns candidate matches. User selects one. Frontend pre-fills the entity form. User confirms before save — never auto-save without confirmation.

```python
# services/integrations/companies_house.py

def lookup_company(company_number: str) -> dict:
    resp = requests.get(
        f"https://api.company-information.service.gov.uk/company/{company_number}",
        auth=(settings.COMPANIES_HOUSE_API_KEY, ""),
        timeout=8,
    )
    resp.raise_for_status()
    data = resp.json()

    address = data.get("registered_office_address", {})
    return {
        "EntityName": data["company_name"].title(),
        "CompaniesHouseNumber": data["company_number"],
        "EntityType": _map_company_type(data.get("type")),
        "SICCodes": data.get("sic_codes", []),
        "RegisteredAddress": {
            "AddressLine1": address.get("address_line_1"),
            "City": address.get("locality"),
            "PostCode": address.get("postal_code"),
            "Country": address.get("country", "United Kingdom"),
        },
        "IncorporationDate": data.get("date_of_creation"),
    }
```

### Fields populated on Entities

- `EntityName` — from `company_name`
- `CompaniesHouseNumber` — stored for future re-sync
- `RegistrationNumber` — same as `company_number`
- `SICCodes` — stored as JSONField; used to suggest SBTi sector pathway
- `IncorporationDate` — for audit trail

Address creates a `Locations` record linked to the entity via `EntityLocations` junction.

### OpenCorporates (non-UK fallback)

```
GET https://api.opencorporates.com/v0.4/companies/search?q={name}&jurisdiction_code={iso2}
Authorization: Token {OPENCORPORATES_API_KEY}
```

Same integration flow — triggered when entity country is not GB. Returns company number, name, registered address. OpenCorporates free tier: 500 calls/month. Upgrade if volume requires it.

---

## 3. DEFRA — UK Emission Factors (Annual Download)

**Purpose:** DEFRA publishes updated UK EFs each March as an Excel workbook. This is the most widely used EF dataset for UK entities. A scheduled task downloads and parses it into `EmissionFactors`.

**Source:** `https://www.gov.uk/government/collections/government-conversion-factors-for-company-reporting`

**Auth:** None — public download.

**Cadence:** Annual, triggered on first Monday of April (to allow for publication delay).

### Download and parse

```python
# tasks/sync_defra.py

DEFRA_DOWNLOAD_URL = settings.DEFRA_EF_SPREADSHEET_URL  # configured annually in .env

@shared_task(name="sync_defra_emission_factors")
def sync_defra_emission_factors():
    """
    Download DEFRA EF workbook and upsert into EmissionFactors.
    Idempotent — existing records matched on (EFSetId, FuelOrActivityType, Scope, CountryCode, ApplicableYear).
    """
    resp = requests.get(DEFRA_DOWNLOAD_URL, timeout=60)
    resp.raise_for_status()

    # Parse using openpyxl — sheet structure varies by year, use sheet named "Conversion Factors"
    wb = openpyxl.load_workbook(BytesIO(resp.content), read_only=True, data_only=True)
    sheet = wb["Conversion Factors"]

    ef_set, _ = EmissionFactorSets.objects.update_or_create(
        Publisher="DEFRA",
        PublishedYear=current_year,
        defaults={
            "Name": f"DEFRA {current_year} UK Government Conversion Factors",
            "Region": "GB",
            "SourceUrl": DEFRA_DOWNLOAD_URL,
            "IsDefault": True,   # DEFRA is default for UK entities
        }
    )

    rows_updated = 0
    for row in sheet.iter_rows(min_row=5, values_only=True):  # header on row 4
        fuel, scope, unit_str, co2, ch4, n2o, total, *_ = row
        if not fuel or not total:
            continue
        unit = Units.objects.filter(UnitSymbol__iexact=unit_str).first()
        EmissionFactors.objects.update_or_create(
            EFSetId=ef_set,
            FuelOrActivityType=str(fuel),
            Scope=int(scope) if scope else None,
            CountryCode="GB",
            ApplicableYear=current_year,
            defaults={
                "CO2FactorKg": _decimal(co2),
                "CH4FactorKg": _decimal(ch4),
                "N2OFactorKg": _decimal(n2o),
                "TotalKgCO2ePerUnit": _decimal(total),
                "InputUnitId": unit,
                "ExternalSyncedAt": now(),
            }
        )
        rows_updated += 1

    logger.info("DEFRA sync complete: %d factors upserted", rows_updated)
```

**Note:** The DEFRA spreadsheet URL changes each year. Store it as `DEFRA_EF_SPREADSHEET_URL` in `.env` and update annually. A SuperAdmin UI to update this URL without a redeploy is desirable.

---

## 4. EPA eGRID — US Grid Emission Factors (Annual)

**Purpose:** US location-based Scope 2 factors by eGRID subregion (e.g. SRSO, WECC, NPCC). Required for any US facility.

**Source:** `https://www.epa.gov/egrid/download-data` — Excel file, no REST API.

**Cadence:** Annual (January, for prior year data).

### Subregion mapping

`EmissionsData` records for US electricity need a `GridSubregion` field (added in migration 0027) to select the correct eGRID factor. The Entities address maps to subregion using the EPA's facility/state lookup table (seeded as a static mapping in the DB).

```python
# Static mapping: US state → default eGRID subregion (approximate)
US_STATE_TO_EGRID = {
    "CA": "WECC_CA",
    "TX": "ERCOT",
    "NY": "NPCC_NYC",
    # ... full table in fixtures/egrid_state_mapping.json
}
```

### Parsing

Same pattern as DEFRA — download Excel, read the `SRL` (Subregion) sheet, upsert into `EmissionFactors` with `CountryCode="US"` and `GridSubregion` in `FuelOrActivityType`.

---

## 5. SBTi Registry — Target Validation Status (Monthly Sync)

> ⚠️ **DEPRECATED / NOT IMPLEMENTED — do not build.** SBTi was removed from the
> product scope in the nature/MRV + TNFD refocus (commit "remove SBTi, CDP, NDC,
> RE100"). This section is retained for historical reference only. There is no
> SBTi sync task, no beat entry, and no `Targets.ValidationStatus` wiring. Other
> stale SBTi mentions remain in `marketing_site.md` (`/features/sbti-progress`),
> `ghg_calculation_spec.md`, and `celery_tasks.md` — clean those up separately.

**Purpose:** Auto-update `Targets.ValidationStatus` for SBTi-framework targets by matching the entity against the public SBTi companies list.

**Source:** `https://sciencebasedtargets.org/companies-taking-action` — CSV download (no API).

**Cadence:** Monthly (1st of each month, 02:00 UTC).

### Download and match

```python
# tasks/sync_sbti.py

SBTI_CSV_URL = "https://sciencebasedtargets.org/resources/legacy/2021/06/companies-taking-action-220621.csv"
# Note: URL changes — store as SBTI_COMPANIES_CSV_URL in .env

@shared_task(name="sync_sbti_registry")
def sync_sbti_registry():
    resp = requests.get(settings.SBTI_COMPANIES_CSV_URL, timeout=30)
    resp.raise_for_status()
    reader = csv.DictReader(StringIO(resp.text))

    for row in reader:
        company_name = row.get("Company Name", "").strip()
        status = row.get("Target Status", "").strip()       # "Targets Set", "Committed", "Achieved"
        target_year = row.get("Target Year")
        sbti_id = row.get("ID", "").strip()

        # Match by SBTiCompanyId (exact) or EntityName (fuzzy, manual review flagged)
        entity = (
            Entities.objects.filter(SBTiCompanyId=sbti_id).first()
            or _fuzzy_match_entity(company_name)
        )
        if not entity:
            continue

        # Update all SBTi-framework targets for this entity
        Targets.objects.filter(
            EntityId=entity,
            Framework=1,  # SBTi
        ).update(
            SBTiStatus=status,
            SBTiLastSyncedAt=now(),
            ValidationStatus=_map_sbti_status(status),
        )
```

**Matching strategy:**
1. Exact match on `Entities.SBTiCompanyId` (set during entity creation or manual entry).
2. Fallback: case-insensitive match on `Entities.EntityName`. Ambiguous matches are queued in a `SBTiMatchReview` admin action — never auto-applied without confidence.

**Status mapping:**

| SBTi CSV status | `Targets.ValidationStatus` |
|----------------|--------------------------|
| Committed | 2 (Submitted) |
| Targets Set | 3 (Validated) |
| Achieved | 3 (Validated) + milestone Achieved flag |
| Removed | 4 (Rejected) |

---

## 6. ECB / Open Exchange Rates — FX Conversion (Daily)

**Purpose:** Convert Scope 3 spend-based activity data from local currencies to USD before applying spend-based emission factors (which are denominated in USD).

**Primary source:** European Central Bank (ECB) — free, no API key.
```
GET https://data-api.ecb.europa.eu/service/data/EXR/D.{CURRENCY}.EUR.SP00.A
?startPeriod={date}&endPeriod={date}&format=jsondata
```

**Fallback:** Open Exchange Rates — `OPEN_EXCHANGE_RATES_API_KEY` env var.
```
GET https://openexchangerates.org/api/historical/{date}.json?app_id={key}&base=USD
```

**Cadence:** Daily at 18:00 UTC (after ECB publishes at ~16:00 CET).

### ExchangeRates table (new in migration 0027)

```
ExchangeRates
├── RateId          AutoField PK
├── FromCurrency    CharField(3)    e.g. "GBP"
├── ToCurrency      CharField(3)    e.g. "USD"
├── Rate            DecimalField    e.g. 1.2734
├── RateDate        DateField       (unique per currency pair per day)
└── Source          CharField       "ECB" | "OpenExchangeRates"
```

### FX application on EmissionsData

When `EmissionsData.Scope == 3` and `SpendCurrency != "USD"`:

```python
def _convert_spend_to_usd(amount: Decimal, currency: str, activity_date: date) -> tuple[Decimal, Decimal]:
    rate_record = ExchangeRates.objects.filter(
        FromCurrency=currency,
        ToCurrency="USD",
        RateDate__lte=activity_date,
    ).order_by("-RateDate").first()

    if not rate_record:
        raise IntegrationError(f"No FX rate for {currency}/USD on or before {activity_date}")

    usd_amount = amount * rate_record.Rate
    return usd_amount, rate_record.Rate
```

`EmissionsData` fields added in migration 0027:
- `SpendCurrency` — original currency code (ISO 4217)
- `SpendAmountLocal` — original spend in local currency
- `ExchangeRateToUSD` — rate applied (snapshot for auditability)
- `ExchangeRateDate` — date the rate was obtained
- `SpendAmountUSD` — converted amount (used as `QuantityCanonical` for spend-based EFs)

---

## 7. Verra / Gold Standard — Carbon Offset Validation (On-Demand)

**Purpose:** When a user saves an `EmissionsOffsets` record with a credit serial number, validate it against the registry to confirm it is real, not double-retired, and matches the stated project type.

### Verra (VCS)

**Registry:** `https://registry.verra.org`

Verra does not have a public REST API. Use their public project search endpoint (unofficial, subject to change):
```
GET https://registry.verra.org/app/search/VCS/All%20Projects?searchValue={project_id}
```

Alternatively, Verra CSV exports are available for bulk download. Recommended approach: daily scheduled download of the full VCS issuance table (CSV) into a local `VerraCredits` cache table, then validate on-demand against the cache.

```python
# tasks/sync_verra.py

@shared_task(name="sync_verra_registry")
def sync_verra_registry():
    """Download Verra VCS issuance table and cache locally."""
    resp = requests.get(settings.VERRA_CSV_URL, timeout=120)
    resp.raise_for_status()

    reader = csv.DictReader(StringIO(resp.text))
    for row in reader:
        VerraCredit.objects.update_or_create(
            SerialNumber=row["Serial Number"],
            defaults={
                "ProjectId": row["Project ID"],
                "ProjectName": row["Project Name"],
                "VintageYear": row["Vintage Year"],
                "Quantity": row["Quantity"],
                "RetiredAt": _parse_date(row.get("Retirement Date")),
                "RetirementBeneficiary": row.get("Retirement Beneficiary"),
                "LastSyncedAt": now(),
            }
        )
```

**On-demand validation** when `EmissionsOffsets.CreditSerialNumber` is saved:

```python
def validate_verra_credit(serial_number: str, entity_name: str) -> dict:
    credit = VerraCredit.objects.filter(SerialNumber=serial_number).first()
    if not credit:
        return {"valid": False, "reason": "Serial number not found in Verra registry"}
    if credit.RetiredAt:
        # Check if retired by this entity (legitimate) or someone else (double-counting risk)
        if entity_name.lower() not in (credit.RetirementBeneficiary or "").lower():
            return {"valid": False, "reason": "Credit retired by a different beneficiary"}
        return {"valid": True, "retired_by": credit.RetirementBeneficiary, "project": credit.ProjectName}
    return {"valid": True, "status": "issued_not_retired", "project": credit.ProjectName}
```

### Gold Standard

```
GET https://registry.goldstandard.org/projects/details/{project_id}
```

Gold Standard provides a public project registry. Credits are validated by project ID + vintage year. Similar pattern to Verra — cache project list, validate on-demand.

### Fields populated on EmissionsOffsets

From migration 0027:
- `CreditSerialNumber` — user-entered
- `RegistryValidatedAt` — timestamp of last validation call
- `RegistryValidationStatus` — `valid` | `invalid` | `pending` | `unverified`
- `RegistryProjectName` — from registry
- `RegistryProjectType` — e.g. "Avoided Deforestation (REDD+)"
- `RegistryVintageYear` — year emissions were reduced/removed
- `RegistryRetirementBeneficiary` — confirms credits retired in entity's name

**Unverified credits are not deducted from `GHGInventories.NetEmissions`** until `RegistryValidationStatus = valid`.

---

## 8. GBIF — Species Identification (On-Demand)

**Purpose:** When users enter a tree species by common name, look up the accepted scientific name, taxonomy, and IUCN status to populate the `Species` model correctly and enable IPCC parameter lookup.

**Docs:** `https://www.gbif.org/developer/species`

**Auth:** None for read endpoints.

### Species search

```
GET https://api.gbif.org/v1/species/suggest?q={common_name}&limit=5
```

Response:
```json
[{
  "key": 5284517,
  "canonicalName": "Shorea robusta",
  "vernacularNames": [{"vernacularName": "Sal", "language": "eng"}],
  "kingdom": "Plantae",
  "family": "Dipterocarpaceae",
  "taxonomicStatus": "ACCEPTED",
  "rank": "SPECIES"
}]
```

### IUCN Red List

```
GET https://apiv3.iucnredlist.org/api/v3/species/{scientific_name}?token={IUCN_API_KEY}
```

Response includes conservation status: `LC`, `NT`, `VU`, `EN`, `CR`, `EW`, `EX`.

### Integration flow

1. User types species common name in the frontend.
2. Frontend calls `GET /api/integrations/species/search/?q={name}`.
3. Backend calls GBIF suggest endpoint, returns top 5 matches.
4. User selects match — scientific name, family, and taxonomy auto-fill.
5. On confirm, backend calls IUCN Red List for conservation status.
6. `Species` record saved with `GBIFKey`, `ScientificName`, `IUCNStatus`, `IUCNSyncedAt`.

```python
# services/integrations/gbif.py

def search_species(query: str) -> list[dict]:
    resp = requests.get(
        "https://api.gbif.org/v1/species/suggest",
        params={"q": query, "limit": 5, "rank": "SPECIES"},
        timeout=8,
    )
    resp.raise_for_status()
    return [
        {
            "GBIFKey": r["key"],
            "ScientificName": r.get("canonicalName"),
            "Family": r.get("family"),
            "Kingdom": r.get("kingdom"),
        }
        for r in resp.json()
        if r.get("taxonomicStatus") == "ACCEPTED"
    ]

def get_iucn_status(scientific_name: str) -> str | None:
    resp = requests.get(
        f"https://apiv3.iucnredlist.org/api/v3/species/{scientific_name}",
        params={"token": settings.IUCN_API_KEY},
        timeout=8,
    )
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    results = resp.json().get("result", [])
    return results[0].get("category") if results else None
```

---

## 9. API Endpoint Additions

These endpoints expose the integrations to the frontend:

```
# Entity auto-population
POST /api/integrations/companies-house/search/
     Body: { "query": "Example Ltd" }
     Returns: [{ "company_number", "company_name", "address", ... }]

POST /api/integrations/companies-house/populate/
     Body: { "company_number": "12345678" }
     Returns: populated entity fields (not saved — user confirms)

# Species search
GET  /api/integrations/species/search/?q={common_name}
     Returns: [{ "GBIFKey", "ScientificName", "Family" }]

# Emission factor search
GET  /api/integrations/emission-factors/search/?q={activity}&region={ISO2}&year={year}
     Returns: [{ "ClimatiqActivityId", "name", "TotalKgCO2ePerUnit", "source" }]

POST /api/integrations/emission-factors/import/
     Body: { "climatiq_activity_id": "...", "region": "GB", "year": 2024 }
     Returns: created EmissionFactors record

# Offset validation
POST /api/integrations/offsets/validate/
     Body: { "serial_number": "VCS-1234-...", "registry": "verra" }
     Returns: { "valid": true, "project_name", "vintage_year", "retired_by" }

# FX rate lookup
GET  /api/integrations/fx/?currency=GBP&date=2024-01-15
     Returns: { "rate": 1.2734, "date": "2024-01-15", "source": "ECB" }
```

All integration endpoints require authentication. Rate limiting: 60 calls/minute per user.

---

## 10. Error Handling

All integration service functions follow this pattern:

```python
class IntegrationError(Exception):
    """Raised when an external API call fails non-transiently."""
    pass

class IntegrationUnavailable(Exception):
    """Raised when an external API is unreachable (network, 5xx). Retry eligible."""
    pass
```

- **4xx (client error):** Raise `IntegrationError`. Do not retry. Log and surface to user: "Could not find company — check registration number."
- **5xx / timeout:** Raise `IntegrationUnavailable`. Celery retries with exponential backoff (max 3 retries, 60s → 300s → 900s delay).
- **Rate limit (429):** Catch and retry after `Retry-After` header value.
- **All failures:** Log to `AuditLog` with `Action=system_integration_error`, `TableName=<service_name>`, `NewValues={"error": ..., "url": ...}`.

Scheduled tasks that fail send an alert via `Notifications` (type `system_error`) to all users with SuperAdmin role.

---

## 11. Environment Variables

Add to `.env.example`:

```bash
# Climatiq
CLIMATIQ_API_KEY=

# Companies House (UK)
COMPANIES_HOUSE_API_KEY=

# OpenCorporates (non-UK entity lookup)
OPENCORPORATES_API_KEY=

# Open Exchange Rates (FX fallback)
OPEN_EXCHANGE_RATES_API_KEY=

# SBTi Companies CSV URL (update annually)
SBTI_COMPANIES_CSV_URL=https://...

# DEFRA EF spreadsheet URL (update annually each April)
DEFRA_EF_SPREADSHEET_URL=https://...

# Verra VCS issuance CSV URL
VERRA_CSV_URL=https://registry.verra.org/...

# IUCN Red List
IUCN_API_KEY=

# EPA eGRID Excel URL (update annually)
EPA_EGRID_URL=https://www.epa.gov/system/files/documents/...
```

---

## 12. Privacy and Data Handling

- No personal data is sent to external APIs. Queries use company names, registration numbers, activity types, and species names only.
- FX rates, DEFRA EFs, and GBIF data are public and can be cached indefinitely.
- Verra/Gold Standard credit data is public registry information — safe to cache.
- Companies House data is publicly registered — safe to cache and display.
- Climatiq is a paid data service — do not expose raw API responses to unauthenticated endpoints.
