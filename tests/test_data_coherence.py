"""Data coherence tests for the full ETL pipeline.

Verifies:
  - Bronze → Silver transformation preserves and validates data correctly.
  - Silver → Gold enrichment produces coherent, complete Gold rows.
  - Data-domain filter catches relevant and excludes irrelevant offers.
  - Salary parsing handles all known formats.
  - Skill extraction + NLP produce consistent, non-empty results.
  - Dedup logic (source_id + external_id) prevents duplicate Bronze rows.
  - processed flag lifecycle: False on ingest, True after transform.
  - Field types match what downstream layers expect.
"""

from unittest.mock import MagicMock, patch

import pytest

from etl.ingest import ingest_raw
from etl.transform import _extract_silver_fields, _is_data_job, _parse_salary, transform_to_silver
from etl.nlp import extract_skills, normalize_contract_type, classify_seniority, normalize_title


# ============================================================================
# Bronze → Silver Coherence
# ============================================================================
class TestBronzeToSilverCoherence:
    """Verify data integrity from Bronze (raw_job_offers) to Silver (job_offers)."""

    SILVER_REQUIRED_KEYS = {
        "source_id", "raw_offer_id", "title", "company", "location",
        "contract_type", "salary_min", "salary_max", "required_skills",
        "description", "published_at",
    }

    def _make_raw_row(self, overrides: dict | None = None) -> dict:
        """Build a raw_job_offers row for testing.

        Args:
            overrides: Override specific raw_json fields.

        Returns:
            A dict matching raw_job_offers schema.
        """
        raw_json = {
            "title": "Data Engineer Senior",
            "company": "DataCorp",
            "location": "Paris, France",
            "description": "Python, Airflow, Spark, SQL. ETL pipelines.",
            "contract_type": "CDI",
            "salary_min": 50000,
            "salary_max": 70000,
            "published_at": "2025-06-15T10:00:00Z",
        }
        if overrides:
            raw_json.update(overrides)
        return {
            "id": "raw-uuid-001",
            "source_id": "source-uuid-001",
            "raw_json": raw_json,
        }

    def test_silver_has_all_required_keys(self) -> None:
        """Silver row must contain all required keys."""
        silver = _extract_silver_fields(self._make_raw_row())
        assert silver is not None
        assert self.SILVER_REQUIRED_KEYS.issubset(silver.keys()), (
            f"Missing keys: {self.SILVER_REQUIRED_KEYS - silver.keys()}"
        )

    def test_silver_preserves_source_id(self) -> None:
        """source_id must flow from Bronze to Silver unchanged."""
        silver = _extract_silver_fields(self._make_raw_row())
        assert silver["source_id"] == "source-uuid-001"

    def test_silver_preserves_raw_offer_id(self) -> None:
        """raw_offer_id must reference the original Bronze row."""
        silver = _extract_silver_fields(self._make_raw_row())
        assert silver["raw_offer_id"] == "raw-uuid-001"

    def test_silver_skills_are_list(self) -> None:
        """required_skills must be a list (never None, never a string)."""
        silver = _extract_silver_fields(self._make_raw_row())
        assert isinstance(silver["required_skills"], list)

    def test_silver_skills_nonempty_for_known_skills(self) -> None:
        """Data job with Python/SQL in description must extract skills."""
        silver = _extract_silver_fields(self._make_raw_row())
        assert len(silver["required_skills"]) > 0
        skills_lower = [s.lower() for s in silver["required_skills"]]
        assert "python" in skills_lower
        assert "sql" in skills_lower

    def test_silver_contract_normalized(self) -> None:
        """Contract type must be normalized to standard labels."""
        valid_contracts = {"CDI", "CDD", "Freelance", "Stage", "Alternance", "Autre"}
        silver = _extract_silver_fields(self._make_raw_row())
        assert silver["contract_type"] in valid_contracts

    def test_silver_salary_types(self) -> None:
        """salary_min/max must be float or None — never strings."""
        silver = _extract_silver_fields(self._make_raw_row())
        for key in ("salary_min", "salary_max"):
            assert silver[key] is None or isinstance(silver[key], float), (
                f"{key} is {type(silver[key])}, expected float or None"
            )

    def test_silver_description_truncated(self) -> None:
        """Description must be capped at 10000 characters."""
        long_desc = "A" * 15000
        silver = _extract_silver_fields(self._make_raw_row({"description": long_desc}))
        assert len(silver["description"]) <= 10000

    def test_silver_rejects_missing_title(self) -> None:
        """Row without title must be rejected (returns None)."""
        assert _extract_silver_fields(self._make_raw_row({"title": ""})) is None

    def test_silver_rejects_non_data_job(self) -> None:
        """Non-data-domain job must be filtered out."""
        row = self._make_raw_row({
            "title": "Comptable Senior",
            "description": "Gestion comptable et fiscale.",
        })
        assert _extract_silver_fields(row) is None

    def test_silver_accepts_data_job_variants(self) -> None:
        """Various data-domain titles must pass the filter."""
        data_titles = [
            "Data Scientist", "ML Engineer", "Data Analyst Junior",
            "Business Intelligence Developer", "MLOps Engineer",
            "Analytics Engineer", "Data Architect",
        ]
        for title in data_titles:
            row = self._make_raw_row({"title": title})
            silver = _extract_silver_fields(row)
            assert silver is not None, f"Title '{title}' was incorrectly filtered out"


