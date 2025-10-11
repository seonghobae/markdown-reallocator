"""Similarity computation utilities for embeddings.

This module provides efficient cosine similarity calculations optimized for
numpy arrays. All functions are stateless and use vectorized operations for
performance on CPUs with SSE4.2 support (Westmere and newer).
"""

import numpy as np


def cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
    """Compute cosine similarity between two vectors.

    Cosine similarity is defined as: dot(v1, v2) / (||v1|| * ||v2||)
    Returns a value in [-1, 1] where:
    - 1: vectors point in same direction (identical)
    - 0: vectors are orthogonal (unrelated)
    - -1: vectors point in opposite directions

    Args:
        v1: First vector (1D numpy array)
        v2: Second vector (1D numpy array, same dimension as v1)

    Returns:
        Cosine similarity score as float

    Raises:
        ValueError: If vectors have different dimensions or are not 1D
        ValueError: If either vector has zero norm (undefined similarity)

    Examples:
        >>> import numpy as np
        >>> v1 = np.array([1, 0, 0])
        >>> v2 = np.array([1, 0, 0])
        >>> cosine_similarity(v1, v2)
        1.0
        >>> v3 = np.array([0, 1, 0])
        >>> cosine_similarity(v1, v3)
        0.0
    """
    # Validate inputs
    if v1.ndim != 1 or v2.ndim != 1:
        raise ValueError(f"Vectors must be 1-dimensional, got shapes {v1.shape} and {v2.shape}")

    if v1.shape[0] != v2.shape[0]:
        raise ValueError(
            f"Vectors must have same dimension, got {v1.shape[0]} and {v2.shape[0]}"
        )

    # Compute norms
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)

    # Check for zero vectors
    if norm1 == 0 or norm2 == 0:
        raise ValueError("Cannot compute similarity with zero vector")

    # Compute cosine similarity
    # Use numpy.dot for SSE4.2 optimization
    similarity = np.dot(v1, v2) / (norm1 * norm2)

    return float(similarity)


def cosine_similarity_normalized(v1: np.ndarray, v2: np.ndarray) -> float:
    """Compute cosine similarity for pre-normalized vectors.

    This is a faster version when vectors are already normalized (norm = 1).
    If vectors are not normalized, results will be incorrect.

    Args:
        v1: First normalized vector (1D numpy array with norm=1)
        v2: Second normalized vector (1D numpy array with norm=1)

    Returns:
        Cosine similarity score as float (equivalent to dot product)

    Raises:
        ValueError: If vectors have different dimensions or are not 1D

    Examples:
        >>> import numpy as np
        >>> v1 = np.array([1.0, 0.0, 0.0])  # Already normalized
        >>> v2 = np.array([0.0, 1.0, 0.0])  # Already normalized
        >>> cosine_similarity_normalized(v1, v2)
        0.0
    """
    # Validate inputs
    if v1.ndim != 1 or v2.ndim != 1:
        raise ValueError(f"Vectors must be 1-dimensional, got shapes {v1.shape} and {v2.shape}")

    if v1.shape[0] != v2.shape[0]:
        raise ValueError(
            f"Vectors must have same dimension, got {v1.shape[0]} and {v2.shape[0]}"
        )

    # For normalized vectors, cosine similarity = dot product
    return float(np.dot(v1, v2))


