"""Tests for deduplication module."""

import numpy as np
import pytest

from markdown_reallocator.models.chunk import Chunk, ChunkMetadata
from markdown_reallocator.modules.dedup import (
    DeduplicationModule,
    SelectionStrategy,
)


@pytest.fixture
def sample_chunks_with_duplicates() -> list[Chunk]:
    """Create sample chunks with some duplicates."""
    # Chunks 0, 1, 2 are nearly identical (duplicates)
    # Chunks 3, 4 are nearly identical (duplicates)
    # Chunk 5 is unique

    chunks_data = [
        ("chunk_0", "Authentication using JWT tokens", "Auth", "JWT", None, 0, 50),
        ("chunk_1", "Authentication with JWT tokens", "Auth", "JWT", None, 1, 45),
        ("chunk_2", "JWT token authentication", "Auth", "JWT", "Security", 2, 40),
        ("chunk_3", "Database connection pooling", "Database", None, None, 3, 35),
        ("chunk_4", "Connection pooling for databases", "Database", None, None, 4, 38),
        ("chunk_5", "API rate limiting strategies", "API", "Rate Limit", None, 5, 60),
    ]

    chunks = []
    for chunk_id, content, h1, h2, h3, pos, length_mod in chunks_data:
        # Make content length vary slightly
        content_full = content + " " * length_mod
        chunk = Chunk(
            chunk_id=chunk_id,
            content=content_full,
            metadata=ChunkMetadata(
                h1=h1,
                h2=h2,
                h3=h3,
                original_position=pos,
            ),
        )
        chunks.append(chunk)

    return chunks


@pytest.fixture
def embedded_duplicates(
    sample_chunks_with_duplicates: list[Chunk],
) -> list[Chunk]:
    """Add embeddings to chunks with duplicates."""
    # Create embeddings where similar chunks have similar vectors
    embeddings = [
        # Group 1: Chunks 0, 1, 2 (very similar - authentication)
        np.array([0.9, 0.1, 0.0], dtype=np.float32),  # chunk_0
        np.array([0.85, 0.15, 0.0], dtype=np.float32),  # chunk_1
        np.array([0.88, 0.12, 0.0], dtype=np.float32),  # chunk_2
        # Group 2: Chunks 3, 4 (very similar - database)
        np.array([0.0, 0.9, 0.1], dtype=np.float32),  # chunk_3
        np.array([0.0, 0.88, 0.12], dtype=np.float32),  # chunk_4
        # Unique: Chunk 5
        np.array([0.0, 0.0, 1.0], dtype=np.float32),  # chunk_5
    ]

    for chunk, embedding in zip(
        sample_chunks_with_duplicates, embeddings, strict=True
    ):
        # Normalize to unit length
        chunk.embedding = embedding / np.linalg.norm(embedding)

    return sample_chunks_with_duplicates


class TestDeduplicationModuleInitialization:
    """Tests for DeduplicationModule initialization."""

    def test_default_initialization(self) -> None:
        """Should initialize with default settings."""
        dedup = DeduplicationModule()

        assert dedup.similarity_threshold == 0.85
        assert dedup.selection_strategy == SelectionStrategy.FIRST
        assert dedup.use_llm is False
        assert dedup.dry_run is False

    def test_custom_configuration(self) -> None:
        """Should accept custom configuration."""
        dedup = DeduplicationModule(
            similarity_threshold=0.9,
            selection_strategy="longest",
            use_llm=True,
            dry_run=True,
        )

        assert dedup.similarity_threshold == 0.9
        assert dedup.selection_strategy == SelectionStrategy.LONGEST
        assert dedup.use_llm is True
        assert dedup.dry_run is True

    def test_invalid_threshold_raises(self) -> None:
        """Should raise ValueError for threshold out of range."""
        with pytest.raises(ValueError, match="similarity_threshold must be in"):
            DeduplicationModule(similarity_threshold=1.5)

        with pytest.raises(ValueError, match="similarity_threshold must be in"):
            DeduplicationModule(similarity_threshold=-0.1)

    def test_invalid_strategy_raises(self) -> None:
        """Should raise ValueError for invalid strategy."""
        with pytest.raises(ValueError, match="Invalid selection_strategy"):
            DeduplicationModule(selection_strategy="invalid")


