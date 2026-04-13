"""Tests for ETL pipeline: ingestion and transformation."""

from unittest.mock import MagicMock, patch

from etl.ingest import ingest_raw, _get_source_id
from etl.transform import _extract_silver_fields, _parse_salary


class TestGetSourceId:
    """Tests for _get_source_id helper."""

    @patch("etl.ingest.get_supabase_client")
    def test_valid_source(self, mock_get_client: MagicMock) -> None:
        """Should return UUID for a valid source name."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        result = MagicMock()
        result.data = [{"id": "test-uuid-123"}]
        mock_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = result

        source_id = _get_source_id("indeed")
        assert source_id == "test-uuid-123"

    @patch("etl.ingest.get_supabase_client")
    def test_invalid_source(self, mock_get_client: MagicMock) -> None:
        """Should auto-create a new source when it doesn't exist."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Select returns empty (source not found)
        select_result = MagicMock()
        select_result.data = []
        mock_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = select_result

        # Upsert auto-creates and returns the new source
        upsert_result = MagicMock()
        upsert_result.data = [{"id": "new-source-uuid"}]
        mock_client.table.return_value.upsert.return_value.execute.return_value = upsert_result

        source_id = _get_source_id("nonexistent")
        assert source_id == "new-source-uuid"


class TestIngestRaw:
    """Tests for ingest_raw function."""

    @patch("etl.ingest._log_scraping_run")
    @patch("etl.ingest.get_supabase_client")
    @patch("etl.ingest._get_source_id")
    def test_ingest_valid_offers(
        self,
        mock_source_id: MagicMock,
        mock_get_client: MagicMock,
        mock_log: MagicMock,
        sample_raw_offers: list[dict],
    ) -> None:
        """Should ingest valid offers and return count."""
        mock_source_id.return_value = "source-uuid"
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        result = MagicMock()
        result.data = [{}] * 3
        mock_client.table.return_value.upsert.return_value.execute.return_value = result
        mock_client.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock()

        count = ingest_raw(sample_raw_offers, "indeed")
        assert count == 3

    def test_ingest_empty_list(self) -> None:
        """Should return 0 for empty offer list."""
        count = ingest_raw([], "indeed")
        assert count == 0


class TestExtractSilverFields:
    """Tests for _extract_silver_fields function."""

    def test_valid_raw_offer(self, sample_raw_db_rows: list[dict]) -> None:
        """Should extract structured fields from raw offer."""
        row = sample_raw_db_rows[0]
        silver = _extract_silver_fields(row)
        assert silver is not None
        assert silver["title"] == "Data Scientist Senior"
        assert silver["company"] == "TechCorp"
        assert silver["location"] == "Paris"
        assert silver["contract_type"] == "CDI"
        assert silver["source_id"] == "source-uuid-001"
        assert isinstance(silver["required_skills"], list)

    def test_missing_title(self) -> None:
        """Should return None for offer without title."""
        row = {
            "id": "raw-uuid",
            "source_id": "source-uuid",
            "raw_json": {"company": "SomeCo"},
        }
        assert _extract_silver_fields(row) is None

    def test_empty_raw_json(self) -> None:
        """Should return None for empty raw_json."""
        row = {"id": "raw-uuid", "source_id": "source-uuid", "raw_json": {}}
        assert _extract_silver_fields(row) is None


class TestParseSalary:
    """Tests for _parse_salary function."""

    def test_explicit_min_max(self) -> None:
        """Should parse explicit salary_min and salary_max."""
        raw = {"salary_min": 40000, "salary_max": 55000}
        smin, smax = _parse_salary(raw)
        assert smin == 40000.0
        assert smax == 55000.0

    def test_salary_range_string(self) -> None:
        """Should parse salary range from string."""
        raw = {"salary": "45000 - 65000 EUR"}
        smin, smax = _parse_salary(raw)
        assert smin == 45000.0
        assert smax == 65000.0

    def test_single_salary_value(self) -> None:
        """Should handle single salary value."""
        raw = {"salary": "50000"}
        smin, smax = _parse_salary(raw)
        assert smin == 50000.0
        assert smax == 50000.0

    def test_no_salary(self) -> None:
        """Should return None for no salary info."""
        raw = {}
        smin, smax = _parse_salary(raw)
        assert smin is None
        assert smax is None
