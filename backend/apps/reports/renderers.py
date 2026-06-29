"""
Report data-gathering and rendering.

Each report type is gathered into a uniform structure::

    {
      "title": str,
      "subtitle": str,
      "generated_at": iso str,
      "sections": [ {"heading": str, "columns": [str], "rows": [[cell, ...]]} ],
    }

which is then rendered to JSON, CSV (stdlib), or PDF (weasyprint HTML→PDF).
This replaces the previous behaviour where every format dumped raw JSON.
"""
import csv
import io
import json
from decimal import Decimal

from django.utils.html import escape
from django.utils.timezone import now

VERIFICATION_LABELS = {1: "Unverified", 2: "Pending", 3: "Verified (1st party)", 4: "Verified (3rd party)"}


# ── Data gathering ──────────────────────────────────────────────────────────────

def build_report_data(job) -> dict:
    entity_id = job.EntityId_id
    params = job.Parameters or {}
    builder = {
        "emissions_summary": _emissions_summary,
        "ghg_inventory": _ghg_inventory,
        "phase_progress": _phase_progress,
        "tree_log": _tree_log,
    }.get(job.ReportType)

    if builder is None:
        sections = [{"heading": "Unsupported", "columns": ["Message"],
                     "rows": [[f"Unknown report type '{job.ReportType}'"]]}]
        return _envelope(f"Report: {job.ReportType}", entity_id, sections)

    return builder(entity_id, params)


def _envelope(title, entity_id, sections, subtitle=""):
    return {
        "title": title,
        "subtitle": subtitle,
        "entity_id": entity_id,
        "generated_at": now().isoformat(),
        "sections": sections,
    }


def _emissions_summary(entity_id, params):
    from apps.emissions.models import EmissionsData

    qs = EmissionsData.objects.filter(EntityId_id=entity_id, Status__lt=4)
    if params.get("project_id"):
        qs = qs.filter(ProjectId_id=params["project_id"])
    if params.get("reporting_year"):
        qs = qs.filter(ReportingYear=params["reporting_year"])

    rows = []
    for r in qs.values("Title", "Scope", "Gas", "EmissionsAmountTonnes",
                       "ReportingYear", "VerificationStatus"):
        rows.append([
            r["Title"], r["Scope"], r["Gas"],
            _num(r["EmissionsAmountTonnes"]), r["ReportingYear"],
            VERIFICATION_LABELS.get(r["VerificationStatus"], r["VerificationStatus"]),
        ])
    sections = [{
        "heading": "Emissions records (tCO₂e)",
        "columns": ["Title", "Scope", "Gas", "Amount (tCO₂e)", "Year", "Verification"],
        "rows": rows,
    }]
    return _envelope("Emissions Summary", entity_id, sections,
                     subtitle=f"{len(rows)} record(s)")


def _ghg_inventory(entity_id, params):
    from apps.emissions.models import GHGInventories

    qs = GHGInventories.objects.filter(EntityId_id=entity_id)
    if params.get("reporting_year"):
        qs = qs.filter(ReportingYear=params["reporting_year"])

    rows = []
    for i in qs.values("ReportingYear", "TotalScope1Tonnes", "TotalScope2LocationTonnes",
                       "TotalScope2MarketTonnes", "TotalScope3Tonnes",
                       "TotalOffsetsTonnes", "NetEmissionsTonnes", "VerificationStatus"):
        rows.append([
            i["ReportingYear"], _num(i["TotalScope1Tonnes"]),
            _num(i["TotalScope2LocationTonnes"]), _num(i["TotalScope2MarketTonnes"]),
            _num(i["TotalScope3Tonnes"]), _num(i["TotalOffsetsTonnes"]),
            _num(i["NetEmissionsTonnes"]),
            VERIFICATION_LABELS.get(i["VerificationStatus"], i["VerificationStatus"]),
        ])
    sections = [{
        "heading": "GHG inventories (tCO₂e)",
        "columns": ["Year", "Scope 1", "Scope 2 (LB)", "Scope 2 (MB)", "Scope 3",
                    "Offsets", "Net", "Verification"],
        "rows": rows,
    }]
    return _envelope("GHG Inventory", entity_id, sections, subtitle=f"{len(rows)} inventory year(s)")


def _phase_progress(entity_id, params):
    from django.db.models import Sum
    from apps.emissions.models import EmissionsData
    from apps.projects.models import ProjectPhases

    qs = ProjectPhases.objects.filter(EntityId_id=entity_id, Status__lt=4).select_related("ProjectId")
    if params.get("project_id"):
        qs = qs.filter(ProjectId_id=params["project_id"])

    rows = []
    for phase in qs.order_by("ProjectId", "PhaseNumber"):
        actual = EmissionsData.objects.filter(
            PhaseId=phase, Status__lt=4
        ).aggregate(t=Sum("EmissionsAmountTonnes"))["t"] or Decimal("0")
        target = phase.TargetEmissionsTonnes
        variance = (actual - target) if target is not None else None
        rows.append([
            phase.ProjectId.ProjectName, phase.PhaseName, phase.PhaseNumber,
            _date(phase.StartDate), _date(phase.EndDate),
            _num(target), _num(actual), _num(variance),
        ])
    sections = [{
        "heading": "Phase progress vs target (tCO₂e)",
        "columns": ["Project", "Phase", "#", "Start", "End",
                    "Target", "Actual", "Variance"],
        "rows": rows,
    }]
    return _envelope("Phase Progress vs Goals", entity_id, sections,
                     subtitle=f"{len(rows)} phase(s)")


