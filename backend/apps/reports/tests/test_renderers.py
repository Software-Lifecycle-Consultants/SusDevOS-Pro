"""
Unit tests for report rendering (apps/reports/renderers.py) — the pass that
replaced JSON-for-every-format with real CSV/PDF and wired up the previously
placeholder phase_progress / tree_log reports.

The renderer's job object only needs EntityId_id / Parameters / ReportType, so a
SimpleNamespace stands in for a ReportJobs row.
"""
import json
from decimal import Decimal
from types import SimpleNamespace

import pytest

pytestmark = pytest.mark.django_db


def _job(entity, report_type, fmt="csv", params=None):
    return SimpleNamespace(
        EntityId_id=entity.EntityId, Parameters=params or {},
        ReportType=report_type, Format=fmt,
    )


def _emission(entity, gwp_dataset):
    from apps.emissions.models import EmissionsData
    return EmissionsData.objects.create(
        EntityId=entity, Title="Diesel", Scope=1,
        QuantityOrCost=Decimal("100"), Unit="litres",
        EmissionFactor=Decimal("2.639"), EmissionFactorSource="DEFRA 2024",
        Gas="CO2", GwpDatasetId=gwp_dataset,
    )


def test_emissions_summary_data_and_csv(entity, gwp_dataset):
    from apps.reports.renderers import build_report_data, render_csv, render_json

    _emission(entity, gwp_dataset)
    data = build_report_data(_job(entity, "emissions_summary"))

    assert data["title"] == "Emissions Summary"
    assert len(data["sections"]) == 1
    assert len(data["sections"][0]["rows"]) == 1

    csv_bytes = render_csv(data)
    assert b"Emissions Summary" in csv_bytes
    assert b"Scope" in csv_bytes            # header row present
    assert b"Diesel" in csv_bytes          # data row present

    parsed = json.loads(render_json(data))
    assert parsed["title"] == "Emissions Summary"


def test_tree_log_has_two_sections(entity, gwp_dataset):
    from apps.restorations.models import Restorations, TreeRemovals
    from apps.reports.renderers import build_report_data

    TreeRemovals.objects.create(EntityId=entity, TotalTreesRemoved=5)
    Restorations.objects.create(EntityId=entity, RestorationName="Replant A")

    data = build_report_data(_job(entity, "tree_log"))
    assert data["title"] == "Tree Removal & Restoration Log"
    headings = [s["heading"] for s in data["sections"]]
    assert len(data["sections"]) == 2
    assert any("removal" in h.lower() for h in headings)
    assert any("restoration" in h.lower() for h in headings)


def test_phase_progress_renders(entity):
    from apps.reports.renderers import build_report_data, render_csv

    data = build_report_data(_job(entity, "phase_progress"))
    assert data["title"] == "Phase Progress vs Goals"
    # Empty project set still produces a valid (header-only) CSV, not JSON.
    csv_bytes = render_csv(data)
    assert b"Phase Progress vs Goals" in csv_bytes


def test_html_renders_title_and_headers(entity, gwp_dataset):
    from apps.reports.renderers import build_report_data, _html

    _emission(entity, gwp_dataset)
    html = _html(build_report_data(_job(entity, "emissions_summary")))
    assert "<table>" in html
    assert "Emissions Summary" in html
    assert "Scope" in html


def test_pdf_render_smoke(entity, gwp_dataset):
    """Real PDF bytes when weasyprint + its system libs are present; skip otherwise."""
    pytest.importorskip("weasyprint")
    from apps.reports.renderers import build_report_data, render

    _emission(entity, gwp_dataset)
    data = build_report_data(_job(entity, "emissions_summary", fmt="pdf"))
    try:
        pdf = render(data, "pdf")
    except OSError as exc:                  # pango/cairo not installed in the image
        pytest.skip(f"weasyprint system libraries unavailable: {exc}")
    assert pdf[:4] == b"%PDF"
