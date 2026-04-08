from django.db import migrations


RND_KPI_VIEW_SQL = """
CREATE OR REPLACE VIEW reports_grafana_rnd_kpi AS
WITH active_period AS (
    SELECT id, name, year, week
    FROM reports_reportingperiod
    WHERE is_active = TRUE
    ORDER BY year DESC, week DESC
    LIMIT 1
),
rnd AS (
    SELECT rr.*
    FROM reports_rndrecord rr
    JOIN active_period ap ON ap.id = rr.period_id
)
SELECT
    ap.id AS period_id,
    ap.name AS period_name,
    COUNT(rnd.id)::int AS total_items,
    COUNT(rnd.id) FILTER (WHERE rnd.status ILIKE 'gotowe' OR rnd.progress >= 100)::int AS completed_items,
    COALESCE(ROUND(AVG(rnd.progress)::numeric, 1), 0)::numeric(5,1) AS avg_progress,
    COALESCE(ROUND(AVG(rnd.trl_level)::numeric, 1), 0)::numeric(4,1) AS avg_trl,
    COUNT(rnd.id) FILTER (WHERE COALESCE(NULLIF(trim(rnd.problem), ''), '') <> '')::int AS issues_count
FROM active_period ap
LEFT JOIN rnd ON TRUE
GROUP BY ap.id, ap.name;
"""

RND_STATUS_VIEW_SQL = """
CREATE OR REPLACE VIEW reports_grafana_rnd_statuses AS
WITH active_period AS (
    SELECT id
    FROM reports_reportingperiod
    WHERE is_active = TRUE
    ORDER BY year DESC, week DESC
    LIMIT 1
)
SELECT
    COALESCE(NULLIF(rr.status, ''), 'Nieznany') AS status,
    COUNT(*)::int AS total
FROM reports_rndrecord rr
JOIN active_period ap ON ap.id = rr.period_id
GROUP BY COALESCE(NULLIF(rr.status, ''), 'Nieznany')
ORDER BY status;
"""

RND_TRL_VIEW_SQL = """
CREATE OR REPLACE VIEW reports_grafana_rnd_trl AS
WITH active_period AS (
    SELECT id
    FROM reports_reportingperiod
    WHERE is_active = TRUE
    ORDER BY year DESC, week DESC
    LIMIT 1
)
SELECT
    rr.trl_level,
    COUNT(*)::int AS total
FROM reports_rndrecord rr
JOIN active_period ap ON ap.id = rr.period_id
GROUP BY rr.trl_level
ORDER BY rr.trl_level;
"""

RND_WORKTYPE_VIEW_SQL = """
CREATE OR REPLACE VIEW reports_grafana_rnd_worktypes AS
WITH active_period AS (
    SELECT id
    FROM reports_reportingperiod
    WHERE is_active = TRUE
    ORDER BY year DESC, week DESC
    LIMIT 1
)
SELECT
    COALESCE(NULLIF(rr.work_type, ''), 'Bez typu') AS work_type,
    COUNT(*)::int AS total_items,
    COALESCE(ROUND(AVG(rr.progress)::numeric, 1), 0)::numeric(5,1) AS avg_progress
FROM reports_rndrecord rr
JOIN active_period ap ON ap.id = rr.period_id
GROUP BY COALESCE(NULLIF(rr.work_type, ''), 'Bez typu')
ORDER BY work_type;
"""

RND_EXCEPTIONS_VIEW_SQL = """
CREATE OR REPLACE VIEW reports_grafana_rnd_exceptions AS
WITH active_period AS (
    SELECT id
    FROM reports_reportingperiod
    WHERE is_active = TRUE
    ORDER BY year DESC, week DESC
    LIMIT 1
)
SELECT
    rr.code,
    rr.name,
    COALESCE(NULLIF(rr.status, ''), 'Nieznany') AS status,
    rr.progress,
    rr.trl_level,
    CASE
        WHEN COALESCE(NULLIF(trim(rr.problem), ''), '') <> '' THEN 'Problemy i blokery'
        WHEN rr.progress < 50 AND rr.trl_level >= 6 THEN 'Ryzyko opoznienia'
        WHEN COALESCE(NULLIF(trim(rr.solution), ''), '') <> '' THEN 'Wymaga decyzji'
        ELSE 'Do obserwacji'
    END AS category,
    COALESCE(NULLIF(rr.problem, ''), NULLIF(rr.current_state, ''), NULLIF(rr.solution, ''), 'Wymaga sprawdzenia.') AS detail
FROM reports_rndrecord rr
JOIN active_period ap ON ap.id = rr.period_id
WHERE
    COALESCE(NULLIF(trim(rr.problem), ''), '') <> ''
    OR COALESCE(NULLIF(trim(rr.solution), ''), '') <> ''
    OR (rr.progress < 50 AND rr.trl_level >= 6);
"""

DROP_VIEW_SQL = """
DROP VIEW IF EXISTS reports_grafana_rnd_exceptions;
DROP VIEW IF EXISTS reports_grafana_rnd_worktypes;
DROP VIEW IF EXISTS reports_grafana_rnd_trl;
DROP VIEW IF EXISTS reports_grafana_rnd_statuses;
DROP VIEW IF EXISTS reports_grafana_rnd_kpi;
"""


class Migration(migrations.Migration):
    dependencies = [
        ("reports", "0003_grafana_views"),
    ]

    operations = [
        migrations.RunSQL(DROP_VIEW_SQL, reverse_sql=migrations.RunSQL.noop),
        migrations.RunSQL(RND_KPI_VIEW_SQL, reverse_sql="DROP VIEW IF EXISTS reports_grafana_rnd_kpi;"),
        migrations.RunSQL(RND_STATUS_VIEW_SQL, reverse_sql="DROP VIEW IF EXISTS reports_grafana_rnd_statuses;"),
        migrations.RunSQL(RND_TRL_VIEW_SQL, reverse_sql="DROP VIEW IF EXISTS reports_grafana_rnd_trl;"),
        migrations.RunSQL(RND_WORKTYPE_VIEW_SQL, reverse_sql="DROP VIEW IF EXISTS reports_grafana_rnd_worktypes;"),
        migrations.RunSQL(RND_EXCEPTIONS_VIEW_SQL, reverse_sql="DROP VIEW IF EXISTS reports_grafana_rnd_exceptions;"),
    ]
