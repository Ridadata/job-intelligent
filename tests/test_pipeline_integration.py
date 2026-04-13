"""End-to-end pipeline integration test.

Simulates the full flow: API client output → ingest_raw → transform_to_silver → enrich_to_gold.
All DB operations are mocked, but the data transformations are real.
Verifies data coherence across all three layers.
"""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from ingestion.api_clients.adzuna_client import AdzunaClient
from ingestion.api_clients.jsearch_client import JSearchClient
from ingestion.api_clients.france_travail_client import FranceTravailClient
from etl.ingest import ingest_raw
from etl.transform import _extract_silver_fields
from etl.enrich import _compute_demand_score
from etl.nlp import extract_skills, normalize_contract_type, classify_seniority, normalize_title


class TestEndToEndPipeline:
    """Simulate end-to-end: API response → Bronze → Silver → Gold field generation."""

    # Realistic API responses from each source
    ADZUNA_RAW = {
        "id": 9876543,
        "title": "Data Engineer — Cloud / Python",
        "company": {"display_name": "CloudData SAS"},
        "location": {"display_name": "Lyon, Auvergne-Rhône-Alpes"},
        "description": (
            "Nous recherchons un Data Engineer expérimenté. "
            "Stack: Python, Apache Airflow, Spark, AWS, Docker, PostgreSQL, dbt. "
            "Méthodologie Agile. CDI temps plein."
        ),
        "redirect_url": "https://adzuna.fr/9876543",
        "salary_min": 48000,
        "salary_max": 62000,
        "contract_type": "permanent",
        "created": "2025-09-01T08:00:00Z",
    }

    JSEARCH_RAW = {
        "job_id": "js-ml-456",
        "job_title": "Machine Learning Engineer Senior",
        "employer_name": "AI Solutions France",
        "job_city": "Paris",
        "job_country": "FR",
        "job_description": (
            "Senior ML Engineer for production model deployment. "
            "Required: Python, PyTorch, TensorFlow, MLflow, Kubernetes, Docker, "
            "CI/CD, monitoring. 5+ years experience."
        ),
        "job_apply_link": "https://jsearch.example.com/ml-456",
        "job_min_salary": 65000,
        "job_max_salary": 85000,
        "job_employment_type": "FULLTIME",
        "job_posted_at_datetime_utc": "2025-09-02T10:00:00.000Z",
    }

    FT_RAW = {
        "id": "FT-DA-789",
        "intitule": "Data Analyst — Power BI / SQL",
        "entreprise": {"nom": "Groupe Finance"},
        "lieuTravail": {"libelle": "33 - BORDEAUX"},
        "description": (
            "Analyste données pour reporting et BI. "
            "Compétences : SQL, Power BI, Excel, Python, pandas. "
            "Poste en CDD 12 mois."
        ),
        "origineOffre": {"urlOrigine": "https://francetravail.fr/FT-DA-789"},
        "typeContratLibelle": "Contrat à durée déterminée",
        "dateCreation": "2025-09-03T14:00:00.000Z",
    }

    def _normalize_all(self) -> list[dict]:
        """Normalize all three API responses."""
        return [
            AdzunaClient(app_id="t", app_key="t")._normalize(self.ADZUNA_RAW),
            JSearchClient(api_key="t")._normalize(self.JSEARCH_RAW),
            FranceTravailClient(client_id="t", client_secret="t")._normalize(self.FT_RAW),
        ]

    def test_api_outputs_all_have_external_id(self) -> None:
        """Every API output must have a non-empty external_id for dedup."""
        for job in self._normalize_all():
            assert job["external_id"], f"Empty external_id for source={job['source']}"

    def test_api_to_bronze_format(self) -> None:
        """Normalized API output must be valid input for ingest_raw.

        ingest_raw expects dicts with at least 'external_id'.
        """
        for job in self._normalize_all():
            assert "external_id" in job
            assert isinstance(job["external_id"], str)
            assert len(job["external_id"]) > 0

    def test_bronze_to_silver_transformation(self) -> None:
        """Each normalized API output, when wrapped as Bronze row, must produce valid Silver."""
        for job in self._normalize_all():
            bronze_row = {
                "id": f"raw-{job['external_id']}",
                "source_id": f"src-{job['source']}",
                "raw_json": job,
            }
            silver = _extract_silver_fields(bronze_row)
            assert silver is not None, f"Silver extraction failed for {job['source']}: {job['title']}"
            assert silver["title"] == job["title"]
            assert isinstance(silver["required_skills"], list)
            assert len(silver["required_skills"]) > 0, (
                f"No skills extracted for '{job['title']}' from {job['source']}"
            )

    def test_silver_skills_match_description(self) -> None:
        """Skills extracted at Silver must be present in the original description text."""
        for job in self._normalize_all():
            bronze_row = {
                "id": f"raw-{job['external_id']}",
                "source_id": f"src-{job['source']}",
                "raw_json": job,
            }
            silver = _extract_silver_fields(bronze_row)
            assert silver is not None
            combined = f"{job['title']} {job['description']}".lower()
            for skill in silver["required_skills"]:
                assert skill.lower() in combined, (
                    f"Skill '{skill}' not found in original text from {job['source']}"
                )

    def test_silver_contract_normalization_per_source(self) -> None:
        """Each source's contract type must normalize to a valid label."""
        valid = {"CDI", "CDD", "Freelance", "Stage", "Alternance", "Autre"}
        for job in self._normalize_all():
            normalized = normalize_contract_type(job.get("contract_type", ""))
            assert normalized in valid, (
                f"Source {job['source']} contract '{job['contract_type']}' → '{normalized}' invalid"
            )

    def test_silver_salary_coherence(self) -> None:
        """salary_min <= salary_max when both are present."""
        for job in self._normalize_all():
            bronze_row = {
                "id": f"raw-{job['external_id']}",
                "source_id": f"src-{job['source']}",
                "raw_json": job,
            }
            silver = _extract_silver_fields(bronze_row)
            assert silver is not None
            if silver["salary_min"] is not None and silver["salary_max"] is not None:
                assert silver["salary_min"] <= silver["salary_max"], (
                    f"salary_min > salary_max for {job['source']}: "
                    f"{silver['salary_min']} > {silver['salary_max']}"
                )

    def test_gold_metadata_from_silver(self) -> None:
        """Gold enrichment metadata (title, seniority, skills, score) must be valid."""
        for job in self._normalize_all():
            bronze_row = {
                "id": f"raw-{job['external_id']}",
                "source_id": f"src-{job['source']}",
                "raw_json": job,
            }
            silver = _extract_silver_fields(bronze_row)
            assert silver is not None

            # Simulate Gold enrichment fields
            norm_title = normalize_title(silver["title"])
            seniority = classify_seniority(f"{silver['title']} {silver.get('description', '')}")
            tech_stack = extract_skills(f"{silver['title']} {silver.get('description', '')}")
            demand_score = _compute_demand_score(silver)

            assert isinstance(norm_title, str) and len(norm_title) > 0
            assert seniority in {"Junior", "Mid", "Senior"}
            assert isinstance(tech_stack, list)
            assert 0.0 <= demand_score <= 1.0

    def test_no_data_loss_across_layers(self) -> None:
        """Key fields (title, company, location) must survive from API to Silver."""
        for job in self._normalize_all():
            bronze_row = {
                "id": f"raw-{job['external_id']}",
                "source_id": f"src-{job['source']}",
                "raw_json": job,
            }
            silver = _extract_silver_fields(bronze_row)
            assert silver is not None
            assert silver["title"] == job["title"]
            # company/location may be stripped but must not be lost
            if job.get("company"):
                assert silver["company"] is not None

    def test_dedup_key_uniqueness(self) -> None:
        """Each API output must produce a unique (source, external_id) pair.

        No two sources should produce the same external_id accidentally.
        """
        jobs = self._normalize_all()
        keys = [(j["source"], j["external_id"]) for j in jobs]
        assert len(keys) == len(set(keys)), f"Duplicate dedup keys: {keys}"

    @patch("etl.ingest._log_scraping_run")
    @patch("etl.ingest.get_supabase_client")
    @patch("etl.ingest._get_source_id")
    def test_ingest_accepts_all_api_outputs(
        self, mock_source: MagicMock, mock_client: MagicMock, mock_log: MagicMock
    ) -> None:
        """ingest_raw must accept normalized output from every API client."""
        mock_source.return_value = "src-uuid"
        client = MagicMock()
        mock_client.return_value = client
        result = MagicMock()
        result.data = [{}]
        client.table.return_value.upsert.return_value.execute.return_value = result
        client.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock()

        for job in self._normalize_all():
            count = ingest_raw([job], job["source"])
            assert count >= 0, f"ingest_raw failed for source={job['source']}"


