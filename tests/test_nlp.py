"""Tests for NLP utilities: skill extraction, normalization, classification."""

from etl.nlp import (
    classify_seniority,
    extract_skills,
    normalize_contract_type,
    normalize_title,
)


class TestExtractSkills:
    """Tests for extract_skills function."""

    def test_extract_known_skills(self) -> None:
        """Should extract known tech skills from text."""
        text = "Looking for a developer with Python, SQL, and Docker experience."
        skills = extract_skills(text)
        assert "python" in skills
        assert "sql" in skills
        assert "docker" in skills

    def test_extract_ml_skills(self) -> None:
        """Should extract ML-related skills."""
        text = "Experience with TensorFlow, PyTorch, and machine learning required."
        skills = extract_skills(text)
        assert "tensorflow" in skills
        assert "pytorch" in skills
        assert "machine learning" in skills

    def test_extract_empty_text(self) -> None:
        """Should return empty list for empty text."""
        assert extract_skills("") == []
        assert extract_skills(None) == []  # type: ignore[arg-type]

    def test_no_false_positives(self) -> None:
        """Should not extract random words as skills."""
        text = "We need a motivated person who enjoys teamwork."
        skills = extract_skills(text)
        assert "motivated" not in skills
        assert "teamwork" not in skills

    def test_case_insensitive(self) -> None:
        """Should match skills regardless of case."""
        text = "PYTHON, PostgreSQL, and DOCKER are required."
        skills = extract_skills(text)
        assert "python" in skills
        assert "postgresql" in skills
        assert "docker" in skills


class TestNormalizeContractType:
    """Tests for normalize_contract_type function."""

    def test_cdi_variants(self) -> None:
        """Should normalize CDI variants."""
        assert normalize_contract_type("CDI") == "CDI"
        assert normalize_contract_type("Contrat à durée indéterminée") == "CDI"
        assert normalize_contract_type("Full-time") == "CDI"

    def test_cdd_variants(self) -> None:
        """Should normalize CDD variants."""
        assert normalize_contract_type("CDD") == "CDD"
        assert normalize_contract_type("temporary") == "CDD"

    def test_stage(self) -> None:
        """Should normalize internship variants."""
        assert normalize_contract_type("Stage") == "Stage"
        assert normalize_contract_type("Internship") == "Stage"

    def test_alternance(self) -> None:
        """Should normalize alternance variants."""
        assert normalize_contract_type("Alternance") == "Alternance"
        assert normalize_contract_type("Apprentissage") == "Alternance"

    def test_unknown(self) -> None:
        """Should return Autre for unknown types."""
        assert normalize_contract_type("Something else") == "Autre"
        assert normalize_contract_type("") == "Autre"


class TestClassifySeniority:
    """Tests for classify_seniority function."""

    def test_senior(self) -> None:
        """Should classify senior roles."""
        assert classify_seniority("Senior Data Scientist") == "Senior"
        assert classify_seniority("Lead ML Engineer") == "Senior"
        assert classify_seniority("Principal Data Engineer") == "Senior"

    def test_junior(self) -> None:
        """Should classify junior roles."""
        assert classify_seniority("Junior Data Analyst") == "Junior"
        assert classify_seniority("Entry-level developer") == "Junior"

    def test_mid(self) -> None:
        """Should default to Mid for unspecified seniority."""
        assert classify_seniority("Data Scientist") == "Mid"
        assert classify_seniority("Data Engineer") == "Mid"

    def test_empty(self) -> None:
        """Should default to Mid for empty text."""
        assert classify_seniority("") == "Mid"


class TestNormalizeTitle:
    """Tests for normalize_title function."""

    def test_data_scientist(self) -> None:
        """Should normalize Data Scientist variants."""
        assert normalize_title("Senior Data Scientist") == "Data Scientist"
        assert normalize_title("data scientist junior") == "Data Scientist"

    def test_data_engineer(self) -> None:
        """Should normalize Data Engineer variants."""
        assert normalize_title("Data Engineer") == "Data Engineer"
        assert normalize_title("Lead Data Engineering") == "Data Engineer"

    def test_ml_engineer(self) -> None:
        """Should normalize ML Engineer variants."""
        assert normalize_title("ML Engineer") == "ML Engineer"
        assert normalize_title("Machine Learning Engineer") == "ML Engineer"

    def test_unknown_title(self) -> None:
        """Should preserve unknown titles as Title Case."""
        assert normalize_title("Cloud Architect") == "Cloud Architect"

    def test_empty(self) -> None:
        """Should return Autre for empty title."""
        assert normalize_title("") == "Autre"
