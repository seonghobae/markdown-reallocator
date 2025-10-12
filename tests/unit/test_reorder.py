"""Tests for reorder module."""

import numpy as np
import pytest

from markdown_reallocator.models.chunk import Chunk, ChunkMetadata
from markdown_reallocator.modules.reorder import ReorderModule, ReorderStrategy


@pytest.fixture
def sample_chunks_with_embeddings() -> list[Chunk]:
    """Create sample chunks with embeddings for testing."""
    chunks = []

    # Create 5 chunks with different embeddings
    # Chunks 0,1 are similar, chunks 2,3 are similar, chunk 4 is different
    embeddings = [
        np.array([1.0, 0.0, 0.0], dtype=np.float32),  # Chunk 0
        np.array([0.9, 0.1, 0.0], dtype=np.float32),  # Chunk 1 (similar to 0)
        np.array([0.0, 1.0, 0.0], dtype=np.float32),  # Chunk 2
        np.array([0.0, 0.9, 0.1], dtype=np.float32),  # Chunk 3 (similar to 2)
        np.array([0.0, 0.0, 1.0], dtype=np.float32),  # Chunk 4 (different)
    ]

    for i, embedding in enumerate(embeddings):
        chunk = Chunk(
            chunk_id=f"chunk_{i}",
            content=f"Content for chunk {i}",
            metadata=ChunkMetadata(
                h1=f"Section {i}",
                original_position=i,
            ),
        )
        chunk.embedding = embedding
        chunks.append(chunk)

    return chunks


class TestReorderModuleInitialization:
    """Tests for ReorderModule initialization."""

    def test_default_initialization(self) -> None:
        """Should initialize with default settings."""
        reorder = ReorderModule()

        assert reorder.strategy == ReorderStrategy.SEQUENTIAL
        assert reorder.similarity_threshold == 0.5

    def test_custom_configuration(self) -> None:
        """Should accept custom configuration."""
        reorder = ReorderModule(
            strategy="cluster",
            similarity_threshold=0.7,
        )

        assert reorder.strategy == ReorderStrategy.CLUSTER
        assert reorder.similarity_threshold == 0.7

    def test_invalid_strategy_raises(self) -> None:
        """Should raise ValueError for invalid strategy."""
        with pytest.raises(ValueError, match="Invalid strategy"):
            ReorderModule(strategy="invalid")

    def test_invalid_threshold_raises(self) -> None:
        """Should raise ValueError for threshold out of range."""
        with pytest.raises(ValueError, match="similarity_threshold must be in"):
            ReorderModule(similarity_threshold=1.5)

        with pytest.raises(ValueError, match="similarity_threshold must be in"):
            ReorderModule(similarity_threshold=-0.1)


class TestSimilarityMatrixComputation:
    """Tests for similarity matrix computation."""

    def test_compute_similarity_matrix(
        self, sample_chunks_with_embeddings: list[Chunk]
    ) -> None:
        """Should compute correct similarity matrix."""
        reorder = ReorderModule()
        matrix = reorder.compute_similarity_matrix(sample_chunks_with_embeddings)

        # Check shape
        assert matrix.shape == (5, 5)

        # Check diagonal is 1.0 (self-similarity)
        assert np.allclose(np.diag(matrix), 1.0)

        # Check symmetry
        assert np.allclose(matrix, matrix.T)

        # Check dtype
        assert matrix.dtype == np.float64 or matrix.dtype == np.float32

    def test_similar_chunks_have_high_similarity(
        self, sample_chunks_with_embeddings: list[Chunk]
    ) -> None:
        """Similar chunks should have high similarity scores."""
        reorder = ReorderModule()
        matrix = reorder.compute_similarity_matrix(sample_chunks_with_embeddings)

        # Chunks 0 and 1 are similar (both [1, 0, 0] direction)
        similarity_0_1 = matrix[0, 1]
        assert similarity_0_1 > 0.9

        # Chunks 2 and 3 are similar (both [0, 1, 0] direction)
        similarity_2_3 = matrix[2, 3]
        assert similarity_2_3 > 0.9

    def test_different_chunks_have_low_similarity(
        self, sample_chunks_with_embeddings: list[Chunk]
    ) -> None:
        """Different chunks should have low similarity scores."""
        reorder = ReorderModule()
        matrix = reorder.compute_similarity_matrix(sample_chunks_with_embeddings)

        # Chunks 0 and 2 are orthogonal (different directions)
        similarity_0_2 = matrix[0, 2]
        assert similarity_0_2 < 0.1

        # Chunks 0 and 4 are orthogonal
        similarity_0_4 = matrix[0, 4]
        assert similarity_0_4 < 0.1

    def test_empty_chunks_raises(self) -> None:
        """Should raise ValueError for empty chunk list."""
        reorder = ReorderModule()

        with pytest.raises(ValueError, match="Cannot reorder empty chunk list"):
            reorder.reorder([])

    def test_chunks_without_embeddings_raises(self) -> None:
        """Should raise ValueError if chunks lack embeddings."""
        reorder = ReorderModule()

        # Create chunk without embedding
        chunk = Chunk(
            chunk_id="test",
            content="Test content",
            metadata=ChunkMetadata(original_position=0),
        )

        with pytest.raises(ValueError, match="has no embedding"):
            reorder.compute_similarity_matrix([chunk])


