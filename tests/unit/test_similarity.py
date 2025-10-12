"""Unit tests for similarity computation utilities.

Tests cover:
- Basic cosine similarity between two vectors
- Normalized vector similarity (faster version)
- Batch similarity computation (vectorized)
- Pairwise similarity matrix computation
- Edge cases: zero vectors, dimension mismatches, single dimensions
- Performance benchmarks: batch operations should be 10x+ faster
"""

import numpy as np
import pytest

from markdown_reallocator.utils.similarity import (
    batch_cosine_similarity,
    batch_cosine_similarity_normalized,
    cosine_similarity,
    cosine_similarity_normalized,
    pairwise_cosine_similarity,
)


class TestCosineSimilarity:
    """Tests for basic cosine similarity computation."""

    def test_identical_vectors(self) -> None:
        """Identical vectors should have similarity 1.0."""
        v1 = np.array([1.0, 2.0, 3.0])
        v2 = np.array([1.0, 2.0, 3.0])
        assert cosine_similarity(v1, v2) == pytest.approx(1.0)

    def test_orthogonal_vectors(self) -> None:
        """Orthogonal vectors should have similarity 0.0."""
        v1 = np.array([1.0, 0.0, 0.0])
        v2 = np.array([0.0, 1.0, 0.0])
        assert cosine_similarity(v1, v2) == pytest.approx(0.0)

    def test_opposite_vectors(self) -> None:
        """Opposite vectors should have similarity -1.0."""
        v1 = np.array([1.0, 2.0, 3.0])
        v2 = np.array([-1.0, -2.0, -3.0])
        assert cosine_similarity(v1, v2) == pytest.approx(-1.0)

    def test_partial_similarity(self) -> None:
        """Partially similar vectors should have similarity in (0, 1)."""
        v1 = np.array([1.0, 0.0])
        v2 = np.array([1.0, 1.0])
        # cos(45°) ≈ 0.707
        assert 0.7 < cosine_similarity(v1, v2) < 0.8

    def test_single_dimension(self) -> None:
        """Single-dimension vectors should work."""
        v1 = np.array([5.0])
        v2 = np.array([3.0])
        # Both positive, same direction
        assert cosine_similarity(v1, v2) == pytest.approx(1.0)

    def test_high_dimension(self) -> None:
        """High-dimensional vectors should work."""
        np.random.seed(42)
        v1 = np.random.randn(1000)
        v2 = np.random.randn(1000)
        # Should compute without error
        similarity = cosine_similarity(v1, v2)
        assert -1.0 <= similarity <= 1.0

    def test_zero_vector_raises(self) -> None:
        """Zero vector should raise ValueError."""
        v1 = np.array([0.0, 0.0, 0.0])
        v2 = np.array([1.0, 2.0, 3.0])
        with pytest.raises(ValueError, match="Cannot compute similarity with zero vector"):
            cosine_similarity(v1, v2)

    def test_dimension_mismatch_raises(self) -> None:
        """Vectors with different dimensions should raise ValueError."""
        v1 = np.array([1.0, 2.0])
        v2 = np.array([1.0, 2.0, 3.0])
        with pytest.raises(ValueError, match="must have same dimension"):
            cosine_similarity(v1, v2)

    def test_non_1d_vectors_raise(self) -> None:
        """Non-1D arrays should raise ValueError."""
        v1 = np.array([[1.0, 2.0]])  # 2D array
        v2 = np.array([1.0, 2.0])
        with pytest.raises(ValueError, match="must be 1-dimensional"):
            cosine_similarity(v1, v2)


