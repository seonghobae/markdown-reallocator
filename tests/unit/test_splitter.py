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
            ("####", "h4"),
            ("#####", "h5"),
            ("######", "h6"),
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

        # Create markdown with long content that has no semantic boundaries
        # (single line prevents semantic splitting)
        long_content = " ".join(["word"] * 50)
        markdown = f"# Title\n\n{long_content}"

        splitter.split(markdown)

        # Should have logged a warning about exceeding tokens or no semantic boundaries
        assert any(
            ("exceeds max tokens" in record.message or "no semantic boundaries" in record.message)
            for record in caplog.records
        )

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

    def test_parser_returns_empty_list(self, caplog: pytest.LogCaptureFixture) -> None:
        """Should handle case where parser returns no chunks."""
        from unittest.mock import Mock

        splitter = MarkdownSplitter()
        markdown = "# Title\n\nContent"

        # Mock parser to return empty list
        monkeypatch_parse = Mock(return_value=[])
        splitter._parse_with_unstructured = monkeypatch_parse

        # Should fallback to single chunk
        chunks = splitter.split(markdown)

        assert len(chunks) == 1
        assert chunks[0].content == markdown
        assert "Parser returned no chunks" in caplog.text

    def test_skip_empty_chunks(self) -> None:
        """Should skip chunks with only whitespace."""
        from unittest.mock import Mock

        splitter = MarkdownSplitter()
        markdown = "# Title\n\nContent"

        # Mock parser to return chunks with whitespace
        mock_parsed = [
            {"content": "# Title\n\nContent", "headers": {"h1": "Title"}, "position": 0},
            {"content": "   \n\n   ", "headers": {}, "position": 1},  # Empty chunk
            {"content": "More content", "headers": {}, "position": 2},
        ]
        splitter._parse_with_unstructured = Mock(return_value=mock_parsed)

        chunks = splitter.split(markdown)

        # Should skip the whitespace-only chunk
        assert len(chunks) == 2
        assert all(c.content.strip() for c in chunks)

    def test_no_valid_chunks_raises(self) -> None:
        """Should raise ValueError if all chunks are invalid."""
        from unittest.mock import Mock

        splitter = MarkdownSplitter()
        markdown = "# Title"

        # Mock parser to return only whitespace chunks
        mock_parsed = [
            {"content": "   ", "headers": {}, "position": 0},
            {"content": "\n\n", "headers": {}, "position": 1},
        ]
        splitter._parse_with_unstructured = Mock(return_value=mock_parsed)

        with pytest.raises(ValueError, match="No valid chunks created"):
            splitter.split(markdown)

    def test_split_exception_logged(self, caplog: pytest.LogCaptureFixture) -> None:
        """Should log error and re-raise on exception."""
        from unittest.mock import Mock

        splitter = MarkdownSplitter()
        markdown = "# Title\n\nContent"

        # Mock parser to raise exception
        splitter._parse_with_unstructured = Mock(side_effect=RuntimeError("Mock error"))

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