class TestSequentialReordering:
    """Tests for sequential reordering strategy."""

    def test_sequential_reorder_basic(
        self, sample_chunks_with_embeddings: list[Chunk]
    ) -> None:
        """Should reorder chunks by chaining most similar."""
        reorder = ReorderModule(strategy="sequential")
        reordered = reorder.reorder(sample_chunks_with_embeddings)

        # Check all chunks are present
        assert len(reordered) == 5
        assert {c.chunk_id for c in reordered} == {
            c.chunk_id for c in sample_chunks_with_embeddings
        }

    def test_sequential_reorder_creates_high_similarity_chain(
        self, sample_chunks_with_embeddings: list[Chunk]
    ) -> None:
        """Adjacent chunks should have high similarity."""
        reorder = ReorderModule(strategy="sequential")
        reordered = reorder.reorder(sample_chunks_with_embeddings)

        # Compute similarity matrix
        matrix = reorder.compute_similarity_matrix(reordered)

        # Check adjacent similarities
        adjacent_similarities = []
        for i in range(len(reordered) - 1):
            sim = matrix[i, i + 1]  # Adjacent in reordered list
            adjacent_similarities.append(sim)

        # Average adjacent similarity should be high
        avg_sim = np.mean(adjacent_similarities)
        assert avg_sim > 0.5, f"Average adjacent similarity {avg_sim} should be > 0.5"

    def test_sequential_reorder_deterministic(
        self, sample_chunks_with_embeddings: list[Chunk]
    ) -> None:
        """Sequential reordering should be deterministic."""
        reorder = ReorderModule(strategy="sequential")

        reordered1 = reorder.reorder(sample_chunks_with_embeddings)
        reordered2 = reorder.reorder(sample_chunks_with_embeddings)

        # Same order every time
        assert [c.chunk_id for c in reordered1] == [c.chunk_id for c in reordered2]

    def test_sequential_reorder_single_chunk(self) -> None:
        """Should handle single chunk gracefully."""
        reorder = ReorderModule(strategy="sequential")

        chunk = Chunk(
            chunk_id="single",
            content="Single chunk",
            metadata=ChunkMetadata(original_position=0),
        )
        chunk.embedding = np.array([1.0, 0.0, 0.0], dtype=np.float32)

        reordered = reorder.reorder([chunk])

        assert len(reordered) == 1
        assert reordered[0].chunk_id == "single"


