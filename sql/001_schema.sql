-- ============================================================================
-- Projet Job Intelligent — Database Schema (Supabase / PostgreSQL 15)
-- All statements are idempotent: IF NOT EXISTS / ON CONFLICT DO NOTHING
-- ============================================================================

-- ── Extensions ──────────────────────────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- ============================================================================
-- 1. sources — scraping source platforms
-- ============================================================================
CREATE TABLE IF NOT EXISTS sources (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            TEXT NOT NULL UNIQUE,
    base_url        TEXT,
    last_scraped_at TIMESTAMPTZ
);

-- Seed default sources (idempotent)
INSERT INTO sources (name, base_url)
VALUES
    ('indeed',        'https://fr.indeed.com'),
    ('linkedin',      'https://www.linkedin.com/jobs'),
    ('france_travail', 'https://francetravail.io/data/api'),
    ('welcometothejungle', 'https://www.welcometothejungle.com')
ON CONFLICT (name) DO NOTHING;

-- ============================================================================
-- 2. raw_job_offers — Bronze layer (raw scraped JSON)
-- ============================================================================
CREATE TABLE IF NOT EXISTS raw_job_offers (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id   UUID NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    external_id TEXT NOT NULL,
    raw_json    JSONB NOT NULL,
    scraped_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    processed   BOOLEAN NOT NULL DEFAULT false,

    UNIQUE (source_id, external_id)
);

CREATE INDEX IF NOT EXISTS idx_raw_offers_unprocessed
    ON raw_job_offers (processed)
    WHERE processed = false;

-- ============================================================================
-- 3. job_offers — Silver layer (cleaned, normalized)
-- ============================================================================
CREATE TABLE IF NOT EXISTS job_offers (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id       UUID NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    raw_offer_id    UUID REFERENCES raw_job_offers(id) ON DELETE SET NULL,
    title           TEXT NOT NULL,
    company         TEXT,
    location        TEXT,
    contract_type   TEXT CHECK (contract_type IN ('CDI', 'CDD', 'Freelance', 'Stage', 'Alternance', 'Autre')),
    salary_min      FLOAT,
    salary_max      FLOAT,
    required_skills TEXT[],
    description     TEXT,
    published_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_job_offers_source
    ON job_offers (source_id);

CREATE INDEX IF NOT EXISTS idx_job_offers_contract
    ON job_offers (contract_type);

CREATE INDEX IF NOT EXISTS idx_job_offers_location
    ON job_offers USING gin (to_tsvector('french', coalesce(location, '')));

CREATE INDEX IF NOT EXISTS idx_job_offers_skills
    ON job_offers USING gin (required_skills);

-- ============================================================================
-- 4. dw_job_offers — Gold layer (enriched with embeddings)
-- ============================================================================
CREATE TABLE IF NOT EXISTS dw_job_offers (
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    offer_id         UUID NOT NULL REFERENCES job_offers(id) ON DELETE CASCADE,
    embedding        vector(384),
    normalized_title TEXT,
    seniority_level  TEXT CHECK (seniority_level IN ('Junior', 'Mid', 'Senior')),
    tech_stack       TEXT[],
    demand_score     FLOAT,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),

    UNIQUE (offer_id)
);

-- HNSW index for fast cosine similarity search
CREATE INDEX IF NOT EXISTS idx_dw_offers_embedding
    ON dw_job_offers
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

CREATE INDEX IF NOT EXISTS idx_dw_offers_seniority
    ON dw_job_offers (seniority_level);

