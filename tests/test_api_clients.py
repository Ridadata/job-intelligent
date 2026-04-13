"""Tests for ingestion API clients — Adzuna, JSearch, France Travail.

Verifies:
  - Normalization to JobItem schema (all required keys present).
  - Correct field mapping from each API's raw response.
  - Error handling for missing/malformed fields.
  - fetch_jobs HTTP interaction (mocked).
"""

from unittest.mock import MagicMock, patch

import pytest

from ingestion.api_clients.adzuna_client import AdzunaClient
from ingestion.api_clients.jsearch_client import JSearchClient
from ingestion.api_clients.france_travail_client import FranceTravailClient

# ── Required keys every normalized job must have ──────────────────────────────
REQUIRED_KEYS = {
    "external_id", "title", "company", "location", "description",
    "url", "salary_min", "salary_max", "contract_type", "published_at", "source",
}


# ============================================================================
# Adzuna Tests
# ============================================================================
class TestAdzunaClient:
    """Tests for the Adzuna API client."""

    def _raw_adzuna_result(self) -> dict:
        """A realistic Adzuna API result object."""
        return {
            "id": 4123456789,
            "title": "Data Engineer — Python / Spark",
            "company": {"display_name": "TechCorp"},
            "location": {"display_name": "Paris, Île-de-France"},
            "description": "Build and maintain ETL pipelines using Python, Spark, Airflow.",
            "redirect_url": "https://www.adzuna.fr/land/ad/4123456789",
            "salary_min": 45000,
            "salary_max": 65000,
            "contract_type": "permanent",
            "created": "2025-06-15T08:30:00Z",
        }

    def test_normalize_all_keys_present(self) -> None:
        """Normalized output must contain all required JobItem keys."""
        client = AdzunaClient(app_id="test", app_key="test")
        result = client._normalize(self._raw_adzuna_result())
        assert REQUIRED_KEYS.issubset(result.keys()), f"Missing keys: {REQUIRED_KEYS - result.keys()}"

    def test_normalize_field_mapping(self) -> None:
        """Fields must map correctly from Adzuna schema."""
        client = AdzunaClient(app_id="test", app_key="test")
        result = client._normalize(self._raw_adzuna_result())

        assert result["external_id"] == "4123456789"
        assert result["title"] == "Data Engineer — Python / Spark"
        assert result["company"] == "TechCorp"
        assert result["location"] == "Paris, Île-de-France"
        assert "ETL" in result["description"]
        assert result["salary_min"] == 45000
        assert result["salary_max"] == 65000
        assert result["source"] == "adzuna"

    def test_normalize_missing_fields(self) -> None:
        """Normalization must handle empty/missing fields gracefully."""
        client = AdzunaClient(app_id="test", app_key="test")
        result = client._normalize({})
        assert REQUIRED_KEYS.issubset(result.keys())
        assert result["external_id"] == ""
        assert result["title"] == ""
        assert result["company"] == ""
        assert result["source"] == "adzuna"

    def test_normalize_nested_company_missing(self) -> None:
        """Must handle company as non-dict."""
        client = AdzunaClient(app_id="test", app_key="test")
        raw = self._raw_adzuna_result()
        raw["company"] = "StringCompany"
        # company is expected to be a dict; if it's a string, .get(...) will fail
        # This is a robustness check — should not crash
        try:
            result = client._normalize(raw)
            # If no crash, just ensure key exists
            assert "company" in result
        except AttributeError:
            pytest.fail("_normalize crashed on non-dict company field")

    @patch("ingestion.api_clients.adzuna_client.requests.get")
    def test_fetch_jobs_success(self, mock_get: MagicMock) -> None:
        """fetch_jobs should call API and return normalized results."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"results": [self._raw_adzuna_result()]}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        client = AdzunaClient(app_id="id123", app_key="key456", country="fr")
        jobs = client.fetch_jobs("data engineer", location="Paris")

        assert len(jobs) == 1
        assert jobs[0]["source"] == "adzuna"
        assert jobs[0]["external_id"] == "4123456789"
        mock_get.assert_called_once()
        call_kwargs = mock_get.call_args
        assert "params" in call_kwargs.kwargs or len(call_kwargs.args) > 1

    @patch("ingestion.api_clients.adzuna_client.requests.get")
    def test_fetch_jobs_empty(self, mock_get: MagicMock) -> None:
        """fetch_jobs should return empty list when API returns no results."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"results": []}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        client = AdzunaClient(app_id="id", app_key="key")
        jobs = client.fetch_jobs("nonexistent")
        assert jobs == []

    @patch("ingestion.api_clients.adzuna_client.requests.get")
    def test_fetch_jobs_http_error(self, mock_get: MagicMock) -> None:
        """fetch_jobs should propagate HTTP errors."""
        import requests

        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("403 Forbidden")
        mock_get.return_value = mock_response

        client = AdzunaClient(app_id="id", app_key="key")
        with pytest.raises(requests.HTTPError):
            client.fetch_jobs("data scientist")