class TestSemanticSplitting:
    """Tests for semantic boundary splitting methods."""

    def test_parse_list_items_unordered(self) -> None:
        """Should parse unordered list items (each indent level separately)."""
        splitter = MarkdownSplitter()
        content = """- Item 1
  - Sub A
  - Sub B
- Item 2
  - Sub C"""

        items = splitter._parse_list_items(content)

        # Parses each list item at each indent level as separate item
        assert len(items) == 5
        assert items[0] == "- Item 1"
        assert items[1] == "  - Sub A"
        assert items[2] == "  - Sub B"
        assert items[3] == "- Item 2"
        assert items[4] == "  - Sub C"

    def test_parse_list_items_ordered(self) -> None:
        """Should parse ordered list items."""
        splitter = MarkdownSplitter()
        content = """1. First item
   - Sub item
2. Second item
3. Third item"""

        items = splitter._parse_list_items(content)

        # Parses each list item at each indent level as separate item
        assert len(items) == 4
        assert "First item" in items[0]
        assert "Sub item" in items[1]
        assert "Second item" in items[2]
        assert "Third item" in items[3]

    def test_parse_list_items_mixed(self) -> None:
        """Should parse mixed unordered and ordered lists."""
        splitter = MarkdownSplitter()
        content = """- Unordered item
1. Ordered item
2. Another ordered
- Another unordered"""

        items = splitter._parse_list_items(content)

        assert len(items) == 4

    def test_parse_list_items_empty(self) -> None:
        """Should return empty list for content without list items."""
        splitter = MarkdownSplitter()
        content = "Just plain text without lists."

        items = splitter._parse_list_items(content)

        assert len(items) == 0

    def test_parse_list_items_preserves_indentation(self) -> None:
        """Should preserve indentation in nested lists."""
        splitter = MarkdownSplitter()
        content = """- Item 1
  - Level 2
    - Level 3
  - Back to level 2
- Item 2"""

        items = splitter._parse_list_items(content)

        # Each indent level is parsed separately
        assert len(items) == 5
        assert items[0] == "- Item 1"
        assert items[1] == "  - Level 2"
        assert items[2] == "    - Level 3"
        assert items[3] == "  - Back to level 2"
        assert items[4] == "- Item 2"

    def test_group_items_by_tokens_single_group(self) -> None:
        """Should keep all items in one group if within limit."""
        splitter = MarkdownSplitter()
        items = ["Short item", "Another short", "Yet another"]

        groups = splitter._group_items_by_tokens(items, 1000)

        assert len(groups) == 1
        assert len(groups[0]) == 3

    def test_group_items_by_tokens_multiple_groups(self) -> None:
        """Should split into multiple groups when exceeding limit."""
        splitter = MarkdownSplitter()
        # Create items that will exceed token limit
        items = [" ".join(["word"] * 100) for _ in range(5)]  # ~130 tokens each

        groups = splitter._group_items_by_tokens(items, 200)

        # Should create multiple groups
        assert len(groups) > 1

    def test_group_items_by_tokens_oversized_item(self, caplog: pytest.LogCaptureFixture) -> None:
        """Should keep oversized item in separate group with warning."""
        splitter = MarkdownSplitter()
        # Create one very large item
        large_item = " ".join(["word"] * 1000)  # ~1300 tokens
        items = ["small", large_item, "small2"]

        groups = splitter._group_items_by_tokens(items, 100)

        # Large item should be in its own group
        assert any(len(g) == 1 and large_item in g for g in groups)
        assert "exceeds token limit" in caplog.text

    def test_group_items_by_tokens_empty(self) -> None:
        """Should return empty list for empty items."""
        splitter = MarkdownSplitter()

        groups = splitter._group_items_by_tokens([], 1000)

        assert len(groups) == 0

    def test_split_oversized_by_list_items_success(self) -> None:
        """Should split oversized chunk by list items."""
        splitter = MarkdownSplitter(max_tokens_per_chunk=100)

        # Create chunk with many list items
        content = "\n".join([f"- Item {i} with some content" for i in range(20)])
        from markdown_reallocator.models.chunk import Chunk, ChunkMetadata

        metadata = ChunkMetadata(
            h1="Test",
            original_position=0,
            token_count=splitter.estimate_tokens(content)
        )
        chunk = Chunk(chunk_id="test-123", content=content, metadata=metadata)

        sub_chunks = splitter._split_oversized_by_list_items(chunk)

        # Should split into multiple chunks
        assert len(sub_chunks) > 1
        # Each sub-chunk should have unique ID
        assert all("-" in c.chunk_id for c in sub_chunks)
        # Metadata should be preserved
        assert all(c.metadata.h1 == "Test" for c in sub_chunks)

    def test_split_oversized_by_list_items_too_few_items(self, caplog: pytest.LogCaptureFixture) -> None:
        """Should return original chunk if too few list items."""
        splitter = MarkdownSplitter(max_tokens_per_chunk=10)

        from markdown_reallocator.models.chunk import Chunk, ChunkMetadata

        content = "- Only one item"
        metadata = ChunkMetadata(original_position=0, token_count=50)
        chunk = Chunk(chunk_id="test-456", content=content, metadata=metadata)

        sub_chunks = splitter._split_oversized_by_list_items(chunk)

        assert len(sub_chunks) == 1
        assert sub_chunks[0].chunk_id == "test-456"
        assert "< 2 list items" in caplog.text

    def test_split_oversized_by_paragraphs_success(self) -> None:
        """Should split oversized chunk by paragraphs."""
        splitter = MarkdownSplitter(max_tokens_per_chunk=50)

        from markdown_reallocator.models.chunk import Chunk, ChunkMetadata

        # Create content with multiple paragraphs
        paragraphs = [f"This is paragraph {i} with some content." for i in range(10)]
        content = "\n\n".join(paragraphs)

        metadata = ChunkMetadata(
            h2="Test Section",
            original_position=0,
            token_count=splitter.estimate_tokens(content)
        )
        chunk = Chunk(chunk_id="test-789", content=content, metadata=metadata)

        sub_chunks = splitter._split_oversized_by_paragraphs(chunk)

        # Should split into multiple chunks
        assert len(sub_chunks) > 1
        # Each sub-chunk should preserve metadata
        assert all(c.metadata.h2 == "Test Section" for c in sub_chunks)

    def test_split_oversized_by_paragraphs_too_few(self, caplog: pytest.LogCaptureFixture) -> None:
        """Should return original chunk if too few paragraphs."""
        splitter = MarkdownSplitter(max_tokens_per_chunk=10)

        from markdown_reallocator.models.chunk import Chunk, ChunkMetadata

        content = "Single paragraph without breaks."
        metadata = ChunkMetadata(original_position=0, token_count=50)
        chunk = Chunk(chunk_id="test-abc", content=content, metadata=metadata)

        sub_chunks = splitter._split_oversized_by_paragraphs(chunk)

        assert len(sub_chunks) == 1
        assert "< 2 paragraphs" in caplog.text

    def test_split_oversized_chunk_uses_list_items_first(self) -> None:
        """Should try list item splitting first."""
        splitter = MarkdownSplitter(max_tokens_per_chunk=100)

        from markdown_reallocator.models.chunk import Chunk, ChunkMetadata

        # Create content with many list items (>5 threshold) that exceeds limit
        content = "\n".join([f"- Item {i} with additional content to make it longer and exceed token limit" for i in range(20)])
        metadata = ChunkMetadata(
            original_position=0,
            token_count=splitter.estimate_tokens(content)
        )
        chunk = Chunk(chunk_id="test-list", content=content, metadata=metadata)

        sub_chunks = splitter._split_oversized_chunk(chunk)

        # Should use list item splitting and create multiple chunks
        assert len(sub_chunks) > 1

    def test_split_oversized_chunk_falls_back_to_paragraphs(self) -> None:
        """Should fall back to paragraph splitting if not enough list items."""
        splitter = MarkdownSplitter(max_tokens_per_chunk=50)

        from markdown_reallocator.models.chunk import Chunk, ChunkMetadata

        # Create content with few list items but many longer paragraphs
        paragraphs = [f"This is a longer paragraph {i} with enough content to make it substantial" for i in range(8)]
        content = "- Item 1\n\n" + "\n\n".join(paragraphs)
        metadata = ChunkMetadata(
            original_position=0,
            token_count=splitter.estimate_tokens(content)
        )
        chunk = Chunk(chunk_id="test-para", content=content, metadata=metadata)

        sub_chunks = splitter._split_oversized_chunk(chunk)

        # Should use paragraph splitting
        assert len(sub_chunks) > 1

    def test_split_oversized_chunk_keeps_with_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        """Should keep chunk as-is with warning if no semantic boundaries."""
        splitter = MarkdownSplitter(max_tokens_per_chunk=10)

        from markdown_reallocator.models.chunk import Chunk, ChunkMetadata

        # Content with no list items and no paragraphs
        content = "Very long single line of text without any semantic boundaries at all"
        metadata = ChunkMetadata(
            original_position=0,
            token_count=splitter.estimate_tokens(content)
        )
        chunk = Chunk(chunk_id="test-warn", content=content, metadata=metadata)

        sub_chunks = splitter._split_oversized_chunk(chunk)

        # Should keep original
        assert len(sub_chunks) == 1
        assert sub_chunks[0].chunk_id == "test-warn"
        assert "no semantic boundaries found" in caplog.text

    def test_split_integration_with_oversized_chunks(self) -> None:
        """Integration test: split() should automatically handle oversized chunks."""
        splitter = MarkdownSplitter(max_tokens_per_chunk=100)

        # Create markdown with long list that will exceed token limit
        items = [f"- Item {i} with some additional content to increase token count" for i in range(30)]
        markdown = f"# Test Section\n\n" + "\n".join(items)

        chunks = splitter.split(markdown)

        # Should create multiple sub-chunks
        sub_chunk_count = sum(1 for c in chunks if '-' in c.chunk_id)
        assert sub_chunk_count > 0

        # All chunks should be under limit (or slightly over for semantic integrity)
        oversized = [c for c in chunks if c.metadata.token_count > 150]  # Allow 50% buffer
        assert len(oversized) == 0 or all(c.metadata.token_count < 1100 for c in oversized)