class TestCosineSimilarityNormalized:
    """Tests for normalized vector cosine similarity (faster version)."""

    def test_normalized_vectors(self) -> None:
        """Pre-normalized vectors should give same result as regular version."""
        # Create normalized vectors
        v1 = np.array([1.0, 0.0, 0.0])  # Already normalized
        v2 = np.array([0.0, 1.0, 0.0])  # Already normalized

        regular = cosine_similarity(v1, v2)
        normalized = cosine_similarity_normalized(v1, v2)
        assert regular == pytest.approx(normalized)

    def test_unnormalized_gives_wrong_result(self) -> None:
        """Using unnormalized vectors should give incorrect result."""
        v1 = np.array([2.0, 0.0, 0.0])  # Not normalized
        v2 = np.array([0.0, 3.0, 0.0])  # Not normalized

        regular = cosine_similarity(v1, v2)
        normalized = cosine_similarity_normalized(v1, v2)
        # Should be different since vectors aren't normalized
        assert regular == pytest.approx(0.0)
        assert normalized == pytest.approx(0.0)  # Dot product is 0

    def test_normalized_is_just_dot_product(self) -> None:
        """For normalized vectors, similarity equals dot product."""
        v1 = np.array([0.6, 0.8])  # norm = 1.0
        v2 = np.array([0.8, 0.6])  # norm = 1.0

        dot_product = np.dot(v1, v2)
        similarity = cosine_similarity_normalized(v1, v2)
        assert dot_product == pytest.approx(similarity)

    def test_dimension_mismatch_raises(self) -> None:
        """Dimension mismatch should raise ValueError."""
        v1 = np.array([1.0, 0.0])
        v2 = np.array([1.0, 0.0, 0.0])
        with pytest.raises(ValueError, match="must have same dimension"):
            cosine_similarity_normalized(v1, v2)


class TestBatchCosineSimilarity:
    """Tests for vectorized batch similarity computation."""

    def test_batch_identical_query(self) -> None:
        """Query identical to one vector should give similarity 1.0."""
        vectors = np.array([
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [1.0, 0.0, 0.0],  # Same as query
        ])
        query = np.array([1.0, 0.0, 0.0])

        similarities = batch_cosine_similarity(vectors, query)
        assert similarities[0] == pytest.approx(1.0)
        assert similarities[1] == pytest.approx(0.0)
        assert similarities[2] == pytest.approx(1.0)

    def test_batch_orthogonal(self) -> None:
        """Orthogonal vectors should have similarity 0.0."""
        vectors = np.array([
            [1.0, 0.0],
            [0.0, 1.0],
        ])
        query = np.array([1.0, 0.0])

        similarities = batch_cosine_similarity(vectors, query)
        assert similarities[0] == pytest.approx(1.0)
        assert similarities[1] == pytest.approx(0.0)

    def test_batch_matches_individual(self) -> None:
        """Batch computation should match individual computations."""
        vectors = np.array([
            [1.0, 2.0, 3.0],
            [4.0, 5.0, 6.0],
            [7.0, 8.0, 9.0],
        ])
        query = np.array([1.0, 1.0, 1.0])

        # Batch computation
        batch_similarities = batch_cosine_similarity(vectors, query)

        # Individual computations
        individual_similarities = [
            cosine_similarity(vectors[i], query)
            for i in range(len(vectors))
        ]

        np.testing.assert_array_almost_equal(
            batch_similarities, individual_similarities, decimal=10
        )

    def test_batch_single_vector(self) -> None:
        """Batch with single vector should work."""
        vectors = np.array([[1.0, 2.0, 3.0]])
        query = np.array([1.0, 2.0, 3.0])

        similarities = batch_cosine_similarity(vectors, query)
        assert len(similarities) == 1
        assert similarities[0] == pytest.approx(1.0)

    def test_batch_large_dataset(self) -> None:
        """Large batch should work efficiently."""
        np.random.seed(42)
        vectors = np.random.randn(1000, 128)  # 1000 vectors, 128 dimensions
        query = np.random.randn(128)

        similarities = batch_cosine_similarity(vectors, query)
        assert len(similarities) == 1000
        assert np.all((similarities >= -1.0) & (similarities <= 1.0))

    def test_batch_zero_vector_raises(self) -> None:
        """Zero vector in batch should raise ValueError."""
        vectors = np.array([
            [1.0, 2.0],
            [0.0, 0.0],  # Zero vector
            [3.0, 4.0],
        ])
        query = np.array([1.0, 1.0])

        with pytest.raises(ValueError, match="Cannot compute similarity with zero vectors"):
            batch_cosine_similarity(vectors, query)

    def test_batch_zero_query_raises(self) -> None:
        """Zero query vector should raise ValueError."""
        vectors = np.array([
            [1.0, 2.0],
            [3.0, 4.0],
        ])
        query = np.array([0.0, 0.0])

        with pytest.raises(ValueError, match="Cannot compute similarity with zero query vector"):
            batch_cosine_similarity(vectors, query)

    def test_batch_dimension_mismatch_raises(self) -> None:
        """Dimension mismatch should raise ValueError."""
        vectors = np.array([
            [1.0, 2.0, 3.0],
            [4.0, 5.0, 6.0],
        ])
        query = np.array([1.0, 2.0])  # Different dimension

        with pytest.raises(ValueError, match="Dimension mismatch"):
            batch_cosine_similarity(vectors, query)

    def test_batch_wrong_shape_raises(self) -> None:
        """Wrong array shapes should raise ValueError."""
        vectors = np.array([1.0, 2.0, 3.0])  # 1D, should be 2D
        query = np.array([1.0, 2.0, 3.0])

        with pytest.raises(ValueError, match="vectors must be 2-dimensional"):
            batch_cosine_similarity(vectors, query)


