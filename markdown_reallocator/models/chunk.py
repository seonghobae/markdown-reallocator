"""Data models for markdown chunks and metadata."""

from dataclasses import dataclass

import numpy as np


@dataclass
class ChunkMetadata:
    """Metadata for a markdown chunk.

    Attributes:
        h1: Level 1 header (# Title) if present
        h2: Level 2 header (## Title) if present
        h3: Level 3 header (### Title) if present
        original_position: Position in original document (0-indexed)
        token_count: Estimated token count for this chunk
    """

    h1: str | None = None
    h2: str | None = None
    h3: str | None = None
    original_position: int = 0
    token_count: int = 0

    def __post_init__(self) -> None:
        """Validate metadata after initialization."""
        if self.original_position < 0:
            raise ValueError(f"original_position must be >= 0, got {self.original_position}")
        if self.token_count < 0:
            raise ValueError(f"token_count must be >= 0, got {self.token_count}")

    def header_path(self) -> str:
        """Return header hierarchy as string.

        Returns:
            Header path in format "H1 > H2 > H3", omitting None headers.

        Examples:
            >>> meta = ChunkMetadata(h1="Intro", h2="Setup")
            >>> meta.header_path()
            'Intro > Setup'
        """
        headers = [h for h in [self.h1, self.h2, self.h3] if h is not None]
        return " > ".join(headers) if headers else ""

    def to_dict(self) -> dict[str, str | int | None]:
        """Convert to dictionary for serialization."""
        return {
            "h1": self.h1,
            "h2": self.h2,
            "h3": self.h3,
            "original_position": self.original_position,
            "token_count": self.token_count,
        }

    @classmethod
    def from_dict(cls, data: dict[str, str | int | None]) -> "ChunkMetadata":
        """Create from dictionary."""
        # Extract values with proper type checking
        h1_val = data.get("h1")
        h2_val = data.get("h2")
        h3_val = data.get("h3")
        pos_val = data.get("original_position")
        tok_val = data.get("token_count")

        return cls(
            h1=h1_val if isinstance(h1_val, str) else None,
            h2=h2_val if isinstance(h2_val, str) else None,
            h3=h3_val if isinstance(h3_val, str) else None,
            original_position=int(pos_val) if pos_val is not None else 0,
            token_count=int(tok_val) if tok_val is not None else 0,
        )


@dataclass
class Chunk:
    """A semantic chunk of markdown content.

    Attributes:
        chunk_id: Unique identifier for this chunk
        content: Markdown content of the chunk
        metadata: Metadata about headers and position
        embedding: Optional embedding vector (lazy-loaded)
    """

    chunk_id: str
    content: str
    metadata: ChunkMetadata
    embedding: np.ndarray | None = None

    def __post_init__(self) -> None:
        """Validate chunk after initialization."""
        if not self.chunk_id:
            raise ValueError("chunk_id cannot be empty")
        if not self.content.strip():
            raise ValueError("content cannot be empty or whitespace-only")
        if self.embedding is not None and self.embedding.ndim != 1:
            raise ValueError(f"embedding must be 1-dimensional, got shape {self.embedding.shape}")

    def __repr__(self) -> str:
        """Return string representation."""
        content_preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        has_embedding = self.embedding is not None
        return (
            f"Chunk(id={self.chunk_id!r}, "
            f"content={content_preview!r}, "
            f"header={self.metadata.header_path()!r}, "
            f"embedding={'present' if has_embedding else 'None'})"
        )

    def to_dict(self, include_embedding: bool = False) -> dict[str, object]:
        """Convert to dictionary for serialization.

        Args:
            include_embedding: Whether to include embedding vector.
                If True, embedding is converted to list.

        Returns:
            Dictionary representation of the chunk.
        """
        data: dict[str, object] = {
            "chunk_id": self.chunk_id,
            "content": self.content,
            "metadata": self.metadata.to_dict(),
        }
        if include_embedding and self.embedding is not None:
            data["embedding"] = self.embedding.tolist()
        return data

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "Chunk":
        """Create chunk from dictionary.

        Args:
            data: Dictionary with chunk_id, content, metadata, and optional embedding.

        Returns:
            Chunk instance.
        """
        metadata_dict = data.get("metadata")
        if not isinstance(metadata_dict, dict):
            raise ValueError("metadata must be a dict")

        metadata = ChunkMetadata.from_dict(metadata_dict)

        embedding_data = data.get("embedding")
        embedding: np.ndarray | None = None
        if embedding_data is not None:
            embedding = np.array(embedding_data, dtype=np.float32)

        return cls(
            chunk_id=str(data["chunk_id"]),
            content=str(data["content"]),
            metadata=metadata,
            embedding=embedding,
        )