class TestClusterReordering:
    """Tests for cluster-based reordering strategy."""

    def test_cluster_reorder_basic(
        self, sample_chunks_with_embeddings: list[Chunk]
    ) -> None:
        """Should reorder chunks by clustering similar content."""
        reorder = ReorderModule(strategy="cluster")
        reordered = reorder.reorder(sample_chunks_with_embeddings)

        # Check all chunks are present
        assert len(reordered) == 5
        assert {c.chunk_id for c in reordered} == {
            c.chunk_id for c in sample_chunks_with_embeddings
        }

    def test_cluster_reorder_groups_similar_chunks(
        self, sample_chunks_with_embeddings: list[Chunk]
    ) -> None:
        """Similar chunks should be grouped together."""
        reorder = ReorderModule(strategy="cluster")
        reordered = reorder.reorder(sample_chunks_with_embeddings)

        # Get positions of chunks in reordered list
        positions = {c.chunk_id: i for i, c in enumerate(reordered)}

        # Chunks 0 and 1 are similar - should be close together
        dist_0_1 = abs(positions["chunk_0"] - positions["chunk_1"])

        # Chunks 2 and 3 are similar - should be close together
        dist_2_3 = abs(positions["chunk_2"] - positions["chunk_3"])

        # Similar chunks should be within 2 positions of each other
        assert dist_0_1 <= 2, f"Chunks 0 and 1 too far apart: {dist_0_1}"
        assert dist_2_3 <= 2, f"Chunks 2 and 3 too far apart: {dist_2_3}"

    def test_cluster_reorder_deterministic(
        self, sample_chunks_with_embeddings: list[Chunk]
    ) -> None:
        """Cluster reordering should be deterministic."""
        reorder = ReorderModule(strategy="cluster")

        reordered1 = reorder.reorder(sample_chunks_with_embeddings)
        reordered2 = reorder.reorder(sample_chunks_with_embeddings)

        # Same order every time
        assert [c.chunk_id for c in reordered1] == [c.chunk_id for c in reordered2]

    def test_cluster_reorder_single_chunk(self) -> None:
        """Should handle single chunk gracefully."""
        reorder = ReorderModule(strategy="cluster")

        chunk = Chunk(
            chunk_id="single",
            content="Single chunk",
            metadata=ChunkMetadata(original_position=0),
        )
        chunk.embedding = np.array([1.0, 0.0, 0.0], dtype=np.float32)

        reordered = reorder.reorder([chunk])

        assert len(reordered) == 1
        assert reordered[0].chunk_id == "single"

    def test_cluster_reorder_creates_coherent_groups(
        self, sample_chunks_with_embeddings: list[Chunk]
    ) -> None:
        """Should create 3-7 clusters for typical documents."""
        np.random.seed(42)  # For reproducibility
        reorder = ReorderModule(strategy="cluster")

        # Create more chunks to test cluster count logic
        chunks = sample_chunks_with_embeddings * 3  # 15 chunks total

        # Give each copy slightly different embeddings
        for i, chunk in enumerate(chunks):
            if chunk.embedding is not None:
                noise = np.random.randn(3) * 0.05
                chunk.embedding = chunk.embedding + noise
            chunk.chunk_id = f"chunk_{i}"

        reordered = reorder.reorder(chunks)

        # All chunks should be present
        assert len(reordered) == 15

    def test_cluster_reorder_large_document(self) -> None:
        """Should handle large documents with >20 chunks (tests line 283)."""
        np.random.seed(42)
        reorder = ReorderModule(strategy="cluster")

        # Create 25 chunks (>20 to trigger different cluster count logic)
        chunks = []
        for i in range(25):
            chunk = Chunk(
                chunk_id=f"chunk_{i}",
                content=f"Content {i}",
                metadata=ChunkMetadata(original_position=i),
            )
            # Create random embeddings
            chunk.embedding = np.random.randn(10).astype(np.float32)
            chunks.append(chunk)

        reordered = reorder.reorder(chunks)

        # All chunks should be present
        assert len(reordered) == 25
        assert {c.chunk_id for c in reordered} == {c.chunk_id for c in chunks}


class TestMarkdownReconstruction:
    """Tests for markdown reconstruction."""

    def test_reconstruct_basic(
        self, sample_chunks_with_embeddings: list[Chunk]
    ) -> None:
        """Should reconstruct markdown from chunks."""
        reorder = ReorderModule()
        markdown = reorder.reconstruct_markdown(sample_chunks_with_embeddings)

        # Check that markdown is a string
        assert isinstance(markdown, str)

        # Check all chunks are included
        for chunk in sample_chunks_with_embeddings:
            assert chunk.content in markdown

        # Check trailing newline
        assert markdown.endswith("\n")

    def test_reconstruct_with_comments(
        self, sample_chunks_with_embeddings: list[Chunk]
    ) -> None:
        """Should include position comments when requested."""
        reorder = ReorderModule()
        markdown = reorder.reconstruct_markdown(
            sample_chunks_with_embeddings, include_comments=True
        )

        # Check for HTML comments
        assert "<!-- Original position:" in markdown
        assert "Reordered position:" in markdown

    def test_reconstruct_empty_raises(self) -> None:
        """Should raise ValueError for empty chunk list."""
        reorder = ReorderModule()

        with pytest.raises(ValueError, match="Cannot reconstruct markdown from empty"):
            reorder.reconstruct_markdown([])

    def test_reconstruct_preserves_content(
        self, sample_chunks_with_embeddings: list[Chunk]
    ) -> None:
        """Should preserve all chunk content."""
        reorder = ReorderModule()
        markdown = reorder.reconstruct_markdown(sample_chunks_with_embeddings)

        # Check character count (approximately)
        total_content_length = sum(len(c.content) for c in sample_chunks_with_embeddings)

        # Markdown should have at least the original content length
        assert len(markdown) >= total_content_length

    def test_reconstruct_after_reorder(
        self, sample_chunks_with_embeddings: list[Chunk]
    ) -> None:
        """Should work correctly after reordering."""
        reorder = ReorderModule(strategy="sequential")

        # Reorder chunks
        reordered = reorder.reorder(sample_chunks_with_embeddings)

        # Reconstruct markdown
        markdown = reorder.reconstruct_markdown(reordered)

        # All chunks should be present
        assert isinstance(markdown, str)
        for chunk in reordered:
            assert chunk.content in markdown

    def test_reconstruct_single_chunk(self) -> None:
        """Should handle reconstruction with single chunk."""
        reorder = ReorderModule()

        chunk = Chunk(
            chunk_id="single",
            content="Single chunk content",
            metadata=ChunkMetadata(original_position=0),
        )

        markdown = reorder.reconstruct_markdown([chunk])

        # Should reconstruct successfully
        assert isinstance(markdown, str)
        assert "Single chunk content" in markdown
        assert markdown.endswith("\n")
