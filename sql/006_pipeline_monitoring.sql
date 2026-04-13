-- ============================================================================
-- 006 — Pipeline Monitoring & Data Quality
-- Adds pipeline_runs table for ETL observability.
-- ============================================================================

-- ── pipeline_runs — tracks every ETL stage execution ────────────────────────
CREATE TABLE IF NOT EXISTS pipeline_runs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    stage           TEXT NOT NULL CHECK (stage IN (
                        'ingest', 'transform', 'enrich', 'quality_check', 'refresh_views'
                    )),
    status          TEXT NOT NULL DEFAULT 'running' CHECK (status IN (
                        'running', 'success', 'failed', 'partial'
                    )),
    source_name     TEXT,                           -- NULL for stages that span all sources
    rows_in         INT NOT NULL DEFAULT 0,         -- rows read
    rows_out        INT NOT NULL DEFAULT 0,         -- rows written
    rows_skipped    INT NOT NULL DEFAULT 0,         -- rows skipped (invalid / dedup / non-data)
    rows_error      INT NOT NULL DEFAULT 0,         -- rows that caused errors
    duration_ms     INT,
    error_message   TEXT,
    metadata        JSONB DEFAULT '{}',             -- extra info: batch_size, model_name, etc.
    started_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ── Indexes ─────────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_pipeline_runs_stage      ON pipeline_runs (stage);
CREATE INDEX IF NOT EXISTS idx_pipeline_runs_status     ON pipeline_runs (status);
CREATE INDEX IF NOT EXISTS idx_pipeline_runs_started_at ON pipeline_runs (started_at DESC);
