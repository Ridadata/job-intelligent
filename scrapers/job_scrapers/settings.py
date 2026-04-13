"""Scrapy settings for job scraping spiders."""

BOT_NAME = "job_scrapers"

SPIDER_MODULES = ["job_scrapers.spiders"]
NEWSPIDER_MODULE = "job_scrapers.spiders"

# ── Politeness settings ─────────────────────────────────────────────────────
ROBOTSTXT_OBEY = True
DOWNLOAD_DELAY = 2
RANDOMIZE_DOWNLOAD_DELAY = True
CONCURRENT_REQUESTS = 4
CONCURRENT_REQUESTS_PER_DOMAIN = 2

# ── User agent ───────────────────────────────────────────────────────────────
# Default UA (overridden per-request by RotateUserAgentMiddleware)
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36"
)

# ── Download middlewares ─────────────────────────────────────────────────────
DOWNLOADER_MIDDLEWARES = {
    "job_scrapers.middlewares.RotateUserAgentMiddleware": 400,
    "job_scrapers.middlewares.ProxyRotationMiddleware": 410,
    "job_scrapers.middlewares.RetryOn429Middleware": 420,
}

# ── AutoThrottle ─────────────────────────────────────────────────────────────
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 2
AUTOTHROTTLE_MAX_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 2.0

# ── Feed / Item pipeline ────────────────────────────────────────────────────
ITEM_PIPELINES = {
    "job_scrapers.pipelines.JobOfferCollectorPipeline": 300,
}

# ── Retry ────────────────────────────────────────────────────────────────────
RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]

# ── Logging ──────────────────────────────────────────────────────────────────
LOG_LEVEL = "INFO"

# ── Cache (useful for development) ──────────────────────────────────────────
# HTTPCACHE_ENABLED = True
# HTTPCACHE_EXPIRATION_SECS = 3600
# HTTPCACHE_DIR = "httpcache"

# ── Output ───────────────────────────────────────────────────────────────────
FEED_EXPORT_ENCODING = "utf-8"

# ── Misc ─────────────────────────────────────────────────────────────────────
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
