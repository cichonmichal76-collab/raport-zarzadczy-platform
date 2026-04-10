from django.db import migrations, models
import django.utils.timezone


PRODIO_ORDERS_VIEW_SQL = """
CREATE OR REPLACE VIEW reports_grafana_prodio_orders AS
SELECT
    id,
    prodio_id,
    order_number,
    COALESCE(NULLIF(status, ''), 'unknown') AS status,
    product_name,
    product_group,
    client_name,
    total,
    done,
    GREATEST(total - done, 0) AS remaining,
    CASE
        WHEN total > 0 THEN ROUND((done / total) * 100, 1)
        ELSE 0
    END AS completion_pct,
    deadline,
    create_date,
    synced_at
FROM reports_prodioorder;
"""


class Migration(migrations.Migration):
    dependencies = [
        ("reports", "0004_grafana_rnd_views"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProdioOrder",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("prodio_id", models.CharField(max_length=128, unique=True)),
                ("order_number", models.CharField(blank=True, db_index=True, max_length=128)),
                ("status", models.CharField(blank=True, db_index=True, max_length=64)),
                ("product_name", models.CharField(blank=True, max_length=255)),
                ("product_group", models.CharField(blank=True, max_length=255)),
                ("client_name", models.CharField(blank=True, max_length=255)),
                ("total", models.DecimalField(decimal_places=3, default=0, max_digits=14)),
                ("done", models.DecimalField(decimal_places=3, default=0, max_digits=14)),
                ("deadline", models.DateField(blank=True, null=True)),
                ("create_date", models.DateField(blank=True, null=True)),
                ("raw_data", models.JSONField(blank=True, default=dict)),
                ("synced_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["-create_date", "-id"],
            },
        ),
        migrations.RunSQL(PRODIO_ORDERS_VIEW_SQL, reverse_sql="DROP VIEW IF EXISTS reports_grafana_prodio_orders;"),
    ]
