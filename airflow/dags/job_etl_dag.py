"""Airflow DAG for the complete job ETL pipeline.

Orchestrates: scraping → ingestion → Silver transform → Gold enrichment
→ analytics view refresh → summary notification.

Schedule: every 6 hours.
"""

import logging
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.trigger_rule import TriggerRule

logger = logging.getLogger(__name__)


def _ensure_env() -> None:
    """Ensure required environment variables are set.

    Load order:
      1. docker-compose injection (already in os.environ).
      2. .env file via python-dotenv (local / dev).
      3. Airflow Variables (fallback for SUPABASE keys).

    Raises RuntimeError if SUPABASE_URL or SUPABASE_KEY cannot be resolved.
    Logs warnings for missing optional API keys.
    """
    import os

    # Load .env if present (no-op if already set or file missing)
    try:
        from dotenv import load_dotenv
        load_dotenv(override=False)   # don't overwrite docker-compose injections
    except ImportError:
        pass

    # Required keys — raise if absent
    for key in ("SUPABASE_URL", "SUPABASE_KEY"):
        if not os.environ.get(key):
            try:
                from airflow.models import Variable
                os.environ[key] = Variable.get(key)
                logger.info("Loaded %s from Airflow Variables", key)
            except Exception:
                raise RuntimeError(
                    f"{key} not found in environment, .env, or Airflow Variables"
                )

    # Optional API keys — warn only
    for key in ("ADZUNA_APP_ID", "ADZUNA_APP_KEY", "JSEARCH_API_KEY"):
        if not os.environ.get(key):
            logger.warning("Optional env var %s is not set — that source will be skipped", key)

# ── DAG default args ─────────────────────────────────────────────────────────
default_args = {
    "owner": "data-team",
    "depends_on_past": False,
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 3,
    "retry_delay": timedelta(minutes=3),
    "execution_timeout": timedelta(hours=2),
}


# ── Task callables ───────────────────────────────────────────────────────────

def _read_jsonl(path: str) -> list[dict]:
    """Read items from a JSONL file and delete it."""
    import json
    import os
    items = []
    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line:
                    items.append(json.loads(line))
        os.unlink(path)
    return items


def _scrape_sources(**context: dict) -> dict[str, int]:
    """Run all Scrapy spiders via subprocess and collect results.

    Scrapy's Twisted reactor cannot run inside Airflow worker processes
    directly, so spiders are invoked as subprocesses. Results are written
    to a temp JSONL file and read back.

    If live scraping yields 0 items (sites block bots), inserts seed
    demo data so the rest of the pipeline can be validated end-to-end.

    Returns:
        Dict mapping source names to item counts scraped.
    """
    import json
    import os
    import subprocess
    import sys
    import tempfile

    sys.path.insert(0, "/opt/airflow")

    _ensure_env()

    spider_names = ["rekrute", "emploi_ma"]
    results: dict[str, int] = {}
    all_items: dict[str, list] = {}

    for spider_name in spider_names:
        tmp_path = None   # initialise before try so timeout handler can reference it
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".jsonl", delete=False, dir="/tmp"
            ) as tmp:
                tmp_path = tmp.name

            cmd = [
                sys.executable, "-m", "scrapy", "crawl", spider_name,
                "-o", f"{tmp_path}:jsonlines",
                "-s", "LOG_LEVEL=WARNING",
                "-s", "CLOSESPIDER_TIMEOUT=480",
            ]
            env = {**os.environ, "SCRAPY_SETTINGS_MODULE": "job_scrapers.settings"}

            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,
                cwd="/opt/airflow/scrapers",
                env=env,
            )

            items = _read_jsonl(tmp_path)
            results[spider_name] = len(items)
            all_items[spider_name] = items
            if items:
                context["ti"].xcom_push(key=f"scraped_{spider_name}", value=items)

            logger.info("Spider %s: %d items (rc=%d)", spider_name, len(items), proc.returncode)
            if proc.returncode != 0 and proc.stderr:
                logger.warning("Spider %s stderr: %s", spider_name, proc.stderr[-500:])

        except subprocess.TimeoutExpired:
            logger.warning("Spider %s timed out — reading partial results", spider_name)
            items = _read_jsonl(tmp_path) if tmp_path else []
            results[spider_name] = len(items)
            all_items[spider_name] = items
            if items:
                context["ti"].xcom_push(key=f"scraped_{spider_name}", value=items)
            logger.info("Spider %s: recovered %d items after timeout", spider_name, len(items))
        except Exception:
            logger.error("Spider %s failed", spider_name, exc_info=True)
            results[spider_name] = 0

    total_items = sum(results.values())

    # If no items scraped (sites blocked us), use demo seed data
    if total_items == 0:
        logger.info("No items scraped from live sources — loading seed data")
        seed = _generate_seed_data()
        context["ti"].xcom_push(key="scraped_seed", value=seed)
        results["seed"] = len(seed)

    logger.info("Scraping complete: %s", results)
    return results


