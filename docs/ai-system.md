# AI System

## Overview

The AI system lives in `ai_services/` and is consumed directly by backend services via Python import.
No separate AI API. No external model API calls (fully self-hosted).

**Three modules:**

| Module | File | Purpose |
|---|---|---|
| Embedding | `ai_services/embedding/generator.py` | Generate 384-dim vectors |
| Matching | `ai_services/matching/scorer.py` | Multi-signal composite scoring |
| Explainability | `ai_services/matching/explainer.py` | Human-readable match explanation |
| Skill Gap | `ai_services/matching/skill_gap.py` | Missing skill analysis |

---

## Embeddings

**Model:** `all-MiniLM-L6-v2` (Sentence-BERT, 384 dimensions)

**Job embedding input:**
```
"{title}. {description}. Skills: {tech_stack_joined}"
```

**Candidate embedding input:**
```
"{title}. Skills: {skills_joined}"
```

**When generated:**
- **Jobs** — during Gold ETL enrichment stage (Airflow DAG)
- **Candidates** — on profile `create` and `update` (auto-generated in `CandidateService`)

**Storage:**
- `dw_job_offers.embedding` — `vector(384)` with HNSW index
- `candidate_profiles.embedding` — `vector(384)` with HNSW index

**Search:**
- pgvector `<=>` operator (cosine distance) via `match_job_offers()` SQL RPC
- HNSW index parameters: default `m=16, ef_construction=64`
- Base similarity threshold: `0.30` (pre-filter before re-scoring)

**Caching:**
- Embeddings for job search cached in Redis (TTL 5 min)
- Recommendation results cached in Redis (TTL 1h)

---

## Matching — Multi-Signal Scorer

Every pgvector result is **re-scored** with 4 signals combined into a composite score.

### Score Formula

$$\text{score} = 0.5 \cdot \text{skill\_overlap} + 0.3 \cdot \text{embedding\_sim} + 0.1 \cdot \text{seniority} + 0.1 \cdot \text{location}$$

### Signal Details

#### 1. Skill Overlap (weight 0.5)
- Compares candidate `skills[]` vs job `tech_stack[]`
- **Fuzzy matching** — not pure exact string equality:
  - Lowercase + strip trailing version numbers (`"python 3"` → `"python"`)
  - Substring match (`"nlp"` matches `"nlp engineer"`)
  - Separator-split (`"python/django"` → checks `"python"` and `"django"` separately)
- Score = `matched_count / len(job_skills)` — ranges 0.0 → 1.0
- If job has no skills listed: score defaults to `1.0`

#### 2. Embedding Similarity (weight 0.3)
- Raw cosine similarity from pgvector (`1 - cosine_distance`)
- Pre-filtered at threshold `0.30` before re-scoring
- Captures semantic proximity even when exact skill terms differ

#### 3. Seniority Alignment (weight 0.1)
- Compares `candidate.experience_years` vs `job.min_years`
- If candidate meets or exceeds requirement: `1.0`
- Each year below requirement: `-0.2` (capped at `0.0`)
- If either value is `NULL`: defaults to `0.5`

#### 4. Location Match (weight 0.1)
- Substring match (case-insensitive): `"paris"` in `"Paris, Île-de-France"` → `1.0`
- No match → `0.0`
- Either value missing → `0.5`

### Default Threshold
- Minimum composite score to include in results: **0.20**
- Frontend can override via `min_score` in the request body

---

## Explainability

Every recommendation includes a human-readable explanation:

```json
{
  "similarity_score": 0.73,
  "matched_skills": ["python", "spark", "kafka"],
  "missing_skills": ["scala", "airflow"],
  "score_breakdown": {
    "skill_overlap": 0.60,
    "embedding_similarity": 0.61,
    "seniority_alignment": 1.00,
    "location_preference": 0.50
  }
}
```

**Matched/missing calculation** uses the same fuzzy matching as the scorer — no separate lookup.

---

## Skill Gap Analysis

**Endpoint:** `GET /api/v1/candidates/{id}/skill-gap?top_n=10`

**Flow:**
1. Fetch candidate profile → extract `skills[]`
2. Embed candidate skills text
3. Run pgvector search to find top matching job offers
4. Aggregate `tech_stack` across those offers
5. Compute frequency of each skill in top results
6. Return skills the candidate lacks, ranked by market frequency

**Output:**
```json
{
  "candidate_skills": ["python", "spark"],
  "gap_skills": [
    { "skill": "scala", "frequency": 0.72, "priority": "high" },
    { "skill": "airflow", "frequency": 0.61, "priority": "high" },
    { "skill": "kubernetes", "frequency": 0.44, "priority": "medium" }
  ],
  "coverage_score": 0.38
}
```

---

## Semantic Search

**Endpoint:** `GET /api/v1/search?q=...`

**Flow:**
1. Embed the user's natural language query
2. Call `semantic_search_jobs()` SQL function (Gold table, pgvector)
3. Return ranked results with similarity scores

**SQL function:** `semantic_search_jobs(query_embedding, match_threshold, match_count, filter_contract, filter_location)`

This is distinct from the standard job listing — it returns results ordered purely by semantic similarity to the query, not by date.

---

## CV Parser (Enrichment)

**Files:** `ai_services/cv_parser/extractor.py`, `ai_services/cv_parser/enrichment.py`

**Supported formats:** PDF (via PyPDF2), DOCX (via python-docx)

**Pipeline:**
1. Extract raw text from file
2. Run spaCy NLP pipeline to extract:
   - Skills and technologies
   - Years of experience
   - Education level
3. Merge with existing candidate profile:
   - Skills: **union** (never overwrite, only add)
   - Experience years: **keep maximum**
   - Education: append

**Parsing is async** — upload returns immediately, parsing runs in background.
Parsing status stored in `cv_documents.parsing_status` (`pending` → `processing` → `success` / `failed`).

---

## Recommendation History

Every recommendation request logs results to `recommendation_history`:

| Column | Description |
|---|---|
| `candidate_id` | FK → candidate_profiles.id (resolved profile ID, not auth user ID) |
| `job_offer_id` | FK → job_offers.id |
| `similarity_score` | Composite score |
| `score_breakdown` | JSONB with all 4 signal scores |
| `action` | `shown` · `clicked` · `saved` · `dismissed` |

Used for future click-through rate analysis and model feedback loops.
