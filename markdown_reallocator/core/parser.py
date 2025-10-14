"""Hybrid parser using unstructured.io + custom enrichment.

This module wraps unstructured.io's partition_md and adds custom metadata
that is specific to our use case (sequence_number, is_inside_code_block, h1~h6).
"""

import logging
from pathlib import Path
from typing import Any

from unstructured.partition.md import partition_md
from unstructured.documents.elements import (
    Element,
    Title,
    NarrativeText,
    ListItem,
    Table,
    Text,
)

from markdown_reallocator.models.chunk import Chunk, ChunkMetadata, ElementType

logger = logging.getLogger(__name__)


class HybridMarkdownParser:
    """Hybrid parser combining unstructured.io with custom enrichment.

    Uses unstructured.io for core parsing (element extraction, hierarchy, coordinates)
    and adds custom metadata specific to markdown reallocation use case:
    - sequence_number: Detect procedural steps (Stage N, Step N)
    - is_inside_code_block: Flag code snippets
    - h1~h6: Precise header level tracking

    Examples:
        >>> parser = HybridMarkdownParser()
        >>> chunks = parser.parse_file("document.md")
        >>> len(chunks) > 0
        True
    """

    def __init__(
        self,
        max_tokens_per_chunk: int = 1000,
    ):
        """Initialize hybrid parser.

        Args:
            max_tokens_per_chunk: Maximum tokens per chunk (for warning)
        """
        self.max_tokens_per_chunk = max_tokens_per_chunk

    def parse_file(
        self,
        filepath: str | Path,
        **unstructured_kwargs: Any
    ) -> list[Chunk]:
        """Parse markdown file using hybrid approach.

        Args:
            filepath: Path to markdown file
            **unstructured_kwargs: Additional kwargs for partition_md

        Returns:
            List of Chunk objects with enriched metadata
        """
        # Step 1: Parse with unstructured.io
        elements = partition_md(
            filename=str(filepath),
            include_metadata=True,
            **unstructured_kwargs
        )

        if not elements:
            logger.warning(f"No elements parsed from {filepath}")
            return []

        # Step 2: Enrich with custom metadata
        chunks = self._enrich_elements(elements)

        return chunks

    def parse_text(
        self,
        text: str,
        **unstructured_kwargs: Any
    ) -> list[Chunk]:
        """Parse markdown text using hybrid approach.

        Args:
            text: Markdown text content
            **unstructured_kwargs: Additional kwargs for partition_md

        Returns:
            List of Chunk objects with enriched metadata
        """
        # Step 1: Parse with unstructured.io
        elements = partition_md(
            text=text,
            include_metadata=True,
            **unstructured_kwargs
        )

        if not elements:
            logger.warning("No elements parsed from text")
            return []

        # Step 2: Enrich with custom metadata
        chunks = self._enrich_elements(elements)

        return chunks

    def _enrich_elements(self, elements: list[Element]) -> list[Chunk]:
        """Enrich unstructured.io elements with custom metadata.

        Args:
            elements: Elements from unstructured.io

        Returns:
            List of enriched Chunk objects
        """
        from markdown_reallocator.core.enrichment import (
            detect_sequence_number,
            extract_precise_header_level,
            is_code_block,
            convert_element_type,
            estimate_tokens,
            generate_chunk_id,
        )

        chunks: list[Chunk] = []
        current_headers = {f"h{i}": None for i in range(1, 7)}  # Track h1-h6

        for i, elem in enumerate(elements):
            # Extract base metadata from unstructured.io
            parent_id = elem.metadata.parent_id if hasattr(elem.metadata, 'parent_id') else None
            category_depth = elem.metadata.category_depth if hasattr(elem.metadata, 'category_depth') else 0

            # Custom enrichment: sequence_number
            sequence_number = detect_sequence_number(elem.text)

            # Custom enrichment: h1~h6 precise tracking
            h_level, h_text = extract_precise_header_level(elem)

            # Update current headers tracking
            if h_level is not None:
                # Set this header
                current_headers[f"h{h_level}"] = h_text

                # Clear all deeper levels
                for j in range(h_level + 1, 7):
                    current_headers[f"h{j}"] = None

            # Custom enrichment: is_inside_code_block
            is_in_code = is_code_block(elem)

            # Convert element type
            element_type = convert_element_type(elem.category, sequence_number)

            # Estimate tokens
            token_count = estimate_tokens(elem.text)

            # Create ChunkMetadata (hybrid: unstructured.io + custom)
            metadata = ChunkMetadata(
                # From unstructured.io
                parent_id=parent_id,
                depth_level=category_depth or 0,

                # From custom logic
                h1=current_headers['h1'],
                h2=current_headers['h2'],
                h3=current_headers['h3'],
                h4=current_headers['h4'],
                h5=current_headers['h5'],
                h6=current_headers['h6'],
                sequence_number=sequence_number,
                is_inside_code_block=is_in_code,
                element_type=element_type,

                # Common
                original_position=i,
                token_count=token_count,
            )

            # Generate chunk ID
            chunk_id = generate_chunk_id(elem.text, i)

            # Create chunk
            chunk = Chunk(
                chunk_id=chunk_id,
                content=elem.text,
                metadata=metadata,
            )

            chunks.append(chunk)

        return chunks

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count (delegated to enrichment module).

        Args:
            text: Text to estimate tokens for

        Returns:
            Estimated token count
        """
        from markdown_reallocator.core.enrichment import estimate_tokens
        return estimate_tokens(text)
