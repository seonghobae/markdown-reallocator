"""Unit tests for LRU cache implementation.

Tests cover:
- Basic cache operations (get, put, contains)
- LRU eviction policy when cache is full
- Statistics tracking (hits, misses, evictions, hit rate)
- EmbeddingCache wrapper functionality
- Edge cases: size limits, clearing, max_size=1
"""

import numpy as np
import pytest

from markdown_reallocator.utils.cache import (
    CacheStatistics,
    EmbeddingCache,
    LRUCache,
)


class TestCacheStatistics:
    """Tests for cache statistics dataclass."""

    def test_initial_stats(self) -> None:
        """Initial statistics should be zeros."""
        stats = CacheStatistics(max_size=100)
        assert stats.hits == 0
        assert stats.misses == 0
        assert stats.evictions == 0
        assert stats.current_size == 0
        assert stats.max_size == 100

    def test_hit_rate_zero_requests(self) -> None:
        """Hit rate should be 0.0 when no requests."""
        stats = CacheStatistics(max_size=100)
        assert stats.hit_rate == 0.0

    def test_hit_rate_calculation(self) -> None:
        """Hit rate should be hits / (hits + misses)."""
        stats = CacheStatistics(hits=7, misses=3, max_size=100)
        assert stats.hit_rate == pytest.approx(0.7)

    def test_hit_rate_all_hits(self) -> None:
        """Hit rate should be 1.0 when all hits."""
        stats = CacheStatistics(hits=10, misses=0, max_size=100)
        assert stats.hit_rate == pytest.approx(1.0)

    def test_hit_rate_all_misses(self) -> None:
        """Hit rate should be 0.0 when all misses."""
        stats = CacheStatistics(hits=0, misses=10, max_size=100)
        assert stats.hit_rate == pytest.approx(0.0)

    def test_to_dict(self) -> None:
        """to_dict should include all fields plus hit_rate."""
        stats = CacheStatistics(
            hits=5, misses=5, evictions=2, current_size=8, max_size=10
        )
        d = stats.to_dict()

        assert d["hits"] == 5
        assert d["misses"] == 5
        assert d["evictions"] == 2
        assert d["current_size"] == 8
        assert d["max_size"] == 10
        assert d["hit_rate"] == pytest.approx(0.5)


