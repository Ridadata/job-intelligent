"""Emploi.ma spider for data job offers.

Scrapes data-related job offers from Emploi.ma, part of the AfricaTalents
network. Targets data science, data engineering, ML, and IT positions.
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
    "python développeur",
    "intelligence artificielle",
    "devops",
    "cloud engineer",
    "BI analyst",
]

BASE_URL = "https://www.emploi.ma/recherche-jobs-maroc"


class EmploiMaSpider(scrapy.Spider):
    """Spider for scraping job offers from Emploi.ma."""

    name: str = "emploi_ma"
    allowed_domains: list[str] = ["www.emploi.ma"]
    source_name: str = "emploi_ma"
    custom_settings: dict[str, Any] = {
        "DOWNLOAD_DELAY": 1.5,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 2,
        "ROBOTSTXT_OBEY": True,
    }

    def start_requests(self) -> Generator[scrapy.Request, None, None]:
        """Generate search requests for each keyword."""
        for query in SEARCH_QUERIES:
            url = f"{BASE_URL}/{query.replace(' ', '+')}"
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                meta={"query": query, "page": 0},
            )

    def parse(self, response: Response) -> Generator[Any, None, None]:
        """Parse search results and follow job detail links."""
        job_links = response.css(
            'a[href*="/offre-emploi-maroc/"]::attr(href)'
        ).getall()

        seen = set()
        for link in job_links:
            if link not in seen:
                seen.add(link)
                yield response.follow(
                    link,
                    callback=self.parse_job,
                    meta={"query": response.meta["query"]},
                )

        # Pagination: max 5 pages per query
        current_page = response.meta.get("page", 0)
        if current_page < 4 and job_links:
            next_page = current_page + 1
            next_url = f"{BASE_URL}/{response.meta['query'].replace(' ', '+')}?page={next_page}"
            yield scrapy.Request(
                url=next_url,
                callback=self.parse,
                meta={"query": response.meta["query"], "page": next_page},
            )

    def parse_job(self, response: Response) -> Generator[JobOfferItem, None, None]:
        """Parse individual job page and extract details."""
        import json

        item = JobOfferItem()

        # External ID from URL
        id_match = re.search(r"-(\d+)$", response.url.rstrip("/"))
        item["external_id"] = f"emploi_ma_{id_match.group(1)}" if id_match else ""
        item["source"] = self.source_name
        item["url"] = response.url

        # Try JSON-LD structured data first (most reliable)
        jsonld = {}
        for script in response.xpath('//script[contains(text(),"JobPosting")]/text()').getall():
            try:
                jsonld = json.loads(script.strip(), strict=False)
                if jsonld.get("@type") == "JobPosting":
                    break
                jsonld = {}
            except (json.JSONDecodeError, TypeError):
                continue

        # Title
        item["title"] = (
            jsonld.get("title", "")
            or response.css("h1::text").get("").strip()
        )

        # Company — from JSON-LD or HTML
        item["company"] = ""
        org = jsonld.get("hiringOrganization")
        if isinstance(org, dict):
            item["company"] = org.get("name", "")
        if not item["company"]:
            item["company"] = response.xpath(
                '//strong[contains(text(),"Type de contrat")]'
                '/ancestor::ul/preceding-sibling::*'
                '//a[contains(@href,"/recruteur/")]/text()'
            ).get("").strip()
        if not item["company"]:
            item["company"] = response.css(
                'h3 a[href*="/recruteur/"]::text'
            ).get("").strip()

        # Location — from JSON-LD or HTML
        item["location"] = ""
        loc = jsonld.get("jobLocation")
        if isinstance(loc, dict):
            addr = loc.get("address", {})
            if isinstance(addr, dict):
                item["location"] = addr.get("addressLocality", "")
        if not item["location"]:
            city_span = response.xpath(
                '//strong[contains(text(),"Ville")]/following-sibling::span/text()'
            ).get("")
            item["location"] = city_span.strip()
        if not item["location"] and " - " in item["title"]:
            item["location"] = item["title"].rsplit(" - ", 1)[-1].strip()

        # Contract type — from JSON-LD or HTML
        item["contract_type"] = jsonld.get("employmentType", "")
        if not item["contract_type"]:
            ct_span = response.xpath(
                '//strong[contains(text(),"Type de contrat")]/following-sibling::span/text()'
            ).get("")
            item["contract_type"] = ct_span.strip()

        # Description — "Poste proposé" + "Profil recherché" sections
        description_parts = []

        poste_section = response.xpath(
            '//h3[contains(text(),"Poste proposé")]/following-sibling::*//text()'
        ).getall()
        if poste_section:
            text = " ".join(t.strip() for t in poste_section if t.strip())
            if text:
                description_parts.append(text)

        profil_section = response.xpath(
            '//h3[contains(text(),"Profil recherché")]/following-sibling::*//text()'
        ).getall()
        if profil_section:
            text = " ".join(t.strip() for t in profil_section if t.strip())
            if text:
                description_parts.append(text)

        # Fallback: JSON-LD description (HTML stripped)
        if not description_parts and jsonld.get("description"):
            from scrapy.utils.markup import remove_tags
            description_parts.append(remove_tags(jsonld["description"])[:3000])

        item["description"] = "\n".join(description_parts)

        # Published date — from JSON-LD or page text
        item["published_at"] = ""
        if jsonld.get("datePosted"):
            item["published_at"] = jsonld["datePosted"]
        else:
            pub_match = re.search(
                r'Publi[ée]e?\s+le\s+(\d{2}\.\d{2}\.\d{4})',
                " ".join(response.css("body *::text").getall()),
            )
            if pub_match:
                from datetime import datetime
                try:
                    dt = datetime.strptime(pub_match.group(1), "%d.%m.%Y")
                    item["published_at"] = dt.isoformat()
                except ValueError:
                    pass

        # Salary
        item["salary"] = ""
        item["salary_min"] = None
        item["salary_max"] = None

        if item["title"] and item["external_id"]:
            yield item
