"""Rekrute.com spider for data job offers.

Scrapes data-related job offers from Rekrute.com, Morocco's leading
job board. Targets data science, data engineering, and ML positions.
"""

import logging
import re
from typing import Any, Generator
from urllib.parse import urlencode

import scrapy
from scrapy.http import Response

from job_scrapers.items import JobOfferItem

logger = logging.getLogger(__name__)

SEARCH_QUERIES: list[str] = [
    "data scientist",
    "data engineer",
    "data analyst",
    "machine learning",
    "big data",
    "MLOps",
    "BI analyst",
    "intelligence artificielle",
    "python développeur",
    "devops",
    "cloud engineer",
    "ETL",
]

BASE_URL = "https://www.rekrute.com/offres.html"


class RekruteSpider(scrapy.Spider):
    """Spider for scraping data job offers from Rekrute.com.

    Attributes:
        name: Spider identifier used by Scrapy.
        allowed_domains: Domains this spider is allowed to crawl.
        source_name: Source platform name for ETL ingestion.
    """

    name: str = "rekrute"
    allowed_domains: list[str] = ["www.rekrute.com"]
    source_name: str = "rekrute"
    custom_settings: dict[str, Any] = {
        "DOWNLOAD_DELAY": 1.5,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 2,
        "ROBOTSTXT_OBEY": False,
    }

    def start_requests(self) -> Generator[scrapy.Request, None, None]:
        """Generate initial search requests for each keyword."""
        for query in SEARCH_QUERIES:
            params = urlencode({
                "s": "1",
                "p": "1",
                "o": "1",
                "keyword": query,
            })
            url = f"{BASE_URL}?{params}"
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                meta={"query": query, "page": 1},
            )

    def parse(self, response: Response) -> Generator[Any, None, None]:
        """Parse search results page and extract job listing links."""
        # Extract job offer links from search results
        job_links = response.css(
            'a[href*="/offre-emploi-"]::attr(href)'
        ).getall()

        seen = set()
        for link in job_links:
            # Skip matching/4K links
            if "#matching4K" in link or "utm_home" in link:
                continue
            if link not in seen:
                seen.add(link)
                yield response.follow(
                    link,
                    callback=self.parse_job,
                    meta={"query": response.meta["query"]},
                )

        # Pagination: max 5 pages per query
        current_page = response.meta.get("page", 1)
        if current_page < 5 and job_links:
            next_page = current_page + 1
            params = urlencode({
                "s": "1",
                "p": str(next_page),
                "o": "1",
                "keyword": response.meta["query"],
            })
            next_url = f"{BASE_URL}?{params}"
            yield scrapy.Request(
                url=next_url,
                callback=self.parse,
                meta={"query": response.meta["query"], "page": next_page},
            )

    def parse_job(self, response: Response) -> Generator[JobOfferItem, None, None]:
        """Parse individual job page and extract offer details."""
        item = JobOfferItem()

        # External ID from URL (the numeric ID at the end)
        match = re.search(r"-(\d+)\.html", response.url)
        item["external_id"] = f"rekrute_{match.group(1)}" if match else ""
        item["source"] = self.source_name
        item["url"] = response.url

        # Title from h1 (format: "Title - City")
        raw_title = response.css("h1::text").get("").strip()
        if " - " in raw_title:
            item["title"] = raw_title.rsplit(" - ", 1)[0].strip()
        else:
            item["title"] = raw_title

        # Company from URL slug: /offre-emploi-...-recrutement-{company}-{city}-{id}.html
        company = ""
        url_match = re.search(r"recrutement-([\w-]+)-\w+-\d+\.html", response.url)
        if url_match:
            company = url_match.group(1).replace("-", " ").title()
        item["company"] = company

        # Build a dict of blc sections keyed by h2 text
        sections: dict[str, str] = {}
        for blc in response.css("div.blc"):
            h2_texts = blc.css("h2::text").getall()
            h2_label = " ".join(t.strip() for t in h2_texts if t.strip())
            all_text = blc.css("div::text, p::text, li::text, span::text").getall()
            content = " ".join(t.strip() for t in all_text if t.strip())
            if h2_label:
                sections[h2_label] = content

        # Location from "Adresse de notre siège :" section or title suffix
        location = ""
        for key, val in sections.items():
            if "Adresse" in key:
                location = val.strip()
                break
        if not location and " - " in raw_title:
            location = raw_title.rsplit(" - ", 1)[-1].strip()
        item["location"] = location

        # Contract type (CDI, CDD, etc.)
        page_text = " ".join(response.css("body *::text").getall())
        contract = ""
        for ct in ["CDI", "CDD", "Stage", "Freelance", "Intérim", "Alternance"]:
            if ct in page_text:
                contract = ct
                break
        item["contract_type"] = contract

        # Description from Poste + Profil sections
        description_parts = []
        for key, val in sections.items():
            if "Poste" in key and "Adresse" not in key:
                description_parts.append(val)
            elif "Profil" in key:
                description_parts.append(val)
        if not description_parts:
            # Fallback to Entreprise section
            for key, val in sections.items():
                if "Entreprise" in key:
                    description_parts.append(val)
                    break
        item["description"] = "\n".join(description_parts)

        # Published date
        pub_match = re.search(
            r'Publi[ée]e?\s+il\s+y\s+a\s+(\d+)\s+(jour|heure|semaine)',
            page_text, re.IGNORECASE,
        )
        item["published_at"] = ""
        if pub_match:
            from datetime import datetime, timedelta
            num = int(pub_match.group(1))
            unit = pub_match.group(2).lower()
            delta = {"jour": timedelta(days=num), "heure": timedelta(hours=num),
                     "semaine": timedelta(weeks=num)}.get(unit, timedelta(days=num))
            item["published_at"] = (datetime.utcnow() - delta).isoformat()

        # Salary (rekrute rarely shows salary, but try)
        salary_match = re.search(
            r'(\d[\d\s]*)\s*(?:à|-)?\s*(\d[\d\s]*)?\s*(?:MAD|DH|€|EUR)',
            page_text, re.IGNORECASE,
        )
        if salary_match:
            item["salary"] = salary_match.group(0).strip()
            item["salary_min"] = int(salary_match.group(1).replace(" ", ""))
            item["salary_max"] = int(
                salary_match.group(2).replace(" ", "")
            ) if salary_match.group(2) else None
        else:
            item["salary"] = ""
            item["salary_min"] = None
            item["salary_max"] = None

        if item["title"] and item["external_id"]:
            yield item
