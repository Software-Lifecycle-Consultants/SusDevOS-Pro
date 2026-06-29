"""
Drop the dormant CountsTowardNDC field.

NDC (Nationally Determined Contributions) was removed from product scope in the
nature/MRV + TNFD refocus. The field had no logic reading it (no serializer,
view, or task referenced it) — purely a leftover column.
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('emissions', '0005_emissionsoffsets_creditregistry'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='emissionsdata',
            name='CountsTowardNDC',
        ),
    ]
