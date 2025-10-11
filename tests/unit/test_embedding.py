"""Unit tests for Embedding model."""

import numpy as np
import pytest

from markdown_reallocator.models import Embedding


class TestEmbedding:
    """Tests for Embedding dataclass."""

    def test_initialization(self) -> None:
        """Test basic Embedding initialization."""
        vector = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        text_hash = "abc123"
        model_name = "embeddinggemma"
        embedding = Embedding(vector=vector, text_hash=text_hash, model_name=model_name)
        assert np.array_equal(embedding.vector, vector)
        assert embedding.text_hash == "abc123"
        assert embedding.model_name == "embeddinggemma"

    def test_auto_convert_to_float32(self) -> None:
        """Test that vector is automatically converted to float32."""
        vector = np.array([0.1, 0.2, 0.3], dtype=np.float64)  # float64
        embedding = Embedding(vector=vector, text_hash="hash", model_name="model")
        assert embedding.vector.dtype == np.float32

    def test_multi_dimensional_vector_raises_error(self) -> None:
        """Test that multi-dimensional vector raises ValueError."""
        vector = np.array([[0.1, 0.2], [0.3, 0.4]], dtype=np.float32)
        with pytest.raises(ValueError, match="vector must be 1-dimensional"):
            Embedding(vector=vector, text_hash="hash", model_name="model")

    def test_empty_vector_raises_error(self) -> None:
        """Test that empty vector raises ValueError."""
        vector = np.array([], dtype=np.float32)
        with pytest.raises(ValueError, match="vector cannot be empty"):
            Embedding(vector=vector, text_hash="hash", model_name="model")

    def test_empty_text_hash_raises_error(self) -> None:
        """Test that empty text_hash raises ValueError."""
        vector = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        with pytest.raises(ValueError, match="text_hash cannot be empty"):
            Embedding(vector=vector, text_hash="", model_name="model")

    def test_empty_model_name_raises_error(self) -> None:
        """Test that empty model_name raises ValueError."""
        vector = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        with pytest.raises(ValueError, match="model_name cannot be empty"):
            Embedding(vector=vector, text_hash="hash", model_name="")

    def test_dimension_property(self) -> None:
        """Test dimension property returns correct size."""
        vector = np.array([0.1, 0.2, 0.3, 0.4, 0.5], dtype=np.float32)
        embedding = Embedding(vector=vector, text_hash="hash", model_name="model")
        assert embedding.dimension == 5

    def test_dimension_property_384(self) -> None:
        """Test dimension property with embeddinggemma size."""
        vector = np.random.rand(384).astype(np.float32)
        embedding = Embedding(vector=vector, text_hash="hash", model_name="embeddinggemma")
        assert embedding.dimension == 384

    def test_normalize(self) -> None:
        """Test vector normalization."""
        vector = np.array([3.0, 4.0], dtype=np.float32)  # magnitude = 5
        embedding = Embedding(vector=vector, text_hash="hash", model_name="model")
        normalized = embedding.normalize()
        assert np.allclose(normalized.vector, [0.6, 0.8])
        assert np.isclose(np.linalg.norm(normalized.vector), 1.0)

    def test_normalize_preserves_metadata(self) -> None:
        """Test that normalization preserves text_hash and model_name."""
        vector = np.array([1.0, 2.0, 3.0], dtype=np.float32)
        embedding = Embedding(vector=vector, text_hash="original_hash", model_name="test_model")
        normalized = embedding.normalize()
        assert normalized.text_hash == "original_hash"
        assert normalized.model_name == "test_model"

    def test_normalize_zero_vector_raises_error(self) -> None:
        """Test that normalizing zero vector raises ValueError."""
        vector = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        embedding = Embedding(vector=vector, text_hash="hash", model_name="model")
        with pytest.raises(ValueError, match="Cannot normalize zero vector"):
            embedding.normalize()

    def test_normalize_creates_new_instance(self) -> None:
        """Test that normalize returns a new Embedding instance."""
        vector = np.array([1.0, 2.0, 3.0], dtype=np.float32)
        original = Embedding(vector=vector, text_hash="hash", model_name="model")
        normalized = original.normalize()
        assert original is not normalized
        assert not np.array_equal(original.vector, normalized.vector)

    def test_to_bytes(self) -> None:
        """Test serialization to bytes."""
        vector = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        embedding = Embedding(vector=vector, text_hash="hash", model_name="model")
        bytes_data = embedding.to_bytes()
        assert isinstance(bytes_data, bytes)
        assert len(bytes_data) == 3 * 4  # 3 floats * 4 bytes each

    def test_from_bytes(self) -> None:
        """Test deserialization from bytes."""
        original_vector = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        bytes_data = original_vector.tobytes()
        embedding = Embedding.from_bytes(bytes_data, text_hash="hash", model_name="model")
        assert np.array_equal(embedding.vector, original_vector)
        assert embedding.text_hash == "hash"
        assert embedding.model_name == "model"

    def test_from_bytes_with_different_dtype(self) -> None:
        """Test deserialization with specified dtype."""
        original_vector = np.array([0.1, 0.2, 0.3], dtype=np.float64)
        bytes_data = original_vector.tobytes()
        embedding = Embedding.from_bytes(
            bytes_data,
            text_hash="hash",
            model_name="model",
            dtype=np.float64,
        )
        assert embedding.vector.dtype == np.float32  # Should be converted in __post_init__
        assert np.allclose(embedding.vector, original_vector, rtol=1e-5)

    def test_roundtrip_serialization_bytes(self) -> None:
        """Test roundtrip serialization through bytes."""
        original_vector = np.array([0.5, 0.6, 0.7, 0.8], dtype=np.float32)
        original = Embedding(vector=original_vector, text_hash="test_hash", model_name="test_model")
        bytes_data = original.to_bytes()
        restored = Embedding.from_bytes(bytes_data, text_hash="test_hash", model_name="test_model")
        assert np.array_equal(restored.vector, original.vector)
        assert restored.text_hash == original.text_hash
        assert restored.model_name == original.model_name

    def test_equality_same_hash_and_model(self) -> None:
        """Test that embeddings with same hash and model are equal."""
        vector1 = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        vector2 = np.array([0.4, 0.5, 0.6], dtype=np.float32)  # Different vector
        emb1 = Embedding(vector=vector1, text_hash="same_hash", model_name="same_model")
        emb2 = Embedding(vector=vector2, text_hash="same_hash", model_name="same_model")
        assert emb1 == emb2

    def test_inequality_different_hash(self) -> None:
        """Test that embeddings with different hashes are not equal."""
        vector = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        emb1 = Embedding(vector=vector, text_hash="hash1", model_name="model")
        emb2 = Embedding(vector=vector, text_hash="hash2", model_name="model")
        assert emb1 != emb2

    def test_inequality_different_model(self) -> None:
        """Test that embeddings with different models are not equal."""
        vector = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        emb1 = Embedding(vector=vector, text_hash="hash", model_name="model1")
        emb2 = Embedding(vector=vector, text_hash="hash", model_name="model2")
        assert emb1 != emb2

    def test_equality_with_non_embedding(self) -> None:
        """Test equality comparison with non-Embedding object."""
        vector = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        embedding = Embedding(vector=vector, text_hash="hash", model_name="model")
        assert embedding != "not an embedding"
        assert embedding != 123
        assert embedding is not None

    def test_repr(self) -> None:
        """Test string representation."""
        vector = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        text_hash = "abcd1234567890"
        embedding = Embedding(vector=vector, text_hash=text_hash, model_name="embeddinggemma")
        repr_str = repr(embedding)
        assert "dim=3" in repr_str
        assert "embeddinggemma" in repr_str
        assert "abcd1234" in repr_str  # First 8 chars of hash
        assert "..." in repr_str

    def test_repr_384_dimensions(self) -> None:
        """Test repr with realistic embedding dimensions."""
        vector = np.random.rand(384).astype(np.float32)
        embedding = Embedding(
            vector=vector, text_hash="full_hash_value_here", model_name="embeddinggemma"
        )
        repr_str = repr(embedding)
        assert "dim=384" in repr_str

    def test_compute_text_hash(self) -> None:
        """Test compute_text_hash static method."""
        text = "This is a test."
        hash1 = Embedding.compute_text_hash(text)
        hash2 = Embedding.compute_text_hash(text)
        assert hash1 == hash2  # Same input produces same hash
        assert len(hash1) == 64  # SHA256 produces 64 hex characters

    def test_compute_text_hash_different_inputs(self) -> None:
        """Test that different texts produce different hashes."""
        hash1 = Embedding.compute_text_hash("Text 1")
        hash2 = Embedding.compute_text_hash("Text 2")
        assert hash1 != hash2

    def test_compute_text_hash_unicode(self) -> None:
        """Test hash computation with Unicode text."""
        text = "한글 텍스트와 日本語 and English"
        hash_value = Embedding.compute_text_hash(text)
        assert len(hash_value) == 64
        assert hash_value == Embedding.compute_text_hash(text)  # Deterministic

    def test_compute_text_hash_empty_string(self) -> None:
        """Test hash computation with empty string."""
        hash_value = Embedding.compute_text_hash("")
        assert len(hash_value) == 64
        # SHA256 of empty string is known value
        assert (
            hash_value == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        )

    def test_realistic_embeddinggemma_embedding(self) -> None:
        """Test with realistic embeddinggemma embedding."""
        text = "This is a sample markdown chunk for embedding."
        text_hash = Embedding.compute_text_hash(text)
        vector = np.random.rand(384).astype(np.float32)  # embeddinggemma output
        embedding = Embedding(vector=vector, text_hash=text_hash, model_name="embeddinggemma")

        # Verify properties
        assert embedding.dimension == 384
        assert embedding.text_hash == text_hash
        assert embedding.model_name == "embeddinggemma"
        assert embedding.vector.dtype == np.float32

        # Verify normalization works
        normalized = embedding.normalize()
        assert np.isclose(np.linalg.norm(normalized.vector), 1.0)

    def test_realistic_cache_key_pattern(self) -> None:
        """Test realistic cache key pattern used in the system."""
        text = "## Introduction\n\nThis is the content."
        text_hash = Embedding.compute_text_hash(text)
        vector = np.random.rand(384).astype(np.float32)
        embedding = Embedding(vector=vector, text_hash=text_hash, model_name="embeddinggemma")

        # Simulate cache key
        cache_key = f"{embedding.model_name}:{embedding.text_hash}"
        assert cache_key.startswith("embeddinggemma:")
        assert len(cache_key.split(":")[1]) == 64

    def test_edge_case_very_large_vector(self) -> None:
        """Test with very large embedding dimension."""
        vector = np.random.rand(4096).astype(np.float32)  # Large dimension
        embedding = Embedding(vector=vector, text_hash="hash", model_name="large_model")
        assert embedding.dimension == 4096
        assert embedding.to_bytes() is not None

    def test_edge_case_single_dimension_vector(self) -> None:
        """Test with single-dimension vector."""
        vector = np.array([0.5], dtype=np.float32)
        embedding = Embedding(vector=vector, text_hash="hash", model_name="model")
        assert embedding.dimension == 1
        normalized = embedding.normalize()
        assert np.isclose(normalized.vector[0], 1.0)

    def test_edge_case_negative_values(self) -> None:
        """Test embedding with negative values."""
        vector = np.array([-0.5, 0.3, -0.1, 0.7], dtype=np.float32)
        embedding = Embedding(vector=vector, text_hash="hash", model_name="model")
        assert np.array_equal(embedding.vector, vector)
        normalized = embedding.normalize()
        assert np.isclose(np.linalg.norm(normalized.vector), 1.0)

    def test_cosine_similarity_use_case(self) -> None:
        """Test normalized embeddings for cosine similarity."""
        # Two embeddings with known similarity
        v1 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        v2 = np.array([1.0, 1.0, 0.0], dtype=np.float32)

        emb1 = Embedding(vector=v1, text_hash="hash1", model_name="model")
        emb2 = Embedding(vector=v2, text_hash="hash2", model_name="model")

        norm1 = emb1.normalize()
        norm2 = emb2.normalize()

        # Cosine similarity = dot product of normalized vectors
        similarity = np.dot(norm1.vector, norm2.vector)
        expected = 1.0 / np.sqrt(2)  # cos(45°)
        assert np.isclose(similarity, expected, rtol=1e-5)

    def test_serialization_preserves_precision(self) -> None:
        """Test that byte serialization preserves float32 precision."""
        original_vector = np.array([0.123456789, 0.987654321], dtype=np.float32)
        embedding = Embedding(vector=original_vector, text_hash="hash", model_name="model")
        bytes_data = embedding.to_bytes()
        restored = Embedding.from_bytes(bytes_data, text_hash="hash", model_name="model")
        # Should be exact for float32 precision
        assert np.array_equal(restored.vector, original_vector)