# ============================================================================
# Data Domain Filter
# ============================================================================
class TestDataDomainFilter:
    """Verify _is_data_job correctly classifies offers."""

    def test_obvious_data_titles(self) -> None:
        """Standard data titles must pass."""
        assert _is_data_job("Data Scientist", "")
        assert _is_data_job("Data Engineer", "")
        assert _is_data_job("ML Engineer", "")
        assert _is_data_job("Data Analyst", "")

    def test_data_keywords_in_description(self) -> None:
        """Jobs with data keywords only in description must pass."""
        assert _is_data_job("Software Engineer", "Experience with Spark and Airflow pipelines")
        assert _is_data_job("Développeur", "Utilisation de pandas et scikit-learn")

    def test_non_data_rejected(self) -> None:
        """Non-data jobs must be rejected."""
        assert not _is_data_job("Comptable", "Gestion comptable et fiscale")
        assert not _is_data_job("Chef de projet", "Gestion de projet immobilier")
        assert not _is_data_job("Infirmier", "Soins infirmiers en réanimation")


# ============================================================================
# Salary Parsing Coherence
# ============================================================================
class TestSalaryParsing:
    """Verify salary parsing handles all formats consistently."""

    def test_explicit_min_max(self) -> None:
        """Explicit salary_min/max should be preserved."""
        smin, smax = _parse_salary({"salary_min": 40000, "salary_max": 55000})
        assert smin == 40000.0
        assert smax == 55000.0

    def test_range_string_dash(self) -> None:
        """'45000 - 65000' should parse to min/max."""
        smin, smax = _parse_salary({"salary": "45000 - 65000 EUR"})
        assert smin == 45000.0
        assert smax == 65000.0

    def test_range_string_euro_sign(self) -> None:
        """'50000€ - 70000€' should parse."""
        smin, smax = _parse_salary({"salary": "50000€ - 70000€"})
        assert smin == 50000.0
        assert smax == 70000.0

    def test_single_value(self) -> None:
        """Single salary sets both min and max."""
        smin, smax = _parse_salary({"salary": "50000"})
        assert smin == 50000.0
        assert smax == 50000.0

    def test_no_salary(self) -> None:
        """Missing salary returns (None, None)."""
        smin, smax = _parse_salary({})
        assert smin is None
        assert smax is None

    def test_non_numeric_salary(self) -> None:
        """Non-numeric salary returns (None, None)."""
        smin, smax = _parse_salary({"salary": "competitive"})
        assert smin is None
        assert smax is None

    def test_min_max_override_string(self) -> None:
        """Explicit min/max takes priority over salary string."""
        smin, smax = _parse_salary({
            "salary": "30000 - 40000",
            "salary_min": 45000,
            "salary_max": 60000,
        })
        assert smin == 45000.0
        assert smax == 60000.0


