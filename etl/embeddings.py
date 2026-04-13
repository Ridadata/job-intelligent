"""Sentence-BERT embedding generation utilities."""

import logging
from typing import Optional

from sentence_transformers import SentenceTransformer

from etl.config import settings

logger = logging.getLogger(__name__)

_model: Optional[SentenceTransformer] = None


def _get_model(model_name: Optional[str] = None) -> SentenceTransformer:
    """Load the Sentence-BERT model lazily.

    Args:
        model_name: Override model name. Defaults to settings.sbert_model.

    Returns:
        SentenceTransformer: The loaded model.
    """
    global _model
    name = model_name or settings.sbert_model
    if _model is None:
        logger.info("Loading Sentence-BERT model: %s", name)
        _model = SentenceTransformer(name)
    return _model


def generate_embedding(text: str, model_name: Optional[str] = None) -> list[float]:
    """Generate a single embedding vector from text.

    Args:
        text: The input text to encode.
        model_name: Override model name. Defaults to settings.sbert_model.

    Returns:
        A list of floats representing the embedding vector (dim=384).
    """
    if not text or not text.strip():
        raise ValueError("Cannot generate embedding for empty text")

    model = _get_model(model_name)
    embedding = model.encode(text, normalize_embeddings=True)
    return embedding.tolist()


def generate_embeddings_batch(
    texts: list[str], model_name: Optional[str] = None, batch_size: int = 32
) -> list[list[float]]:
    """Generate embeddings for a batch of texts.

    Args:
        texts: List of input texts to encode.
        model_name: Override model name. Defaults to settings.sbert_model.
        batch_size: Encoding batch size for the model.

    Returns:
        List of embedding vectors, one per input text.
    """
    if not texts:
        return []

    model = _get_model(model_name)
    embeddings = model.encode(
        texts, normalize_embeddings=True, batch_size=batch_size, show_progress_bar=False
    )
    return [emb.tolist() for emb in embeddings]


def reset_model() -> None:
    """Reset the cached model (useful for testing)."""
    global _model
    _model = None
