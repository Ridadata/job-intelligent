-- ============================================================================
-- Projet Job Intelligent — Schema Extension: Auth, Candidates, CV, Product
-- All statements are idempotent: IF NOT EXISTS / ON CONFLICT DO NOTHING
-- ============================================================================

-- ============================================================================
-- 1. users — authentication accounts
-- ============================================================================
CREATE TABLE IF NOT EXISTS users (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email           TEXT NOT NULL UNIQUE,
    password_hash   TEXT NOT NULL,
    role            TEXT NOT NULL DEFAULT 'candidate'
                        CHECK (role IN ('candidate', 'admin')),
    is_active       BOOLEAN NOT NULL DEFAULT true,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_users_email
    ON users (email);

-- ============================================================================
-- 2. candidate_profiles — full candidate data (replaces minimal candidates)
-- ============================================================================
CREATE TABLE IF NOT EXISTS candidate_profiles (
    id                       UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id                  UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    name                     TEXT,
    title                    TEXT,
    skills                   TEXT[] DEFAULT '{}',
    experience_years         INT,
    education_level          TEXT CHECK (education_level IN (
                                 'Bac', 'Bac+2', 'Bac+3', 'Bac+5', 'Doctorat', 'Autre'
                             )),
    location                 TEXT,
    salary_expectation       FLOAT,
    preferred_contract_types TEXT[] DEFAULT '{}',
    profile_completeness     INT NOT NULL DEFAULT 0
                                 CHECK (profile_completeness BETWEEN 0 AND 100),
    embedding                vector(384),
    created_at               TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at               TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_candidate_profiles_user
    ON candidate_profiles (user_id);

CREATE INDEX IF NOT EXISTS idx_candidate_profiles_skills
    ON candidate_profiles USING gin (skills);

CREATE INDEX IF NOT EXISTS idx_candidate_profiles_embedding
    ON candidate_profiles
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- ============================================================================
-- 3. cv_documents — uploaded CVs and NLP parsing results
-- ============================================================================
CREATE TABLE IF NOT EXISTS cv_documents (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    candidate_id      UUID NOT NULL REFERENCES candidate_profiles(id) ON DELETE CASCADE,
    file_path         TEXT NOT NULL,
    file_type         TEXT NOT NULL CHECK (file_type IN ('pdf', 'docx')),
    file_size_bytes   INT,
    raw_text          TEXT,
    parsed_skills     TEXT[] DEFAULT '{}',
    parsed_experience TEXT,
    parsed_education  TEXT,
    parsing_status    TEXT NOT NULL DEFAULT 'pending'
                          CHECK (parsing_status IN ('pending', 'processing', 'success', 'failed')),
    parsing_error     TEXT,
    parsed_at         TIMESTAMPTZ,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_cv_documents_candidate
    ON cv_documents (candidate_id);

CREATE INDEX IF NOT EXISTS idx_cv_documents_status
    ON cv_documents (parsing_status)
    WHERE parsing_status IN ('pending', 'processing');

-- ============================================================================
-- 4. saved_jobs — candidate bookmarks
-- ============================================================================
CREATE TABLE IF NOT EXISTS saved_jobs (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    candidate_id  UUID NOT NULL REFERENCES candidate_profiles(id) ON DELETE CASCADE,
    job_offer_id  UUID NOT NULL REFERENCES job_offers(id) ON DELETE CASCADE,
    saved_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    UNIQUE (candidate_id, job_offer_id)
);

CREATE INDEX IF NOT EXISTS idx_saved_jobs_candidate
    ON saved_jobs (candidate_id, saved_at DESC);

-- ============================================================================
-- 5. applications — candidate applications tracking
-- ============================================================================
CREATE TABLE IF NOT EXISTS applications (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    candidate_id  UUID NOT NULL REFERENCES candidate_profiles(id) ON DELETE CASCADE,
    job_offer_id  UUID NOT NULL REFERENCES job_offers(id) ON DELETE CASCADE,
    status        TEXT NOT NULL DEFAULT 'applied'
                      CHECK (status IN ('applied', 'viewed', 'interview', 'rejected', 'accepted')),
    applied_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),

    UNIQUE (candidate_id, job_offer_id)
);

CREATE INDEX IF NOT EXISTS idx_applications_candidate
    ON applications (candidate_id, applied_at DESC);

CREATE INDEX IF NOT EXISTS idx_applications_status
    ON applications (status);

-- ============================================================================
-- 6. pipeline_runs — ETL monitoring
-- ============================================================================
CREATE TABLE IF NOT EXISTS pipeline_runs (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pipeline_name TEXT NOT NULL,
    stage         TEXT NOT NULL,
    status        TEXT NOT NULL CHECK (status IN ('running', 'success', 'failed')),
    row_count     INT DEFAULT 0,
    duration_ms   INT,
    error_message TEXT,
    metadata      JSONB DEFAULT '{}',
    started_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at   TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_pipeline_runs_pipeline
    ON pipeline_runs (pipeline_name, started_at DESC);

CREATE INDEX IF NOT EXISTS idx_pipeline_runs_status
    ON pipeline_runs (status)
    WHERE status = 'running';

-- ============================================================================
-- 7. Seed new sources for API-based ingestion
-- ============================================================================
INSERT INTO sources (name, base_url)
VALUES
    ('adzuna',         'https://api.adzuna.com'),
    ('jsearch',        'https://jsearch.p.rapidapi.com'),
    ('rekrute',        'https://www.rekrute.com'),
    ('emploi_ma',      'https://www.emploi.ma')
ON CONFLICT (name) DO NOTHING;
