from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("reports", "0007_prodio_grafana_raw_views"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProdioSyncSettings",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("enabled", models.BooleanField(default=True)),
                (
                    "interval_minutes",
                    models.PositiveIntegerField(
                        choices=[(1, "1 minuta"), (10, "10 minut"), (60, "1 godzina")],
                        default=10,
                    ),
                ),
                ("last_started_at", models.DateTimeField(blank=True, null=True)),
                ("last_finished_at", models.DateTimeField(blank=True, null=True)),
                ("last_status", models.CharField(blank=True, default="never", max_length=16)),
                ("last_message", models.TextField(blank=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Ustawienia sync Prodio",
                "verbose_name_plural": "Ustawienia sync Prodio",
            },
        ),
    ]
