# RADIAN — Project Backlog & Status Report
**As of April 27, 2026 · Branch: `feature/amine-dev` · Repo: Ridadata/job-intelligent**

---

## Table of Contents
1. [Project Overview](#1-project-overview)
2. [Timeline & Milestones](#2-timeline--milestones)
3. [Architecture Analysis](#3-architecture-analysis)
4. [Completed Work — Full Audit](#4-completed-work--full-audit)
5. [In-Progress Work](#5-in-progress-work)
6. [Backlog — Tasks To Do](#6-backlog--tasks-to-do)
7. [PowerBI Dashboard Backlog](#7-powerbi-dashboard-backlog)
8. [Technical Debt & Risks](#8-technical-debt--risks)
9. [Team Contributions](#9-team-contributions)
10. [Definition of Done](#10-definition-of-done)

---

## 1. Project Overview

| Field | Value |
|---|---|
| **Product** | RADIAN — AI-Powered Job Intelligence Platform |
| **Goal** | Centralize data-domain job offers and deliver AI-driven job-to-candidate matching |
| **Stack** | FastAPI · React/TypeScript · Supabase (PG 15 + pgvector) · Redis · Scrapy · Airflow · spaCy · Sentence-BERT |
| **Architecture** | Modular monolith. Medallion data pattern (Bronze → Silver → Gold). |
| **Data sources live** | Adzuna API, JSearch (RapidAPI), France Travail API, Rekrute.ma spider, Emploi.ma spider |
| **Target users** | Data professionals (engineers, scientists, analysts, ML engineers) in France + Morocco |
| **Current completion** | **~88% of core platform** |
| **Sprint cadence** | 1-week sprints (informal, solo + 1 contributor) |
| **Deployment** | Docker Compose (local & production ready) |

---

## 2. Timeline & Milestones

> Reconstructed from git history, code evolution (SQL migration numbering), and module complexity.

```
MARCH 2026
├── Week 1 (Mar 1–7)    ── Project bootstrap, Docker Compose, Supabase schema (001_schema.sql)
├── Week 2 (Mar 8–14)   ── Backend scaffolding: FastAPI app, routers, Pydantic models, JWT auth
├── Week 3 (Mar 15–21)  ── ETL pipeline: ingestion layer, Adzuna + JSearch API clients
│                           France Travail API client, Bronze ingest logic
├── Week 4 (Mar 22–31)  ── Silver transform, Scrapy spiders (Rekrute, Emploi.ma)
│                           SQL migrations 002–004 (functions, materialized views, candidate schema)

APRIL 2026
├── Week 1 (Apr 1–7)    ── AI services: embedding generator (MiniLM-L6-v2), matching scorer
│                           explainer, skill gap, spaCy NLP pipeline
│                           SQL migrations 005–006 (candidate functions, pipeline monitoring)
├── Week 2 (Apr 8–14)   ── CV parser (PDF + DOCX), candidate enrichment pipeline
│                           Recommendation service + Redis caching
│                           SQL migrations 007–008 (Gold schema, recommendation history, fixes)
│                           Frontend: React project setup, Vite, Tailwind, Shadcn UI
│                           Authentication pages (Login, Register) + Zustand auth store
├── Week 3 (Apr 15–21)  ── Frontend: Dashboard, Job Search, Job Detail, Recommendations
│                           Profile page (with CV upload), Saved Jobs, Skill Gap
│                           ProtectedRoute + AdminRoute guards
│                           Admin panel: AdminDashboard, PipelineStatus, UserManagement
│                           PowerBI: export_to_csv.py, materialized view exports (11 CSVs)
│                           PowerBI Page 1 — Market Overview (IN PROGRESS → ACTIVE)
├── Week 4 (Apr 22–27)  ── PowerBI Pages 2–4 design & build (ACTIVE NOW)
│                           Test suite: 8 modules, 6 passing fully, 2 in progress
│                           Progress report HTML (docs/progress-report.html)
│                           Project documentation (ARCHITECTURE.md, backend.md, frontend.md)

NEXT — May 2026
└── May Week 1+         ── Production deployment, WelcomeToTheJungle spider, email alerts,
                            feedback loop, performance tuning, test coverage to 90%+
```

---

## 3. Architecture Analysis

### 3.1 Strengths ✅

| Layer | Assessment |
|---|---|
| **Backend** | Clean 4-layer separation (router → service → repository → DB). No business logic leaks into routers. All HTTP concerns isolated. |
| **ETL Pipeline** | Medallion pattern is correctly implemented. Bronze rows are immutable. Incremental processing via `processed` flag works. |
| **AI Services** | Fully decoupled module. No FastAPI imports. Batch-only embedding, fuzzy skill matching with version stripping, weighted scorer with full explainer. |
| **Frontend** | Strict separation of concerns: TanStack Query for server state, Zustand for client state, centralized API client with token injection. No raw fetch calls in components. |
| **Security** | JWT + bcrypt + RLS + rate limiting + CORS allowlist + pydantic-settings — all 6 OWASP-aligned controls present. |
| **Database** | pgvector HNSW index on `vector(384)`. GIN index on `required_skills`. RLS on all tables. 9 SQL migrations with clean numbering. |

### 3.2 Architecture Gaps / Risks ⚠️

| Gap | Impact | Priority |
|---|---|---|
| No token refresh endpoint | Users are silently logged out after 60 min — bad UX | HIGH |
| CV file storage is local disk (`cv_uploads/`) | Not portable across Docker restarts; should be object storage (Supabase Storage or S3) | HIGH |
| `auth.store.ts` hydrate only reads token from localStorage, doesn't validate it with `/auth/me` | Stale/invalid tokens pass the `isAuthenticated` check | MEDIUM |
| Admin PipelineStatus page has no real API connection yet | Admin panel is structurally present but reads no live data | MEDIUM |
| WelcomeToTheJungle spider not implemented | Only 2 of 3 planned scrapy spiders exist | LOW |
| No test for auth routes | Auth flows (register, login, JWT decode) have no automated tests | MEDIUM |
| Airflow runs locally only | No staging/prod Airflow environment documented | LOW |
| PowerBI connected via CSV exports, not live DB | Data in PowerBI is as fresh as the last `export_to_csv.py` run | MEDIUM |

### 3.3 Data Flow

```
[Adzuna API]  [JSearch API]  [France Travail API]     [Rekrute spider]  [Emploi.ma spider]
      └──────────────────────────────┬───────────────────────────┘
                               JobItem schema
                                     │
                              [Bronze Layer]
                           raw_job_offers (JSONB)
                                     │ processed=False → True
                              [Silver Layer]
                         job_offers (Pydantic validated)
                                     │ Airflow every 6h
                               [Gold Layer]
                     dw_job_offers + vector(384) HNSW index
                                     │
              ┌──────────────────────┤
              │                      │
        [FastAPI REST]        [Materialized Views]
              │                      │
     [React SPA]              [PowerBI CSVs]
              │
    [Candidate] ←→ [CV Parser] ←→ [Embeddings] ←→ [Matcher/Recommender]
```

---

## 4. Completed Work — Full Audit

### 4.1 Infrastructure & DevOps ✅ DONE

- [x] `docker-compose.yml` — orchestrates API, frontend, Airflow, Redis, Nginx
- [x] `Dockerfile` — FastAPI production container
- [x] `Dockerfile.airflow` — Airflow container with ETL dependencies
- [x] `pyproject.toml` — Python project config, Ruff linting, dependency groups
- [x] `requirements.txt` — pinned production dependencies
- [x] Environment variable architecture via pydantic-settings (`api/core/config.py`)
- [x] Request ID middleware for distributed tracing (`api/middleware/request_id.py`)
- [x] Error handler middleware with global exception registration (`api/middleware/error_handler.py`)
- [x] Rate limit middleware via SlowAPI (`api/middleware/rate_limit.py`)

---

### 4.2 Database & SQL ✅ DONE

| Migration | Content | Status |
|---|---|---|
| `001_schema.sql` | Core tables: `sources`, `raw_job_offers`, `job_offers`, `users`, `saved_jobs`, `applications` | ✅ Done |
| `002_functions.sql` | PostgreSQL helper functions, triggers | ✅ Done |
| `003_materialized_views.sql` | `mv_market_trends`, `mv_offers_by_skill`, `mv_offers_by_location`, `mv_salary_by_role`, `mv_top_companies` | ✅ Done |
| `004_candidate_and_product.sql` | `candidate_profiles`, `cv_documents`, `pipeline_runs` | ✅ Done |
| `005_candidate_functions.sql` | `get_candidate_skills()`, candidate-related DB functions | ✅ Done |
| `006_pipeline_monitoring.sql` | `pipeline_runs` extended columns, monitoring indices | ✅ Done |
| `007_gold_schema_update.sql` | `dw_job_offers` with `embedding vector(384)`, HNSW index | ✅ Done |
| `007_recommendation_history.sql` | `recommendation_history` with score breakdown JSONB | ✅ Done |
| `008_schema_fixes.sql` | RLS policies, `updated_at` triggers, `semantic_search_jobs()` function, idempotent fixes | ✅ Done |

**Total tables:** 14+  
**Vector index:** HNSW `m=16, ef_construction=64` on `dw_job_offers.embedding`  
**GIN index:** `required_skills` array on `job_offers`

---

### 4.3 Backend API ✅ DONE (95%)

#### Routers implemented
| Router | Endpoints | Key Features |
|---|---|---|
| `auth.py` | `POST /register`, `POST /login`, `GET /me` | JWT HS256, bcrypt 12-round hashing, `get_current_user` dependency |
| `jobs.py` | `GET /jobs`, `GET /jobs/{id}`, `POST /jobs/{id}/save`, `DELETE /jobs/{id}/save` | Pagination, filters, bookmark toggle |
| `candidates.py` | `GET /profile`, `POST /profile`, `PUT /profile`, `POST /cv` | CV upload with background parse task, profile CRUD |
| `recommendations.py` | `GET /candidates/{id}/recommendations` | Multi-signal scorer, Redis cache-first, explainer output |
| `search.py` | `GET /search?q=...` | pgvector semantic search via `semantic_search_jobs()` SQL function |
| `admin.py` | Admin-only routes | `require_role("admin")` dependency guard |
| `health.py` | `GET /health` | Supabase + Redis connectivity check |

#### Services implemented
| Service | Responsibility |
|---|---|
| `auth_service.py` | Register, login, token decode, password hash/verify |
| `job_service.py` | Job listing with filters, pagination, save/unsave |
| `candidate_service.py` | Profile create/update, CV upload, async enrichment trigger |
| `recommendation_service.py` | Cache-first recommendation pipeline, score computation |
| `skill_gap_service.py` | Missing skills aggregation from top job matches |
| `search_service.py` | Embedding generation for query → pgvector cosine search |
| `redis_service.py` | Get/set/delete recommendations cache (1h TTL) |

#### Repositories implemented
| Repository | Table |
|---|---|
| `user_repository.py` | `users` |
| `candidate_repository.py` | `candidate_profiles` |
| `cv_repository.py` | `cv_documents` |
| `job_repository.py` | `job_offers`, `dw_job_offers`, `saved_jobs` |
| `saved_jobs_repository.py` | `saved_jobs` |

---

### 4.4 AI Services ✅ DONE (100%)

| Module | File | Status |
|---|---|---|
| Batch embedding generator | `ai_services/embedding/generator.py` | ✅ MiniLM-L6-v2, 384-dim, batch-only |
| Matching scorer | `ai_services/matching/scorer.py` | ✅ 4-signal weighted (0.5/0.3/0.1/0.1) with fuzzy skill match |
| Score explainer | `ai_services/matching/explainer.py` | ✅ Per-result: matched_skills, missing_skills, score_breakdown |
| Skill gap analyzer | `ai_services/matching/skill_gap.py` | ✅ Ranked missing skills by market frequency |
| CV text extractor | `ai_services/cv_parser/extractor.py` | ✅ PyPDF2 (PDF) + python-docx (DOCX) |
| Candidate enrichment | `ai_services/cv_parser/enrichment.py` | ✅ Smart merge: union skills, max experience, no overwrite |
| NLP pipeline | `etl/nlp.py` | ✅ spaCy fr_core_news_md, pattern matching, canonical normalization |
| Skill normalization | `etl/skill_normalization.py` | ✅ Against `skills_canonical.json` dictionary |
| Taxonomy classifier | `etl/taxonomy.py` | ✅ Data-domain role classification |

---

### 4.5 ETL Data Platform ✅ DONE (85%)

#### Ingestion — API Clients
| Client | Source | Status |
|---|---|---|
| `adzuna_client.py` | Adzuna API (international) | ✅ Implemented, rate-limit handling |
| `jsearch_client.py` | JSearch / RapidAPI | ✅ Implemented |
| `france_travail_client.py` | France Travail (official FR data) | ✅ Implemented |

#### Ingestion — Scrapy Spiders
| Spider | Source | Status |
|---|---|---|
| `rekrute_spider.py` | Rekrute.com (Morocco) | ✅ Implemented |
| `emploi_ma_spider.py` | Emploi.ma (Morocco/Africa) | ✅ Implemented |
| WelcomeToTheJungle | WTTJ (France/Europe) | ❌ Not started |

#### ETL Processing Modules
| Module | Status |
|---|---|
| `etl/ingest.py` — Bronze write with dedup | ✅ Done |
| `etl/transform.py` — Bronze → Silver | ✅ Done |
| `etl/validation.py` — Pydantic Silver schema | ✅ Done |
| `etl/enrich.py` — Silver → Gold with embeddings | ✅ Done |
| `etl/embeddings.py` — Batch embed jobs | ✅ Done |
| `etl/nlp.py` — Skill/tech stack extraction | ✅ Done |
| `etl/dedup.py` — external_id deduplication | ✅ Done |
| `etl/quality_checks.py` — Data quality assertions | ✅ Done |
| `etl/monitoring.py` — pipeline_runs logging | ✅ Done |
| `etl/taxonomy.py` — Role taxonomy classifier | ✅ Done |
| `etl/skill_normalization.py` — Canonical skills | ✅ Done |

#### Airflow DAG
- [x] `airflow/dags/job_etl_dag.py`
- [x] Full pipeline: scrape → ingest → transform → enrich → refresh views → summary
- [x] `schedule_interval = timedelta(hours=6)`
- [x] `max_active_runs = 1`, `catchup = False`
- [x] Retries: 3 with 3-min delay, 2h execution timeout
- [x] `_ensure_env()` pattern for secret resolution order

---

### 4.6 Frontend SPA ✅ DONE (80%)

#### Pages implemented
| Page | Route | Status | Notes |
|---|---|---|---|
| `Landing.tsx` | `/` | ✅ Done | Marketing landing page |
| `Login.tsx` | `/login` | ✅ Done | JWT login with error handling |
| `Register.tsx` | `/register` | ✅ Done | Account creation |
| `Dashboard.tsx` | `/dashboard` | ✅ Done | KPI cards, recent jobs, top match |
| `JobSearch.tsx` | `/jobs` | ✅ Done | Paginated search with FilterPanel |
| `JobDetail.tsx` | `/jobs/:id` | ✅ Done | Full job view, save button |
| `Recommendations.tsx` | `/recommendations` | ✅ Done | AI matches with score breakdown |
| `SkillGap.tsx` | `/skill-gap` | ✅ Done | Missing skills ranked by frequency |
| `Profile.tsx` | `/profile` | ✅ Done | Profile CRUD + CV upload + parsing status |
| `SavedJobs.tsx` | `/saved-jobs` | ✅ Done | Bookmarked jobs with unsave |
| `AdminDashboard.tsx` | `/admin` | ✅ Done | Navigation hub (structure only) |
| `PipelineStatus.tsx` | `/admin/pipeline` | ⚠️ Partial | UI exists, no live API data |
| `UserManagement.tsx` | `/admin/users` | ⚠️ Partial | UI exists, no live API data |

#### Hooks implemented
| Hook | Purpose | Status |
|---|---|---|
| `useJobs.ts` | Job listing, single job, save/unsave mutations | ✅ Done |
| `useRecommendations.ts` | AI recommendations with cache metadata | ✅ Done |
| `useSkillGap.ts` | Skill gap data | ✅ Done |
| `useSavedJobs.ts` | Saved jobs with pagination | ✅ Done |
| `useProfile.ts` | Candidate profile CRUD | ✅ Done |
| `useSearch.ts` | Semantic search | ✅ Done |

#### Stores (Zustand)
| Store | State managed | Status |
|---|---|---|
| `auth.store.ts` | `token`, `user`, `isAuthenticated`, `hydrate()`, `logout()` | ✅ Done |
| `filters.store.ts` | Active job search filters | ✅ Done |
| `theme.store.ts` | Dark/light mode preference | ✅ Done |

#### Components implemented
| Component | Purpose | Status |
|---|---|---|
| `JobCard.tsx` | Job listing card with save toggle | ✅ Done |
| `MatchScore.tsx` | Visual score display | ✅ Done |
| `SkillBadge.tsx` | Skill tag with matched/missing variant | ✅ Done |
| `FilterPanel.tsx` | Contract type, location, salary filters | ✅ Done |
| `SearchBar.tsx` | Text search input with debounce | ✅ Done |
| `Pagination.tsx` | Page navigation | ✅ Done |
| `EmptyState.tsx` | Zero-result placeholder | ✅ Done |
| `PageSkeleton.tsx` | Loading skeleton | ✅ Done |
| `ErrorBoundary.tsx` | React error boundary | ✅ Done |
| `ProtectedRoute.tsx` | Auth guard wrapper | ✅ Done |
| `AdminRoute.tsx` | Role-based route guard | ✅ Done |

#### Infrastructure
- [x] `services/api-client.ts` — centralized fetch with token injection, 204 handling
- [x] `services/jobs.service.ts`, `candidates.service.ts`, `auth.service.ts`, `recommendations.service.ts`, `search.service.ts`
- [x] `lib/query-client.ts` — TanStack Query config
- [x] `lib/toast.ts` — Sonner notification helpers
- [x] `layouts/AppLayout.tsx` — sidebar + topbar shell
- [x] `layouts/AuthLayout.tsx` — centered auth card shell
- [x] `config/routes.ts` — all route constants in one file
- [x] `types/index.ts` — `Job`, `CandidateProfile`, `Recommendation`, `PaginatedResponse<T>`, etc.
- [x] Dark mode via Tailwind `dark:` + Zustand theme store
- [x] Framer Motion transitions on all pages

---

### 4.7 Analytics & PowerBI ✅ PARTIAL

| Asset | Status |
|---|---|
| `powerbi/export_to_csv.py` | ✅ Exports 11 CSVs from Supabase materialized views |
| `powerbi/exports/` — 11 CSV files | ✅ Generated: market trends, skills, locations, salary, companies, candidates, recommendations |
| `powerbi/dashboard_specs.md` | ✅ Full 3-page design spec written |
| `powerbi/dax_measures.md` | ✅ All DAX measures documented |
| `powerbi/connection_guide.md` | ✅ Connection setup guide |
| **PAGE 1 — Market Overview** | 🔄 In progress (shown in screenshot: KPIs + line chart + bar + donut built) |
| **PAGE 2 — Skills & Seniority Deep Dive** | 🔄 In progress (active now) |
| **PAGE 3 — Salary Analysis** | ⏳ Not started |
| **PAGE 4 — Pipeline & Data Quality** | ⏳ Not started |

---

### 4.8 Tests ✅ PARTIAL (70%)

| Test File | Type | Passing |
|---|---|---|
| `test_api_clients.py` | Unit | ✅ Full |
| `test_embeddings.py` | Unit | ✅ Full |
| `test_nlp.py` | Unit | ✅ Full |
| `test_recommendations.py` | Integration | ✅ Full |
| `test_etl.py` | Integration | ✅ Full |
| `test_data_coherence.py` | Integration | ✅ Full |
| `test_pipeline_integration.py` | E2E | ⚠️ In progress |
| `test_phase3.py` | E2E | ⚠️ In progress |

---

### 4.9 Documentation ✅ DONE

- [x] `docs/ARCHITECTURE.md` — system architecture overview
- [x] `docs/backend.md` — API and service layer docs
- [x] `docs/frontend.md` — React component and store docs
- [x] `docs/ai-system.md` — AI/ML pipeline documentation
- [x] `docs/data-platform.md` — ETL and ingestion docs
- [x] `docs/progress-report.html` — visual progress report (no emojis, professional layout)
- [x] `README.md` — project overview

---

## 5. In-Progress Work

### 5.1 PowerBI Dashboard — Active Sprint

| Task | Assignee | Status | Notes |
|---|---|---|---|
| PAGE 1 Market Overview — KPI cards | You | ✅ Built | 1.256K offers, 199 companies, 1M salary visible |
| PAGE 1 — Line chart (daily offers by source) | You | ✅ Built | Adzuna, emploi.ma, rekrute, seed visible |
| PAGE 1 — Bar chart (by contract type) | You | ✅ Built | CDI, CDD, Autre, Stage |
| PAGE 1 — Horizontal bar (skills demand) | You | ✅ Built | Machine learning, SQL, Python, Agile... |
| PAGE 1 — Donut (offers by source %) | You | ✅ Built | Adzuna 71.82%, rekrute 14.8%, emploi.ma 12.45% |
| PAGE 2 — Skills & Seniority Deep Dive | You | 🔄 Active | Building now |
| PAGE 3 — Salary Analysis | You | ⏳ Queued | |
| PAGE 4 — Pipeline & Data Quality | You | ⏳ Queued | |

### 5.2 Test Suite Completion

| Task | Assignee | Status |
|---|---|---|
| `test_pipeline_integration.py` — complete mocks | TBD | 🔄 Active |
| `test_phase3.py` — remaining assertions | TBD | 🔄 Active |

---

## 6. Backlog — Tasks To Do

> Priority: 🔴 HIGH · 🟡 MEDIUM · 🟢 LOW

---

### EPIC 1 — Backend Hardening

| ID | Task | Priority | Effort | Notes |
|---|---|---|---|---|
| B-01 | Implement `/api/v1/auth/refresh` token refresh endpoint | 🔴 HIGH | S | Returns new JWT using refresh token; prevents silent logout |
| B-02 | Validate JWT on `hydrate()` in `auth.store.ts` by calling `/auth/me` | 🔴 HIGH | S | Currently accepts stale tokens from localStorage |
| B-03 | Move CV file storage to Supabase Storage (or S3) | 🔴 HIGH | M | Current `cv_uploads/` is ephemeral in Docker; data loss risk |
| B-04 | Connect `PipelineStatus.tsx` to real `GET /admin/pipeline` API | 🟡 MEDIUM | M | Admin page reads no live data currently |
| B-05 | Connect `UserManagement.tsx` to real `GET /admin/users` API | 🟡 MEDIUM | M | Admin page reads no live data currently |
| B-06 | Add auth test suite (`test_auth.py`) | 🟡 MEDIUM | M | Register, login, JWT decode, role check not tested |
| B-07 | Complete `test_pipeline_integration.py` | 🟡 MEDIUM | M | Finalize mocks and assertion coverage |
| B-08 | Complete `test_phase3.py` | 🟡 MEDIUM | M | CV upload flow, recommendation shape |
| B-09 | Add `GET /candidates/{id}/cv/status` endpoint | 🟡 MEDIUM | S | Polling endpoint so frontend can show parsing progress |
| B-10 | Implement admin `GET /admin/pipeline-runs` with pagination | 🟡 MEDIUM | M | Read from `pipeline_runs` table |
| B-11 | Add `GET /admin/stats` — platform-wide counts | 🟡 MEDIUM | S | Total jobs, candidates, recommendations served |
| B-12 | Rate limit per-user (not just per-IP) on `/recommendations` | 🟢 LOW | S | Prevent expensive embedding calls from being abused |

---

### EPIC 2 — Frontend Completion

| ID | Task | Priority | Effort | Notes |
|---|---|---|---|---|
| F-01 | Implement CV parsing status polling on Profile page | 🔴 HIGH | S | Currently shows static "pending" — no real-time update |
| F-02 | Fix `hydrate()` to validate token with `/auth/me` call | 🔴 HIGH | S | Depends on B-02 |
| F-03 | Wire `PipelineStatus.tsx` to `/admin/pipeline-runs` API | 🟡 MEDIUM | M | Depends on B-10 |
| F-04 | Wire `UserManagement.tsx` to `/admin/users` API | 🟡 MEDIUM | M | Depends on B-05 |
| F-05 | Add admin stats card row on `AdminDashboard.tsx` | 🟡 MEDIUM | S | Total jobs / candidates / pipeline runs |
| F-06 | Add score breakdown detail expand on Recommendations page | 🟡 MEDIUM | M | Show matched_skills, missing_skills, per-signal scores per card |
| F-07 | Add salary display on `JobCard.tsx` and `JobDetail.tsx` | 🟡 MEDIUM | S | `salary_min` / `salary_max` already in the `Job` type |
| F-08 | Add "Applied" status tracking on `JobDetail.tsx` | 🟢 LOW | M | POST to applications table |
| F-09 | Landing page — add live job count from API | 🟢 LOW | S | Replace static number with real `GET /jobs?per_page=1` total |
| F-10 | Add skill filter chip on `JobSearch.tsx` | 🟢 LOW | M | Multi-select skill filter, GIN index ready on DB |
| F-11 | Dark mode toggle button in `AppLayout` topbar | 🟢 LOW | S | Zustand theme store exists but toggle UI not added |
| F-12 | Mobile bottom nav bar for small screens | 🟢 LOW | M | Current sidebar is hidden on mobile |

---

### EPIC 3 — Data Platform

| ID | Task | Priority | Effort | Notes |
|---|---|---|---|---|
| D-01 | Implement WelcomeToTheJungle Scrapy spider | 🟡 MEDIUM | L | France/Europe listings; 3rd planned spider |
| D-02 | Add LinkedIn spider (best-effort, fragile) | 🟢 LOW | L | Use `scrapy-playwright` to handle JS rendering |
| D-03 | Schedule `export_to_csv.py` via Airflow DAG step | 🟡 MEDIUM | S | Currently manual; add as post-Gold task |
| D-04 | Add Airflow email alert on pipeline failure | 🟡 MEDIUM | S | `email_on_failure=True` is set but SMTP not configured |
| D-05 | Add data freshness check task to Airflow DAG | 🟢 LOW | S | Alert if no new Bronze rows in last 12h |
| D-06 | Implement `pipeline/cleaning/` module (stub exists) | 🟢 LOW | M | Duplicate title normalization, HTML stripping |

---

### EPIC 4 — AI & Matching

| ID | Task | Priority | Effort | Notes |
|---|---|---|---|---|
| A-01 | Implement candidate feedback loop on recommendation_history | 🟡 MEDIUM | L | Use `action` column (clicked/saved/dismissed) to re-weight per-user scores |
| A-02 | Add model versioning to embeddings | 🟢 LOW | M | Track `model_version` column on `dw_job_offers` for future model upgrades |
| A-03 | Add confidence score to NLP skill extraction | 🟢 LOW | M | spaCy entity confidence already available |
| A-04 | Benchmark HNSW parameters (`m`, `ef_construction`) | 🟢 LOW | S | Run pgvector benchmark at 10K+ offers to tune |

---

### EPIC 5 — PowerBI Analytics

| ID | Task | Priority | Effort | Notes |
|---|---|---|---|---|
| P-01 | PAGE 2 — Skills & Seniority Deep Dive | 🔴 HIGH | M | **Active now** (see Section 7) |
| P-02 | PAGE 3 — Salary Analysis | 🔴 HIGH | M | Depends on PAGE 2 completion |
| P-03 | PAGE 4 — Pipeline & Data Quality | 🔴 HIGH | M | Depends on PAGE 3 completion |
| P-04 | Publish `.pbix` file to repo | 🟡 MEDIUM | S | Version control the dashboard file |
| P-05 | Set up live Supabase DirectQuery connection | 🟡 MEDIUM | M | Replace CSV import with live PostgreSQL connection |
| P-06 | Add row-level security to PowerBI service | 🟢 LOW | M | Restrict dashboard access by role |

---

### EPIC 6 — Production & DevOps

| ID | Task | Priority | Effort | Notes |
|---|---|---|---|---|
| O-01 | Write production deployment guide | 🟡 MEDIUM | M | VPS: Nginx + SSL (Let's Encrypt) + Docker Compose prod override |
| O-02 | Create `.env.example` with all required variables | 🟡 MEDIUM | S | Document every env var with description |
| O-03 | Add GitHub Actions CI pipeline | 🟡 MEDIUM | M | Run Ruff + Pytest on every push to main |
| O-04 | Supabase database backup schedule | 🟡 MEDIUM | S | Enable PITR or pg_dump cron |
| O-05 | Configure SMTP for Airflow failure emails | 🟡 MEDIUM | S | Gmail app password or SendGrid |
| O-06 | Add health check endpoint to Docker Compose | 🟢 LOW | S | `HEALTHCHECK` instruction in Dockerfile |

---

## 7. PowerBI Dashboard Backlog

> Based on attached screenshot (PAGE 1 complete) and `dashboard_specs.md`

### PAGE 1 — Market Overview ✅ COMPLETE
**What's built (confirmed from screenshot):**
- KPI cards: 1.256K total offers, 199 companies, 1M sum of salary_avg
- Line chart: Sum of offer_count by Day and source_name (Adzuna spike to ~330 on day 28)
- Horizontal bar chart: Count of offers by contract_type (Autre > CDI > CDD > Stage)
- Horizontal bar chart: Sum of offer_count by skill_name (machine learning, sql, python, agile, ci/cd, azure, aws, spark, scrum, data science, gcp)
- Donut chart: Sum of offer_count by source_name (Adzuna 71.82%, rekrute 14.8%, emploi.ma 12.45%, seed ~1%)

**Missing from spec (to finalize PAGE 1):**
- [ ] Map visual — offers by French city (requires `mv_offers_by_location` data)
- [ ] Top Skill KPI card (currently showing salary instead)
- [ ] Week-over-week growth % DAX card

---

### PAGE 2 — Skills & Seniority Deep Dive ⏳ IN PROGRESS

**Recommended visuals:**

| # | Visual | Source | Config |
|---|---|---|---|
| 1 | **Matrix heatmap** — Skills × Source | `mv_offers_by_skill` | Rows: skill_name, Cols: source_name, Values: offer_count, conditional color |
| 2 | **Clustered bar** — Top 20 skills by demand | `mv_offers_by_skill` | Sort by offer_count DESC, filter top 20 |
| 3 | **Donut** — Seniority distribution | `dw_job_offers` | Values: COUNT by seniority_level (Junior/Mid/Senior/Unknown) |
| 4 | **Line trend** — Skill demand over time | `mv_market_trends` + `mv_offers_by_skill` | Top 5 skills week-over-week |
| 5 | **KPI Card** — Most demanded skill | `mv_offers_by_skill` | DAX: `TOPN(1, ...)` |
| 6 | **KPI Card** — Skills coverage % | `dw_job_offers` | % of offers with 3+ skills |
| 7 | **Slicer** — Filter by skill category | `mv_offers_by_skill` | Multi-select: AI/ML, Data Eng, Analytics, DevOps |
| 8 | **Table** — Skill co-occurrence | `dw_job_offers` | Which skills appear together most |

**DAX measures needed:**
```dax
Avg Skills Per Offer =
AVERAGEX(VALUES(dw_job_offers[id]), COUNTROWS(RELATEDTABLE(skills_table)))

Seniority Distribution % =
DIVIDE(COUNTROWS(FILTER(dw_job_offers, dw_job_offers[seniority_level] = "Senior")),
       COUNTROWS(dw_job_offers))

Top 5 Skills =
TOPN(5, VALUES(mv_offers_by_skill[skill_name]),
     CALCULATE(SUM(mv_offers_by_skill[offer_count])))
```

---

### PAGE 3 — Salary Analysis ⏳ NOT STARTED

**Recommended visuals:**

| # | Visual | Source | Config |
|---|---|---|---|
| 1 | **Clustered bar** — Salary range by role | `mv_salary_by_role` | salary_min, salary_avg, salary_max per job_title |
| 2 | **Scatter plot** — Salary vs. offer volume | `mv_salary_by_role` | X: offer_count, Y: salary_avg, size: offer_count, color: contract_type |
| 3 | **Matrix** — Contract type × role salary | `mv_salary_by_role` | Heatmap: conditional formatting on salary_avg |
| 4 | **KPI Cards** — Median salary, top paying role, salary coverage % | DAX measures | |
| 5 | **Box plot / violin** — Salary spread | `mv_salary_by_role` | salary_min, salary_avg, salary_max as error bars |
| 6 | **Slicer** — Contract type, location | `mv_salary_by_role` | CDI / CDD / Freelance / Stage |

**DAX measures needed:**
```dax
Median Salary = PERCENTILE.INC(mv_salary_by_role[salary_avg], 0.5)
Salary Coverage % = DIVIDE(COUNTROWS(FILTER(job_offers, job_offers[salary_avg] <> BLANK())), COUNTROWS(job_offers))
Top Paying Role = FIRSTNONBLANK(TOPN(1, VALUES(mv_salary_by_role[job_title]), CALCULATE(MAX(mv_salary_by_role[salary_max]))), 1)
Salary Premium CDI vs CDD = [Avg Salary CDI] - [Avg Salary CDD]
```

---

### PAGE 4 — Pipeline & Data Quality ⏳ NOT STARTED

**Recommended visuals:**

| # | Visual | Source | Config |
|---|---|---|---|
| 1 | **Line chart** — Pipeline run history | `pipeline_runs` | X: created_at, Y: row_count by stage (Bronze/Silver/Gold) |
| 2 | **Clustered bar** — Rows per stage per run | `pipeline_runs` | Bronze vs Silver vs Gold — shows funnel drop-off |
| 3 | **KPI Cards** — Total pipeline runs, avg duration (ms), last run status | `pipeline_runs` | |
| 4 | **Table** — Failed runs log | `pipeline_runs` | Filter: status = 'failed', show stage, error, timestamp |
| 5 | **Gauge** — Bronze → Silver conversion rate | `pipeline_runs` | Silver row_count / Bronze row_count |
| 6 | **Gauge** — Silver → Gold conversion rate | `pipeline_runs` | Gold row_count / Silver row_count |
| 7 | **Bar** — Offers by source freshness | `raw_job_offers` | Count grouped by ingested_at date |
| 8 | **KPI Card** — Unprocessed Bronze rows | `raw_job_offers` | COUNT WHERE processed = false — data health metric |
| 9 | **Donut** — Scraping logs status breakdown | `scraping_logs` | success vs failed vs skipped |

**DAX measures needed:**
```dax
Pipeline Success Rate =
DIVIDE(COUNTROWS(FILTER(pipeline_runs, pipeline_runs[status] = "success")),
       COUNTROWS(pipeline_runs))

Bronze to Silver Rate =
DIVIDE([Silver Row Count], [Bronze Row Count])

Avg Pipeline Duration (min) =
AVERAGE(pipeline_runs[duration_ms]) / 60000

Last Run Status =
FIRSTNONBLANK(TOPN(1, VALUES(pipeline_runs[status]),
    CALCULATE(MAX(pipeline_runs[created_at]))), 1)
```

---

## 8. Technical Debt & Risks

| Debt Item | Risk Level | Action |
|---|---|---|
| `auth.store.ts` accepts expired/invalid tokens from localStorage | 🔴 HIGH | Call `/auth/me` on hydrate; redirect to login on 401 |
| CV files stored on local disk | 🔴 HIGH | Migrate to Supabase Storage before production |
| No token refresh mechanism | 🔴 HIGH | Implement refresh token flow (backend + frontend) |
| Admin pages have no real API connections | 🟡 MEDIUM | Wire to existing admin endpoints or create new ones |
| PowerBI connected via CSV snapshots, not live | 🟡 MEDIUM | Set up DirectQuery to Supabase PostgreSQL |
| No CI/CD pipeline | 🟡 MEDIUM | GitHub Actions: Ruff + Pytest on every PR |
| SMTP not configured for Airflow alerts | 🟡 MEDIUM | Configure before production deployment |
| WelcomeToTheJungle spider missing | 🟢 LOW | One sprint to implement + test |
| Test coverage 70% (target: 90%+) | 🟡 MEDIUM | Add auth tests, complete E2E test modules |
| No `.env.example` file | 🟡 MEDIUM | Document all 15+ required env variables |

---

## 9. Team Contributions

### Amine (You) — Full-Stack + AI + Data
- **Architecture & DevOps:** Docker Compose, Dockerfile, full infra design
- **Backend:** All 7 routers, 7 services, 5 repositories, JWT auth, RBAC
- **AI Services:** Matching scorer, explainer, skill gap, embedding generator, CV parser
- **ETL:** All 3 API clients, Airflow DAG, Bronze/Silver/Gold pipeline, monitoring
- **Database:** All 9 SQL migrations, pgvector HNSW setup, RLS policies
- **Frontend:** Architecture, routing, Zustand stores, API client, component system
- **PowerBI:** Dashboard specs, DAX measures, export pipeline, Page 1 complete
- **Documentation:** All 5 docs + progress report + this backlog

### Reda — Frontend
- **Pages implemented:** Dashboard, Job Search, Job Detail, Profile, Recommendations, Skill Gap, Saved Jobs, Login, Register, Landing
- **Components:** JobCard, MatchScore, SkillBadge, FilterPanel, SearchBar, Pagination, EmptyState, PageSkeleton, ErrorBoundary, ProtectedRoute, AdminRoute
- **Hooks:** useJobs, useRecommendations, useSkillGap, useSavedJobs, useProfile, useSearch
- **Admin pages:** AdminDashboard, PipelineStatus, UserManagement (structure)
- **UX polish:** Framer Motion transitions, dark mode support, Tailwind responsive layout, Sonner notifications
- **State management:** auth.store, filters.store, theme.store wiring

---

## 10. Definition of Done

A task is **Done** when ALL of the following apply:

- [ ] **Code complete** — feature is implemented with no TODOs
- [ ] **Tests added** — unit or integration test covers the new code
- [ ] **Types updated** — TypeScript types and Pydantic schemas reflect changes
- [ ] **Documentation updated** — relevant `.md` doc updated if public API changed
- [ ] **No regressions** — `pytest` passes, `ruff check` clean
- [ ] **Committed** — staged with `git add -A`, committed with conventional commit message
- [ ] **Reviewer approved** (when working in team) — PR reviewed before merge to `main`

---

## Appendix — Effort Key

| Label | Estimate |
|---|---|
| XS | < 1 hour |
| S | 1–4 hours (half day) |
| M | 1–2 days |
| L | 3–5 days |
| XL | 1+ week |

---

*Generated by GitHub Copilot acting as Project Manager — April 27, 2026*  
*Repository: Ridadata/job-intelligent · Branch: feature/amine-dev*
