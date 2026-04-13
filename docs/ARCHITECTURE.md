# Architecture

## Overview

Job Intelligent is a monolithic SaaS platform with four clearly separated layers:
**Data Platform → Database → Backend API → Frontend**.

Each layer has strict boundaries — no layer skips the one below it.

---

## System Design

```
┌────────────────────────────────────────────────────────────────┐
│                        DATA SOURCES                            │
│                                                                │
│  Job APIs (primary)              Scrapy Spiders (fallback)     │
│  ┌─────────────────┐             ┌──────────────────────┐      │
│  │ Adzuna API      │             │ Rekrute.com          │      │
│  │ JSearch API     │──────────── │ Emploi.ma            │      │
│  │                 │  Airflow    │    │                 │
│  └─────────────────┘  6h cron    └──────────────────────┘      │
└──────────────────────────┬─────────────────────────────────────┘
                           │ normalized JobItem schema
                           ▼
┌────────────────────────────────────────────────────────────────┐
│                    ETL PIPELINE (Airflow DAG)                  │
│                                                                │
│  ┌──────────────┐   ┌──────────────────┐   ┌───────────────┐  │
│  │    BRONZE    │──▶│     SILVER       │──▶│     GOLD      │  │
│  │raw_job_offers│   │   job_offers     │   │dw_job_offers  │  │
│  │ raw JSON     │   │ validated/clean  │   │ + embeddings  │  │
│  │ immutable    │   │ NLP·dedup·taxo   │   │ vector(384)   │  │
│  └──────────────┘   └──────────────────┘   └───────────────┘  │
│                                                                │
│  Every stage → pipeline_runs (observability)                   │
└──────────────────────────┬─────────────────────────────────────┘
                           │ Supabase PostgreSQL 15 + pgvector
                           ▼
┌────────────────────────────────────────────────────────────────┐
│                    BACKEND API (FastAPI)                       │
│                                                                │
│  Routers → Services → Repositories → Supabase client          │
│                                                                │
│  /auth          JWT HS256 · bcrypt · RBAC                      │
│  /jobs          search · detail · save                         │
│  /candidates    profile CRUD · CV upload                       │
│  /recommendations  pgvector cosine · multi-signal scorer       │
│  /search        semantic search (natural language query)       │
│  /health        liveness probe                                 │
│                                                                │
│  Redis: recommendation cache (TTL 1h), search cache (5 min)   │
│  Middleware: JWT auth · rate limiting · request ID · CORS      │
└──────────────────────────┬─────────────────────────────────────┘
                           │ REST/JSON
                           ▼
┌────────────────────────────────────────────────────────────────┐
│                   FRONTEND (React + TypeScript)                │
│                                                                │
│  Pages: Dashboard · Job Search · Recommendations               │
│         Profile · Skill Gap · Saved Jobs                       │
│                                                                │
│  TanStack Query (server state) · Zustand (client state)        │
│  Tailwind CSS + Shadcn UI · Dark/light mode                    │
└────────────────────────────────────────────────────────────────┘
```

---

## Database Schema (key tables)

| Table | Layer | Purpose |
|---|---|---|
| `sources` | Meta | Registry of all ingestion sources |
| `raw_job_offers` | Bronze | Immutable raw JSON blobs |
| `job_offers` | Silver | Validated, normalized job records |
| `dw_job_offers` | Gold | Enriched with embeddings + demand scores |
| `users` | Auth | Email, bcrypt hash, role |
| `candidate_profiles` | Candidate | Skills, experience, embedding vector(384) |
| `cv_documents` | Candidate | CV file path, raw text, parse status |
| `saved_jobs` | Product | Candidate ↔ job_offers bookmarks |
| `recommendation_history` | AI | Log of surfaced recommendations |
| `pipeline_runs` | Ops | ETL observability (rows, timing, errors) |

---

## Key Design Decisions

- **Monorepo, not microservices.** All modules import each other directly; no inter-service HTTP.
- **Supabase as managed Postgres.** pgvector extension enables HNSW vector search without a separate vector DB.
- **Redis is cache-only.** Every cached value is rebuildable from the DB. Redis holds recommendations (1h TTL) and search results (5 min TTL).
- **AI services as a library.** `ai_services/` is imported directly by the backend — no separate AI API server.
- **Docker Compose only.** No Kubernetes, no Kafka, no Spark. One `docker compose up -d` starts everything.
- **Airflow runs ETL.** One DAG (`job_etl`) orchestrates ingest → transform → enrich, scheduled every 6 hours.
- **Scrapers run via subprocess.** Twisted reactor conflicts with Airflow; spiders are launched as subprocesses, never imported directly.

---

## Request Flow — Recommendations

```
Browser
  │  POST /api/v1/recommendations {candidate_id, top_n}
  │
  ▼
FastAPI Router (recommendations.py)
  │  validates JWT, extracts user identity
  │
  ▼
RecommendationService
  │  1. Redis cache hit? → return immediately
  │  2. CandidateRepository.find_by_user_id() → candidate profile + skills
  │  3. ai_services/embedding → generate query embedding (384d)
  │  4. JobRepository.match_by_embedding() → RPC match_job_offers() (pgvector)
  │  5. ai_services/matching/scorer → multi-signal re-score each result
  │  6. ai_services/matching/explainer → matched/missing skills per result
  │  7. Redis set (TTL 1h)
  │  8. JobRepository.log_recommendation_history()
  │
  ▼
Response: {data: [{title, company, score, matched_skills, ...}], total, latency_ms}
```

---

## Security Model

- JWT (HS256) — 60 min expiry, validated on every protected route
- Passwords hashed with bcrypt (passlib, 12 rounds)
- Roles: `candidate` (default), `admin`
- Row-level security (RLS) enabled on all Supabase tables — service-role key bypasses for backend writes
- Rate limiting middleware (per-IP, configurable)
- CORS restricted to configured origins
- No raw SQL string concatenation — all queries via Supabase query builder
