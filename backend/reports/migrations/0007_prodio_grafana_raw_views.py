from django.db import migrations


OPERATIONS_VIEW_SQL = """
CREATE OR REPLACE VIEW reports_grafana_prodio_operations AS
SELECT
    o.id,
    o.prodio_id AS operation_id,
    o.raw_data->>'order_id' AS order_id,
    o.raw_data->>'auto_order_id' AS auto_order_id,
    o.raw_data->>'status' AS status_code,
    CASE o.raw_data->>'status'
        WHEN '1' THEN 'W toku / aktywne'
        WHEN '2' THEN 'Zaplanowane / oczekuje'
        WHEN '3' THEN 'Wstrzymane'
        WHEN '4' THEN 'Zakonczone'
        ELSE NULLIF(o.raw_data->>'status', '')
    END AS status_label,
    o.raw_data#>>'{product,name}' AS product_name,
    o.raw_data#>>'{product,weight}' AS product_code,
    o.raw_data#>>'{product,product_group_name}' AS product_group_name,
    o.raw_data#>>'{client,name}' AS client_name,
    NULLIF(o.raw_data->>'machine_name', '') AS machine_name,
    NULLIF(o.raw_data->>'desktop_name', '') AS desktop_name,
    NULLIF(o.raw_data->>'note', '') AS note,
    NULLIF(o.raw_data->>'assigned_workers', '') AS assigned_workers_json,
    NULLIF(o.raw_data->>'deadline', '')::date AS deadline,
    NULLIF(o.raw_data->>'deadline_time', '') AS deadline_time,
    NULLIF(o.raw_data->>'datetime_start', '')::timestamp AS datetime_start,
    NULLIF(o.raw_data->>'create_date', '')::timestamp AS create_date,
    COALESCE(NULLIF(o.raw_data->>'todo', '')::numeric, 0) AS todo,
    COALESCE(NULLIF(o.raw_data->>'done', '')::numeric, 0) AS done,
    GREATEST(
        COALESCE(NULLIF(o.raw_data->>'todo', '')::numeric, 0)
        - COALESCE(NULLIF(o.raw_data->>'done', '')::numeric, 0),
        0
    ) AS remaining,
    CASE
        WHEN COALESCE(NULLIF(o.raw_data->>'todo', '')::numeric, 0) = 0 THEN NULL
        ELSE ROUND(
            COALESCE(NULLIF(o.raw_data->>'done', '')::numeric, 0)
            / NULLIF(COALESCE(NULLIF(o.raw_data->>'todo', '')::numeric, 0), 0)
            * 100,
            1
        )
    END AS completion_pct,
    COALESCE(NULLIF(o.raw_data->>'hour_price', '')::numeric, 0) AS hour_price,
    COALESCE(NULLIF(o.raw_data->>'machine_hour_price', '')::numeric, 0) AS machine_hour_price,
    COALESCE(NULLIF(o.raw_data->>'assigned_workers_hour_price', '')::numeric, 0) AS assigned_workers_hour_price,
    o.synced_at
FROM reports_prodioapiobject o
WHERE o.resource = 'order-machines';
"""


WORK_LOGS_VIEW_SQL = """
CREATE OR REPLACE VIEW reports_grafana_prodio_work_logs AS
SELECT
    o.id AS operation_db_id,
    o.prodio_id AS operation_id,
    o.raw_data->>'order_id' AS order_id,
    o.raw_data->>'auto_order_id' AS auto_order_id,
    o.raw_data->>'machine_name' AS machine_name,
    o.raw_data#>>'{product,name}' AS product_name,
    worker->>'id' AS work_log_id,
    worker->>'worker_id' AS worker_id,
    worker->>'worker_full_name' AS worker_full_name,
    NULLIF(worker->>'note', '') AS worker_note,
    COALESCE(NULLIF(worker->>'total', '')::numeric, 0) AS total_done,
    COALESCE(NULLIF(worker->>'incompatibile_count', '')::numeric, 0) AS incompatibile_count,
    NULLIF(worker->>'incompatibile_desc', '') AS incompatibile_desc,
    NULLIF(worker->>'incompatibile_solution', '') AS incompatibile_solution,
    NULLIF(worker->>'start_time', '')::timestamp AS start_time,
    NULLIF(worker->>'stop_time', '')::timestamp AS stop_time,
    CASE
        WHEN NULLIF(worker->>'start_time', '') IS NULL
          OR NULLIF(worker->>'stop_time', '') IS NULL
        THEN NULL
        ELSE ROUND(
            EXTRACT(EPOCH FROM (
                NULLIF(worker->>'stop_time', '')::timestamp
                - NULLIF(worker->>'start_time', '')::timestamp
            )) / 60,
            1
        )
    END AS work_minutes,
    COALESCE(NULLIF(worker->>'worker_hour_price', '')::numeric, 0) AS worker_hour_price,
    o.synced_at
FROM reports_prodioapiobject o
CROSS JOIN LATERAL jsonb_array_elements(
    CASE
        WHEN jsonb_typeof(o.raw_data->'orderWorkers') = 'array' THEN o.raw_data->'orderWorkers'
        ELSE '[]'::jsonb
    END
) AS worker
WHERE o.resource = 'order-machines';
"""


PRODUCTS_VIEW_SQL = """
CREATE OR REPLACE VIEW reports_grafana_prodio_products AS
SELECT
    p.id,
    p.prodio_id AS product_id,
    p.display_name AS product_name,
    p.raw_data->>'weight' AS product_code,
    p.raw_data->>'product_group_name' AS product_group_name,
    p.raw_data->>'client_name' AS client_name,
    NULLIF(p.raw_data->>'note', '') AS note,
    NULLIF(p.raw_data->>'public_note', '') AS public_note,
    COALESCE(NULLIF(p.raw_data->>'demand', '')::numeric, 0) AS demand,
    COALESCE(NULLIF(p.raw_data->>'stock_level', '')::numeric, 0) AS stock_level,
    COALESCE(NULLIF(p.raw_data->>'stock_level_on_production', '')::numeric, 0) AS stock_level_on_production,
    COALESCE(NULLIF(p.raw_data->>'stock_optimal_level', '')::numeric, 0) AS stock_optimal_level,
    COALESCE(NULLIF(p.raw_data->>'stock_critical_level', '')::numeric, 0) AS stock_critical_level,
    NULLIF(p.raw_data->>'stock_level_by_warehouse', '') AS stock_level_by_warehouse_json,
    p.synced_at
FROM reports_prodioapiobject p
WHERE p.resource = 'products';
"""


DROP_VIEWS_SQL = """
DROP VIEW IF EXISTS reports_grafana_prodio_products;
DROP VIEW IF EXISTS reports_grafana_prodio_work_logs;
DROP VIEW IF EXISTS reports_grafana_prodio_operations;
"""


class Migration(migrations.Migration):
    dependencies = [
        ("reports", "0006_prodio_api_object"),
    ]

    operations = [
        migrations.RunSQL(OPERATIONS_VIEW_SQL, "DROP VIEW IF EXISTS reports_grafana_prodio_operations;"),
        migrations.RunSQL(WORK_LOGS_VIEW_SQL, "DROP VIEW IF EXISTS reports_grafana_prodio_work_logs;"),
        migrations.RunSQL(PRODUCTS_VIEW_SQL, "DROP VIEW IF EXISTS reports_grafana_prodio_products;"),
    ]