# ============================================================================
# JSearch Tests
# ============================================================================
class TestJSearchClient:
    """Tests for the JSearch (RapidAPI) client."""

    def _raw_jsearch_result(self) -> dict:
        """A realistic JSearch API result object."""
        return {
            "job_id": "abc-def-123",
            "job_title": "Senior Data Scientist",
            "employer_name": "AI Corp",
            "job_city": "Paris",
            "job_country": "FR",
            "job_description": "Python, TensorFlow, statistics, A/B testing.",
            "job_apply_link": "https://jsearch.example.com/apply/abc-def-123",
            "job_min_salary": 50000,
            "job_max_salary": 70000,
            "job_employment_type": "FULLTIME",
            "job_posted_at_datetime_utc": "2025-07-01T12:00:00.000Z",
        }

    def test_normalize_all_keys_present(self) -> None:
        """Normalized output must contain all required JobItem keys."""
        client = JSearchClient(api_key="test")
        result = client._normalize(self._raw_jsearch_result())
        assert REQUIRED_KEYS.issubset(result.keys())

    def test_normalize_field_mapping(self) -> None:
        """Fields must map correctly from JSearch schema."""
        client = JSearchClient(api_key="test")
        result = client._normalize(self._raw_jsearch_result())

        assert result["external_id"] == "abc-def-123"
        assert result["title"] == "Senior Data Scientist"
        assert result["company"] == "AI Corp"
        assert "Paris" in result["location"]
        assert result["salary_min"] == 50000
        assert result["salary_max"] == 70000
        assert result["source"] == "jsearch"

    def test_normalize_missing_city(self) -> None:
        """Location should gracefully handle missing city."""
        client = JSearchClient(api_key="test")
        raw = self._raw_jsearch_result()
        raw.pop("job_city")
        result = client._normalize(raw)
        assert "FR" in result["location"]

    def test_normalize_empty_input(self) -> None:
        """Normalization must handle empty dict."""
        client = JSearchClient(api_key="test")
        result = client._normalize({})
        assert REQUIRED_KEYS.issubset(result.keys())
        assert result["source"] == "jsearch"

    @patch("ingestion.api_clients.jsearch_client.requests.get")
    def test_fetch_jobs_success(self, mock_get: MagicMock) -> None:
        """fetch_jobs should call API and return normalized results."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": [self._raw_jsearch_result()]}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        client = JSearchClient(api_key="test-key")
        jobs = client.fetch_jobs("data scientist", location="France")

        assert len(jobs) == 1
        assert jobs[0]["source"] == "jsearch"
        mock_get.assert_called_once()
        headers = mock_get.call_args.kwargs.get("headers", {})
        assert headers.get("X-RapidAPI-Key") == "test-key"

    @patch("ingestion.api_clients.jsearch_client.requests.get")
    def test_fetch_jobs_no_data_key(self, mock_get: MagicMock) -> None:
        """fetch_jobs should handle response without 'data' key."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "OK"}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        client = JSearchClient(api_key="test-key")
        jobs = client.fetch_jobs("data engineer")
        assert jobs == []


