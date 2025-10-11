"""Module for reordering markdown chunks by semantic similarity.

This module provides strategies for reorganizing document chunks based on
their embedding similarity to improve document flow and coherence.
"""

import logging
from enum import Enum

import numpy as np

from markdown_reallocator.models.chunk import Chunk
from markdown_reallocator.utils.similarity import pairwise_cosine_similarity

logger = logging.getLogger(__name__)


class ReorderStrategy(Enum):
    """Reordering strategy options."""

    CLUSTER = "cluster"
    SEQUENTIAL = "sequential"


class ReorderModule:
    """Module for reordering document chunks by semantic similarity.

    This module provides two strategies for reorganizing chunks:
    - cluster: Group similar chunks together using hierarchical clustering
    - sequential: Chain chunks by highest similarity to previous chunk

    Examples:
        >>> reorder = ReorderModule(strategy="sequential")
        >>> chunks = [...]  # Chunks with embeddings
        >>> reordered = reorder.reorder(chunks)
        >>> markdown = reorder.reconstruct_markdown(reordered)
    """

    def __init__(
        self,
        strategy: str = "sequential",
        similarity_threshold: float = 0.5,
    ):
        """Initialize reorder module.

        Args:
            strategy: Reordering strategy ("cluster" or "sequential")
            similarity_threshold: Minimum similarity for considering chunks related (0.0-1.0)

        Raises:
            ValueError: If strategy is invalid or threshold out of range
        """
        # Validate strategy
        try:
            self.strategy = ReorderStrategy(strategy)
        except ValueError as e:
            valid = [s.value for s in ReorderStrategy]
            raise ValueError(
                f"Invalid strategy '{strategy}'. Must be one of: {valid}"
            ) from e

        # Validate threshold
        if not 0.0 <= similarity_threshold <= 1.0:
            raise ValueError(
                f"similarity_threshold must be in [0.0, 1.0], got {similarity_threshold}"
            )

        self.similarity_threshold = similarity_threshold

    def compute_similarity_matrix(
        self, chunks: list[Chunk]
    ) -> np.ndarray:
        """Compute pairwise similarity matrix for chunks.

        Args:
            chunks: List of chunks with embeddings

        Returns:
            Symmetric similarity matrix (n x n) where element [i,j] is
            cosine similarity between chunks[i] and chunks[j]

        Raises:
            ValueError: If any chunk is missing embedding
        """
        # Validate all chunks have embeddings
        for i, chunk in enumerate(chunks):
            if chunk.embedding is None:
                raise ValueError(
                    f"Chunk at index {i} (id={chunk.chunk_id}) has no embedding. "
                    "Run embedder first."
                )

        # Extract embeddings into matrix
        embeddings = np.array([chunk.embedding for chunk in chunks])

        # Compute pairwise similarities
        logger.debug(f"Computing similarity matrix for {len(chunks)} chunks")
        similarity_matrix = pairwise_cosine_similarity(embeddings)

        logger.debug(
            f"Similarity matrix computed: shape={similarity_matrix.shape}, "
            f"dtype={similarity_matrix.dtype}"
        )

        return similarity_matrix

    def reorder(self, chunks: list[Chunk]) -> list[Chunk]:
        """Reorder chunks using configured strategy.

        Args:
            chunks: List of chunks with embeddings

        Returns:
            Reordered list of chunks

        Raises:
            ValueError: If chunks list is empty or chunks lack embeddings
        """
        if not chunks:
            raise ValueError("Cannot reorder empty chunk list")

        # Compute similarity matrix
        similarity_matrix = self.compute_similarity_matrix(chunks)

        # Apply strategy
        if self.strategy == ReorderStrategy.SEQUENTIAL:
            return self._sequential_reorder(chunks, similarity_matrix)
        elif self.strategy == ReorderStrategy.CLUSTER:
            return self._cluster_reorder(chunks, similarity_matrix)
        else:
            raise NotImplementedError(f"Strategy {self.strategy} not implemented")

    def _sequential_reorder(
        self, chunks: list[Chunk], similarity_matrix: np.ndarray
    ) -> list[Chunk]:
        """Reorder chunks sequentially by chaining most similar chunks.

        Starts from a seed chunk and repeatedly selects the most similar
        unvisited chunk, creating a smooth semantic flow.

        Algorithm:
        1. Start with the first chunk as anchor
        2. Find the most similar unvisited chunk
        3. Add it to the sequence and mark as visited
        4. Repeat until all chunks are visited

        Args:
            chunks: Original chunks
            similarity_matrix: Precomputed similarity matrix

        Returns:
            Reordered chunks
        """
        n = len(chunks)
        if n == 0:
            return []
        if n == 1:
            return chunks.copy()

        # Track visited chunks
        visited = np.zeros(n, dtype=bool)
        reordered_indices = []

        # Start with first chunk (could be made configurable)
        current_idx = 0
        visited[current_idx] = True
        reordered_indices.append(current_idx)

        logger.debug(f"Starting sequential reorder with chunk {current_idx}")

        # Build sequence by chaining most similar chunks
        for _ in range(n - 1):
            # Get similarities from current chunk to all others
            similarities = similarity_matrix[current_idx]

            # Mask out visited chunks (set their similarity to -inf)
            similarities = similarities.copy()
            similarities[visited] = -np.inf

            # Find most similar unvisited chunk
            next_idx = int(np.argmax(similarities))
            max_similarity = similarities[next_idx]

            logger.debug(
                f"Chaining chunk {current_idx} -> {next_idx} "
                f"(similarity={max_similarity:.3f})"
            )

            # Add to sequence
            visited[next_idx] = True
            reordered_indices.append(next_idx)
            current_idx = next_idx

        # Build reordered chunk list
        reordered = [chunks[i] for i in reordered_indices]

        # Log statistics
        avg_similarity = self._compute_avg_adjacent_similarity(
            reordered_indices, similarity_matrix
        )
        logger.info(
            f"Sequential reorder complete: {n} chunks, "
            f"avg adjacent similarity={avg_similarity:.3f}"
        )

        return reordered

    def _compute_avg_adjacent_similarity(
        self, indices: list[int], similarity_matrix: np.ndarray
    ) -> float:
        """Compute average similarity between adjacent chunks in sequence.

        Args:
            indices: Sequence of chunk indices
            similarity_matrix: Similarity matrix

        Returns:
            Average similarity between adjacent chunks
        """
        if len(indices) < 2:
            return 1.0

        similarities = []
        for i in range(len(indices) - 1):
            sim = similarity_matrix[indices[i], indices[i + 1]]
            similarities.append(sim)

        return float(np.mean(similarities))

    def _cluster_reorder(
        self, chunks: list[Chunk], similarity_matrix: np.ndarray
    ) -> list[Chunk]:
        """Reorder chunks by clustering similar content together.

        Uses hierarchical clustering to group related chunks into
        coherent topics. Within each cluster, chunks are ordered by
        their original position to maintain logical flow.

        Algorithm:
        1. Convert similarity matrix to distance matrix (1 - similarity)
        2. Apply hierarchical clustering with average linkage
        3. Cut dendrogram to get 3-7 clusters (adaptive based on size)
        4. Sort clusters by first chunk's original position
        5. Within each cluster, maintain original order

        Args:
            chunks: Original chunks
            similarity_matrix: Precomputed similarity matrix

        Returns:
            Reordered chunks grouped by topic
        """
        from scipy.cluster.hierarchy import fcluster, linkage  # type: ignore[import-untyped]
        from scipy.spatial.distance import squareform  # type: ignore[import-untyped]

        n = len(chunks)
        if n == 0:
            return []
        if n == 1:
            return chunks.copy()

        # Convert similarity to distance (1 - similarity)
        # Clip to ensure non-negative distances (numerical stability)
        distance_matrix = np.clip(1 - similarity_matrix, 0, 2)

        # Convert to condensed form for scipy
        # Only upper triangle (scipy expects condensed distance matrix)
        condensed_distances = squareform(distance_matrix, checks=False)

        logger.debug(f"Computing hierarchical clustering for {n} chunks")

        # Perform hierarchical clustering
        linkage_matrix = linkage(condensed_distances, method="average")

        # Determine number of clusters (3-7 range, adaptive)
        # For small documents: fewer clusters
        # For large documents: more clusters
        if n <= 5:
            num_clusters = min(n, 3)
        elif n <= 20:
            num_clusters = min(n // 3, 5)
        else:
            num_clusters = min(n // 5, 7)

        logger.debug(f"Cutting dendrogram into {num_clusters} clusters")

        # Cut dendrogram to get cluster labels
        cluster_labels = fcluster(linkage_matrix, num_clusters, criterion="maxclust")

        # Group chunks by cluster
        clusters: dict[int, list[tuple[int, Chunk]]] = {}
        for i, label in enumerate(cluster_labels):
            if label not in clusters:
                clusters[label] = []
            clusters[label].append((i, chunks[i]))

        logger.debug(f"Created {len(clusters)} clusters: {[len(c) for c in clusters.values()]}")

        # Sort clusters by the original position of their first chunk
        sorted_clusters = sorted(
            clusters.values(),
            key=lambda cluster: min(idx for idx, _ in cluster)
        )

        # Within each cluster, maintain original order
        reordered: list[Chunk] = []
        for cluster in sorted_clusters:
            # Sort by original position within cluster
            cluster_sorted = sorted(cluster, key=lambda x: x[0])
            reordered.extend(chunk for _, chunk in cluster_sorted)

        # Log statistics
        cluster_sizes = [len(c) for c in sorted_clusters]
        logger.info(
            f"Cluster reorder complete: {n} chunks into {len(clusters)} clusters "
            f"(sizes: {cluster_sizes})"
        )

        return reordered

    def reconstruct_markdown(
        self, chunks: list[Chunk], include_comments: bool = False
    ) -> str:
        """Reconstruct markdown document from reordered chunks.

        Preserves header hierarchy and ensures proper spacing between chunks.
        Optionally includes HTML comments showing original positions.

        Args:
            chunks: Reordered chunks
            include_comments: If True, add HTML comments with original positions

        Returns:
            Reconstructed markdown as string

        Raises:
            ValueError: If chunks list is empty
        """
        if not chunks:
            raise ValueError("Cannot reconstruct markdown from empty chunk list")

        lines = []

        for i, chunk in enumerate(chunks):
            # Add comment with original position if requested
            if include_comments:
                orig_pos = chunk.metadata.original_position
                comment = f"<!-- Original position: {orig_pos}, Reordered position: {i} -->\n"
                lines.append(comment)

            # Add chunk content
            content = chunk.content.strip()
            if content:
                lines.append(content)

            # Add spacing between chunks (double newline for separation)
            if i < len(chunks) - 1:
                lines.append("")  # Single empty line between chunks

        # Join with newlines
        markdown = "\n".join(lines)

        # Ensure single trailing newline
        if not markdown.endswith("\n"):
            markdown += "\n"

        logger.info(
            f"Reconstructed markdown from {len(chunks)} chunks: "
            f"{len(markdown)} characters"
        )

        return markdown
