-- ============================================================================
-- Projet Job Intelligent — Materialized Views for Power BI
-- ============================================================================

-- ============================================================================
-- 1. mv_offers_by_skill — skill demand per week
-- ============================================================================
DROP MATERIALIZED VIEW IF EXISTS mv_offers_by_skill;
CREATE MATERIALIZED VIEW mv_offers_by_skill AS
SELECT
    skill_name,
    COUNT(*)::INT                        AS offer_count,
    date_trunc('week', jo.published_at)  AS week_date
FROM job_offers jo,
     LATERAL unnest(jo.required_skills) AS skill_name
WHERE jo.published_at IS NOT NULL
GROUP BY skill_name, week_date
ORDER BY week_date DESC, offer_count DESC;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_offers_by_skill
    ON mv_offers_by_skill (skill_name, week_date);

-- ============================================================================
-- 2. mv_salary_by_role — salary statistics by role and contract
-- ============================================================================
DROP MATERIALIZED VIEW IF EXISTS mv_salary_by_role;
CREATE MATERIALIZED VIEW mv_salary_by_role AS
SELECT
    dw.normalized_title                  AS job_title,
    jo.contract_type,
    ROUND(AVG((jo.salary_min + jo.salary_max) / 2)::NUMERIC, 0) AS salary_avg,
    ROUND(MIN(jo.salary_min)::NUMERIC, 0)                       AS salary_min,
    ROUND(MAX(jo.salary_max)::NUMERIC, 0)                       AS salary_max,
    COUNT(*)::INT                                                 AS offer_count
FROM job_offers jo
JOIN dw_job_offers dw ON dw.offer_id = jo.id
WHERE jo.salary_min IS NOT NULL
  AND jo.salary_max IS NOT NULL
  AND dw.normalized_title IS NOT NULL
GROUP BY dw.normalized_title, jo.contract_type
ORDER BY salary_avg DESC;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_salary_by_role
    ON mv_salary_by_role (job_title, contract_type);

-- ============================================================================
-- 3. mv_offers_by_location — geographic distribution
-- ============================================================================
DROP MATERIALIZED VIEW IF EXISTS mv_offers_by_location;
CREATE MATERIALIZED VIEW mv_offers_by_location AS
SELECT
    jo.location                 AS city,
    COUNT(*)::INT               AS offer_count,
    ROUND(AVG((jo.salary_min + jo.salary_max) / 2)::NUMERIC, 0) AS avg_salary
FROM job_offers jo
WHERE jo.location IS NOT NULL
  AND jo.location <> ''
GROUP BY jo.location
ORDER BY offer_count DESC;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_offers_by_location
    ON mv_offers_by_location (city);

-- ============================================================================
-- 4. mv_market_trends — weekly offer count by source (last 12 weeks)
-- ============================================================================
DROP MATERIALIZED VIEW IF EXISTS mv_market_trends;
CREATE MATERIALIZED VIEW mv_market_trends AS
SELECT
    s.name                                AS source_name,
    date_trunc('week', jo.published_at)   AS week_date,
    COUNT(*)::INT                         AS offer_count
FROM job_offers jo
JOIN sources s ON s.id = jo.source_id
WHERE jo.published_at >= now() - INTERVAL '12 weeks'
GROUP BY s.name, week_date
ORDER BY week_date DESC, offer_count DESC;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_market_trends
    ON mv_market_trends (source_name, week_date);

-- ============================================================================
-- 5. mv_top_companies — most active hiring companies
-- ============================================================================
DROP MATERIALIZED VIEW IF EXISTS mv_top_companies;
CREATE MATERIALIZED VIEW mv_top_companies AS
SELECT
    jo.company                  AS company_name,
    COUNT(*)::INT               AS active_offers,
    ROUND(AVG((jo.salary_min + jo.salary_max) / 2)::NUMERIC, 0) AS avg_salary,
    array_agg(DISTINCT jo.contract_type)
        FILTER (WHERE jo.contract_type IS NOT NULL) AS contract_types
FROM job_offers jo
WHERE jo.company IS NOT NULL
  AND jo.company <> ''
GROUP BY jo.company
ORDER BY active_offers DESC;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_top_companies
    ON mv_top_companies (company_name);

-- ============================================================================
-- refresh_all_analytics_views() — called by Airflow after ETL
-- ============================================================================
CREATE OR REPLACE FUNCTION refresh_all_analytics_views()
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_offers_by_skill;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_salary_by_role;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_offers_by_location;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_market_trends;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_top_companies;
END;
$$;
