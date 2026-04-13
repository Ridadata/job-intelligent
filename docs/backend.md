# Backend

## Overview

The backend is a FastAPI application following a strict layered architecture.
**Routers → Services → Repositories → Database.** No layer skips another.

**Entry point:** `api/main.py`
**Port:** 8000
**Base URL:** `/api/v1`

---

## Project Structure

```
api/
├── main.py                 App factory: routers, middleware, exception handlers
├── core/
│   ├── config.py           Pydantic BaseSettings — all config from env vars
│   ├── security.py         JWT encode/decode, bcrypt hashing
│   └── exceptions.py       Domain exception classes (NotFoundError, etc.)
├── middleware/
│   ├── error_handler.py    Global exception → JSON response
│   ├── rate_limit.py       Per-IP rate limiting
│   └── request_id.py       X-Request-ID header injection
├── models/
│   └── schemas.py          Recommendation engine data models (JobOfferMatch, etc.)
├── repositories/
│   ├── user_repository.py
│   ├── candidate_repository.py
│   ├── job_repository.py
│   ├── saved_jobs_repository.py
│   └── cv_repository.py
├── routers/
│   ├── auth.py
│   ├── jobs.py
│   ├── candidates.py
│   ├── recommendations.py
│   ├── search.py
│   └── health.py
├── schemas/
│   ├── common.py           PaginatedResponse[T], error schemas
│   ├── job.py              JobResponse, JobListResponse
│   ├── candidate.py        CandidateProfileRequest/Response
│   └── recommendation.py  RecommendationRequest/Response
├── services/
│   ├── auth_service.py
│   ├── job_service.py
│   ├── candidate_service.py
│   ├── recommendation_service.py
│   ├── search_service.py
│   ├── skill_gap_service.py
│   └── redis_service.py
└── dependencies.py         FastAPI Depends() factories
```

---

## Layered Architecture

### Routers
- Parse request, validate input, extract identity from JWT
- Call one service method
- Return the service result as a typed Pydantic response
- **Never** contain business logic or direct DB calls

### Services
- Contain all business logic
- Raise domain exceptions (`NotFoundError`, `DuplicateEmailError`)
- **Never** import `fastapi`, `Request`, or `Response`
- Stateless — dependencies injected via constructor

### Repositories
- Thin wrappers around Supabase table operations
- One repository per database table
- Return dicts or domain models
- **Never** raise HTTP exceptions
- **Never** build raw SQL strings — use Supabase query builder

---

## Services Reference

### `AuthService`
- `register(email, password)` — hash password, insert user, return JWT
- `login(email, password)` — verify bcrypt hash, return JWT
- `get_current_user(token)` — decode JWT, return user dict

### `JobService`
- `list_jobs(filters, page, per_page)` — paginated Silver table query
- `get_job(job_id)` — single record lookup
- `save_job(user_id, job_id)` — upsert into saved_jobs
- `unsave_job(user_id, job_id)` — delete from saved_jobs
- `_resolve_candidate_id(user_id)` — converts auth user ID → candidate profile ID

### `CandidateService`
- `get_profile(user_id)` — fetch candidate_profiles by user_id
- `create_profile(user_id, data)` — insert profile, compute completeness, generate embedding
- `update_profile(user_id, data)` — merge + update, recompute completeness, regenerate embedding
- `upload_cv(user_id, file)` — save file, insert cv_documents row, trigger async parsing
- `_update_embedding(profile)` — calls `ai_services.embedding.generate_embedding()`, stores result

### `RecommendationService`
- Resolves candidate by profile ID or user ID (fallback)
- Generates query embedding from skills text
- Calls `JobRepository.match_by_embedding()` (pgvector RPC)
- Re-scores with `ai_services.matching.scorer.compute_match_score()`
- Generates explanations via `ai_services.matching.explainer`
- Logs to `recommendation_history`
- Returns cached response if Redis hit

### `SearchService`
- Embeds the natural language query string
- Calls `semantic_search_jobs()` SQL function (Gold table)
- Returns results cached in Redis (5 min TTL)

### `SkillGapService`
- Resolves candidate profile
- Aggregates `tech_stack` from top matching jobs (pgvector)
- Returns frequency-ranked list of missing skills

---

## Authentication

- **Algorithm:** HS256 (HMAC-SHA256)
- **Token TTL:** 60 minutes (configurable via `JWT_EXPIRE_MINUTES`)
- **Token payload:** `{"sub": user_id, "role": "candidate"|"admin", "exp": ...}`
- **Header:** `Authorization: Bearer <token>`

**Dependency injection:**
```python
# Any route that requires auth
current_user = Depends(get_current_user)

# Admin-only routes
current_user = Depends(require_role("admin"))
```

**Guards** — `get_current_user` validates signature, expiry, and looks up the user in the DB. Returns the user dict for downstream services.

---

## Error Handling

All errors return:
```json
{ "detail": "Human-readable message", "code": "ERROR_CODE" }
```

| HTTP Code | When |
|---|---|
| 400 | Validation error |
| 401 | Missing or invalid JWT |
| 403 | Insufficient role |
| 404 | Resource not found |
| 409 | Duplicate (email, profile, etc.) |
| 429 | Rate limited |
| 500 | Unexpected server error |

A global exception handler in `main.py` catches all `AppError` subclasses and maps them to the correct HTTP code. Unhandled exceptions return 500.

---

## Middleware Stack (execution order)

1. **Request ID** — injects `X-Request-ID` header for tracing
2. **Rate Limit** — blocks excessive requests per IP
3. **CORS** — restricts to configured origins
4. **JWT Auth** — applied per-route via `Depends()`, not globally

---

## Configuration

All settings in `api/core/config.py` via Pydantic `BaseSettings`. Values come from environment variables — never hardcode.

```python
from api.core.config import get_settings
settings = get_settings()
settings.supabase_url   # accessed via dependency, not directly
```

`get_settings()` is cached with `@lru_cache` — only one instance created per process.

---

## API Endpoints

### Auth
```
POST   /api/v1/auth/register     Create user account
POST   /api/v1/auth/login        Get JWT token
GET    /api/v1/auth/me           Current user profile
```

### Jobs
```
GET    /api/v1/jobs                     List jobs (paginated, filterable)
GET    /api/v1/jobs/{id}                Job detail
POST   /api/v1/jobs/{id}/save           Save a job          [auth]
DELETE /api/v1/jobs/{id}/save           Unsave a job        [auth]
```

### Candidates
```
GET    /api/v1/candidates/profile       Get own profile     [auth]
POST   /api/v1/candidates/profile       Create profile      [auth]
PUT    /api/v1/candidates/profile       Update profile      [auth]
POST   /api/v1/candidates/cv            Upload CV           [auth]
GET    /api/v1/candidates/saved-jobs    Saved jobs list     [auth]
```

### AI
```
POST   /api/v1/recommendations                        Get recommendations   [auth]
GET    /api/v1/candidates/{id}/skill-gap              Skill gap analysis    [auth]
GET    /api/v1/search?q=...                           Semantic search       [auth]
```

### Ops
```
GET    /api/v1/health    Liveness probe (no auth)
```

---

## Pagination

All list endpoints support:
```
?page=1&per_page=20
```

Response shape:
```json
{
  "items": [...],
  "total": 1256,
  "page": 1,
  "per_page": 20,
  "pages": 63
}
```

Full Swagger documentation available at `http://localhost:8000/docs`.
