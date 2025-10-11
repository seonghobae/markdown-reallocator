"""Smoke tests using real complex documents.

Tests the complete workflow with actual complex markdown files
like CLAUDE.md to ensure the system handles real-world documents.
"""

from pathlib import Path

import pytest

from markdown_reallocator.core import Embedder, MarkdownPreprocessor, MarkdownSplitter
from markdown_reallocator.modules import SearchModule


@pytest.fixture
def claude_md_path() -> Path:
    """Get path to CLAUDE.md if it exists."""
    candidate_paths = [
        Path.home() / ".claude" / "CLAUDE.md",
        Path(__file__).parent.parent.parent / "CLAUDE.md",
    ]
    for path in candidate_paths:
        if path.exists():
            return path
    pytest.skip("CLAUDE.md not found in expected locations")


@pytest.mark.smoke
class TestRealDocumentProcessing:
    """Test processing of real complex markdown documents."""

    def test_process_claude_md(self, claude_md_path: Path) -> None:
        """Should successfully process CLAUDE.md through full pipeline.

        This test verifies:
        1. Preprocessing handles complex markdown with various formatting
        2. Splitting produces reasonable chunks
        3. Search functionality works on real content
        """
        # Read the document
        content = claude_md_path.read_text(encoding="utf-8")
        assert len(content) > 0, "CLAUDE.md should not be empty"

        # Preprocess
        preprocessor = MarkdownPreprocessor()
        clean_content = preprocessor.preprocess(content)
        assert len(clean_content) > 0, "Preprocessing should produce output"

        # Split into chunks
        splitter = MarkdownSplitter(max_tokens_per_chunk=500)
        chunks = splitter.split(clean_content)
        assert len(chunks) > 0, "Should produce at least one chunk"
        assert len(chunks) > 3, "Complex document should produce multiple chunks"

        # Verify chunk properties
        for chunk in chunks:
            assert chunk.content, "Each chunk should have content"
            assert chunk.chunk_id, "Each chunk should have an ID"

    def test_search_claude_md_without_embedding(self, claude_md_path: Path) -> None:
        """Should handle search workflow structure without actual embedding.

        Tests the workflow structure without requiring Ollama.
        """
        # Read and preprocess
        content = claude_md_path.read_text(encoding="utf-8")
        preprocessor = MarkdownPreprocessor()
        clean_content = preprocessor.preprocess(content)

        # Split
        splitter = MarkdownSplitter(max_tokens_per_chunk=500)
        chunks = splitter.split(clean_content)

        # Verify we can initialize search module (structure test)
        search = SearchModule()
        assert search is not None
        assert search.top_k == 5  # Default value
        assert search.min_similarity == 0.5  # Default value

        # Verify chunks are properly structured for search
        for chunk in chunks[:3]:  # Check first 3 chunks
            assert hasattr(chunk, "content")
            assert hasattr(chunk, "chunk_id")
            assert hasattr(chunk, "metadata")
            assert hasattr(chunk, "embedding")  # Attribute exists (None is ok)

    @pytest.mark.requires_ollama
    def test_full_workflow_with_claude_md(self, claude_md_path: Path) -> None:
        """Complete workflow test with actual embedding and search.

        Requires Ollama server running with embeddinggemma model.
        """
        # Read and preprocess
        content = claude_md_path.read_text(encoding="utf-8")
        preprocessor = MarkdownPreprocessor()
        clean_content = preprocessor.preprocess(content)

        # Split
        splitter = MarkdownSplitter(max_tokens_per_chunk=500)
        chunks = splitter.split(clean_content)

        # Embed chunks
        embedder = Embedder(model_name="embeddinggemma")
        embedded_chunks = [embedder.embed_chunk(chunk) for chunk in chunks]

        # Verify embeddings
        for chunk in embedded_chunks:
            assert chunk.embedding is not None
            assert len(chunk.embedding) > 0

        # Search
        search = SearchModule(embedder=embedder)
        results = search.search("Git commit workflow", embedded_chunks, top_k=3)

        # Verify results
        assert len(results) > 0, "Should find relevant results"
        assert len(results) <= 3, "Should respect top_k limit"

        # Check result structure
        for chunk, score in results:
            assert chunk.content, "Result should have content"
            assert 0.0 <= score <= 1.0, "Score should be in valid range"

        # Format results
        text_output = search.format_results(results, output_format="text")
        assert "Found" in text_output
        assert "Similarity:" in text_output

        json_output = search.format_results(results, output_format="json")
        assert "count" in json_output
        assert "results" in json_output


@pytest.mark.smoke
class TestDocumentComplexity:
    """Test handling of document complexity."""

    def test_claude_md_structure_extraction(self, claude_md_path: Path) -> None:
        """Should extract meaningful structure from CLAUDE.md."""
        content = claude_md_path.read_text(encoding="utf-8")
        preprocessor = MarkdownPreprocessor()
        clean_content = preprocessor.preprocess(content)

        # Check that complex structures are preserved
        assert "# " in clean_content, "Should preserve headings"
        assert len(clean_content.split("\n")) > 10, "Should have multiple lines"

        # Split and check metadata extraction
        splitter = MarkdownSplitter(max_tokens_per_chunk=500)
        chunks = splitter.split(clean_content)

        # At least some chunks should have H1 metadata
        h1_chunks = [c for c in chunks if c.metadata and c.metadata.h1]
        assert len(h1_chunks) > 0, "Should extract H1 headers as metadata"

    def test_document_size_handling(self, claude_md_path: Path) -> None:
        """Should handle large document size appropriately."""
        content = claude_md_path.read_text(encoding="utf-8")

        # Document should be substantial
        assert len(content) > 1000, "CLAUDE.md should be a substantial document"
        assert content.count("\n") > 50, "Should have many lines"

        # Preprocessing should not drastically reduce size
        preprocessor = MarkdownPreprocessor()
        clean_content = preprocessor.preprocess(content)
        size_ratio = len(clean_content) / len(content)
        assert size_ratio > 0.5, "Preprocessing should not remove more than 50% of content"

        # Splitting should create reasonable number of chunks
        splitter = MarkdownSplitter(max_tokens_per_chunk=500)
        chunks = splitter.split(clean_content)
        assert 5 < len(chunks) < 200, "Should create reasonable number of chunks"
