"""Embedder for generating semantic embeddings using Ollama.

This module provides embedding generation for markdown chunks using
embeddinggemma with caching and memory management.
"""

import hashlib
import logging
from collections.abc import Callable
from typing import Any

import numpy as np
import ollama

from markdown_reallocator.models.chunk import Chunk
from markdown_reallocator.utils.cache import EmbeddingCache
from markdown_reallocator.utils.memory import GPUMemoryMonitor, check_gpu_memory_available
from markdown_reallocator.utils.model_loader import load_embedding_model

logger = logging.getLogger(__name__)


class Embedder:
    """Embedder for generating semantic embeddings using Ollama.

    This class provides embedding generation with caching, memory monitoring,
    and batch processing capabilities.

    Examples:
        >>> embedder = Embedder()
        >>> chunk = Chunk(chunk_id="test", content="Hello world", metadata=ChunkMetadata())
        >>> embedded_chunk = embedder.embed_chunk(chunk)
        >>> embedded_chunk.embedding.shape
        (384,)
    """

    def __init__(
        self,
        model_name: str = "embeddinggemma",
        cache_enabled: bool = True,
        cache_max_size: int = 1000,
        batch_size: int = 10,
        memory_threshold_mb: float = 1500.0,
    ):
        """Initialize embedder with configuration.

        Args:
            model_name: Name of Ollama embedding model (default: "embeddinggemma")
            cache_enabled: Whether to enable embedding cache
            cache_max_size: Maximum cache size (number of embeddings)
            batch_size: Number of chunks to process in each batch
            memory_threshold_mb: Maximum GPU memory usage in MB
        """
        self.model_name = model_name
        self.cache_enabled = cache_enabled
        self.batch_size = batch_size
        self.memory_threshold_mb = memory_threshold_mb

        # Initialize cache if enabled
        self._cache: EmbeddingCache | None = None
        if cache_enabled:
            self._cache = EmbeddingCache(max_size=cache_max_size)

        # Lazy-loaded Ollama client
        self._client: ollama.Client | None = None
        self._model_loaded = False

    def _compute_text_hash(self, text: str) -> str:
        """Compute SHA256 hash of text for cache key.

        Args:
            text: Text to hash

        Returns:
            Hex string hash (16 characters)
        """
        hash_digest = hashlib.sha256(text.encode()).hexdigest()
        return hash_digest[:16]

    def _ensure_model_loaded(self) -> None:
        """Load Ollama model if not already loaded.

        Performs GPU memory check before loading model.

        Raises:
            RuntimeError: If GPU memory is insufficient or model loading fails
        """
        if self._model_loaded:
            return

        # Check GPU memory availability
        if not check_gpu_memory_available(self.memory_threshold_mb):
            logger.warning(
                f"GPU memory may be insufficient. Threshold: {self.memory_threshold_mb}MB"
            )

        try:
            self._client = load_embedding_model(
                model_name=self.model_name,
                retry_count=3,
                retry_delay=1.0,
            )
            self._model_loaded = True
            logger.info(f"Loaded embedding model: {self.model_name}")

        except Exception as e:
            raise RuntimeError(f"Failed to load embedding model: {e}") from e

    def embed_chunk(self, chunk: Chunk, force_refresh: bool = False) -> Chunk:
        """Generate embedding for a single chunk.

        Uses cache if enabled and embedding is cached. Updates chunk.embedding
        in-place and returns the modified chunk.

        Args:
            chunk: Chunk to embed
            force_refresh: Force regeneration even if cached

        Returns:
            Chunk with embedding populated

        Raises:
            RuntimeError: If model loading or embedding generation fails
        """
        # Compute text hash for cache lookup
        text_hash = self._compute_text_hash(chunk.content)

        # Check cache if enabled
        if self.cache_enabled and not force_refresh and self._cache is not None:
            cached_embedding = self._cache.get(text_hash, self.model_name)
            if cached_embedding is not None:
                chunk.embedding = cached_embedding
                logger.debug(f"Cache hit for chunk {chunk.chunk_id}")
                return chunk

        # Ensure model is loaded
        self._ensure_model_loaded()

        if not self._client:
            raise RuntimeError("Ollama client not initialized")

        try:
            # Generate embedding with GPU monitoring
            with GPUMemoryMonitor(warn_threshold=0.9):
                response = self._client.embeddings(
                    model=self.model_name,
                    prompt=chunk.content
                )

            # Extract embedding
            if "embedding" not in response:
                raise RuntimeError(
                    f"Model '{self.model_name}' did not return embedding"
                )

            embedding = np.array(response["embedding"], dtype=np.float32)

            # Update chunk
            chunk.embedding = embedding

            # Cache if enabled
            if self.cache_enabled and self._cache is not None:
                self._cache.put(text_hash, self.model_name, embedding)
                logger.debug(
                    f"Cached embedding for chunk {chunk.chunk_id} "
                    f"(text_hash={text_hash}, model={self.model_name})"
                )

            logger.debug(
                f"Generated embedding for chunk {chunk.chunk_id}: "
                f"dim={len(embedding)}"
            )

            return chunk

        except Exception as e:
            logger.error(f"Failed to generate embedding for chunk {chunk.chunk_id}: {e}")
            raise RuntimeError(f"Embedding generation failed: {e}") from e

    def embed_batch(
        self,
        chunks: list[Chunk],
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> list[Chunk]:
        """Generate embeddings for multiple chunks in batches.

        Processes chunks in batches to manage memory and provide progress updates.
        Individual failures are logged but don't halt the entire process.

        Args:
            chunks: List of chunks to embed
            progress_callback: Optional callback(current, total) for progress tracking

        Returns:
            List of chunks with embeddings populated

        Raises:
            RuntimeError: If model loading fails
        """
        if not chunks:
            return []

        # Ensure model is loaded once
        self._ensure_model_loaded()

        total = len(chunks)
        embedded_chunks: list[Chunk] = []
        failed_chunks: list[tuple[str, Exception]] = []

        # Process in batches
        for batch_start in range(0, total, self.batch_size):
            batch_end = min(batch_start + self.batch_size, total)
            batch = chunks[batch_start:batch_end]

            # Process each chunk in batch
            for chunk in batch:
                try:
                    self.embed_chunk(chunk)
                    embedded_chunks.append(chunk)

                except Exception as e:
                    logger.warning(
                        f"Failed to embed chunk {chunk.chunk_id}: {e}"
                    )
                    failed_chunks.append((chunk.chunk_id, e))
                    # Still add to list but without embedding
                    embedded_chunks.append(chunk)

            # Report progress
            if progress_callback:
                progress_callback(batch_end, total)

        # Log summary
        if failed_chunks:
            logger.warning(
                f"Batch embedding completed with {len(failed_chunks)} failures "
                f"out of {total} chunks"
            )
            for chunk_id, error in failed_chunks[:5]:  # Log first 5
                logger.warning(f"  - {chunk_id}: {error}")

        else:
            logger.info(f"Successfully embedded {total} chunks")

        return embedded_chunks

    def get_cache_stats(self) -> dict[str, Any] | None:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics or None if cache disabled
        """
        if not self.cache_enabled or self._cache is None:
            return None

        stats = self._cache.stats
        return {
            "hits": stats.hits,
            "misses": stats.misses,
            "hit_rate": stats.hit_rate,
            "current_size": stats.current_size,
            "max_size": stats.max_size,
        }

    def clear_cache(self) -> None:
        """Clear the embedding cache."""
        if self._cache is not None:
            self._cache.clear()
            logger.info("Embedding cache cleared")

    def save_embeddings(
        self,
        chunks: list[Chunk],
        filepath: str,
    ) -> None:
        """Save chunk embeddings to .npz file.

        Args:
            chunks: List of chunks with embeddings
            filepath: Path to save .npz file

        Raises:
            ValueError: If chunks have no embeddings
        """
        # Filter chunks with embeddings
        embedded_chunks = [c for c in chunks if c.embedding is not None]

        if not embedded_chunks:
            raise ValueError("No chunks have embeddings to save")

        # Prepare data - dict values must be non-None
        embeddings_dict: dict[str, np.ndarray] = {}
        for c in embedded_chunks:
            if c.embedding is not None:  # Type guard for mypy
                embeddings_dict[c.chunk_id] = c.embedding

        # Save as npz
        np.savez(filepath, **embeddings_dict)
        logger.info(
            f"Saved {len(embedded_chunks)} embeddings to {filepath}"
        )

    def load_embeddings(
        self,
        chunks: list[Chunk],
        filepath: str,
    ) -> list[Chunk]:
        """Load chunk embeddings from .npz file.

        Args:
            chunks: List of chunks to populate with embeddings
            filepath: Path to .npz file

        Returns:
            List of chunks with embeddings populated

        Raises:
            FileNotFoundError: If filepath doesn't exist
        """
        # Load npz file
        embeddings_data = np.load(filepath)

        # Match embeddings to chunks by ID
        loaded_count = 0
        for chunk in chunks:
            if chunk.chunk_id in embeddings_data:
                chunk.embedding = embeddings_data[chunk.chunk_id]
                loaded_count += 1

        logger.info(
            f"Loaded {loaded_count}/{len(chunks)} embeddings from {filepath}"
        )

        return chunks
