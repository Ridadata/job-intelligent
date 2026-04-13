"""ETL pipeline monitoring — logs run metrics to pipeline_runs table.

Every pipeline stage (ingest, transform, enrich, quality_check, refresh_views)
creates a run record that tracks row counts, duration, and errors.
"""

import logging
import time
from contextlib import contextmanager
from typing import Any, Generator, Optional

from etl.db import get_supabase_client

logger = logging.getLogger(__name__)


class PipelineRun:
    """Tracks a single ETL stage execution.

    Use as a context manager to automatically record start/end times
    and handle error logging.

    Args:
        stage: One of 'ingest', 'transform', 'enrich', 'quality_check', 'refresh_views'.
        source_name: Optional source name for ingest stages.
        metadata: Optional extra metadata dict.
    """

    def __init__(
        self,
        stage: str,
        source_name: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        self.stage = stage
        self.source_name = source_name
        self.metadata = metadata or {}
        self.rows_in = 0
        self.rows_out = 0
        self.rows_skipped = 0
        self.rows_error = 0
        self.run_id: Optional[str] = None
        self._start_time: Optional[float] = None

    def start(self) -> "PipelineRun":
        """Record the start of the pipeline run.

        Creates a row in pipeline_runs with status='running'.
        Handles schema mismatches gracefully.

        Returns:
            Self for chaining.
        """
        self._start_time = time.time()
        try:
            client = get_supabase_client()
            payload: dict[str, Any] = {
                "stage": self.stage,
                "status": "running",
            }
            # Only include optional fields if they have values
            if self.source_name:
                payload["source_name"] = self.source_name
            if self.metadata:
                payload["metadata"] = self.metadata
            result = client.table("pipeline_runs").insert(payload).execute()
            if result.data:
                self.run_id = result.data[0]["id"]
            logger.info("Pipeline run started: stage=%s, id=%s", self.stage, self.run_id)
        except Exception:
            logger.warning("Failed to create pipeline_runs record — continuing without tracking", exc_info=True)
        return self

    def finish(self, status: str = "success", error_message: Optional[str] = None) -> None:
        """Record the end of the pipeline run.

        Updates the pipeline_runs row with final metrics.

        Args:
            status: Final status ('success', 'failed', 'partial').
            error_message: Error details if status is 'failed'.
        """
        duration_ms = int((time.time() - (self._start_time or time.time())) * 1000)

        if not self.run_id:
            logger.warning("No run_id to finish — start() was not called or failed")
            return

        try:
            client = get_supabase_client()
            client.table("pipeline_runs").update({
                "status": status,
                "rows_in": self.rows_in,
                "rows_out": self.rows_out,
                "rows_skipped": self.rows_skipped,
                "rows_error": self.rows_error,
                "duration_ms": duration_ms,
                "error_message": error_message,
                "finished_at": "now()",
            }).eq("id", self.run_id).execute()
            logger.info(
                "Pipeline run finished: stage=%s, status=%s, in=%d, out=%d, skipped=%d, errors=%d, %dms",
                self.stage, status,
                self.rows_in, self.rows_out, self.rows_skipped, self.rows_error,
                duration_ms,
            )
        except Exception:
            logger.warning("Failed to update pipeline_runs record", exc_info=True)


@contextmanager
def track_pipeline(
    stage: str,
    source_name: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> Generator[PipelineRun, None, None]:
    """Context manager that tracks a pipeline stage execution.

    Usage::

        with track_pipeline("transform") as run:
            run.rows_in = 100
            # ... do work ...
            run.rows_out = 95
            run.rows_skipped = 5

    On exception, the run is marked as 'failed' with the error message.

    Args:
        stage: The pipeline stage name.
        source_name: Optional source identifier.
        metadata: Optional extra data to store.

    Yields:
        PipelineRun instance to record metrics on.
    """
    run = PipelineRun(stage, source_name, metadata)
    run.start()
    try:
        yield run
        status = "partial" if run.rows_error > 0 else "success"
        run.finish(status=status)
    except Exception as e:
        run.finish(status="failed", error_message=str(e)[:2000])
        raise
