"""Scrapy pipelines for collecting and batching scraped job offers."""

import logging
from typing import Any

from scrapy import Spider

logger = logging.getLogger(__name__)


class JobOfferCollectorPipeline:
    """Collects scraped job offers into a list for batch ingestion.

    Items are accumulated in memory and can be retrieved after the
    spider finishes via the spider's `collected_items` attribute.
    """

    def open_spider(self, spider: Spider) -> None:
        """Initialize the item collection list on spider open.

        Args:
            spider: The Scrapy spider instance.
        """
        spider.collected_items: list[dict[str, Any]] = []  # type: ignore[attr-defined]
        logger.info("Pipeline opened for spider '%s'", spider.name)

    def process_item(self, item: dict[str, Any], spider: Spider) -> dict[str, Any]:
        """Collect each item into the spider's list.

        Args:
            item: The scraped item dictionary.
            spider: The Scrapy spider instance.

        Returns:
            The unmodified item.
        """
        spider.collected_items.append(dict(item))  # type: ignore[attr-defined]
        return item

    def close_spider(self, spider: Spider) -> None:
        """Log collection stats when spider closes.

        Args:
            spider: The Scrapy spider instance.
        """
        count = len(spider.collected_items)  # type: ignore[attr-defined]
        logger.info(
            "Pipeline closed for spider '%s': %d items collected",
            spider.name, count,
        )
