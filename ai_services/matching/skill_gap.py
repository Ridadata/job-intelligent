"""Skill gap analysis for candidates.

Analyzes recommended jobs to identify the most in-demand skills
a candidate is missing.
"""

from collections import Counter


def analyze_skill_gap(
    candidate_skills: list[str],
    recommended_jobs: list[dict],
    top_n: int = 10,
) -> dict:
    """Compute skill gap analysis across recommended jobs.

    Args:
        candidate_skills: Current candidate skills (lowercased internally).
        recommended_jobs: List of job dicts, each with a 'tech_stack' or
            'required_skills' field (list of strings).
        top_n: Number of top missing skills to return.

    Returns:
        Dict with candidate_skills, top_missing_skills, skill_frequency,
        and improvement_potential.
    """
    cand_set = {s.lower() for s in candidate_skills}
    missing_counter: Counter[str] = Counter()

    for job in recommended_jobs:
        job_skills = job.get("tech_stack") or job.get("required_skills") or []
        for skill in job_skills:
            normalized = skill.lower()
            if normalized not in cand_set:
                missing_counter[normalized] += 1

    top_missing = missing_counter.most_common(top_n)

    total_job_count = len(recommended_jobs) if recommended_jobs else 1
    improvement_potential = {}
    for skill, count in top_missing:
        improvement_potential[skill] = round(count / total_job_count, 2)

    return {
        "candidate_skills": sorted(cand_set),
        "top_missing_skills": [skill for skill, _ in top_missing],
        "skill_frequency": dict(top_missing),
        "improvement_potential": improvement_potential,
    }
