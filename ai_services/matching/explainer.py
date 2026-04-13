"""Human-readable explanation generator for job-candidate matches.

Takes the raw score breakdown and produces a structured explanation
with an `explanation_text` summary sentence.
"""


def generate_explanation(
    matched_skills: list[str],
    missing_skills: list[str],
    score_breakdown: dict[str, float],
    job_title: str,
    total_score: float,
) -> dict:
    """Generate a human-readable explanation for a match.

    Args:
        matched_skills: Skills present in both candidate and job.
        missing_skills: Job skills the candidate lacks.
        score_breakdown: Breakdown of composite score components.
        job_title: Title of the matched job.
        total_score: Overall composite score (0-1).

    Returns:
        Dict with matched_skills, missing_skills, score_breakdown,
        and explanation_text.
    """
    parts: list[str] = []

    pct = int(total_score * 100)
    parts.append(f"You are a {pct}% match for {job_title}.")

    skill_score = score_breakdown.get("skill_overlap", 0)
    if skill_score >= 0.8:
        parts.append(f"You match {len(matched_skills)} of the required skills.")
    elif skill_score >= 0.5:
        parts.append(
            f"You match {len(matched_skills)} skills but are missing "
            f"{len(missing_skills)}."
        )
    elif missing_skills:
        parts.append(
            f"Consider learning {', '.join(missing_skills[:3])} to improve your fit."
        )

    seniority_score = score_breakdown.get("seniority_alignment", 0)
    if seniority_score >= 0.8:
        parts.append("Your experience level is a strong fit.")
    elif seniority_score < 0.5:
        parts.append("The role may require more experience than you currently have.")

    location_score = score_breakdown.get("location_preference", 0)
    if location_score >= 1.0:
        parts.append("Location matches your preference.")
    elif location_score <= 0.0:
        parts.append("This role is in a different location than you prefer.")

    return {
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "score_breakdown": score_breakdown,
        "explanation_text": " ".join(parts),
    }
