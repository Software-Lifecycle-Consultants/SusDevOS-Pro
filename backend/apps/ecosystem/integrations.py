"""
Biodiversity reference-data integrations for the Species model (TNFD-aligned).

GBIF (Global Biodiversity Information Facility) — taxonomy + accepted scientific
names. No auth required. IUCN Red List — conservation status; requires
IUCN_API_KEY.

All functions are defensive: network/parse failures return empty results or
None rather than raising into the request path, so species creation never
breaks because an external service is down.
"""
import logging

from django.conf import settings

import requests

logger = logging.getLogger(__name__)

GBIF_SUGGEST = "https://api.gbif.org/v1/species/suggest"
IUCN_BASE = "https://apiv3.iucnredlist.org/api/v3/species"
TIMEOUT = 8

# IUCN categories we store (matches Species.IUCN_STATUS_CHOICES).
_VALID_IUCN = {"LC", "NT", "VU", "EN", "CR", "EW", "EX", "DD", "NE"}


def search_species(query: str, limit: int = 5) -> list[dict]:
    """
    Look up accepted species matches by common or scientific name via GBIF.
    Returns a list of {GBIFKey, ScientificName, Family, Kingdom, CommonName}.
    Empty list on any failure.
    """
    query = (query or "").strip()
    if not query:
        return []
    try:
        resp = requests.get(
            GBIF_SUGGEST,
            params={"q": query, "limit": limit, "rank": "SPECIES"},
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        rows = resp.json()
    except (requests.RequestException, ValueError) as exc:
        logger.warning("GBIF search failed for %r: %s", query, exc)
        return []

    matches = []
    for r in rows:
        if r.get("taxonomicStatus") != "ACCEPTED":
            continue
        matches.append({
            "GBIFKey": r.get("key"),
            "ScientificName": r.get("canonicalName") or r.get("scientificName"),
            "Family": r.get("family"),
            "Kingdom": r.get("kingdom"),
            "CommonName": _first_vernacular(r),
        })
    return matches


def _first_vernacular(row) -> str | None:
    for v in row.get("vernacularNames", []) or []:
        if v.get("language") in (None, "eng", "en"):
            return v.get("vernacularName")
    names = row.get("vernacularNames") or []
    return names[0].get("vernacularName") if names else None


def get_iucn_status(scientific_name: str) -> str | None:
    """
    Fetch IUCN Red List conservation status code for a scientific name.
    Returns a code from _VALID_IUCN, or None (not found / not configured / error).
    """
    scientific_name = (scientific_name or "").strip()
    if not scientific_name:
        return None
    api_key = getattr(settings, "IUCN_API_KEY", "")
    if not api_key:
        logger.info("IUCN_API_KEY not set — skipping Red List lookup for %r", scientific_name)
        return None
    try:
        resp = requests.get(
            f"{IUCN_BASE}/{requests.utils.quote(scientific_name)}",
            params={"token": api_key},
            timeout=TIMEOUT,
        )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        results = resp.json().get("result", [])
    except (requests.RequestException, ValueError) as exc:
        logger.warning("IUCN lookup failed for %r: %s", scientific_name, exc)
        return None

    if not results:
        return None
    category = (results[0].get("category") or "").upper()
    return category if category in _VALID_IUCN else None


def enrich_species(species) -> bool:
    """
    Best-effort: fill ScientificName/Family/Kingdom from GBIF (if a key or name
    is available) and IUCNStatus from the Red List, only for fields the user
    left blank. Mutates and saves the species. Returns True if anything changed.

    Safe to call from the create path — never raises.
    """
    from django.utils.timezone import now

    changed_fields = []

    # Resolve taxonomy from GBIF when scientific name is missing but we have a name to search.
    if not species.ScientificName:
        matches = search_species(species.ScientificName or species.CommonName, limit=1)
        if matches:
            m = matches[0]
            if m.get("ScientificName"):
                species.ScientificName = m["ScientificName"]; changed_fields.append("ScientificName")
            if m.get("GBIFKey") and not species.GBIFKey:
                species.GBIFKey = m["GBIFKey"]; changed_fields.append("GBIFKey")
            if m.get("Family") and not species.Family:
                species.Family = m["Family"]; changed_fields.append("Family")
            if m.get("Kingdom") and not species.Kingdom:
                species.Kingdom = m["Kingdom"]; changed_fields.append("Kingdom")

    # Conservation status from IUCN when we have a scientific name and no status yet.
    if species.ScientificName and not species.IUCNStatus:
        status = get_iucn_status(species.ScientificName)
        if status:
            species.IUCNStatus = status
            species.IUCNSyncedAt = now()
            changed_fields += ["IUCNStatus", "IUCNSyncedAt"]

    if changed_fields:
        species.save(update_fields=changed_fields)
        return True
    return False
