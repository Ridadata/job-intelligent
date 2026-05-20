# API Reference

Base URL (local): `http://localhost:8000`
Interactive docs: `http://localhost:8000/docs` (Swagger UI) · `http://localhost:8000/redoc` (ReDoc)

All endpoints are prefixed with `/api/v1`.

## Authentication

The API uses JWT Bearer tokens (HS256). Obtain a token via `POST /api/v1/auth/login`, then send it as:

```http
Authorization: Bearer <token>
```

Tokens expire after the duration configured in `JWT_EXPIRE_MINUTES` (default 60 minutes).

## Standard Response Formats

### Single resource

```json
{ "id": "uuid", "title": "Data Engineer", "company": "Acme" }
```

### Paginated list

```json
{
  "items": [...],
  "total": 142,
  "page": 1,
  "per_page": 20,
  "pages": 8
}
```

### Error

```json
{ "detail": "Job not found", "code": "JOB_NOT_FOUND" }
```

## HTTP Status Codes

| Code | Meaning |
|---|---|
| 200 | Success (GET, PUT, PATCH) |
| 201 | Created (POST) |
| 204 | Deleted (DELETE) |
| 400 | Validation error |
| 401 | Not authenticated |
| 403 | Not authorized |
| 404 | Not found |
| 409 | Conflict (duplicate) |
| 429 | Rate limit exceeded |
| 500 | Internal server error |

## Rate Limiting

Default: **60 requests per minute per IP** for authenticated endpoints. Limits are enforced by middleware and return `429 Too Many Requests` when exceeded.

---

## Auth

### POST `/api/v1/auth/register`

Create a new candidate account.

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com","password":"strongpass123","full_name":"Alice"}'
```

**201 Created**

```json
{ "id": "uuid", "email": "alice@example.com", "role": "candidate" }
```

### POST `/api/v1/auth/login`

Exchange credentials for a JWT.

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com","password":"strongpass123"}'
```

**200 OK**

```json
{ "access_token": "eyJ...", "token_type": "bearer", "expires_in": 3600 }
```

### GET `/api/v1/auth/me`

Return the authenticated user.

---

## Jobs

### GET `/api/v1/jobs`

List or search jobs (paginated).

Query params: `q`, `location`, `contract_type`, `company`, `page`, `per_page`.

```bash
curl "http://localhost:8000/api/v1/jobs?q=data+engineer&location=Paris&page=1&per_page=20" \
  -H "Authorization: Bearer $TOKEN"
```

### GET `/api/v1/jobs/{id}`

Single job detail with full description and required skills.

### POST `/api/v1/jobs/{id}/save`

Bookmark a job for the authenticated candidate.

### DELETE `/api/v1/jobs/{id}/save`

Remove the bookmark.

---

## Candidates

### GET `/api/v1/candidates/profile`

Return the authenticated candidate's profile.

### POST `/api/v1/candidates/profile`

Create a profile.

```bash
curl -X POST http://localhost:8000/api/v1/candidates/profile \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Data Engineer",
    "skills": ["python","sql","airflow"],
    "experience_years": 3,
    "location": "Paris",
    "salary_expectation": 55000
  }'
```

### PUT `/api/v1/candidates/profile`

Update profile fields. Triggers candidate embedding regeneration.

### POST `/api/v1/candidates/cv`

Upload a CV (multipart/form-data, PDF or DOCX, max 5 MB). Parsing is asynchronous.

```bash
curl -X POST http://localhost:8000/api/v1/candidates/cv \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@./resume.pdf"
```

**202 Accepted**

```json
{ "cv_id": "uuid", "status": "pending" }
```

### GET `/api/v1/candidates/saved-jobs`

List saved jobs (paginated).

---

## Recommendations & AI

### POST `/api/v1/recommendations`

Get top-N scored job matches for the authenticated candidate.

```bash
curl -X POST http://localhost:8000/api/v1/recommendations \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"top_n": 10}'
```

**200 OK** — each item includes:

```json
{
  "job_id": "uuid",
  "title": "Senior Data Engineer",
  "company": "Acme",
  "score": 0.87,
  "matched_skills": ["python","sql","airflow"],
  "missing_skills": ["spark","kubernetes"],
  "score_breakdown": {
    "skill_overlap": 0.50,
    "embedding_similarity": 0.27,
    "seniority": 0.07,
    "location": 0.03
  }
}
```

Cached in Redis for 1 hour per candidate.

### GET `/api/v1/candidates/{id}/skill-gap`

Return skill-gap analysis: skills the candidate has, top in-demand skills missing, and recommended learning paths.

### GET `/api/v1/search?q=...`

Natural-language semantic search powered by pgvector cosine similarity.

```bash
curl "http://localhost:8000/api/v1/search?q=python+remote+startup" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Health

### GET `/health`

Liveness probe. Returns `{ "status": "ok" }` when the API is up.

### GET `/health/db`

Verifies the database connection.

---

## Admin (role: `admin`)

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/v1/admin/pipeline-runs` | ETL run history |
| POST | `/api/v1/admin/refresh-views` | Refresh materialized views |
| GET | `/api/v1/admin/stats` | Platform-wide metrics |

---

## Error Codes

| Code | HTTP | Meaning |
|---|---|---|
| `INVALID_CREDENTIALS` | 401 | Wrong email or password |
| `TOKEN_EXPIRED` | 401 | JWT expired |
| `INSUFFICIENT_PERMISSIONS` | 403 | Role does not allow operation |
| `JOB_NOT_FOUND` | 404 | Job ID does not exist |
| `CANDIDATE_NOT_FOUND` | 404 | Candidate profile missing |
| `DUPLICATE_EMAIL` | 409 | Email already registered |
| `CV_TOO_LARGE` | 400 | CV exceeds 5 MB |
| `UNSUPPORTED_FILE_TYPE` | 400 | CV is not PDF or DOCX |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |

---

## OpenAPI Schema

The full machine-readable schema is available at:

- JSON: `http://localhost:8000/openapi.json`
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
