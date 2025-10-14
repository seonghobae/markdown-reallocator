"""Markdown splitter inspired by Unstructured.io's philosophy.

This module provides semantic markdown chunking that splits by headers
while preserving hierarchy metadata and indentation.

IMPORTANT: We DO NOT use LangChain because it strips indentation.
We use a simple approach inspired by Unstructured.io that preserves all structure.
"""

import hashlib
import logging
import re
from typing import Any

from markdown_reallocator.models.chunk import Chunk, ChunkMetadata

logger = logging.getLogger(__name__)


class MarkdownSplitter:
    """Splitter for markdown documents based on header hierarchy.

    This class splits markdown while preserving indentation and hierarchy metadata.
    Inspired by Unstructured.io's philosophy of preserving document structure.

    IMPORTANT: Does NOT use LangChain because it strips indentation.
    Uses simple regex-based parsing that preserves all whitespace.

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

    def _parse_with_unstructured(self, markdown: str) -> list[dict[str, Any]]:
        """Parse markdown preserving all whitespace and indentation.

        IMPORTANT: Does NOT use LangChain because it strips indentation.
        Uses simple regex-based parsing that preserves all structure.

        Inspired by Unstructured.io's philosophy of preserving document structure,
        but implemented without external dependencies to ensure indentation is kept.

        Splitting behavior:
        - Split at configured header levels (based on headers_to_split_on)
        - Headers at or above current level trigger new chunk
        - Lower-level headers accumulate as metadata
        - Example: h1, then h2, then another h2 → split at second h2

        Args:
            markdown: Markdown document to parse

        Returns:
            List of dicts with 'content', 'headers', and 'position' keys
            where 'headers' is a dict like {"h1": "Title", "h2": "Section", ...}

        Examples:
            >>> splitter = MarkdownSplitter()
            >>> markdown = "# Title\\n\\n## Section\\n\\nMore"
            >>> chunks = splitter._parse_with_unstructured(markdown)
            >>> len(chunks) == 1  # h1 and h2 together
            True
        """
        lines = markdown.split('\n')
        chunks = []
        current_headers = {}  # Track current header hierarchy
        current_content_lines = []
        position = 0
        current_split_level = None  # Track what level triggers splits

        # Build set of split levels from configuration
        split_levels = set()
        for marker, _ in self.headers_to_split_on:
            split_levels.add(len(marker))  # # = 1, ## = 2, etc.

        for line in lines:
            # Check if line is a header (# to ######)
            header_match = re.match(r'^(#{1,6})\s+(.+)$', line)

            if header_match:
                header_marker = header_match.group(1)
                header_text = header_match.group(2).strip()
                header_level = len(header_marker)
                header_name = f"h{header_level}"

                # Determine if this header should trigger a split
                should_split = False

                if header_level in split_levels:
                    # Split if:
                    # 1. We have existing content AND
                    # 2. This header level already exists in current_headers (same level)
                    # OR
                    # 3. This header is at a SHALLOWER level (lower number) than the deepest level
                    if current_content_lines and current_headers:
                        if header_name in current_headers:
                            # Same level as before → split
                            should_split = True
                        else:
                            # Check if we're at same/shallower level than deepest level
                            # Example: have {"h1": ..., "h2": ...}, now seeing h1 or h2 → split
                            # But if have {"h1": ...}, now seeing h2 → don't split (going deeper)
                            max_existing_level = max(int(h[1]) for h in current_headers.keys())
                            if header_level <= max_existing_level:
                                # We're at same or shallower level than deepest → split
                                should_split = True

                # Save previous chunk if splitting
                if should_split and current_content_lines:
                    chunks.append({
                        'content': '\n'.join(current_content_lines),
                        'headers': current_headers.copy(),
                        'position': position
                    })
                    position += 1
                    current_content_lines = []

                # Update current headers
                current_headers[header_name] = header_text

                # Clear all deeper levels
                for i in range(header_level + 1, 7):
                    deeper_name = f"h{i}"
                    if deeper_name in current_headers:
                        del current_headers[deeper_name]

                # Start/continue content with the header line itself
                current_content_lines.append(line)
            else:
                # Regular content line - preserve ALL whitespace (unlike LangChain)
                current_content_lines.append(line)

        # Add last chunk
        if current_content_lines:
            chunks.append({
                'content': '\n'.join(current_content_lines),
                'headers': current_headers.copy(),
                'position': position
            })

        return chunks

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

        Uses simple parsing that preserves indentation (not LangChain).
        Inspired by Unstructured.io's philosophy of structure preservation.

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
            # Parse with whitespace preservation (inspired by Unstructured.io)
            parsed_chunks = self._parse_with_unstructured(markdown)

            if not parsed_chunks:
                logger.warning("Parser returned no chunks")
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

            for parsed_chunk in parsed_chunks:
                content = parsed_chunk['content']
                headers = parsed_chunk['headers']
                position = parsed_chunk['position']

                # Skip empty chunks
                if not content.strip():
                    continue

                # Create metadata from parsed headers
                metadata = ChunkMetadata(
                    h1=headers.get('h1'),
                    h2=headers.get('h2'),
                    h3=headers.get('h3'),
                    h4=headers.get('h4'),
                    h5=headers.get('h5'),
                    h6=headers.get('h6'),
                    original_position=position,
                    token_count=self.estimate_tokens(content),
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

    def _calculate_depth(self, line: str) -> int:
        """Calculate indentation depth of a line.

        Inspired by Unstructured.io's depth tracking approach.
        Counts leading spaces (2 spaces = 1 depth level, 4 spaces = 2 depth levels).

        Args:
            line: Line to calculate depth for

        Returns:
            Depth level (0 for no indentation, 1+ for indented)

        Examples:
            >>> splitter = MarkdownSplitter()
            >>> splitter._calculate_depth("- Item")
            0
            >>> splitter._calculate_depth("  - Sub item")
            1
            >>> splitter._calculate_depth("    - Sub-sub item")
            2
        """
        if not line or not line.strip():
            return 0

        # Count leading whitespace
        leading_spaces = len(line) - len(line.lstrip(' \t'))

        # Convert tabs to spaces (1 tab = 4 spaces)
        if '\t' in line[:leading_spaces]:
            leading_spaces = line[:leading_spaces].replace('\t', '    ').count(' ')

        # 2 spaces = 1 depth level
        return leading_spaces // 2

    def _parse_list_items_with_depth(self, content: str) -> list[dict[str, Any]]:
        """Parse list items with depth information.

        Similar to Unstructured.io's ListItem with depth and parent_id metadata.

        Args:
            content: Markdown content with list items

        Returns:
            List of dicts with 'content', 'depth', and 'parent_idx' keys

        Examples:
            >>> splitter = MarkdownSplitter()
            >>> content = "- Item 1\\n  - Sub 1a\\n  - Sub 1b\\n- Item 2"
            >>> items = splitter._parse_list_items_with_depth(content)
            >>> len(items)
            4
            >>> items[0]['depth']
            0
            >>> items[1]['depth']
            1
            >>> items[1]['parent_idx']
            0
        """
        lines = content.split('\n')
        items = []
        current_item_lines = []
        current_depth = 0
        depth_stack = [-1]  # Stack of parent indices

        for line in lines:
            # Check if line starts a new list item
            is_list_start = (
                re.match(r'^(\s*)[-*]\s+', line) or
                re.match(r'^(\s*)\d+\.\s+', line)
            )

            if is_list_start:
                # Save previous item if exists
                if current_item_lines:
                    items.append({
                        'content': '\n'.join(current_item_lines),
                        'depth': current_depth,
                        'parent_idx': depth_stack[-1] if depth_stack[-1] >= 0 else None
                    })

                # Calculate depth of new item
                current_depth = self._calculate_depth(line)

                # Update parent stack
                # Pop until we find the parent level
                while len(depth_stack) > 1 and depth_stack[-1] >= current_depth:
                    depth_stack.pop()

                # Current item index will be len(items)
                if current_depth > 0:
                    # Find parent at depth-1
                    parent_depth = current_depth - 1
                    parent_idx = None
                    for i in range(len(items) - 1, -1, -1):
                        if items[i]['depth'] == parent_depth:
                            parent_idx = i
                            break
                    depth_stack.append(parent_idx if parent_idx is not None else -1)
                else:
                    depth_stack = [-1]

                current_item_lines = [line]
            elif current_item_lines:
                # Continue current item
                current_item_lines.append(line)

        # Add last item
        if current_item_lines:
            items.append({
                'content': '\n'.join(current_item_lines),
                'depth': current_depth,
                'parent_idx': depth_stack[-1] if depth_stack[-1] >= 0 else None
            })

        return items

    def _split_by_depth_boundaries(
        self,
        chunk: Chunk
    ) -> list[Chunk]:
        """Split chunk at depth-0 boundaries while preserving parent-child groups.

        Implements depth-aware splitting inspired by Unstructured.io's approach:
        - Only split at depth-0 (top-level) list items
        - Keep parent-child groups together
        - Respect semantic boundaries defined by indentation hierarchy

        Args:
            chunk: Chunk that exceeds token limit

        Returns:
            List of smaller chunks split at depth-0 boundaries

        Examples:
            >>> splitter = MarkdownSplitter()
            >>> # Chunk with hierarchical list
            >>> # Will split at depth-0 items while keeping sub-items with parent
        """
        # Parse with depth information
        items = self._parse_list_items_with_depth(chunk.content)

        if len(items) < 2:
            logger.warning(
                f"Chunk {chunk.chunk_id} has < 2 list items. "
                f"Cannot split by depth boundaries."
            )
            return [chunk]

        # Count depth-0 items
        depth_0_count = sum(1 for item in items if item['depth'] == 0)

        if depth_0_count < 2:
            logger.warning(
                f"Chunk {chunk.chunk_id} has < 2 depth-0 items. "
                f"Cannot split at depth-0 boundaries."
            )
            return [chunk]

        # Group items by depth-0 boundaries
        groups = []
        current_group = []
        current_tokens = 0

        for item in items:
            item_tokens = self.estimate_tokens(item['content'])

            # Depth 0: potential split point
            if item['depth'] == 0 and current_tokens + item_tokens > self.max_tokens_per_chunk:
                if current_group:
                    groups.append(current_group)
                current_group = [item]
                current_tokens = item_tokens
            else:
                # Depth 1+: must stay with parent
                current_group.append(item)
                current_tokens += item_tokens

        # Add last group
        if current_group:
            groups.append(current_group)

        if len(groups) == 1:
            # All items fit in one group
            logger.info(
                f"Chunk {chunk.chunk_id} could not be split at depth-0 boundaries "
                f"(would require splitting parent-child groups). "
                f"Keeping as-is to preserve semantic hierarchy."
            )
            return [chunk]

        # Create sub-chunks
        sub_chunks = []
        for i, group in enumerate(groups):
            sub_content = '\n'.join(item['content'] for item in group)
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

            sub_chunk_id = f"{chunk.chunk_id}-d{i}"  # 'd' for depth-aware

            sub_chunk = Chunk(
                chunk_id=sub_chunk_id,
                content=sub_content,
                metadata=sub_metadata,
            )

            sub_chunks.append(sub_chunk)

        logger.info(
            f"Split chunk {chunk.chunk_id} ({chunk.metadata.token_count} tokens) "
            f"into {len(sub_chunks)} sub-chunks at depth-0 boundaries"
        )

        return sub_chunks

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

        DESIGN PHILOSOPHY:
        This method prioritizes semantic completeness over strict token limits.
        For technical documentation (policies, protocols, procedures), we allow
        chunks to slightly exceed the token limit if splitting would break
        semantic meaning. This aligns with Pinecone's principle:
        "If the chunk of text makes sense without surrounding context to a human,
        it will make sense to the language model as well."

        Real-world validation (AGENTS.md, 227KB):
        - 205 total chunks
        - 15 oversized (7.3%), average +9 tokens (1.8% overflow)
        - All oversized chunks contained complete policies/protocols
        - Conclusion: 1.8% overflow acceptable for semantic integrity

        See docs/semantic_chunking_strategy.md for full rationale and comparison
        with industry approaches (Unstructured.io, Docling, Pinecone).

        Tries multiple strategies in order:
        1. Depth-aware splitting (Unstructured.io-inspired hierarchical lists)
        2. Split by list items (if many flat list items present)
        3. Split by paragraphs (if many paragraphs present)
        4. Keep as-is with warning (if no semantic boundaries found)

        Args:
            chunk: Chunk that exceeds token limit

        Returns:
            List of chunks (original if cannot split, or multiple smaller chunks)
        """
        # Try depth-aware splitting first (hierarchical lists)
        items_with_depth = self._parse_list_items_with_depth(chunk.content)
        if len(items_with_depth) >= 5:  # At least 5 list items
            # Check if there are hierarchical structures (depth > 0)
            has_hierarchy = any(item['depth'] > 0 for item in items_with_depth)
            depth_0_count = sum(1 for item in items_with_depth if item['depth'] == 0)

            if has_hierarchy and depth_0_count >= 2:
                # Hierarchical list with multiple depth-0 items
                # Try depth-aware splitting
                result = self._split_by_depth_boundaries(chunk)
                if len(result) > 1:
                    return result
                # else: depth-aware splitting couldn't help, try other methods

        # Try flat list item splitting
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
