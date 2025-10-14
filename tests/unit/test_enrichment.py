"""Unit tests for custom enrichment functions."""

import sys
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from unstructured.documents.elements import Title, NarrativeText, Text

from markdown_reallocator.core.enrichment import (
    detect_sequence_number,
    extract_precise_header_level,
    is_code_block,
    convert_element_type,
    estimate_tokens,
    generate_chunk_id,
)
from markdown_reallocator.models.chunk import ElementType


class TestDetectSequenceNumber:
    """Test sequence number detection."""

    def test_stage_detection(self):
        assert detect_sequence_number("## Stage 1: Setup") == 1
        assert detect_sequence_number("### Stage 2: Development") == 2
        assert detect_sequence_number("Stage 10: Deployment") == 10

    def test_step_detection(self):
        assert detect_sequence_number("Step 1: Install") == 1
        assert detect_sequence_number("### Step 5: Configure") == 5

    def test_phase_detection(self):
        assert detect_sequence_number("Phase 3: Testing") == 3

    def test_case_insensitive(self):
        assert detect_sequence_number("stage 1: setup") == 1
        assert detect_sequence_number("STEP 2: BUILD") == 2

    def test_no_sequence(self):
        assert detect_sequence_number("Regular text") is None
        assert detect_sequence_number("## Overview") is None


class TestExtractPreciseHeaderLevel:
    """Test header level extraction."""

    def test_h1_extraction(self):
        elem = Title("Project Documentation")
        elem.metadata.category_depth = 0
        level, text = extract_precise_header_level(elem)
        assert level == 1
        assert text == "Project Documentation"

    def test_h2_extraction(self):
        elem = Title("Overview")
        elem.metadata.category_depth = 1
        level, text = extract_precise_header_level(elem)
        assert level == 2
        assert text == "Overview"

    def test_h3_extraction(self):
        elem = Title("Installation Steps")
        elem.metadata.category_depth = 2
        level, text = extract_precise_header_level(elem)
        assert level == 3
        assert text == "Installation Steps"

    def test_h4_h5_h6(self):
        for depth, expected_level in [(3, 4), (4, 5), (5, 6)]:
            elem = Title(f"Header {expected_level}")
            elem.metadata.category_depth = depth
            level, text = extract_precise_header_level(elem)
            assert level == expected_level
            assert text == f"Header {expected_level}"

    def test_non_title_element(self):
        elem = NarrativeText("Regular paragraph")
        level, text = extract_precise_header_level(elem)
        assert level is None
        assert text is None

    def test_title_without_category_depth(self):
        """Test fallback: Title without category_depth assumes h1."""
        elem = Title("Untitled")
        # Don't set category_depth
        level, text = extract_precise_header_level(elem)
        assert level == 1
        assert text == "Untitled"


class TestIsCodeBlock:
    """Test code block detection."""

    def test_code_fence_detection(self):
        elem = Text("```python\nprint('hello')\n```")
        assert is_code_block(elem) is True

    def test_code_snippet_category(self):
        elem = Text("print('hello')")
        elem.category = "CodeSnippet"
        assert is_code_block(elem) is True

    def test_not_code_block(self):
        elem = NarrativeText("Regular text")
        assert is_code_block(elem) is False


class TestConvertElementType:
    """Test element type conversion."""

    def test_procedure_step_priority(self):
        """Sequence number takes precedence over category."""
        result = convert_element_type("NarrativeText", sequence_number=1)
        assert result == ElementType.PROCEDURE_STEP

        result = convert_element_type("Title", sequence_number=2)
        assert result == ElementType.PROCEDURE_STEP

    def test_title_mapping(self):
        result = convert_element_type("Title", sequence_number=None)
        assert result == ElementType.TITLE

    def test_header_mapping(self):
        result = convert_element_type("Header", sequence_number=None)
        assert result == ElementType.HEADER

    def test_narrative_text_mapping(self):
        result = convert_element_type("NarrativeText", sequence_number=None)
        assert result == ElementType.NARRATIVE_TEXT

    def test_list_item_mapping(self):
        result = convert_element_type("ListItem", sequence_number=None)
        assert result == ElementType.LIST_ITEM

    def test_table_mapping(self):
        """Table maps to NARRATIVE_TEXT (no TABLE in ElementType)."""
        result = convert_element_type("Table", sequence_number=None)
        assert result == ElementType.NARRATIVE_TEXT

    def test_code_snippet_mapping(self):
        result = convert_element_type("CodeSnippet", sequence_number=None)
        assert result == ElementType.CODE_SNIPPET

    def test_figure_caption_mapping(self):
        result = convert_element_type("FigureCaption", sequence_number=None)
        assert result == ElementType.NARRATIVE_TEXT

    def test_image_mapping(self):
        result = convert_element_type("Image", sequence_number=None)
        assert result == ElementType.NARRATIVE_TEXT

    def test_unknown_category(self):
        """Unknown categories default to NARRATIVE_TEXT."""
        result = convert_element_type("UnknownType", sequence_number=None)
        assert result == ElementType.NARRATIVE_TEXT


class TestEstimateTokens:
    """Test token estimation."""

    def test_simple_text(self):
        tokens = estimate_tokens("Hello world this is a test")
        # 6 words * 1.3 = 7.8 → 7
        assert tokens == 7

    def test_empty_text(self):
        assert estimate_tokens("") == 0
        assert estimate_tokens("   ") == 0

    def test_single_word(self):
        tokens = estimate_tokens("Hello")
        # 1 word * 1.3 = 1.3 → 1
        assert tokens == 1

    def test_long_text(self):
        text = "This is a longer text with many words to test token estimation accuracy"
        tokens = estimate_tokens(text)
        # 13 words * 1.3 = 16.9 → 16
        assert tokens == 16


class TestGenerateChunkId:
    """Test chunk ID generation."""

    def test_deterministic(self):
        """Same content and position should produce same ID."""
        id1 = generate_chunk_id("Hello world", 0)
        id2 = generate_chunk_id("Hello world", 0)
        assert id1 == id2
        assert len(id1) == 8

    def test_different_content(self):
        """Different content should produce different IDs."""
        id1 = generate_chunk_id("Hello world", 0)
        id2 = generate_chunk_id("Goodbye world", 0)
        assert id1 != id2

    def test_different_position(self):
        """Different position should produce different IDs."""
        id1 = generate_chunk_id("Hello world", 0)
        id2 = generate_chunk_id("Hello world", 1)
        assert id1 != id2

    def test_hex_format(self):
        """ID should be 8-character hex string."""
        chunk_id = generate_chunk_id("Test", 42)
        assert len(chunk_id) == 8
        # Check if valid hex
        int(chunk_id, 16)  # Should not raise ValueError
