-- ============================================================================
-- Local development post-restore steps
-- Purpose:
--   1) Ensure required extensions exist
--   2) Disable RLS locally for easier development
--   3) Refresh analytics materialized views (if function exists)
--   4) Refresh planner stats
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

DO $$
DECLARE
    table_name text;
BEGIN
    FOR table_name IN
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = 'public'
          AND tablename IN (
              'sources',
              'raw_job_offers',
              'job_offers',
              'dw_job_offers',
              'candidates',
              'recommendations',
              'users',
              'candidate_profiles',
              'saved_jobs',
              'cv_documents',
              'applications',
              'recommendation_history',
              'pipeline_runs'
          )
    LOOP
        EXECUTE format('ALTER TABLE public.%I DISABLE ROW LEVEL SECURITY', table_name);
    END LOOP;
END $$;

DO $$
BEGIN
    IF to_regprocedure('refresh_all_analytics_views()') IS NOT NULL THEN
        PERFORM refresh_all_analytics_views();
    END IF;
END $$;

ANALYZE;
