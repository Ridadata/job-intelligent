"""Skill normalization against a canonical dictionary.

Maps skill aliases (e.g. "sklearn" → "scikit-learn", "tf" → "tensorflow")
to their canonical form before storage.
"""

import json
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

# ── Lazy-loaded canonical mapping ────────────────────────────────────────────
_CANONICAL_MAP: Optional[dict[str, str]] = None
_CANONICAL_PATH = os.path.join(os.path.dirname(__file__), "skills_canonical.json")


def _load_canonical_map() -> dict[str, str]:
    """Load the canonical skill dictionary and build a reverse lookup.

    Returns:
        Dict mapping every known alias (lowercase) → canonical skill name.
    """
    global _CANONICAL_MAP
    if _CANONICAL_MAP is not None:
        return _CANONICAL_MAP

    with open(_CANONICAL_PATH, encoding="utf-8") as f:
        raw = json.load(f)

    mapping: dict[str, str] = {}

    for canonical, aliases in raw.items():
        if canonical.startswith("_"):
            continue  # skip metadata keys
        canonical_lower = canonical.lower()
        mapping[canonical_lower] = canonical_lower
        for alias in aliases:
            mapping[alias.lower()] = canonical_lower

    _CANONICAL_MAP = mapping
    logger.info("Loaded canonical skill map: %d entries", len(mapping))
    return mapping


def normalize_skill(skill: str) -> str:
    """Normalize a single skill to its canonical form.

    Args:
        skill: A raw skill string (e.g. "sklearn", "TensorFlow", "tf").

    Returns:
        The canonical skill name (lowercase), or the original lowercased
        skill if no mapping exists.
    """
    mapping = _load_canonical_map()
    return mapping.get(skill.lower().strip(), skill.lower().strip())


def normalize_skills(skills: list[str]) -> list[str]:
    """Normalize a list of skills, deduplicating after normalization.

    Args:
        skills: List of raw skill strings.

    Returns:
        Sorted, deduplicated list of canonical skill names.
    """
    normalized = {normalize_skill(s) for s in skills if s}
    return sorted(normalized)


def get_canonical_skills() -> set[str]:
    """Return the set of all canonical skill names.

    Returns:
        Set of canonical skill strings (lowercase).
    """
    mapping = _load_canonical_map()
    return set(mapping.values())


def reset_cache() -> None:
    """Reset the cached canonical map (useful for testing).

    Returns:
        None.
    """
    global _CANONICAL_MAP
    _CANONICAL_MAP = None
