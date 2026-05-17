# Job Intelligent - End-to-End Platform Dossier (Professor Presentation)

## 1) Executive Summary

Job Intelligent is an AI-powered platform that centralizes data/AI job offers, transforms them through a medallion pipeline (Bronze -> Silver -> Gold), and matches those jobs to candidate profiles using embeddings + multi-signal scoring.

The project is implemented as a modular monolith (not microservices) with:
- Frontend: React + TypeScript + Vite
- Backend: FastAPI + Supabase client
- Data Platform: Airflow + ETL modules + Scrapy + API clients
- AI: Sentence-BERT embeddings + NLP + explainable scoring
- Storage: Supabase PostgreSQL + pgvector (application DB), local Postgres (Airflow metadata DB)
- Cache: Redis (cache only)

The stack is runnable end-to-end locally with Docker Compose for backend services and Vite for frontend.

---

## 2) Product Goal and Value Proposition

### Core product objective
- Aggregate fragmented job opportunities in data/AI.
- Normalize and enrich raw job data into searchable intelligence.
- Match candidates to jobs with transparent explainability (matched skills, missing skills, score breakdown).

### Main user value
- Less manual job search effort.
- Better fit quality through semantic matching.
- Skill-gap visibility for career planning.

---

## 3) End-to-End Architecture

```
[Job APIs + Scrapers]
        |
        v
[Bronze: raw_job_offers]
        |
        v
[Silver: job_offers]
        |
        v
[Gold: dw_job_offers + vector(384)]
        |
        v
[FastAPI: routers -> services -> repositories]
        |
        v
[React SPA: pages + hooks + stores]
```

### Architectural style
- Modular monolith with strict layering.
- Backend pattern: routers -> services -> repositories -> Supabase.
- Data pattern: Bronze -> Silver -> Gold.
- AI modules imported directly as Python libraries (no separate AI microservice).

---

## 4) Infrastructure Topology

## Runtime components
- fastapi container on port 8000
- redis container on port 6379
- airflow-webserver container on port 8080
- airflow-scheduler container
- airflow-init one-shot setup container
- airflow-db local Postgres container on port 5433
- frontend Vite dev server on host port 3000

### Important distinction: 2 PostgreSQL roles
- Supabase PostgreSQL (cloud): application database (jobs, users, candidates, embeddings, history).
- Local Postgres in Compose (airflow-db): Airflow metadata only (DAG runs, task state).

### Docker files
- Dockerfile: FastAPI runtime + dependencies + spaCy model download.
- Dockerfile.airflow: Airflow runtime + ETL dependencies + spaCy model.

---

## 5) Backend (FastAPI) - Technical Breakdown

## Entry point and middleware
- Main app: api/main.py
- CORS middleware with env-driven origins.
- Request ID middleware.
- Redis-backed rate limiting middleware.
- AppError global handler + fallback 500 handler.

### Dependency injection and auth
- Dependencies in api/dependencies.py.
- Supabase client singleton.
- JWT decode first, fallback to Supabase auth token validation.
- Role guard via require_role(...).

### Core routers
- /health and /readiness
- /api/v1/auth
- /api/v1/jobs
- /api/v1/candidates
- /api/v1/recommendations
- /api/v1/search
- /api/v1/admin

### Layer responsibilities
- Routers: HTTP contracts and dependency wiring.
- Services: business logic only.
- Repositories: table-level data access wrappers.

---

## 6) Frontend (React + TypeScript) - Technical Breakdown

## Tech and architecture
- React 18, TypeScript, Vite, TanStack Query, Zustand, Tailwind.
- Route composition in frontend/src/App.tsx.
- ProtectedRoute and AdminRoute gate protected areas.

### Main pages
- Landing, Login, Register
- Dashboard
- JobSearch, JobDetail
- Recommendations
- SkillGap
- Profile
- SavedJobs
- AdminDashboard, PipelineStatus, UserManagement

### State management
- Server state: TanStack Query.
- Client state: Zustand stores (auth, theme, filters).

