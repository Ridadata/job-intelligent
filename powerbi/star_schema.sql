-- ============================================================================
-- Power BI Starter Star Schema for Job Intelligent
--
-- Run this in Supabase SQL Editor after base migrations.
-- Creates a dedicated schema with analytical views for Power BI.
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS powerbi;

-- ----------------------------------------------------------------------------
-- Dimensions
-- ----------------------------------------------------------------------------

CREATE OR REPLACE VIEW powerbi.dim_date AS
SELECT
    TO_CHAR(d, 'YYYYMMDD')::INT AS date_key,
    d::DATE AS date_day,
    EXTRACT(YEAR FROM d)::INT AS year,
    EXTRACT(QUARTER FROM d)::INT AS quarter,
    EXTRACT(MONTH FROM d)::INT AS month,
    TO_CHAR(d, 'Mon') AS month_name,
    EXTRACT(WEEK FROM d)::INT AS iso_week,
    EXTRACT(DOW FROM d)::INT AS day_of_week,
    TO_CHAR(d, 'Dy') AS day_name
FROM generate_series(
    (
        SELECT COALESCE(
            MIN(DATE_TRUNC('day', published_at))::DATE,
            CURRENT_DATE - INTERVAL '365 days'
        )
        FROM public.job_offers
    ),
    CURRENT_DATE + INTERVAL '365 days',
    INTERVAL '1 day'
) AS gs(d);

CREATE OR REPLACE VIEW powerbi.dim_source AS
SELECT
    id AS source_id,
    name AS source_name,
    base_url,
    last_scraped_at
FROM public.sources;

CREATE OR REPLACE VIEW powerbi.dim_contract AS
SELECT DISTINCT
    COALESCE(contract_type, 'Autre') AS contract_type
FROM public.job_offers;

CREATE OR REPLACE VIEW powerbi.dim_company AS
SELECT
    MD5(LOWER(TRIM(company))) AS company_key,
    INITCAP(TRIM(company)) AS company_name
FROM public.job_offers
WHERE company IS NOT NULL
  AND TRIM(company) <> ''
GROUP BY 1, 2;

CREATE OR REPLACE VIEW powerbi.dim_location AS
SELECT
    MD5(LOWER(TRIM(location))) AS location_key,
    INITCAP(TRIM(location)) AS location_name
FROM public.job_offers
WHERE location IS NOT NULL
  AND TRIM(location) <> ''
GROUP BY 1, 2;

CREATE OR REPLACE VIEW powerbi.dim_role AS
SELECT
    MD5(
        LOWER(COALESCE(dw.normalized_title, 'unknown')) || '|' ||
        LOWER(COALESCE(dw.category, 'other')) || '|' ||
        LOWER(COALESCE(dw.seniority_level, 'mid'))
    ) AS role_key,
    COALESCE(dw.normalized_title, 'Unknown') AS normalized_title,
    COALESCE(dw.category, 'Other') AS category,
    COALESCE(dw.seniority_level, 'Mid') AS seniority_level
FROM public.dw_job_offers dw
GROUP BY 1, 2, 3, 4;

CREATE OR REPLACE VIEW powerbi.dim_skill AS
SELECT DISTINCT
    LOWER(TRIM(skill_name)) AS skill_name
FROM (
    SELECT UNNEST(required_skills) AS skill_name
    FROM public.job_offers
    WHERE required_skills IS NOT NULL

    UNION ALL

    SELECT UNNEST(tech_stack) AS skill_name
    FROM public.dw_job_offers
    WHERE tech_stack IS NOT NULL
) skill_union
WHERE skill_name IS NOT NULL
  AND TRIM(skill_name) <> '';

-- ----------------------------------------------------------------------------
-- Facts
-- ----------------------------------------------------------------------------

