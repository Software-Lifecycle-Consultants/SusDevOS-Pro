"""
Management command: seed_units

Seeds the Units reference table with the units the DEFRA/DESNZ UK Government GHG
conversion factors are published in. Nothing seeded this table before, so it was
empty in production alongside the empty factor library.

Safe to run multiple times — uses update_or_create keyed on UnitName.

Usage:
    python manage.py seed_units

Why every unit is a pass-through (ConversionFactor = 1, IsCanonical = True)
--------------------------------------------------------------------------
The calculation in apps/emissions/services.py is:

    QuantityCanonical = QuantityOrCost x InputUnitId.ConversionFactor
    kg CO2e           = QuantityCanonical x EmissionFactor x GWP100

so the emission factor must be expressed per *canonical* unit. DEFRA publishes a
separate factor for each unit an activity can be measured in — diesel per litre
and per tonne, car travel per km and per mile — rather than one factor per
physical dimension. Converting the quantity to some other canonical unit would
therefore desynchronise it from the factor and silently scale every result.

Keeping each unit canonical to itself makes `quantity x factor` exact, and means
the unit shown in the picker is the unit the number is actually per. If a real
conversion is ever wanted (say, letting someone enter gallons against a
per-litre factor), it belongs in a unit *pair* mapped to a specific factor's
unit, not in a global canonical-per-dimension scheme.
"""
from django.core.management.base import BaseCommand

# (UnitName, UnitSymbol, PhysicalDimension)
# UnitName must match the DEFRA "UOM" column verbatim: import_defra_factors
# resolves the FK by that string, and EmissionFactorsSerializer.get_unit()
# surfaces it as the unit label in the factor picker.
UNITS = [
    ("kg",                   "kg",       "mass"),
    ("tonnes",               "t",        "mass"),
    ("litres",               "L",        "volume"),
    ("million litres",       "Ml",       "volume"),
    ("cubic metres",         "m3",       "volume"),
    ("kWh",                  "kWh",      "energy"),
    ("kWh (Net CV)",         "kWh",      "energy"),
    ("kWh (Gross CV)",       "kWh",      "energy"),
    ("GJ",                   "GJ",       "energy"),
    ("km",                   "km",       "distance"),
    ("miles",                "mi",       "distance"),
    ("tonne.km",             "t.km",     "freight transport"),
    ("passenger.km",         "p.km",     "passenger transport"),
    ("Room per night",       "room/nt",  "occupancy"),
    ("per FTE Working Hour", "FTE.h",    "labour"),
]


class Command(BaseCommand):
    help = "Seed the Units reference table used by the DEFRA emission factor library."

    def handle(self, *args, **options):
        from apps.emissions.models import Units

        created = updated = 0
        for name, symbol, dimension in UNITS:
            _, was_created = Units.objects.update_or_create(
                UnitName=name,
                defaults={
                    "UnitSymbol": symbol,
                    "PhysicalDimension": dimension,
                    # See the module docstring: pass-through is deliberate.
                    "ConversionFactor": 1,
                    "CanonicalUnit": symbol,
                    "IsCanonical": True,
                },
            )
            created += was_created
            updated += not was_created

        self.stdout.write(self.style.SUCCESS(
            f"Units seeded: {created} created, {updated} updated ({len(UNITS)} total)."
        ))
