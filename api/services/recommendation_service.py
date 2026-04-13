"""Core recommendation service.

Handles the full recommendation flow: candidate lookup → embedding generation
→ pgvector similarity search → multi-signal scoring → explainability → caching.
"""

import logging
import time
from uuid import UUID

from api.models.schemas import (
    JobOfferMatch,
    RecommendationFilters,
    RecommendationMeta,
    RecommendationResponse,
)
from api.repositories.candidate_repository import CandidateRepository
from api.repositories.job_repository import JobRepository
from api.services.redis_service import get_cached, set_cached
from ai_services.embedding.generator import generate_embedding
from ai_services.matching.scorer import compute_match_score
from ai_services.matching.explainer import generate_explanation

logger = logging.getLogger(__name__)


async def get_recommendations(
    candidate_repo: CandidateRepository,
    job_repo: JobRepository,
    candidate_id: UUID,
    top_n: int = 10,
    min_score: float = 0.40,
    filters: RecommendationFilters | None = None,
    model_name: str = "all-MiniLM-L6-v2",
) -> RecommendationResponse:
    """Generate job recommendations for a candidate.

    Flow:
    1. Check Redis cache
    2. Fetch candidate profile via CandidateRepository
    3. Generate embedding from skills text (ai_services)
    4. Call match_job_offers() via JobRepository (pgvector)
    5. Re-score with multi-signal scorer (skill overlap, seniority, location)
    6. Generate human-readable explanations
    7. Cache result in Redis (TTL 1h)
    8. Return response with latency

    Args:
        candidate_repo: CandidateRepository instance.
        job_repo: JobRepository instance.
        candidate_id: UUID of the candidate profile.
        top_n: Maximum number of recommendations.
        min_score: Minimum composite score threshold.
        filters: Optional contract/location filters.
        model_name: Sentence-BERT model for embeddings (informational).

    Returns:
        RecommendationResponse with matched offers, metadata, and timing.

    Raises:
        ValueError: If candidate not found or has no skills.
    """
    start_time = time.time()

    # 1. Check cache
    cache_key = f"rec:{candidate_id}"
    cached = await get_cached(cache_key)
    if cached:
        latency = int((time.time() - start_time) * 1000)
        cached["latency_ms"] = latency
        cached["meta"]["cached"] = True
        return RecommendationResponse(**cached)

    # 2. Get candidate profile via repository
    #    Try by profile ID first, then by auth user_id (frontend sends user.id)
    candidate = candidate_repo.find_by_id(str(candidate_id))
    if not candidate:
        candidate = candidate_repo.find_by_user_id(str(candidate_id))
    if not candidate:
        logger.warning("Candidate not found for id=%s", candidate_id)
        return RecommendationResponse(
            data=[],
            total=0,
            latency_ms=int((time.time() - start_time) * 1000),
            meta=RecommendationMeta(model=model_name, threshold=min_score, cached=False),
        )

    skills: list[str] = candidate.get("skills") or []
    if not skills:
        logger.warning("Candidate %s has no skills — returning empty recommendations", candidate_id)
        return RecommendationResponse(
            data=[],
            total=0,
            latency_ms=int((time.time() - start_time) * 1000),
            meta=RecommendationMeta(model=model_name, threshold=min_score, cached=False),
        )

    candidate_title = candidate.get("title") or candidate.get("current_title") or ""
    candidate_years = candidate.get("experience_years")
    candidate_location = candidate.get("location") or ""

    # 3. Build text and generate embedding (ai_services)
    skills_text = ", ".join(skills)
    embedding_text = f"{candidate_title}. Skills: {skills_text}" if candidate_title else f"Skills: {skills_text}"

    logger.info(
        "[REC] candidate=%s | title=%s | skills=%d | location=%s",
        candidate_id, candidate_title, len(skills), candidate_location,
    )

    try:
        query_embedding = generate_embedding(embedding_text)
    except Exception as exc:
        logger.error("[REC] Embedding generation failed: %s", exc, exc_info=True)
        return RecommendationResponse(
            data=[],
            total=0,
            latency_ms=int((time.time() - start_time) * 1000),
            meta=RecommendationMeta(model=model_name, threshold=min_score, cached=False),
        )

    # 4. Similarity search via repository (cast a wider net for re-scoring)
    try:
        raw_matches = job_repo.match_by_embedding(
            query_embedding=query_embedding,
            match_threshold=0.30,
            match_count=top_n * 3,
            filter_contract=filters.contract_type if filters else None,
            filter_location=filters.location if filters else None,
        )
    except Exception as exc:
        logger.error("[REC] pgvector match_by_embedding failed: %s", exc, exc_info=True)
        raw_matches = []

    logger.info("[REC] pgvector returned %d raw matches", len(raw_matches))

    # 5. Re-score with multi-signal scorer + generate explanations
    scored_matches: list[tuple[dict, dict, dict]] = []
    _debug_logged = 0

    for match in raw_matches:
        job_skills = match.get("tech_stack") or []
        embedding_sim = match.get("similarity", 0.0)

        score_result = compute_match_score(
            embedding_similarity=embedding_sim,
            candidate_skills=skills,
            job_skills=job_skills,
            candidate_years=candidate_years,
            job_min_years=None,
            candidate_location=candidate_location,
            job_location=match.get("location"),
        )

        if _debug_logged < 3:
            logger.info(
                "[REC] score for '%s': total=%.3f | skill=%.3f | emb=%.3f | sen=%.3f | loc=%.3f | job_skills=%s",
                match.get("title", "?"), score_result["total_score"],
                score_result["score_breakdown"]["skill_overlap"],
                score_result["score_breakdown"]["embedding_similarity"],
                score_result["score_breakdown"]["seniority_alignment"],
                score_result["score_breakdown"]["location_preference"],
                job_skills[:5],
            )
            _debug_logged += 1

        if score_result["total_score"] >= min_score:
            explanation = generate_explanation(
                matched_skills=score_result["matched_skills"],
                missing_skills=score_result["missing_skills"],
                score_breakdown=score_result["score_breakdown"],
                job_title=match.get("title", ""),
                total_score=score_result["total_score"],
            )
            scored_matches.append((match, score_result, explanation))

    # Sort by composite score descending and take top_n
    scored_matches.sort(key=lambda x: x[1]["total_score"], reverse=True)
    scored_matches = scored_matches[:top_n]

    # 6. Build response
    matches: list[JobOfferMatch] = []
    for match, score_result, explanation in scored_matches:
        matches.append(JobOfferMatch(
            offer_id=match["offer_id"],
            title=match["title"],
            company=match.get("company"),
            location=match.get("location"),
            contract_type=match.get("contract_type"),
            similarity_score=score_result["total_score"],
            matched_skills=score_result["matched_skills"],
            missing_skills=score_result["missing_skills"],
            score_breakdown=score_result["score_breakdown"],
            explanation_text=explanation["explanation_text"],
            tech_stack=match.get("tech_stack") or [],
        ))

    latency_ms = int((time.time() - start_time) * 1000)

    response = RecommendationResponse(
        data=matches,
        total=len(matches),
        latency_ms=latency_ms,
        meta=RecommendationMeta(
            model=model_name,
            threshold=min_score,
            cached=False,
        ),
    )

    # 7. Cache result (use mode="python" so field names stay as Python attrs)
    await set_cached(cache_key, response.model_dump())

    # 8. Log recommendation history (best-effort)
    # Use the actual candidate_profiles.id (not the auth user.id)
    profile_id = candidate.get("id", str(candidate_id))
    history_rows = [
        {
            "offer_id": str(m.offer_id),
            "similarity_score": m.similarity_score,
            "score_breakdown": m.score_breakdown,
        }
        for m in matches
    ]
    job_repo.log_recommendation_history(str(profile_id), history_rows)

    logger.info(
        "Generated %d recommendations for candidate %s in %dms",
        len(matches), candidate_id, latency_ms,
    )

    return response