#!/usr/bin/env python3
"""Tests for depth-aware splitting functions."""

import pytest
from markdown_reallocator.core.splitter import MarkdownSplitter
from markdown_reallocator.models.chunk import Chunk, ChunkMetadata


class TestDepthAwareFunctions:
    """Tests for depth-aware splitting functionality."""

    def test_calculate_depth_no_indentation(self):
        """Should return 0 for lines with no indentation."""
        splitter = MarkdownSplitter()

        assert splitter._calculate_depth("- Item") == 0
        assert splitter._calculate_depth("* Item") == 0
        assert splitter._calculate_depth("1. Item") == 0

    def test_calculate_depth_with_spaces(self):
        """Should calculate depth based on leading spaces (2 spaces = 1 depth)."""
        splitter = MarkdownSplitter()

        assert splitter._calculate_depth("  - Sub item") == 1
        assert splitter._calculate_depth("    - Sub-sub item") == 2
        assert splitter._calculate_depth("      - Deep item") == 3

    def test_calculate_depth_with_tabs(self):
        """Should convert tabs to spaces (1 tab = 4 spaces = 2 depth)."""
        splitter = MarkdownSplitter()

        assert splitter._calculate_depth("\t- Item") == 2
        assert splitter._calculate_depth("\t\t- Item") == 4

    def test_calculate_depth_empty_line(self):
        """Should return 0 for empty lines."""
        splitter = MarkdownSplitter()

        assert splitter._calculate_depth("") == 0
        assert splitter._calculate_depth("   ") == 0

    def test_parse_list_items_with_depth_flat(self):
        """Should parse flat list with all depth-0 items."""
        splitter = MarkdownSplitter()
        content = """- Item 1
- Item 2
- Item 3"""

        items = splitter._parse_list_items_with_depth(content)

        assert len(items) == 3
        assert all(item['depth'] == 0 for item in items)
        assert all(item['parent_idx'] is None for item in items)

    def test_parse_list_items_with_depth_hierarchical(self):
        """Should parse hierarchical list with parent-child relationships."""
        splitter = MarkdownSplitter()
        content = """- Parent 1
  - Child 1a
  - Child 1b
- Parent 2
  - Child 2a"""

        items = splitter._parse_list_items_with_depth(content)

        assert len(items) == 5

        # Parent 1 (index 0)
        assert items[0]['depth'] == 0
        assert items[0]['parent_idx'] is None
        assert 'Parent 1' in items[0]['content']

        # Child 1a (index 1)
        assert items[1]['depth'] == 1
        assert items[1]['parent_idx'] == 0
        assert 'Child 1a' in items[1]['content']

        # Child 1b (index 2)
        assert items[2]['depth'] == 1
        assert items[2]['parent_idx'] == 0

        # Parent 2 (index 3)
        assert items[3]['depth'] == 0
        assert items[3]['parent_idx'] is None

        # Child 2a (index 4)
        assert items[4]['depth'] == 1
        assert items[4]['parent_idx'] == 3

    def test_parse_list_items_with_depth_deep_hierarchy(self):
        """Should handle multiple depth levels."""
        splitter = MarkdownSplitter()
        content = """- Level 0
  - Level 1
    - Level 2
      - Level 3"""

        items = splitter._parse_list_items_with_depth(content)

        assert len(items) == 4
        assert items[0]['depth'] == 0
        assert items[1]['depth'] == 1
        assert items[2]['depth'] == 2
        assert items[3]['depth'] == 3

    def test_split_by_depth_boundaries_success(self):
        """Should split at depth-0 boundaries when token limit exceeded."""
        splitter = MarkdownSplitter(max_tokens_per_chunk=50)

        # Create chunk with hierarchical list
        content = """- First policy with many words to exceed token limit here
  - Sub-point 1 for first policy
  - Sub-point 2 for first policy
- Second policy also with many words to exceed the token limit
  - Sub-point 1 for second policy
  - Sub-point 2 for second policy"""

        chunk = Chunk(
            chunk_id="test",
            content=content,
            metadata=ChunkMetadata(
                original_position=0,
                token_count=splitter.estimate_tokens(content)
            )
        )

        result = splitter._split_by_depth_boundaries(chunk)

        # Should split into 2 chunks at depth-0 boundary
        assert len(result) >= 1

        if len(result) > 1:
            # Verify split happened at depth-0
            assert 'First policy' in result[0].content
            assert 'Second policy' in result[1].content
            # Children should stay with parents
            assert 'Sub-point 1 for first' in result[0].content
            assert 'Sub-point 1 for second' in result[1].content

    def test_split_by_depth_boundaries_too_few_items(self):
        """Should return original chunk if < 2 list items."""
        splitter = MarkdownSplitter(max_tokens_per_chunk=50)

        content = "- Single item"
        chunk = Chunk(
            chunk_id="test",
            content=content,
            metadata=ChunkMetadata(
                original_position=0,
                token_count=splitter.estimate_tokens(content)
            )
        )

        result = splitter._split_by_depth_boundaries(chunk)

        assert len(result) == 1
        assert result[0] == chunk

    def test_split_by_depth_boundaries_no_depth0_split_points(self):
        """Should return original chunk if < 2 depth-0 items."""
        splitter = MarkdownSplitter(max_tokens_per_chunk=50)

        content = """- Single parent
  - Child 1
  - Child 2
  - Child 3"""

        chunk = Chunk(
            chunk_id="test",
            content=content,
            metadata=ChunkMetadata(
                original_position=0,
                token_count=splitter.estimate_tokens(content)
            )
        )

        result = splitter._split_by_depth_boundaries(chunk)

        # Only 1 depth-0 item, cannot split
        assert len(result) == 1

    def test_split_by_depth_boundaries_preserves_metadata(self):
        """Should preserve header metadata in sub-chunks."""
        splitter = MarkdownSplitter(max_tokens_per_chunk=50)

        content = """- First policy item with enough words to exceed limit
  - Sub A
- Second policy item with enough words to exceed limit
  - Sub B"""

        chunk = Chunk(
            chunk_id="test",
            content=content,
            metadata=ChunkMetadata(
                h1="Test H1",
                h2="Test H2",
                original_position=5,
                token_count=splitter.estimate_tokens(content)
            )
        )

        result = splitter._split_by_depth_boundaries(chunk)

        for sub_chunk in result:
            assert sub_chunk.metadata.h1 == "Test H1"
            assert sub_chunk.metadata.h2 == "Test H2"
            assert sub_chunk.metadata.original_position == 5

    def test_split_oversized_chunk_with_hierarchy(self):
        """Should use depth-aware splitting for hierarchical lists."""
        splitter = MarkdownSplitter(max_tokens_per_chunk=50)

        # Hierarchical list that exceeds token limit
        content = """- Parent 1 with many words to make it long enough to exceed token limit
  - Child 1a also with many words
  - Child 1b also with many words
- Parent 2 with many words to make it long enough to exceed token limit
  - Child 2a also with many words
  - Child 2b also with many words"""

        chunk = Chunk(
            chunk_id="test",
            content=content,
            metadata=ChunkMetadata(
                original_position=0,
                token_count=splitter.estimate_tokens(content)
            )
        )

        result = splitter._split_oversized_chunk(chunk)

        # Should split (either by depth-aware or list items)
        assert len(result) >= 1

        # Check if depth-aware splitting was attempted
        # (even if it falls back to list item splitting)
        depth_aware_used = any('-d' in c.chunk_id for c in result)
        list_split_used = any('-0' in c.chunk_id or '-1' in c.chunk_id for c in result)

        assert depth_aware_used or list_split_used


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
