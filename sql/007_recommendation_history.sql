-- ============================================================================
-- 007 — Recommendation History
-- Tracks which recommendations were shown, clicked, and saved.
-- ============================================================================

CREATE TABLE IF NOT EXISTS recommendation_history (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    candidate_id    UUID NOT NULL REFERENCES candidate_profiles(id) ON DELETE CASCADE,
    job_offer_id    UUID NOT NULL REFERENCES job_offers(id) ON DELETE CASCADE,
    similarity_score FLOAT NOT NULL,
    score_breakdown JSONB DEFAULT '{}',
    action          TEXT NOT NULL DEFAULT 'shown'
                        CHECK (action IN ('shown', 'clicked', 'saved', 'dismissed')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_rec_history_candidate
    ON recommendation_history (candidate_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_rec_history_job
    ON recommendation_history (job_offer_id);

CREATE INDEX IF NOT EXISTS idx_rec_history_action
    ON recommendation_history (action);

-- ============================================================================
-- Semantic search function — query embedding → Gold table cosine search
-- Extends match_job_offers with additional return columns for search.
-- ============================================================================
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
