from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("emissions", "0008_ghginventories_boundary_notes"),
    ]

    operations = [
        migrations.AddField(
            model_name="emissionsdata",
            name="SupplierName",
            field=models.CharField(
                blank=True,
                help_text="Supplier shown on the bill, contract, or source evidence.",
                max_length=200,
                null=True,
            ),
        ),
    ]
