"""NLP enrichment of CV text — skill, experience, and education extraction.

Uses spaCy with pattern matching + NER for French CVs.
"""

import logging
import re

import spacy

logger = logging.getLogger(__name__)

_nlp = None


def _get_nlp(model_name: str = "fr_core_news_md"):
    """Load and cache the spaCy model.

    Args:
        model_name: spaCy model identifier.

    Returns:
        The loaded spaCy Language model.
    """
    global _nlp
    if _nlp is None:
        logger.info("Loading spaCy model: %s", model_name)
        _nlp = spacy.load(model_name)
    return _nlp


def extract_skills(text: str, skill_dictionary: list[str] | None = None) -> list[str]:
    """Extract skills from CV text using NER + pattern matching.

    Args:
        text: Raw CV text.
        skill_dictionary: Optional canonical list of known skills.

    Returns:
        Deduplicated sorted list of skills.
    """
    skills = set()

    if skill_dictionary:
        text_lower = text.lower()
        for skill in skill_dictionary:
            if skill.lower() in text_lower:
                skills.add(skill)

    nlp = _get_nlp()
    doc = nlp(text)
    for ent in doc.ents:
        if ent.label_ in ("ORG", "PRODUCT", "MISC"):
            skills.add(ent.text.strip())

    return sorted(skills)


def extract_experience(text: str) -> str | None:
    """Extract experience summary from CV text.

    Args:
        text: Raw CV text.

    Returns:
        Experience description string or None.
    """
    patterns = [
        r"(\d+)\s*(?:ans?|years?)\s*(?:d['\u2019]exp[ée]rience|experience)",
        r"(?:exp[ée]rience|experience)\s*(?:professionnelle)?\s*[:\-]?\s*(\d+)\s*(?:ans?|years?)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            years = match.group(1)
            return f"{years} years of experience"
    return None


def extract_education(text: str) -> str | None:
    """Extract education level from CV text.

    Args:
        text: Raw CV text.

    Returns:
        Education level string or None.
    """
    education_patterns = [
        (r"(?:bac\s*\+\s*5|master|ingénieur|mba)", "Bac+5"),
        (r"(?:bac\s*\+\s*4|maîtrise)", "Bac+4"),
        (r"(?:bac\s*\+\s*3|licence|bachelor)", "Bac+3"),
        (r"(?:bac\s*\+\s*2|bts|dut|deug)", "Bac+2"),
        (r"(?:baccalauréat|bac\b)", "Bac"),
        (r"(?:doctorat|phd|ph\.d)", "Doctorat"),
    ]
    for pattern, level in education_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return level
    return None


def parse_cv(text: str, skill_dictionary: list[str] | None = None) -> dict:
    """Full CV parsing pipeline: skills + experience + education.

    Args:
        text: Raw CV text.
        skill_dictionary: Optional canonical skill list.

    Returns:
        Dict with keys: skills, experience, education.
    """
    return {
        "skills": extract_skills(text, skill_dictionary),
        "experience": extract_experience(text),
        "education": extract_education(text),
    }
