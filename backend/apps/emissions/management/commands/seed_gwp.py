"""
Management command: seed_gwp

Seeds the IPCC AR6 GWP100 dataset as the system default.
Safe to run multiple times — uses get_or_create.

Usage:
    python manage.py seed_gwp
"""
from django.core.management.base import BaseCommand

GWP_VALUES = [
    ("CO2",      "",          "1.0000"),
    ("CH4",      "fossil",    "29.8000"),
    ("CH4",      "biogenic",  "27.9000"),
    ("N2O",      "",          "273.0000"),
    ("SF6",      "",          "25200.0000"),
    ("NF3",      "",          "17400.0000"),
    ("HFC-23",   "",          "14800.0000"),
    ("HFC-32",   "",          "771.0000"),
    ("HFC-125",  "",          "3740.0000"),
    ("HFC-134a", "",          "1530.0000"),
    ("HFC-143a", "",          "5810.0000"),
    ("HFC-152a", "",          "164.0000"),
    ("HFC-227ea","",          "3600.0000"),
    ("HFC-236fa","",          "8690.0000"),
    ("HFC-245fa","",          "962.0000"),
]


class Command(BaseCommand):
    help = "Seed IPCC AR6 GWP100 dataset as the system default GWP dataset"

    def handle(self, *args, **options):
        from apps.emissions.models import GwpDatasets, GwpValues

        dataset, created = GwpDatasets.objects.get_or_create(
            Version="AR6",
            Horizon=100,
            defaults={
                "Name":          "IPCC AR6 GWP100",
                "IsDefault":     True,
                "PublishedYear": 2021,
            },
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"Created GwpDataset: {dataset.Name} (id={dataset.GwpDatasetId})"))
        else:
            self.stdout.write(f"GwpDataset already exists: {dataset.Name} (id={dataset.GwpDatasetId})")

        added = 0
        for gas, subtype, factor in GWP_VALUES:
            _, created = GwpValues.objects.get_or_create(
                GwpDatasetId=dataset, Gas=gas, GasSubtype=subtype,
                defaults={"GwpFactor": factor},
            )
            if created:
                added += 1

        self.stdout.write(self.style.SUCCESS(f"Done. {added} new GwpValues added."))