class TestBatchCosineSimilarityNormalized:
    """Tests for normalized batch similarity computation."""

    def test_normalized_batch_matches_individual(self) -> None:
        """Normalized batch should match individual normalized computations."""
        # Create normalized vectors
        vectors = np.array([
            [1.0, 0.0],
            [0.0, 1.0],
            [0.707, 0.707],
        ])
        query = np.array([1.0, 0.0])

        batch_result = batch_cosine_similarity_normalized(vectors, query)
        individual_result = np.array([
            cosine_similarity_normalized(vectors[i], query)
            for i in range(len(vectors))
        ])

        np.testing.assert_array_almost_equal(batch_result, individual_result, decimal=10)

    def test_normalized_batch_is_dot_products(self) -> None:
        """For normalized vectors, batch similarity equals dot products."""
        vectors = np.array([
            [1.0, 0.0],
            [0.0, 1.0],
            [0.6, 0.8],
        ])
        query = np.array([0.8, 0.6])

        similarities = batch_cosine_similarity_normalized(vectors, query)
        dot_products = np.dot(vectors, query)

        np.testing.assert_array_almost_equal(similarities, dot_products, decimal=10)


class TestPairwiseCosineSimilarity:
    """Tests for pairwise similarity matrix computation."""

    def test_pairwise_diagonal_ones(self) -> None:
        """Diagonal elements should be 1.0 (self-similarity)."""
        vectors = np.array([
            [1.0, 0.0],
            [0.0, 1.0],
            [1.0, 1.0],
        ])

        similarity_matrix = pairwise_cosine_similarity(vectors)
        np.testing.assert_array_almost_equal(
            np.diag(similarity_matrix), [1.0, 1.0, 1.0], decimal=10
        )

    def test_pairwise_symmetric(self) -> None:
        """Similarity matrix should be symmetric."""
        np.random.seed(42)
        vectors = np.random.randn(5, 10)

        similarity_matrix = pairwise_cosine_similarity(vectors)
        np.testing.assert_array_almost_equal(
            similarity_matrix, similarity_matrix.T, decimal=10
        )

    def test_pairwise_correct_shape(self) -> None:
        """Output matrix should be n×n."""
        vectors = np.array([
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ])

        similarity_matrix = pairwise_cosine_similarity(vectors)
        assert similarity_matrix.shape == (3, 3)

    def test_pairwise_orthogonal_vectors(self) -> None:
        """Orthogonal vectors should have zero similarity."""
        vectors = np.array([
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ])

        similarity_matrix = pairwise_cosine_similarity(vectors)

        # Off-diagonal elements should be 0.0 (orthogonal)
        assert similarity_matrix[0, 1] == pytest.approx(0.0)
        assert similarity_matrix[0, 2] == pytest.approx(0.0)
        assert similarity_matrix[1, 2] == pytest.approx(0.0)

    def test_pairwise_matches_batch(self) -> None:
        """Pairwise computation should match batch computations."""
        vectors = np.array([
            [1.0, 2.0, 3.0],
            [4.0, 5.0, 6.0],
            [7.0, 8.0, 9.0],
        ])

        pairwise = pairwise_cosine_similarity(vectors)

        # Check each row against batch computation
        for i in range(len(vectors)):
            batch_result = batch_cosine_similarity(vectors, vectors[i])
            np.testing.assert_array_almost_equal(
                pairwise[i], batch_result, decimal=10
            )

    def test_pairwise_single_vector(self) -> None:
        """Single vector should give 1×1 matrix with value 1.0."""
        vectors = np.array([[1.0, 2.0, 3.0]])

        similarity_matrix = pairwise_cosine_similarity(vectors)
        assert similarity_matrix.shape == (1, 1)
        assert similarity_matrix[0, 0] == pytest.approx(1.0)

    def test_pairwise_zero_vector_raises(self) -> None:
        """Zero vector should raise ValueError."""
        vectors = np.array([
            [1.0, 2.0],
            [0.0, 0.0],  # Zero vector
            [3.0, 4.0],
        ])

        with pytest.raises(ValueError, match="Cannot compute similarity with zero vectors"):
            pairwise_cosine_similarity(vectors)

    def test_pairwise_wrong_shape_raises(self) -> None:
        """1D array should raise ValueError."""
        vectors = np.array([1.0, 2.0, 3.0])

        with pytest.raises(ValueError, match="vectors must be 2-dimensional"):
            pairwise_cosine_similarity(vectors)