CREATE OR REPLACE VIEW powerbi.fact_job_offers AS
SELECT
    jo.id AS offer_id,
    jo.source_id,
    MD5(LOWER(TRIM(jo.company))) AS company_key,
    MD5(LOWER(TRIM(jo.location))) AS location_key,
    MD5(
        LOWER(COALESCE(dw.normalized_title, 'unknown')) || '|' ||
        LOWER(COALESCE(dw.category, 'other')) || '|' ||
        LOWER(COALESCE(dw.seniority_level, 'mid'))
    ) AS role_key,
    COALESCE(jo.contract_type, 'Autre') AS contract_type,
    CASE
        WHEN jo.published_at IS NULL THEN NULL
        ELSE TO_CHAR(DATE_TRUNC('day', jo.published_at), 'YYYYMMDD')::INT
    END AS published_date_key,
    jo.published_at::DATE AS published_date,
    jo.salary_min,
    jo.salary_max,
    COALESCE(dw.normalized_title, 'Unknown') AS normalized_title,
    COALESCE(dw.category, 'Other') AS category,
    COALESCE(dw.seniority_level, 'Mid') AS seniority_level,
    dw.demand_score,
    COALESCE(ARRAY_LENGTH(jo.required_skills, 1), 0) AS required_skill_count,
    COALESCE(ARRAY_LENGTH(dw.tech_stack, 1), 0) AS tech_stack_count,
    jo.created_at,
    jo.updated_at
FROM public.job_offers jo
LEFT JOIN public.dw_job_offers dw
    ON dw.offer_id = jo.id;

CREATE OR REPLACE VIEW powerbi.fact_skill_demand AS
SELECT
    jo.id AS offer_id,
    jo.source_id,
    LOWER(TRIM(skill.skill_name)) AS skill_name,
    CASE
        WHEN jo.published_at IS NULL THEN NULL
        ELSE TO_CHAR(DATE_TRUNC('day', jo.published_at), 'YYYYMMDD')::INT
    END AS published_date_key,
    jo.published_at::DATE AS published_date
FROM public.job_offers jo
CROSS JOIN LATERAL UNNEST(COALESCE(jo.required_skills, ARRAY[]::TEXT[])) AS skill(skill_name)
WHERE skill.skill_name IS NOT NULL
  AND TRIM(skill.skill_name) <> '';

CREATE OR REPLACE VIEW powerbi.fact_recommendation_events AS
SELECT
    rh.id AS recommendation_event_id,
    rh.candidate_id,
    rh.job_offer_id AS offer_id,
    rh.action,
    rh.similarity_score,
    (rh.score_breakdown ->> 'skill_overlap')::FLOAT AS score_skill_overlap,
    (rh.score_breakdown ->> 'embedding_similarity')::FLOAT AS score_embedding_similarity,
    (rh.score_breakdown ->> 'seniority_alignment')::FLOAT AS score_seniority_alignment,
    (rh.score_breakdown ->> 'location_preference')::FLOAT AS score_location_preference,
    TO_CHAR(DATE_TRUNC('day', rh.created_at), 'YYYYMMDD')::INT AS event_date_key,
    rh.created_at::DATE AS event_date,
    rh.created_at
FROM public.recommendation_history rh;

CREATE OR REPLACE VIEW powerbi.fact_pipeline_runs AS
SELECT
    pr.id AS pipeline_run_id,
    pr.stage,
    pr.status,
    pr.source_name,
    pr.rows_in,
    pr.rows_out,
    pr.rows_skipped,
    pr.rows_error,
    pr.duration_ms,
    pr.error_message,
    CASE
        WHEN pr.started_at IS NULL THEN NULL
        ELSE TO_CHAR(DATE_TRUNC('day', pr.started_at), 'YYYYMMDD')::INT
    END AS started_date_key,
    pr.started_at::DATE AS started_date,
    pr.started_at,
    pr.finished_at
FROM public.pipeline_runs pr;

-- ----------------------------------------------------------------------------
-- Permissions for Power BI users/roles
-- ----------------------------------------------------------------------------

GRANT USAGE ON SCHEMA powerbi TO service_role, authenticated, anon;
GRANT SELECT ON ALL TABLES IN SCHEMA powerbi TO service_role, authenticated, anon;
ALTER DEFAULT PRIVILEGES IN SCHEMA powerbi
GRANT SELECT ON TABLES TO service_role, authenticated, anon;
