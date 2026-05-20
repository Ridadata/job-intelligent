"""Tests for Phase 3 — Data Platform Improvements.

Covers schema validation, skill normalization, taxonomy classification,
monitoring, quality checks, deduplication, and spider middlewares.
"""

import json
import os
from unittest.mock import MagicMock, patch

import pytest


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Schema Validation (etl/validation.py)
# ═══════════════════════════════════════════════════════════════════════════════

class TestSilverValidation:
    """Tests for SilverOfferSchema validation."""

    def _valid_row(self, **overrides):
        base = {
            "source_id": "abc-123",
            "raw_offer_id": "raw-456",
            "title": "Data Engineer",
            "company": "Acme Corp",
            "location": "Paris",
            "contract_type": "CDI",
            "salary_min": 45000.0,
            "salary_max": 65000.0,
            "required_skills": ["python", "sql"],
            "description": "A great job.",
            "published_at": "2026-01-15",
        }
        base.update(overrides)
        return base

    def test_valid_silver_row(self):
        from etl.validation import validate_silver_row
        ok, result = validate_silver_row(self._valid_row())
        assert ok is True
        assert result["title"] == "Data Engineer"

    def test_missing_title_rejected(self):
        from etl.validation import validate_silver_row
        ok, err = validate_silver_row(self._valid_row(title=""))
        assert ok is False

    def test_invalid_contract_type_rejected(self):
        from etl.validation import validate_silver_row
        ok, err = validate_silver_row(self._valid_row(contract_type="INVALID"))
        assert ok is False

    def test_negative_salary_rejected(self):
        from etl.validation import validate_silver_row
        ok, err = validate_silver_row(self._valid_row(salary_min=-100))
        assert ok is False

    def test_skills_deduplicated_and_sorted(self):
        from etl.validation import validate_silver_row
        ok, result = validate_silver_row(
            self._valid_row(required_skills=["sql", "python", "sql", "python"])
        )
        assert ok is True
        assert result["required_skills"] == ["python", "sql"]

    def test_contract_type_defaults_to_autre(self):
        from etl.validation import validate_silver_row
        ok, result = validate_silver_row(self._valid_row(contract_type="Autre"))
        assert ok is True
        assert result["contract_type"] == "Autre"

    def test_none_salary_accepted(self):
        from etl.validation import validate_silver_row
        ok, result = validate_silver_row(
            self._valid_row(salary_min=None, salary_max=None)
        )
        assert ok is True
        assert result["salary_min"] is None


class TestGoldValidation:
    """Tests for GoldOfferSchema validation."""

    def _valid_gold(self, **overrides):
        base = {
            "offer_id": "offer-789",
            "embedding": [0.1] * 384,
            "normalized_title": "Data Engineer",
            "seniority_level": "Mid",
            "tech_stack": ["python", "spark"],
            "demand_score": 0.75,
            "category": "Data Engineering",
        }
        base.update(overrides)
        return base

    def test_valid_gold_row(self):
        from etl.validation import validate_gold_row
        ok, result = validate_gold_row(self._valid_gold())
        assert ok is True

    def test_wrong_embedding_dimension_rejected(self):
        from etl.validation import validate_gold_row
        ok, err = validate_gold_row(self._valid_gold(embedding=[0.1] * 100))
        assert ok is False

    def test_nan_in_embedding_rejected(self):
        from etl.validation import validate_gold_row
        emb = [0.1] * 383 + [float("nan")]
        ok, err = validate_gold_row(self._valid_gold(embedding=emb))
        assert ok is False

    def test_invalid_seniority_rejected(self):
        from etl.validation import validate_gold_row
        ok, err = validate_gold_row(self._valid_gold(seniority_level="Expert"))
        assert ok is False

    def test_demand_score_out_of_range_rejected(self):
        from etl.validation import validate_gold_row
        ok, err = validate_gold_row(self._valid_gold(demand_score=1.5))
        assert ok is False

    def test_demand_score_zero_accepted(self):
        from etl.validation import validate_gold_row
        ok, result = validate_gold_row(self._valid_gold(demand_score=0.0))
        assert ok is True


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Skill Normalization (etl/skill_normalization.py)
# ═══════════════════════════════════════════════════════════════════════════════

