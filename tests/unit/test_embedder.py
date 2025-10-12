"""Tests for embedder."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np
import pytest

from markdown_reallocator.core.embedder import Embedder
from markdown_reallocator.models.chunk import Chunk, ChunkMetadata


@pytest.fixture
def sample_chunk() -> Chunk:
    """Create a sample chunk for testing."""
    return Chunk(
        chunk_id="test_chunk_1",
        content="This is test content for embedding.",
        metadata=ChunkMetadata(h1="Test", original_position=0),
    )


@pytest.fixture
def sample_chunks() -> list[Chunk]:
    """Create multiple sample chunks for testing."""
    return [
        Chunk(
            chunk_id=f"chunk_{i}",
            content=f"Content for chunk {i}",
            metadata=ChunkMetadata(original_position=i),
        )
        for i in range(5)
    ]


class TestEmbedderInitialization:
    """Tests for Embedder initialization."""

    def test_default_initialization(self) -> None:
        """Should initialize with default settings."""
        embedder = Embedder()

        assert embedder.model_name == "embeddinggemma"
        assert embedder.cache_enabled is True
        assert embedder.batch_size == 10
        assert embedder.memory_threshold_mb == 1500.0

    def test_custom_configuration(self) -> None:
        """Should accept custom configuration."""
        embedder = Embedder(
            model_name="custom-model",
            cache_enabled=False,
            batch_size=20,
            memory_threshold_mb=2000.0,
        )

        assert embedder.model_name == "custom-model"
        assert embedder.cache_enabled is False
        assert embedder.batch_size == 20
        assert embedder.memory_threshold_mb == 2000.0

    def test_cache_initialized_when_enabled(self) -> None:
        """Should initialize cache when enabled."""
        embedder = Embedder(cache_enabled=True, cache_max_size=500)

        assert embedder._cache is not None

    def test_cache_not_initialized_when_disabled(self) -> None:
        """Should not initialize cache when disabled."""
        embedder = Embedder(cache_enabled=False)

        assert embedder._cache is None


class TestTextHashing:
    """Tests for text hashing."""

    def test_hash_deterministic(self) -> None:
        """Hash should be deterministic."""
        embedder = Embedder()
        text = "Test text for hashing"

        hash1 = embedder._compute_text_hash(text)
        hash2 = embedder._compute_text_hash(text)

        assert hash1 == hash2

    def test_different_text_different_hash(self) -> None:
        """Different text should produce different hashes."""
        embedder = Embedder()

        hash1 = embedder._compute_text_hash("Text 1")
        hash2 = embedder._compute_text_hash("Text 2")

        assert hash1 != hash2

    def test_hash_length(self) -> None:
        """Hash should be 16 characters."""
        embedder = Embedder()
        text_hash = embedder._compute_text_hash("Test")

        assert len(text_hash) == 16


class TestModelLoading:
    """Tests for model loading."""

    @patch("markdown_reallocator.core.embedder.load_embedding_model")
    @patch("markdown_reallocator.core.embedder.check_gpu_memory_available")
    def test_lazy_loading(self, mock_check_mem, mock_load_model) -> None:
        """Model should not load until first use."""
        mock_check_mem.return_value = True
        mock_client = Mock()
        mock_load_model.return_value = mock_client

        embedder = Embedder()

        # Model not loaded yet
        assert embedder._model_loaded is False

        # Trigger loading
        embedder._ensure_model_loaded()

        # Model should now be loaded
        assert embedder._model_loaded is True
        mock_load_model.assert_called_once()

    @patch("markdown_reallocator.core.embedder.load_embedding_model")
    @patch("markdown_reallocator.core.embedder.check_gpu_memory_available")
    def test_model_loaded_once(self, mock_check_mem, mock_load_model) -> None:
        """Model should only load once."""
        mock_check_mem.return_value = True
        mock_client = Mock()
        mock_load_model.return_value = mock_client

        embedder = Embedder()

        embedder._ensure_model_loaded()
        embedder._ensure_model_loaded()

        # Should only call once
        assert mock_load_model.call_count == 1

    @patch("markdown_reallocator.core.embedder.load_embedding_model")
    @patch("markdown_reallocator.core.embedder.check_gpu_memory_available")
    def test_warns_on_low_memory(self, mock_check_mem, mock_load_model, caplog: pytest.LogCaptureFixture) -> None:
        """Should warn when GPU memory is low."""
        mock_check_mem.return_value = False
        mock_client = Mock()
        mock_load_model.return_value = mock_client

        embedder = Embedder()
        embedder._ensure_model_loaded()

        assert any("GPU memory may be insufficient" in record.message for record in caplog.records)

    @patch("markdown_reallocator.core.embedder.load_embedding_model")
    @patch("markdown_reallocator.core.embedder.check_gpu_memory_available")
    def test_loading_failure_raises(self, mock_check_mem, mock_load_model) -> None:
        """Should raise RuntimeError if loading fails."""
        mock_check_mem.return_value = True
        mock_load_model.side_effect = Exception("Model not found")

        embedder = Embedder()

        with pytest.raises(RuntimeError, match="Failed to load embedding model"):
            embedder._ensure_model_loaded()


class TestSingleChunkEmbedding:
    """Tests for single chunk embedding."""

    @patch("markdown_reallocator.core.embedder.GPUMemoryMonitor")
    @patch("markdown_reallocator.core.embedder.load_embedding_model")
    @patch("markdown_reallocator.core.embedder.check_gpu_memory_available")
    def test_embed_chunk_success(
        self,
        mock_check_mem,
        mock_load_model,
        mock_monitor,
        sample_chunk: Chunk,
    ) -> None:
        """Should successfully embed a chunk."""
        mock_check_mem.return_value = True

        # Mock Ollama client
        mock_client = Mock()
        mock_client.embeddings.return_value = {
            "embedding": [0.1, 0.2, 0.3, 0.4]
        }
        mock_load_model.return_value = mock_client

        # Mock GPU monitor
        mock_monitor.return_value.__enter__.return_value = Mock()
        mock_monitor.return_value.__exit__.return_value = False

        embedder = Embedder()
        result = embedder.embed_chunk(sample_chunk)

        assert result.embedding is not None
        assert result.embedding.shape == (4,)
        assert np.allclose(result.embedding, [0.1, 0.2, 0.3, 0.4])

    @patch("markdown_reallocator.core.embedder.GPUMemoryMonitor")
    @patch("markdown_reallocator.core.embedder.load_embedding_model")
    @patch("markdown_reallocator.core.embedder.check_gpu_memory_available")
    def test_cache_hit_skips_api_call(
        self,
        mock_check_mem,
        mock_load_model,
        mock_monitor,
        sample_chunk: Chunk,
    ) -> None:
        """Should use cached embedding without API call."""
        mock_check_mem.return_value = True

        # Mock Ollama client
        mock_client = Mock()
        mock_client.embeddings.return_value = {
            "embedding": [0.1, 0.2, 0.3, 0.4]
        }
        mock_load_model.return_value = mock_client

        # Mock GPU monitor
        mock_monitor.return_value.__enter__.return_value = Mock()
        mock_monitor.return_value.__exit__.return_value = False

        embedder = Embedder(cache_enabled=True)

        # First call - should hit API
        embedder.embed_chunk(sample_chunk)
        assert mock_client.embeddings.call_count == 1

        # Second call - should use cache
        embedder.embed_chunk(sample_chunk)
        assert mock_client.embeddings.call_count == 1  # No additional call

    @patch("markdown_reallocator.core.embedder.GPUMemoryMonitor")
    @patch("markdown_reallocator.core.embedder.load_embedding_model")
    @patch("markdown_reallocator.core.embedder.check_gpu_memory_available")
    def test_force_refresh_bypasses_cache(
        self,
        mock_check_mem,
        mock_load_model,
        mock_monitor,
        sample_chunk: Chunk,
    ) -> None:
        """Should bypass cache when force_refresh=True."""
        mock_check_mem.return_value = True

        # Mock Ollama client
        mock_client = Mock()
        mock_client.embeddings.return_value = {
            "embedding": [0.1, 0.2, 0.3, 0.4]
        }
        mock_load_model.return_value = mock_client

        # Mock GPU monitor
        mock_monitor.return_value.__enter__.return_value = Mock()
        mock_monitor.return_value.__exit__.return_value = False

        embedder = Embedder(cache_enabled=True)

        # First call
        embedder.embed_chunk(sample_chunk)

        # Second call with force_refresh
        embedder.embed_chunk(sample_chunk, force_refresh=True)

        assert mock_client.embeddings.call_count == 2

    @patch("markdown_reallocator.core.embedder.load_embedding_model")
    @patch("markdown_reallocator.core.embedder.check_gpu_memory_available")
    def test_no_embedding_response_raises(
        self,
        mock_check_mem,
        mock_load_model,
        sample_chunk: Chunk,
    ) -> None:
        """Should raise if API doesn't return embedding."""
        mock_check_mem.return_value = True

        # Mock Ollama client with missing embedding
        mock_client = Mock()
        mock_client.embeddings.return_value = {"model": "test"}
        mock_load_model.return_value = mock_client

        embedder = Embedder()

        with pytest.raises(RuntimeError, match="did not return embedding"):
            embedder.embed_chunk(sample_chunk)

    @patch("markdown_reallocator.core.embedder.load_embedding_model")
    @patch("markdown_reallocator.core.embedder.check_gpu_memory_available")
    def test_api_failure_raises(
        self,
        mock_check_mem,
        mock_load_model,
        sample_chunk: Chunk,
    ) -> None:
        """Should raise if API call fails."""
        mock_check_mem.return_value = True

        # Mock Ollama client that raises
        mock_client = Mock()
        mock_client.embeddings.side_effect = Exception("API error")
        mock_load_model.return_value = mock_client

        embedder = Embedder()

        with pytest.raises(RuntimeError, match="Embedding generation failed"):
            embedder.embed_chunk(sample_chunk)


