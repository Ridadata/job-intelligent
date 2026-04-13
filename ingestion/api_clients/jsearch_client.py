"""JSearch (RapidAPI) client — broad job aggregator coverage.

Docs: https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch
API key via JSEARCH_API_KEY env var.
"""

import logging
import os
import time
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

JSEARCH_BASE_URL = "https://jsearch.p.rapidapi.com/search"

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


class JSearchClient:
    """Client for the JSearch job API on RapidAPI.

    Args:
        api_key: RapidAPI key. Defaults to JSEARCH_API_KEY env var.
    """

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.environ.get("JSEARCH_API_KEY", "")
        self._session = _build_session()

        if not self.api_key:
            logger.warning("JSearch credentials missing — JSEARCH_API_KEY not set")

    def fetch_jobs(
        self,
        query: str,
        location: str = "",
        page: int = 1,
        num_pages: int = 1,
        **params: Any,
    ) -> list[dict[str, Any]]:
        """Fetch jobs from JSearch API.

        Args:
            query: Search keywords.
            location: Location filter (appended to query).
            page: Page number.
            num_pages: Number of pages to fetch.
            **params: Additional parameters.

        Returns:
            List of normalized job dicts.
        """
        if not self.api_key:
            logger.error("JSEARCH FETCH ABORTED — API key not configured")
            return []

        search_query = f"{query} {location}".strip() if location else query
        headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
        }
        request_params = {
            "query": search_query,
            "page": str(page),
            "num_pages": str(num_pages),
            **params,
        }

        logger.info(
            "START JSEARCH FETCH — query=%r, location=%r, page=%d, num_pages=%d",
            query, location, page, num_pages,
        )

        try:
            start = time.time()
            response = self._session.get(
                JSEARCH_BASE_URL, headers=headers, params=request_params,
                timeout=_DEFAULT_TIMEOUT,
            )
            elapsed_ms = int((time.time() - start) * 1000)

            logger.info(
                "JSEARCH RESPONSE — status=%d, size=%d bytes, elapsed=%dms",
                response.status_code, len(response.content), elapsed_ms,
            )
            response.raise_for_status()
            data = response.json()

        except requests.exceptions.HTTPError as exc:
            logger.error(
                "JSEARCH HTTP ERROR — status=%d, query=%r: %s",
                exc.response.status_code if exc.response is not None else 0,
                query, exc,
            )
            return []
        except requests.exceptions.RequestException as exc:
            logger.error("JSEARCH REQUEST FAILED — query=%r: %s", query, exc)
            return []

        results = data.get("data", [])
        jobs = [self._normalize(r) for r in results if r]

        if not jobs:
            logger.warning("JSEARCH EMPTY — query=%r returned 0 jobs", query)
        else:
            logger.info("JSEARCH OK — query=%r returned %d jobs", query, len(jobs))

        return jobs

    def _normalize(self, raw: dict[str, Any]) -> dict[str, Any]:
        """Normalize a JSearch result into JobItem schema.

        Args:
            raw: Raw JSearch API result.

        Returns:
            Normalized job dict.
        """
        city = raw.get("job_city", "") or ""
        country = raw.get("job_country", "") or ""
        location = ", ".join(p for p in [city, country] if p)

        return {
            "external_id": raw.get("job_id", ""),
            "title": raw.get("job_title", ""),
            "company": raw.get("employer_name", ""),
            "location": location,
            "description": raw.get("job_description", ""),
            "url": raw.get("job_apply_link", ""),
            "salary_min": raw.get("job_min_salary"),
            "salary_max": raw.get("job_max_salary"),
            "contract_type": raw.get("job_employment_type", ""),
            "published_at": raw.get("job_posted_at_datetime_utc", ""),
            "source": "jsearch",
        }
