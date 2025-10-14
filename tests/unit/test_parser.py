"""Unit tests for HybridMarkdownParser."""

import sys
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from tempfile import NamedTemporaryFile

from markdown_reallocator.core.parser import HybridMarkdownParser
from markdown_reallocator.models.chunk import ElementType


class TestHybridMarkdownParser:
    """Test HybridMarkdownParser class."""

    def test_parse_text_basic(self):
        """Test basic text parsing."""
        parser = HybridMarkdownParser(max_tokens_per_chunk=1000)
        markdown = """# Title

## Section

Paragraph text."""

        chunks = parser.parse_text(markdown)

        assert len(chunks) > 0
        # Check h1 detection
        h1_chunks = [c for c in chunks if c.metadata.h1 is not None]
        assert len(h1_chunks) > 0

    def test_parse_text_whitespace_only(self):
        """Test parsing whitespace-only text returns empty list."""
        parser = HybridMarkdownParser()
        # unstructured.io treats whitespace-only as no content
        chunks = parser.parse_text("\n\n   \n\n")

        # Should return empty list (logged warning)
        assert isinstance(chunks, list)
        assert len(chunks) == 0

    def test_parse_file(self):
        """Test parsing from file."""
        parser = HybridMarkdownParser()

        # Create temporary markdown file
        with NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("# Test File\n\n## Section\n\nContent here.")
            temp_path = f.name

        try:
            chunks = parser.parse_file(temp_path)

            assert len(chunks) > 0
            # Check h1 detection
            h1_chunks = [c for c in chunks if c.metadata.h1 == "Test File"]
            assert len(h1_chunks) > 0
        finally:
            Path(temp_path).unlink()

    def test_parse_file_empty(self):
        """Test parsing empty/whitespace-only file."""
        parser = HybridMarkdownParser()

        # Create temporary empty markdown file
        with NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("\n\n   \n\n")  # Only whitespace
            temp_path = f.name

        try:
            chunks = parser.parse_file(temp_path)

            # Should return empty list (logged warning)
            assert isinstance(chunks, list)
            assert len(chunks) == 0
        finally:
            Path(temp_path).unlink()

    def test_parse_file_nonexistent(self):
        """Test parsing non-existent file."""
        parser = HybridMarkdownParser()

        # Should raise FileNotFoundError
        with pytest.raises(FileNotFoundError):
            parser.parse_file("/tmp/nonexistent_file_12345.md")

    def test_hierarchical_tracking(self):
        """Test that headers cascade to child elements."""
        parser = HybridMarkdownParser()
        markdown = """# Title

## Section 1

Paragraph 1.

Paragraph 2.

## Section 2

Paragraph 3."""

        chunks = parser.parse_text(markdown)

        # Find paragraph chunks
        para_chunks = [c for c in chunks if c.metadata.element_type == ElementType.NARRATIVE_TEXT]

        # All paragraphs should have h1="Title"
        for chunk in para_chunks:
            assert chunk.metadata.h1 == "Title"

        # Paragraphs under Section 1 should have h2="Section 1"
        para1_chunks = [c for c in para_chunks if "Paragraph 1" in c.content or "Paragraph 2" in c.content]
        for chunk in para1_chunks:
            assert chunk.metadata.h2 == "Section 1"

    def test_sequence_number_detection(self):
        """Test procedural step detection."""
        parser = HybridMarkdownParser()
        markdown = """# Guide

## Stage 1: Setup

Instructions here.

## Stage 2: Development

More instructions."""

        chunks = parser.parse_text(markdown)

        # Find chunks with sequence numbers
        stage_chunks = [c for c in chunks if c.metadata.sequence_number is not None]

        assert len(stage_chunks) >= 2
        seq_numbers = sorted([c.metadata.sequence_number for c in stage_chunks])
        assert seq_numbers[:2] == [1, 2]

    def test_element_type_conversion(self):
        """Test element type mapping."""
        parser = HybridMarkdownParser()
        markdown = """# Title

Paragraph text.

- List item 1
- List item 2

## Stage 1: Action

Step content."""

        chunks = parser.parse_text(markdown)

        # Check TITLE
        title_chunks = [c for c in chunks if c.metadata.element_type == ElementType.TITLE]
        assert len(title_chunks) > 0

        # Check NARRATIVE_TEXT
        text_chunks = [c for c in chunks if c.metadata.element_type == ElementType.NARRATIVE_TEXT]
        assert len(text_chunks) > 0

        # Check LIST_ITEM
        list_chunks = [c for c in chunks if c.metadata.element_type == ElementType.LIST_ITEM]
        assert len(list_chunks) > 0

        # Check PROCEDURE_STEP (Stage 1 should be detected)
        proc_chunks = [c for c in chunks if c.metadata.element_type == ElementType.PROCEDURE_STEP]
        assert len(proc_chunks) > 0

    def test_chunk_metadata(self):
        """Test that all metadata fields are populated."""
        parser = HybridMarkdownParser()
        markdown = """# Test

Content here."""

        chunks = parser.parse_text(markdown)

        for chunk in chunks:
            # Check required metadata
            assert chunk.chunk_id is not None
            assert chunk.content is not None
            assert chunk.metadata is not None
            assert chunk.metadata.token_count >= 0
            assert chunk.metadata.original_position >= 0
            assert chunk.metadata.element_type is not None

    def test_estimate_tokens_method(self):
        """Test estimate_tokens method (delegated to enrichment)."""
        parser = HybridMarkdownParser()

        tokens = parser.estimate_tokens("Hello world this is a test")
        assert tokens > 0

        tokens_empty = parser.estimate_tokens("")
        assert tokens_empty == 0

    def test_max_tokens_parameter(self):
        """Test max_tokens_per_chunk parameter."""
        parser = HybridMarkdownParser(max_tokens_per_chunk=500)
        assert parser.max_tokens_per_chunk == 500

        parser2 = HybridMarkdownParser(max_tokens_per_chunk=2000)
        assert parser2.max_tokens_per_chunk == 2000

    def test_code_block_in_markdown(self):
        """Test code block preservation."""
        parser = HybridMarkdownParser()
        markdown = """# Guide

```python
def hello():
    print("Hello, World!")
```

End of guide."""

        chunks = parser.parse_text(markdown)

        # Find code-related chunks
        code_chunks = [c for c in chunks if "def hello" in c.content or "print" in c.content]

        # Code should be preserved
        assert len(code_chunks) > 0
