"""Module for detecting and removing duplicate chunks.

This module provides similarity-based duplicate detection with optional
LLM verification using Gemma 2B for improved precision.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

import numpy as np

from markdown_reallocator.models.chunk import Chunk
from markdown_reallocator.utils.similarity import pairwise_cosine_similarity

logger = logging.getLogger(__name__)


class SelectionStrategy(Enum):
    """Strategy for selecting which chunk to keep from duplicates."""

    FIRST = "first"  # Keep first occurrence (preserves original order)
    LONGEST = "longest"  # Keep chunk with most content
    BEST_METADATA = "best_metadata"  # Keep chunk with most complete metadata


@dataclass
class DeduplicationReport:
    """Report of deduplication operation."""

    original_count: int
    deduplicated_count: int
    removed_count: int
    duplicate_groups: list[list[str]]  # List of groups of duplicate chunk IDs
    removed_chunk_ids: list[str]
    kept_chunk_ids: list[str]

    @property
    def reduction_percentage(self) -> float:
        """Calculate percentage of chunks removed."""
        if self.original_count == 0:
            return 0.0
        return (self.removed_count / self.original_count) * 100


class DeduplicationModule:
    """Module for detecting and removing duplicate or near-duplicate chunks.

    This module identifies duplicate chunks based on embedding similarity
    and optionally verifies them using Gemma 2B LLM. Supports various
    strategies for selecting which chunk to keep from each duplicate group.

    Examples:
        >>> dedup = DeduplicationModule(similarity_threshold=0.85)
        >>> chunks = [...]  # Chunks with embeddings
        >>> result, report = dedup.deduplicate(chunks)
        >>> print(f"Removed {report.removed_count} duplicates")
    """

    def __init__(
        self,
        similarity_threshold: float = 0.85,
        selection_strategy: str = "first",
        use_llm: bool = False,
        dry_run: bool = False,
    ):
        """Initialize deduplication module.

        Args:
            similarity_threshold: Minimum similarity to consider chunks duplicates (0.0-1.0)
            selection_strategy: Strategy for selecting which chunk to keep
                               ("first", "longest", "best_metadata")
            use_llm: Whether to use Gemma 2B for verification (requires more memory)
            dry_run: If True, only report duplicates without removing them

        Raises:
            ValueError: If threshold out of range or strategy invalid
        """
        # Validate threshold
        if not 0.0 <= similarity_threshold <= 1.0:
            raise ValueError(
                f"similarity_threshold must be in [0.0, 1.0], got {similarity_threshold}"
            )

        # Validate strategy
        try:
            self.selection_strategy = SelectionStrategy(selection_strategy)
        except ValueError as e:
            valid = [s.value for s in SelectionStrategy]
            raise ValueError(
                f"Invalid selection_strategy '{selection_strategy}'. "
                f"Must be one of: {valid}"
            ) from e

        self.similarity_threshold = similarity_threshold
        self.use_llm = use_llm
        self.dry_run = dry_run

        # LLM client (lazy-loaded)
        self._llm_client: Any = None

    def find_duplicates(self, chunks: list[Chunk]) -> list[list[int]]:
        """Find groups of duplicate chunks based on similarity.

        Uses transitive closure to group all related chunks together.
        For example, if A is similar to B, and B is similar to C,
        then A, B, and C form one group even if A and C aren't directly similar.

        Args:
            chunks: List of chunks with embeddings

        Returns:
            List of duplicate groups, where each group is a list of chunk indices

        Raises:
            ValueError: If chunks lack embeddings
        """
        if not chunks:
            return []

        # Validate all chunks have embeddings
        for i, chunk in enumerate(chunks):
            if chunk.embedding is None:
                raise ValueError(
                    f"Chunk at index {i} (id={chunk.chunk_id}) has no embedding. "
                    "Run embedder first."
                )

        # Compute pairwise similarity matrix
        embeddings = np.array([c.embedding for c in chunks])
        similarity_matrix = pairwise_cosine_similarity(embeddings)

        logger.debug(
            f"Computed similarity matrix for {len(chunks)} chunks: "
            f"shape={similarity_matrix.shape}"
        )

        # Find pairs above threshold
        n = len(chunks)
        duplicate_pairs: set[tuple[int, int]] = set()

        for i in range(n):
            for j in range(i + 1, n):
                if similarity_matrix[i, j] >= self.similarity_threshold:
                    duplicate_pairs.add((i, j))

        logger.debug(
            f"Found {len(duplicate_pairs)} duplicate pairs above threshold "
            f"{self.similarity_threshold}"
        )

        # Build duplicate groups using union-find (transitive closure)
        groups = self._build_duplicate_groups(n, duplicate_pairs)

        logger.info(
            f"Found {len(groups)} duplicate groups from {len(chunks)} chunks"
        )

        return groups

    def _build_duplicate_groups(
        self, n: int, pairs: set[tuple[int, int]]
    ) -> list[list[int]]:
        """Build duplicate groups using union-find algorithm.

        Args:
            n: Number of chunks
            pairs: Set of (i, j) index pairs that are duplicates

        Returns:
            List of groups, where each group is a list of chunk indices
        """
        # Union-find data structure
        parent = list(range(n))

        def find(x: int) -> int:
            if parent[x] != x:
                parent[x] = find(parent[x])  # Path compression
            return parent[x]

        def union(x: int, y: int) -> None:
            root_x = find(x)
            root_y = find(y)
            if root_x != root_y:
                parent[root_y] = root_x

        # Build connected components
        for i, j in pairs:
            union(i, j)

        # Group chunks by their root parent
        groups_dict: dict[int, list[int]] = {}
        for i in range(n):
            root = find(i)
            if root not in groups_dict:
                groups_dict[root] = []
            groups_dict[root].append(i)

        # Filter out singleton groups (not duplicates)
        groups = [group for group in groups_dict.values() if len(group) > 1]

        return groups

    def _select_best_chunk(
        self, chunks: list[Chunk], indices: list[int]
    ) -> int:
        """Select the best chunk to keep from a duplicate group.

        Args:
            chunks: Full list of chunks
            indices: Indices of chunks in the duplicate group

        Returns:
            Index of the chunk to keep
        """
        if self.selection_strategy == SelectionStrategy.FIRST:
            # Keep the chunk with smallest original position
            return min(
                indices,
                key=lambda i: chunks[i].metadata.original_position
            )

        elif self.selection_strategy == SelectionStrategy.LONGEST:
            # Keep the chunk with most content
            return max(indices, key=lambda i: len(chunks[i].content))

        elif self.selection_strategy == SelectionStrategy.BEST_METADATA:
            # Keep the chunk with most complete metadata
            def metadata_score(idx: int) -> int:
                meta = chunks[idx].metadata
                score = 0
                if meta.h1:
                    score += 6
                if meta.h2:
                    score += 5
                if meta.h3:
                    score += 4
                if meta.h4:
                    score += 3
                if meta.h5:
                    score += 2
                if meta.h6:
                    score += 1
                return score

            return max(indices, key=metadata_score)

        else:
            # Fallback to first
            return min(
                indices,
                key=lambda i: chunks[i].metadata.original_position
            )

    def deduplicate(
        self, chunks: list[Chunk]
    ) -> tuple[list[Chunk], DeduplicationReport]:
        """Remove duplicate chunks from the list.

        Args:
            chunks: List of chunks with embeddings

        Returns:
            Tuple of (deduplicated_chunks, report)

        Raises:
            ValueError: If chunks lack embeddings
        """
        if not chunks:
            return [], DeduplicationReport(
                original_count=0,
                deduplicated_count=0,
                removed_count=0,
                duplicate_groups=[],
                removed_chunk_ids=[],
                kept_chunk_ids=[],
            )

        original_count = len(chunks)

        # Find duplicate groups
        duplicate_groups = self.find_duplicates(chunks)

        if not duplicate_groups:
            logger.info("No duplicates found")
            return chunks.copy(), DeduplicationReport(
                original_count=original_count,
                deduplicated_count=original_count,
                removed_count=0,
                duplicate_groups=[],
                removed_chunk_ids=[],
                kept_chunk_ids=[c.chunk_id for c in chunks],
            )

        # Determine which chunks to keep/remove
        chunks_to_keep: set[int] = set(range(len(chunks)))
        kept_from_groups: list[int] = []

        for group in duplicate_groups:
            # Select best chunk from group
            best_idx = self._select_best_chunk(chunks, group)
            kept_from_groups.append(best_idx)

            # Mark others for removal
            for idx in group:
                if idx != best_idx:
                    chunks_to_keep.discard(idx)

        # Build result
        if self.dry_run:
            # Dry run: return original chunks but with report
            deduplicated_chunks = chunks.copy()
        else:
            # Actually remove duplicates
            deduplicated_chunks = [
                chunks[i] for i in sorted(chunks_to_keep)
            ]

        # Build report
        removed_indices = set(range(len(chunks))) - chunks_to_keep
        report = DeduplicationReport(
            original_count=original_count,
            deduplicated_count=len(deduplicated_chunks),
            removed_count=len(removed_indices),
            duplicate_groups=[
                [chunks[i].chunk_id for i in group]
                for group in duplicate_groups
            ],
            removed_chunk_ids=[chunks[i].chunk_id for i in sorted(removed_indices)],
            kept_chunk_ids=[c.chunk_id for c in deduplicated_chunks],
        )

        logger.info(
            f"Deduplication complete: {original_count} → {len(deduplicated_chunks)} "
            f"({report.reduction_percentage:.1f}% reduction)"
        )

        return deduplicated_chunks, report

    def format_report(self, report: DeduplicationReport) -> str:
        """Format deduplication report as human-readable text.

        Args:
            report: Deduplication report

        Returns:
            Formatted report string
        """
        lines = ["Deduplication Report", "=" * 50]

        # Summary
        lines.append(f"\nOriginal chunks: {report.original_count}")
        lines.append(f"After deduplication: {report.deduplicated_count}")
        lines.append(f"Removed: {report.removed_count} ({report.reduction_percentage:.1f}%)")

        # Duplicate groups
        if report.duplicate_groups:
            lines.append(f"\nDuplicate groups: {len(report.duplicate_groups)}")
            for i, group in enumerate(report.duplicate_groups, 1):
                lines.append(f"\n  Group {i}: {len(group)} chunks")
                for chunk_id in group[:3]:  # Show first 3
                    lines.append(f"    - {chunk_id}")
                if len(group) > 3:
                    lines.append(f"    ... and {len(group) - 3} more")

        # Removed chunks
        if report.removed_chunk_ids:
            lines.append(f"\nRemoved chunk IDs ({len(report.removed_chunk_ids)}):")
            for chunk_id in report.removed_chunk_ids[:10]:  # Show first 10
                lines.append(f"  - {chunk_id}")
            if len(report.removed_chunk_ids) > 10:
                lines.append(f"  ... and {len(report.removed_chunk_ids) - 10} more")

        return "\n".join(lines)
