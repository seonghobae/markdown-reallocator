"""Integration tests for end-to-end workflows.

These tests verify that modules work together correctly.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from markdown_reallocator.core.embedder import Embedder
from markdown_reallocator.core.preprocessor import MarkdownPreprocessor
from markdown_reallocator.core.splitter import MarkdownSplitter
from markdown_reallocator.models.chunk import Chunk, ChunkMetadata
from markdown_reallocator.modules.dedup import DeduplicationModule
from markdown_reallocator.modules.reorder import ReorderModule
from markdown_reallocator.modules.search import SearchModule


@pytest.fixture
def sample_markdown():
    """Create a realistic markdown document."""
    return """# Introduction

This is a test document for integration testing.

**Key Concepts**

Understanding the basic concepts is important.

## Section 1: Getting Started

This section covers the basics.

**Installation Steps**

Follow these steps to install.

## Section 2: Advanced Topics

This section covers advanced topics.

### Subsection 2.1

Details about subsection 2.1.

## Section 3: Conclusion

Final thoughts and summary.
"""


@pytest.fixture
def chunks_with_embeddings():
    """Create sample chunks with mock embeddings."""
    chunks = [
        Chunk(
            chunk_id="chunk001",
            content="# Introduction\n\nThis is about introduction.",
            metadata=ChunkMetadata(h1="Introduction", original_position=0),
        ),
        Chunk(
            chunk_id="chunk002",
            content="## Getting Started\n\nBasics here.",
            metadata=ChunkMetadata(
                h1="Introduction", h2="Getting Started", original_position=1
            ),
        ),
        Chunk(
            chunk_id="chunk003",
            content="## Advanced Topics\n\nAdvanced content.",
            metadata=ChunkMetadata(
                h1="Introduction", h2="Advanced Topics", original_position=2
            ),
        ),
        Chunk(
            chunk_id="chunk004",
            content="# Conclusion\n\nFinal thoughts.",
            metadata=ChunkMetadata(h1="Conclusion", original_position=3),
        ),
    ]

    # Add mock embeddings
    # Similar chunks have similar embeddings
    chunks[0].embedding = np.array([1.0, 0.0, 0.0, 0.0])  # Introduction
    chunks[1].embedding = np.array([0.8, 0.2, 0.0, 0.0])  # Similar to intro
    chunks[2].embedding = np.array([0.0, 0.0, 1.0, 0.0])  # Advanced (different)
    chunks[3].embedding = np.array([0.0, 0.0, 0.0, 1.0])  # Conclusion (different)

    return chunks


class TestPreprocessSplitWorkflow:
    """Test preprocessing and splitting workflow."""

    def test_preprocess_then_split(self, sample_markdown):
        """Test full preprocess→split workflow."""
        # Step 1: Preprocess
        preprocessor = MarkdownPreprocessor()
        processed = preprocessor.preprocess(sample_markdown)

        # Verify preprocessing worked
        assert "## Key Concepts" in processed
        assert "## Installation Steps" in processed

        # Step 2: Split
        splitter = MarkdownSplitter(max_tokens_per_chunk=100)
        chunks = splitter.split(processed)

        # Verify splitting worked
        assert len(chunks) > 0
        assert all(isinstance(c, Chunk) for c in chunks)
        assert all(c.chunk_id for c in chunks)
        assert all(c.metadata.original_position >= 0 for c in chunks)

        # Verify hierarchy is preserved
        h1_titles = {c.metadata.h1 for c in chunks if c.metadata.h1}
        assert len(h1_titles) > 0


class TestSearchWorkflow:
    """Test search workflow."""

    @patch.object(Embedder, "embed_chunk")
    def test_search_workflow(self, mock_embed, chunks_with_embeddings):
        """Test full search workflow."""
        # Mock embedder to return a query embedding
        def mock_embed_side_effect(chunk):
            # Query embedding similar to introduction
            chunk.embedding = np.array([0.9, 0.1, 0.0, 0.0])
            return chunk

        mock_embed.side_effect = mock_embed_side_effect

        # Create embedder
        embedder = Embedder()

        # Create search module
        search = SearchModule(embedder=embedder, top_k=2, min_similarity=0.5)

        # Perform search
        results = search.search("introduction topics", chunks_with_embeddings)

        # Verify results
        assert len(results) > 0
        assert len(results) <= 2  # top_k=2

        # Results should be sorted by similarity
        if len(results) > 1:
            assert results[0][1] >= results[1][1]

        # Format results
        formatted = search.format_results(results, include_context=True)
        assert "Found" in formatted
        assert "result" in formatted.lower()


class TestReorderWorkflow:
    """Test reorder workflow."""

    def test_sequential_reorder_workflow(self, chunks_with_embeddings):
        """Test sequential reordering workflow."""
        # Create reorder module
        reorder = ReorderModule(strategy="sequential")

        # Reorder chunks
        reordered = reorder.reorder(chunks_with_embeddings)

        # Verify reordering
        assert len(reordered) == len(chunks_with_embeddings)
        assert all(isinstance(c, Chunk) for c in reordered)

        # Reconstruct markdown
        markdown = reorder.reconstruct_markdown(reordered)
        assert isinstance(markdown, str)
        assert len(markdown) > 0

    def test_cluster_reorder_workflow(self, chunks_with_embeddings):
        """Test cluster reordering workflow."""
        # Create reorder module
        reorder = ReorderModule(strategy="cluster")

        # Reorder chunks
        reordered = reorder.reorder(chunks_with_embeddings)

        # Verify reordering
        assert len(reordered) == len(chunks_with_embeddings)
        assert all(isinstance(c, Chunk) for c in reordered)

        # Reconstruct markdown
        markdown = reorder.reconstruct_markdown(reordered, include_comments=True)
        assert "Original position:" in markdown


class TestDeduplicationWorkflow:
    """Test deduplication workflow."""

    def test_dedup_workflow(self):
        """Test deduplication workflow."""
        # Create chunks with duplicates
        chunks = [
            Chunk(
                chunk_id="chunk001",
                content="# Introduction\n\nSame content.",
                metadata=ChunkMetadata(original_position=0),
            ),
            Chunk(
                chunk_id="chunk002",
                content="# Introduction\n\nSame content.",
                metadata=ChunkMetadata(original_position=1),
            ),
            Chunk(
                chunk_id="chunk003",
                content="# Different\n\nDifferent content.",
                metadata=ChunkMetadata(original_position=2),
            ),
        ]

        # Add embeddings (first two are identical)
        chunks[0].embedding = np.array([1.0, 0.0, 0.0])
        chunks[1].embedding = np.array([1.0, 0.0, 0.0])  # Duplicate
        chunks[2].embedding = np.array([0.0, 1.0, 0.0])  # Different

        # Deduplicate
        dedup = DeduplicationModule(similarity_threshold=0.95, selection_strategy="first")
        deduplicated, report = dedup.deduplicate(chunks)

        # Verify deduplication
        assert report.original_count == 3
        assert report.deduplicated_count == 2
        assert report.removed_count == 1

        # Format report
        formatted = dedup.format_report(report)
        assert "Deduplication Report" in formatted
        assert "Removed: 1" in formatted


class TestEndToEndWorkflow:
    """Test complete end-to-end workflows."""

    @patch.object(Embedder, "_ensure_model_loaded")
    @patch.object(Embedder, "embed_chunk")
    def test_full_pipeline(
        self, mock_embed_chunk, mock_ensure_loaded, sample_markdown, tmp_path
    ):
        """Test complete pipeline: preprocess → split → embed → search."""
        # Mock embedding
        def embed_side_effect(chunk):
            # Generate deterministic embedding from chunk content
            content_hash = hash(chunk.content) % 100
            chunk.embedding = np.random.RandomState(content_hash).rand(4).astype(
                np.float32
            )
            return chunk

        mock_embed_chunk.side_effect = embed_side_effect
        mock_ensure_loaded.return_value = None

        # Step 1: Preprocess
        preprocessor = MarkdownPreprocessor()
        processed = preprocessor.preprocess(sample_markdown)
        assert len(processed) > 0

        # Step 2: Split
        splitter = MarkdownSplitter(max_tokens_per_chunk=200)
        chunks = splitter.split(processed)
        assert len(chunks) > 0

        # Step 3: Embed
        embedder = Embedder()
        embedded_chunks = embedder.embed_batch(chunks)
        assert all(c.embedding is not None for c in embedded_chunks)

        # Step 4: Search
        search = SearchModule(embedder=embedder, top_k=3)
        results = search.search("getting started", embedded_chunks)
        assert len(results) <= 3

        # Verify pipeline integrity
        assert all(isinstance(r[0], Chunk) for r in results)
        assert all(isinstance(r[1], float) for r in results)

    @patch.object(Embedder, "_ensure_model_loaded")
    @patch.object(Embedder, "embed_chunk")
    def test_process_and_reorder(
        self, mock_embed_chunk, mock_ensure_loaded, sample_markdown
    ):
        """Test pipeline: preprocess → split → embed → reorder."""
        # Mock embedding
        def embed_side_effect(chunk):
            content_hash = hash(chunk.content) % 100
            chunk.embedding = np.random.RandomState(content_hash).rand(4).astype(
                np.float32
            )
            return chunk

        mock_embed_chunk.side_effect = embed_side_effect
        mock_ensure_loaded.return_value = None

        # Preprocess and split
        preprocessor = MarkdownPreprocessor()
        processed = preprocessor.preprocess(sample_markdown)

        splitter = MarkdownSplitter()
        chunks = splitter.split(processed)

        # Embed
        embedder = Embedder()
        embedded_chunks = embedder.embed_batch(chunks)

        # Reorder
        reorder = ReorderModule(strategy="sequential")
        reordered = reorder.reorder(embedded_chunks)

        # Reconstruct
        markdown = reorder.reconstruct_markdown(reordered)

        # Verify output
        assert isinstance(markdown, str)
        assert len(markdown) > 0
        assert len(reordered) == len(chunks)


class TestFileIOWorkflow:
    """Test workflows with file I/O."""

    def test_save_and_load_chunks(self, chunks_with_embeddings, tmp_path):
        """Test saving and loading chunks with embeddings."""
        # Save chunks to JSON
        chunks_file = tmp_path / "chunks.json"
        chunks_data = [
            {
                "chunk_id": c.chunk_id,
                "content": c.content,
                "metadata": {
                    "h1": c.metadata.h1,
                    "h2": c.metadata.h2,
                    "h3": c.metadata.h3,
                    "original_position": c.metadata.original_position,
                },
            }
            for c in chunks_with_embeddings
        ]
        chunks_file.write_text(json.dumps(chunks_data, indent=2))

        # Save embeddings to NPZ
        embeddings_file = tmp_path / "embeddings.npz"
        embeddings_dict = {c.chunk_id: c.embedding for c in chunks_with_embeddings}
        np.savez(str(embeddings_file), **embeddings_dict)

        # Load chunks back
        loaded_chunks_data = json.loads(chunks_file.read_text())
        loaded_chunks = [
            Chunk(
                chunk_id=data["chunk_id"],
                content=data["content"],
                metadata=ChunkMetadata(
                    h1=data["metadata"].get("h1"),
                    h2=data["metadata"].get("h2"),
                    h3=data["metadata"].get("h3"),
                    original_position=data["metadata"]["original_position"],
                ),
            )
            for data in loaded_chunks_data
        ]

        # Load embeddings back
        loaded_embeddings = np.load(str(embeddings_file))
        for chunk in loaded_chunks:
            if chunk.chunk_id in loaded_embeddings:
                chunk.embedding = loaded_embeddings[chunk.chunk_id]

        # Verify roundtrip
        assert len(loaded_chunks) == len(chunks_with_embeddings)
        assert all(c.embedding is not None for c in loaded_chunks)
