"""Tests for markdown splitter."""

import pytest

from markdown_reallocator.core.splitter import MarkdownSplitter


class TestMarkdownSplitter:
    """Tests for MarkdownSplitter initialization."""

    def test_default_initialization(self) -> None:
        """Should initialize with default settings."""
        splitter = MarkdownSplitter()

        assert splitter.headers_to_split_on == [
            ("#", "h1"),
            ("##", "h2"),
            ("###", "h3"),
        ]
        assert splitter.max_tokens_per_chunk == 1000

    def test_custom_headers(self) -> None:
        """Should accept custom header configuration."""
        headers = [("#", "h1"), ("##", "h2")]
        splitter = MarkdownSplitter(headers_to_split_on=headers)

        assert splitter.headers_to_split_on == headers

    def test_custom_max_tokens(self) -> None:
        """Should accept custom max tokens."""
        splitter = MarkdownSplitter(max_tokens_per_chunk=500)

        assert splitter.max_tokens_per_chunk == 500


class TestEstimateTokens:
    """Tests for token estimation."""

    def test_empty_string(self) -> None:
        """Should return 0 for empty string."""
        splitter = MarkdownSplitter()

        assert splitter.estimate_tokens("") == 0
        assert splitter.estimate_tokens("   ") == 0

    def test_simple_text(self) -> None:
        """Should estimate tokens for simple text."""
        splitter = MarkdownSplitter()

        # "Hello world" = 2 words * 1.3 = 2.6 → 2
        tokens = splitter.estimate_tokens("Hello world")
        assert tokens == 2

    def test_longer_text(self) -> None:
        """Should estimate tokens for longer text."""
        splitter = MarkdownSplitter()

        text = "This is a longer piece of text with multiple words"
        # 10 words * 1.3 = 13
        tokens = splitter.estimate_tokens(text)
        assert tokens == 13

    def test_markdown_with_formatting(self) -> None:
        """Should handle markdown formatting."""
        splitter = MarkdownSplitter()

        text = "**Bold** and *italic* and `code`"
        # 5 words * 1.3 = 6.5 → 6
        tokens = splitter.estimate_tokens(text)
        assert tokens == 6


class TestSplitBasic:
    """Tests for basic splitting functionality."""

    def test_split_empty_raises(self) -> None:
        """Should raise ValueError for empty markdown."""
        splitter = MarkdownSplitter()

        with pytest.raises(ValueError, match="Cannot split empty markdown"):
            splitter.split("")

        with pytest.raises(ValueError, match="Cannot split empty markdown"):
            splitter.split("   ")

    def test_split_single_section(self) -> None:
        """Should split markdown with single section."""
        splitter = MarkdownSplitter()
        markdown = "# Title\n\nSome content here."

        chunks = splitter.split(markdown)

        assert len(chunks) == 1
        assert chunks[0].metadata.h1 == "Title"
        assert "content" in chunks[0].content

    def test_split_multiple_h1_sections(self) -> None:
        """Should split markdown with multiple H1 sections."""
        splitter = MarkdownSplitter()
        markdown = """# First Section

Content for first section.

# Second Section

Content for second section."""

        chunks = splitter.split(markdown)

        assert len(chunks) == 2
        assert chunks[0].metadata.h1 == "First Section"
        assert chunks[1].metadata.h1 == "Second Section"

    def test_split_h1_with_h2(self) -> None:
        """Should split markdown with H1 and H2 headers."""
        splitter = MarkdownSplitter()
        markdown = """# Main Title

## Subsection One

Content for subsection one.

## Subsection Two

Content for subsection two."""

        chunks = splitter.split(markdown)

        assert len(chunks) == 2
        assert chunks[0].metadata.h1 == "Main Title"
        assert chunks[0].metadata.h2 == "Subsection One"
        assert chunks[1].metadata.h1 == "Main Title"
        assert chunks[1].metadata.h2 == "Subsection Two"

    def test_split_full_hierarchy(self) -> None:
        """Should split markdown with H1, H2, and H3."""
        splitter = MarkdownSplitter()
        markdown = """# Title

## Section

### Subsection

Content here."""

        chunks = splitter.split(markdown)

        assert len(chunks) == 1
        assert chunks[0].metadata.h1 == "Title"
        assert chunks[0].metadata.h2 == "Section"
        assert chunks[0].metadata.h3 == "Subsection"

    def test_chunk_ids_are_unique(self) -> None:
        """Chunk IDs should be unique."""
        splitter = MarkdownSplitter()
        markdown = """# Section 1

Content 1

# Section 2

Content 2"""

        chunks = splitter.split(markdown)

        chunk_ids = [c.chunk_id for c in chunks]
        assert len(chunk_ids) == len(set(chunk_ids))

    def test_chunk_ids_deterministic(self) -> None:
        """Chunk IDs should be deterministic."""
        splitter = MarkdownSplitter()
        markdown = "# Title\n\nContent"

        chunks1 = splitter.split(markdown)
        chunks2 = splitter.split(markdown)

        assert chunks1[0].chunk_id == chunks2[0].chunk_id


