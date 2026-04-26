"""NLP enrichment of CV text — skill, experience, and education extraction.

Uses a hybrid approach: canonical skill dictionary (highest precision) +
tech-pattern regex (high-confidence tokens only). spaCy NER is intentionally
NOT used for skill extraction because French NER labels (ORG/MISC) produce
too many false positives (schools, names, cities) on CV text.

Design principles:
- High precision over high recall: only emit skills we are confident about.
- All noise filtering happens before and after extraction.
- Return None for experience/education when not found — never guess.
"""

import json
import logging
import re
import unicodedata
from pathlib import Path

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

_MAX_SKILLS = 20  # cap output list to prevent runaway extraction

# Absolute path to the canonical skill dictionary shipped with the ETL module.
_SKILLS_JSON_PATH = Path(__file__).parent.parent.parent / "etl" / "skills_canonical.json"

# ── Noise filters ─────────────────────────────────────────────────────────────

# Human languages that appear in CV "Langues" sections — must not be skills.
_LANGUAGE_BLACKLIST: frozenset[str] = frozenset({
    "arabe", "arabic", "français", "french", "anglais", "english",
    "espagnol", "spanish", "allemand", "german", "italien", "italian",
    "portugais", "portuguese", "chinois", "chinese", "japonais", "japanese",
    "russe", "russian", "langue", "maternelle", "bilingue", "courant",
    "intermédiaire", "débutant", "natif", "native", "fluent",
})

# Education / school keywords — must not be emitted as skills.
_EDUCATION_BLACKLIST: frozenset[str] = frozenset({
    "ensa", "ensias", "enim", "emsi", "esi", "insa", "iga", "iscae",
    "université", "university", "école", "ecole", "school", "college",
    "faculty", "faculté", "institut", "institute",
    "master", "licence", "bachelor", "doctorat", "phd",
    "bac", "bts", "dut", "deug", "ingénieur", "engineer",
    "formation", "diplôme", "diploma", "mention", "très bien", "bien",
    "gpa", "grade", "classe prépa", "cpge",
})

# Generic / non-technical words that sneak through pattern matching.
_GENERIC_BLACKLIST: frozenset[str] = frozenset({
    "soft", "skills", "hard", "tools", "outils", "compétences",
    "technologie", "technologies", "stack", "environnement",
    "framework", "frameworks", "language", "languages", "langages",
    "projet", "project", "team", "équipe", "stage", "internship",
    "experience", "expérience", "profil", "profile", "summary",
    "contact", "email", "phone", "linkedin", "github", "portfolio",
    "objectif", "objective", "curriculum", "vitae", "cv",
    "date", "lieu", "adresse", "address", "né", "born",
    "référence", "reference", "hobby", "loisir", "centre", "intérêt",
})

# Merged blacklist for O(1) lookup.
_BLACKLIST: frozenset[str] = _LANGUAGE_BLACKLIST | _EDUCATION_BLACKLIST | _GENERIC_BLACKLIST

# Regex patterns for high-confidence tech tokens (version-bearing or hyphenated).
# Only used when a token is NOT already in the dictionary.
_TECH_PATTERNS: list[re.Pattern] = [
    # Versioned tools: python3.11, node18, java17, dotnet6
    re.compile(r"^(?:python|node|java|dotnet|ruby|php|go|rust|swift|kotlin)\d{1,2}(?:\.\d+)?$", re.I),
    # Cloud-style patterns: aws-lambda, gcp-storage
    re.compile(r"^(?:aws|azure|gcp)-[a-z][a-z0-9\-]{2,20}$", re.I),
    # Pure alphanumeric tech tokens with no spaces: ReactJS, VueJS, NextJS
    re.compile(r"^(?:react|vue|angular|next|nuxt|svelte)(?:js|\.js)?$", re.I),
]

# ── Canonical skill dictionary ────────────────────────────────────────────────

def _load_canonical_dict() -> dict[str, str]:
    """Load the canonical skill dictionary and build alias → canonical map.

    Returns:
        Dict mapping every known alias/variant (lowercase) → canonical name.
    """
    try:
        raw: dict = json.loads(_SKILLS_JSON_PATH.read_text(encoding="utf-8"))
    except Exception:
        logger.warning("Could not load skills_canonical.json — skill dict disabled")
        return {}

    mapping: dict[str, str] = {}
    for canonical, aliases in raw.items():
        if canonical == "_meta":
            continue
        canonical_lower = canonical.lower()
        mapping[canonical_lower] = canonical  # canonical maps to itself
        if isinstance(aliases, list):
            for alias in aliases:
                mapping[alias.lower()] = canonical
    return mapping


