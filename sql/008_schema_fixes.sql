-- ============================================================================
-- 008 — Safe Schema Fixes (audit findings)
--
-- RUN THIS IN SUPABASE SQL EDITOR  (idempotent — safe to run multiple times)
--
-- Fixes:
--   0. Create recommendation_history table + semantic_search_jobs (from 007)
--   1. pipeline_runs: add missing columns from 006 if table was created by 004
--   2. updated_at triggers for users, candidate_profiles, applications
--   3. RLS policies for all Phase 3+ tables
--   4. Fix get_candidate_skills to query candidate_profiles
-- ============================================================================

-- ============================================================================
-- 0. Create recommendation_history + semantic_search_jobs (007 was never run)
-- ============================================================================

CREATE TABLE IF NOT EXISTS recommendation_history (
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    candidate_id     UUID NOT NULL REFERENCES candidate_profiles(id) ON DELETE CASCADE,
    job_offer_id     UUID NOT NULL REFERENCES job_offers(id) ON DELETE CASCADE,
    similarity_score FLOAT NOT NULL,
    score_breakdown  JSONB DEFAULT '{}',
    action           TEXT NOT NULL DEFAULT 'shown'
                         CHECK (action IN ('shown', 'clicked', 'saved', 'dismissed')),
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_rec_history_candidate
    ON recommendation_history (candidate_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_rec_history_job
    ON recommendation_history (job_offer_id);

CREATE INDEX IF NOT EXISTS idx_rec_history_action
    ON recommendation_history (action);

-- Semantic search function — query embedding → Gold table cosine search
CREATE OR REPLACE FUNCTION semantic_search_jobs(
    query_embedding  vector(384),
    match_threshold  FLOAT DEFAULT 0.30,
    match_count      INT DEFAULT 20,
    filter_contract  TEXT DEFAULT NULL,
    filter_location  TEXT DEFAULT NULL
)
RETURNS TABLE (
    offer_id      UUID,
    title         TEXT,
    company       TEXT,
    location      TEXT,
    contract_type TEXT,
    description   TEXT,
    similarity    FLOAT,
    tech_stack    TEXT[],
    published_at  TIMESTAMPTZ
)
LANGUAGE plpgsql
STABLE
AS $$
BEGIN
    RETURN QUERY
    SELECT
        dw.offer_id,
        jo.title,
        jo.company,
        jo.location,
        jo.contract_type,
        jo.description,
        (1 - (dw.embedding <=> query_embedding))::FLOAT AS similarity,
        dw.tech_stack,
        jo.published_at
    FROM dw_job_offers dw
    JOIN job_offers jo ON jo.id = dw.offer_id
    WHERE
        dw.embedding IS NOT NULL
        AND (1 - (dw.embedding <=> query_embedding)) >= match_threshold
        AND (filter_contract IS NULL OR jo.contract_type = filter_contract)
        AND (filter_location IS NULL OR jo.location ILIKE '%' || filter_location || '%')
    ORDER BY similarity DESC
    LIMIT match_count;
END;
$$;

-- ============================================================================
-- 1. Fix pipeline_runs columns (safe: ADD COLUMN IF NOT EXISTS)
-- 004 schema lacks source_name, rows_in, rows_out, rows_skipped, rows_error
-- 006 schema has them but lacks pipeline_name
-- This ensures ALL needed columns exist regardless of which ran first.
-- ============================================================================

ALTER TABLE pipeline_runs ADD COLUMN IF NOT EXISTS pipeline_name TEXT;
ALTER TABLE pipeline_runs ADD COLUMN IF NOT EXISTS source_name   TEXT;
ALTER TABLE pipeline_runs ADD COLUMN IF NOT EXISTS rows_in       INT DEFAULT 0;
ALTER TABLE pipeline_runs ADD COLUMN IF NOT EXISTS rows_out      INT DEFAULT 0;
ALTER TABLE pipeline_runs ADD COLUMN IF NOT EXISTS rows_skipped  INT DEFAULT 0;
ALTER TABLE pipeline_runs ADD COLUMN IF NOT EXISTS rows_error    INT DEFAULT 0;
ALTER TABLE pipeline_runs ADD COLUMN IF NOT EXISTS row_count     INT DEFAULT 0;

-- Relax the status CHECK constraint to include 'partial' (used by ETL)
ALTER TABLE pipeline_runs DROP CONSTRAINT IF EXISTS pipeline_runs_stage_check;
ALTER TABLE pipeline_runs DROP CONSTRAINT IF EXISTS pipeline_runs_status_check;

ALTER TABLE pipeline_runs ADD CONSTRAINT pipeline_runs_status_check
    CHECK (status IN ('running', 'success', 'failed', 'partial'));

-- ============================================================================
-- 2. updated_at triggers for new tables
-- ============================================================================

-- Reuse the existing trigger function from 001_schema.sql
DROP TRIGGER IF EXISTS set_updated_at ON users;
CREATE TRIGGER set_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION trigger_set_updated_at();

DROP TRIGGER IF EXISTS set_updated_at ON candidate_profiles;
CREATE TRIGGER set_updated_at
    BEFORE UPDATE ON candidate_profiles
    FOR EACH ROW
    EXECUTE FUNCTION trigger_set_updated_at();

DROP TRIGGER IF EXISTS set_updated_at ON applications;
CREATE TRIGGER set_updated_at
    BEFORE UPDATE ON applications
    FOR EACH ROW
    EXECUTE FUNCTION trigger_set_updated_at();

-- ============================================================================
-- 3. RLS policies for all Phase 3+ tables
-- ============================================================================

-- users
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "service_role_all_users" ON users;
CREATE POLICY "service_role_all_users" ON users
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- candidate_profiles
ALTER TABLE candidate_profiles ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "service_role_all_candidate_profiles" ON candidate_profiles;
CREATE POLICY "service_role_all_candidate_profiles" ON candidate_profiles
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- saved_jobs
ALTER TABLE saved_jobs ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "service_role_all_saved_jobs" ON saved_jobs;
CREATE POLICY "service_role_all_saved_jobs" ON saved_jobs
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- cv_documents
ALTER TABLE cv_documents ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "service_role_all_cv_documents" ON cv_documents;
CREATE POLICY "service_role_all_cv_documents" ON cv_documents
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- applications
ALTER TABLE applications ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "service_role_all_applications" ON applications;
CREATE POLICY "service_role_all_applications" ON applications
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- recommendation_history
ALTER TABLE recommendation_history ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "service_role_all_recommendation_history" ON recommendation_history;
CREATE POLICY "service_role_all_recommendation_history" ON recommendation_history
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- pipeline_runs
ALTER TABLE pipeline_runs ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "service_role_all_pipeline_runs" ON pipeline_runs;
CREATE POLICY "service_role_all_pipeline_runs" ON pipeline_runs
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- ============================================================================
-- 4. Fix get_candidate_skills to use candidate_profiles (not orphan candidates)
-- ============================================================================
CREATE OR REPLACE FUNCTION get_candidate_skills(p_candidate_id UUID)
RETURNS TEXT
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    result TEXT;
BEGIN
    SELECT array_to_string(skills, ' ')
    INTO result
    FROM candidate_profiles
    WHERE id = p_candidate_id;

    IF result IS NULL THEN
        RAISE EXCEPTION 'Candidate % not found', p_candidate_id;
    END IF;

    RETURN result;
END;
$$;