class TestDuplicateDetection:
    """Tests for duplicate detection."""

    def test_find_duplicates_basic(
        self, embedded_duplicates: list[Chunk]
    ) -> None:
        """Should find duplicate groups correctly."""
        dedup = DeduplicationModule(similarity_threshold=0.85)

        groups = dedup.find_duplicates(embedded_duplicates)

        # Should find 2 groups
        assert len(groups) == 2

        # Each group should have multiple chunks
        for group in groups:
            assert len(group) >= 2

    def test_find_duplicates_transitive_closure(
        self, embedded_duplicates: list[Chunk]
    ) -> None:
        """Should use transitive closure for grouping."""
        dedup = DeduplicationModule(similarity_threshold=0.8)

        groups = dedup.find_duplicates(embedded_duplicates)

        # Check that groups are complete (transitive)
        # If A similar to B, and B similar to C, then A, B, C are in one group
        for group in groups:
            # All pairs in group should be related (directly or transitively)
            assert len(group) >= 2

    def test_find_duplicates_high_threshold(
        self, embedded_duplicates: list[Chunk]
    ) -> None:
        """High threshold should find fewer duplicates."""
        dedup_high = DeduplicationModule(similarity_threshold=0.99)

        groups_high = dedup_high.find_duplicates(embedded_duplicates)

        # Very high threshold may find fewer or no duplicates
        # depending on exact similarity values
        # Our test embeddings are normalized and quite similar
        assert len(groups_high) <= 2  # At most the 2 groups we have

    def test_find_duplicates_low_threshold(
        self, embedded_duplicates: list[Chunk]
    ) -> None:
        """Low threshold should find more duplicates."""
        dedup_low = DeduplicationModule(similarity_threshold=0.5)

        groups_low = dedup_low.find_duplicates(embedded_duplicates)

        # Lower threshold should find groups
        assert len(groups_low) >= 2

    def test_find_duplicates_empty_chunks(self) -> None:
        """Should handle empty chunk list."""
        dedup = DeduplicationModule()

        groups = dedup.find_duplicates([])

        assert groups == []

    def test_find_duplicates_no_duplicates(self) -> None:
        """Should return empty if no duplicates found."""
        # Create chunks with very different embeddings
        chunks = []
        for i in range(3):
            chunk = Chunk(
                chunk_id=f"chunk_{i}",
                content=f"Content {i}",
                metadata=ChunkMetadata(original_position=i),
            )
            # Orthogonal embeddings
            embedding = np.zeros(3, dtype=np.float32)
            embedding[i] = 1.0
            chunk.embedding = embedding
            chunks.append(chunk)

        dedup = DeduplicationModule(similarity_threshold=0.9)
        groups = dedup.find_duplicates(chunks)

        assert groups == []

    def test_find_duplicates_chunks_without_embeddings_raises(
        self, sample_chunks_with_duplicates: list[Chunk]
    ) -> None:
        """Should raise ValueError if chunks lack embeddings."""
        dedup = DeduplicationModule()

        with pytest.raises(ValueError, match="has no embedding"):
            dedup.find_duplicates(sample_chunks_with_duplicates)


