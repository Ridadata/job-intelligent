"""Job data cleaning and normalization module.

Provides functions to clean raw job titles, standardize contract types,
validate job records, compute content-based dedup keys, and log
ingestion metrics.  Every function is pure and stateless.
"""

import hashlib
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# ── Title noise patterns (removed before any matching) ───────────────────────
_NOISE_PHRASES: list[re.Pattern[str]] = [
    # Call-to-action / marketing
    re.compile(r"\b(submit\s+your\s+(spontaneous\s+)?application)\b", re.I),
    re.compile(r"\b(apply\s+now|postulez?\s+maintenant|candidature\s+spontan[ée]e)\b", re.I),
    re.compile(r"\b(join\s+us|rejoignez[- ]nous|nous\s+recrutons|recrutement)\b", re.I),
    re.compile(r"\b(we\s+are\s+hiring|on\s+recrute|venez?\s+rejoindre)\b", re.I),
    re.compile(r"\b(opportunit[ée]\s+de\s+carri[èe]re)\b", re.I),
    re.compile(r"\b(urgent|asap|new|nouveau|nouvelle)\b", re.I),
    # Company promotion suffixes
    re.compile(r"\b(and\s+join\s+\w+)\s*!?", re.I),
    re.compile(r"\b(chez\s+\w+)\s*!?$", re.I),
    # "Permanent" / "Temporary" qualifiers that are contract info, not title
    re.compile(r"\bpermanent(e)?\b", re.I),
    re.compile(r"\btemporaire\b", re.I),
]

# H/F gender markers common in French job titles
_HF_PATTERN = re.compile(
    r"\s*[-–]?\s*\(?\s*[HFhf]\s*/\s*[HFhf]\s*\)?"
    r"|\s*[-–]?\s*\(?\s*[MmFf]\s*/\s*[MmFf]\s*\)?",
)

# Location suffixes: "- City", "(City)", "/ City"
_LOCATION_SUFFIX = re.compile(
    r"""
    \s*                             # optional whitespace
    [-–/|]                          # separator
    \s*                             # optional whitespace
    (
        [A-Z\u00C0-\u024F][a-z\u00C0-\u024F]+   # Capitalised city
        (?:\s+[A-Z\u00C0-\u024F][a-z\u00C0-\u024F]+)*  # multi-word
    )
    \s*$                            # end of string
    """,
    re.VERBOSE,
)

_PARENTHETICAL_LOCATION = re.compile(
    r"\s*\(\s*(?:France|Remote|Maroc|Morocco|Paris|Casablanca|Rabat|Fès|Fez"
    r"|Lyon|Marseille|Toulouse|Bordeaux|Lille|Nantes|Strasbourg|T[ée]l[ée]travail"
    r"|Hybrid|Hybride|On\s*site|Sur\s*site)\s*\)\s*",
    re.I,
)

# Known Moroccan / French city list for aggressive suffix removal
_CITY_SUFFIXES: list[str] = [
    "Casablanca", "Rabat", "Fès", "Fez", "Marrakech", "Tanger", "Agadir",
    "Oujda", "Kenitra", "Meknès", "Mohammedia", "Salé", "Témara",
    "Paris", "Lyon", "Marseille", "Toulouse", "Bordeaux", "Lille",
    "Nantes", "Strasbourg", "Montpellier", "Nice", "Rennes",
]
_CITY_SUFFIX_RE = re.compile(
    r"\s*[-–/]\s*(" + "|".join(re.escape(c) for c in _CITY_SUFFIXES) + r")\s*$",
    re.I,
)

# Duplicate-word removal ("Data Data Engineer" → "Data Engineer")
_DUPLICATE_WORD = re.compile(r"\b(\w+)(\s+\1)+\b", re.I)

# Excessive punctuation
_EXCESS_PUNCT = re.compile(r"[!?]{2,}")
_TRAILING_PUNCT = re.compile(r"[!?.,:;]+\s*$")
_LEADING_PUNCT = re.compile(r"^\s*[!?.,:;/\-–|]+\s*")

# Collapse whitespace
_MULTI_SPACE = re.compile(r"\s{2,}")