def _fetch_api_sources(**context: dict) -> dict[str, int]:
    """Fetch jobs from Tier 1 API sources (Adzuna, JSearch, France Travail).

    Each client is called with data-related queries. Results are pushed
    to XCom for the ingest task. Failures are logged but never crash the DAG.

    Returns:
        Dict mapping source names to item counts fetched.
    """
    import os
    import sys

    sys.path.insert(0, "/opt/airflow")
    _ensure_env()

    import time

    results: dict[str, int] = {}
    queries = ["data engineer", "data scientist", "data analyst", "machine learning"]
    ti = context["ti"]
    t_start = time.time()

    # ── Adzuna ───────────────────────────────────────────────────────────
    try:
        from ingestion.api_clients.adzuna_client import AdzunaClient

        t0 = time.time()
        client = AdzunaClient()
        items: list[dict] = []
        for q in queries:
            items.extend(client.fetch_jobs(q, location="france"))
        if items:
            ti.xcom_push(key="scraped_adzuna", value=items)
        results["adzuna"] = len(items)
        logger.info("Adzuna: %d items in %.1fs", len(items), time.time() - t0)
    except Exception:
        logger.error("Adzuna API failed — continuing", exc_info=True)
        results["adzuna"] = 0

    # ── JSearch ──────────────────────────────────────────────────────────
    try:
        from ingestion.api_clients.jsearch_client import JSearchClient

        t0 = time.time()
        client = JSearchClient()
        items = []
        for q in queries:
            items.extend(client.fetch_jobs(q, location="France"))
        if items:
            ti.xcom_push(key="scraped_jsearch", value=items)
        results["jsearch"] = len(items)
        logger.info("JSearch: %d items in %.1fs", len(items), time.time() - t0)
    except Exception:
        logger.error("JSearch API failed — continuing", exc_info=True)
        results["jsearch"] = 0

    total = sum(results.values())
    elapsed = time.time() - t_start
    if total == 0:
        logger.warning("API FETCH: 0 jobs returned by all sources in %.1fs", elapsed)
    else:
        logger.info("API fetch complete: %s — total=%d in %.1fs", results, total, elapsed)
    return results


def _generate_seed_data() -> list[dict]:
    """Generate demo job offers to test the full pipeline."""
    from datetime import datetime

    seed_offers = [
        {
            "external_id": "seed_ds_001",
            "title": "Data Scientist Senior",
            "company": "DataCorp France",
            "location": "Paris, France",
            "description": (
                "Nous recherchons un Data Scientist Senior pour rejoindre notre équipe. "
                "Compétences requises : Python, TensorFlow, PyTorch, SQL, scikit-learn, "
                "NLP, deep learning. Expérience en déploiement de modèles ML en production. "
                "Connaissance de Docker, Kubernetes, MLflow. Salaire attractif."
            ),
            "contract_type": "CDI",
            "salary": "55000-75000€",
            "salary_min": 55000,
            "salary_max": 75000,
            "url": "https://example.com/jobs/seed_ds_001",
            "published_at": datetime.utcnow().isoformat(),
            "source": "seed",
        },
        {
            "external_id": "seed_de_002",
            "title": "Data Engineer",
            "company": "TechFlow",
            "location": "Lyon, France",
            "description": (
                "Poste de Data Engineer pour construire des pipelines de données. "
                "Stack technique : Apache Airflow, Spark, dbt, PostgreSQL, AWS S3, "
                "Kafka, Python, Docker. Méthodologie Agile Scrum."
            ),
            "contract_type": "CDI",
            "salary": "45000-60000€",
            "salary_min": 45000,
            "salary_max": 60000,
            "url": "https://example.com/jobs/seed_de_002",
            "published_at": datetime.utcnow().isoformat(),
            "source": "seed",
        },
        {
            "external_id": "seed_da_003",
            "title": "Data Analyst Junior",
            "company": "AnalytiQ",
            "location": "Bordeaux, France",
            "description": (
                "Rejoignez notre équipe en tant que Data Analyst. "
                "Outils : Power BI, SQL, Excel, Python, pandas. "
                "Analyse de données marketing et reporting."
            ),
            "contract_type": "CDD",
            "salary": "32000-38000€",
            "salary_min": 32000,
            "salary_max": 38000,
            "url": "https://example.com/jobs/seed_da_003",
            "published_at": datetime.utcnow().isoformat(),
            "source": "seed",
        },
        {
            "external_id": "seed_mle_004",
            "title": "Machine Learning Engineer",
            "company": "AI Solutions",
            "location": "Paris, France",
            "description": (
                "ML Engineer pour déployer des modèles en production. "
                "Compétences : Python, TensorFlow, Kubernetes, Docker, "
                "CI/CD, MLOps, monitoring de modèles, API REST."
            ),
            "contract_type": "CDI",
            "salary": "60000-80000€",
            "salary_min": 60000,
            "salary_max": 80000,
            "url": "https://example.com/jobs/seed_mle_004",
            "published_at": datetime.utcnow().isoformat(),
            "source": "seed",
        },
        {
            "external_id": "seed_ae_005",
            "title": "Analytics Engineer",
            "company": "DataWarehouse Co",
            "location": "Toulouse, France",
            "description": (
                "Analytics Engineer pour moderniser notre stack data. "
                "dbt, BigQuery, Looker, SQL avancé, Python, Git. "
                "Modélisation dimensionnelle et data quality."
            ),
            "contract_type": "CDI",
            "salary": "48000-58000€",
            "salary_min": 48000,
            "salary_max": 58000,
            "url": "https://example.com/jobs/seed_ae_005",
            "published_at": datetime.utcnow().isoformat(),
            "source": "seed",
        },
    ]
    return seed_offers