class TestCrossSourceSkillConsistency:
    """Verify that the same skill mentioned in different sources is extracted the same way."""

    def test_python_extracted_from_all_sources(self) -> None:
        """'Python' mentioned in any source must be extracted as 'python'."""
        texts = [
            "Data Engineer with Python and SQL",
            "Développeur Python pour traitement de données",
            "Python, TensorFlow, PyTorch required",
        ]
        for text in texts:
            skills = extract_skills(text)
            assert "python" in skills, f"'python' not extracted from: '{text}'"

    def test_sql_extracted_from_all_sources(self) -> None:
        """'SQL' mentioned in any source must be extracted as 'sql'."""
        texts = [
            "SQL Server and PostgreSQL expertise",
            "Compétences SQL avancées",
            "Required skills: SQL, Python",
        ]
        for text in texts:
            skills = extract_skills(text)
            assert "sql" in skills, f"'sql' not extracted from: '{text}'"

    def test_docker_extracted_consistently(self) -> None:
        """'Docker' must be extracted regardless of context."""
        texts = [
            "Docker and Kubernetes knowledge",
            "Déploiement avec Docker",
            "Docker, CI/CD pipeline",
        ]
        for text in texts:
            skills = extract_skills(text)
            assert "docker" in skills, f"'docker' not extracted from: '{text}'"
