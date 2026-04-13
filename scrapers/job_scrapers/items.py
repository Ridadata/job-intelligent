"""Scrapy Item definitions for job offer scraping."""

import scrapy


class JobOfferItem(scrapy.Item):
    """Standard item representing a scraped job offer.

    All spiders should populate these fields from their respective
    source platforms. Fields map to raw_json in raw_job_offers.
    """

    external_id = scrapy.Field()
    title = scrapy.Field()
    company = scrapy.Field()
    location = scrapy.Field()
    description = scrapy.Field()
    contract_type = scrapy.Field()
    salary = scrapy.Field()
    salary_min = scrapy.Field()
    salary_max = scrapy.Field()
    url = scrapy.Field()
    published_at = scrapy.Field()
    source = scrapy.Field()