class TestMetadataExtraction:
    """Tests for metadata extraction."""

    def test_position_tracking(self) -> None:
        """Should track original position."""
        splitter = MarkdownSplitter()
        markdown = """# First

Content 1

# Second

Content 2

# Third

Content 3"""

        chunks = splitter.split(markdown)

        assert chunks[0].metadata.original_position == 0
        assert chunks[1].metadata.original_position == 1
        assert chunks[2].metadata.original_position == 2

    def test_token_counting(self) -> None:
        """Should count tokens for each chunk."""
        splitter = MarkdownSplitter()
        markdown = """# Title

This is a short piece of content.

# Another Title

This is a much longer piece of content with many more words to increase the token count."""

        chunks = splitter.split(markdown)

        # Second chunk should have more tokens
        assert chunks[1].metadata.token_count > chunks[0].metadata.token_count

    def test_header_path(self) -> None:
        """Should construct correct header path."""
        splitter = MarkdownSplitter()
        markdown = """# Main

## Sub

### Detail

Content"""

        chunks = splitter.split(markdown)

        assert chunks[0].metadata.header_path() == "Main > Sub > Detail"


class TestEdgeCases:
    """Tests for edge cases and malformed markdown."""

    def test_no_headers(self) -> None:
        """Should handle markdown without headers."""
        splitter = MarkdownSplitter()
        markdown = "Just some plain text without any headers."

        chunks = splitter.split(markdown)

        assert len(chunks) == 1
        assert chunks[0].metadata.h1 is None
        assert chunks[0].content == markdown

    def test_empty_sections(self) -> None:
        """Should handle sections with no content."""
        splitter = MarkdownSplitter()
        markdown = """# Title One

# Title Two

Actual content here."""

        chunks = splitter.split(markdown)

        # Empty sections should be skipped
        assert all(chunk.content.strip() for chunk in chunks)

    def test_code_blocks_preserved(self) -> None:
        """Should preserve code blocks correctly."""
        splitter = MarkdownSplitter()
        markdown = """# Code Example

```python
def hello():
    print("Hello")
```

End of section."""

        chunks = splitter.split(markdown)

        assert "```python" in chunks[0].content
        assert "def hello():" in chunks[0].content

    def test_nested_lists(self) -> None:
        """Should handle nested lists."""
        splitter = MarkdownSplitter()
        markdown = """# List Section

- Item 1
  - Nested 1
  - Nested 2
- Item 2"""

        chunks = splitter.split(markdown)

        assert "- Item 1" in chunks[0].content
        assert "- Nested 1" in chunks[0].content

    def test_tables(self) -> None:
        """Should handle markdown tables."""
        splitter = MarkdownSplitter()
        markdown = """# Table Section

| Header 1 | Header 2 |
|----------|----------|
| Cell 1   | Cell 2   |"""

        chunks = splitter.split(markdown)

        assert "| Header 1 |" in chunks[0].content

    def test_mixed_header_levels(self) -> None:
        """Should handle mixed header levels correctly."""
        splitter = MarkdownSplitter()
        markdown = """# H1

Content under H1

### H3 without H2

Content under H3"""

        chunks = splitter.split(markdown)

        # Should still split correctly despite missing H2
        assert len(chunks) >= 1

    def test_unicode_content(self) -> None:
        """Should handle Unicode content."""
        splitter = MarkdownSplitter()
        markdown = """# 한글 제목

한글 내용입니다.

# Emoji 😀

Content with emoji."""

        chunks = splitter.split(markdown)

        assert chunks[0].metadata.h1 == "한글 제목"
        assert "한글" in chunks[0].content
        assert "Emoji 😀" in chunks[1].metadata.h1 or "Emoji" in chunks[1].metadata.h1

    def test_special_characters(self) -> None:
        """Should handle special characters in headers."""
        splitter = MarkdownSplitter()
        markdown = """# Title with *italic* and **bold**

Content here."""

        chunks = splitter.split(markdown)

        # Header should preserve formatting
        assert len(chunks) == 1


