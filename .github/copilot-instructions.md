# Copilot Instructions — JOB INTELLIGENT

## Project Context

Job Intelligent is an AI-powered SaaS platform that centralizes data-related job opportunities and provides intelligent job-to-candidate matching using NLP, embeddings, and pgvector similarity search.

**Stack:** FastAPI · React/TypeScript · Supabase (PostgreSQL 15 + pgvector) · Redis · Scrapy · Airflow · spaCy · Sentence-BERT · Docker Compose

**Architecture:** Monorepo with clear module boundaries — NOT microservices.

---

## Git & Commit Workflow

- **Commit after every completed change or task.** Do not batch unrelated work into a single commit.
- Use [Conventional Commits](https://www.conventionalcommits.org/) format: `feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `chore:`.
- Commit message body must list every file changed and what was done.
- Always commit on the current working branch — never commit directly to `main`.
- Stage all related files with `git add -A` before committing — do not leave unstaged work behind.

---

## Data Ingestion Strategy

Hybrid job ingestion with two tiers:

### Primary — Job APIs (reliable, structured)
- **Adzuna API** — international coverage, free tier.
- **JSearch (RapidAPI)** — aggregator with broad coverage.
- **France Travail API** — official French public employment data.

API clients live in `data-platform/ingestion/api_clients/`. One client class per API.
Each client must implement `fetch_jobs(query, location, **params) -> list[JobItem]`.
Store API keys in environment variables, never hardcode.

### Fallback — Web Scraping (supplementary)
- **Rekrute.com** — Morocco.
- **Emploi.ma** — Morocco / Africa.
- **WelcomeToTheJungle** — France / Europe.
- **Indeed, LinkedIn** — global, fragile, best-effort.

Scrapy spiders live in `data-platform/scrapers/job_scrapers/spiders/`.

### Normalization Rule
All sources — API and scraper — normalize into the same `JobItem` schema before Bronze ingestion. The downstream pipeline is source-agnostic.

---

## Candidate Data Strategy

Two input channels:

### 1. Profile Form (primary source)
```
candidate_profiles:
  name, email, title, skills[], experience_years,
  education_level, location, salary_expectation,
  preferred_contract_types[], profile_completeness
```
- Profiles are created via `/api/v1/candidates/profile` (POST/PUT).
- Skills are stored as a text array, normalized against the canonical skill dictionary.
- `profile_completeness` is a computed percentage (0–100) based on filled fields.

### 2. CV Upload (enrichment source)
```
cv_documents:
  candidate_id, file_path, file_type, raw_text,
  parsed_skills[], parsed_experience, parsed_education,
  parsing_status, parsed_at
```
- Accept PDF and DOCX via `/api/v1/candidates/cv` (POST, multipart/form-data).
- Parse with `PyPDF2` (PDF) and `python-docx` (DOCX) to extract raw text.
- Run NLP pipeline (spaCy + pattern matching) to extract skills, experience, education.
- Auto-enrich `candidate_profiles` with parsed data.
- **Never overwrite** manual profile fields — merge intelligently (union for skills, keep higher experience).
- Generate/update candidate embedding after enrichment.

### CV Parsing Rules
- File size limit: 5 MB.
- Store files in a `cv_uploads/` directory (or object storage in production).
- Never store file content in the database — store the file path and extracted text.
- Parsing is async: upload returns immediately, parsing runs in background.
- Log parsing results to `cv_documents.parsing_status` (`pending`, `success`, `failed`).

---

## Dual Embedding Pipeline

### Job Embeddings
- **Input text:** `"{title}. {description}. Skills: {skills_joined}"`
- **Generated during:** Gold enrichment stage (Airflow DAG).
- **Stored in:** `dw_job_offers.embedding` (`vector(384)`).

### Candidate Embeddings
- **Input text:** `"{title}. Skills: {skills_joined}. {experience_summary}"`
- **Generated on:** profile create, profile update, CV enrichment.
- **Stored in:** `candidate_profiles.embedding` (`vector(384)`).

### Matching
- Use pgvector `<=>` operator for cosine distance.
- bidirectional: find jobs for a candidate OR find candidates for a job.
- Always batch-embed. Never embed one document at a time.

---

## Architecture Rules

- **Layered backend:** `routers → services → repositories → database`. Never skip a layer.
- **Data platform:** Bronze (raw) → Silver (validated/normalized) → Gold (enriched with embeddings). Layers are immutable boundaries.
- **Data ingestion:** APIs first, scraping as fallback. All sources normalize to the same schema before Bronze.
- **Candidate data:** Profile form is primary. CV upload enriches but never overwrites manual data.
- **AI services:** Standalone module consumed by backend services via direct import. No separate API for AI.
- **Frontend:** React SPA communicating with backend via REST API. No server-side rendering.
- **Infrastructure:** Docker Compose only. No Kubernetes, no Kafka, no Spark.
- **State management:** PostgreSQL is the source of truth. Redis is cache only — every cached value must be rebuildable from DB.
- **Simplicity:** Simple modular monolith. Avoid microservices, complex distributed systems, and unnecessary tools.

---

## Backend Patterns

### FastAPI Conventions

```python
# Router → Service → Repository. Never call DB from a router.
@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: UUID, service: JobService = Depends(get_job_service)):
    return await service.get_by_id(job_id)
```

- Use `Depends()` for all injected dependencies (services, auth, DB client).
- Use Pydantic `BaseModel` for all request/response schemas. Never return raw dicts.
- Use `HTTPException` with specific status codes. Never return 200 with an error body.
- Use `status_code=status.HTTP_201_CREATED` for POST endpoints that create resources.
- All list endpoints must support pagination via `page` and `per_page` query params.
- Return paginated responses using `PaginatedResponse[T]` schema.

### Service Layer

- Services contain business logic. They are classes instantiated with repository dependencies.
- Services never import `fastapi`, `Request`, or `Response`.
- Services raise domain exceptions (`JobNotFoundError`, `DuplicateEmailError`), not HTTP exceptions.
- Services are stateless — no instance state beyond injected dependencies.

### Repository Layer

- Repositories are thin wrappers around Supabase table operations.
- One repository per database table.
- Repositories return domain models or dicts. They never raise HTTP exceptions.
- Use parameterized queries via the Supabase client — never build SQL strings manually.

### Authentication & Authorization

- JWT tokens for API authentication (`python-jose`).
- Roles: `candidate`, `admin`.
- Protect routes with `Depends(get_current_user)` or `Depends(require_role("admin"))`.
- Never store passwords in plain text — use `passlib` bcrypt.

### Error Handling

- All API errors return JSON with `{"detail": "message", "code": "ERROR_CODE"}`.
- Use custom exception classes inheriting from a base `AppError`.
- Register a global exception handler in `main.py`.

### Configuration

- All config via Pydantic `BaseSettings` in `backend/core/config.py`.
- Access config through `get_settings()` dependency. Never use `os.environ` directly in business code.
- Secrets come from environment variables, never hardcoded.

---

## Frontend Patterns

### React / TypeScript Conventions

- Functional components only. No class components.
- Use TypeScript strict mode. No `any` types except at API boundaries with explicit casting.
- Use TanStack Query for all server state. No `useEffect` + `useState` for data fetching.
- Use Zustand for client-only state (auth, theme, UI filters).
- Colocate hooks with features: `hooks/useJobs.ts` next to `pages/JobSearch.tsx`.

### Component Structure

```
ComponentName/
    ComponentName.tsx       # Component logic + JSX
    ComponentName.test.tsx  # Tests (when needed)
```

- Props interfaces are defined in the same file, named `{ComponentName}Props`.
- Use Shadcn UI primitives. Don't build custom UI components when Shadcn has one.
- All pages must handle: loading (skeleton), error (error boundary), empty (empty state).

### API Communication

- All API calls go through a centralized `api-client.ts` with Axios or fetch wrapper.
- The API client handles token injection, refresh, and error normalization.
- Use TanStack Query `queryKey` conventions: `["jobs", filters]`, `["job", jobId]`, `["recommendations", candidateId]`.
- Mutations invalidate related queries automatically.

### Styling

- TailwindCSS utility classes only. No custom CSS files unless absolutely necessary.
- Dark mode via Tailwind `dark:` variant backed by a Zustand theme store.
- Responsive-first: design for mobile, enhance for desktop.

---

## ETL Rules

### Job Data Pipeline

```
APIs (Adzuna, JSearch, France Travail)
  → Bronze (raw_job_offers)
Scrapers (Rekrute, Emploi.ma, WTTJ)
  → Bronze (raw_job_offers)
Bronze → Silver (job_offers) — validated, normalized, filtered to data-domain
Silver → Gold (dw_job_offers) — embeddings, NLP skills, scores
```

### Candidate Data Pipeline

```
Profile form → candidate_profiles
CV upload → cv_documents → NLP parsing → enrich candidate_profiles
Profile create/update → generate candidate embedding
```

### Pipeline Principles

- **Bronze layer** is immutable raw data. Never modify Bronze rows after insertion.
- **Silver layer** is validated and normalized. Schema-validated via Pydantic before insert.
- **Gold layer** is enriched with embeddings, NLP extractions, and computed scores.
- Every pipeline run must log to `pipeline_runs` table: stage, row_count, duration_ms, status, errors.
- Use `processed` flag on Bronze rows for incremental processing. Mark processed = True after Silver transformation.
- Upsert with `processed = False` on re-ingestion so updated rows are re-processed.

### API Clients

- One client class per job API in `data-platform/ingestion/api_clients/`.
- Each client implements `fetch_jobs(query, location, **params) -> list[JobItem]`.
- API keys via environment variables. Never hardcode.
- Handle rate limiting, pagination, and retries inside each client.
- Normalize API response to `JobItem` before returning.

### Scrapy Spiders

- One spider per job board in `scrapers/job_scrapers/spiders/`.
- Every spider must yield items matching the `JobItem` schema: `external_id`, `title`, `company`, `location`, `description`, `contract_type`, `url`, `published_at`.
- `external_id` is mandatory — it's the dedup key.
- Run spiders via subprocess from Airflow (Twisted reactor conflicts). Never import spider code directly into Airflow tasks.
- Handle per-spider `custom_settings` for rate limiting, timeouts, and robots.txt policy.

### Airflow DAGs

- One DAG per pipeline: `job_etl` (scrape → ingest → transform → enrich → refresh → summary).
- Use `PythonOperator` with callable functions defined in the DAG file.
- Environment variables for secrets — use `os.environ` with `_ensure_env()` fallback pattern. Avoid hard dependency on Airflow Variables.
- Set `catchup=False` on all DAGs. No backfills unless explicitly triggered.
- Set `max_active_runs=1` to prevent parallel ETL runs.

---

## AI Service Rules

### Embeddings

- Model: `all-MiniLM-L6-v2` (Sentence-BERT, 384 dimensions).
- **Job embedding input:** `"{title}. {description}. Skills: {skills_joined}"`
- **Candidate embedding input:** `"{title}. Skills: {skills_joined}. {experience_summary}"`
- Store embeddings in `vector(384)` column with HNSW index.
- Batch embed — never embed one document at a time.
- Cache hot embeddings in Redis (TTL 1 hour).
- Regenerate candidate embedding on profile update or CV enrichment.

### NLP / Skill Extraction

- Model: `spaCy fr_core_news_md` for French NER.
- Extract skills via pattern matching + NER, not pure regex.
- Normalize extracted skills against a canonical skill dictionary.
- Return skills as a deduplicated sorted list.
- Used for both job descriptions (Gold enrichment) and CV text (candidate enrichment).

### CV Parsing

- Extract raw text from PDF (`PyPDF2`) and DOCX (`python-docx`).
- Run spaCy pipeline to extract: skills, technologies, experience, education.
- Map extracted data to candidate profile fields.
- Merge strategy: union for skills, keep max for experience_years, append for education.
- Log parsing results with status and confidence metrics.

### Matching & Recommendations

- Match score is a weighted combination: skill overlap (0.5) + embedding similarity (0.3) + seniority alignment (0.1) + location preference (0.1).
- Every recommendation must include an explanation: `matched_skills`, `missing_skills`, `score_breakdown`.
- Use pgvector `<=>` operator for cosine distance in similarity queries.
- Limit recommendation results to top 20 per request.

---

## API Response Standards

### Success Responses

```json
// Single resource
{
  "id": "uuid",
  "title": "Data Engineer",
  "company": "Acme"
}

// List (paginated)
{
  "items": [...],
  "total": 142,
  "page": 1,
  "per_page": 20,
  "pages": 8
}
```

### Error Responses

```json
{
  "detail": "Job not found",
  "code": "JOB_NOT_FOUND"
}
```

### HTTP Status Codes

| Code | Usage |
|------|-------|
| 200 | Success (GET, PUT, PATCH) |
| 201 | Created (POST) |
| 204 | Deleted (DELETE) |
| 400 | Validation error |
| 401 | Not authenticated |
| 403 | Not authorized |
| 404 | Resource not found |
| 409 | Conflict (duplicate) |
| 429 | Rate limited |
| 500 | Internal server error |

---

## Naming Conventions

### Python (Backend + ETL + AI)

- **Files:** `snake_case.py` — `job_service.py`, `skill_normalization.py`
- **Classes:** `PascalCase` — `JobService`, `CandidateRepository`
- **Functions:** `snake_case` — `get_by_id()`, `transform_to_silver()`
- **Constants:** `UPPER_SNAKE_CASE` — `MAX_RETRIES`, `DEFAULT_PAGE_SIZE`
- **Private:** prefix with `_` — `_validate_skills()`, `_DATA_KEYWORDS`

### TypeScript (Frontend)

- **Files:** `PascalCase.tsx` for components, `camelCase.ts` for utilities — `JobCard.tsx`, `useJobs.ts`
- **Components:** `PascalCase` — `JobCard`, `SearchBar`
- **Functions/hooks:** `camelCase` — `useJobs()`, `formatDate()`
- **Types/interfaces:** `PascalCase` — `Job`, `UserProfile`, `PaginatedResponse<T>`
- **Constants:** `UPPER_SNAKE_CASE` — `API_BASE_URL`, `MAX_SKILLS`

### Database

- **Tables:** `snake_case` plural — `job_offers`, `raw_job_offers`, `dw_job_offers`, `candidate_profiles`, `cv_documents`, `saved_jobs`, `applications`
- **Columns:** `snake_case` — `published_at`, `contract_type`, `required_skills`, `experience_years`, `parsing_status`
- **Indexes:** `idx_{table}_{column}` — `idx_job_offers_published_at`, `idx_candidate_profiles_embedding`
- **Functions:** `snake_case` — `refresh_all_analytics_views()`

### API Endpoints

- **REST convention:** `/api/v1/{resource}` — `/api/v1/jobs`, `/api/v1/candidates`
- **Nested resources:** `/api/v1/candidates/{id}/recommendations`, `/api/v1/candidates/{id}/saved-jobs`
- **Actions:** `/api/v1/jobs/{id}/save`, `/api/v1/auth/login`, `/api/v1/candidates/cv` (upload)
- Always plural nouns. Never verbs in URLs except for actions.

### Key Endpoints Map

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/v1/auth/register` | Create account |
| POST | `/api/v1/auth/login` | Get JWT token |
| GET/PUT | `/api/v1/candidates/profile` | Manage own profile |
| POST | `/api/v1/candidates/cv` | Upload CV (multipart) |
| GET | `/api/v1/jobs` | Search/list jobs (paginated) |
| GET | `/api/v1/jobs/{id}` | Job detail |
| POST | `/api/v1/jobs/{id}/save` | Save a job |
| GET | `/api/v1/candidates/{id}/recommendations` | Get recommendations |
| GET | `/api/v1/candidates/{id}/skill-gap` | Skill gap analysis |
| GET | `/api/v1/search?q=...` | Semantic job search |

---

## Code Quality Rules

1. **No `any` in TypeScript.** Use `unknown` + type guards when type is truly unknown.
2. **No raw SQL strings in Python.** Use the Supabase client's query builder.
3. **No `print()` in production code.** Use the `logging` module.
4. **No hardcoded secrets.** All secrets via environment variables.
5. **No business logic in routers.** Routers parse requests and call services.
6. **No HTTP concepts in services.** Services don't know about requests, responses, or status codes.
7. **No unused imports.** Enforced by Ruff.
8. **No `# type: ignore` without an inline comment explaining why.**
9. **Tests must be deterministic.** No reliance on external APIs, current time, or random values without mocking.
10. **Every public function must have a docstring** with Args, Returns, and Raises sections.

---

## Repository Organization

```
job-intelligent/
├── backend/              # FastAPI application
│   ├── core/             # Config, logging, security, exceptions
│   ├── models/           # Database models / domain objects
│   ├── schemas/          # Pydantic request/response schemas
│   ├── repositories/     # Data access layer
│   ├── services/         # Business logic layer
│   ├── routers/          # API endpoint definitions
│   ├── middleware/        # Request processing (auth, rate limit, logging)
│   └── dependencies/     # FastAPI Depends() factories
├── frontend/             # React + TypeScript SPA
│   └── src/
│       ├── components/   # Reusable UI components
│       ├── pages/        # Route-level page components
│       ├── hooks/        # Custom React hooks
│       ├── services/     # API client and service functions
│       ├── store/        # Zustand state stores
│       └── types/        # TypeScript type definitions
├── data-platform/        # ETL + Ingestion + Scraping
│   ├── etl/              # Transform, validate, enrich logic
│   ├── ingestion/        # API clients for job data sources
│   │   └── api_clients/  # One client per API (Adzuna, JSearch, France Travail)
│   ├── scrapers/         # Scrapy spiders (fallback sources)
│   └── airflow/          # DAG definitions
├── ai-services/          # NLP, embeddings, matching engine
│   ├── matching/         # Scorer, explainer, skill gap
│   ├── cv_parser/        # CV text extraction + NLP enrichment
│   └── embedding/        # Job + candidate embedding generation
├── sql/                  # Database migrations (numbered)
├── tests/                # All tests (unit, integration, ETL)
├── infra/                # Docker, Nginx, CI/CD configs
├── docs/                 # Architecture, specs, guides
└── Makefile              # Developer commands
```

**Rule:** every folder has a `__init__.py` (Python) or `index.ts` (TypeScript) that defines its public API. Internal modules are prefixed with `_`.