class TestLRUCache:
    """Tests for LRU cache implementation."""

    def test_initialization(self) -> None:
        """Cache should initialize with correct max_size."""
        cache = LRUCache(max_size=50)
        assert len(cache) == 0
        assert cache.stats.max_size == 50

    def test_invalid_max_size(self) -> None:
        """max_size < 1 should raise ValueError."""
        with pytest.raises(ValueError, match="max_size must be at least 1"):
            LRUCache(max_size=0)

        with pytest.raises(ValueError, match="max_size must be at least 1"):
            LRUCache(max_size=-5)

    def test_put_and_get(self) -> None:
        """Basic put and get operations should work."""
        cache = LRUCache(max_size=10)
        value = np.array([1.0, 2.0, 3.0])

        cache.put("key1", value)
        retrieved = cache.get("key1")

        assert retrieved is not None
        np.testing.assert_array_equal(retrieved, value)

    def test_get_nonexistent_returns_none(self) -> None:
        """Getting nonexistent key should return None."""
        cache = LRUCache(max_size=10)
        assert cache.get("nonexistent") is None

    def test_contains(self) -> None:
        """__contains__ should check key existence."""
        cache = LRUCache(max_size=10)
        value = np.array([1.0, 2.0, 3.0])

        assert "key1" not in cache
        cache.put("key1", value)
        assert "key1" in cache

    def test_update_existing_key(self) -> None:
        """Putting same key should update value."""
        cache = LRUCache(max_size=10)
        value1 = np.array([1.0, 2.0, 3.0])
        value2 = np.array([4.0, 5.0, 6.0])

        cache.put("key1", value1)
        cache.put("key1", value2)

        retrieved = cache.get("key1")
        np.testing.assert_array_equal(retrieved, value2)
        assert len(cache) == 1

    def test_lru_eviction(self) -> None:
        """Least recently used item should be evicted when full."""
        cache = LRUCache(max_size=3)

        cache.put("key1", np.array([1.0]))
        cache.put("key2", np.array([2.0]))
        cache.put("key3", np.array([3.0]))

        # Cache is full, next put should evict key1 (least recently used)
        cache.put("key4", np.array([4.0]))

        assert "key1" not in cache
        assert "key2" in cache
        assert "key3" in cache
        assert "key4" in cache
        assert len(cache) == 3

    def test_get_updates_lru_order(self) -> None:
        """Getting a key should mark it as recently used."""
        cache = LRUCache(max_size=3)

        cache.put("key1", np.array([1.0]))
        cache.put("key2", np.array([2.0]))
        cache.put("key3", np.array([3.0]))

        # Access key1 to mark as recently used
        _ = cache.get("key1")

        # Add new key, should evict key2 (oldest unreferenced)
        cache.put("key4", np.array([4.0]))

        assert "key1" in cache  # Recently accessed
        assert "key2" not in cache  # Evicted
        assert "key3" in cache
        assert "key4" in cache

    def test_statistics_tracking(self) -> None:
        """Cache should track hits, misses, and evictions."""
        cache = LRUCache(max_size=2)

        # First access: miss
        cache.get("key1")
        assert cache.stats.hits == 0
        assert cache.stats.misses == 1

        # Put and get: hit
        cache.put("key1", np.array([1.0]))
        cache.get("key1")
        assert cache.stats.hits == 1
        assert cache.stats.misses == 1

        # Another miss
        cache.get("key2")
        assert cache.stats.hits == 1
        assert cache.stats.misses == 2

        # Fill cache
        cache.put("key2", np.array([2.0]))
        assert cache.stats.evictions == 0

        # Trigger eviction
        cache.put("key3", np.array([3.0]))
        assert cache.stats.evictions == 1

    def test_hit_rate(self) -> None:
        """Hit rate should be calculated correctly."""
        cache = LRUCache(max_size=10)

        cache.put("key1", np.array([1.0]))
        cache.put("key2", np.array([2.0]))

        cache.get("key1")  # Hit
        cache.get("key2")  # Hit
        cache.get("key3")  # Miss

        # 2 hits, 1 miss = 2/3 ≈ 0.667
        assert cache.stats.hit_rate == pytest.approx(2.0 / 3.0)

    def test_clear(self) -> None:
        """Clear should remove all items and reset stats."""
        cache = LRUCache(max_size=10)

        cache.put("key1", np.array([1.0]))
        cache.put("key2", np.array([2.0]))
        cache.get("key1")  # Generate some stats

        cache.clear()

        assert len(cache) == 0
        assert "key1" not in cache
        assert "key2" not in cache
        assert cache.stats.hits == 0
        assert cache.stats.misses == 0
        assert cache.stats.evictions == 0
        assert cache.stats.max_size == 10  # Should preserve max_size

    def test_len(self) -> None:
        """__len__ should return current number of items."""
        cache = LRUCache(max_size=10)

        assert len(cache) == 0
        cache.put("key1", np.array([1.0]))
        assert len(cache) == 1
        cache.put("key2", np.array([2.0]))
        assert len(cache) == 2

    def test_put_non_numpy_raises(self) -> None:
        """Putting non-numpy value should raise TypeError."""
        cache = LRUCache(max_size=10)

        with pytest.raises(TypeError, match="value must be numpy array"):
            cache.put("key1", [1.0, 2.0, 3.0])  # List, not numpy array

        with pytest.raises(TypeError, match="value must be numpy array"):
            cache.put("key2", "not an array")

    def test_repr(self) -> None:
        """__repr__ should show size and hit rate."""
        cache = LRUCache(max_size=100)
        cache.put("key1", np.array([1.0]))

        repr_str = repr(cache)
        assert "1/100" in repr_str
        assert "hit_rate" in repr_str or "%" in repr_str

    def test_max_size_one(self) -> None:
        """Cache with max_size=1 should work correctly."""
        cache = LRUCache(max_size=1)

        cache.put("key1", np.array([1.0]))
        assert "key1" in cache

        cache.put("key2", np.array([2.0]))
        assert "key1" not in cache  # Evicted
        assert "key2" in cache
        assert len(cache) == 1

    def test_large_cache(self) -> None:
        """Cache should handle large number of items."""
        cache = LRUCache(max_size=1000)

        # Add 1000 items
        for i in range(1000):
            cache.put(f"key{i}", np.array([float(i)]))

        assert len(cache) == 1000

        # Add one more, should evict key0
        cache.put("key1000", np.array([1000.0]))
        assert "key0" not in cache
        assert "key1000" in cache
        assert len(cache) == 1000

    def test_different_array_shapes(self) -> None:
        """Cache should handle arrays of different shapes."""
        cache = LRUCache(max_size=10)

        cache.put("1d", np.array([1.0, 2.0, 3.0]))
        cache.put("2d", np.array([[1.0, 2.0], [3.0, 4.0]]))
        cache.put("scalar", np.array(42.0))

        assert cache.get("1d").shape == (3,)
        assert cache.get("2d").shape == (2, 2)
        assert cache.get("scalar").shape == ()


