from django.db import migrations, models
import django.utils.timezone


PRODIO_RAW_OBJECTS_VIEW_SQL = """
CREATE OR REPLACE VIEW reports_grafana_prodio_raw_objects AS
SELECT
    id,
    resource,
    prodio_id,
    display_name,
    status,
    synced_at,
    raw_data
FROM reports_prodioapiobject;
"""


class Migration(migrations.Migration):
    dependencies = [
        ("reports", "0005_prodio_orders"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProdioApiObject",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("resource", models.CharField(db_index=True, max_length=64)),
                ("prodio_id", models.CharField(max_length=128)),
                ("display_name", models.CharField(blank=True, max_length=255)),
                ("status", models.CharField(blank=True, db_index=True, max_length=128)),
                ("raw_data", models.JSONField(blank=True, default=dict)),
                ("synced_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["resource", "display_name", "prodio_id"],
                "constraints": [
                    models.UniqueConstraint(fields=["resource", "prodio_id"], name="reports_unique_prodio_api_object"),
                ],
            },
        ),
        migrations.RunSQL(PRODIO_RAW_OBJECTS_VIEW_SQL, reverse_sql="DROP VIEW IF EXISTS reports_grafana_prodio_raw_objects;"),
    ]
