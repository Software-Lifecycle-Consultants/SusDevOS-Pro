"""
Tests for the DEFRA emission-factor importer.

Every test builds its own workbook in memory, so the suite never touches GOV.UK.
The layout mirrors the published flat file: a title block, a header row starting
with "ID", then data.
"""
import io
from decimal import Decimal
from unittest.mock import patch

import openpyxl
import pytest
import requests

from tasks.integrations.defra import (
    DefraImportError,
    import_factors,
    parse_flat_file,
    resolve_flat_file_url,
)

HEADER = [
    "ID", "Scope", "Level 1", "Level 2", "Level 3", "Level 4",
    "Column Text", "UOM", "GHG/Unit", "GHG Conversion Factor 2026",
]


def _workbook(rows, *, sheet="Factors by Category", header=None):
    """A flat file containing `rows`, returned as bytes."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = sheet
    ws.append(["UK Government GHG Conversion Factors"])
    ws.append([sheet])
    ws.append([])
    ws.append(header if header is not None else HEADER)
    for row in rows:
        ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _row(id_, scope, l1, l2, l3, uom, ghg_unit, value, l4="", column_text=""):
    return [id_, scope, l1, l2, l3, l4, column_text, uom, ghg_unit, value]


# ── Parsing ──────────────────────────────────────────────────────────────────


class TestParseFlatFile:
    def test_keeps_only_the_aggregate_co2e_rows(self):
        content = _workbook([
            _row("1", "Scope 1", "Fuels", "Gaseous fuels", "Butane", "litres", "kg CO2e", "1.74533"),
            _row("2", "Scope 1", "Fuels", "Gaseous fuels", "Butane", "litres", "kg CO2e of CO2 per unit", "1.74296"),
            _row("3", "Scope 1", "Fuels", "Gaseous fuels", "Butane", "litres", "kg CO2e of CH4 per unit", "0.00144"),
        ])
        rows = parse_flat_file(content)

        assert len(rows) == 1, "the per-gas breakdown rows must not become separate factors"
        assert rows[0]["value"] == Decimal("1.74533")

    def test_skips_rows_with_no_ghg_protocol_scope(self):
        content = _workbook([
            _row("1", "Scope 1", "Fuels", "Gaseous fuels", "Butane", "litres", "kg CO2e", "1.7"),
            _row("2", "Outside of scopes", "Bioenergy", "Biofuel", "Biodiesel", "litres", "kg CO2e", "0.03"),
        ])
        rows = parse_flat_file(content)

        assert [r["scope"] for r in rows] == [1]

    def test_builds_a_searchable_activity_name_and_category(self):
        content = _workbook([
            _row("1", "Scope 3", "Business travel- air", "Flights", "Domestic, to/from UK",
                 "passenger.km", "kg CO2e", "0.13552", column_text="Average passenger"),
        ])
        rows = parse_flat_file(content)

        assert rows[0]["category"] == "Business travel- air"
        assert rows[0]["name"] == "Flights - Domestic, to/from UK - Average passenger"

    def test_unparseable_value_is_skipped_not_fatal(self):
        content = _workbook([
            _row("1", "Scope 1", "Fuels", "Gaseous fuels", "Butane", "litres", "kg CO2e", "n/a"),
            _row("2", "Scope 1", "Fuels", "Gaseous fuels", "Propane", "litres", "kg CO2e", "1.5"),
        ])
        rows = parse_flat_file(content)

        assert len(rows) == 1
        assert rows[0]["name"] == "Gaseous fuels - Propane"

    def test_missing_data_sheet_is_an_error(self):
        content = _workbook([], sheet="Something Else")
        with pytest.raises(DefraImportError, match="not found"):
            parse_flat_file(content)

    def test_changed_columns_are_an_error_not_a_silent_misread(self):
        """Importing the wrong column would be worse than importing nothing."""
        wrong = list(HEADER)
        wrong[7] = "Units"
        content = _workbook([], header=wrong)

        with pytest.raises(DefraImportError, match="columns have changed"):
            parse_flat_file(content)

    def test_value_column_is_matched_by_prefix_so_the_year_can_change(self):
        header = list(HEADER)
        header[9] = "GHG Conversion Factor 2027"
        content = _workbook(
            [_row("1", "Scope 1", "Fuels", "Gaseous fuels", "Butane", "litres", "kg CO2e", "1.7")],
            header=header,
        )
        assert len(parse_flat_file(content)) == 1

    def test_a_value_column_that_is_not_a_factor_is_an_error(self):
        header = list(HEADER)
        header[9] = "Some Other Column"
        content = _workbook([], header=header)

        with pytest.raises(DefraImportError, match="GHG Conversion Factor"):
            parse_flat_file(content)


# ── Source resolution ────────────────────────────────────────────────────────


class TestResolveFlatFileUrl:
    @staticmethod
    def _api(attachments):
        class _Resp:
            def raise_for_status(self):
                pass

            def json(self):
                return {"details": {"attachments": attachments}}

        return _Resp()

    def test_picks_the_flat_file_not_the_full_workbook(self):
        attachments = [
            {"title": "Conversion factors 2026: full set (for all users)", "url": "https://x/full-set.xlsx"},
            {"title": "Conversion factors 2026: flat file (for automatic processing only)",
             "url": "https://x/flat-format.xlsx"},
            {"title": "Conversion factors 2026: methodology", "url": "https://x/method.pdf"},
        ]
        with patch("tasks.integrations.defra.requests.get", return_value=self._api(attachments)):
            assert resolve_flat_file_url(2026) == "https://x/flat-format.xlsx"

    def test_missing_flat_file_names_what_was_published(self):
        attachments = [{"title": "Conversion factors 2099: full set", "url": "https://x/full.xlsx"}]
        with patch("tasks.integrations.defra.requests.get", return_value=self._api(attachments)):
            with pytest.raises(DefraImportError, match="full set"):
                resolve_flat_file_url(2099)

    def test_network_failure_is_a_clear_error(self):
        with patch("tasks.integrations.defra.requests.get",
                   side_effect=requests.ConnectionError("down")):
            with pytest.raises(DefraImportError, match="content API"):
                resolve_flat_file_url(2026)


# ── Import ───────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestImportFactors:
    @pytest.fixture(autouse=True)
    def _units(self):
        from django.core.management import call_command

        call_command("seed_units")

    @staticmethod
    def _rows():
        return parse_flat_file(_workbook([
            _row("1", "Scope 1", "Fuels", "Gaseous fuels", "Butane", "litres", "kg CO2e", "1.74533"),
            _row("2", "Scope 2", "UK electricity", "Electricity generated", "Electricity: UK",
                 "kWh", "kg CO2e", "0.13096"),
        ]))

    def test_creates_a_set_and_its_factors(self):
        from apps.emissions.models import EmissionFactors, EmissionFactorSets

        result = import_factors(rows=self._rows(), year=2026)

        assert result["created"] == 2
        assert EmissionFactorSets.objects.get(SetName="DEFRA 2026").ApplicableYear == 2026
        assert EmissionFactors.objects.count() == 2

    def test_links_the_unit_so_the_picker_can_show_it(self):
        from apps.emissions.models import EmissionFactors

        import_factors(rows=self._rows(), year=2026)
        butane = EmissionFactors.objects.get(ActivityName="Gaseous fuels - Butane")

        assert butane.InputUnitId is not None
        assert butane.InputUnitId.UnitName == "litres"
        assert butane.FactorValue == Decimal("1.74533000")

    def test_rerunning_updates_in_place(self):
        from apps.emissions.models import EmissionFactors

        import_factors(rows=self._rows(), year=2026)
        result = import_factors(rows=self._rows(), year=2026)

        assert result["created"] == 0
        assert result["updated"] == 2
        assert EmissionFactors.objects.count() == 2

    def test_level_1_distinguishes_direct_from_well_to_tank(self):
        """Regression: these differ only in Level 1 and were collapsing into one.

        'Fuels' is direct combustion and 'WTT- fuels' is the upstream well-to-tank
        factor for the very same fuel. Folding them together silently served one
        value under the other's name.
        """
        from apps.emissions.models import EmissionFactors

        rows = parse_flat_file(_workbook([
            _row("1", "Scope 1", "Fuels", "Gaseous fuels", "Butane", "litres", "kg CO2e", "1.74533"),
            _row("2", "Scope 3", "WTT- fuels", "Gaseous fuels", "Butane", "litres", "kg CO2e", "0.30363"),
        ]))
        import_factors(rows=rows, year=2026)

        stored = EmissionFactors.objects.filter(ActivityName="Gaseous fuels - Butane")
        assert stored.count() == 2
        assert {f.ActivityCategory for f in stored} == {"Fuels", "WTT- fuels"}
        assert stored.get(ActivityCategory="Fuels").FactorValue == Decimal("1.74533000")

    def test_never_sets_climatiq_activity_id(self):
        """The Climatiq sync overwrites any row carrying one — DEFRA rows must not."""
        from apps.emissions.models import EmissionFactors

        import_factors(rows=self._rows(), year=2026)

        assert EmissionFactors.objects.exclude(ClimatiqActivityId="").count() == 0

    def test_a_unit_missing_from_the_table_stops_the_import(self):
        from apps.emissions.models import Units

        Units.objects.filter(UnitName="litres").delete()

        with pytest.raises(DefraImportError, match="seed_units"):
            import_factors(rows=self._rows(), year=2026)

    def test_refuses_to_import_nothing(self):
        with pytest.raises(DefraImportError, match="empty"):
            import_factors(rows=[], year=2026)
