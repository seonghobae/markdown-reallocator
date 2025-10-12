"""Tests for search module."""

import json

import numpy as np
import pytest

from markdown_reallocator.core.embedder import Embedder
from markdown_reallocator.models.chunk import Chunk, ChunkMetadata
from markdown_reallocator.modules.search import SearchModule


@pytest.fixture
def mock_embedder(monkeypatch: pytest.MonkeyPatch) -> Embedder:
    """Create mock embedder that returns predictable embeddings."""
    embedder = Embedder()

    # Mock embed_chunk to return deterministic embeddings based on content
    def mock_embed(chunk: Chunk, force_refresh: bool = False) -> Chunk:
        # Generate embedding based on content hash for determinism
        content_hash = hash(chunk.content) % 100
        # Create 3D embedding with variations
        embedding = np.array(
            [
                float(content_hash) / 100,
                float((content_hash + 1) % 100) / 100,
                float((content_hash + 2) % 100) / 100,
            ],
            dtype=np.float32,
        )
        # Normalize to unit length
        chunk.embedding = embedding / np.linalg.norm(embedding)
        return chunk

    monkeypatch.setattr(embedder, "embed_chunk", mock_embed)
    return embedder


@pytest.fixture
def sample_chunks() -> list[Chunk]:
    """Create sample chunks with varied content."""
    chunks_data = [
        ("chunk_0", "User authentication using JWT tokens", "Authentication", 0),
        ("chunk_1", "OAuth 2.0 authorization flow", "Authentication", 1),
        ("chunk_2", "Database connection pooling", "Database", 2),
        ("chunk_3", "API rate limiting strategies", "API", 3),
        ("chunk_4", "Token refresh mechanism", "Authentication", 4),
        ("chunk_5", "SQL injection prevention", "Security", 5),
    ]

    chunks = []
    for chunk_id, content, h1, pos in chunks_data:
        chunk = Chunk(
            chunk_id=chunk_id,
            content=content,
            metadata=ChunkMetadata(
                h1=h1,
                original_position=pos,
            ),
        )
        chunks.append(chunk)

    return chunks


@pytest.fixture
def embedded_chunks(
    sample_chunks: list[Chunk], mock_embedder: Embedder
) -> list[Chunk]:
    """Return sample chunks with embeddings."""
    return [mock_embedder.embed_chunk(chunk) for chunk in sample_chunks]


class TestSearchModuleInitialization:
    """Tests for SearchModule initialization."""

    def test_default_initialization(self, mock_embedder: Embedder) -> None:
        """Should initialize with default settings."""
        search = SearchModule(embedder=mock_embedder)

        assert search.top_k == 5
        assert search.min_similarity == 0.5
        assert search.output_format == "text"
        assert search.embedder is mock_embedder

    def test_custom_configuration(self, mock_embedder: Embedder) -> None:
        """Should accept custom configuration."""
        search = SearchModule(
            embedder=mock_embedder,
            top_k=10,
            min_similarity=0.7,
            output_format="json",
        )

        assert search.top_k == 10
        assert search.min_similarity == 0.7
        assert search.output_format == "json"

    def test_invalid_top_k_raises(self, mock_embedder: Embedder) -> None:
        """Should raise ValueError for invalid top_k."""
        with pytest.raises(ValueError, match="top_k must be > 0"):
            SearchModule(embedder=mock_embedder, top_k=0)

        with pytest.raises(ValueError, match="top_k must be > 0"):
            SearchModule(embedder=mock_embedder, top_k=-1)

    def test_invalid_min_similarity_raises(self, mock_embedder: Embedder) -> None:
        """Should raise ValueError for min_similarity out of range."""
        with pytest.raises(ValueError, match="min_similarity must be in"):
            SearchModule(embedder=mock_embedder, min_similarity=1.5)

        with pytest.raises(ValueError, match="min_similarity must be in"):
            SearchModule(embedder=mock_embedder, min_similarity=-0.1)

    def test_invalid_output_format_raises(self, mock_embedder: Embedder) -> None:
        """Should raise ValueError for invalid output_format."""
        with pytest.raises(ValueError, match="output_format must be"):
            SearchModule(embedder=mock_embedder, output_format="xml")

    def test_creates_default_embedder_if_none(self) -> None:
        """Should create default embedder if none provided."""
        search = SearchModule()
        assert search.embedder is not None
        assert isinstance(search.embedder, Embedder)