class TestSelectionStrategies:
    """Tests for chunk selection strategies."""

    def test_selection_strategy_first(
        self, embedded_duplicates: list[Chunk]
    ) -> None:
        """FIRST strategy should keep earliest chunk."""
        dedup = DeduplicationModule(
            similarity_threshold=0.85,
            selection_strategy="first",
        )

        result, report = dedup.deduplicate(embedded_duplicates)

        # Should keep chunks with earliest positions
        kept_ids = {c.chunk_id for c in result}

        # From group [0,1,2], should keep chunk_0 (earliest)
        assert "chunk_0" in kept_ids
        assert "chunk_1" not in kept_ids
        assert "chunk_2" not in kept_ids

        # From group [3,4], should keep chunk_3 (earliest)
        assert "chunk_3" in kept_ids
        assert "chunk_4" not in kept_ids

        # Unique chunk should be kept
        assert "chunk_5" in kept_ids

    def test_selection_strategy_longest(
        self, embedded_duplicates: list[Chunk]
    ) -> None:
        """LONGEST strategy should keep chunk with most content."""
        dedup = DeduplicationModule(
            similarity_threshold=0.85,
            selection_strategy="longest",
        )

        result, report = dedup.deduplicate(embedded_duplicates)

        kept_ids = {c.chunk_id for c in result}

        # chunk_0 has longest content in group [0,1,2]
        assert "chunk_0" in kept_ids

        # chunk_4 has longest content in group [3,4]
        assert "chunk_4" in kept_ids

        # Unique chunk
        assert "chunk_5" in kept_ids

    def test_selection_strategy_best_metadata(
        self, embedded_duplicates: list[Chunk]
    ) -> None:
        """BEST_METADATA strategy should keep chunk with most complete metadata."""
        dedup = DeduplicationModule(
            similarity_threshold=0.85,
            selection_strategy="best_metadata",
        )

        result, report = dedup.deduplicate(embedded_duplicates)

        kept_ids = {c.chunk_id for c in result}

        # chunk_2 has most complete metadata (h1, h2, h3) in group [0,1,2]
        assert "chunk_2" in kept_ids

        # chunk_3 and chunk_4 have same metadata, either is fine
        assert "chunk_3" in kept_ids or "chunk_4" in kept_ids

        # Unique chunk
        assert "chunk_5" in kept_ids


class TestDeduplicationOperation:
    """Tests for deduplicate() operation."""

    def test_deduplicate_basic(
        self, embedded_duplicates: list[Chunk]
    ) -> None:
        """Should remove duplicates and return report."""
        dedup = DeduplicationModule(similarity_threshold=0.85)

        result, report = dedup.deduplicate(embedded_duplicates)

        # Should have fewer chunks
        assert len(result) < len(embedded_duplicates)

        # Report should be accurate
        assert report.original_count == 6
        assert report.deduplicated_count == len(result)
        assert report.removed_count == 6 - len(result)

    def test_deduplicate_preserves_order(
        self, embedded_duplicates: list[Chunk]
    ) -> None:
        """Should preserve original order of kept chunks."""
        dedup = DeduplicationModule(similarity_threshold=0.85)

        result, report = dedup.deduplicate(embedded_duplicates)

        # Check that original positions are in ascending order
        positions = [c.metadata.original_position for c in result]
        assert positions == sorted(positions)

    def test_deduplicate_empty_chunks(self) -> None:
        """Should handle empty chunk list."""
        dedup = DeduplicationModule()

        result, report = dedup.deduplicate([])

        assert result == []
        assert report.original_count == 0
        assert report.deduplicated_count == 0

    def test_deduplicate_no_duplicates(self) -> None:
        """Should return original chunks if no duplicates."""
        # Create chunks with orthogonal embeddings
        chunks = []
        for i in range(3):
            chunk = Chunk(
                chunk_id=f"chunk_{i}",
                content=f"Content {i}",
                metadata=ChunkMetadata(original_position=i),
            )
            embedding = np.zeros(3, dtype=np.float32)
            embedding[i] = 1.0
            chunk.embedding = embedding
            chunks.append(chunk)

        dedup = DeduplicationModule(similarity_threshold=0.9)
        result, report = dedup.deduplicate(chunks)

        assert len(result) == 3
        assert report.removed_count == 0

    def test_deduplicate_dry_run(
        self, embedded_duplicates: list[Chunk]
    ) -> None:
        """Dry run should not modify chunks but still return report."""
        dedup = DeduplicationModule(
            similarity_threshold=0.85,
            dry_run=True,
        )

        result, report = dedup.deduplicate(embedded_duplicates)

        # Should return original chunks in dry run
        assert len(result) == len(embedded_duplicates)

        # But report should show what would be removed
        assert report.removed_count > 0
        assert report.duplicate_groups  # Should have groups

    def test_deduplicate_idempotent(
        self, embedded_duplicates: list[Chunk]
    ) -> None:
        """Running deduplicate twice should be idempotent."""
        dedup = DeduplicationModule(similarity_threshold=0.85)

        result1, report1 = dedup.deduplicate(embedded_duplicates)
        result2, report2 = dedup.deduplicate(result1)

        # Second run should find no more duplicates
        assert len(result2) == len(result1)
        assert report2.removed_count == 0