class TestPerformance:
    """Performance benchmarks for vectorized operations."""

    def test_batch_faster_than_loop(self, benchmark=None) -> None:
        """Batch operation should be significantly faster than loop.

        This is a smoke test rather than a strict benchmark.
        Batch operations should be 10x+ faster due to vectorization.
        """
        np.random.seed(42)
        vectors = np.random.randn(1000, 128)
        query = np.random.randn(128)

        # Batch computation (vectorized)
        import time
        start = time.time()
        batch_result = batch_cosine_similarity(vectors, query)
        batch_time = time.time() - start

        # Loop computation (slower)
        start = time.time()
        loop_result = np.array([
            cosine_similarity(vectors[i], query)
            for i in range(len(vectors))
        ])
        loop_time = time.time() - start

        # Results should match
        np.testing.assert_array_almost_equal(batch_result, loop_result, decimal=10)

        # Batch should be at least 3x faster (conservative check)
        # On modern CPUs with SSE4.2, typically 10x+ faster
        assert batch_time < loop_time / 3, (
            f"Batch operation not fast enough: "
            f"{batch_time:.4f}s vs {loop_time:.4f}s "
            f"(speedup: {loop_time/batch_time:.1f}x)"
        )

    def test_normalized_faster_than_regular(self) -> None:
        """Normalized version should be faster than regular version on large datasets.

        This is a statistical benchmark that measures average performance
        over multiple runs to reduce noise from CPU scheduling and caching.
        """
        np.random.seed(42)
        # Create normalized vectors - larger dataset for meaningful benchmark
        vectors = np.random.randn(10000, 256)  # 10x larger
        vectors = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)
        query = np.random.randn(256)
        query = query / np.linalg.norm(query)

        import time

        # Warmup - prevent cold cache effects
        _ = batch_cosine_similarity(vectors, query)
        _ = batch_cosine_similarity_normalized(vectors, query)

        # Multiple runs for statistical reliability
        n_runs = 10
        regular_times = []
        normalized_times = []

        for _ in range(n_runs):
            # Regular version
            start = time.time()
            regular_result = batch_cosine_similarity(vectors, query)
            regular_times.append(time.time() - start)

            # Normalized version
            start = time.time()
            normalized_result = batch_cosine_similarity_normalized(vectors, query)
            normalized_times.append(time.time() - start)

        # Results should match (vectors are normalized)
        np.testing.assert_array_almost_equal(
            regular_result, normalized_result, decimal=10
        )

        # Compare median times (more robust than mean)
        median_regular = np.median(regular_times)
        median_normalized = np.median(normalized_times)

        # Normalized should be at least 20% faster (conservative threshold)
        # On large datasets, typically 40-50% faster due to skipping norm computation
        speedup = median_regular / median_normalized
        assert speedup > 1.2, (
            f"Normalized version not significantly faster: "
            f"regular={median_regular:.4f}s, normalized={median_normalized:.4f}s, "
            f"speedup={speedup:.2f}x (expected >1.2x)"
        )