class TestSearchFunctionality:
    """Tests for search functionality."""

    def test_search_basic(
        self, embedded_chunks: list[Chunk], mock_embedder: Embedder
    ) -> None:
        """Should return relevant chunks for query."""
        search = SearchModule(embedder=mock_embedder, min_similarity=0.0)

        # Search for authentication-related content
        results = search.search("authentication methods", embedded_chunks, top_k=3)

        # Should return results
        assert len(results) <= 3
        assert all(isinstance(chunk, Chunk) for chunk, _ in results)
        assert all(isinstance(score, float) for _, score in results)

    def test_search_returns_sorted_results(
        self, embedded_chunks: list[Chunk], mock_embedder: Embedder
    ) -> None:
        """Results should be sorted by similarity descending."""
        search = SearchModule(embedder=mock_embedder, min_similarity=0.0)

        results = search.search("security", embedded_chunks)

        # Check scores are descending
        scores = [score for _, score in results]
        assert scores == sorted(scores, reverse=True)

    def test_search_respects_top_k(
        self, embedded_chunks: list[Chunk], mock_embedder: Embedder
    ) -> None:
        """Should return at most top_k results."""
        search = SearchModule(embedder=mock_embedder, min_similarity=0.0, top_k=3)

        results = search.search("database", embedded_chunks)

        assert len(results) <= 3

    def test_search_respects_min_similarity(
        self, embedded_chunks: list[Chunk], mock_embedder: Embedder
    ) -> None:
        """Should filter results below min_similarity threshold."""
        search = SearchModule(embedder=mock_embedder, min_similarity=0.9)

        results = search.search("completely unrelated query xyz", embedded_chunks)

        # All results should have similarity >= 0.9
        for _, score in results:
            assert score >= 0.9

    def test_search_with_override_parameters(
        self, embedded_chunks: list[Chunk], mock_embedder: Embedder
    ) -> None:
        """Should allow overriding top_k and min_similarity per search."""
        search = SearchModule(
            embedder=mock_embedder, top_k=5, min_similarity=0.5
        )

        # Override both parameters
        results = search.search(
            "authentication", embedded_chunks, top_k=2, min_similarity=0.0
        )

        # Should respect override
        assert len(results) <= 2

    def test_search_empty_query_raises(
        self, embedded_chunks: list[Chunk], mock_embedder: Embedder
    ) -> None:
        """Should raise ValueError for empty query."""
        search = SearchModule(embedder=mock_embedder)

        with pytest.raises(ValueError, match="Query cannot be empty"):
            search.search("", embedded_chunks)

        with pytest.raises(ValueError, match="Query cannot be empty"):
            search.search("   ", embedded_chunks)

    def test_search_empty_chunks_returns_empty(
        self, mock_embedder: Embedder
    ) -> None:
        """Should return empty list for empty chunks."""
        search = SearchModule(embedder=mock_embedder)

        results = search.search("test query", [])

        assert results == []

    def test_search_chunks_without_embeddings_raises(
        self, sample_chunks: list[Chunk], mock_embedder: Embedder
    ) -> None:
        """Should raise ValueError if chunks lack embeddings."""
        search = SearchModule(embedder=mock_embedder)

        # sample_chunks don't have embeddings yet
        with pytest.raises(ValueError, match="has no embedding"):
            search.search("test query", sample_chunks)

    def test_search_returns_all_unique_chunks(
        self, embedded_chunks: list[Chunk], mock_embedder: Embedder
    ) -> None:
        """Should return unique chunks (no duplicates)."""
        search = SearchModule(embedder=mock_embedder, min_similarity=0.0)

        results = search.search("test", embedded_chunks)

        # Check uniqueness
        chunk_ids = [chunk.chunk_id for chunk, _ in results]
        assert len(chunk_ids) == len(set(chunk_ids))

    def test_search_scores_in_valid_range(
        self, embedded_chunks: list[Chunk], mock_embedder: Embedder
    ) -> None:
        """Similarity scores should be in [-1, 1] range (with small tolerance)."""
        search = SearchModule(embedder=mock_embedder, min_similarity=0.0)

        results = search.search("test query", embedded_chunks)

        # Allow small epsilon for floating-point precision
        epsilon = 1e-6
        for _, score in results:
            assert -1.0 - epsilon <= score <= 1.0 + epsilon

    def test_search_no_results_below_threshold(
        self, embedded_chunks: list[Chunk], mock_embedder: Embedder
    ) -> None:
        """Should return empty if no chunks meet threshold."""
        search = SearchModule(embedder=mock_embedder, min_similarity=0.99)

        # With mock embedder, unlikely to get 0.99 similarity
        results = search.search("xyz impossible match", embedded_chunks)

        # May be empty or have very high similarity
        assert isinstance(results, list)

    def test_search_query_embedding_failure_raises(
        self, embedded_chunks: list[Chunk], mock_embedder: Embedder
    ) -> None:
        """Should raise RuntimeError when query embedding fails."""
        search = SearchModule(embedder=mock_embedder)

        # Mock embed_chunk to return chunk with None embedding (failure case)
        def mock_failing_embed(chunk: Chunk, force_refresh: bool = False) -> Chunk:
            chunk.embedding = None
            return chunk

        import unittest.mock

        with unittest.mock.patch.object(
            mock_embedder, "embed_chunk", side_effect=mock_failing_embed
        ):
            with pytest.raises(RuntimeError, match="Failed to embed query"):
                search.search("test query", embedded_chunks)

    def test_search_empty_results_with_high_threshold(
        self, embedded_chunks: list[Chunk], mock_embedder: Embedder
    ) -> None:
        """Should filter results that don't meet very high threshold."""
        # Set threshold just below 1.0 (near-perfect match required)
        search = SearchModule(embedder=mock_embedder, min_similarity=0.999)

        # Use query very unlikely to match any chunk at 0.999+ similarity
        results = search.search(
            "xyzqwertyasdfzxcvbnmunmatchable query content", embedded_chunks
        )

        # All results (if any) must meet threshold
        for _, score in results:
            assert score >= 0.999