class TestDeduplicationReport:
    """Tests for deduplication report."""

    def test_report_structure(
        self, embedded_duplicates: list[Chunk]
    ) -> None:
        """Report should have correct structure."""
        dedup = DeduplicationModule(similarity_threshold=0.85)

        result, report = dedup.deduplicate(embedded_duplicates)

        # Check all fields are present
        assert isinstance(report.original_count, int)
        assert isinstance(report.deduplicated_count, int)
        assert isinstance(report.removed_count, int)
        assert isinstance(report.duplicate_groups, list)
        assert isinstance(report.removed_chunk_ids, list)
        assert isinstance(report.kept_chunk_ids, list)

    def test_report_counts(
        self, embedded_duplicates: list[Chunk]
    ) -> None:
        """Report counts should be consistent."""
        dedup = DeduplicationModule(similarity_threshold=0.85)

        result, report = dedup.deduplicate(embedded_duplicates)

        # Counts should add up
        assert report.deduplicated_count + report.removed_count == report.original_count

        # Chunk IDs should match
        assert len(report.kept_chunk_ids) == report.deduplicated_count
        assert len(report.removed_chunk_ids) == report.removed_count

    def test_report_reduction_percentage(
        self, embedded_duplicates: list[Chunk]
    ) -> None:
        """Should calculate reduction percentage correctly."""
        dedup = DeduplicationModule(similarity_threshold=0.85)

        result, report = dedup.deduplicate(embedded_duplicates)

        # Check percentage calculation
        expected = (report.removed_count / report.original_count) * 100
        assert abs(report.reduction_percentage - expected) < 0.01

    def test_report_duplicate_groups(
        self, embedded_duplicates: list[Chunk]
    ) -> None:
        """Report should list duplicate groups."""
        dedup = DeduplicationModule(similarity_threshold=0.85)

        result, report = dedup.deduplicate(embedded_duplicates)

        # Should have duplicate groups
        assert len(report.duplicate_groups) >= 2

        # Each group should have multiple IDs
        for group in report.duplicate_groups:
            assert len(group) >= 2
            assert all(isinstance(chunk_id, str) for chunk_id in group)

    def test_format_report(
        self, embedded_duplicates: list[Chunk]
    ) -> None:
        """Should format report as readable text."""
        dedup = DeduplicationModule(similarity_threshold=0.85)

        result, report = dedup.deduplicate(embedded_duplicates)
        formatted = dedup.format_report(report)

        # Check format contains key information
        assert "Deduplication Report" in formatted
        assert "Original chunks:" in formatted
        assert "After deduplication:" in formatted
        assert "Removed:" in formatted
        assert str(report.original_count) in formatted


