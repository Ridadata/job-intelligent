"""France Travail API client — official French public employment data.

Docs: https://francetravail.io/
API keys via FRANCE_TRAVAIL_CLIENT_ID and FRANCE_TRAVAIL_CLIENT_SECRET env vars.
"""

import logging
import os
import time
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

AUTH_URL = "https://entreprise.francetravail.fr/connexion/oauth2/access_token"
SEARCH_URL = "https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search"

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
            allowed_methods=["GET", "POST"],
        )
    )
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


class FranceTravailClient:
    """Client for the France Travail (ex-Pôle Emploi) job API.

    Args:
        client_id: OAuth client ID. Defaults to FRANCE_TRAVAIL_CLIENT_ID env var.
        client_secret: OAuth client secret. Defaults to FRANCE_TRAVAIL_CLIENT_SECRET env var.
    """

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
    ) -> None:
        self.client_id = client_id or os.environ.get("FRANCE_TRAVAIL_CLIENT_ID", "")
        self.client_secret = client_secret or os.environ.get("FRANCE_TRAVAIL_CLIENT_SECRET", "")
        self._token: str | None = None
        self._session = _build_session()

        if not self.client_id or not self.client_secret:
            logger.warning(
                "France Travail credentials missing — "
                "FRANCE_TRAVAIL_CLIENT_ID / FRANCE_TRAVAIL_CLIENT_SECRET not set"
            )

    def _authenticate(self) -> str | None:
        """Obtain an OAuth2 access token.

        Returns:
            Access token string, or None on failure.
        """
        if not self.client_id or not self.client_secret:
            logger.error("FRANCE_TRAVAIL AUTH ABORTED — credentials not configured")
            return None

        logger.info("START FRANCE_TRAVAIL AUTH — requesting access token")

        try:
            start = time.time()
            response = self._session.post(
                AUTH_URL,
                params={"realm": "/partenaire"},
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "scope": "api_offresdemploiv2 o2dsoffre",
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=15,
            )
            elapsed_ms = int((time.time() - start) * 1000)

            logger.info(
                "FRANCE_TRAVAIL AUTH RESPONSE — status=%d, elapsed=%dms",
                response.status_code, elapsed_ms,
            )
            response.raise_for_status()
            self._token = response.json()["access_token"]
            logger.info("FRANCE_TRAVAIL AUTH OK — token obtained")
            return self._token

        except requests.exceptions.HTTPError as exc:
            logger.error(
                "FRANCE_TRAVAIL AUTH HTTP ERROR — status=%d: %s",
                exc.response.status_code if exc.response is not None else 0, exc,
            )
            return None
        except (requests.exceptions.RequestException, KeyError) as exc:
            logger.error("FRANCE_TRAVAIL AUTH FAILED — %s", exc)
            return None

    def fetch_jobs(
        self,
        query: str,
        location: str = "",
        page: int = 0,
        per_page: int = 50,
        **params: Any,
    ) -> list[dict[str, Any]]:
        """Fetch jobs from France Travail API.

        Args:
            query: Search keywords (motsCles).
            location: Commune code or department.
            page: Page index (0-based).
            per_page: Results per page (max 150).
            **params: Additional API parameters.

        Returns:
            List of normalized job dicts.
        """
        token = self._token or self._authenticate()
        if not token:
            logger.error("FRANCE_TRAVAIL FETCH ABORTED — no valid token")
            return []

        headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
        request_params: dict[str, Any] = {
            "motsCles": query,
            "range": f"{page * per_page}-{(page + 1) * per_page - 1}",
            **params,
        }
        if location:
            request_params["commune"] = location

        logger.info(
            "START FRANCE_TRAVAIL FETCH — query=%r, location=%r, page=%d, per_page=%d",
            query, location, page, per_page,
        )

        try:
            start = time.time()
            response = self._session.get(
                SEARCH_URL, headers=headers, params=request_params,
                timeout=_DEFAULT_TIMEOUT,
            )
            elapsed_ms = int((time.time() - start) * 1000)

            logger.info(
                "FRANCE_TRAVAIL RESPONSE — status=%d, size=%d bytes, elapsed=%dms",
                response.status_code, len(response.content), elapsed_ms,
            )

            # Token expired — re-authenticate once
            if response.status_code == 401:
                logger.warning("FRANCE_TRAVAIL TOKEN EXPIRED — re-authenticating")
                self._token = None
                token = self._authenticate()
                if not token:
                    return []
                headers["Authorization"] = f"Bearer {token}"
                response = self._session.get(
                    SEARCH_URL, headers=headers, params=request_params,
                    timeout=_DEFAULT_TIMEOUT,
                )

            response.raise_for_status()
            data = response.json()

        except requests.exceptions.HTTPError as exc:
            logger.error(
                "FRANCE_TRAVAIL HTTP ERROR — status=%d, query=%r: %s",
                exc.response.status_code if exc.response is not None else 0,
                query, exc,
            )
            return []
        except requests.exceptions.RequestException as exc:
            logger.error("FRANCE_TRAVAIL REQUEST FAILED — query=%r: %s", query, exc)
            return []

        results = data.get("resultats", [])
        jobs = [self._normalize(r) for r in results if r]

        if not jobs:
            logger.warning("FRANCE_TRAVAIL EMPTY — query=%r returned 0 jobs", query)
        else:
            logger.info("FRANCE_TRAVAIL OK — query=%r returned %d jobs", query, len(jobs))

        return jobs

    def _normalize(self, raw: dict[str, Any]) -> dict[str, Any]:
        """Normalize a France Travail result into JobItem schema.

        Args:
            raw: Raw API result.

        Returns:
            Normalized job dict.
        """
        return {
            "external_id": raw.get("id", ""),
            "title": raw.get("intitule", ""),
            "company": raw.get("entreprise", {}).get("nom", ""),
            "location": raw.get("lieuTravail", {}).get("libelle", ""),
            "description": raw.get("description", ""),
            "url": raw.get("origineOffre", {}).get("urlOrigine", ""),
            "salary_min": None,
            "salary_max": None,
            "contract_type": raw.get("typeContratLibelle", ""),
            "published_at": raw.get("dateCreation", ""),
            "source": "france_travail",
        }