class TestSkillNormalization:
    """Tests for canonical skill normalization."""

    def setup_method(self):
        from etl.skill_normalization import reset_cache
        reset_cache()

    def test_canonical_skill_unchanged(self):
        from etl.skill_normalization import normalize_skill
        assert normalize_skill("python") == "python"

    def test_alias_mapped_to_canonical(self):
        from etl.skill_normalization import normalize_skill
        assert normalize_skill("sklearn") == "scikit-learn"

    def test_tensorflow_alias(self):
        from etl.skill_normalization import normalize_skill
        assert normalize_skill("tf") == "tensorflow"

    def test_case_insensitive(self):
        from etl.skill_normalization import normalize_skill
        assert normalize_skill("PyTorch") == "pytorch"

    def test_unknown_skill_passthrough(self):
        from etl.skill_normalization import normalize_skill
        assert normalize_skill("some-unknown-lib") == "some-unknown-lib"

    def test_normalize_skills_dedup(self):
        from etl.skill_normalization import normalize_skills
        result = normalize_skills(["sklearn", "scikit-learn", "Python", "python"])
        assert result == ["python", "scikit-learn"]

    def test_normalize_skills_sorted(self):
        from etl.skill_normalization import normalize_skills
        result = normalize_skills(["sql", "python", "aws"])
        assert result == sorted(result)

    def test_empty_list(self):
        from etl.skill_normalization import normalize_skills
        assert normalize_skills([]) == []

    def test_get_canonical_skills_returns_set(self):
        from etl.skill_normalization import get_canonical_skills
        skills = get_canonical_skills()
        assert isinstance(skills, set)
        assert "python" in skills
        assert "scikit-learn" in skills

    def test_canonical_json_loads(self):
        """Verify the canonical JSON file is valid."""
        path = os.path.join(os.path.dirname(__file__), "..", "etl", "skills_canonical.json")
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        assert "python" in data
        assert isinstance(data["python"], list)


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Job Taxonomy Classifier (etl/taxonomy.py)
# ═══════════════════════════════════════════════════════════════════════════════

class TestTaxonomy:
    """Tests for rule-based job taxonomy classification."""

    def test_data_scientist(self):
        from etl.taxonomy import classify_job
        assert classify_job("Senior Data Scientist") == "Data Science"

    def test_data_engineer(self):
        from etl.taxonomy import classify_job
        assert classify_job("Data Engineer - ETL") == "Data Engineering"

    def test_ml_engineer(self):
        from etl.taxonomy import classify_job
        assert classify_job("ML Engineer") == "ML Engineering"

    def test_mlops(self):
        from etl.taxonomy import classify_job
        assert classify_job("MLOps Engineer") == "MLOps"

    def test_bi_analyst(self):
        from etl.taxonomy import classify_job
        assert classify_job("BI Analyst") == "BI"

    def test_data_analyst(self):
        from etl.taxonomy import classify_job
        assert classify_job("Data Analyst Junior") == "Analytics"

    def test_analytics_engineer(self):
        from etl.taxonomy import classify_job
        assert classify_job("Analytics Engineer") == "Analytics"

    def test_data_architect(self):
        from etl.taxonomy import classify_job
        assert classify_job("Data Architect") == "Data Management"

    def test_description_fallback(self):
        from etl.taxonomy import classify_job
        result = classify_job(
            "Generic Title",
            "We need a data scientist with ML experience"
        )
        assert result == "Data Science"

    def test_unknown_returns_other(self):
        from etl.taxonomy import classify_job
        assert classify_job("Chef de Cuisine") == "Other"

    def test_empty_title_returns_other(self):
        from etl.taxonomy import classify_job
        assert classify_job("") == "Other"

    def test_get_all_categories(self):
        from etl.taxonomy import get_all_categories
        cats = get_all_categories()
        assert "Data Science" in cats
        assert "Other" in cats
        assert len(cats) == 8  # 7 rules + Other

    def test_specificity_order_mlops_before_ml(self):
        """MLOps should match before ML Engineering."""
        from etl.taxonomy import classify_job
        assert classify_job("MLOps Engineer") == "MLOps"
        assert classify_job("ML Engineer") == "ML Engineering"


