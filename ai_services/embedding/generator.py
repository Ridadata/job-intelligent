"""Embedding generator for jobs and candidate profiles.

Uses Sentence-BERT (all-MiniLM-L6-v2) to produce 384-dim vectors.
"""

import logging

from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

_model: SentenceTransformer | None = None


def _get_model(model_name: str = "all-MiniLM-L6-v2") -> SentenceTransformer:
    """Load and cache the embedding model.

    Args:
        model_name: HuggingFace model identifier.

    Returns:
        The loaded SentenceTransformer model.
    """
    global _model
    if _model is None:
        logger.info("Loading embedding model: %s", model_name)
        _model = SentenceTransformer(model_name)
    return _model


def embed_job(title: str, description: str, skills: list[str]) -> list[float]:
    """Generate an embedding for a single job offer.

    Args:
        title: Job title.
        description: Job description text.
        skills: List of required skills.

    Returns:
        384-dimensional embedding vector.
    """
    text = f"{title}. {description}. Skills: {', '.join(skills)}"
    model = _get_model()
    return model.encode(text).tolist()


def embed_candidate(title: str, skills: list[str], experience_summary: str = "") -> list[float]:
    """Generate an embedding for a candidate profile.

    Args:
        title: Candidate job title / desired role.
        skills: List of candidate skills.
        experience_summary: Brief description of experience.

    Returns:
        384-dimensional embedding vector.
    """
    text = f"{title}. Skills: {', '.join(skills)}. {experience_summary}"
    model = _get_model()
    return model.encode(text).tolist()


def batch_embed_texts(texts: list[str]) -> list[list[float]]:
    """Batch-embed a list of text strings.

    Args:
        texts: List of input texts.

    Returns:
        List of 384-dimensional embedding vectors.
    """
    model = _get_model()
    embeddings = model.encode(texts, batch_size=32, show_progress_bar=False)
    return [e.tolist() for e in embeddings]


def generate_embedding(text: str, model_name: str = "all-MiniLM-L6-v2") -> list[float]:
    """Generate a single embedding vector for a text string.

    Args:
        text: Input text.
        model_name: HuggingFace model identifier (ignored after first load).

    Returns:
        384-dimensional embedding vector.
    """
    return batch_embed_texts([text])[0]
