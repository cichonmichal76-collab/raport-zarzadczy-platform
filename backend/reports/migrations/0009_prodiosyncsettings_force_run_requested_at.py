from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("reports", "0008_prodiosyncsettings"),
    ]

    operations = [
        migrations.AddField(
            model_name="prodiosyncsettings",
            name="force_run_requested_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
