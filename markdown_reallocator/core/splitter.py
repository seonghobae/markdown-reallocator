"""Markdown splitter using LangChain.

This module provides semantic markdown chunking that splits by headers
while preserving hierarchy metadata.
"""

import hashlib
import logging
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

        # Estimate tokens
        token_count = self.estimate_tokens(content)

        return ChunkMetadata(
            h1=h1,
            h2=h2,
            h3=h3,
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

                # Check token limit
                if metadata.token_count > self.max_tokens_per_chunk:
                    logger.warning(
                        f"Chunk at position {position} exceeds max tokens "
                        f"({metadata.token_count} > {self.max_tokens_per_chunk})"
                    )

                # Generate chunk ID
                chunk_id = self._generate_chunk_id(content, position)

                # Create chunk
                chunk = Chunk(
                    chunk_id=chunk_id,
                    content=content,
                    metadata=metadata,
                )

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

        metadata = {
            "total_chunks": len(chunks),
            "total_tokens": total_tokens,
            "max_chunk_tokens": max_chunk_tokens,
            "headers_used": sorted(headers_used),
        }

        return chunks, metadata
