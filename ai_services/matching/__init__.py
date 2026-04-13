"""Matching engine — scorer, explainer, skill gap analysis."""

from ai_services.matching.scorer import compute_match_score
from ai_services.matching.explainer import generate_explanation
from ai_services.matching.skill_gap import analyze_skill_gap

__all__ = ["compute_match_score", "generate_explanation", "analyze_skill_gap"]
