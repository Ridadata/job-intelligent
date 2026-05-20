# Getting Started

This guide walks you through running Job Intelligent locally end-to-end.

## Prerequisites

| Tool | Version | Notes |
|---|---|---|
| Docker Desktop | 24+ with Compose v2 | Required |
| Git | 2.40+ | Required |
| Node.js | 20+ | Optional — only for frontend dev outside Docker |
| Python | 3.11+ | Optional — only for local tooling |

A free [Supabase](https://supabase.com) account is recommended for the managed Postgres path. The repo also supports a fully local Postgres container via the included `app-db` service.

## 1. Clone and Configure

```bash
git clone https://github.com/Ridadata/job-intelligent.git
cd job-intelligent
cp .env.example .env
```

Open `.env` and fill in at minimum:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key
SERVICE_ROLE_KEY=your-service-role-key
JWT_SECRET_KEY=<generate a 64+ char random string>
POSTGRES_PASSWORD=<your local postgres password>
AIRFLOW_FERNET_KEY=<generate via: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())">
AIRFLOW_WEBSERVER_SECRET_KEY=<long random string>
POWERBI_READER_PASSWORD=<long random string>
```

Optional (enables real ingestion — without these, the app runs on seed data):

```env
ADZUNA_APP_ID=...
ADZUNA_APP_KEY=...
JSEARCH_API_KEY=...
FRANCE_TRAVAIL_CLIENT_ID=...
FRANCE_TRAVAIL_CLIENT_SECRET=...
```

## 2. Start the Stack

```bash
docker compose up -d
```

This starts:

| Service | Port | URL |
|---|---|---|
| FastAPI backend | 8000 | http://localhost:8000/docs |
| React frontend | 3000 | http://localhost:3000 |
| Airflow UI | 8080 | http://localhost:8080 (admin / admin) |
| Local Postgres | 54320 | (psql / Power BI) |
| Supabase Studio | 54323 | http://localhost:54323 |
| Redis | 6379 | (internal) |
| Adminer | 8081 | http://localhost:8081 |

Verify all containers are healthy:

```bash
docker compose ps
```

## 3. Apply Database Migrations

Run these SQL files in order against your Supabase project (SQL Editor) **or** the local container:

```
sql/001_schema.sql
sql/002_functions.sql
sql/003_materialized_views.sql
sql/004_candidate_and_product.sql
sql/005_candidate_functions.sql
sql/006_pipeline_monitoring.sql
sql/007_recommendation_history.sql
sql/008_schema_fixes.sql
```

For local container, you can apply them via Adminer (http://localhost:8081) or directly:

```bash
docker compose exec app-db psql -U postgres -d job_intelligent -f /sql/001_schema.sql
```

## 4. Trigger ETL

1. Open Airflow at http://localhost:8080 (admin / admin).
2. Enable the `job_etl` DAG.
3. Click "Trigger DAG".
4. Monitor task progress in the Graph view.

The pipeline runs: `ingest_apis → ingest_scrapers → transform_silver → enrich_gold → refresh_views → summary`.

## 5. Use the App

- **Frontend**: http://localhost:3000 — register a candidate, fill the profile, browse jobs, view recommendations.
- **Swagger UI**: http://localhost:8000/docs — interactive API explorer.
- **Power BI**: connect to `localhost:54320` (see [powerbi/local_connection_guide.md](../powerbi/local_connection_guide.md)).

## 6. Run Tests

```bash
docker compose exec fastapi python -m pytest tests/ -v
```

For frontend tests:

```bash
cd frontend && npm test
```

## Troubleshooting

### Containers fail to start

```bash
docker compose logs <service-name>
```

Common causes: missing required `.env` variables, port conflicts (8000/8080/3000/54320), Docker memory limit too low.

### Power BI cannot connect to Supabase pooler

The Supabase Supavisor pooler is not compatible with Npgsql (Power BI's driver). Use the **direct local container port `54320`** instead. See [powerbi/local_connection_guide.md](../powerbi/local_connection_guide.md).

### Airflow DAG import errors

Ensure `AIRFLOW_FERNET_KEY` and `AIRFLOW_WEBSERVER_SECRET_KEY` are set in `.env`. Restart the Airflow services:

```bash
docker compose restart airflow-webserver airflow-scheduler
```

### Embeddings missing on jobs

Re-run the `enrich_gold` task in Airflow, or trigger a full `job_etl` DAG run.

## Next Steps

- Read [ARCHITECTURE.md](ARCHITECTURE.md) to understand the system layout.
- Read [API.md](API.md) for endpoint reference.
- Read [data-platform.md](data-platform.md) to understand the ETL pipeline.
- Read [ai-system.md](ai-system.md) for matching engine internals.