class TestBatchEmbedding:
    """Tests for batch embedding."""

    @patch("markdown_reallocator.core.embedder.GPUMemoryMonitor")
    @patch("markdown_reallocator.core.embedder.load_embedding_model")
    @patch("markdown_reallocator.core.embedder.check_gpu_memory_available")
    def test_batch_embed_all_chunks(
        self,
        mock_check_mem,
        mock_load_model,
        mock_monitor,
        sample_chunks: list[Chunk],
    ) -> None:
        """Should embed all chunks in batch."""
        mock_check_mem.return_value = True

        # Mock Ollama client
        mock_client = Mock()
        mock_client.embeddings.return_value = {
            "embedding": [0.1, 0.2, 0.3, 0.4]
        }
        mock_load_model.return_value = mock_client

        # Mock GPU monitor
        mock_monitor.return_value.__enter__.return_value = Mock()
        mock_monitor.return_value.__exit__.return_value = False

        embedder = Embedder(batch_size=2)
        result = embedder.embed_batch(sample_chunks)

        assert len(result) == 5
        assert all(c.embedding is not None for c in result)

    @patch("markdown_reallocator.core.embedder.GPUMemoryMonitor")
    @patch("markdown_reallocator.core.embedder.load_embedding_model")
    @patch("markdown_reallocator.core.embedder.check_gpu_memory_available")
    def test_progress_callback_called(
        self,
        mock_check_mem,
        mock_load_model,
        mock_monitor,
        sample_chunks: list[Chunk],
    ) -> None:
        """Should call progress callback."""
        mock_check_mem.return_value = True

        # Mock Ollama client
        mock_client = Mock()
        mock_client.embeddings.return_value = {
            "embedding": [0.1, 0.2, 0.3, 0.4]
        }
        mock_load_model.return_value = mock_client

        # Mock GPU monitor
        mock_monitor.return_value.__enter__.return_value = Mock()
        mock_monitor.return_value.__exit__.return_value = False

        embedder = Embedder(batch_size=2)

        progress_calls = []

        def progress_callback(current: int, total: int) -> None:
            progress_calls.append((current, total))

        embedder.embed_batch(sample_chunks, progress_callback=progress_callback)

        # Should have been called for each batch
        assert len(progress_calls) > 0
        assert progress_calls[-1] == (5, 5)  # Final call

    @patch("markdown_reallocator.core.embedder.GPUMemoryMonitor")
    @patch("markdown_reallocator.core.embedder.load_embedding_model")
    @patch("markdown_reallocator.core.embedder.check_gpu_memory_available")
    def test_individual_failures_logged_not_raised(
        self,
        mock_check_mem,
        mock_load_model,
        mock_monitor,
        sample_chunks: list[Chunk],
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Individual failures should be logged but not stop processing."""
        mock_check_mem.return_value = True

        # Mock Ollama client that fails for one chunk
        mock_client = Mock()
        call_count = 0

        def embeddings_side_effect(*args: object, **kwargs: object) -> dict[str, list[float]]:
            nonlocal call_count
            call_count += 1
            if call_count == 2:  # Fail on second chunk
                raise Exception("Transient error")
            return {"embedding": [0.1, 0.2, 0.3, 0.4]}

        mock_client.embeddings.side_effect = embeddings_side_effect
        mock_load_model.return_value = mock_client

        # Mock GPU monitor
        mock_monitor.return_value.__enter__.return_value = Mock()
        mock_monitor.return_value.__exit__.return_value = False

        embedder = Embedder()
        result = embedder.embed_batch(sample_chunks)

        # Should still return all chunks
        assert len(result) == 5

        # Should have logged warnings
        assert any("Failed to embed chunk" in record.message for record in caplog.records)

    def test_empty_list_returns_empty(self) -> None:
        """Should handle empty chunk list."""
        embedder = Embedder()
        result = embedder.embed_batch([])

        assert result == []


class TestCacheManagement:
    """Tests for cache management."""

    @patch("markdown_reallocator.core.embedder.load_embedding_model")
    @patch("markdown_reallocator.core.embedder.check_gpu_memory_available")
    def test_get_cache_stats_when_enabled(
        self,
        mock_check_mem,
        mock_load_model,
        sample_chunk: Chunk,
    ) -> None:
        """Should return cache stats when cache enabled."""
        mock_check_mem.return_value = True
        mock_client = Mock()
        mock_client.embeddings.return_value = {"embedding": [0.1, 0.2, 0.3]}
        mock_load_model.return_value = mock_client

        embedder = Embedder(cache_enabled=True)
        embedder.embed_chunk(sample_chunk)

        stats = embedder.get_cache_stats()

        assert stats is not None
        assert "hits" in stats
        assert "misses" in stats
        assert "hit_rate" in stats

    def test_get_cache_stats_when_disabled(self) -> None:
        """Should return None when cache disabled."""
        embedder = Embedder(cache_enabled=False)
        stats = embedder.get_cache_stats()

        assert stats is None

    def test_clear_cache(self) -> None:
        """Should clear cache."""
        embedder = Embedder(cache_enabled=True)
        embedder.clear_cache()

        # Should not raise


class TestSaveLoadEmbeddings:
    """Tests for saving and loading embeddings."""

    @patch("markdown_reallocator.core.embedder.load_embedding_model")
    @patch("markdown_reallocator.core.embedder.check_gpu_memory_available")
    def test_save_embeddings(
        self,
        mock_check_mem,
        mock_load_model,
        sample_chunks: list[Chunk],
    ) -> None:
        """Should save embeddings to file."""
        # Add embeddings to chunks
        for chunk in sample_chunks:
            chunk.embedding = np.array([0.1, 0.2, 0.3], dtype=np.float32)

        embedder = Embedder()

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "embeddings.npz"

            embedder.save_embeddings(sample_chunks, str(filepath))

            assert filepath.exists()

    def test_save_no_embeddings_raises(self, sample_chunks: list[Chunk]) -> None:
        """Should raise if no chunks have embeddings."""
        embedder = Embedder()

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "embeddings.npz"

            with pytest.raises(ValueError, match="No chunks have embeddings"):
                embedder.save_embeddings(sample_chunks, str(filepath))

    @patch("markdown_reallocator.core.embedder.load_embedding_model")
    @patch("markdown_reallocator.core.embedder.check_gpu_memory_available")
    def test_load_embeddings(
        self,
        mock_check_mem,
        mock_load_model,
        sample_chunks: list[Chunk],
    ) -> None:
        """Should load embeddings from file."""
        # Save embeddings first
        for chunk in sample_chunks:
            chunk.embedding = np.array([0.1, 0.2, 0.3], dtype=np.float32)

        embedder = Embedder()

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "embeddings.npz"

            embedder.save_embeddings(sample_chunks, str(filepath))

            # Clear embeddings
            for chunk in sample_chunks:
                chunk.embedding = None

            # Load back
            embedder.load_embeddings(sample_chunks, str(filepath))

            assert all(c.embedding is not None for c in sample_chunks)

    def test_load_nonexistent_file_raises(self, sample_chunks: list[Chunk]) -> None:
        """Should raise if file doesn't exist."""
        embedder = Embedder()

        with pytest.raises(FileNotFoundError):
            embedder.load_embeddings(sample_chunks, "/nonexistent/file.npz")


class TestIntegration:
    """Integration tests."""

    @patch("markdown_reallocator.core.embedder.GPUMemoryMonitor")
    @patch("markdown_reallocator.core.embedder.load_embedding_model")
    @patch("markdown_reallocator.core.embedder.check_gpu_memory_available")
    def test_full_workflow(
        self,
        mock_check_mem,
        mock_load_model,
        mock_monitor,
        sample_chunks: list[Chunk],
    ) -> None:
        """Test complete workflow: batch embed, cache, save, load."""
        mock_check_mem.return_value = True

        # Mock Ollama client
        mock_client = Mock()
        mock_client.embeddings.return_value = {
            "embedding": list(np.random.randn(384))
        }
        mock_load_model.return_value = mock_client

        # Mock GPU monitor
        mock_monitor.return_value.__enter__.return_value = Mock()
        mock_monitor.return_value.__exit__.return_value = False

        embedder = Embedder(cache_enabled=True)

        # Batch embed
        embedded = embedder.embed_batch(sample_chunks)
        assert len(embedded) == 5

        # Check cache stats
        stats = embedder.get_cache_stats()
        assert stats is not None

        # Save
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test.npz"
            embedder.save_embeddings(embedded, str(filepath))

            # Clear embeddings
            for chunk in embedded:
                chunk.embedding = None

            # Load
            embedder.load_embeddings(embedded, str(filepath))

            assert all(c.embedding is not None for c in embedded)


class TestBranchCoverage:
    """Tests specifically for branch coverage."""

    @patch("markdown_reallocator.core.embedder.GPUMemoryMonitor")
    @patch("markdown_reallocator.core.embedder.load_embedding_model")
    @patch("markdown_reallocator.core.embedder.check_gpu_memory_available")
    def test_embed_chunk_cache_disabled_path(
        self,
        mock_check_mem,
        mock_load_model,
        mock_monitor,
        sample_chunk: Chunk,
    ) -> None:
        """Should cover branch 162->169 when cache is disabled."""
        mock_check_mem.return_value = True

        # Mock Ollama client
        mock_client = Mock()
        mock_client.embeddings.return_value = {
            "embedding": [0.1, 0.2, 0.3, 0.4]
        }
        mock_load_model.return_value = mock_client

        # Mock GPU monitor
        mock_monitor.return_value.__enter__.return_value = Mock()
        mock_monitor.return_value.__exit__.return_value = False

        # Cache disabled - this should hit the branch 162->169
        embedder = Embedder(cache_enabled=False)
        result = embedder.embed_chunk(sample_chunk)

        assert result.embedding is not None
        assert result.embedding.shape == (4,)

    def test_clear_cache_when_cache_is_none(self) -> None:
        """Should cover branch 267->exit when cache is None."""
        # Cache disabled - _cache is None
        embedder = Embedder(cache_enabled=False)

        # This should hit the early exit branch 267->exit
        embedder.clear_cache()

        # Should not raise, just return early

    @patch("markdown_reallocator.core.embedder.load_embedding_model")
    @patch("markdown_reallocator.core.embedder.check_gpu_memory_available")
    def test_save_embeddings_loop_coverage(
        self,
        mock_check_mem,
        mock_load_model,
    ) -> None:
        """Should cover branch 294->293 loop in save_embeddings."""
        # Create chunks with varying embedding presence
        chunks = [
            Chunk(
                chunk_id="chunk_1",
                content="Content 1",
                metadata=ChunkMetadata(original_position=0),
            ),
            Chunk(
                chunk_id="chunk_2",
                content="Content 2",
                metadata=ChunkMetadata(original_position=1),
            ),
        ]

        # Add embeddings to both chunks
        chunks[0].embedding = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        chunks[1].embedding = np.array([0.4, 0.5, 0.6], dtype=np.float32)

        embedder = Embedder()

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "embeddings.npz"

            # This should iterate through all chunks, covering the loop
            embedder.save_embeddings(chunks, str(filepath))

            assert filepath.exists()

    @patch("markdown_reallocator.core.embedder.load_embedding_model")
    @patch("markdown_reallocator.core.embedder.check_gpu_memory_available")
    def test_load_embeddings_loop_coverage(
        self,
        mock_check_mem,
        mock_load_model,
    ) -> None:
        """Should cover branch 326->325 loop in load_embeddings."""
        # Create chunks with embeddings
        chunks = [
            Chunk(
                chunk_id="chunk_1",
                content="Content 1",
                metadata=ChunkMetadata(original_position=0),
            ),
            Chunk(
                chunk_id="chunk_2",
                content="Content 2",
                metadata=ChunkMetadata(original_position=1),
            ),
        ]

        # Add embeddings
        for chunk in chunks:
            chunk.embedding = np.array([0.1, 0.2, 0.3], dtype=np.float32)

        embedder = Embedder()

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "embeddings.npz"

            # Save embeddings
            embedder.save_embeddings(chunks, str(filepath))

            # Clear embeddings
            for chunk in chunks:
                chunk.embedding = None

            # Load - this should iterate through all chunks, covering the loop
            embedder.load_embeddings(chunks, str(filepath))

            # Verify all chunks got embeddings
            assert all(c.embedding is not None for c in chunks)

    @patch("markdown_reallocator.core.embedder.load_embedding_model")
    @patch("markdown_reallocator.core.embedder.check_gpu_memory_available")
    def test_client_not_initialized_defensive_check(
        self,
        mock_check_mem,
        mock_load_model,
        sample_chunk: Chunk,
    ) -> None:
        """Should cover line 140 defensive check for uninitialized client."""
        mock_check_mem.return_value = True

        # Mock load_embedding_model to return None (edge case)
        mock_load_model.return_value = None

        embedder = Embedder()

        # This should trigger _ensure_model_loaded which sets _client to None
        # Then embed_chunk should hit line 140 and raise RuntimeError
        with pytest.raises(RuntimeError, match="Ollama client not initialized"):
            embedder.embed_chunk(sample_chunk)