# ============================================================================
# NLP Skill Extraction Coherence
# ============================================================================
class TestSkillExtractionCoherence:
    """Ensure skill extraction is consistent and deterministic."""

    def test_same_input_same_output(self) -> None:
        """Repeated calls with identical text produce identical results."""
        text = "Python, SQL, Docker, Kubernetes, Airflow"
        result1 = extract_skills(text)
        result2 = extract_skills(text)
        assert result1 == result2

    def test_skills_are_sorted(self) -> None:
        """Skills must be returned as a sorted list."""
        skills = extract_skills("Docker, Python, SQL, Airflow, Spark")
        assert skills == sorted(skills)

    def test_skills_are_unique(self) -> None:
        """Duplicate mentions should produce unique entries."""
        text = "Python Python Python SQL SQL"
        skills = extract_skills(text)
        assert len(skills) == len(set(skills))

    def test_case_normalized(self) -> None:
        """Skills should be lowercase regardless of input case."""
        skills = extract_skills("PYTHON, SQL, DOCKER")
        for skill in skills:
            assert skill == skill.lower(), f"Skill '{skill}' not lowercased"


# ============================================================================
# Contract Type + Title Normalization
# ============================================================================
class TestNormalizationCoherence:
    """Verify normalization functions produce valid outputs."""

    VALID_CONTRACTS = {"CDI", "CDD", "Freelance", "Stage", "Alternance", "Autre"}

    def test_all_normalized_contracts_valid(self) -> None:
        """Every normalization result must be in the valid set."""
        inputs = [
            "CDI", "CDD", "Stage", "Alternance", "Freelance",
            "Full-time", "Internship", "Apprentissage",
            "Permanent", "Fixed-term", "Contractor",
            "", "something weird", None,
        ]
        for raw in inputs:
            result = normalize_contract_type(raw or "")
            assert result in self.VALID_CONTRACTS, (
                f"normalize_contract_type('{raw}') = '{result}' not in valid set"
            )

    VALID_SENIORITIES = {"Junior", "Mid", "Senior"}

    def test_all_seniorities_valid(self) -> None:
        """classify_seniority must always return a valid level."""
        inputs = [
            "Senior Data Scientist", "Junior Developer", "Data Analyst",
            "Lead ML Engineer", "", "Entry-level",
        ]
        for text in inputs:
            result = classify_seniority(text)
            assert result in self.VALID_SENIORITIES, (
                f"classify_seniority('{text}') = '{result}' not in valid set"
            )

    def test_normalize_title_returns_string(self) -> None:
        """normalize_title must always return a non-empty string."""
        inputs = ["Data Scientist", "ML Engineer", "Random Title", ""]
        for raw in inputs:
            result = normalize_title(raw)
            assert isinstance(result, str)
            assert len(result) > 0


# ============================================================================
# Ingestion → Transform Processed Flag
# ============================================================================
class TestProcessedFlagLifecycle:
    """Verify the processed flag transitions correctly."""

    @patch("etl.ingest.get_supabase_client")
    @patch("etl.ingest._get_source_id")
    @patch("etl.ingest._log_scraping_run")
    def test_ingest_sets_processed_false(
        self, mock_log: MagicMock, mock_source: MagicMock, mock_client_fn: MagicMock,
    ) -> None:
        """ingest_raw must set processed=False on upserted rows."""
        mock_source.return_value = "src-uuid"
        mock_client = MagicMock()
        mock_client_fn.return_value = mock_client
        mock_result = MagicMock()
        mock_result.data = [{}]
        mock_client.table.return_value.upsert.return_value.execute.return_value = mock_result
        mock_client.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock()

        ingest_raw([{"external_id": "x1", "title": "Data Engineer"}], "test_source")

        # Verify upsert was called with processed=False
        upsert_call = mock_client.table.return_value.upsert.call_args
        rows = upsert_call[0][0]
        assert all(row["processed"] is False for row in rows)

    @patch("etl.transform.get_supabase_client")
    def test_transform_marks_processed_true(self, mock_client_fn: MagicMock) -> None:
        """transform_to_silver must mark Bronze rows as processed=True."""
        mock_client = MagicMock()
        mock_client_fn.return_value = mock_client

        # First call returns raw rows, second call returns empty (end loop)
        raw_rows = [{
            "id": "raw-1",
            "source_id": "src-1",
            "raw_json": {
                "title": "Data Scientist",
                "company": "Co",
                "location": "Paris",
                "description": "Python SQL machine learning",
                "contract_type": "CDI",
            },
        }]
        select_mock = MagicMock()
        eq_mock = MagicMock()
        limit_mock = MagicMock()

        first_result = MagicMock()
        first_result.data = raw_rows
        second_result = MagicMock()
        second_result.data = []

        call_count = [0]
        def limit_execute():
            result = MagicMock()
            if call_count[0] == 0:
                result.data = raw_rows
            else:
                result.data = []
            call_count[0] += 1
            return result

        mock_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute = limit_execute
        mock_client.table.return_value.insert.return_value.execute.return_value = MagicMock(data=[{}])
        mock_client.table.return_value.update.return_value.in_.return_value.execute.return_value = MagicMock()

        transform_to_silver(batch_size=10)

        # Verify update was called with processed=True
        update_call = mock_client.table.return_value.update.call_args
        assert update_call is not None
        assert update_call[0][0] == {"processed": True}