class TestTokenLimits:
    """Tests for token limit enforcement."""

    def test_warns_on_exceeding_limit(self, caplog: pytest.LogCaptureFixture) -> None:
        """Should log warning when chunk exceeds token limit."""
        splitter = MarkdownSplitter(max_tokens_per_chunk=10)

        # Create markdown with long content
        long_content = " ".join(["word"] * 50)
        markdown = f"# Title\n\n{long_content}"

        splitter.split(markdown)

        # Should have logged a warning
        assert any("exceeds max tokens" in record.message for record in caplog.records)

    def test_small_limit_still_creates_chunks(self) -> None:
        """Should create chunks even with very small limit."""
        splitter = MarkdownSplitter(max_tokens_per_chunk=5)
        markdown = "# Title\n\nSome content that exceeds the limit."

        chunks = splitter.split(markdown)

        # Should still create the chunk despite exceeding limit
        assert len(chunks) >= 1


class TestSplitWithMetadata:
    """Tests for split_with_metadata method."""

    def test_returns_chunks_and_metadata(self) -> None:
        """Should return both chunks and metadata."""
        splitter = MarkdownSplitter()
        markdown = """# First

Content

# Second

More content"""

        chunks, metadata = splitter.split_with_metadata(markdown)

        assert isinstance(chunks, list)
        assert isinstance(metadata, dict)
        assert len(chunks) == 2

    def test_metadata_has_required_keys(self) -> None:
        """Metadata should have all required keys."""
        splitter = MarkdownSplitter()
        markdown = "# Title\n\nContent"

        chunks, metadata = splitter.split_with_metadata(markdown)

        assert "total_chunks" in metadata
        assert "total_tokens" in metadata
        assert "max_chunk_tokens" in metadata
        assert "headers_used" in metadata

    def test_metadata_chunk_count(self) -> None:
        """Should count chunks correctly."""
        splitter = MarkdownSplitter()
        markdown = """# One

# Two

# Three"""

        chunks, metadata = splitter.split_with_metadata(markdown)

        assert metadata["total_chunks"] == len(chunks)

    def test_metadata_token_count(self) -> None:
        """Should sum tokens correctly."""
        splitter = MarkdownSplitter()
        markdown = """# Title

Content here."""

        chunks, metadata = splitter.split_with_metadata(markdown)

        expected_tokens = sum(c.metadata.token_count for c in chunks)
        assert metadata["total_tokens"] == expected_tokens

    def test_metadata_headers_used(self) -> None:
        """Should track which header levels were used."""
        splitter = MarkdownSplitter()
        markdown = """# H1 Title

## H2 Subtitle

Content"""

        chunks, metadata = splitter.split_with_metadata(markdown)

        assert "h1" in metadata["headers_used"]
        assert "h2" in metadata["headers_used"]
        assert "h3" not in metadata["headers_used"]