-- ============================================================================
-- 5. candidates
-- ============================================================================
CREATE TABLE IF NOT EXISTS candidates (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email               TEXT NOT NULL UNIQUE,
    current_title       TEXT,
    skills              TEXT[],
    years_experience    INT,
    preferred_location  TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================================
-- 6. recommendations
-- ============================================================================
CREATE TABLE IF NOT EXISTS recommendations (
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    candidate_id     UUID NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    offer_id         UUID NOT NULL REFERENCES job_offers(id) ON DELETE CASCADE,
    similarity_score FLOAT NOT NULL,
    matched_skills   TEXT[],
    generated_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_recommendations_candidate
    ON recommendations (candidate_id);

CREATE INDEX IF NOT EXISTS idx_recommendations_score
    ON recommendations (similarity_score DESC);

-- ============================================================================
-- 7. scraping_logs
-- ============================================================================
CREATE TABLE IF NOT EXISTS scraping_logs (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id     UUID REFERENCES sources(id) ON DELETE SET NULL,
    status        TEXT NOT NULL CHECK (status IN ('success', 'failed', 'partial')),
    rows_inserted INT DEFAULT 0,
    duration_ms   INT,
    error_message TEXT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_scraping_logs_source
    ON scraping_logs (source_id, created_at DESC);

-- ============================================================================
-- Trigger: auto-update updated_at
-- ============================================================================
CREATE OR REPLACE FUNCTION trigger_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to job_offers
DROP TRIGGER IF EXISTS set_updated_at ON job_offers;
CREATE TRIGGER set_updated_at
    BEFORE UPDATE ON job_offers
    FOR EACH ROW
    EXECUTE FUNCTION trigger_set_updated_at();

-- Apply trigger to candidates
DROP TRIGGER IF EXISTS set_updated_at ON candidates;
CREATE TRIGGER set_updated_at
    BEFORE UPDATE ON candidates
    FOR EACH ROW
    EXECUTE FUNCTION trigger_set_updated_at();

-- ============================================================================
-- Row Level Security (RLS)
-- Enable on all tables, allow service_role full access
-- ============================================================================

-- sources
ALTER TABLE sources ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "service_role_all_sources" ON sources;
CREATE POLICY "service_role_all_sources" ON sources
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- raw_job_offers
ALTER TABLE raw_job_offers ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "service_role_all_raw_job_offers" ON raw_job_offers;
CREATE POLICY "service_role_all_raw_job_offers" ON raw_job_offers
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- job_offers
ALTER TABLE job_offers ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "service_role_all_job_offers" ON job_offers;
CREATE POLICY "service_role_all_job_offers" ON job_offers
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- dw_job_offers
ALTER TABLE dw_job_offers ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "service_role_all_dw_job_offers" ON dw_job_offers;
CREATE POLICY "service_role_all_dw_job_offers" ON dw_job_offers
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- candidates
ALTER TABLE candidates ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "service_role_all_candidates" ON candidates;
CREATE POLICY "service_role_all_candidates" ON candidates
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- recommendations
ALTER TABLE recommendations ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "service_role_all_recommendations" ON recommendations;
CREATE POLICY "service_role_all_recommendations" ON recommendations
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- scraping_logs
ALTER TABLE scraping_logs ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "service_role_all_scraping_logs" ON scraping_logs;
CREATE POLICY "service_role_all_scraping_logs" ON scraping_logs
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Allow authenticated users to read job_offers and dw_job_offers
DROP POLICY IF EXISTS "authenticated_read_job_offers" ON job_offers;
CREATE POLICY "authenticated_read_job_offers" ON job_offers
    FOR SELECT
    TO authenticated
    USING (true);

DROP POLICY IF EXISTS "authenticated_read_dw_job_offers" ON dw_job_offers;
CREATE POLICY "authenticated_read_dw_job_offers" ON dw_job_offers
    FOR SELECT
    TO authenticated
    USING (true);

-- Allow authenticated users to manage their own candidate profile
DROP POLICY IF EXISTS "candidates_own_profile" ON candidates;
CREATE POLICY "candidates_own_profile" ON candidates
    FOR ALL
    TO authenticated
    USING (id = auth.uid())
    WITH CHECK (id = auth.uid());

-- Allow authenticated users to read their own recommendations
DROP POLICY IF EXISTS "recommendations_own" ON recommendations;
CREATE POLICY "recommendations_own" ON recommendations
    FOR SELECT
    TO authenticated
    USING (candidate_id = auth.uid());
