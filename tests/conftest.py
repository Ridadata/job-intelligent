"""Shared test fixtures and configuration."""

import os
from unittest.mock import MagicMock, AsyncMock

import pytest

# Set test environment variables before any imports
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-key")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("SBERT_MODEL", "all-MiniLM-L6-v2")
os.environ.setdefault("SPACY_MODEL", "fr_core_news_md")


@pytest.fixture
def mock_supabase():
    """Create a mock Supabase client with chainable methods.

    Returns:
        MagicMock: A mock Supabase client.
    """
    client = MagicMock()

    # Make table().select().eq().execute() chainable
    table_mock = MagicMock()
    client.table.return_value = table_mock
    table_mock.select.return_value = table_mock
    table_mock.insert.return_value = table_mock
    table_mock.upsert.return_value = table_mock
    table_mock.update.return_value = table_mock
    table_mock.eq.return_value = table_mock
    table_mock.in_.return_value = table_mock
    table_mock.limit.return_value = table_mock

    # Default execute result
    result = MagicMock()
    result.data = []
    table_mock.execute.return_value = result

    # RPC mock
    rpc_mock = MagicMock()
    rpc_mock.execute.return_value = result
    client.rpc.return_value = rpc_mock

    return client


@pytest.fixture
def mock_redis():
    """Create a mock async Redis client.

    Returns:
        AsyncMock: A mock Redis client.
    """
    redis_mock = AsyncMock()
    redis_mock.get.return_value = None
    redis_mock.setex.return_value = True
    redis_mock.delete.return_value = 1
    return redis_mock


@pytest.fixture
def sample_raw_offers() -> list[dict]:
    """Sample raw offer data for testing ingestion.

    Returns:
        List of raw offer dictionaries.
    """
    return [
        {
            "external_id": "test_001",
            "title": "Data Scientist Senior",
            "company": "TechCorp",
            "location": "Paris",
            "description": "We are looking for a senior data scientist with Python, TensorFlow, and SQL skills.",
            "contract_type": "CDI",
            "salary": "55000 - 75000",
            "published_at": "2025-06-01T10:00:00Z",
        },
        {
            "external_id": "test_002",
            "title": "Data Engineer Junior",
            "company": "DataFlow",
            "location": "Lyon",
            "description": "Entry-level data engineer position. Skills needed: Python, SQL, Airflow, Docker.",
            "contract_type": "CDD",
            "salary_min": 35000,
            "salary_max": 42000,
            "published_at": "2025-06-02T09:00:00Z",
        },
        {
            "external_id": "test_003",
            "title": "ML Engineer",
            "company": "AIStartup",
            "location": "Remote",
            "description": "Machine learning engineer with PyTorch, Kubernetes experience. MLOps pipeline development.",
            "contract_type": "Freelance",
        },
    ]


@pytest.fixture
def sample_raw_db_rows() -> list[dict]:
    """Sample raw_job_offers rows as returned from DB.

    Returns:
        List of raw DB row dictionaries.
    """
    return [
        {
            "id": "raw-uuid-001",
            "source_id": "source-uuid-001",
            "raw_json": {
                "title": "Data Scientist Senior",
                "company": "TechCorp",
                "location": "Paris",
                "description": "Senior data scientist role requiring Python, TensorFlow, SQL, machine learning expertise.",
                "contract_type": "CDI",
                "salary": "55000 - 75000",
                "published_at": "2025-06-01T10:00:00Z",
            },
        },
        {
            "id": "raw-uuid-002",
            "source_id": "source-uuid-001",
            "raw_json": {
                "title": "Data Analyst",
                "company": "BigCo",
                "location": "Marseille",
                "description": "Analyst role: SQL, Power BI, Excel, statistics. Entry level welcome.",
                "contract_type": "Stage",
                "salary_min": 25000,
                "salary_max": 30000,
            },
        },
    ]