class TestIntegration:
    """Integration tests with real-world scenarios."""

    def test_typical_blog_post(self) -> None:
        """Should handle typical blog post structure."""
        splitter = MarkdownSplitter()
        markdown = """# My Blog Post

Introduction paragraph.

## Background

Some background information.

## Implementation

Details about implementation.

### Code Example

```python
def example():
    return "Hello"
```

### Performance

Performance metrics.

## Conclusion

Final thoughts."""

        chunks = splitter.split(markdown)

        # Should create multiple chunks
        assert len(chunks) >= 3

        # Check some metadata
        assert any(c.metadata.h2 == "Background" for c in chunks)
        assert any(c.metadata.h3 == "Code Example" for c in chunks)

    def test_documentation_structure(self) -> None:
        """Should handle documentation structure."""
        splitter = MarkdownSplitter()
        markdown = """# API Documentation

## Authentication

Use API keys for authentication.

## Endpoints

### GET /users

Retrieve all users.

### POST /users

Create a new user.

## Error Codes

List of error codes."""

        chunks = splitter.split(markdown)

        assert len(chunks) >= 4

        # Should have proper hierarchy
        api_chunks = [c for c in chunks if c.metadata.h1 == "API Documentation"]
        assert len(api_chunks) >= 1

    def test_korean_documentation(self) -> None:
        """Should handle Korean documentation."""
        splitter = MarkdownSplitter()
        markdown = """# 시작하기

이 문서는 시작 가이드입니다.

## 설치

설치 방법을 설명합니다.

## 사용법

사용 방법입니다."""

        chunks = splitter.split(markdown)

        assert len(chunks) >= 2
        assert any("시작하기" in (c.metadata.h1 or "") for c in chunks)
        assert any("설치" in (c.metadata.h2 or "") for c in chunks)

    def test_roundtrip_content_preservation(self) -> None:
        """Content should be preserved in roundtrip."""
        splitter = MarkdownSplitter()
        markdown = """# Title

Content paragraph 1.

Content paragraph 2.

## Subtitle

More content."""

        chunks = splitter.split(markdown)

        # Reconstruct by joining chunks
        reconstructed = "\n\n".join(c.content for c in chunks)

        # Key content should be preserved
        assert "Content paragraph 1" in reconstructed
        assert "Content paragraph 2" in reconstructed
        assert "More content" in reconstructed


class TestPerformance:
    """Performance tests."""

    def test_split_large_document(self) -> None:
        """Should handle large documents efficiently."""
        splitter = MarkdownSplitter()

        # Create document with 50 sections
        sections = []
        for i in range(50):
            sections.append(f"# Section {i}")
            sections.append("")
            sections.append(f"Content for section {i} with multiple words to increase size.")
            sections.append("")

        markdown = "\n".join(sections)

        import time
        start = time.time()
        chunks = splitter.split(markdown)
        duration = time.time() - start

        # Should complete quickly
        assert duration < 1.0
        assert len(chunks) == 50


