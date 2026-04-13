"""Scrapy download middlewares for spider resilience.

Provides user-agent rotation and optional proxy rotation to improve
scraping reliability and reduce blocking.
"""

import logging
import random
from typing import Any, Optional

from scrapy import Request, signals
from scrapy.crawler import Crawler
from scrapy.http import Response

logger = logging.getLogger(__name__)

# ── User-Agent pool ──────────────────────────────────────────────────────────
USER_AGENTS: list[str] = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
]


class RotateUserAgentMiddleware:
    """Rotates the User-Agent header on each request.

    Randomizes the User-Agent from a pool of realistic browser strings
    to reduce the chance of being blocked by pattern detection.
    """

    def process_request(self, request: Request, spider: Any) -> None:
        """Set a random User-Agent on the request.

        Args:
            request: The Scrapy request object.
            spider: The spider making the request.
        """
        request.headers["User-Agent"] = random.choice(USER_AGENTS)


class ProxyRotationMiddleware:
    """Optional proxy rotation middleware.

    Reads a list of proxy URLs from the spider setting PROXY_LIST.
    If no proxies are configured, this middleware is a no-op.

    Configure in spider custom_settings or settings.py::

        PROXY_LIST = [
            "http://proxy1:8080",
            "http://proxy2:8080",
        ]
    """

    def __init__(self) -> None:
        self.proxies: list[str] = []

    @classmethod
    def from_crawler(cls, crawler: Crawler) -> "ProxyRotationMiddleware":
        """Create middleware instance from crawler settings.

        Args:
            crawler: The Scrapy crawler.

        Returns:
            Configured middleware instance.
        """
        middleware = cls()
        proxy_list = crawler.settings.getlist("PROXY_LIST", [])
        middleware.proxies = proxy_list
        if proxy_list:
            logger.info("Proxy rotation enabled with %d proxies", len(proxy_list))
        return middleware

    def process_request(self, request: Request, spider: Any) -> None:
        """Set a random proxy on the request if proxies are configured.

        Args:
            request: The Scrapy request object.
            spider: The spider making the request.
        """
        if self.proxies:
            request.meta["proxy"] = random.choice(self.proxies)


class RetryOn429Middleware:
    """Enhanced retry middleware for 429 (Too Many Requests).

    Respects the Retry-After header when present, and applies
    exponential backoff otherwise.
    """

    def __init__(self) -> None:
        self.max_retries = 3

    @classmethod
    def from_crawler(cls, crawler: Crawler) -> "RetryOn429Middleware":
        """Create middleware from crawler settings.

        Args:
            crawler: The Scrapy crawler.

        Returns:
            Configured middleware instance.
        """
        middleware = cls()
        middleware.max_retries = crawler.settings.getint("RETRY_429_TIMES", 3)
        return middleware

    def process_response(
        self, request: Request, response: Response, spider: Any
    ) -> Response | Request:
        """Retry 429 responses with backoff.

        Args:
            request: The original request.
            response: The received response.
            spider: The spider making the request.

        Returns:
            Response if not retrying, or a new Request to retry.
        """
        if response.status != 429:
            return response

        retries = request.meta.get("retry_429_count", 0)
        if retries >= self.max_retries:
            logger.warning(
                "429 max retries reached for %s after %d attempts",
                request.url, retries,
            )
            return response

        retry_after = response.headers.get("Retry-After", b"").decode("utf-8", errors="ignore")
        delay = float(retry_after) if retry_after.isdigit() else (2 ** retries * 5)

        logger.info(
            "429 on %s — retry %d/%d after %.0fs",
            request.url, retries + 1, self.max_retries, delay,
        )

        new_request = request.copy()
        new_request.meta["retry_429_count"] = retries + 1
        new_request.meta["download_delay"] = delay
        new_request.dont_filter = True
        return new_request