def normalize_title(title: str) -> str:
    """Normalize a raw job title into a clean, standardised form.

    Steps:
    1. Strip marketing / CTA phrases.
    2. Remove location suffixes ('- Fès', '(France)', etc.).
    3. Remove excessive punctuation.
    4. Remove duplicate words.
    5. Collapse whitespace and apply Title Case.

    Args:
        title: The raw job title.

    Returns:
        A clean, Title Cased job title.
    """
    if not title or not title.strip():
        return "Untitled"

    text = title.strip()

    # 1. Remove H/F gender markers
    text = _HF_PATTERN.sub("", text)

    # 2. Remove noise phrases
    for pattern in _NOISE_PHRASES:
        text = pattern.sub("", text)

    # 3. Remove parenthetical locations
    text = _PARENTHETICAL_LOCATION.sub("", text)

    # 4. Remove city suffixes "- CityName"
    text = _CITY_SUFFIX_RE.sub("", text)

    # 5. Remove generic location suffixes
    text = _LOCATION_SUFFIX.sub("", text)

    # 6. Remove excessive / trailing / leading punctuation
    text = _EXCESS_PUNCT.sub("", text)
    text = _TRAILING_PUNCT.sub("", text)
    text = _LEADING_PUNCT.sub("", text)

    # 7. Remove duplicate words
    text = _DUPLICATE_WORD.sub(r"\1", text)

    # 8. Collapse whitespace + trim
    text = _MULTI_SPACE.sub(" ", text).strip()

    if not text:
        return "Untitled"

    # 9. Title Case
    return text.title()


# ── Contract type standardization ────────────────────────────────────────────
_CONTRACT_MAP: dict[str, str] = {
    # French
    "cdi": "FULL_TIME",
    "contrat à durée indéterminée": "FULL_TIME",
    "temps plein": "FULL_TIME",
    "cdd": "CONTRACT",
    "contrat à durée déterminée": "CONTRACT",
    "stage": "INTERNSHIP",
    "internship": "INTERNSHIP",
    "intern": "INTERNSHIP",
    "alternance": "INTERNSHIP",
    "apprentissage": "INTERNSHIP",
    "contrat pro": "INTERNSHIP",
    "freelance": "FREELANCE",
    "indépendant": "FREELANCE",
    "contractor": "FREELANCE",
    "mission": "FREELANCE",
    # English
    "full-time": "FULL_TIME",
    "full time": "FULL_TIME",
    "permanent": "FULL_TIME",
    "part-time": "PART_TIME",
    "part time": "PART_TIME",
    "temporary": "CONTRACT",
    "fixed-term": "CONTRACT",
    "contract": "CONTRACT",
}


def standardize_contract(raw: str) -> str:
    """Map a raw contract type to a standard enum.

    Args:
        raw: The raw contract type string.

    Returns:
        One of: FULL_TIME, CONTRACT, INTERNSHIP, FREELANCE, PART_TIME, OTHER.
    """
    if not raw:
        return "OTHER"

    cleaned = raw.strip().lower()
    for key, value in _CONTRACT_MAP.items():
        if key in cleaned:
            return value

    return "OTHER"


# ── Seniority detection ─────────────────────────────────────────────────────
_SENIOR_RE = re.compile(
    r"\b(senior|sr\.?|lead|principal|staff|architect|expert|head|directeur|manager)\b",
    re.I,
)
_JUNIOR_RE = re.compile(
    r"\b(junior|jr\.?|entry[- ]?level|débutant|graduate|sortie\s+d'école|stagiaire)\b",
    re.I,
)


def detect_seniority(title: str, description: str = "") -> str:
    """Detect seniority level from title and description.

    Args:
        title: Job title.
        description: Job description (optional).

    Returns:
        One of: JUNIOR, MID, SENIOR.
    """
    text = f"{title} {description}"
    if _SENIOR_RE.search(text):
        return "SENIOR"
    if _JUNIOR_RE.search(text):
        return "JUNIOR"
    return "MID"


# ── Seniority normalization ─────────────────────────────────────────────────

_SENIORITY_MAP: dict[str, str] = {
    "junior": "Junior",
    "jr": "Junior",
    "mid": "Mid",
    "middle": "Mid",
    "senior": "Senior",
    "sr": "Senior",
    "lead": "Senior",
}


def normalize_seniority(level: str) -> str:
    """Normalize a seniority string to the canonical form.

    Args:
        level: Raw seniority string (any case).

    Returns:
        One of: 'Junior', 'Mid', 'Senior'. Defaults to 'Mid'.
    """
    return _SENIORITY_MAP.get(level.strip().lower(), "Mid")


