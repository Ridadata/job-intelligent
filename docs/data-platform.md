# Data Platform

## Overview

The data platform is a 3-layer medallion pipeline orchestrated by Apache Airflow.
All job data flows through **Bronze → Silver → Gold** before being served by the API.

---

## Pipeline Flow

```
Job APIs                 Scrapy Spiders
Adzuna                   Rekrute.com
JSearch         ──┐      Emploi.ma      ──┐
France Travail    │      WelcomeToTheJungle│
                  │                        │
                  └──── normalize to JobItem ────┐
                                                 │
                                                 ▼
                                       ┌─────────────────┐
                                       │  BRONZE LAYER   │
                                       │ raw_job_offers  │
                                       │ immutable JSON  │
                                       └────────┬────────┘
                                                │ Stage 2: Transform
                                                ▼
                                       ┌─────────────────┐
                                       │  SILVER LAYER   │
                                       │  job_offers     │
                                       │  validated      │
                                       │  normalized     │
                                       │  deduplicated   │
                                       └────────┬────────┘
                                                │ Stage 3: Enrich
                                                ▼
                                       ┌─────────────────┐
                                       │   GOLD LAYER    │
                                       │ dw_job_offers   │
                                       │ + embedding     │
                                       │   vector(384)   │
                                       │ + demand_score  │
                                       └─────────────────┘
```

---

## Layer Details

### Bronze — `raw_job_offers`

**Purpose:** Immutable landing zone. Never modified after insert.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID | PK |
| `source_id` | UUID | FK → sources |
| `external_id` | TEXT | Dedup key per source (required) |
| `raw_json` | JSONB | Full original payload |
| `scraped_at` | TIMESTAMPTZ | Ingestion timestamp |
| `processed` | BOOLEAN | False until Silver picks it up |

**Rules:**
- All sources insert here before any transformation
- If a job is re-ingested, `processed` resets to `false` so it re-flows
- `external_id` is mandatory — it's the per-source dedup key

---

### Silver — `job_offers`

**Purpose:** Clean, validated, normalized records ready for the API.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID | PK |
| `source_id` | UUID | FK → sources |
| `raw_offer_id` | UUID | FK → raw_job_offers |
| `title` | TEXT | Normalized title |
| `company` | TEXT | |
| `location` | TEXT | |
| `contract_type` | TEXT | CDI · CDD · Freelance · Stage · Alternance · Autre |
| `salary_min/max` | FLOAT | |
| `required_skills` | TEXT[] | Extracted by spaCy NER |
| `description` | TEXT | |
| `published_at` | TIMESTAMPTZ | |

**Transformations applied:**
1. **Schema validation** — Pydantic model rejects malformed rows (missing title, invalid dates)
2. **Skill extraction** — spaCy `fr_core_news_md` NER + pattern matching on job description
3. **Skill normalization** — 100+ canonical aliases (`"tf"` → `"tensorflow"`, `"sklearn"` → `"scikit-learn"`)
4. **Deduplication** — Jaccard similarity on title + company across sources (threshold: 0.85)
5. **Taxonomy classification** — Rule-based classifier assigns one of 8 categories:
   - `data_engineering` · `data_science` · `machine_learning` · `analytics` · `cloud`
   - `devops` · `software_engineering` · `other`
6. **Data quality checks** — 6 post-transform checks (NULL rates, skill array length, etc.)

---

### Gold — `dw_job_offers`

**Purpose:** AI-enriched records for vector search and analytics.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID | PK |
| `offer_id` | UUID | FK → job_offers (unique) |
| `embedding` | VECTOR(384) | Sentence-BERT embedding |
| `normalized_title` | TEXT | |
| `seniority_level` | TEXT | Junior · Mid · Senior |
| `tech_stack` | TEXT[] | NLP-extracted skill list |
| `demand_score` | FLOAT | Frequency-weighted skill demand |
| `category` | TEXT | Taxonomy category |
| `contract_type_standardized` | TEXT | |
| `dedup_key` | TEXT | Cross-source fingerprint |

**Enrichment applied:**
1. **Embedding generation** — Input text: `"{title}. {description}. Skills: {tech_stack_joined}"`
2. **Model** — `all-MiniLM-L6-v2` (384 dimensions, Sentence-BERT)
3. **HNSW index** — pgvector HNSW index on `embedding` column for sub-second ANN search
4. **Demand scoring** — Each skill gets a score based on frequency across the Gold table

---

## Airflow DAG — `job_etl`

**Schedule:** Every 6 hours (`0 */6 * * *`)
**Config:** `catchup=False`, `max_active_runs=1`

```
ingest_apis
    │
    ├── adzuna_ingest
    ├── jsearch_ingest
    └── france_travail_ingest
          │
          ▼
ingest_scrapers
    │
    ├── rekrute_spider
    ├── emploi_ma_spider
    └── wttj_spider
          │
          ▼
transform_silver       (Bronze → Silver for all unprocessed rows)
          │
          ▼
enrich_gold            (Silver → Gold: embeddings + demand scores)
          │
          ▼
refresh_views          (Refresh materialized views for analytics)
          │
          ▼
quality_summary        (Log pass/fail counts to pipeline_runs)
```

---

## ETL Observability — `pipeline_runs`

Every stage writes one row to `pipeline_runs`:

| Column | Description |
|---|---|
| `pipeline_name` | DAG name |
| `stage` | `ingest` · `transform` · `enrich` · `refresh` |
| `status` | `running` · `success` · `failed` · `partial` |
| `rows_in` | Input row count |
| `rows_out` | Output row count |
| `rows_skipped` | Rejected by validation |
| `rows_error` | Failed during processing |
| `duration_ms` | Wall-clock time for the stage |
| `error_message` | First error encountered (if any) |
| `source_name` | API or spider name |

---

## Analytics Views — `sql/003_materialized_views.sql`

Five materialized views power the Power BI / admin dashboard:

| View | What it shows |
|---|---|
| `mv_offers_by_skill` | Job count per skill (top skills in demand) |
| `mv_salary_by_role` | Salary range per normalized title |
| `mv_offers_by_location` | Job count per city/region |
| `mv_market_trends` | Job volume over time |
| `mv_top_companies` | Most active hiring companies |

Refreshed at end of each ETL run via `refresh_all_analytics_views()`.

---

## Data Sources

| Source | Type | Coverage | Priority |
|---|---|---|---|
| Adzuna API | API | International | Primary |
| JSearch (RapidAPI) | API | Aggregator | Primary |
| France Travail | API | France (official) | Primary |
| Rekrute.com | Scraper | Morocco | Fallback |
| Emploi.ma | Scraper | Morocco / Africa | Fallback |
| WelcomeToTheJungle | Scraper | France / Europe | Fallback |

**Rule:** API clients run first. Scrapers fill gaps for sources without a stable API.
All sources normalize to `JobItem` before touching the database.