class TestErrorHandling:
    """Tests for error handling and edge cases."""

    def test_langchain_returns_empty_list(self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
        """Should handle case where LangChain returns no chunks."""
        from unittest.mock import Mock

        splitter = MarkdownSplitter()
        markdown = "# Title\n\nContent"

        # Mock LangChain splitter to return empty list
        mock_splitter = Mock()
        mock_splitter.split_text.return_value = []
        monkeypatch.setattr(splitter, "_splitter", mock_splitter)

        # Should fallback to single chunk
        chunks = splitter.split(markdown)

        assert len(chunks) == 1
        assert chunks[0].content == markdown
        assert "LangChain splitter returned no chunks" in caplog.text

    def test_skip_empty_chunks(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should skip chunks with only whitespace."""
        from unittest.mock import Mock
        from langchain_core.documents import Document

        splitter = MarkdownSplitter()
        markdown = "# Title\n\nContent"

        # Mock LangChain to return chunks with whitespace
        mock_splitter = Mock()
        mock_splitter.split_text.return_value = [
            Document(page_content="# Title\n\nContent", metadata={"h1": "Title"}),
            Document(page_content="   \n\n   ", metadata={}),  # Empty chunk
            Document(page_content="More content", metadata={}),
        ]
        monkeypatch.setattr(splitter, "_splitter", mock_splitter)

        chunks = splitter.split(markdown)

        # Should skip the whitespace-only chunk
        assert len(chunks) == 2
        assert all(c.content.strip() for c in chunks)

    def test_no_valid_chunks_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should raise ValueError if all chunks are invalid."""
        from unittest.mock import Mock
        from langchain_core.documents import Document

        splitter = MarkdownSplitter()
        markdown = "# Title"

        # Mock LangChain to return only whitespace chunks
        mock_splitter = Mock()
        mock_splitter.split_text.return_value = [
            Document(page_content="   ", metadata={}),
            Document(page_content="\n\n", metadata={}),
        ]
        monkeypatch.setattr(splitter, "_splitter", mock_splitter)

        with pytest.raises(ValueError, match="No valid chunks created"):
            splitter.split(markdown)

    def test_split_exception_logged(self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
        """Should log error and re-raise on exception."""
        from unittest.mock import Mock

        splitter = MarkdownSplitter()
        markdown = "# Title\n\nContent"

        # Mock LangChain to raise exception
        mock_splitter = Mock()
        mock_splitter.split_text.side_effect = RuntimeError("Mock error")
        monkeypatch.setattr(splitter, "_splitter", mock_splitter)

        with pytest.raises(RuntimeError, match="Mock error"):
            splitter.split(markdown)

        # Should have logged the error
        assert "Failed to split markdown" in caplog.text
        assert "Mock error" in caplog.text


class TestBranchCoverage:
    """Tests specifically for branch coverage."""

    def test_split_with_metadata_h2_detection(self) -> None:
        """Should cover branch 245->247 for h2 header detection."""
        splitter = MarkdownSplitter()
        markdown = """# Main Title

## Section One

Content for section one.

## Section Two

Content for section two."""

        chunks, metadata = splitter.split_with_metadata(markdown)

        # Should detect h2 headers
        assert "h2" in metadata["headers_used"]
        assert "h1" in metadata["headers_used"]

        # Verify chunks have h2 metadata
        assert any(c.metadata.h2 == "Section One" for c in chunks)
        assert any(c.metadata.h2 == "Section Two" for c in chunks)

    def test_split_with_metadata_h3_detection(self) -> None:
        """Should cover line 250 for h3 header detection."""
        splitter = MarkdownSplitter()
        markdown = """# Main Title

## Section

### Subsection One

Content for subsection one.

### Subsection Two

Content for subsection two."""

        chunks, metadata = splitter.split_with_metadata(markdown)

        # Should detect h3 headers
        assert "h3" in metadata["headers_used"]
        assert "h2" in metadata["headers_used"]
        assert "h1" in metadata["headers_used"]

        # Verify chunks have h3 metadata
        assert any(c.metadata.h3 == "Subsection One" for c in chunks)
        assert any(c.metadata.h3 == "Subsection Two" for c in chunks)

    def test_split_with_metadata_all_header_levels(self) -> None:
        """Should detect all header levels (h1, h2, h3) in one document."""
        splitter = MarkdownSplitter()
        markdown = """# Top Level

Introduction paragraph.

## Second Level

Some content here.

### Third Level

Detailed content.

### Another Third Level

More details.

## Another Second Level

Final content."""

        chunks, metadata = splitter.split_with_metadata(markdown)

        # All header levels should be detected
        assert metadata["headers_used"] == ["h1", "h2", "h3"]
        assert len(chunks) >= 3

        # Verify metadata structure
        assert metadata["total_chunks"] == len(chunks)
        assert metadata["total_tokens"] > 0
        assert metadata["max_chunk_tokens"] > 0

    def test_split_with_metadata_no_headers(self) -> None:
        """Should cover branch 245->247 when h1 is None (no headers)."""
        splitter = MarkdownSplitter()
        markdown = "Just plain text without any headers."

        chunks, metadata = splitter.split_with_metadata(markdown)

        # No headers should be detected
        assert metadata["headers_used"] == []
        assert len(chunks) == 1

        # Verify all chunks have no header metadata
        for chunk in chunks:
            assert chunk.metadata.h1 is None
            assert chunk.metadata.h2 is None
            assert chunk.metadata.h3 is None