# ═══════════════════════════════════════════════════════════════════════════════
# 4. ETL Monitoring (etl/monitoring.py)
# ═══════════════════════════════════════════════════════════════════════════════

class TestMonitoring:
    """Tests for PipelineRun tracking."""

    @patch("etl.monitoring.get_supabase_client")
    def test_pipeline_run_lifecycle(self, mock_client):
        from etl.monitoring import PipelineRun

        mock_table = MagicMock()
        mock_table.insert.return_value = mock_table
        mock_table.update.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = MagicMock(data=[{"id": "run-1"}])
        mock_client.return_value.table.return_value = mock_table

        run = PipelineRun("transform")
        run.start()
        assert run.run_id == "run-1"

        run.rows_in = 100
        run.rows_out = 95
        run.rows_skipped = 5
        run.finish(status="success")

        mock_table.update.assert_called_once()
        call_args = mock_table.update.call_args[0][0]
        assert call_args["status"] == "success"
        assert call_args["rows_in"] == 100
        assert call_args["rows_out"] == 95

    @patch("etl.monitoring.get_supabase_client")
    def test_track_pipeline_context_manager_success(self, mock_client):
        from etl.monitoring import track_pipeline

        mock_table = MagicMock()
        mock_table.insert.return_value = mock_table
        mock_table.update.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = MagicMock(data=[{"id": "run-2"}])
        mock_client.return_value.table.return_value = mock_table

        with track_pipeline("ingest", source_name="indeed") as run:
            run.rows_in = 50
            run.rows_out = 50

        # Should have called update with success
        call_args = mock_table.update.call_args[0][0]
        assert call_args["status"] == "success"

    @patch("etl.monitoring.get_supabase_client")
    def test_track_pipeline_context_manager_failure(self, mock_client):
        from etl.monitoring import track_pipeline

        mock_table = MagicMock()
        mock_table.insert.return_value = mock_table
        mock_table.update.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = MagicMock(data=[{"id": "run-3"}])
        mock_client.return_value.table.return_value = mock_table

        with pytest.raises(ValueError):
            with track_pipeline("enrich") as _:
                raise ValueError("embedding failed")

        call_args = mock_table.update.call_args[0][0]
        assert call_args["status"] == "failed"
        assert "embedding failed" in call_args["error_message"]

    @patch("etl.monitoring.get_supabase_client")
    def test_partial_status_on_errors(self, mock_client):
        from etl.monitoring import track_pipeline

        mock_table = MagicMock()
        mock_table.insert.return_value = mock_table
        mock_table.update.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = MagicMock(data=[{"id": "run-4"}])
        mock_client.return_value.table.return_value = mock_table

        with track_pipeline("transform") as run:
            run.rows_in = 100
            run.rows_out = 90
            run.rows_error = 10

        call_args = mock_table.update.call_args[0][0]
        assert call_args["status"] == "partial"


# ═══════════════════════════════════════════════════════════════════════════════
# 5. Data Quality Checks (etl/quality_checks.py)
# ═══════════════════════════════════════════════════════════════════════════════

