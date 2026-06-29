"""
Drop orphaned SBTi columns left behind by the "remove SBTi" refocus.

SBTi was removed from product scope; the model fields were deleted but the
original removal never dropped the DB columns. Databases migrated before that
commit still carry them — and emissions_data.CountsTowardSBTi is NOT NULL with
no default, so it breaks every EmissionsData insert.

These columns are not in any current model/migration state, so this uses raw
DROP COLUMN IF EXISTS (idempotent: a no-op on fresh databases, a repair on
pre-existing ones). No state_operations — Django's model state already lacks
these fields.
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('emissions', '0006_remove_emissionsdata_countstowardndc'),
    ]

    operations = [
        migrations.RunSQL(
            sql=[
                'ALTER TABLE emissions_data DROP COLUMN IF EXISTS "CountsTowardSBTi";',
                'ALTER TABLE targets DROP COLUMN IF EXISTS "SBTiStatus";',
                'ALTER TABLE targets DROP COLUMN IF EXISTS "SBTiLastSyncedAt";',
            ],
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
