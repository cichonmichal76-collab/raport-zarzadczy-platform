from django.db import migrations


KPI_VIEW_SQL = """
CREATE OR REPLACE VIEW reports_grafana_kpi AS
WITH active_period AS (
    SELECT id, name, year, week
    FROM reports_reportingperiod
    WHERE is_active = TRUE
    ORDER BY year DESC, week DESC
    LIMIT 1
),
prod AS (
    SELECT pr.*
    FROM reports_productionrecord pr
    JOIN active_period ap ON ap.id = pr.period_id
)
SELECT
    ap.id AS period_id,
    ap.name AS period_name,
    COUNT(prod.id)::int AS total_orders,
    COUNT(prod.id) FILTER (WHERE prod.status = 'Gotowe')::int AS ready_orders,
    COALESCE(SUM(prod.completed_units), 0)::int AS completed_units,
    COALESCE(SUM(prod.planned_units), 0)::int AS planned_units,
    COALESCE(SUM(
        CASE
            WHEN prod.work_time ~ '^[0-9]+:[0-9]{1,2}$'
                THEN split_part(prod.work_time, ':', 1)::numeric + split_part(prod.work_time, ':', 2)::numeric / 60
            WHEN prod.work_time ~ '^[0-9]+([.,][0-9]+)?$'
                THEN replace(prod.work_time, ',', '.')::numeric
            ELSE 0
        END
    ), 0)::numeric(10,2) AS actual_hours,
    COALESCE(SUM(
        CASE
            WHEN prod.norm_time ~ '^[0-9]+:[0-9]{1,2}$'
                THEN split_part(prod.norm_time, ':', 1)::numeric + split_part(prod.norm_time, ':', 2)::numeric / 60
            WHEN prod.norm_time ~ '^[0-9]+([.,][0-9]+)?$'
                THEN replace(prod.norm_time, ',', '.')::numeric
            ELSE 0
        END
    ), 0)::numeric(10,2) AS norm_hours,
    (
        COALESCE(SUM(
            CASE
                WHEN prod.work_time ~ '^[0-9]+:[0-9]{1,2}$'
                    THEN split_part(prod.work_time, ':', 1)::numeric + split_part(prod.work_time, ':', 2)::numeric / 60
                WHEN prod.work_time ~ '^[0-9]+([.,][0-9]+)?$'
                    THEN replace(prod.work_time, ',', '.')::numeric
                ELSE 0
            END
        ), 0)
        -
        COALESCE(SUM(
            CASE
                WHEN prod.norm_time ~ '^[0-9]+:[0-9]{1,2}$'
                    THEN split_part(prod.norm_time, ':', 1)::numeric + split_part(prod.norm_time, ':', 2)::numeric / 60
                WHEN prod.norm_time ~ '^[0-9]+([.,][0-9]+)?$'
                    THEN replace(prod.norm_time, ',', '.')::numeric
                ELSE 0
            END
        ), 0)
    )::numeric(10,2) AS time_delta
FROM active_period ap
LEFT JOIN prod ON TRUE
GROUP BY ap.id, ap.name;
"""

STATUS_VIEW_SQL = """
CREATE OR REPLACE VIEW reports_grafana_statuses AS
WITH active_period AS (
    SELECT id
    FROM reports_reportingperiod
    WHERE is_active = TRUE
    ORDER BY year DESC, week DESC
    LIMIT 1
)
SELECT
    pr.status,
    COUNT(*)::int AS total
FROM reports_productionrecord pr
JOIN active_period ap ON ap.id = pr.period_id
GROUP BY pr.status
ORDER BY pr.status;
"""

GROUP_VIEW_SQL = """
CREATE OR REPLACE VIEW reports_grafana_group_execution AS
WITH active_period AS (
    SELECT id
    FROM reports_reportingperiod
    WHERE is_active = TRUE
    ORDER BY year DESC, week DESC
    LIMIT 1
)
SELECT
    COALESCE(NULLIF(pr.product_group, ''), 'Bez grupy') AS product_group,
    COALESCE(SUM(pr.completed_units), 0)::int AS completed_units,
    COALESCE(SUM(pr.planned_units), 0)::int AS planned_units
FROM reports_productionrecord pr
JOIN active_period ap ON ap.id = pr.period_id
GROUP BY COALESCE(NULLIF(pr.product_group, ''), 'Bez grupy')
ORDER BY product_group;
"""