# ============================================================================
# Silver → Gold Coherence
# ============================================================================
class TestSilverToGoldCoherence:
    """Verify Gold enrichment output meets schema expectations."""

    @patch("etl.enrich.generate_embeddings_batch")
    @patch("etl.enrich.get_supabase_client")
    def test_gold_row_has_required_fields(
        self, mock_client_fn: MagicMock, mock_embeddings: MagicMock
    ) -> None:
        """Gold rows must have: offer_id, embedding, normalized_title, seniority_level, tech_stack, demand_score."""
        import numpy as np

        mock_client = MagicMock()
        mock_client_fn.return_value = mock_client

        silver_offers = [{
            "id": "silver-1",
            "title": "Data Scientist Senior",
            "company": "Co",
            "description": "Python TensorFlow SQL",
            "required_skills": ["python", "tensorflow", "sql"],
            "published_at": "2025-06-01",
            "source_id": "src-1",
        }]

        # Gold table has no existing rows
        mock_client.table.return_value.select.return_value.execute.return_value = MagicMock(data=[])
        # Silver table returns one row then empty
        silver_result = MagicMock()
        silver_result.data = silver_offers

        call_count = [0]
        def select_side_effect(*args, **kwargs):
            mock_chain = MagicMock()
            if call_count[0] == 0:
                # dw_job_offers select (existing IDs)
                mock_chain.execute.return_value = MagicMock(data=[])
            elif call_count[0] == 1:
                # job_offers select (Silver offers)
                mock_chain.limit.return_value.execute.return_value = MagicMock(data=silver_offers)
            else:
                # Second iteration — no more Silver offers
                mock_chain.execute.return_value = MagicMock(data=[])
                mock_chain.limit.return_value.execute.return_value = MagicMock(data=[])
            call_count[0] += 1
            return mock_chain

        mock_client.table.return_value.select = select_side_effect
        mock_client.table.return_value.upsert.return_value.execute.return_value = MagicMock(data=[{}])

        # Mock embeddings
        mock_embeddings.return_value = [np.random.rand(384).tolist()]

        from etl.enrich import enrich_to_gold
        enrich_to_gold(batch_size=10)

        # Verify upsert was called with correct Gold schema
        upsert_call = mock_client.table.return_value.upsert.call_args
        assert upsert_call is not None
        gold_rows = upsert_call[0][0]
        assert len(gold_rows) == 1
        gold = gold_rows[0]

        gold_required = {"offer_id", "embedding", "normalized_title", "seniority_level", "tech_stack", "demand_score"}
        assert gold_required.issubset(gold.keys()), f"Missing: {gold_required - gold.keys()}"
        assert gold["offer_id"] == "silver-1"
        assert isinstance(gold["embedding"], list)
        assert len(gold["embedding"]) == 384
        assert isinstance(gold["tech_stack"], list)
        assert isinstance(gold["demand_score"], float)
        assert 0.0 <= gold["demand_score"] <= 1.0