### API integration
- Centralized API client in frontend/src/services/api-client.ts.
- Uses VITE_API_BASE_URL (default http://localhost:8000/api/v1).
- Vite proxy forwards /api to http://localhost:8000.

### Frontend runtime
- Dev server configured to port 3000 in vite.config.ts.

---

## 7) Data Platform and ETL

## Ingestion sources
### API clients implemented
- Adzuna client (ingestion/api_clients/adzuna_client.py)
- JSearch client (ingestion/api_clients/jsearch_client.py)
- France Travail client exists (ingestion/api_clients/france_travail_client.py)

### Scrapers implemented
- Rekrute spider
- Emploi.ma spider

## ETL layers
### Bronze (raw_job_offers)
- Immutable raw JSON payloads.
- Dedup key per source: (source_id, external_id).
- processed flag controls incremental flow.

### Silver (job_offers)
- Schema validation.
- Data-domain filtering (data/AI keywords).
- Contract normalization.
- Skill extraction + canonical normalization.
- Salary parsing and field normalization.

### Gold (dw_job_offers)
- Embedding generation (vector 384).
- Taxonomy category assignment.
- Seniority normalization.
- Demand score calculation.
- Dedup key and contract standardization.

## Orchestration with Airflow
- DAG: job_etl
- Schedule: every 6 hours (0 */6 * * *)
- catchup=False, max_active_runs=1
- Parallel fetch stage: scrape_sources + fetch_api
- Sequence: ingest_raw -> transform_silver -> dedup_cross_source -> enrich_gold -> refresh_views -> summary
- Parallel side path: process_pending_cvs after transform

## Pipeline observability
- pipeline_runs table with stage/status/rows_in/rows_out/rows_skipped/rows_error/duration_ms/error_message.
- Track context manager in etl/monitoring.py.

---

## 8) AI System (Embeddings + Matching + Explainability)

## Embedding model
- Sentence-BERT all-MiniLM-L6-v2
- 384-dimensional vectors
- Batch embedding support implemented

### Embedding usage
- Job embeddings stored in dw_job_offers.embedding
- Candidate embeddings stored in candidate_profiles.embedding

## Recommendation scoring model
Composite score:
- 0.5 * skill overlap
- 0.3 * embedding similarity
- 0.1 * seniority alignment
- 0.1 * location preference

### Explainability output
For each recommendation:
- matched_skills
- missing_skills
- score_breakdown
- explanation_text

## Skill gap analysis
- Candidate skills are compared against similar jobs.
- Missing skills are ranked by frequency and improvement potential.

## Semantic search
- Query text embedded.
- Similarity search through SQL function semantic_search_jobs.

---

## 9) Database Model (Supabase PostgreSQL + pgvector)

## Main application entities
- sources
- raw_job_offers
- job_offers
- dw_job_offers
- users
- candidate_profiles
- cv_documents
- saved_jobs
- applications
- pipeline_runs
- recommendation_history

## Vector search functions
- match_job_offers(query_embedding, ...)
- semantic_search_jobs(query_embedding, ...)
- match_jobs_for_candidate(...)
- match_candidates_for_job(...)

## Analytics materialized views
- mv_offers_by_skill
- mv_salary_by_role
- mv_offers_by_location
- mv_market_trends
- mv_top_companies

## Refresh function
- refresh_all_analytics_views()

---

## 10) Candidate Lifecycle (End-to-End)

## Profile flow
1. User registers and logs in.
2. Candidate creates profile at /api/v1/candidates/profile.
3. Profile completeness is computed.
4. Candidate embedding is generated and stored.

## CV enrichment flow
1. Candidate uploads PDF/DOCX CV.
2. File saved under cv_uploads/.
3. CV document row created with parsing_status=pending.
4. Background parser extracts text + skills + experience + education.
5. Profile is enriched (union skills, max experience, fill education if empty).
6. Candidate embedding regenerated after enrichment.

---

## 11) Job Lifecycle (End-to-End)

1. Jobs fetched by APIs/scrapers.
2. Ingested into Bronze raw_job_offers.
3. Transformed to Silver job_offers.
4. Enriched to Gold dw_job_offers with embedding/category/seniority.
5. Exposed via FastAPI endpoints for listing/search/recommendations.
6. Surfaced in frontend pages and can be saved by candidates.

---

## 12) API Surface (Presentation-Friendly)

## Auth
- POST /api/v1/auth/register
- POST /api/v1/auth/login
- GET /api/v1/auth/me

## Jobs
- GET /api/v1/jobs
- GET /api/v1/jobs/{id}
- POST /api/v1/jobs/{id}/save
- DELETE /api/v1/jobs/{id}/save

## Candidates
- GET /api/v1/candidates/profile
- POST /api/v1/candidates/profile
- PUT /api/v1/candidates/profile
- POST /api/v1/candidates/cv
- GET /api/v1/candidates/saved-jobs

## AI endpoints
- POST /api/v1/recommendations
- GET /api/v1/candidates/{id}/skill-gap
- GET /api/v1/search

## Admin endpoints
- GET /api/v1/admin/pipeline-runs
- GET /api/v1/admin/users
- GET /api/v1/admin/stats

## System
- GET /health
- GET /readiness

---

## 13) Redis Role

Redis is used as cache-only (rebuildable from DB):
- Recommendation response cache (default 1 hour)
- Semantic search cache (5 minutes)
- Skill gap cache (30 minutes)
- Rate limiter sliding window storage

No permanent business state is stored in Redis.

---

## 14) Security Model

- JWT auth (HS256) using python-jose.
- Password hashing using passlib bcrypt.
- Role-based access for admin routes.
- RLS policies enabled in Supabase SQL migrations.
- Standardized API error shape: { detail, code }.
- Request tracing via X-Request-ID.
- Per-IP rate limiting via Redis middleware.

---

## 15) Power BI and Analytics Layer

Power BI artifacts are documented in powerbi/ with:
- dashboard_specs.md
- dax_measures.md
- connection_guide.md
- export_to_csv.py helper script

Analytics are powered by materialized views refreshed after ETL.

---

## 16) Verified Runtime Status (Session Snapshot)

Validated during this session:
- Frontend responds on http://localhost:3000 (HTTP 200).
- Backend health endpoint responds on http://localhost:8000/health (HTTP 200).
- Airflow health endpoint responds on http://localhost:8080/health (HTTP 200).
- Redis and airflow-db are healthy in docker compose ps.

Observed caveat:
- fastapi container may show unhealthy because Docker healthcheck uses curl, which is not present in the image, while the app itself is reachable and healthy.

---

## 17) Testing and Quality Snapshot

## Automated tests present
- API client tests
- ETL tests
- NLP tests
- Embedding tests
- Recommendation tests
- Pipeline integration tests
- Data coherence tests
- Phase 3 tests

## Executed in this session
- docker compose exec fastapi python -m pytest tests/test_recommendations.py -q
- Result: 6 passed, 3 warnings.

Warnings were deprecation-related (Pydantic config style, gotrue package, crypt deprecation).

---

## 18) Important Gaps / Risks Identified

These are useful to show transparency in your presentation:

1. Frontend build currently fails (TypeScript)
- Missing Activity import in admin PipelineStatus page.
- Framer Motion typing issue in Landing variants (ease typed as generic string).
- One unused import in Profile page.

2. Source coverage mismatch
- France Travail client exists, but current Airflow API fetch task only calls Adzuna and JSearch.
- WTTJ is referenced in docs, but no WTTJ spider file is currently present.

3. Documentation drift
- Some docs still mention VITE_API_URL, while actual code uses VITE_API_BASE_URL.
- README mentions frontend on 5173 in some sections, but vite.config.ts sets 3000.

4. SQL migration complexity
- Early and later migrations overlap (pipeline_runs/candidate model evolution).
- sql/008_schema_fixes.sql is essential to reconcile schema differences.

5. Legacy export script tables
- powerbi/export_to_csv.py exports legacy candidates/recommendations tables that may not reflect the latest candidate_profiles/recommendation_history model.

---

## 19) Suggested Professor Demo Flow (10-12 minutes)

1. Problem and value (1 min)
- Explain market pain: fragmented job discovery and low match transparency.

2. Architecture overview (2 min)
- Show modular monolith with data -> AI -> API -> UI pipeline.

3. Data pipeline demo (2 min)
- Show Airflow DAG and pipeline runs.
- Explain Bronze/Silver/Gold transformation logic.

4. Candidate intelligence demo (2 min)
- Show profile creation + CV enrichment concept.
- Explain embedding update lifecycle.

5. Recommendation and explainability demo (2 min)
- Show recommendation cards with matched/missing skills and score breakdown.

6. BI and analytics demo (1-2 min)
- Show Power BI view specs and refreshed market indicators.

7. Honest engineering review (1 min)
- Present current gaps (frontend build issues, source coverage gaps) and next actions.

---

## 20) Next Iteration Priorities

Priority 1
- Fix frontend TypeScript build errors.

Priority 2
- Add France Travail call into Airflow fetch_api task.

Priority 3
- Add WTTJ spider or remove from docs until implemented.

Priority 4
- Align env var names and port docs to code reality.

Priority 5
- Update Power BI export script to use candidate_profiles and recommendation_history.

---

## 21) One-Slide Summary (ready to copy)

Job Intelligent delivers an end-to-end AI recruitment intelligence platform:
- Multi-source ingestion (APIs + scraping)
- Medallion ETL (Bronze/Silver/Gold)
- Vector search and explainable recommendation scoring
- Candidate profile + CV enrichment lifecycle
- FastAPI backend + React frontend
- Supabase PostgreSQL + pgvector + Redis + Airflow

Current status: core architecture is operational and demonstrable, with a clear shortlist of engineering fixes to reach production-grade polish.