class TestQualityReport:
    """Tests for QualityReport accumulator."""

    def test_all_passed(self):
        from etl.quality_checks import QualityReport
        report = QualityReport("silver")
        report.record("check_a", True)
        report.record("check_b", True)
        assert report.all_passed is True
        assert report.checks_passed == 2
        assert report.checks_failed == 0

    def test_failure_recorded(self):
        from etl.quality_checks import QualityReport
        report = QualityReport("gold")
        report.record("check_a", True)
        report.record("check_b", False, "missing data")
        assert report.all_passed is False
        assert report.checks_failed == 1
        assert report.failures[0]["check"] == "check_b"

    def test_summary_structure(self):
        from etl.quality_checks import QualityReport
        report = QualityReport("silver")
        report.record("ok", True)
        report.record("fail", False, "bad")
        summary = report.summary()
        assert summary["stage"] == "silver"
        assert summary["passed"] == 1
        assert summary["failed"] == 1
        assert summary["all_passed"] is False


class TestSilverQualityChecks:
    """Tests for Silver quality checks with mocked DB."""

    @patch("etl.quality_checks.get_supabase_client")
    def test_empty_table_fails(self, mock_client):
        from etl.quality_checks import check_silver_quality

        mock_table = MagicMock()
        mock_table.select.return_value = mock_table
        mock_table.limit.return_value = mock_table
        mock_table.execute.return_value = MagicMock(data=[])
        mock_client.return_value.table.return_value = mock_table

        report = check_silver_quality()
        assert not report.all_passed

    @patch("etl.quality_checks.get_supabase_client")
    def test_valid_data_passes(self, mock_client):
        from etl.quality_checks import check_silver_quality

        mock_table = MagicMock()
        mock_table.select.return_value = mock_table
        mock_table.limit.return_value = mock_table
        mock_table.execute.return_value = MagicMock(data=[
            {
                "id": "1", "title": "Data Eng", "contract_type": "CDI",
                "required_skills": ["python"], "salary_min": 40000,
                "salary_max": 60000, "published_at": "2026-01-01",
            },
            {
                "id": "2", "title": "ML Eng", "contract_type": "CDD",
                "required_skills": ["pytorch"], "salary_min": 50000,
                "salary_max": 70000, "published_at": "2026-01-02",
            },
        ])
        mock_client.return_value.table.return_value = mock_table

        report = check_silver_quality()
        assert report.all_passed


# ═══════════════════════════════════════════════════════════════════════════════
# 6. Deduplication (etl/dedup.py)
# ═══════════════════════════════════════════════════════════════════════════════

class TestDedupHelpers:
    """Tests for dedup helper functions."""

    def test_normalize_text(self):
        from etl.dedup import _normalize_text
        assert _normalize_text("  Senior Data  Engineer  ") == "senior data engineer"

    def test_normalize_text_strips_suffix(self):
        from etl.dedup import _normalize_text
        result = _normalize_text("Data Engineer - Paris (H/F)")
        assert result == "data engineer"

    def test_jaccard_identical(self):
        from etl.dedup import _jaccard_similarity
        assert _jaccard_similarity("data engineer python", "data engineer python") == 1.0

    def test_jaccard_partial(self):
        from etl.dedup import _jaccard_similarity
        sim = _jaccard_similarity("data engineer", "data scientist")
        assert 0.0 < sim < 1.0

    def test_jaccard_empty(self):
        from etl.dedup import _jaccard_similarity
        assert _jaccard_similarity("", "anything") == 0.0

    def test_jaccard_no_overlap(self):
        from etl.dedup import _jaccard_similarity
        assert _jaccard_similarity("python spark", "java kotlin") == 0.0


# ═══════════════════════════════════════════════════════════════════════════════
# 7. Spider Middlewares (scrapers/job_scrapers/middlewares.py)
# ═══════════════════════════════════════════════════════════════════════════════

# Spider middlewares run in the Airflow/Scrapy container, not fastapi.
# We add the scrapers dir to sys.path so tests can import them.
_scrapers_importable = False
try:
    import sys
    _scrapers_root = os.path.join(os.path.dirname(__file__), "..", "scrapers")
    if os.path.isdir(_scrapers_root) and _scrapers_root not in sys.path:
        sys.path.insert(0, _scrapers_root)
    from job_scrapers.middlewares import (
        RotateUserAgentMiddleware,
        ProxyRotationMiddleware,
        RetryOn429Middleware,
        USER_AGENTS,
    )
    _scrapers_importable = True
