"""
Migration: Units — canonical unit conversion table
App: apps.shared
Depends on: nothing (base reference table)

Every activity quantity entered in EmissionsData must reference a Unit row.
Before applying an emission factor, the system converts QuantityOrCost to the
canonical unit for that dimension, then applies the EF (which is always stored
in canonical units).

Canonical units per dimension:
  energy   → kilojoule (kJ)
  volume   → litre (L)
  mass     → kilogram (kg)
  distance → kilometre (km)
  area     → square metre (m²)
  count    → unit (no conversion)
  currency → USD (for spend-based Scope 3 estimates; rate applied separately)

ConversionFactor: multiply the raw quantity by this to get canonical units.
  e.g. 1 kWh × 3600 = 3600 kJ  →  kWh.ConversionFactor = 3600
       1 tonne × 1000 = 1000 kg →  tonne.ConversionFactor = 1000
"""

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Units',
            fields=[
                ('UnitId', models.AutoField(primary_key=True)),
                ('UnitName', models.CharField(max_length=100, help_text="Full name, e.g. 'kilowatt-hour'")),
                ('UnitSymbol', models.CharField(max_length=20, unique=True, help_text="Symbol, e.g. 'kWh'")),
                ('Dimension', models.CharField(
                    max_length=50,
                    help_text="energy | volume | mass | distance | area | count | currency"
                )),
                # Self-FK: NULL means this IS the canonical unit for its dimension
                ('CanonicalUnitId', models.ForeignKey(
                    'self',
                    on_delete=models.PROTECT,
                    null=True,
                    blank=True,
                    related_name='derived_units',
                    help_text="NULL = this is the canonical unit. Otherwise points to canonical unit."
                )),
                ('ConversionFactor', models.DecimalField(
                    max_digits=20,
                    decimal_places=10,
                    default=1,
                    help_text="Multiply raw quantity by this to get canonical unit quantity"
                )),
                ('IsCommon', models.BooleanField(
                    default=False,
                    help_text="Show prominently in UI unit dropdowns"
                )),
            ],
            options={'db_table': 'units', 'ordering': ['Dimension', 'UnitName']},
        ),
    ]


class SeedMigration(migrations.Migration):
    """Seed all common units with conversion factors."""

    dependencies = [('shared', '0019_units')]

    def seed_units(apps, schema_editor):
        Units = apps.get_model('shared', 'Units')

        # Helper: create canonical unit (ConversionFactor=1, CanonicalUnitId=NULL)
        def canonical(name, symbol, dimension, is_common=True):
            return Units.objects.create(
                UnitName=name, UnitSymbol=symbol,
                Dimension=dimension, ConversionFactor=1, IsCommon=is_common
            )

        # Helper: create derived unit
        def derived(name, symbol, dimension, canonical_unit, factor, is_common=False):
            return Units.objects.create(
                UnitName=name, UnitSymbol=symbol, Dimension=dimension,
                CanonicalUnitId=canonical_unit, ConversionFactor=factor,
                IsCommon=is_common
            )

        # ── Energy (canonical: kJ) ──────────────────────────────────────────
        kj    = canonical('kilojoule',           'kJ',    'energy', is_common=False)
        derived('kilowatt-hour',                 'kWh',   'energy', kj, 3600,           is_common=True)
        derived('megawatt-hour',                 'MWh',   'energy', kj, 3_600_000,      is_common=True)
        derived('gigajoule',                     'GJ',    'energy', kj, 1_000_000,      is_common=True)
        derived('megajoule',                     'MJ',    'energy', kj, 1_000,          is_common=False)
        derived('million British thermal unit',  'MMBtu', 'energy', kj, 1_055_055.85,  is_common=True)
        derived('British thermal unit',          'Btu',   'energy', kj, 1.055,          is_common=False)
        derived('therm (US)',                    'therm', 'energy', kj, 105_480.4,      is_common=False)
        derived('kilocalorie',                   'kcal',  'energy', kj, 4.184,          is_common=False)

        # ── Volume (canonical: litre) ───────────────────────────────────────
        litre = canonical('litre',               'L',     'volume', is_common=True)
        derived('millilitre',                    'mL',    'volume', litre, 0.001,        is_common=False)
        derived('cubic metre',                   'm³',    'volume', litre, 1_000,        is_common=True)
        derived('cubic kilometre',               'km³',   'volume', litre, 1e12,         is_common=False)
        derived('US gallon',                     'gal',   'volume', litre, 3.785411784,  is_common=True)
        derived('UK gallon (imperial)',          'imp gal','volume',litre, 4.54609,      is_common=False)
        derived('barrel (oil)',                  'bbl',   'volume', litre, 158.987,      is_common=False)
        derived('cubic foot',                    'ft³',   'volume', litre, 28.316847,    is_common=False)

        # ── Mass (canonical: kg) ───────────────────────────────────────────
        kg    = canonical('kilogram',            'kg',    'mass',   is_common=True)
        derived('gram',                          'g',     'mass',   kg, 0.001,           is_common=False)
        derived('tonne (metric ton)',            't',     'mass',   kg, 1_000,           is_common=True)
        derived('kilotonne',                     'kt',    'mass',   kg, 1_000_000,       is_common=False)
        derived('megatonne',                     'Mt',    'mass',   kg, 1_000_000_000,   is_common=False)
        derived('pound',                         'lb',    'mass',   kg, 0.453592,        is_common=False)
        derived('short ton (US)',                'short ton','mass',kg, 907.185,         is_common=False)
        derived('long ton (UK)',                 'long ton','mass', kg, 1016.047,        is_common=False)

        # ── Distance (canonical: km) ────────────────────────────────────────
        km    = canonical('kilometre',           'km',    'distance', is_common=True)
        derived('metre',                         'm',     'distance', km, 0.001,         is_common=False)
        derived('mile',                          'mi',    'distance', km, 1.60934,       is_common=True)
        derived('nautical mile',                 'nmi',   'distance', km, 1.852,         is_common=False)
        derived('tonne-kilometre',               'tkm',   'distance', km, 1,             is_common=True)  # freight unit

        # ── Area (canonical: m²) ───────────────────────────────────────────
        m2    = canonical('square metre',        'm²',    'area',   is_common=True)
        derived('hectare',                       'ha',    'area',   m2, 10_000,          is_common=True)
        derived('square kilometre',              'km²',   'area',   m2, 1_000_000,       is_common=False)
        derived('acre',                          'ac',    'area',   m2, 4_046.856,       is_common=False)

        # ── Count (canonical: unit) ─────────────────────────────────────────
        canonical('unit',                        'unit',  'count',  is_common=True)

        # ── Currency (canonical: USD) ───────────────────────────────────────
        # Used for spend-based Scope 3 estimates (EFs in kg CO2e / USD)
        # Actual FX conversion applied at application layer before lookup
        canonical('US dollar',                   'USD',   'currency', is_common=True)

    operations = [
        migrations.RunPython(seed_units, migrations.RunPython.noop),
    ]
