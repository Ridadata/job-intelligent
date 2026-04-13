-- ============================================================================
-- Projet Job Intelligent — Functions: Candidate Matching & Profile Helpers
-- ============================================================================

-- ============================================================================
-- match_candidates_for_job — find best candidates for a given job
-- ============================================================================
CREATE OR REPLACE FUNCTION match_candidates_for_job(
    job_offer_id     UUID,
    match_threshold  FLOAT DEFAULT 0.60,
    match_count      INT DEFAULT 20
)
RETURNS TABLE (
    candidate_id         UUID,
    name                 TEXT,
    title                TEXT,
    skills               TEXT[],
    similarity           FLOAT
)
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    job_embedding vector(384);
BEGIN
    SELECT dw.embedding INTO job_embedding
    FROM dw_job_offers dw
    WHERE dw.offer_id = job_offer_id
      AND dw.embedding IS NOT NULL;

    IF job_embedding IS NULL THEN
        RAISE EXCEPTION 'Job offer % has no embedding', job_offer_id;
    END IF;

    RETURN QUERY
    SELECT
        cp.id,
        cp.name,
        cp.title,
        cp.skills,
        (1 - (cp.embedding <=> job_embedding))::FLOAT AS similarity
    FROM candidate_profiles cp
    WHERE
        cp.embedding IS NOT NULL
        AND (1 - (cp.embedding <=> job_embedding)) >= match_threshold
    ORDER BY similarity DESC
    LIMIT match_count;
END;
$$;

-- ============================================================================
-- match_jobs_for_candidate — find best jobs for a given candidate
-- ============================================================================
CREATE OR REPLACE FUNCTION match_jobs_for_candidate(
    p_candidate_id   UUID,
    match_threshold  FLOAT DEFAULT 0.60,
    match_count      INT DEFAULT 20
)
RETURNS TABLE (
    offer_id        UUID,
    title           TEXT,
    company         TEXT,
    location        TEXT,
    contract_type   TEXT,
    tech_stack      TEXT[],
    similarity      FLOAT
)
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    cand_embedding vector(384);
BEGIN
    SELECT cp.embedding INTO cand_embedding
    FROM candidate_profiles cp
    WHERE cp.id = p_candidate_id
      AND cp.embedding IS NOT NULL;

    IF cand_embedding IS NULL THEN
        RAISE EXCEPTION 'Candidate % has no embedding', p_candidate_id;
    END IF;

    RETURN QUERY
    SELECT
        dw.offer_id,
        jo.title,
        jo.company,
        jo.location,
        jo.contract_type,
        dw.tech_stack,
        (1 - (dw.embedding <=> cand_embedding))::FLOAT AS similarity
    FROM dw_job_offers dw
    JOIN job_offers jo ON jo.id = dw.offer_id
    WHERE
        dw.embedding IS NOT NULL
        AND (1 - (dw.embedding <=> cand_embedding)) >= match_threshold
    ORDER BY similarity DESC
    LIMIT match_count;
END;
$$;

-- ============================================================================
-- compute_profile_completeness — calculate percentage of filled fields
-- ============================================================================
CREATE OR REPLACE FUNCTION compute_profile_completeness(p_candidate_id UUID)
RETURNS INT
LANGUAGE plpgsql
AS $$
DECLARE
    score INT := 0;
    total INT := 8;
    rec   RECORD;
BEGIN
    SELECT * INTO rec FROM candidate_profiles WHERE id = p_candidate_id;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Candidate profile % not found', p_candidate_id;
    END IF;

    IF rec.name IS NOT NULL AND rec.name <> '' THEN score := score + 1; END IF;
    IF rec.title IS NOT NULL AND rec.title <> '' THEN score := score + 1; END IF;
    IF array_length(rec.skills, 1) > 0 THEN score := score + 1; END IF;
    IF rec.experience_years IS NOT NULL THEN score := score + 1; END IF;
    IF rec.education_level IS NOT NULL THEN score := score + 1; END IF;
    IF rec.location IS NOT NULL AND rec.location <> '' THEN score := score + 1; END IF;
    IF rec.salary_expectation IS NOT NULL THEN score := score + 1; END IF;
    IF array_length(rec.preferred_contract_types, 1) > 0 THEN score := score + 1; END IF;

    RETURN ROUND((score::FLOAT / total) * 100);
END;
$$;