def batch_cosine_similarity(vectors: np.ndarray, query: np.ndarray) -> np.ndarray:
    """Compute cosine similarity between a query vector and multiple vectors.

    This is a vectorized implementation that computes similarities in parallel,
    achieving 10x+ speedup over looping through vectors individually.

    Args:
        vectors: Matrix of vectors (shape: [n_vectors, dimension])
        query: Single query vector (shape: [dimension])

    Returns:
        Array of similarity scores (shape: [n_vectors])
        Each score corresponds to similarity between query and that vector

    Raises:
        ValueError: If dimensions don't match or inputs have wrong shape
        ValueError: If query or any vector has zero norm

    Examples:
        >>> import numpy as np
        >>> vectors = np.array([[1, 0, 0], [0, 1, 0], [1, 1, 0]])
        >>> query = np.array([1, 0, 0])
        >>> batch_cosine_similarity(vectors, query)
        array([1., 0., 0.707...])
    """
    # Validate inputs
    if vectors.ndim != 2:
        raise ValueError(f"vectors must be 2-dimensional, got shape {vectors.shape}")

    if query.ndim != 1:
        raise ValueError(f"query must be 1-dimensional, got shape {query.shape}")

    if vectors.shape[1] != query.shape[0]:
        raise ValueError(
            f"Dimension mismatch: vectors have dimension {vectors.shape[1]}, "
            f"query has dimension {query.shape[0]}"
        )

    # Compute query norm
    query_norm = np.linalg.norm(query)
    if query_norm == 0:
        raise ValueError("Cannot compute similarity with zero query vector")

    # Compute norms for all vectors
    # Use axis=1 to compute norm for each row
    vector_norms = np.linalg.norm(vectors, axis=1)

    # Check for zero vectors
    if np.any(vector_norms == 0):
        zero_indices = np.where(vector_norms == 0)[0]
        raise ValueError(f"Cannot compute similarity with zero vectors at indices {zero_indices}")

    # Compute dot products in parallel
    # This is the key optimization: matrix-vector multiplication
    dot_products = np.dot(vectors, query)

    # Compute similarities
    similarities = dot_products / (vector_norms * query_norm)

    return similarities  # type: ignore[no-any-return]


def batch_cosine_similarity_normalized(
    vectors: np.ndarray, query: np.ndarray
) -> np.ndarray:
    """Compute cosine similarity for pre-normalized vectors (batch version).

    This is the fastest version when all vectors and query are normalized.
    If vectors are not normalized, results will be incorrect.

    Args:
        vectors: Matrix of normalized vectors (shape: [n_vectors, dimension])
        query: Single normalized query vector (shape: [dimension])

    Returns:
        Array of similarity scores (shape: [n_vectors])

    Raises:
        ValueError: If dimensions don't match or inputs have wrong shape

    Examples:
        >>> import numpy as np
        >>> vectors = np.array([[1.0, 0.0], [0.0, 1.0], [0.707, 0.707]])
        >>> query = np.array([1.0, 0.0])
        >>> batch_cosine_similarity_normalized(vectors, query)
        array([1.   , 0.   , 0.707])
    """
    # Validate inputs
    if vectors.ndim != 2:
        raise ValueError(f"vectors must be 2-dimensional, got shape {vectors.shape}")

    if query.ndim != 1:
        raise ValueError(f"query must be 1-dimensional, got shape {query.shape}")

    if vectors.shape[1] != query.shape[0]:
        raise ValueError(
            f"Dimension mismatch: vectors have dimension {vectors.shape[1]}, "
            f"query has dimension {query.shape[0]}"
        )

    # For normalized vectors, cosine similarity = dot product
    return np.dot(vectors, query)  # type: ignore[no-any-return]


def pairwise_cosine_similarity(vectors: np.ndarray) -> np.ndarray:
    """Compute pairwise cosine similarities between all vectors.

    Returns a symmetric matrix where element [i, j] is the cosine similarity
    between vectors[i] and vectors[j].

    Args:
        vectors: Matrix of vectors (shape: [n_vectors, dimension])

    Returns:
        Similarity matrix (shape: [n_vectors, n_vectors])
        Diagonal elements are 1.0 (self-similarity)
        Matrix is symmetric

    Raises:
        ValueError: If input is not 2D
        ValueError: If any vector has zero norm

    Examples:
        >>> import numpy as np
        >>> vectors = np.array([[1, 0], [0, 1], [1, 1]])
        >>> pairwise_cosine_similarity(vectors)
        array([[1.   , 0.   , 0.707],
               [0.   , 1.   , 0.707],
               [0.707, 0.707, 1.   ]])
    """
    # Validate input
    if vectors.ndim != 2:
        raise ValueError(f"vectors must be 2-dimensional, got shape {vectors.shape}")

    # Compute norms
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)

    # Check for zero vectors
    if np.any(norms == 0):
        zero_indices = np.where(norms.squeeze() == 0)[0]
        raise ValueError(f"Cannot compute similarity with zero vectors at indices {zero_indices}")

    # Normalize vectors
    normalized = vectors / norms

    # Compute similarity matrix using matrix multiplication
    # This is highly optimized in numpy
    similarity_matrix = np.dot(normalized, normalized.T)

    return similarity_matrix  # type: ignore[no-any-return]