MACHINE_VIEW_SQL = """
CREATE OR REPLACE VIEW reports_grafana_machine_time AS
WITH active_period AS (
    SELECT id
    FROM reports_reportingperiod
    WHERE is_active = TRUE
    ORDER BY year DESC, week DESC
    LIMIT 1
)
SELECT
    COALESCE(NULLIF(pr.machine, ''), 'Nieprzypisana') AS machine,
    COALESCE(SUM(
        CASE
            WHEN pr.work_time ~ '^[0-9]+:[0-9]{1,2}$'
                THEN split_part(pr.work_time, ':', 1)::numeric + split_part(pr.work_time, ':', 2)::numeric / 60
            WHEN pr.work_time ~ '^[0-9]+([.,][0-9]+)?$'
                THEN replace(pr.work_time, ',', '.')::numeric
            ELSE 0
        END
    ), 0)::numeric(10,2) AS actual_hours,
    COALESCE(SUM(
        CASE
            WHEN pr.norm_time ~ '^[0-9]+:[0-9]{1,2}$'
                THEN split_part(pr.norm_time, ':', 1)::numeric + split_part(pr.norm_time, ':', 2)::numeric / 60
            WHEN pr.norm_time ~ '^[0-9]+([.,][0-9]+)?$'
                THEN replace(pr.norm_time, ',', '.')::numeric
            ELSE 0
        END
    ), 0)::numeric(10,2) AS norm_hours
FROM reports_productionrecord pr
JOIN active_period ap ON ap.id = pr.period_id
GROUP BY COALESCE(NULLIF(pr.machine, ''), 'Nieprzypisana')
ORDER BY machine;
"""

EXCEPTIONS_VIEW_SQL = """
CREATE OR REPLACE VIEW reports_grafana_exceptions AS
WITH active_period AS (
    SELECT id
    FROM reports_reportingperiod
    WHERE is_active = TRUE
    ORDER BY year DESC, week DESC
    LIMIT 1
)
SELECT
    pr.order_number,
    pr.product,
    CASE
        WHEN COALESCE(NULLIF(trim(pr.workers), ''), '') = '' THEN 'Brak operatora'
        WHEN lower(COALESCE(pr.current_state, '') || ' ' || COALESCE(pr.problem, '') || ' ' || COALESCE(pr.solution, '')) ~ '(rewiz|norma|normatyw|norm)' THEN 'Rewizja normy'
        WHEN lower(COALESCE(pr.current_state, '') || ' ' || COALESCE(pr.problem, '') || ' ' || COALESCE(pr.solution, '')) ~ '(plan|harmonogram|kolejk|zaplan)' THEN 'Bledne planowanie'
        WHEN lower(COALESCE(pr.current_state, '') || ' ' || COALESCE(pr.problem, '') || ' ' || COALESCE(pr.solution, '')) ~ '(technolog|ustaw|przezbroj|proces)' THEN 'Problemy technologiczne'
        WHEN COALESCE(NULLIF(trim(pr.problem), ''), '') <> '' THEN 'Komentarze i odchylenia'
        ELSE 'Inne'
    END AS category,
    COALESCE(NULLIF(pr.problem, ''), NULLIF(pr.current_state, ''), NULLIF(pr.solution, ''), 'Wymaga sprawdzenia.') AS detail
FROM reports_productionrecord pr
JOIN active_period ap ON ap.id = pr.period_id
WHERE
    COALESCE(NULLIF(trim(pr.workers), ''), '') = ''
    OR COALESCE(NULLIF(trim(pr.problem), ''), '') <> ''
    OR lower(COALESCE(pr.current_state, '') || ' ' || COALESCE(pr.problem, '') || ' ' || COALESCE(pr.solution, '')) ~ '(rewiz|norma|normatyw|norm|plan|harmonogram|kolejk|zaplan|technolog|ustaw|przezbroj|proces)';
"""

DROP_VIEW_SQL = """
DROP VIEW IF EXISTS reports_grafana_exceptions;
DROP VIEW IF EXISTS reports_grafana_machine_time;
DROP VIEW IF EXISTS reports_grafana_group_execution;
DROP VIEW IF EXISTS reports_grafana_statuses;
DROP VIEW IF EXISTS reports_grafana_kpi;
"""


class Migration(migrations.Migration):
    dependencies = [
        ("reports", "0002_reportingperiod_constraints"),
    ]

    operations = [
        migrations.RunSQL(DROP_VIEW_SQL, reverse_sql=migrations.RunSQL.noop),
        migrations.RunSQL(KPI_VIEW_SQL, reverse_sql="DROP VIEW IF EXISTS reports_grafana_kpi;"),
        migrations.RunSQL(STATUS_VIEW_SQL, reverse_sql="DROP VIEW IF EXISTS reports_grafana_statuses;"),
        migrations.RunSQL(GROUP_VIEW_SQL, reverse_sql="DROP VIEW IF EXISTS reports_grafana_group_execution;"),
        migrations.RunSQL(MACHINE_VIEW_SQL, reverse_sql="DROP VIEW IF EXISTS reports_grafana_machine_time;"),
        migrations.RunSQL(EXCEPTIONS_VIEW_SQL, reverse_sql="DROP VIEW IF EXISTS reports_grafana_exceptions;"),
    ]
