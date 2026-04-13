"""Rule-based job taxonomy classifier.

Classifies job offers into predefined categories based on title
and description pattern matching.
"""

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

# ── Taxonomy rules ───────────────────────────────────────────────────────────
# Ordered by specificity: most specific patterns first.
_TAXONOMY_RULES: list[tuple[str, list[re.Pattern[str]]]] = [
    ("MLOps", [
        re.compile(r"\bmlops\b", re.I),
        re.compile(r"\bml\s*ops\b", re.I),
        re.compile(r"\bmachine\s*learning\s*ops", re.I),
    ]),
    ("ML Engineering", [
        re.compile(r"\bml\s*eng", re.I),
        re.compile(r"\bmachine\s*learning\s*eng", re.I),
        re.compile(r"\bdeep\s*learning\s*eng", re.I),
        re.compile(r"\bai\s*eng", re.I),
    ]),
    ("Data Science", [
        re.compile(r"\bdata\s*scien", re.I),
        re.compile(r"\bscientifique\s*de\s*donn", re.I),
        re.compile(r"\bnlp\s*(eng|scien|research)", re.I),
        re.compile(r"\bcomputer\s*vision\s*(eng|scien|research)", re.I),
    ]),
    ("Data Engineering", [
        re.compile(r"\bdata\s*eng", re.I),
        re.compile(r"\bing[ée]nieur\s*de?\s*donn", re.I),
        re.compile(r"\betl\b", re.I),
        re.compile(r"\bdata\s*platform", re.I),
        re.compile(r"\bdata\s*infra", re.I),
    ]),
    ("Analytics", [
        re.compile(r"\bdata\s*analy", re.I),
        re.compile(r"\banalyste?\s*de?\s*donn", re.I),
        re.compile(r"\banalytics\s*eng", re.I),
        re.compile(r"\bquanti", re.I),
    ]),
    ("BI", [
        re.compile(r"\bbi\s*(analyst|eng|dev|consult)", re.I),
        re.compile(r"\bbusiness\s*intelligence", re.I),
        re.compile(r"\bpower\s*bi\b", re.I),
        re.compile(r"\btableau\b", re.I),
        re.compile(r"\blooker\b", re.I),
    ]),
    ("Data Management", [
        re.compile(r"\bdata\s*arch", re.I),
        re.compile(r"\bdata\s*govern", re.I),
        re.compile(r"\bdata\s*steward", re.I),
        re.compile(r"\bdata\s*quality", re.I),
        re.compile(r"\bdata\s*manag", re.I),
        re.compile(r"\bmaster\s*data", re.I),
    ]),
]


def classify_job(title: str, description: str = "") -> str:
    """Classify a job offer into a taxonomy category.

    Rules are evaluated in order from most specific to least specific.
    The title is checked first; if no match, the first 2000 chars of
    the description are checked.

    Args:
        title: Job title.
        description: Job description text.

    Returns:
        Category string, one of: MLOps, ML Engineering, Data Science,
        Data Engineering, Analytics, BI, Data Management, Other.
    """
    if not title:
        return "Other"

    for category, patterns in _TAXONOMY_RULES:
        for pattern in patterns:
            if pattern.search(title):
                return category

    # Fallback: check description
    desc_snippet = (description or "")[:2000]
    if desc_snippet:
        for category, patterns in _TAXONOMY_RULES:
            for pattern in patterns:
                if pattern.search(desc_snippet):
                    return category

    return "Other"


def get_all_categories() -> list[str]:
    """Return all taxonomy category names.

    Returns:
        Ordered list of category strings.
    """
    return [cat for cat, _ in _TAXONOMY_RULES] + ["Other"]