# Module-level cache — loaded once per process.
_SKILL_ALIAS_MAP: dict[str, str] = {}


def _get_skill_alias_map() -> dict[str, str]:
    """Return the cached alias → canonical map, loading if necessary.

    Returns:
        Alias map dict.
    """
    global _SKILL_ALIAS_MAP
    if not _SKILL_ALIAS_MAP:
        _SKILL_ALIAS_MAP = _load_canonical_dict()
    return _SKILL_ALIAS_MAP


# ── Text normalisation ────────────────────────────────────────────────────────

def _normalise_text(text: str) -> str:
    """Clean raw CV text for downstream processing.

    Steps:
    - Normalize unicode (NFC)
    - Replace line breaks / tabs with spaces
    - Collapse multiple spaces
    - Strip leading/trailing whitespace

    Args:
        text: Raw extracted CV text.

    Returns:
        Cleaned text (original case preserved for display; callers lowercase as needed).
    """
    # Unicode normalization
    text = unicodedata.normalize("NFC", text)
    # Replace various line-ending and tab characters with a single space
    text = re.sub(r"[\r\n\t\u00a0\u2028\u2029]+", " ", text)
    # Remove non-printable / control characters (except regular space)
    text = re.sub(r"[\x00-\x1f\x7f-\x9f]", " ", text)
    # Collapse runs of whitespace
    text = re.sub(r" {2,}", " ", text)
    return text.strip()


def _is_noise(token: str) -> bool:
    """Return True if the token should be filtered out as noise.

    Rejects:
    - Tokens under 2 characters
    - Tokens over 40 characters (likely a sentence fragment)
    - Tokens containing digits mixed with letters in suspicious patterns
    - Any token in the combined blacklist

    Args:
        token: Lowercased candidate skill token.

    Returns:
        True if the token is noise and should be discarded.
    """
    if len(token) < 2 or len(token) > 40:
        return True
    # Sentences or phrases (contains 4+ words)
    if len(token.split()) >= 4:
        return True
    if token in _BLACKLIST:
        return True
    # Contains newline remnants
    if "\n" in token or "\r" in token:
        return True
    return False


# ── Skill extraction ──────────────────────────────────────────────────────────

def extract_skills(text: str, skill_dictionary: list[str] | None = None) -> list[str]:
    """Extract skills from CV text using a high-precision hybrid approach.

    Strategy (in priority order):
    1. Dictionary match — look up every token/bigram against the canonical
       alias map. Canonical name is returned (normalised casing).
    2. Tech-pattern regex — catch versioned/hyphenated tech tokens not in dict.
    3. Optional external dictionary pass (backward-compatible parameter).

    Noise filters applied throughout:
    - Language blacklist (French, English, Arabic, etc.)
    - Education blacklist (school names, degree words)
    - Generic blacklist (soft skills, section headers)
    - Length guard (< 2 or > 40 chars rejected)
    - Phrase guard (≥ 4 words rejected)

    Args:
        text: Raw CV text.
        skill_dictionary: Ignored (kept for backward compatibility).
            The canonical JSON dictionary is always used.

    Returns:
        Deduplicated, sorted list of canonical skill names. Max 20 items.
    """
    alias_map = _get_skill_alias_map()
    cleaned = _normalise_text(text)
    text_lower = cleaned.lower()

    found: set[str] = set()

    # ── Pass 1: canonical dictionary (unigrams + bigrams) ─────────────────
    # Split on whitespace and punctuation to get candidate tokens.
    tokens = re.split(r"[\s,;:|/\(\)\[\]{}<>\"']+", text_lower)
    tokens = [t.strip(".-+") for t in tokens if t.strip(".-+")]

    for i, tok in enumerate(tokens):
        if not tok or _is_noise(tok):
            continue
        # Try unigram
        if tok in alias_map:
            found.add(alias_map[tok])
        # Try bigram (e.g. "machine learning", "power bi", "deep learning")
        if i + 1 < len(tokens):
            bigram = tok + " " + tokens[i + 1]
            if bigram in alias_map:
                found.add(alias_map[bigram])

    # ── Pass 2: tech-pattern regex (for tokens not caught by dictionary) ──
    for tok in tokens:
        if not tok or _is_noise(tok):
            continue
        if any(p.match(tok) for p in _TECH_PATTERNS):
            # Only add if not already covered and not blacklisted
            if tok.lower() not in alias_map and tok.lower() not in _BLACKLIST:
                found.add(tok.lower())  # keep as-is, already short & safe

    # ── Cap and sort ──────────────────────────────────────────────────────
    result = sorted(found)
    if len(result) > _MAX_SKILLS:
        # Prefer canonical/dictionary skills over pattern-matched ones
        # by returning the first _MAX_SKILLS alphabetically.
        result = result[:_MAX_SKILLS]

    return result