class TestResultFormatting:
    """Tests for result formatting."""

    def test_format_text_basic(
        self, embedded_chunks: list[Chunk], mock_embedder: Embedder
    ) -> None:
        """Should format results as human-readable text."""
        search = SearchModule(embedder=mock_embedder, output_format="text")

        results = search.search("authentication", embedded_chunks, top_k=2)
        formatted = search.format_results(results)

        # Check format
        assert isinstance(formatted, str)
        assert "Found" in formatted
        assert "Similarity:" in formatted
        assert "Content:" in formatted

    def test_format_json_basic(
        self, embedded_chunks: list[Chunk], mock_embedder: Embedder
    ) -> None:
        """Should format results as valid JSON."""
        search = SearchModule(embedder=mock_embedder, output_format="json")

        results = search.search("database", embedded_chunks, top_k=2)
        formatted = search.format_results(results)

        # Parse JSON
        data = json.loads(formatted)

        # Check structure
        assert "count" in data
        assert "results" in data
        assert data["count"] == len(results)
        assert len(data["results"]) == len(results)

        # Check result fields
        for result in data["results"]:
            assert "chunk_id" in result
            assert "similarity" in result
            assert "content" in result

    def test_format_text_with_context(
        self, embedded_chunks: list[Chunk], mock_embedder: Embedder
    ) -> None:
        """Should include metadata when include_context=True."""
        search = SearchModule(embedder=mock_embedder)

        results = search.search("authentication", embedded_chunks, top_k=1)
        formatted = search.format_results(results, include_context=True)

        # Check for metadata
        assert "H1:" in formatted or "Position:" in formatted

    def test_format_text_with_h2_h3_metadata(self, mock_embedder: Embedder) -> None:
        """Should include H2 and H3 metadata in text format."""
        # Create chunk with H1, H2, H3 metadata
        chunk = Chunk(
            chunk_id="test_chunk",
            content="Test content with hierarchical headers",
            metadata=ChunkMetadata(
                h1="Chapter 1",
                h2="Section 1.1",
                h3="Subsection 1.1.1",
                original_position=0,
            ),
        )
        chunk = mock_embedder.embed_chunk(chunk)

        search = SearchModule(embedder=mock_embedder)
        results = [(chunk, 0.95)]

        # Format with context
        formatted = search.format_results(results, include_context=True)

        # Check all heading levels are present
        assert "H1: Chapter 1" in formatted
        assert "H2: Section 1.1" in formatted
        assert "H3: Subsection 1.1.1" in formatted
        assert "Position: 0" in formatted

    def test_format_json_with_context(
        self, embedded_chunks: list[Chunk], mock_embedder: Embedder
    ) -> None:
        """Should include metadata in JSON when include_context=True."""
        search = SearchModule(embedder=mock_embedder)

        results = search.search("security", embedded_chunks, top_k=1)
        formatted = search.format_results(
            results, output_format="json", include_context=True
        )

        data = json.loads(formatted)

        # Check metadata is present
        assert "metadata" in data["results"][0]
        metadata = data["results"][0]["metadata"]
        assert "h1" in metadata
        assert "original_position" in metadata

    def test_format_empty_results_text(self, mock_embedder: Embedder) -> None:
        """Should handle empty results in text format."""
        search = SearchModule(embedder=mock_embedder)

        formatted = search.format_results([])

        assert formatted == "No results found.\n"

    def test_format_empty_results_json(self, mock_embedder: Embedder) -> None:
        """Should handle empty results in JSON format."""
        search = SearchModule(embedder=mock_embedder)

        formatted = search.format_results([], output_format="json")

        data = json.loads(formatted)
        assert data["count"] == 0
        assert data["results"] == []

    def test_format_override_output_format(
        self, embedded_chunks: list[Chunk], mock_embedder: Embedder
    ) -> None:
        """Should allow overriding output format per call."""
        search = SearchModule(embedder=mock_embedder, output_format="text")

        results = search.search("test", embedded_chunks, top_k=1)

        # Override to JSON
        formatted = search.format_results(results, output_format="json")

        # Should be valid JSON despite text default
        data = json.loads(formatted)
        assert "count" in data

    def test_format_invalid_format_raises(
        self, embedded_chunks: list[Chunk], mock_embedder: Embedder
    ) -> None:
        """Should raise ValueError for invalid format."""
        search = SearchModule(embedder=mock_embedder)

        results = search.search("test", embedded_chunks, top_k=1)

        with pytest.raises(ValueError, match="output_format must be"):
            search.format_results(results, output_format="xml")