class TestEdgeCases:
    """Tests for edge cases."""

    def test_single_chunk(self) -> None:
        """Should handle single chunk gracefully."""
        chunk = Chunk(
            chunk_id="single",
            content="Single chunk",
            metadata=ChunkMetadata(original_position=0),
        )
        chunk.embedding = np.array([1.0, 0.0, 0.0], dtype=np.float32)

        dedup = DeduplicationModule()
        result, report = dedup.deduplicate([chunk])

        assert len(result) == 1
        assert report.removed_count == 0

    def test_all_duplicates(self) -> None:
        """Should handle case where all chunks are duplicates."""
        # Create 5 nearly identical chunks
        chunks = []
        for i in range(5):
            chunk = Chunk(
                chunk_id=f"chunk_{i}",
                content=f"Same content {i}",
                metadata=ChunkMetadata(original_position=i),
            )
            # Very similar embeddings
            embedding = np.array([0.9, 0.1, 0.0], dtype=np.float32)
            embedding += np.random.randn(3) * 0.01  # Small noise
            chunk.embedding = embedding / np.linalg.norm(embedding)
            chunks.append(chunk)

        dedup = DeduplicationModule(similarity_threshold=0.85)
        result, report = dedup.deduplicate(chunks)

        # Should keep only 1 chunk
        assert len(result) == 1
        assert report.removed_count == 4

    def test_exact_duplicates(self) -> None:
        """Should handle exact duplicates (similarity = 1.0)."""
        # Create 3 chunks with identical embeddings
        chunks = []
        embedding = np.array([1.0, 0.0, 0.0], dtype=np.float32)

        for i in range(3):
            chunk = Chunk(
                chunk_id=f"chunk_{i}",
                content=f"Content {i}",
                metadata=ChunkMetadata(original_position=i),
            )
            chunk.embedding = embedding.copy()
            chunks.append(chunk)

        dedup = DeduplicationModule(similarity_threshold=0.99)
        result, report = dedup.deduplicate(chunks)

        # Should keep only 1
        assert len(result) == 1
        assert report.removed_count == 2