class TestEmbeddingCache:
    """Tests for EmbeddingCache wrapper."""

    def test_initialization(self) -> None:
        """EmbeddingCache should initialize with max_size."""
        cache = EmbeddingCache(max_size=50)
        assert len(cache) == 0
        assert cache.stats.max_size == 50

    def test_put_and_get_with_model(self) -> None:
        """Should store and retrieve with text_hash and model_name."""
        cache = EmbeddingCache(max_size=10)
        embedding = np.array([0.1, 0.2, 0.3], dtype=np.float32)

        cache.put("hash123", "embeddinggemma", embedding)
        retrieved = cache.get("hash123", "embeddinggemma")

        assert retrieved is not None
        np.testing.assert_array_equal(retrieved, embedding)

    def test_different_models_different_keys(self) -> None:
        """Same text_hash with different models should be separate entries."""
        cache = EmbeddingCache(max_size=10)
        embedding1 = np.array([0.1, 0.2, 0.3])
        embedding2 = np.array([0.4, 0.5, 0.6])

        cache.put("hash123", "model1", embedding1)
        cache.put("hash123", "model2", embedding2)

        retrieved1 = cache.get("hash123", "model1")
        retrieved2 = cache.get("hash123", "model2")

        np.testing.assert_array_equal(retrieved1, embedding1)
        np.testing.assert_array_equal(retrieved2, embedding2)
        assert len(cache) == 2

    def test_contains(self) -> None:
        """contains should check existence with text_hash and model_name."""
        cache = EmbeddingCache(max_size=10)
        embedding = np.array([0.1, 0.2, 0.3])

        assert not cache.contains("hash123", "embeddinggemma")
        cache.put("hash123", "embeddinggemma", embedding)
        assert cache.contains("hash123", "embeddinggemma")

    def test_get_nonexistent(self) -> None:
        """Getting nonexistent embedding should return None."""
        cache = EmbeddingCache(max_size=10)
        assert cache.get("nonexistent", "embeddinggemma") is None

    def test_lru_eviction_with_models(self) -> None:
        """LRU eviction should work with composite keys."""
        cache = EmbeddingCache(max_size=3)

        cache.put("hash1", "model1", np.array([1.0]))
        cache.put("hash2", "model1", np.array([2.0]))
        cache.put("hash3", "model1", np.array([3.0]))

        # Cache is full
        assert len(cache) == 3

        # Add another, should evict oldest
        cache.put("hash4", "model1", np.array([4.0]))

        assert not cache.contains("hash1", "model1")  # Evicted
        assert cache.contains("hash4", "model1")
        assert len(cache) == 3

    def test_statistics(self) -> None:
        """Statistics should be accessible."""
        cache = EmbeddingCache(max_size=10)

        cache.put("hash1", "model1", np.array([1.0]))
        cache.get("hash1", "model1")  # Hit
        cache.get("hash2", "model1")  # Miss

        assert cache.stats.hits == 1
        assert cache.stats.misses == 1
        assert cache.stats.hit_rate == pytest.approx(0.5)

    def test_clear(self) -> None:
        """Clear should remove all cached embeddings."""
        cache = EmbeddingCache(max_size=10)

        cache.put("hash1", "model1", np.array([1.0]))
        cache.put("hash2", "model1", np.array([2.0]))

        cache.clear()

        assert len(cache) == 0
        assert not cache.contains("hash1", "model1")
        assert not cache.contains("hash2", "model1")

    def test_repr(self) -> None:
        """__repr__ should be informative."""
        cache = EmbeddingCache(max_size=100)
        cache.put("hash1", "model1", np.array([1.0]))

        repr_str = repr(cache)
        assert "EmbeddingCache" in repr_str
        assert "LRUCache" in repr_str

    def test_realistic_usage_pattern(self) -> None:
        """Test realistic embedding cache usage pattern."""
        cache = EmbeddingCache(max_size=100)

        # Simulate processing documents with same model
        for i in range(50):
            text_hash = f"doc{i}_hash"
            embedding = np.random.randn(384)  # embeddinggemma dimension
            cache.put(text_hash, "embeddinggemma", embedding)

        # Access some embeddings (simulate cache hits)
        for i in range(0, 50, 5):
            text_hash = f"doc{i}_hash"
            retrieved = cache.get(text_hash, "embeddinggemma")
            assert retrieved is not None
            assert retrieved.shape == (384,)

        # Should have high hit rate
        assert cache.stats.hits > 0
        assert len(cache) == 50

    def test_key_format(self) -> None:
        """Cache keys should follow model:hash format."""
        cache = EmbeddingCache(max_size=10)
        embedding = np.array([0.1, 0.2, 0.3])

        cache.put("abc123", "embeddinggemma", embedding)

        # Internal key should be "embeddinggemma:abc123"
        # Verify by checking we can't retrieve with different model
        assert cache.get("abc123", "embeddinggemma") is not None
        assert cache.get("abc123", "different_model") is None


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_empty_string_key(self) -> None:
        """Empty string should work as a key."""
        cache = LRUCache(max_size=10)
        cache.put("", np.array([1.0]))
        assert "" in cache
        np.testing.assert_array_equal(cache.get(""), np.array([1.0]))

    def test_very_long_key(self) -> None:
        """Very long keys should work."""
        cache = LRUCache(max_size=10)
        long_key = "a" * 10000
        cache.put(long_key, np.array([1.0]))
        assert long_key in cache

    def test_unicode_keys(self) -> None:
        """Unicode keys should work."""
        cache = LRUCache(max_size=10)
        cache.put("한글", np.array([1.0]))
        cache.put("日本語", np.array([2.0]))
        cache.put("🔥", np.array([3.0]))

        assert "한글" in cache
        assert "日本語" in cache
        assert "🔥" in cache

    def test_zero_dimensional_array(self) -> None:
        """Zero-dimensional arrays (scalars) should work."""
        cache = LRUCache(max_size=10)
        scalar = np.array(42.0)
        cache.put("scalar", scalar)

        retrieved = cache.get("scalar")
        assert retrieved.shape == ()
        assert retrieved.item() == 42.0

    def test_large_embeddings(self) -> None:
        """Large embedding vectors should work."""
        cache = EmbeddingCache(max_size=10)
        # Simulate large embedding (e.g., from BERT-large)
        large_embedding = np.random.randn(1024)

        cache.put("hash", "bert-large", large_embedding)
        retrieved = cache.get("hash", "bert-large")

        assert retrieved.shape == (1024,)
        np.testing.assert_array_equal(retrieved, large_embedding)

    def test_repeated_puts_same_key(self) -> None:
        """Repeatedly putting same key should not cause issues."""
        cache = LRUCache(max_size=10)

        for i in range(100):
            cache.put("same_key", np.array([float(i)]))

        # Should only have one item
        assert len(cache) == 1
        # Should have latest value
        np.testing.assert_array_equal(cache.get("same_key"), np.array([99.0]))
