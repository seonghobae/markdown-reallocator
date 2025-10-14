"""Custom metadata enrichment for unstructured.io elements.

This module provides domain-specific metadata extraction that is not available
in unstructured.io out of the box:

- sequence_number: Detect procedural steps (Stage N, Step N, Phase N)
- is_inside_code_block: Flag code snippets
- h1~h6 precise tracking: More granular than unstructured.io's Title vs Header
- element_type conversion: Map to our ElementType enum with custom logic
"""

import hashlib
import re

from unstructured.documents.elements import (
    Element,
    Title,
    NarrativeText,
    ListItem,
    Table,
    Text,
    FigureCaption,
    Image,
)

from markdown_reallocator.models.chunk import ElementType


def detect_sequence_number(text: str) -> int | None:
    """Detect procedural step numbers from text.

    Looks for patterns like "Stage 1", "Step 2", "Phase 3", etc.

    Args:
        text: Text to analyze

    Returns:
        Integer sequence number if found, None otherwise

    Examples:
        >>> detect_sequence_number("## Stage 1: Setup")
        1
        >>> detect_sequence_number("### Step 2: Installation")
        2
        >>> detect_sequence_number("Regular text")
        None
    """
    # Pattern: Stage/Step/Phase followed by number
    match = re.search(r'(Stage|Step|Phase)\s+(\d+)', text, re.IGNORECASE)
    if match:
        return int(match.group(2))
    return None


def extract_precise_header_level(elem: Element) -> tuple[int | None, str | None]:
    """Extract precise header level (h1-h6) from element.

    unstructured.io provides category_depth metadata for Title elements:
    - category_depth=0 → h1
    - category_depth=1 → h2
    - category_depth=2 → h3
    - etc.

    Args:
        elem: Element from unstructured.io

    Returns:
        Tuple of (level, text) where level is 1-6, or (None, None) if not a header

    Examples:
        >>> from unstructured.documents.elements import Title
        >>> elem = Title("My Title")
        >>> elem.metadata.category_depth = 0
        >>> extract_precise_header_level(elem)
        (1, 'My Title')
    """
    # Check if this is a Title element
    if elem.category != "Title":
        return None, None

    # Use category_depth from unstructured.io metadata
    if hasattr(elem.metadata, 'category_depth') and elem.metadata.category_depth is not None:
        # category_depth is 0-based, header level is 1-based
        level = elem.metadata.category_depth + 1
        if 1 <= level <= 6:
            return level, elem.text.strip()

    # Fallback: If no category_depth, assume h1
    if elem.category == "Title":
        return 1, elem.text.strip()

    return None, None


def is_code_block(elem: Element) -> bool:
    """Check if element is a code block.

    Args:
        elem: Element from unstructured.io

    Returns:
        True if element is code, False otherwise

    Examples:
        >>> from unstructured.documents.elements import Text
        >>> elem = Text("```python\\nprint('hello')\\n```")
        >>> is_code_block(elem)
        True
    """
    text = elem.text.strip()

    # Check if text starts with code fence
    if text.startswith('```'):
        return True

    # Check element category (unstructured.io may classify as CodeSnippet)
    if elem.category == "CodeSnippet":
        return True

    return False


def convert_element_type(
    category: str,
    sequence_number: int | None
) -> ElementType:
    """Convert unstructured.io category to our ElementType enum.

    Args:
        category: Element category from unstructured.io
        sequence_number: Detected sequence number (if procedural step)

    Returns:
        ElementType enum value

    Examples:
        >>> convert_element_type("Title", None)
        <ElementType.TITLE: 'title'>
        >>> convert_element_type("NarrativeText", 1)
        <ElementType.PROCEDURE_STEP: 'procedure_step'>
    """
    # Procedural step takes precedence (domain-specific)
    if sequence_number is not None:
        return ElementType.PROCEDURE_STEP

    # Map unstructured.io categories
    mapping = {
        "Title": ElementType.TITLE,
        "Header": ElementType.HEADER,
        "NarrativeText": ElementType.NARRATIVE_TEXT,
        "ListItem": ElementType.LIST_ITEM,
        "Table": ElementType.NARRATIVE_TEXT,  # No TABLE in ElementType, treat as narrative
        "CodeSnippet": ElementType.CODE_SNIPPET,
        "FigureCaption": ElementType.NARRATIVE_TEXT,  # Treat as narrative
        "Image": ElementType.NARRATIVE_TEXT,  # Treat as narrative
    }

    return mapping.get(category, ElementType.NARRATIVE_TEXT)


def estimate_tokens(text: str) -> int:
    """Estimate token count using simple whitespace-based heuristic.

    This is a fast approximation. For more accuracy, use tiktoken.

    Args:
        text: Text to estimate tokens for

    Returns:
        Estimated token count (roughly words * 1.3)

    Examples:
        >>> estimate_tokens("Hello world this is a test")
        8
        >>> estimate_tokens("")
        0
    """
    if not text.strip():
        return 0

    # Simple heuristic: split on whitespace
    words = len(text.split())

    # Average English token/word ratio is ~1.3
    # (accounting for subword tokenization)
    return int(words * 1.3)


def generate_chunk_id(content: str, position: int) -> str:
    """Generate unique chunk ID from content and position.

    Uses SHA256 hash of content + position for deterministic IDs.

    Args:
        content: Chunk content
        position: Position in document

    Returns:
        Hex string chunk ID (8 characters)

    Examples:
        >>> generate_chunk_id("Hello world", 0)
        '88d4266f'
        >>> generate_chunk_id("Hello world", 1)
        'bdd19c8f'
    """
    # Create deterministic ID from content + position
    identifier = f"{content}{position}".encode()
    hash_digest = hashlib.sha256(identifier).hexdigest()

    # Use first 8 characters of hash
    return hash_digest[:8]