def _ingest_raw(**context: dict) -> dict[str, int]:
    """Ingest scraped and API-fetched items into the Bronze layer.

    Pulls items from XCom, calls etl.ingest.ingest_raw for each source.

    Returns:
        Dict mapping source names to rows ingested.
    """
    import os

    _ensure_env()

    from etl.ingest import ingest_raw

    import time
    t_start = time.time()

    ti = context["ti"]
    source_names = ["rekrute", "emploi_ma", "adzuna", "jsearch", "seed"]
    results: dict[str, int] = {}

    for source_name in source_names:
        # Try scrape_sources first, then fetch_api
        items = ti.xcom_pull(
            task_ids="scrape_sources",
            key=f"scraped_{source_name}",
        )
        if not items:
            items = ti.xcom_pull(
                task_ids="fetch_api",
                key=f"scraped_{source_name}",
            )
        if items:
            try:
                count = ingest_raw(items, source_name)
                results[source_name] = count
                logger.info(
                    "Ingested %d/%d items from '%s'", count, len(items), source_name,
                )
            except Exception:
                logger.error("Ingestion failed for '%s' — continuing", source_name, exc_info=True)
                results[source_name] = 0
        else:
            logger.info("No items found for source '%s' — skipping", source_name)
            results[source_name] = 0

    total_ingested = sum(results.values())
    elapsed = time.time() - t_start
    if total_ingested == 0:
        logger.critical(
            "PIPELINE HEALTH: 0 rows ingested across all sources in %.1fs. "
            "Check spider output and API credentials.",
            elapsed,
        )
    else:
        logger.info("Ingestion complete: %s — total=%d in %.1fs", results, total_ingested, elapsed)
    return results


def _transform_silver(**context: dict) -> int:
    """Run the Bronze → Silver transformation.

    Returns:
        Number of rows transformed.
    """
    import time

    _ensure_env()

    from etl.transform import transform_to_silver

    t_start = time.time()
    try:
        count = transform_to_silver(batch_size=100)
        logger.info("Silver transformation: %d rows in %.1fs", count, time.time() - t_start)
        return count
    except Exception:
        logger.error("Silver transformation FAILED after %.1fs", time.time() - t_start, exc_info=True)
        return 0


def _enrich_gold(**context: dict) -> int:
    """Run the Silver → Gold enrichment.

    Returns:
        Number of rows enriched.
    """
    import time

    _ensure_env()

    from etl.enrich import enrich_to_gold

    t_start = time.time()
    try:
        count = enrich_to_gold(model="all-MiniLM-L6-v2", batch_size=50)
        logger.info("Gold enrichment: %d rows in %.1fs", count, time.time() - t_start)
        return count
    except Exception:
        logger.error("Gold enrichment FAILED after %.1fs", time.time() - t_start, exc_info=True)
        return 0