# ── Experience extraction ─────────────────────────────────────────────────────

def extract_experience(text: str) -> str | None:
    """Extract years of experience from CV text using regex.

    Only returns a value when a clear numeric pattern is found.
    Returns None rather than guessing from vague context.

    Args:
        text: Raw CV text.

    Returns:
        String like "3 years of experience" or None.
    """
    cleaned = _normalise_text(text)
    patterns = [
        # "3 ans d'expérience", "5 years of experience"
        r"(\d{1,2})\s*(?:ans?|years?)\s*(?:d[''´\u2019]?\s*)?(?:exp[ée]rience|experience)",
        # "expérience : 3 ans", "experience: 5 years"
        r"(?:exp[ée]rience|experience)\s*(?:professionnelle)?\s*[:\-–]\s*(\d{1,2})\s*(?:ans?|years?)",
        # "3+ years", "5+ ans"
        r"(\d{1,2})\+?\s*(?:ans?|years?)\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, cleaned, re.IGNORECASE)
        if match:
            years = int(match.group(1))
            if 0 < years <= 50:  # sanity guard
                return f"{years} years of experience"
    return None


# ── Education extraction ──────────────────────────────────────────────────────

# Ordered from highest to lowest so we return the highest detected level.
_EDUCATION_LEVELS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\bdoctorat\b|\bph\.?d\b", re.I), "Doctorat"),
    (re.compile(r"\bbac\s*\+\s*5\b|\bmaster\b|\bm(?:sc|\.sc)\b|\bingénieur\b|\bmba\b", re.I), "Bac+5"),
    (re.compile(r"\bbac\s*\+\s*4\b|\bmaîtrise\b|\bm(?:aîtrise|aitrise)\b", re.I), "Bac+4"),
    (re.compile(r"\bbac\s*\+\s*3\b|\blicence\b|\bbachelor\b|\bbs(?:c)?\b|\bba\b", re.I), "Bac+3"),
    (re.compile(r"\bbac\s*\+\s*2\b|\bbts\b|\bdut\b|\bdeug\b|\bhnd\b", re.I), "Bac+2"),
    (re.compile(r"\bbaccalauréat\b|\bbac\b(?!\s*\+)", re.I), "Bac"),
]


def extract_education(text: str) -> str | None:
    """Extract highest education level from CV text.

    Uses strict regex anchored to level-specific keywords. Returns the
    highest level detected. Returns None if no clear pattern is found —
    never guesses.

    Args:
        text: Raw CV text.

    Returns:
        Education level string (e.g. "Bac+5") or None.
    """
    cleaned = _normalise_text(text)
    for pattern, level in _EDUCATION_LEVELS:
        if pattern.search(cleaned):
            return level
    return None


# ── Fallback extraction ───────────────────────────────────────────────────────

def _fallback_keyword_extraction(text: str) -> list[str]:
    """Simple keyword extraction used when the main pipeline fails.

    Only matches canonical dictionary keys — no pattern matching, no NER.
    Maximum 10 results.

    Args:
        text: Raw CV text.

    Returns:
        List of matched canonical skill names.
    """
    alias_map = _get_skill_alias_map()
    text_lower = text.lower()
    found: set[str] = set()
    for alias, canonical in alias_map.items():
        if len(alias) >= 3 and alias in text_lower:
            found.add(canonical)
    return sorted(found)[:10]


# ── Public API ────────────────────────────────────────────────────────────────

def parse_cv(text: str, skill_dictionary: list[str] | None = None) -> dict:
    """Full CV parsing pipeline: text cleaning → skills → experience → education.

    Falls back to simple keyword extraction if the main skill pipeline raises.

    Args:
        text: Raw CV text (as returned by extractor.extract_text()).
        skill_dictionary: Ignored. Kept for backward compatibility.

    Returns:
        Dict with keys:
            skills (list[str]): clean canonical skill list, max 20 items.
            experience (str | None): "N years of experience" or None.
            education (str | None): education level string or None.
    """
    try:
        skills = extract_skills(text)
    except Exception:
        logger.warning("Main skill extraction failed — using fallback", exc_info=True)
        skills = _fallback_keyword_extraction(text)

    return {
        "skills": skills,
        "experience": extract_experience(text),
        "education": extract_education(text),
    }
