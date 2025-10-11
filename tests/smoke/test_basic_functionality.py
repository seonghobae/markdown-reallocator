"""Smoke tests for basic functionality.

These tests verify core functionality works without external dependencies.
"""

import numpy as np
import pytest

from markdown_reallocator.core.preprocessor import MarkdownPreprocessor, PreprocessorConfig
from markdown_reallocator.core.splitter import MarkdownSplitter
from markdown_reallocator.models.chunk import Chunk, ChunkMetadata
from markdown_reallocator.models.embedding import Embedding
from markdown_reallocator.utils.cache import EmbeddingCache, LRUCache
from markdown_reallocator.utils.similarity import cosine_similarity


class TestPreprocessorSmoke:
    """Smoke tests for preprocessor."""

    def test_preprocessor_creation(self):
        """Test preprocessor can be created."""
        preprocessor = MarkdownPreprocessor()
        assert preprocessor is not None

    def test_preprocessor_with_config(self):
        """Test preprocessor with custom config."""
        config = PreprocessorConfig(max_title_length=100)
        preprocessor = MarkdownPreprocessor(config)
        assert preprocessor.config.max_title_length == 100

    def test_simple_preprocessing(self):
        """Test basic preprocessing works."""
        preprocessor = MarkdownPreprocessor()
        markdown = "**Title**\n\nContent here."
        result = preprocessor.preprocess(markdown)
        assert isinstance(result, str)
        assert len(result) > 0


class TestSplitterSmoke:
    """Smoke tests for splitter."""

    def test_splitter_creation(self):
        """Test splitter can be created."""
        splitter = MarkdownSplitter()
        assert splitter is not None

    def test_simple_split(self):
        """Test basic splitting works."""
        splitter = MarkdownSplitter()
        markdown = "# Title\n\nContent here."
        chunks = splitter.split(markdown)
        assert isinstance(chunks, list)
        assert len(chunks) > 0
        assert all(isinstance(c, Chunk) for c in chunks)


class TestChunkSmoke:
    """Smoke tests for chunk models."""

    def test_chunk_creation(self):
        """Test chunk can be created."""
        metadata = ChunkMetadata(original_position=0)
        chunk = Chunk(
            chunk_id="test123",
            content="Test content",
            metadata=metadata,
        )
        assert chunk.chunk_id == "test123"
        assert chunk.content == "Test content"

    def test_chunk_with_embedding(self):
        """Test chunk can hold an embedding."""
        metadata = ChunkMetadata(original_position=0)
        chunk = Chunk(
            chunk_id="test123",
            content="Test content",
            metadata=metadata,
        )
        chunk.embedding = np.array([0.1, 0.2, 0.3])
        assert chunk.embedding is not None
        assert len(chunk.embedding) == 3


class TestEmbeddingSmoke:
    """Smoke tests for embedding models."""

    def test_embedding_vector_creation(self):
        """Test embedding vector can be created."""
        vector = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        embedding = Embedding(
            vector=vector,
            text_hash="test_hash_123",
            model_name="test-model",
        )
        assert embedding.dimension == 3
        assert embedding.model_name == "test-model"

    def test_embedding_normalization(self):
        """Test embedding normalization."""
        vector = np.array([3.0, 4.0], dtype=np.float32)
        embedding = Embedding(
            vector=vector,
            text_hash="test_hash_456",
            model_name="test",
        )
        normalized = embedding.normalize()
        # 3-4-5 triangle: norm should be 5, normalized should be [0.6, 0.8]
        assert np.allclose(normalized.vector, [0.6, 0.8])


class TestCacheSmoke:
    """Smoke tests for caching."""

    def test_lru_cache_creation(self):
        """Test LRU cache can be created."""
        cache = LRUCache(max_size=10)
        assert cache is not None
        assert len(cache) == 0

    def test_lru_cache_basic_ops(self):
        """Test basic cache operations."""
        cache = LRUCache(max_size=2)
        arr1 = np.array([1, 2, 3])
        arr2 = np.array([4, 5, 6])

        cache.put("key1", arr1)
        cache.put("key2", arr2)

        assert cache.get("key1") is not None
        assert cache.get("key2") is not None
        assert cache.get("key3") is None

    def test_embedding_cache_creation(self):
        """Test embedding cache can be created."""
        cache = EmbeddingCache(max_size=10)
        assert cache is not None


class TestSimilaritySmoke:
    """Smoke tests for similarity functions."""

    def test_cosine_similarity(self):
        """Test cosine similarity calculation."""
        vec1 = np.array([1.0, 0.0, 0.0])
        vec2 = np.array([1.0, 0.0, 0.0])
        similarity = cosine_similarity(vec1, vec2)
        assert np.isclose(similarity, 1.0)

    def test_cosine_similarity_orthogonal(self):
        """Test cosine similarity for orthogonal vectors."""
        vec1 = np.array([1.0, 0.0])
        vec2 = np.array([0.0, 1.0])
        similarity = cosine_similarity(vec1, vec2)
        assert np.isclose(similarity, 0.0)


class TestConfigSmoke:
    """Smoke tests for configuration system."""

    def test_default_settings(self):
        """Test default settings can be created."""
        from markdown_reallocator.config import Settings

        settings = Settings()
        assert settings is not None
        assert settings.preprocessor is not None
        assert settings.embedder is not None

    def test_settings_to_dict(self):
        """Test settings can be converted to dict."""
        from markdown_reallocator.config import Settings

        settings = Settings()
        config_dict = settings.to_dict()
        assert isinstance(config_dict, dict)
        assert "preprocessor" in config_dict
        assert "embedder" in config_dict

    def test_settings_from_dict(self):
        """Test settings can be created from dict."""
        from markdown_reallocator.config import Settings

        config_dict = {
            "preprocessor": {"max_title_length": 100},
            "embedder": {"batch_size": 20},
        }
        settings = Settings.from_dict(config_dict)
        assert settings.preprocessor.max_title_length == 100
        assert settings.embedder.batch_size == 20