def _tree_log(entity_id, params):
    from apps.restorations.models import Restorations, TreeRemovals

    removals = TreeRemovals.objects.filter(EntityId_id=entity_id, Status__lt=4)
    restorations = Restorations.objects.filter(EntityId_id=entity_id, Status__lt=4)

    removal_rows = [[
        r.RemovalReference or f"#{r.TreeRemovalId}", _date(r.RemovalDate),
        r.TotalTreesRemoved, _num(r.TotalBiomassCarbon),
        "yes" if r.HasMitigationPlan else "no",
    ] for r in removals]

    restoration_rows = [[
        r.RestorationName, _date(r.StartDate), _date(r.CompletionDate),
        r.TotalTreesPlanted, _num(r.TotalAreaHectares),
        _num(r.EstimatedCarbonSequestrationTonnes),
    ] for r in restorations]

    sections = [
        {
            "heading": "Tree removals (biogenic carbon loss, tCO₂e)",
            "columns": ["Reference", "Date", "Trees removed", "Carbon (tCO₂e)", "Mitigation plan"],
            "rows": removal_rows,
        },
        {
            "heading": "Restorations (sequestration, tCO₂e)",
            "columns": ["Name", "Start", "Completion", "Trees planted", "Area (ha)", "Sequestration (tCO₂e)"],
            "rows": restoration_rows,
        },
    ]
    return _envelope("Tree Removal & Restoration Log", entity_id, sections,
                     subtitle=f"{len(removal_rows)} removal(s), {len(restoration_rows)} restoration(s)")


def _num(value):
    if value is None:
        return ""
    return str(value)


def _date(value):
    return value.isoformat() if value else ""


# ── Rendering ───────────────────────────────────────────────────────────────────

def render(data: dict, fmt: str) -> bytes:
    if fmt == "csv":
        return render_csv(data)
    if fmt == "pdf":
        return render_pdf(data)
    return render_json(data)


def render_json(data: dict) -> bytes:
    return json.dumps(data, default=str, indent=2).encode("utf-8")


def render_csv(data: dict) -> bytes:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([data["title"]])
    if data.get("subtitle"):
        writer.writerow([data["subtitle"]])
    writer.writerow([f"Generated: {data['generated_at']}"])
    for section in data["sections"]:
        writer.writerow([])
        writer.writerow([section["heading"]])
        writer.writerow(section["columns"])
        for row in section["rows"]:
            writer.writerow(row)
    return buf.getvalue().encode("utf-8")


def render_pdf(data: dict) -> bytes:
    from weasyprint import HTML
    return HTML(string=_html(data)).write_pdf()


def _html(data: dict) -> str:
    sections_html = []
    for section in data["sections"]:
        head = "".join(f"<th>{escape(str(c))}</th>" for c in section["columns"])
        if section["rows"]:
            body = "".join(
                "<tr>" + "".join(f"<td>{escape(str(cell))}</td>" for cell in row) + "</tr>"
                for row in section["rows"]
            )
        else:
            body = f'<tr><td colspan="{len(section["columns"])}" class="empty">No data</td></tr>'
        sections_html.append(
            f"<h2>{escape(section['heading'])}</h2>"
            f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"
        )

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
  @page {{ size: A4; margin: 1.8cm; }}
  body {{ font-family: 'Helvetica Neue', Arial, sans-serif; color: #1a1a1a; font-size: 11px; }}
  h1 {{ font-size: 20px; margin: 0 0 2px; }}
  .subtitle {{ color: #555; margin: 0 0 2px; }}
  .meta {{ color: #888; font-size: 9px; margin: 0 0 16px; }}
  h2 {{ font-size: 13px; margin: 18px 0 6px; border-bottom: 2px solid #2e7d32; padding-bottom: 3px; }}
  table {{ width: 100%; border-collapse: collapse; }}
  th {{ background: #2e7d32; color: #fff; text-align: left; padding: 5px 7px; font-size: 10px; }}
  td {{ padding: 4px 7px; border-bottom: 1px solid #e0e0e0; }}
  tr:nth-child(even) td {{ background: #f6f8f6; }}
  td.empty {{ color: #999; font-style: italic; text-align: center; }}
</style></head><body>
  <h1>{escape(data['title'])}</h1>
  <p class="subtitle">{escape(data.get('subtitle', ''))}</p>
  <p class="meta">Generated {escape(data['generated_at'])} · SusDevOS</p>
  {''.join(sections_html)}
</body></html>"""
