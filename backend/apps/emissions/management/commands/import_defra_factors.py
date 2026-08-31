"""
Management command: import_defra_factors

Populates EmissionFactors from the DEFRA / DESNZ UK Government GHG conversion
factors. Without this the library is empty, the factor picker returns nothing,
and the emissions form blocks submission — which is exactly how production
shipped.

Run `seed_units` first; the importer refuses to run if a unit in the file has no
Units row, rather than silently dropping those factors.

Usage:
    python manage.py import_defra_factors                 # latest known year, resolved from GOV.UK
    python manage.py import_defra_factors --year 2026
    python manage.py import_defra_factors --file ./ghg-conversion-factors-2026-flat-format.xlsx
    python manage.py import_defra_factors --url https://.../flat-format.xlsx
    python manage.py import_defra_factors --dry-run       # parse and report, write nothing

Data is published under the Open Government Licence v3.0. Attribution is carried
on the EmissionFactorSets row (SetName "DEFRA <year>", Publisher "DEFRA / DESNZ").
"""
from django.core.management.base import BaseCommand, CommandError

DEFAULT_YEAR = 2026


class Command(BaseCommand):
    help = "Import the DEFRA/DESNZ UK Government GHG conversion factors into EmissionFactors."

    def add_arguments(self, parser):
        parser.add_argument(
            "--year", type=int, default=DEFAULT_YEAR,
            help=f"Conversion-factor edition to import (default {DEFAULT_YEAR}).",
        )
        parser.add_argument("--url", default="", help="Explicit flat-file URL, bypassing GOV.UK lookup.")
        parser.add_argument("--file", default="", help="Local flat-file path, for offline or pinned imports.")
        parser.add_argument(
            "--dry-run", action="store_true",
            help="Parse and report what would be imported without writing.",
        )
        parser.add_argument(
            "--if-empty", action="store_true",
            help=(
                "Do nothing if any factors already exist. For the deploy pipeline: "
                "guarantees the library is never empty without putting GOV.UK in the "
                "deploy path on every release."
            ),
        )

    def handle(self, *args, **options):
        from django.conf import settings

        from apps.emissions.models import EmissionFactors
        from tasks.integrations.defra import (
            DefraImportError,
            download,
            import_factors,
            parse_flat_file,
            resolve_flat_file_url,
        )

        year = options["year"]
        path = options["file"]
        url = options["url"]

        # Checked before any network call, which is the whole point: a deploy of
        # an already-populated instance must not depend on GOV.UK being up.
        if options["if_empty"] and EmissionFactors.objects.exists():
            self.stdout.write(
                f"Factor library already populated "
                f"({EmissionFactors.objects.count()} factors) — nothing to do."
            )
            return

        try:
            if path:
                self.stdout.write(f"Reading {path}")
                with open(path, "rb") as handle:
                    content = handle.read()
                source = path
            else:
                source = url or getattr(settings, "DEFRA_EF_SPREADSHEET_URL", "")
                if not source:
                    self.stdout.write(f"Resolving the {year} flat file from GOV.UK…")
                    source = resolve_flat_file_url(year)
                self.stdout.write(f"Downloading {source}")
                content = download(source)

            rows = parse_flat_file(content)
        except DefraImportError as exc:
            raise CommandError(str(exc)) from exc
        except OSError as exc:
            raise CommandError(f"Could not read {path}: {exc}") from exc

        self.stdout.write(f"Parsed {len(rows)} aggregate CO2e factors from {source}")

        if options["dry_run"]:
            by_scope: dict[int, int] = {}
            for row in rows:
                by_scope[row["scope"]] = by_scope.get(row["scope"], 0) + 1
            for scope in sorted(by_scope):
                self.stdout.write(f"  Scope {scope}: {by_scope[scope]}")
            self.stdout.write(self.style.WARNING("Dry run — nothing written."))
            return

        try:
            result = import_factors(rows=rows, year=year)
        except DefraImportError as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(self.style.SUCCESS(
            f"{result['set']}: {result['created']} created, {result['updated']} updated "
            f"({result['total']} parsed)."
        ))
