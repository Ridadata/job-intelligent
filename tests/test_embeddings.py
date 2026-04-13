"""Tests for embedding generation utilities."""

from unittest.mock import MagicMock, patch

import pytest

from etl.embeddings import generate_embedding, generate_embeddings_batch, reset_model


class TestGenerateEmbedding:
    """Tests for generate_embedding function."""

    def setup_method(self) -> None:
        """Reset model cache before each test."""
        reset_model()

    @patch("etl.embeddings.SentenceTransformer")
    def test_single_embedding(self, mock_model_cls: MagicMock) -> None:
        """Should generate a 384-dim embedding for valid text."""
        import numpy as np

        mock_model = MagicMock()
        mock_model.encode.return_value = np.random.rand(384).astype("float32")
        mock_model_cls.return_value = mock_model

        result = generate_embedding("data scientist python sql")
        assert isinstance(result, list)
        assert len(result) == 384

    @patch("etl.embeddings.SentenceTransformer")
    def test_empty_text_raises(self, mock_model_cls: MagicMock) -> None:
        """Should raise ValueError for empty text."""
        with pytest.raises(ValueError, match="empty text"):
            generate_embedding("")

        with pytest.raises(ValueError, match="empty text"):
            generate_embedding("   ")


class TestGenerateEmbeddingsBatch:
    """Tests for generate_embeddings_batch function."""

    def setup_method(self) -> None:
        """Reset model cache before each test."""
        reset_model()

    @patch("etl.embeddings.SentenceTransformer")
    def test_batch_embeddings(self, mock_model_cls: MagicMock) -> None:
        """Should generate embeddings for a batch of texts."""
        import numpy as np

        mock_model = MagicMock()
        mock_model.encode.return_value = np.random.rand(3, 384).astype("float32")
        mock_model_cls.return_value = mock_model

        texts = ["text one", "text two", "text three"]
        result = generate_embeddings_batch(texts)
        assert len(result) == 3
        assert all(len(emb) == 384 for emb in result)

    def test_empty_list(self) -> None:
        """Should return empty list for empty input."""
        assert generate_embeddings_batch([]) == []
