"""Markdown splitter using LangChain.

This module provides semantic markdown chunking that splits by headers
while preserving hierarchy metadata.
"""

import hashlib
import logging
import re
from typing import Any

from langchain_text_splitters import MarkdownHeaderTextSplitter

from markdown_reallocator.models.chunk import Chunk, ChunkMetadata

logger = logging.getLogger(__name__)


class MarkdownSplitter:
    """Splitter for markdown documents based on header hierarchy.

    This class wraps LangChain's MarkdownHeaderTextSplitter and converts
    results into our Chunk/ChunkMetadata format.

    Examples:
        >>> splitter = MarkdownSplitter()
        >>> markdown = "# Title\\n\\nContent\\n\\n## Section\\n\\nMore content"
        >>> chunks = splitter.split(markdown)
        >>> len(chunks)
        2
        >>> chunks[0].metadata.h1
        'Title'
    """

    def __init__(
        self,
        headers_to_split_on: list[tuple[str, str]] | None = None,
        max_tokens_per_chunk: int = 1000,
    ):
        """Initialize splitter with configuration.

        Args:
            headers_to_split_on: List of (header_marker, header_name) tuples.
                Defaults to [("#", "h1"), ("##", "h2"), ("###", "h3")].
            max_tokens_per_chunk: Maximum estimated tokens per chunk.
                Chunks exceeding this will trigger a warning.
        """
        self.headers_to_split_on = headers_to_split_on or [
            ("#", "h1"),
            ("##", "h2"),
            ("###", "h3"),
            ("####", "h4"),
            ("#####", "h5"),
            ("######", "h6"),
        ]
        self.max_tokens_per_chunk = max_tokens_per_chunk

        # Initialize LangChain splitter
        self._splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=self.headers_to_split_on,
            strip_headers=False,  # Keep headers in content
        )

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count using simple whitespace-based heuristic.

        This is a fast approximation. For more accuracy, use tiktoken.

        Args:
            text: Text to estimate tokens for

        Returns:
            Estimated token count (roughly words * 1.3)

        Examples:
            >>> splitter = MarkdownSplitter()
            >>> splitter.estimate_tokens("Hello world this is a test")
            8
        """
        if not text.strip():
            return 0

        # Simple heuristic: split on whitespace and punctuation
        words = len(text.split())

        # Average English token/word ratio is ~1.3
        # (accounting for subword tokenization)
        return int(words * 1.3)

    def _extract_metadata(
        self,
        langchain_metadata: dict[str, str],
        position: int,
        content: str
    ) -> ChunkMetadata:
        """Extract metadata from LangChain split result.

        Args:
            langchain_metadata: Metadata dict from LangChain splitter
            position: Position in original document
            content: Content of the chunk

        Returns:
            ChunkMetadata instance
        """
        # LangChain stores headers as {"h1": "Title", "h2": "Subtitle", ...}
        h1 = langchain_metadata.get("h1")
        h2 = langchain_metadata.get("h2")
        h3 = langchain_metadata.get("h3")
        h4 = langchain_metadata.get("h4")
        h5 = langchain_metadata.get("h5")
        h6 = langchain_metadata.get("h6")

        # Estimate tokens
        token_count = self.estimate_tokens(content)

        return ChunkMetadata(
            h1=h1,
            h2=h2,
            h3=h3,
            h4=h4,
            h5=h5,
            h6=h6,
            original_position=position,
            token_count=token_count,
        )

    def _generate_chunk_id(self, content: str, position: int) -> str:
        """Generate unique chunk ID from content and position.

        Uses SHA256 hash of content + position for deterministic IDs.

        Args:
            content: Chunk content
            position: Position in document

        Returns:
            Hex string chunk ID (8 characters)
        """
        # Create deterministic ID from content + position
        identifier = f"{content}{position}".encode()
        hash_digest = hashlib.sha256(identifier).hexdigest()

        # Use first 8 characters of hash
        return hash_digest[:8]

    def split(self, markdown: str) -> list[Chunk]:
        """Split markdown document into semantic chunks.

        Args:
            markdown: Markdown document to split

        Returns:
            List of Chunk objects with metadata

        Raises:
            ValueError: If markdown is empty or splitting fails
        """
        if not markdown.strip():
            raise ValueError("Cannot split empty markdown")

        try:
            # Use LangChain splitter
            langchain_chunks = self._splitter.split_text(markdown)

            if not langchain_chunks:
                logger.warning("LangChain splitter returned no chunks")
                # Return single chunk for entire document
                metadata = ChunkMetadata(
                    original_position=0,
                    token_count=self.estimate_tokens(markdown)
                )
                chunk_id = self._generate_chunk_id(markdown, 0)
                return [Chunk(
                    chunk_id=chunk_id,
                    content=markdown,
                    metadata=metadata,
                )]

            chunks: list[Chunk] = []

            for position, lc_chunk in enumerate(langchain_chunks):
                # Extract content and metadata
                content = lc_chunk.page_content

                # Skip empty chunks
                if not content.strip():
                    continue

                # Extract metadata
                metadata = self._extract_metadata(
                    lc_chunk.metadata,
                    position,
                    content
                )

                # Generate chunk ID
                chunk_id = self._generate_chunk_id(content, position)

                # Create chunk
                chunk = Chunk(
                    chunk_id=chunk_id,
                    content=content,
                    metadata=metadata,
                )

                # Check if chunk exceeds token limit and try semantic splitting
                if chunk.metadata.token_count > self.max_tokens_per_chunk:
                    sub_chunks = self._split_oversized_chunk(chunk)
                    chunks.extend(sub_chunks)
                else:
                    chunks.append(chunk)

            if not chunks:
                raise ValueError("No valid chunks created after splitting")

            return chunks

        except Exception as e:
            # Log and re-raise with context
            logger.error(f"Failed to split markdown: {e}")
            raise

    def split_with_metadata(self, markdown: str) -> tuple[list[Chunk], dict[str, Any]]:
        """Split markdown and return both chunks and splitting metadata.

        Args:
            markdown: Markdown document to split

        Returns:
            Tuple of (chunks, metadata_dict) where metadata_dict contains:
            - total_chunks: Number of chunks created
            - total_tokens: Sum of all token counts
            - max_chunk_tokens: Maximum tokens in any chunk
            - headers_used: Set of header levels found

        Examples:
            >>> splitter = MarkdownSplitter()
            >>> markdown = "# Title\\n\\n Content"
            >>> chunks, meta = splitter.split_with_metadata(markdown)
            >>> meta['total_chunks']
            1
        """
        chunks = self.split(markdown)

        # Collect statistics
        total_tokens = sum(c.metadata.token_count for c in chunks)
        max_chunk_tokens = max(c.metadata.token_count for c in chunks) if chunks else 0

        # Determine which header levels were used
        headers_used = set()
        for chunk in chunks:
            if chunk.metadata.h1:
                headers_used.add("h1")
            if chunk.metadata.h2:
                headers_used.add("h2")
            if chunk.metadata.h3:
                headers_used.add("h3")
            if chunk.metadata.h4:
                headers_used.add("h4")
            if chunk.metadata.h5:
                headers_used.add("h5")
            if chunk.metadata.h6:
                headers_used.add("h6")

        metadata = {
            "total_chunks": len(chunks),
            "total_tokens": total_tokens,
            "max_chunk_tokens": max_chunk_tokens,
            "headers_used": sorted(headers_used),
        }

        return chunks, metadata

    def _parse_list_items(self, content: str) -> list[str]:
        """Parse content into list items, preserving indented sub-items.

        Args:
            content: Markdown content with list items

        Returns:
            List of complete list items (each may contain multiple lines)

        Examples:
            >>> splitter = MarkdownSplitter()
            >>> content = "- Item 1\\n  - Sub A\\n- Item 2"
            >>> items = splitter._parse_list_items(content)
            >>> len(items)
            2
        """
        lines = content.split('\n')
        items = []
        current_item = []

        for line in lines:
            # Check if line starts a new list item
            # Patterns: '- ', '* ', '1. ', '2. ', etc.
            is_list_start = (
                re.match(r'^(\s*)[-*]\s+', line) or  # Unordered list
                re.match(r'^(\s*)\d+\.\s+', line)     # Ordered list
            )

            if is_list_start:
                # Save previous item if exists
                if current_item:
                    items.append('\n'.join(current_item))
                # Start new item
                current_item = [line]
            elif current_item:
                # Continue current item (indented or blank line)
                current_item.append(line)
            # else: skip lines before first list item

        # Add last item
        if current_item:
            items.append('\n'.join(current_item))

        return items

    def _group_items_by_tokens(
        self,
        items: list[str],
        max_tokens: int
    ) -> list[list[str]]:
        """Group items into chunks that fit within token limit.

        Args:
            items: List of content items (e.g., list items, paragraphs)
            max_tokens: Maximum tokens per group

        Returns:
            List of groups, where each group is a list of items

        Examples:
            >>> splitter = MarkdownSplitter()
            >>> items = ["Short item", "Another short", "Yet another"]
            >>> groups = splitter._group_items_by_tokens(items, 1000)
            >>> len(groups)
            1
        """
        if not items:
            return []

        groups = []
        current_group = []
        current_tokens = 0

        for item in items:
            item_tokens = self.estimate_tokens(item)

            # If single item exceeds limit, keep it as separate group
            if item_tokens > max_tokens:
                # Save current group if exists
                if current_group:
                    groups.append(current_group)
                    current_group = []
                    current_tokens = 0

                # Single oversized item becomes its own group
                groups.append([item])
                logger.warning(
                    f"Single list item exceeds token limit "
                    f"({item_tokens} > {max_tokens}). "
                    f"Keeping as-is to preserve semantic boundary."
                )
                continue

            # Check if adding this item would exceed limit
            if current_tokens + item_tokens > max_tokens:
                # Save current group and start new one
                groups.append(current_group)
                current_group = [item]
                current_tokens = item_tokens
            else:
                # Add to current group
                current_group.append(item)
                current_tokens += item_tokens

        # Add last group
        if current_group:
            groups.append(current_group)

        return groups

    def _split_oversized_by_list_items(
        self,
        chunk: Chunk
    ) -> list[Chunk]:
        """Split oversized chunk by list item boundaries.

        Args:
            chunk: Chunk that exceeds token limit

        Returns:
            List of smaller chunks split at list item boundaries

        Examples:
            >>> splitter = MarkdownSplitter()
            >>> # Assume chunk has 2000 tokens with many list items
            >>> sub_chunks = splitter._split_oversized_by_list_items(chunk)
            >>> all(c.metadata.token_count <= 1000 for c in sub_chunks)
            True
        """
        # Parse list items
        items = self._parse_list_items(chunk.content)

        if len(items) < 2:
            # Cannot split further by list items
            logger.warning(
                f"Chunk {chunk.chunk_id} has < 2 list items. "
                f"Cannot split further while preserving semantic boundaries."
            )
            return [chunk]

        # Group items by token limit
        groups = self._group_items_by_tokens(items, self.max_tokens_per_chunk)

        if len(groups) == 1:
            # All items fit in one group (shouldn't happen for oversized chunks)
            return [chunk]

        # Create sub-chunks
        sub_chunks = []
        for i, group in enumerate(groups):
            sub_content = '\n'.join(group)
            sub_tokens = self.estimate_tokens(sub_content)

            # Copy metadata from parent chunk
            sub_metadata = ChunkMetadata(
                h1=chunk.metadata.h1,
                h2=chunk.metadata.h2,
                h3=chunk.metadata.h3,
                h4=chunk.metadata.h4,
                h5=chunk.metadata.h5,
                h6=chunk.metadata.h6,
                original_position=chunk.metadata.original_position,
                token_count=sub_tokens,
            )

            # Generate new chunk ID
            sub_chunk_id = f"{chunk.chunk_id}-{i}"

            sub_chunk = Chunk(
                chunk_id=sub_chunk_id,
                content=sub_content,
                metadata=sub_metadata,
            )

            sub_chunks.append(sub_chunk)

        logger.info(
            f"Split chunk {chunk.chunk_id} ({chunk.metadata.token_count} tokens) "
            f"into {len(sub_chunks)} sub-chunks by list items"
        )

        return sub_chunks

    def _split_oversized_by_paragraphs(
        self,
        chunk: Chunk
    ) -> list[Chunk]:
        """Split oversized chunk by paragraph boundaries.

        Args:
            chunk: Chunk that exceeds token limit

        Returns:
            List of smaller chunks split at paragraph boundaries
        """
        # Split by double newlines (paragraph separator)
        paragraphs = [p for p in chunk.content.split('\n\n') if p.strip()]

        if len(paragraphs) < 2:
            logger.warning(
                f"Chunk {chunk.chunk_id} has < 2 paragraphs. "
                f"Cannot split further while preserving semantic boundaries."
            )
            return [chunk]

        # Group paragraphs by token limit
        groups = self._group_items_by_tokens(paragraphs, self.max_tokens_per_chunk)

        if len(groups) == 1:
            return [chunk]

        # Create sub-chunks
        sub_chunks = []
        for i, group in enumerate(groups):
            sub_content = '\n\n'.join(group)
            sub_tokens = self.estimate_tokens(sub_content)

            sub_metadata = ChunkMetadata(
                h1=chunk.metadata.h1,
                h2=chunk.metadata.h2,
                h3=chunk.metadata.h3,
                h4=chunk.metadata.h4,
                h5=chunk.metadata.h5,
                h6=chunk.metadata.h6,
                original_position=chunk.metadata.original_position,
                token_count=sub_tokens,
            )

            sub_chunk_id = f"{chunk.chunk_id}-{i}"

            sub_chunk = Chunk(
                chunk_id=sub_chunk_id,
                content=sub_content,
                metadata=sub_metadata,
            )

            sub_chunks.append(sub_chunk)

        logger.info(
            f"Split chunk {chunk.chunk_id} ({chunk.metadata.token_count} tokens) "
            f"into {len(sub_chunks)} sub-chunks by paragraphs"
        )

        return sub_chunks

    def _split_oversized_chunk(self, chunk: Chunk) -> list[Chunk]:
        """Split oversized chunk using semantic boundaries.

        Tries multiple strategies in order:
        1. Split by list items (if many list items present)
        2. Split by paragraphs (if many paragraphs present)
        3. Keep as-is with warning (if no semantic boundaries found)

        Args:
            chunk: Chunk that exceeds token limit

        Returns:
            List of chunks (original if cannot split, or multiple smaller chunks)
        """
        # Try list item splitting first
        items = self._parse_list_items(chunk.content)
        if len(items) >= 5:  # Threshold: at least 5 list items
            return self._split_oversized_by_list_items(chunk)

        # Try paragraph splitting
        paragraphs = [p for p in chunk.content.split('\n\n') if p.strip()]
        if len(paragraphs) >= 3:  # Threshold: at least 3 paragraphs
            return self._split_oversized_by_paragraphs(chunk)

        # No semantic boundaries found - keep as-is
        logger.warning(
            f"Chunk {chunk.chunk_id} exceeds token limit "
            f"({chunk.metadata.token_count} > {self.max_tokens_per_chunk}) "
            f"but no semantic boundaries found for splitting. "
            f"Keeping as-is to preserve semantic integrity."
        )
        return [chunk]
