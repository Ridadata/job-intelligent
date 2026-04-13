-- ============================================================================
-- Projet Job Intelligent — PostgreSQL Functions
-- ============================================================================

-- ============================================================================
-- match_job_offers — pgvector cosine similarity search
-- ============================================================================
CREATE OR REPLACE FUNCTION match_job_offers(
    query_embedding  vector(384),
    match_threshold  FLOAT DEFAULT 0.70,
    match_count      INT DEFAULT 10,
    filter_contract  TEXT DEFAULT NULL,
    filter_location  TEXT DEFAULT NULL
)
RETURNS TABLE (
    offer_id    UUID,
    title       TEXT,
    company     TEXT,
    location    TEXT,
    contract_type TEXT,
    similarity  FLOAT,
    tech_stack  TEXT[]
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
        (1 - (dw.embedding <=> query_embedding))::FLOAT AS similarity,
        dw.tech_stack
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
-- get_candidate_skills — helper to retrieve candidate skills as text
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
    FROM candidates
    WHERE id = p_candidate_id;

    IF result IS NULL THEN
        RAISE EXCEPTION 'Candidate % not found', p_candidate_id;
    END IF;

    RETURN result;
END;
$$;
