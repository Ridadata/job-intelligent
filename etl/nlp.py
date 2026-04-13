"""NLP utilities for job offer processing.

Handles skill extraction, contract normalization, seniority classification,
and title normalization using spaCy and pattern-based matching.
"""

import logging
import re
from typing import Optional

import spacy

from etl.config import settings

logger = logging.getLogger(__name__)

# ── Lazy-loaded spaCy model ─────────────────────────────────────────────────
_nlp: Optional[spacy.Language] = None


def _get_nlp() -> spacy.Language:
    """Load the spaCy model lazily.

    Returns:
        spacy.Language: The loaded spaCy model.
    """
    global _nlp
    if _nlp is None:
        logger.info("Loading spaCy model: %s", settings.spacy_model)
        _nlp = spacy.load(settings.spacy_model)
    return _nlp


# ── Tech skill dictionary ───────────────────────────────────────────────────
TECH_SKILLS: set[str] = {
    # Languages
    "python", "java", "javascript", "typescript", "scala", "r", "sql",
    "golang", "go", "rust", "c++", "c#", "ruby", "php", "kotlin", "swift",
    # Data & ML
    "pandas", "numpy", "scikit-learn", "sklearn", "tensorflow", "pytorch",
    "keras", "xgboost", "lightgbm", "spark", "pyspark", "hadoop", "hive",
    "dbt", "airflow", "luigi", "dagster", "prefect", "mlflow", "kubeflow",
    "huggingface", "transformers", "spacy", "nltk", "opencv",
    # Databases
    "postgresql", "postgres", "mysql", "mongodb", "redis", "elasticsearch",
    "cassandra", "neo4j", "snowflake", "bigquery", "redshift", "clickhouse",
    "supabase", "firebase",
    # Cloud & Infra
    "aws", "azure", "gcp", "docker", "kubernetes", "k8s", "terraform",
    "ansible", "jenkins", "gitlab-ci", "github-actions", "ci/cd",
    # BI & Viz
    "power bi", "powerbi", "tableau", "looker", "metabase", "grafana",
    "matplotlib", "seaborn", "plotly",
    # Data formats & tools
    "kafka", "rabbitmq", "api", "rest", "graphql", "fastapi", "flask",
    "django", "react", "next.js", "git", "linux", "excel", "sas", "spss",
    "databricks", "delta lake", "iceberg", "parquet", "avro",
    # Soft skills (data-relevant)
    "machine learning", "deep learning", "nlp", "computer vision",
    "data analysis", "data engineering", "data science", "statistics",
    "etl", "data modeling", "data warehouse", "data lake",
    "agile", "scrum",
}

# ── Contract type normalization map ──────────────────────────────────────────
CONTRACT_MAP: dict[str, str] = {
    "cdi": "CDI",
    "contrat à durée indéterminée": "CDI",
    "permanent": "CDI",
    "full-time": "CDI",
    "temps plein": "CDI",
    "cdd": "CDD",
    "contrat à durée déterminée": "CDD",
    "temporary": "CDD",
    "fixed-term": "CDD",
    "freelance": "Freelance",
    "indépendant": "Freelance",
    "contractor": "Freelance",
    "mission": "Freelance",
    "stage": "Stage",
    "internship": "Stage",
    "intern": "Stage",
    "alternance": "Alternance",
    "apprenticeship": "Alternance",
    "apprentissage": "Alternance",
    "contrat pro": "Alternance",
}

# ── Seniority patterns ──────────────────────────────────────────────────────
SENIOR_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\b(senior|sr\.?|lead|principal|staff|architect|expert|head)\b", re.I),
    re.compile(r"\b(5\+?\s*(?:ans|years)|[6-9]\d*\s*(?:ans|years)|\d{2,}\s*(?:ans|years))\b", re.I),
]
JUNIOR_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\b(junior|jr\.?|entry[- ]level|débutant|graduate|sortie d'école)\b", re.I),
    re.compile(r"\b([0-2]\s*(?:ans|years)\s*(?:d'expérience|experience))\b", re.I),
]

# ── Title normalization map ──────────────────────────────────────────────────
TITLE_NORMALIZATION: dict[re.Pattern[str], str] = {
    re.compile(r"data\s*scien", re.I): "Data Scientist",
    re.compile(r"data\s*eng", re.I): "Data Engineer",
    re.compile(r"data\s*analy", re.I): "Data Analyst",
    re.compile(r"ml\s*eng|machine\s*learning\s*eng", re.I): "ML Engineer",
    re.compile(r"mlops|ml\s*ops", re.I): "MLOps Engineer",
    re.compile(r"bi\s*(analyst|eng|dev)|business\s*intelligence", re.I): "BI Analyst",
    re.compile(r"analytics\s*eng", re.I): "Analytics Engineer",
    re.compile(r"data\s*arch", re.I): "Data Architect",
    re.compile(r"devops", re.I): "DevOps Engineer",
    re.compile(r"full\s*stack|fullstack", re.I): "Full Stack Developer",
    re.compile(r"front\s*end|frontend", re.I): "Frontend Developer",
    re.compile(r"back\s*end|backend", re.I): "Backend Developer",
}


def extract_skills(text: str) -> list[str]:
    """Extract technical skills from text using pattern matching and NER.

    Uses a curated dictionary for tech skills, plus spaCy NER for
    additional entity detection.

    Args:
        text: The text to extract skills from (job description, etc.).

    Returns:
        Sorted list of unique skill names found in the text.
    """
    if not text:
        return []

    text_lower = text.lower()
    found: set[str] = set()

    # Pattern-based matching against skill dictionary
    for skill in TECH_SKILLS:
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, text_lower):
            found.add(skill)

    # spaCy NER for additional entities (ORG, PRODUCT often catch tools/frameworks)
    try:
        nlp = _get_nlp()
        doc = nlp(text[:5000])  # Limit text length for performance
        for ent in doc.ents:
            if ent.label_ in ("ORG", "PRODUCT", "MISC"):
                skill_candidate = ent.text.lower().strip()
                if skill_candidate in TECH_SKILLS:
                    found.add(skill_candidate)
    except Exception:
        logger.warning("spaCy NER failed, using pattern-only extraction", exc_info=True)

    return sorted(found)


def normalize_contract_type(raw: str) -> str:
    """Normalize a raw contract type string to a standard label.

    Args:
        raw: The raw contract type string from the source.

    Returns:
        One of: CDI, CDD, Freelance, Stage, Alternance, Autre.
    """
    if not raw:
        return "Autre"

    raw_clean = raw.strip().lower()
    for key, value in CONTRACT_MAP.items():
        if key in raw_clean:
            return value

    return "Autre"


def classify_seniority(text: str) -> str:
    """Classify seniority level from job title and description.

    Args:
        text: Combined title and description text.

    Returns:
        One of: Junior, Mid, Senior.
    """
    if not text:
        return "Mid"

    for pattern in SENIOR_PATTERNS:
        if pattern.search(text):
            return "Senior"

    for pattern in JUNIOR_PATTERNS:
        if pattern.search(text):
            return "Junior"

    return "Mid"


def normalize_title(raw_title: str) -> str:
    """Map a raw job title to a standardized title.

    Args:
        raw_title: The original job title from the source.

    Returns:
        A normalized title string, or the cleaned original if no match.
    """
    if not raw_title:
        return "Autre"

    for pattern, normalized in TITLE_NORMALIZATION.items():
        if pattern.search(raw_title):
            return normalized

    return raw_title.strip().title()
