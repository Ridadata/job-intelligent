"""Adzuna API client — international job coverage, free tier.

Docs: https://developer.adzuna.com/
API keys via ADZUNA_APP_ID and ADZUNA_APP_KEY env vars.
"""

import logging
import os
import time
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

ADZUNA_BASE_URL = "https://api.adzuna.com/v1/api/jobs"

_DEFAULT_RETRIES = 3
_DEFAULT_BACKOFF = 0.5
_DEFAULT_TIMEOUT = 30


def _build_session(retries: int = _DEFAULT_RETRIES) -> requests.Session:
    """Build a requests session with automatic retry."""
    session = requests.Session()
    adapter = HTTPAdapter(
        max_retries=Retry(
            total=retries,
            backoff_factor=_DEFAULT_BACKOFF,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
        )
    )
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


class AdzunaClient:
    """Client for the Adzuna job search API.

    Args:
        app_id: Adzuna application ID. Defaults to ADZUNA_APP_ID env var.
        app_key: Adzuna application key. Defaults to ADZUNA_APP_KEY env var.
        country: Country code (e.g., 'fr', 'gb', 'us').
    """

    def __init__(
        self,
        app_id: str | None = None,
        app_key: str | None = None,
        country: str = "fr",
    ) -> None:
        self.app_id = app_id or os.environ.get("ADZUNA_APP_ID", "")
        self.app_key = app_key or os.environ.get("ADZUNA_APP_KEY", "")
        self.country = country
        self._session = _build_session()

        if not self.app_id or not self.app_key:
            logger.warning("Adzuna credentials missing — ADZUNA_APP_ID / ADZUNA_APP_KEY not set")

    def fetch_jobs(
        self,
        query: str,
        location: str = "",
        page: int = 1,
        results_per_page: int = 50,
        **params: Any,
    ) -> list[dict[str, Any]]:
        """Fetch jobs from Adzuna API.

        Args:
            query: Search keywords.
            location: Location filter.
            page: Page number.
            results_per_page: Results per page (max 50).
            **params: Additional query parameters.

        Returns:
            List of normalized job dicts with keys matching JobItem schema.
        """
        if not self.app_id or not self.app_key:
            logger.error("ADZUNA FETCH ABORTED — API credentials not configured")
            return []

        url = f"{ADZUNA_BASE_URL}/{self.country}/search/{page}"
        request_params = {
            "app_id": self.app_id,
            "app_key": self.app_key,
            "what": query,
            "results_per_page": results_per_page,
            **params,
        }
        if location:
            request_params["where"] = location

        logger.info(
            "START ADZUNA FETCH — query=%r, location=%r, page=%d, per_page=%d",
            query, location, page, results_per_page,
        )

        try:
            start = time.time()
            response = self._session.get(url, params=request_params, timeout=_DEFAULT_TIMEOUT)
            elapsed_ms = int((time.time() - start) * 1000)

            logger.info(
                "ADZUNA RESPONSE — status=%d, size=%d bytes, elapsed=%dms",
                response.status_code, len(response.content), elapsed_ms,
            )
            response.raise_for_status()
            data = response.json()

        except requests.exceptions.HTTPError as exc:
            logger.error(
                "ADZUNA HTTP ERROR — status=%d, query=%r: %s",
                exc.response.status_code if exc.response is not None else 0,
                query, exc,
            )
            raise
        except requests.exceptions.RequestException as exc:
            logger.error("ADZUNA REQUEST FAILED — query=%r: %s", query, exc)
            return []

        results = data.get("results", [])
        jobs = [self._normalize(r) for r in results]

        if not jobs:
            logger.warning("ADZUNA EMPTY — query=%r returned 0 jobs", query)
        else:
            logger.info("ADZUNA OK — query=%r returned %d jobs", query, len(jobs))

        return jobs

    def _normalize(self, raw: dict[str, Any]) -> dict[str, Any]:
        """Normalize an Adzuna result into JobItem schema.

        Args:
            raw: Raw Adzuna API result.

        Returns:
            Normalized job dict.
        """
        return {
            "external_id": str(raw.get("id", "")),
            "title": raw.get("title", ""),
            "company": raw["company"].get("display_name", "") if isinstance(raw.get("company"), dict) else str(raw.get("company", "")),
            "location": raw["location"].get("display_name", "") if isinstance(raw.get("location"), dict) else str(raw.get("location", "")),
            "description": raw.get("description", ""),
            "url": raw.get("redirect_url", ""),
            "salary_min": raw.get("salary_min"),
            "salary_max": raw.get("salary_max"),
            "contract_type": raw.get("contract_type", ""),
            "published_at": raw.get("created", ""),
            "source": "adzuna",
        }