# ── Validation ───────────────────────────────────────────────────────────────

def is_valid_job(job: dict[str, Any]) -> bool:
    """Check whether a job record passes minimum quality gates.

    Only hard requirement is a meaningful title (>= 3 chars).
    Company, description, and skills are optional — many valid
    API results lack some of these fields.

    Args:
        job: A job dict with at least a 'title' key.

    Returns:
        True if valid, False if should be quarantined.
    """
    title = (job.get("title") or "").strip()

    if len(title) < 3:
        logger.debug("REJECT job — title too short: %r", title)
        return False

    return True


def validate_job(job: dict[str, Any]) -> tuple[bool, list[str]]:
    """Validate a job and return (is_valid, list_of_reasons).

    Only hard requirement is a meaningful title.
    Other fields generate warnings but don't fail validation.

    Args:
        job: A job dict.

    Returns:
        Tuple of (is_valid, reasons). reasons is empty if valid.
    """
    reasons: list[str] = []
    title = (job.get("title") or "").strip()

    if len(title) < 3:
        reasons.append(f"title_too_short (len={len(title)})")

    # Log warnings for missing optional fields (don't reject)
    if not (job.get("company") or "").strip():
        logger.debug("WARN job — empty company for title %r", title)
    if not (job.get("description") or "").strip():
        logger.debug("WARN job — empty description for title %r", title)

    return len(reasons) == 0, reasons


# ── Content-based dedup key ──────────────────────────────────────────────────

def _normalize_for_dedup(text: str) -> str:
    """Lowercase, strip, collapse whitespace, remove punctuation."""
    if not text:
        return ""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text


def compute_dedup_key(title: str, company: str, location: str) -> str:
    """Compute a content-based dedup hash.

    Uses SHA-256 of normalized(title + company + location).

    Args:
        title: Job title.
        company: Company name.
        location: Job location.

    Returns:
        Hex digest string (64 chars).
    """
    parts = "|".join([
        _normalize_for_dedup(title),
        _normalize_for_dedup(company),
        _normalize_for_dedup(location),
    ])
    return hashlib.sha256(parts.encode("utf-8")).hexdigest()


# ── Gold row builder ─────────────────────────────────────────────────────────

def build_gold_record(job: dict[str, Any]) -> dict[str, Any]:
    """Build a clean Gold-layer record from a Silver job.

    Args:
        job: A Silver-layer job dict.

    Returns:
        Dict with clean_title, clean_company, clean_location,
        contract_type_standardized, seniority_level, dedup_key.
    """
    title = job.get("title", "")
    company = (job.get("company") or "").strip()
    location = (job.get("location") or "").strip()
    contract = job.get("contract_type", "")
    description = job.get("description", "")

    clean_title = normalize_title(title)

    return {
        "clean_title": clean_title,
        "clean_company": company.title() if company else "",
        "clean_location": location.title() if location else "",
        "contract_type_standardized": standardize_contract(contract),
        "seniority_level": normalize_seniority(detect_seniority(title, description)),
        "dedup_key": compute_dedup_key(clean_title, company, location),
    }


# ── Ingestion metrics ───────────────────────────────────────────────────────

class IngestionMetrics:
    """Tracks per-source ingestion statistics.

    Usage::

        metrics = IngestionMetrics("adzuna")
        metrics.fetched += 50
        metrics.cleaned += 48
        metrics.rejected += 2
        metrics.inserted += 48
        metrics.log_summary()
    """

    def __init__(self, source: str) -> None:
        self.source = source
        self.fetched = 0
        self.cleaned = 0
        self.rejected = 0
        self.inserted = 0

    def log_summary(self) -> None:
        """Log a structured summary of this source's ingestion run."""
        logger.info(
            "METRICS [%s] — fetched=%d, cleaned=%d, rejected=%d, inserted=%d",
            self.source, self.fetched, self.cleaned, self.rejected, self.inserted,
        )

    def to_dict(self) -> dict[str, Any]:
        """Return metrics as a dict for JSON logging / pipeline_runs.

        Returns:
            Dict with source, fetched, cleaned, rejected, inserted.
        """
        return {
            "source": self.source,
            "fetched": self.fetched,
            "cleaned": self.cleaned,
            "rejected": self.rejected,
            "inserted": self.inserted,
        }
