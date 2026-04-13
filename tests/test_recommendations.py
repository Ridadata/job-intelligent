"""Tests for the FastAPI recommendation endpoint."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create a test client with mocked dependencies.

    Returns:
        TestClient: A FastAPI test client.
    """
    from api.main import app
    from api.dependencies import get_db, get_current_user

    async def mock_current_user():
        return {"id": "user-uuid", "email": "test@example.com"}

    app.dependency_overrides[get_current_user] = mock_current_user
    app.dependency_overrides[get_db] = lambda: MagicMock()

    yield TestClient(app)

    app.dependency_overrides.clear()


class TestHealthCheck:
    """Tests for the health check endpoint."""

    def test_health(self, client: TestClient) -> None:
        """Should return healthy status."""
        response = client.get("/health")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "healthy"


class TestRecommendationsEndpoint:
    """Tests for POST /api/v1/recommendations."""

    @patch("api.routers.recommendations.get_recommendations")
    def test_successful_recommendation(
        self, mock_get_recs: AsyncMock, client: TestClient
    ) -> None:
        """Should return recommendations in API envelope format."""
        from api.models.schemas import (
            JobOfferMatch,
            RecommendationMeta,
            RecommendationResponse,
        )

        mock_get_recs.return_value = RecommendationResponse(
            data=[
                JobOfferMatch(
                    offer_id="00000000-0000-0000-0000-000000000001",
                    title="Data Scientist",
                    company="TestCo",
                    similarity_score=0.85,
                    matched_skills=["python", "sql"],
                    tech_stack=["python", "sql", "tensorflow"],
                )
            ],
            total=1,
            latency_ms=42,
            meta=RecommendationMeta(
                model="all-MiniLM-L6-v2",
                threshold=0.70,
                cached=False,
            ),
        )

        response = client.post(
            "/api/v1/recommendations",
            json={
                "candidate_id": "00000000-0000-0000-0000-000000000002",
                "top_n": 10,
                "min_score": 0.70,
            },
        )

        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 1
        assert len(body["data"]) == 1

    def test_invalid_candidate_id(self, client: TestClient) -> None:
        """Should reject request with invalid UUID."""
        response = client.post(
            "/api/v1/recommendations",
            json={"candidate_id": "not-a-uuid"},
        )
        assert response.status_code == 422

    def test_min_score_out_of_range(self, client: TestClient) -> None:
        """Should reject min_score > 1.0."""
        response = client.post(
            "/api/v1/recommendations",
            json={
                "candidate_id": "00000000-0000-0000-0000-000000000001",
                "min_score": 1.5,
            },
        )
        assert response.status_code == 422

    def test_top_n_too_large(self, client: TestClient) -> None:
        """Should reject top_n > 100."""
        response = client.post(
            "/api/v1/recommendations",
            json={
                "candidate_id": "00000000-0000-0000-0000-000000000001",
                "top_n": 500,
            },
        )
        assert response.status_code == 422

    @patch("api.routers.recommendations.get_recommendations")
    def test_candidate_not_found(
        self, mock_get_recs: AsyncMock, client: TestClient
    ) -> None:
        """Should return 404 when candidate does not exist."""
        mock_get_recs.side_effect = ValueError("Candidate not found")

        response = client.post(
            "/api/v1/recommendations",
            json={
                "candidate_id": "00000000-0000-0000-0000-000000000099",
            },
        )
        assert response.status_code == 404
