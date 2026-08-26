from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("emissions", "0007_drop_orphaned_sbti_columns"),
    ]

    operations = [
        migrations.AddField(
            model_name="ghginventories",
            name="BoundaryNotes",
            field=models.TextField(
                blank=True,
                help_text=(
                    "Included/excluded operations and rationale for the inventory boundary."
                ),
                null=True,
            ),
        ),
    ]