# ============================================================================
# France Travail Tests
# ============================================================================
class TestFranceTravailClient:
    """Tests for the France Travail (Pôle Emploi) client."""

    def _raw_ft_result(self) -> dict:
        """A realistic France Travail API result object."""
        return {
            "id": "154XYZW",
            "intitule": "Ingénieur Data / Machine Learning",
            "entreprise": {"nom": "Ministère de l'Économie"},
            "lieuTravail": {"libelle": "75 - PARIS"},
            "description": "Développement de modèles ML, Python, scikit-learn, déploiement.",
            "origineOffre": {"urlOrigine": "https://candidat.francetravail.fr/offres/154XYZW"},
            "typeContratLibelle": "Contrat à durée indéterminée",
            "dateCreation": "2025-08-01T10:00:00.000Z",
        }

    def test_normalize_all_keys_present(self) -> None:
        """Normalized output must contain all required JobItem keys."""
        client = FranceTravailClient(client_id="test", client_secret="test")
        result = client._normalize(self._raw_ft_result())
        assert REQUIRED_KEYS.issubset(result.keys())

    def test_normalize_field_mapping(self) -> None:
        """Fields must map correctly from France Travail schema."""
        client = FranceTravailClient(client_id="test", client_secret="test")
        result = client._normalize(self._raw_ft_result())

        assert result["external_id"] == "154XYZW"
        assert result["title"] == "Ingénieur Data / Machine Learning"
        assert "Ministère" in result["company"]
        assert "PARIS" in result["location"]
        assert result["salary_min"] is None
        assert result["salary_max"] is None
        assert result["source"] == "france_travail"
        assert result["contract_type"] == "Contrat à durée indéterminée"

    def test_normalize_missing_entreprise(self) -> None:
        """Must handle missing entreprise gracefully."""
        client = FranceTravailClient(client_id="t", client_secret="t")
        raw = self._raw_ft_result()
        raw.pop("entreprise")
        result = client._normalize(raw)
        assert result["company"] == ""

    def test_normalize_empty_input(self) -> None:
        """Normalization must handle empty dict."""
        client = FranceTravailClient(client_id="t", client_secret="t")
        result = client._normalize({})
        assert REQUIRED_KEYS.issubset(result.keys())
        assert result["source"] == "france_travail"

    @patch("ingestion.api_clients.france_travail_client.requests.get")
    @patch("ingestion.api_clients.france_travail_client.requests.post")
    def test_fetch_jobs_authenticates_and_fetches(
        self, mock_post: MagicMock, mock_get: MagicMock
    ) -> None:
        """fetch_jobs should authenticate then search."""
        # Mock OAuth
        auth_response = MagicMock()
        auth_response.json.return_value = {"access_token": "tok-123"}
        auth_response.raise_for_status = MagicMock()
        mock_post.return_value = auth_response

        # Mock search
        search_response = MagicMock()
        search_response.json.return_value = {"resultats": [self._raw_ft_result()]}
        search_response.raise_for_status = MagicMock()
        mock_get.return_value = search_response

        client = FranceTravailClient(client_id="cid", client_secret="csec")
        jobs = client.fetch_jobs("data scientist")

        assert len(jobs) == 1
        assert jobs[0]["source"] == "france_travail"
        mock_post.assert_called_once()  # auth
        mock_get.assert_called_once()   # search
        # Verify auth header
        call_kwargs = mock_get.call_args.kwargs
        assert "Bearer tok-123" in call_kwargs.get("headers", {}).get("Authorization", "")

    @patch("ingestion.api_clients.france_travail_client.requests.get")
    @patch("ingestion.api_clients.france_travail_client.requests.post")
    def test_fetch_jobs_empty_results(
        self, mock_post: MagicMock, mock_get: MagicMock
    ) -> None:
        """fetch_jobs should handle empty resultats."""
        auth_response = MagicMock()
        auth_response.json.return_value = {"access_token": "tok"}
        auth_response.raise_for_status = MagicMock()
        mock_post.return_value = auth_response

        search_response = MagicMock()
        search_response.json.return_value = {"resultats": []}
        search_response.raise_for_status = MagicMock()
        mock_get.return_value = search_response

        client = FranceTravailClient(client_id="c", client_secret="s")
        jobs = client.fetch_jobs("nothing")
        assert jobs == []


# ============================================================================
# Cross-Client Schema Coherence
# ============================================================================
class TestCrossClientCoherence:
    """Verify all API clients produce identical schema structure."""

    def test_all_clients_same_keys(self) -> None:
        """Every client must normalize to exactly the same set of keys."""
        adzuna = AdzunaClient(app_id="t", app_key="t")._normalize({
            "id": 1, "title": "T", "company": {"display_name": "C"},
            "location": {"display_name": "L"}, "description": "D",
            "redirect_url": "U", "created": "2025-01-01",
        })
        jsearch = JSearchClient(api_key="t")._normalize({
            "job_id": "1", "job_title": "T", "employer_name": "C",
            "job_description": "D", "job_apply_link": "U",
        })
        ft = FranceTravailClient(client_id="t", client_secret="t")._normalize({
            "id": "1", "intitule": "T", "description": "D",
        })

        assert set(adzuna.keys()) == set(jsearch.keys()) == set(ft.keys()), (
            f"Key mismatch:\n  Adzuna:  {sorted(adzuna.keys())}\n"
            f"  JSearch: {sorted(jsearch.keys())}\n"
            f"  FT:      {sorted(ft.keys())}"
        )

    def test_normalized_to_ingest_compatibility(self) -> None:
        """Normalized outputs must be compatible with ingest_raw().

        ingest_raw() requires 'external_id' key. Every client must produce it.
        """
        clients_outputs = [
            AdzunaClient(app_id="t", app_key="t")._normalize({"id": 99}),
            JSearchClient(api_key="t")._normalize({"job_id": "j99"}),
            FranceTravailClient(client_id="t", client_secret="t")._normalize({"id": "f99"}),
        ]

        for output in clients_outputs:
            assert "external_id" in output, f"Missing external_id in {output}"
            assert output["external_id"], f"Empty external_id in {output}"
            assert "title" in output
            assert "source" in output
