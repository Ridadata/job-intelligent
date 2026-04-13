-- ============================================================================
-- 007 — Gold layer schema update
-- Adds missing columns to dw_job_offers for full enrichment pipeline.
-- ============================================================================

ALTER TABLE dw_job_offers
    ADD COLUMN IF NOT EXISTS category               TEXT,
    ADD COLUMN IF NOT EXISTS contract_type_standardized TEXT,
    ADD COLUMN IF NOT EXISTS dedup_key               TEXT;

CREATE INDEX IF NOT EXISTS idx_dw_offers_category ON dw_job_offers (category);
CREATE INDEX IF NOT EXISTS idx_dw_offers_dedup_key ON dw_job_offers (dedup_key);
