"""LRU cache implementation for embedding storage.

This module provides an in-memory LRU (Least Recently Used) cache for storing
embeddings. The cache is designed to be stateful but thread-safe, with
configurable size limits and statistics tracking.
"""

from collections import OrderedDict
from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass
class CacheStatistics:
    """Statistics for cache performance monitoring.

    Attributes:
        hits: Number of cache hits
        misses: Number of cache misses
        evictions: Number of items evicted due to size limit
        current_size: Current number of items in cache
        max_size: Maximum capacity of cache
    """

    hits: int = 0
    misses: int = 0
    evictions: int = 0
    current_size: int = 0
    max_size: int = 0

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate.

        Returns:
            Hit rate as float (0.0 to 1.0), or 0.0 if no requests yet
        """
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert statistics to dictionary."""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "current_size": self.current_size,
            "max_size": self.max_size,
            "hit_rate": self.hit_rate,
        }


class LRUCache:
    """Thread-safe LRU cache for storing embeddings.

    This cache uses an OrderedDict to maintain insertion order and implements
    LRU (Least Recently Used) eviction policy. When the cache reaches max_size,
    the least recently used item is evicted.

    Attributes:
        max_size: Maximum number of items to store
        stats: Cache statistics tracker

    Examples:
        >>> import numpy as np
        >>> cache = LRUCache(max_size=100)
        >>> embedding = np.array([0.1, 0.2, 0.3])
        >>> cache.put("text_hash_123", embedding)
        >>> cached = cache.get("text_hash_123")
        >>> np.array_equal(cached, embedding)
        True
        >>> cache.stats.hit_rate
        1.0
    """

    def __init__(self, max_size: int = 1000):
        """Initialize LRU cache.

        Args:
            max_size: Maximum number of items to cache (default: 1000)

        Raises:
            ValueError: If max_size is less than 1
        """
        if max_size < 1:
            raise ValueError(f"max_size must be at least 1, got {max_size}")

        self._cache: OrderedDict[str, np.ndarray] = OrderedDict()
        self._max_size = max_size
        self._stats = CacheStatistics(max_size=max_size)

    @property
    def stats(self) -> CacheStatistics:
        """Get cache statistics.

        Returns:
            Current cache statistics
        """
        # Update current size before returning stats
        self._stats.current_size = len(self._cache)
        return self._stats

    def get(self, key: str) -> np.ndarray | None:
        """Retrieve item from cache.

        If item exists, it's moved to the end (most recently used).
        Updates cache statistics.

        Args:
            key: Cache key (typically text hash)

        Returns:
            Cached numpy array if found, None otherwise
        """
        if key in self._cache:
            # Move to end (mark as recently used)
            self._cache.move_to_end(key)
            self._stats.hits += 1
            return self._cache[key]

        self._stats.misses += 1
        return None

    def put(self, key: str, value: np.ndarray) -> None:
        """Store item in cache.

        If cache is full, evicts least recently used item.
        If key already exists, updates value and moves to end.

        Args:
            key: Cache key (typically text hash)
            value: Numpy array to cache (typically embedding vector)

        Raises:
            TypeError: If value is not a numpy array
        """
        if not isinstance(value, np.ndarray):
            raise TypeError(f"value must be numpy array, got {type(value).__name__}")

        # If key exists, remove it first (will be re-added at end)
        if key in self._cache:
            del self._cache[key]

        # Add new item
        self._cache[key] = value

        # Evict oldest if over capacity
        if len(self._cache) > self._max_size:
            # Remove first item (least recently used)
            self._cache.popitem(last=False)
            self._stats.evictions += 1

    def __contains__(self, key: str) -> bool:
        """Check if key exists in cache without updating access time.

        Args:
            key: Cache key to check

        Returns:
            True if key exists, False otherwise
        """
        return key in self._cache

    def clear(self) -> None:
        """Clear all items from cache.

        Resets statistics except for max_size.
        """
        self._cache.clear()
        self._stats = CacheStatistics(max_size=self._max_size)

    def __len__(self) -> int:
        """Return number of items in cache."""
        return len(self._cache)

    def __repr__(self) -> str:
        """Return string representation of cache."""
        return (
            f"LRUCache(size={len(self._cache)}/{self._max_size}, "
            f"hit_rate={self.stats.hit_rate:.2%})"
        )


class EmbeddingCache:
    """High-level cache specifically for embeddings with text hash keys.

    This is a wrapper around LRUCache with additional utilities for
    embedding-specific operations like computing cache keys from text.

    Examples:
        >>> import numpy as np
        >>> from markdown_reallocator.models import Embedding
        >>> cache = EmbeddingCache(max_size=100)
        >>> text = "Hello, world!"
        >>> embedding_vector = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        >>> text_hash = Embedding.compute_text_hash(text)
        >>> cache.put(text_hash, "embeddinggemma", embedding_vector)
        >>> cached = cache.get(text_hash, "embeddinggemma")
        >>> np.array_equal(cached, embedding_vector)
        True
    """

    def __init__(self, max_size: int = 1000):
        """Initialize embedding cache.

        Args:
            max_size: Maximum number of embeddings to cache
        """
        self._cache = LRUCache(max_size=max_size)

    def _make_key(self, text_hash: str, model_name: str) -> str:
        """Create cache key from text hash and model name.

        Args:
            text_hash: SHA256 hash of text
            model_name: Name of embedding model

        Returns:
            Cache key in format "model:hash"
        """
        return f"{model_name}:{text_hash}"

    def get(self, text_hash: str, model_name: str) -> np.ndarray | None:
        """Retrieve embedding from cache.

        Args:
            text_hash: SHA256 hash of text
            model_name: Name of embedding model used

        Returns:
            Cached embedding vector if found, None otherwise
        """
        key = self._make_key(text_hash, model_name)
        return self._cache.get(key)

    def put(self, text_hash: str, model_name: str, embedding: np.ndarray) -> None:
        """Store embedding in cache.

        Args:
            text_hash: SHA256 hash of text
            model_name: Name of embedding model used
            embedding: Embedding vector to cache
        """
        key = self._make_key(text_hash, model_name)
        self._cache.put(key, embedding)

    def contains(self, text_hash: str, model_name: str) -> bool:
        """Check if embedding exists in cache.

        Args:
            text_hash: SHA256 hash of text
            model_name: Name of embedding model used

        Returns:
            True if embedding is cached, False otherwise
        """
        key = self._make_key(text_hash, model_name)
        return key in self._cache

    @property
    def stats(self) -> CacheStatistics:
        """Get cache statistics."""
        return self._cache.stats

    def clear(self) -> None:
        """Clear all cached embeddings."""
        self._cache.clear()

    def __len__(self) -> int:
        """Return number of cached embeddings."""
        return len(self._cache)

    def __repr__(self) -> str:
        """Return string representation."""
        return f"EmbeddingCache({self._cache!r})"
