"""
Drop the orphaned entities.SBTiCompanyId column (SBTi out of product scope).

Companion to emissions/0007 — same rationale: the field was removed from the
model but the column was never dropped. Idempotent raw SQL; no-op on fresh DBs.
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('entities', '0003_alter_entities_options'),
    ]

    operations = [
        migrations.RunSQL(
            sql='ALTER TABLE entities DROP COLUMN IF EXISTS "SBTiCompanyId";',
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