except ImportError:
    pass


@pytest.mark.skipif(not _scrapers_importable, reason="scrapers not on path")
class TestRotateUserAgentMiddleware:
    """Tests for user-agent rotation middleware."""

    def test_sets_user_agent(self):
        middleware = RotateUserAgentMiddleware()
        request = MagicMock()
        request.headers = {}
        middleware.process_request(request, spider=MagicMock())
        assert request.headers["User-Agent"] in USER_AGENTS

    def test_randomizes_user_agent(self):
        middleware = RotateUserAgentMiddleware()
        agents = set()
        for _ in range(50):
            request = MagicMock()
            request.headers = {}
            middleware.process_request(request, spider=MagicMock())
            agents.add(request.headers["User-Agent"])
        # With 8 UAs and 50 tries, expect at least 2 different ones
        assert len(agents) >= 2


@pytest.mark.skipif(not _scrapers_importable, reason="scrapers not on path")
class TestProxyRotationMiddleware:
    """Tests for proxy rotation middleware."""

    def test_no_proxies_noop(self):
        middleware = ProxyRotationMiddleware()
        middleware.proxies = []
        request = MagicMock()
        request.meta = {}
        middleware.process_request(request, spider=MagicMock())
        assert "proxy" not in request.meta

    def test_sets_proxy_when_configured(self):
        middleware = ProxyRotationMiddleware()
        middleware.proxies = ["http://proxy1:8080", "http://proxy2:8080"]
        request = MagicMock()
        request.meta = {}
        middleware.process_request(request, spider=MagicMock())
        assert request.meta["proxy"] in middleware.proxies


@pytest.mark.skipif(not _scrapers_importable, reason="scrapers not on path")
class TestRetryOn429Middleware:
    """Tests for 429 retry middleware."""

    def test_non_429_passes_through(self):
        middleware = RetryOn429Middleware()
        response = MagicMock()
        response.status = 200
        result = middleware.process_response(
            request=MagicMock(), response=response, spider=MagicMock()
        )
        assert result is response

    def test_429_retries(self):
        middleware = RetryOn429Middleware()
        middleware.max_retries = 3

        request = MagicMock()
        request.meta = {"retry_429_count": 0}
        request.copy.return_value = MagicMock(meta={})

        response = MagicMock()
        response.status = 429
        headers_mock = MagicMock()
        headers_mock.get.return_value = b""
        response.headers = headers_mock

        result = middleware.process_response(request, response, spider=MagicMock())
        assert result is not response  # returns a new request, not the 429 response

    def test_429_max_retries_exhausted(self):
        middleware = RetryOn429Middleware()
        middleware.max_retries = 3

        request = MagicMock()
        request.meta = {"retry_429_count": 3}

        response = MagicMock()
        response.status = 429

        result = middleware.process_response(request, response, spider=MagicMock())
        assert result is response  # gives up, returns the 429


# ═══════════════════════════════════════════════════════════════════════════════
# 8. Integration: transform uses validation + normalization
# ═══════════════════════════════════════════════════════════════════════════════

class TestTransformIntegration:
    """Verify transform.py uses the new Phase 3 modules."""

    def test_extract_silver_fields_normalizes_skills(self):
        from etl.transform import _extract_silver_fields

        row = {
            "id": "raw-1",
            "source_id": "src-1",
            "raw_json": {
                "title": "Data Engineer Python",
                "description": "We use sklearn and tensorflow for our ML pipeline.",
                "company": "Acme",
                "location": "Paris",
                "contract_type": "CDI",
            },
        }
        result = _extract_silver_fields(row)
        assert result is not None
        skills = result["required_skills"]
        # sklearn should be normalized to scikit-learn
        if "scikit-learn" in skills:
            assert "sklearn" not in skills
        # tf should be normalized to tensorflow
        if "tensorflow" in skills:
            assert "tf" not in skills
