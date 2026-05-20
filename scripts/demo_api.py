"""
Quick demo: fetch real jobs from APIs and show them after cleaning.

Usage:
    python demo_api.py

Reads credentials from .env automatically (via python-dotenv).
No need to set env vars manually.
"""

import os

# Load .env automatically
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed — env vars must be set manually

# ── Helpers ──────────────────────────────────────────────────────────────────

def _sep(label: str) -> None:
    width = 70
    print(f"\n{'─' * width}")
    print(f"  {label}")
    print(f"{'─' * width}")


def _print_job(i: int, job: dict, *, show_cleaned: bool = True) -> None:
    title_raw = job.get("title", "")
    company   = job.get("company", "") or "—"
    location  = job.get("location", "") or "—"
    contract  = job.get("contract_type", "") or "—"
    url       = job.get("url", "") or "—"
    source    = job.get("source", "")

    from pipeline.cleaning.job_cleaner import (
        normalize_title,
        standardize_contract,
        validate_job,
    )

    title_clean = normalize_title(title_raw)
    contract_std = standardize_contract(contract)
    valid, reasons = validate_job(job)
    status = "✓ valid" if valid else f"✗ quarantine ({', '.join(reasons)})"

    print(f"\n  [{i+1}] [{source.upper()}]")
    print(f"      RAW title  : {title_raw}")
    if show_cleaned:
        changed = title_raw != title_clean
        print(f"      CLEAN title: {title_clean}  {'← changed' if changed else ''}")
    print(f"      Company    : {company}")
    print(f"      Location   : {location}")
    print(f"      Contract   : {contract}  →  {contract_std}")
    print(f"      URL        : {url[:70]}")
    print(f"      Status     : {status}")


def _demo_source(name: str, jobs: list[dict]) -> None:
    _sep(f"{name}  ({len(jobs)} jobs fetched)")
    if not jobs:
        print("  (no results — check API credentials or query returned empty)")
        return
    for i, job in enumerate(jobs[:5]):   # show max 5 per source
        _print_job(i, job)
    if len(jobs) > 5:
        print(f"\n  … and {len(jobs) - 5} more jobs")


# ── API calls ────────────────────────────────────────────────────────────────

QUERIES = ["data engineer", "data scientist"]

def fetch_adzuna() -> list[dict]:
    try:
        from ingestion.api_clients.adzuna_client import AdzunaClient
        c = AdzunaClient()
        results = []
        for q in QUERIES:
            results.extend(c.fetch_jobs(q, location="france", results_per_page=5))
        return results
    except Exception as e:
        print(f"  Adzuna error: {e}")
        return []


def fetch_jsearch() -> list[dict]:
    try:
        from ingestion.api_clients.jsearch_client import JSearchClient
        c = JSearchClient()
        results = []
        for q in QUERIES:
            results.extend(c.fetch_jobs(q, location="France", num_pages=1))
        return results
    except Exception as e:
        print(f"  JSearch error: {e}")
        return []


# ── Cleaning summary ─────────────────────────────────────────────────────────

def cleaning_summary(all_jobs: list[dict]) -> None:
    from pipeline.cleaning.job_cleaner import (
        normalize_title, standardize_contract, validate_job,
        compute_dedup_key, IngestionMetrics,
    )

    _sep("Cleaning + Validation Summary")

    metrics = IngestionMetrics("demo")
    metrics.fetched = len(all_jobs)

    seen_keys: set[str] = set()
    dupes = 0

    for job in all_jobs:
        valid, _ = validate_job(job)
        if valid:
            metrics.cleaned += 1
        else:
            metrics.rejected += 1

        key = compute_dedup_key(
            normalize_title(job.get("title", "")),
            job.get("company", ""),
            job.get("location", ""),
        )
        if key in seen_keys:
            dupes += 1
        seen_keys.add(key)

    metrics.inserted = metrics.cleaned - dupes
    metrics.log_summary()

    print(f"\n  Duplicates detected (hash-based) : {dupes}")
    print(f"  Unique insertable jobs           : {metrics.inserted}")

    # Contract type distribution
    from collections import Counter
    contracts = Counter(
        standardize_contract(j.get("contract_type", "")) for j in all_jobs
    )
    print("\n  Contract distribution:")
    for ctype, count in sorted(contracts.items(), key=lambda x: -x[1]):
        print(f"    {ctype:15s} {count}")


# ── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.WARNING)   # suppress verbose HTTP logs for demo

    print("\n" + "═" * 70)
    print("  JOB INTELLIGENT — API Demo")
    print("═" * 70)

    print("\n  Credentials detected:")
    print(f"    Adzuna  : {'✓' if os.environ.get('ADZUNA_APP_ID') else '✗ not set (ADZUNA_APP_ID)'}")
    print(f"    JSearch : {'✓' if os.environ.get('JSEARCH_API_KEY') else '✗ not set (JSEARCH_API_KEY)'}")

    print(f"\n  Queries: {QUERIES}")

    adzuna_jobs  = fetch_adzuna()
    jsearch_jobs = fetch_jsearch()

    _demo_source("Adzuna", adzuna_jobs)
    _demo_source("JSearch", jsearch_jobs)

    all_jobs = adzuna_jobs + jsearch_jobs
    if all_jobs:
        cleaning_summary(all_jobs)

    print("\n" + "═" * 70)
    print(f"  Total jobs fetched: {len(all_jobs)}")
    print("═" * 70 + "\n")
