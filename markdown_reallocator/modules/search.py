"""Module for semantic search over document chunks.

This module provides functionality to search for relevant chunks based on
natural language queries using embedding similarity.
"""

import json
import logging
from typing import Any

import numpy as np

from markdown_reallocator.core.embedder import Embedder
from markdown_reallocator.models.chunk import Chunk
from markdown_reallocator.utils.similarity import batch_cosine_similarity

logger = logging.getLogger(__name__)


class SearchModule:
    """Module for semantic search over document chunks.

    This module enables finding relevant chunks based on natural language
    queries by computing cosine similarity between query embeddings and
    chunk embeddings.

    Examples:
        >>> search = SearchModule()
        >>> chunks = [...]  # Chunks with embeddings
        >>> results = search.search("authentication methods", chunks, top_k=5)
        >>> for chunk, score in results:
        ...     print(f"Score: {score:.3f} - {chunk.content[:50]}")
    """

    def __init__(
        self,
        embedder: Embedder | None = None,
        top_k: int = 5,
        min_similarity: float = 0.5,
        output_format: str = "text",
    ):
        """Initialize search module with configuration.

        Args:
            embedder: Embedder instance for query embedding. If None, creates default.
            top_k: Default number of results to return (must be > 0)
            min_similarity: Minimum similarity threshold (0.0-1.0)
            output_format: Default output format ("text" or "json")

        Raises:
            ValueError: If top_k <= 0 or min_similarity not in [0.0, 1.0]
        """
        # Validate parameters
        if top_k <= 0:
            raise ValueError(f"top_k must be > 0, got {top_k}")

        if not 0.0 <= min_similarity <= 1.0:
            raise ValueError(
                f"min_similarity must be in [0.0, 1.0], got {min_similarity}"
            )

        if output_format not in ("text", "json"):
            raise ValueError(
                f"output_format must be 'text' or 'json', got '{output_format}'"
            )

        # Initialize embedder
        self.embedder = embedder if embedder is not None else Embedder()

        # Store configuration
        self.top_k = top_k
        self.min_similarity = min_similarity
        self.output_format = output_format

    def search(
        self,
        query: str,
        chunks: list[Chunk],
        top_k: int | None = None,
        min_similarity: float | None = None,
    ) -> list[tuple[Chunk, float]]:
        """Search for chunks similar to the query.

        Embeds the query using the same model as document chunks, then
        computes cosine similarity between query and all chunks. Returns
        top-k most similar chunks with scores.

        Args:
            query: Natural language search query
            chunks: List of chunks with embeddings to search
            top_k: Number of results to return (overrides default if provided)
            min_similarity: Minimum similarity threshold (overrides default)

        Returns:
            List of (chunk, similarity_score) tuples, sorted by score descending

        Raises:
            ValueError: If query is empty or chunks lack embeddings
        """
        # Validate query
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        # Validate chunks
        if not chunks:
            logger.warning("No chunks provided for search")
            return []

        # Check all chunks have embeddings
        for i, chunk in enumerate(chunks):
            if chunk.embedding is None:
                raise ValueError(
                    f"Chunk at index {i} (id={chunk.chunk_id}) has no embedding. "
                    "Run embedder first."
                )

        # Use provided parameters or defaults
        k = top_k if top_k is not None else self.top_k
        threshold = (
            min_similarity if min_similarity is not None else self.min_similarity
        )

        # Embed query
        logger.debug(f"Embedding query: '{query[:50]}...'")

        # Create temporary chunk for query to leverage embedder's caching
        from markdown_reallocator.models.chunk import ChunkMetadata
        query_chunk = Chunk(
            chunk_id="__query__",
            content=query,
            metadata=ChunkMetadata(original_position=0),
        )

        # Embed query (will use cache if query seen before)
        query_chunk = self.embedder.embed_chunk(query_chunk)

        if query_chunk.embedding is None:
            raise RuntimeError("Failed to embed query")

        query_embedding = query_chunk.embedding

        # Extract chunk embeddings into matrix
        chunk_embeddings = np.array([c.embedding for c in chunks])

        # Compute similarities between query and all chunks
        # query_embedding shape: (dim,)
        # chunk_embeddings shape: (n_chunks, dim)
        # Use batch_cosine_similarity for efficient computation
        # Result shape: (n_chunks,)
        similarities = batch_cosine_similarity(chunk_embeddings, query_embedding)

        logger.debug(
            f"Computed similarities for {len(chunks)} chunks: "
            f"min={similarities.min():.3f}, max={similarities.max():.3f}, "
            f"mean={similarities.mean():.3f}"
        )

        # Filter by threshold
        mask = similarities >= threshold
        filtered_indices = np.where(mask)[0]
        filtered_similarities = similarities[filtered_indices]

        logger.debug(
            f"Filtered to {len(filtered_indices)} chunks with similarity >= {threshold}"
        )

        if len(filtered_indices) == 0:
            logger.info(f"No chunks found with similarity >= {threshold}")
            return []

        # Sort by similarity (descending)
        sorted_order = np.argsort(filtered_similarities)[::-1]
        sorted_indices = filtered_indices[sorted_order]
        sorted_similarities = filtered_similarities[sorted_order]

        # Take top-k
        top_indices = sorted_indices[:k]
        top_similarities = sorted_similarities[:k]

        # Build results
        results = [
            (chunks[idx], float(sim))
            for idx, sim in zip(top_indices, top_similarities, strict=False)
        ]

        logger.info(
            f"Search complete: found {len(results)} results "
            f"(top similarity: {results[0][1]:.3f})"
        )

        return results

    def format_results(
        self,
        results: list[tuple[Chunk, float]],
        output_format: str | None = None,
        include_context: bool = False,
    ) -> str:
        """Format search results as text or JSON.

        Args:
            results: List of (chunk, score) tuples from search()
            output_format: Output format ("text" or "json"), uses default if None
            include_context: If True, include additional metadata context

        Returns:
            Formatted results as string

        Raises:
            ValueError: If output_format is invalid
        """
        # Use provided format or default
        fmt = output_format if output_format is not None else self.output_format

        if fmt not in ("text", "json"):
            raise ValueError(f"output_format must be 'text' or 'json', got '{fmt}'")

        # Handle empty results
        if not results:
            if fmt == "text":
                return "No results found.\n"
            else:
                return json.dumps({"results": [], "count": 0}, indent=2)

        # Format based on output type
        if fmt == "text":
            return self._format_text(results, include_context)
        else:
            return self._format_json(results, include_context)

    def _format_text(
        self, results: list[tuple[Chunk, float]], include_context: bool
    ) -> str:
        """Format results as human-readable text.

        Args:
            results: List of (chunk, score) tuples
            include_context: Whether to include metadata context

        Returns:
            Formatted text string
        """
        lines = [f"Found {len(results)} result(s):\n"]

        for i, (chunk, score) in enumerate(results, 1):
            # Header
            lines.append(f"[{i}] Similarity: {score:.3f}")

            # Metadata
            if include_context:
                metadata = chunk.metadata
                if metadata.h1:
                    lines.append(f"    H1: {metadata.h1}")
                if metadata.h2:
                    lines.append(f"    H2: {metadata.h2}")
                if metadata.h3:
                    lines.append(f"    H3: {metadata.h3}")
                lines.append(f"    Position: {metadata.original_position}")

            # Content preview (first 100 chars)
            content_preview = chunk.content[:100].replace("\n", " ")
            if len(chunk.content) > 100:
                content_preview += "..."
            lines.append(f"    Content: {content_preview}")

            lines.append("")  # Empty line between results

        return "\n".join(lines)

    def _format_json(
        self, results: list[tuple[Chunk, float]], include_context: bool
    ) -> str:
        """Format results as JSON.

        Args:
            results: List of (chunk, score) tuples
            include_context: Whether to include metadata context

        Returns:
            JSON string
        """
        output: dict[str, Any] = {
            "count": len(results),
            "results": [],
        }

        for chunk, score in results:
            result_dict: dict[str, Any] = {
                "chunk_id": chunk.chunk_id,
                "similarity": round(score, 4),
                "content": chunk.content,
            }

            if include_context:
                result_dict["metadata"] = {
                    "h1": chunk.metadata.h1,
                    "h2": chunk.metadata.h2,
                    "h3": chunk.metadata.h3,
                    "original_position": chunk.metadata.original_position,
                }

            output["results"].append(result_dict)

        return json.dumps(output, indent=2, ensure_ascii=False)
