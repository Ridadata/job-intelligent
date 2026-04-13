"""Job-candidate matching scorer with weighted multi-signal scoring.

Weights:
  - skill_overlap: 0.5
  - embedding_similarity: 0.3
  - seniority_alignment: 0.1
  - location_preference: 0.1
"""

import logging

logger = logging.getLogger(__name__)

WEIGHTS = {
    "skill_overlap": 0.5,
    "embedding_similarity": 0.3,
    "seniority_alignment": 0.1,
    "location_preference": 0.1,
}


def _normalize_skill(skill: str) -> str:
    """Normalize a skill string for fuzzy matching.

    Strips whitespace, lowercases, removes trailing version numbers.
    """
    s = skill.lower().strip()
    # Remove common separators: "python/django" → match both parts individually
    # Remove version suffixes: "python 3" → "python", "react 18" → "react"
    import re
    s = re.sub(r"\s*\d+(\.\d+)*$", "", s)  # strip trailing versions
    return s


def _fuzzy_skill_match(cand_skill: str, job_skill: str) -> bool:
    """Check if two skills match (exact, substring, or split on separators)."""
    c = _normalize_skill(cand_skill)
    j = _normalize_skill(job_skill)
    if c == j:
        return True
    # Substring: "python" in "python/django" or "data engineering" in "data engineering (etl)"
    if c in j or j in c:
        return True
    # Split on / and check parts: "python/django" → ["python", "django"]
    j_parts = {p.strip() for p in j.replace("/", ",").split(",") if p.strip()}
    if c in j_parts:
        return True
    c_parts = {p.strip() for p in c.replace("/", ",").split(",") if p.strip()}
    if j in c_parts:
        return True
    return False


def compute_skill_overlap(candidate_skills: list[str], job_skills: list[str]) -> float:
    """Compute the skill overlap ratio between candidate and job.

    Uses fuzzy matching: exact, substring, and separator-split comparison
    after normalizing (lowercase, strip versions).

    Args:
        candidate_skills: List of candidate skills.
        job_skills: List of required job skills.

    Returns:
        Overlap ratio between 0 and 1.
    """
    if not job_skills:
        return 1.0
    matched_count = 0
    matched_set: set[str] = set()
    for js in job_skills:
        for cs in candidate_skills:
            if _fuzzy_skill_match(cs, js):
                matched_count += 1
                matched_set.add(js.lower().strip())
                break
    return matched_count / len(job_skills)


def compute_seniority_alignment(candidate_years: int | None, job_min_years: int | None) -> float:
    """Compute seniority alignment score.

    Args:
        candidate_years: Candidate's years of experience.
        job_min_years: Job's minimum required years.

    Returns:
        Alignment score between 0 and 1.
    """
    if candidate_years is None or job_min_years is None:
        return 0.5
    diff = candidate_years - job_min_years
    if diff >= 0:
        return 1.0
    return max(0.0, 1.0 + diff * 0.2)


def compute_location_match(candidate_location: str | None, job_location: str | None) -> float:
    """Compute location preference match.

    Args:
        candidate_location: Candidate's preferred location.
        job_location: Job's location.

    Returns:
        1.0 if matching, 0.5 if either is None, 0.0 if mismatch.
    """
    if not candidate_location or not job_location:
        return 0.5
    if candidate_location.lower() in job_location.lower() or job_location.lower() in candidate_location.lower():
        return 1.0
    return 0.0


def compute_match_score(
    embedding_similarity: float,
    candidate_skills: list[str],
    job_skills: list[str],
    candidate_years: int | None = None,
    job_min_years: int | None = None,
    candidate_location: str | None = None,
    job_location: str | None = None,
) -> dict:
    """Compute the composite match score with full breakdown.

    Args:
        embedding_similarity: Cosine similarity from pgvector (0-1).
        candidate_skills: Candidate skill list.
        job_skills: Job required skills.
        candidate_years: Candidate experience years.
        job_min_years: Job min experience requirement.
        candidate_location: Candidate preferred location.
        job_location: Job location.

    Returns:
        Dict with total_score, matched_skills, missing_skills, score_breakdown.
    """
    skill_score = compute_skill_overlap(candidate_skills, job_skills)
    seniority_score = compute_seniority_alignment(candidate_years, job_min_years)
    location_score = compute_location_match(candidate_location, job_location)

    total = (
        WEIGHTS["skill_overlap"] * skill_score
        + WEIGHTS["embedding_similarity"] * embedding_similarity
        + WEIGHTS["seniority_alignment"] * seniority_score
        + WEIGHTS["location_preference"] * location_score
    )

    # Use fuzzy matching for matched/missing skill lists too
    matched_skills: list[str] = []
    missing_skills: list[str] = []
    for js in job_skills:
        found = any(_fuzzy_skill_match(cs, js) for cs in candidate_skills)
        if found:
            matched_skills.append(js.lower().strip())
        else:
            missing_skills.append(js.lower().strip())

    return {
        "total_score": round(total, 4),
        "matched_skills": sorted(set(matched_skills)),
        "missing_skills": sorted(set(missing_skills)),
        "score_breakdown": {
            "skill_overlap": round(skill_score, 4),
            "embedding_similarity": round(embedding_similarity, 4),
            "seniority_alignment": round(seniority_score, 4),
            "location_preference": round(location_score, 4),
        },
    }