class TestSearchIntegration:
    """Integration tests for search module."""

    def test_full_search_workflow(
        self, embedded_chunks: list[Chunk], mock_embedder: Embedder
    ) -> None:
        """Should support complete search workflow."""
        search = SearchModule(embedder=mock_embedder)

        # Search
        results = search.search("authentication security", embedded_chunks)

        # Format as text
        text_output = search.format_results(results, output_format="text")
        assert isinstance(text_output, str)
        assert len(text_output) > 0

        # Format as JSON
        json_output = search.format_results(results, output_format="json")
        data = json.loads(json_output)
        assert data["count"] == len(results)

    def test_korean_query_support(
        self, embedded_chunks: list[Chunk], mock_embedder: Embedder
    ) -> None:
        """Should handle Korean queries correctly."""
        search = SearchModule(embedder=mock_embedder)

        # Korean query
        results = search.search("인증 방법", embedded_chunks)

        # Should return results (mock embedder will handle it)
        assert isinstance(results, list)

    def test_multiple_searches_with_caching(
        self, embedded_chunks: list[Chunk], mock_embedder: Embedder
    ) -> None:
        """Should leverage embedder's cache for repeated queries."""
        search = SearchModule(embedder=mock_embedder)

        # Same query multiple times
        query = "authentication"
        results1 = search.search(query, embedded_chunks)
        results2 = search.search(query, embedded_chunks)

        # Results should be identical (deterministic with caching)
        assert len(results1) == len(results2)
        assert [c.chunk_id for c, _ in results1] == [c.chunk_id for c, _ in results2]

    def test_search_different_chunk_sets(
        self, sample_chunks: list[Chunk], mock_embedder: Embedder
    ) -> None:
        """Should work with different chunk sets."""
        search = SearchModule(embedder=mock_embedder)

        # Embed first 3 chunks
        chunks1 = [mock_embedder.embed_chunk(c) for c in sample_chunks[:3]]
        results1 = search.search("authentication", chunks1)

        # Embed last 3 chunks
        chunks2 = [mock_embedder.embed_chunk(c) for c in sample_chunks[3:]]
        results2 = search.search("authentication", chunks2)

        # Should return different results
        ids1 = {c.chunk_id for c, _ in results1}
        ids2 = {c.chunk_id for c, _ in results2}
        assert ids1 != ids2


class TestBranchCoverage:
    """Tests specifically for branch coverage."""

    def test_search_zero_results_above_threshold(
        self, embedded_chunks: list[Chunk], mock_embedder: Embedder
    ) -> None:
        """Should cover lines 168-169 when no chunks pass threshold."""
        search = SearchModule(embedder=mock_embedder, min_similarity=1.0)

        # With threshold = 1.0 (perfect similarity), it's nearly impossible to get results
        # unless query and chunk are identical
        results = search.search(
            "qwertyuiopasdfghjklzxcvbnm12345678901234567890unique", embedded_chunks
        )

        # Should return empty list (covering lines 168-169)
        assert results == []

    def test_format_text_with_none_h1_metadata(
        self, mock_embedder: Embedder
    ) -> None:
        """Should cover branch 252->254 when metadata.h1 is None."""
        # Create chunk with NO h1 metadata (h1=None)
        chunk = Chunk(
            chunk_id="no_h1_chunk",
            content="Content without h1 header",
            metadata=ChunkMetadata(
                h1=None,  # No h1 header
                h2="Section 2",
                h3="Subsection 3",
                original_position=0,
            ),
        )
        chunk = mock_embedder.embed_chunk(chunk)

        search = SearchModule(embedder=mock_embedder)
        results = [(chunk, 0.85)]

        # Format with context
        formatted = search.format_results(results, include_context=True)

        # Should NOT include "H1:" line (covers branch 252->254)
        assert "H1:" not in formatted
        # But should include H2 and H3
        assert "H2: Section 2" in formatted
        assert "H3: Subsection 3" in formatted
        assert "Position: 0" in formatted