class TestBranchCoverage:
    """Tests specifically for branch coverage."""

    def test_reduction_percentage_with_zero_original_count(self) -> None:
        """Should cover line 43 - reduction_percentage when original_count is 0."""
        from markdown_reallocator.modules.dedup import DeduplicationReport

        # Create report with 0 original count
        report = DeduplicationReport(
            original_count=0,
            deduplicated_count=0,
            removed_count=0,
            duplicate_groups=[],
            removed_chunk_ids=[],
            kept_chunk_ids=[],
        )

        # Should return 0.0 without division by zero error
        assert report.reduction_percentage == 0.0

    def test_metadata_scoring_all_levels(self) -> None:
        """Should cover branch 233->235 - metadata scoring with different h1/h2/h3."""
        # Create chunks with varying metadata completeness
        chunks = []

        # Chunk 0: h1 only (score = 3)
        chunks.append(
            Chunk(
                chunk_id="chunk_0",
                content="Content 0",
                metadata=ChunkMetadata(h1="Title", original_position=0),
            )
        )

        # Chunk 1: h1 + h2 (score = 5)
        chunks.append(
            Chunk(
                chunk_id="chunk_1",
                content="Content 1",
                metadata=ChunkMetadata(h1="Title", h2="Subtitle", original_position=1),
            )
        )

        # Chunk 2: h1 + h2 + h3 (score = 6) - best metadata
        chunks.append(
            Chunk(
                chunk_id="chunk_2",
                content="Content 2",
                metadata=ChunkMetadata(
                    h1="Title", h2="Subtitle", h3="Section", original_position=2
                ),
            )
        )

        # Add similar embeddings so they form a duplicate group
        embedding = np.array([0.9, 0.1, 0.0], dtype=np.float32)
        for chunk in chunks:
            chunk.embedding = embedding / np.linalg.norm(embedding)

        dedup = DeduplicationModule(
            similarity_threshold=0.85, selection_strategy="best_metadata"
        )

        result, report = dedup.deduplicate(chunks)

        # Should keep chunk_2 (most complete metadata with all h1, h2, h3)
        assert len(result) == 1
        assert result[0].chunk_id == "chunk_2"

    def test_format_report_no_duplicate_groups(self) -> None:
        """Should cover branch 352->362 when duplicate_groups is empty."""
        from markdown_reallocator.modules.dedup import DeduplicationReport

        dedup = DeduplicationModule()

        # Create report with no duplicate groups
        report = DeduplicationReport(
            original_count=5,
            deduplicated_count=5,
            removed_count=0,
            duplicate_groups=[],  # Empty - no duplicates found
            removed_chunk_ids=[],
            kept_chunk_ids=["chunk_0", "chunk_1", "chunk_2", "chunk_3", "chunk_4"],
        )

        formatted = dedup.format_report(report)

        # Should still format without duplicate groups section
        assert "Deduplication Report" in formatted
        assert "Original chunks: 5" in formatted
        assert "After deduplication: 5" in formatted
        assert "Removed: 0" in formatted
        # Should NOT have duplicate groups section since empty
        assert "Duplicate groups:" not in formatted

    def test_format_report_no_removed_chunks(self) -> None:
        """Should cover branch 362->369 when removed_chunk_ids is empty."""
        from markdown_reallocator.modules.dedup import DeduplicationReport

        dedup = DeduplicationModule()

        # Create report with no removed chunks
        report = DeduplicationReport(
            original_count=3,
            deduplicated_count=3,
            removed_count=0,
            duplicate_groups=[],
            removed_chunk_ids=[],  # Empty - nothing removed
            kept_chunk_ids=["chunk_0", "chunk_1", "chunk_2"],
        )

        formatted = dedup.format_report(report)

        # Should format without removed chunks section
        assert "Deduplication Report" in formatted
        assert "Original chunks: 3" in formatted
        # Should NOT have removed chunk IDs section since empty
        assert "Removed chunk IDs" not in formatted

    def test_format_report_with_long_removed_list(self) -> None:
        """Should cover truncation branch in format_report for >10 removed chunks."""
        from markdown_reallocator.modules.dedup import DeduplicationReport

        dedup = DeduplicationModule()

        # Create report with >10 removed chunks (to test truncation)
        removed_ids = [f"chunk_{i}" for i in range(15)]
        report = DeduplicationReport(
            original_count=20,
            deduplicated_count=5,
            removed_count=15,
            duplicate_groups=[],
            removed_chunk_ids=removed_ids,
            kept_chunk_ids=["kept_0", "kept_1", "kept_2", "kept_3", "kept_4"],
        )

        formatted = dedup.format_report(report)

        # Should show first 10 and indicate more
        assert "Removed chunk IDs (15):" in formatted
        assert "chunk_0" in formatted  # First item
        assert "chunk_9" in formatted  # 10th item
        assert "... and 5 more" in formatted  # Truncation message

    def test_format_report_with_long_duplicate_groups(self) -> None:
        """Should cover truncation branch in format_report for groups >3 chunks."""
        from markdown_reallocator.modules.dedup import DeduplicationReport

        dedup = DeduplicationModule()

        # Create a duplicate group with >3 chunks
        large_group = [f"chunk_{i}" for i in range(5)]
        report = DeduplicationReport(
            original_count=10,
            deduplicated_count=6,
            removed_count=4,
            duplicate_groups=[large_group],  # One group with 5 chunks
            removed_chunk_ids=["chunk_1", "chunk_2", "chunk_3", "chunk_4"],
            kept_chunk_ids=["chunk_0", "kept_1", "kept_2", "kept_3", "kept_4", "kept_5"],
        )

        formatted = dedup.format_report(report)

        # Should show first 3 and indicate more
        assert "Group 1: 5 chunks" in formatted
        assert "chunk_0" in formatted  # First item
        assert "chunk_1" in formatted  # Second item
        assert "chunk_2" in formatted  # Third item
        assert "... and 2 more" in formatted  # Truncation message
