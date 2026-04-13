"""Skill gap analysis service.

Combines recommendation data with skill gap analysis to identify
the most important skills a candidate should acquire.
"""

import logging
import time
from uuid import UUID

from api.repositories.candidate_repository import CandidateRepository
from api.repositories.job_repository import JobRepository
from api.services.redis_service import get_cached, set_cached
from ai_services.embedding.generator import generate_embedding
from ai_services.matching.skill_gap import analyze_skill_gap

logger = logging.getLogger(__name__)


async def get_skill_gap(
    candidate_repo: CandidateRepository,
    job_repo: JobRepository,
    candidate_id: UUID,
    top_n_skills: int = 10,
    job_count: int = 30,
) -> dict:
    """Compute a skill gap report for a candidate.

    Fetches the candidate's profile, finds similar jobs via embedding,
    then aggregates missing skills across those jobs.

    Args:
        candidate_repo: CandidateRepository instance.
        job_repo: JobRepository instance.
        candidate_id: UUID of the candidate.
        top_n_skills: Number of top missing skills to return.
        job_count: Number of similar jobs to consider.

    Returns:
        Dict with candidate_skills, top_missing_skills, skill_frequency,
        improvement_potential, and latency_ms.

    Raises:
        ValueError: If candidate not found or has no skills.
    """
    start_time = time.time()

    # Check cache
    cache_key = f"skill_gap:{candidate_id}"
    cached = await get_cached(cache_key)
    if cached:
        latency = int((time.time() - start_time) * 1000)
        cached["latency_ms"] = latency
        return cached

    # Fetch candidate (try profile ID, then auth user_id)
    candidate = candidate_repo.find_by_id(str(candidate_id))
    if not candidate:
        candidate = candidate_repo.find_by_user_id(str(candidate_id))
    if not candidate:
        logger.warning("[SKILL_GAP] Candidate not found for id=%s", candidate_id)
        return {
            "candidate_skills": [],
            "top_missing_skills": [],
            "skill_frequency": {},
            "improvement_potential": {},
            "latency_ms": int((time.time() - start_time) * 1000),
        }

    skills: list[str] = candidate.get("skills") or []
    if not skills:
        logger.warning("[SKILL_GAP] Candidate %s has no skills", candidate_id)
        return {
            "candidate_skills": [],
            "top_missing_skills": [],
            "skill_frequency": {},
            "improvement_potential": {},
            "latency_ms": int((time.time() - start_time) * 1000),
        }

    # Generate embedding
    title = candidate.get("title") or candidate.get("current_title") or ""
    skills_text = ", ".join(skills)
    embedding_text = f"{title}. Skills: {skills_text}" if title else f"Skills: {skills_text}"

    try:
        query_embedding = generate_embedding(embedding_text)
    except Exception as exc:
        logger.error("[SKILL_GAP] Embedding generation failed: %s", exc, exc_info=True)
        return {
            "candidate_skills": sorted(s.lower() for s in skills),
            "top_missing_skills": [],
            "skill_frequency": {},
            "improvement_potential": {},
            "latency_ms": int((time.time() - start_time) * 1000),
        }

    # Get similar jobs
    try:
        raw_matches = job_repo.match_by_embedding(
            query_embedding=query_embedding,
            match_threshold=0.25,
            match_count=job_count,
        )
    except Exception as exc:
        logger.error("[SKILL_GAP] pgvector search failed: %s", exc, exc_info=True)
        raw_matches = []

    logger.info("[SKILL_GAP] candidate=%s | skills=%d | matches=%d", candidate_id, len(skills), len(raw_matches))

    # Run skill gap analysis
    gap_result = analyze_skill_gap(
        candidate_skills=skills,
        recommended_jobs=raw_matches,
        top_n=top_n_skills,
    )

    latency_ms = int((time.time() - start_time) * 1000)
    gap_result["latency_ms"] = latency_ms

    # Cache for 30 minutes
    await set_cached(cache_key, gap_result, ttl=1800)

    logger.info(
        "Skill gap analysis for candidate %s: %d missing skills in %dms",
        candidate_id, len(gap_result["top_missing_skills"]), latency_ms,
    )

    return gap_result
