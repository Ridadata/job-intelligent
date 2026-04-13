"""API clients for external job data sources.

One client class per API. Each implements fetch_jobs(query, location, **params) -> list[dict].
API keys come from environment variables — never hardcode.
"""