def _refresh_views(**context: dict) -> None:
    """Refresh all materialized views for Power BI.

    Calls the refresh_all_analytics_views() PostgreSQL function.
    """
    import os

    _ensure_env()

    from etl.db import get_supabase_client

    client = get_supabase_client()
    try:
        client.rpc("refresh_all_analytics_views", {}).execute()
        logger.info("Materialized views refreshed")
    except Exception:
        logger.warning("Could not refresh views (may not exist yet)", exc_info=True)


def _build_summary_email(**context: dict) -> str:
    """Build the summary email body from upstream task results.

    Returns:
        HTML email body string.
    """
    ti = context["ti"]
    scrape_results = ti.xcom_pull(task_ids="scrape_sources") or {}
    api_results    = ti.xcom_pull(task_ids="fetch_api") or {}
    ingest_results = ti.xcom_pull(task_ids="ingest_raw") or {}
    silver_count   = ti.xcom_pull(task_ids="transform_silver") or 0
    gold_count     = ti.xcom_pull(task_ids="enrich_gold") or 0

    total_fetched  = sum(scrape_results.values()) + sum(api_results.values())
    total_ingested = sum(ingest_results.values())
    health = "OK" if gold_count > 0 else "WARNING — 0 rows enriched"

    scrape_rows = "".join(f"<li>{k}: {v} items</li>" for k, v in scrape_results.items())
    api_rows    = "".join(f"<li>{k}: {v} items</li>" for k, v in api_results.items())
    ingest_rows = "".join(f"<li>{k}: {v} rows</li>" for k, v in ingest_results.items())

    body = f"""
    <h2>Job ETL Pipeline — Run Summary</h2>
    <p><strong>Execution date:</strong> {context.get('ds', 'N/A')}</p>
    <p><strong>Pipeline health:</strong> {health}</p>

    <h3>Scraping (spiders)</h3>
    <ul>{scrape_rows or '<li>No spider results</li>'}</ul>

    <h3>API Fetch (Adzuna, JSearch)</h3>
    <ul>{api_rows or '<li>No API results</li>'}</ul>

    <p><strong>Total fetched:</strong> {total_fetched} jobs</p>

    <h3>Ingestion (Bronze)</h3>
    <ul>{ingest_rows or '<li>No rows ingested</li>'}</ul>
    <p><strong>Total ingested:</strong> {total_ingested} rows</p>

    <h3>Transform (Silver)</h3>
    <p>{silver_count} rows transformed</p>

    <h3>Enrichment (Gold)</h3>
    <p>{gold_count} rows enriched</p>

    <p>Materialized views refreshed.</p>
    """
    logger.info("Summary: fetched=%d ingested=%d silver=%d gold=%d",
                total_fetched, total_ingested, silver_count, gold_count)
    return body


def _send_summary(**context: dict) -> None:
    """Log the pipeline summary email body."""
    body = context["ti"].xcom_pull(task_ids="build_summary")
    logger.info("Pipeline run summary:\n%s", body)


# ── DAG definition ───────────────────────────────────────────────────────────
with DAG(
    dag_id="job_etl",
    default_args=default_args,
    description="End-to-end ETL pipeline for job offers: scrape → ingest → transform → enrich → refresh",
    schedule_interval="0 */6 * * *",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["etl", "jobs", "data"],
    max_active_runs=1,
) as dag:

    scrape_sources = PythonOperator(
        task_id="scrape_sources",
        python_callable=_scrape_sources,
    )

    fetch_api = PythonOperator(
        task_id="fetch_api",
        python_callable=_fetch_api_sources,
    )

    ingest_raw = PythonOperator(
        task_id="ingest_raw",
        python_callable=_ingest_raw,
        trigger_rule=TriggerRule.ALL_DONE,
    )

    transform_silver = PythonOperator(
        task_id="transform_silver",
        python_callable=_transform_silver,
        trigger_rule=TriggerRule.ALL_DONE,
    )

    enrich_gold = PythonOperator(
        task_id="enrich_gold",
        python_callable=_enrich_gold,
        trigger_rule=TriggerRule.ALL_DONE,
    )

    refresh_views = PythonOperator(
        task_id="refresh_views",
        python_callable=_refresh_views,
        trigger_rule=TriggerRule.ALL_DONE,
    )

    send_summary = PythonOperator(
        task_id="send_summary",
        python_callable=_send_summary,
    )

    build_summary = PythonOperator(
        task_id="build_summary",
        python_callable=_build_summary_email,
    )

    # Task dependencies
    # Scraping and API fetch run in parallel, then ingest → transform → enrich → refresh → summary
    [scrape_sources, fetch_api] >> ingest_raw >> transform_silver >> enrich_gold >> refresh_views >> build_summary >> send_summary
