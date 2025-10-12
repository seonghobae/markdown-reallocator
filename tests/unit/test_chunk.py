"""Unit tests for Chunk and ChunkMetadata models."""

import numpy as np
import pytest

from markdown_reallocator.models import (
    Chunk,
    ChunkMetadata,
)


class TestChunkMetadata:
    """Tests for ChunkMetadata dataclass."""

    def test_default_initialization(self) -> None:
        """Test ChunkMetadata with default values."""
        meta = ChunkMetadata()
        assert meta.h1 is None
        assert meta.h2 is None
        assert meta.h3 is None
        assert meta.original_position == 0
        assert meta.token_count == 0

    def test_initialization_with_headers(self) -> None:
        """Test ChunkMetadata with header values."""
        meta = ChunkMetadata(h1="Introduction", h2="Setup", h3="Installation")
        assert meta.h1 == "Introduction"
        assert meta.h2 == "Setup"
        assert meta.h3 == "Installation"

    def test_initialization_with_position_and_tokens(self) -> None:
        """Test ChunkMetadata with position and token count."""
        meta = ChunkMetadata(original_position=5, token_count=150)
        assert meta.original_position == 5
        assert meta.token_count == 150

    def test_negative_position_raises_error(self) -> None:
        """Test that negative position raises ValueError."""
        with pytest.raises(ValueError, match="original_position must be >= 0"):
            ChunkMetadata(original_position=-1)

    def test_negative_token_count_raises_error(self) -> None:
        """Test that negative token count raises ValueError."""
        with pytest.raises(ValueError, match="token_count must be >= 0"):
            ChunkMetadata(token_count=-1)

    def test_header_path_all_headers(self) -> None:
        """Test header_path with all headers present."""
        meta = ChunkMetadata(h1="Chapter 1", h2="Section A", h3="Subsection I")
        assert meta.header_path() == "Chapter 1 > Section A > Subsection I"

    def test_header_path_partial_headers(self) -> None:
        """Test header_path with only some headers present."""
        meta = ChunkMetadata(h1="Introduction", h2="Setup")
        assert meta.header_path() == "Introduction > Setup"

    def test_header_path_single_header(self) -> None:
        """Test header_path with only h1."""
        meta = ChunkMetadata(h1="Title")
        assert meta.header_path() == "Title"

    def test_header_path_no_headers(self) -> None:
        """Test header_path with no headers returns empty string."""
        meta = ChunkMetadata()
        assert meta.header_path() == ""

    def test_header_path_skip_none_headers(self) -> None:
        """Test header_path skips None values in the middle."""
        meta = ChunkMetadata(h1="Chapter", h3="Detail")
        assert meta.header_path() == "Chapter > Detail"

    def test_to_dict(self) -> None:
        """Test serialization to dictionary."""
        meta = ChunkMetadata(
            h1="Intro", h2="Background", h3="Context", original_position=3, token_count=200
        )
        data = meta.to_dict()
        assert data == {
            "h1": "Intro",
            "h2": "Background",
            "h3": "Context",
            "h4": None,
            "h5": None,
            "h6": None,
            "original_position": 3,
            "token_count": 200,
        }

    def test_to_dict_with_none_headers(self) -> None:
        """Test serialization with None headers."""
        meta = ChunkMetadata(h1="Title", original_position=1, token_count=50)
        data = meta.to_dict()
        assert data["h1"] == "Title"
        assert data["h2"] is None
        assert data["h3"] is None

    def test_from_dict(self) -> None:
        """Test deserialization from dictionary."""
        data: dict[str, str | int | None] = {
            "h1": "Introduction",
            "h2": "Getting Started",
            "h3": "Installation",
            "original_position": 2,
            "token_count": 120,
        }
        meta = ChunkMetadata.from_dict(data)
        assert meta.h1 == "Introduction"
        assert meta.h2 == "Getting Started"
        assert meta.h3 == "Installation"
        assert meta.original_position == 2
        assert meta.token_count == 120

    def test_from_dict_with_missing_headers(self) -> None:
        """Test deserialization with missing header fields."""
        data: dict[str, str | int | None] = {"original_position": 1, "token_count": 50}
        meta = ChunkMetadata.from_dict(data)
        assert meta.h1 is None
        assert meta.h2 is None
        assert meta.h3 is None

    def test_from_dict_with_missing_position_defaults_to_zero(self) -> None:
        """Test deserialization with missing position defaults to 0."""
        data: dict[str, str | int | None] = {"h1": "Title"}
        meta = ChunkMetadata.from_dict(data)
        assert meta.original_position == 0
        assert meta.token_count == 0

    def test_roundtrip_serialization(self) -> None:
        """Test that to_dict -> from_dict preserves data."""
        original = ChunkMetadata(
            h1="Test", h2="Chapter", h3="Section", original_position=10, token_count=250
        )
        data = original.to_dict()
        restored = ChunkMetadata.from_dict(data)
        assert restored.h1 == original.h1
        assert restored.h2 == original.h2
        assert restored.h3 == original.h3
        assert restored.original_position == original.original_position
        assert restored.token_count == original.token_count


class TestChunk:
    """Tests for Chunk dataclass."""

    def test_initialization(self) -> None:
        """Test basic Chunk initialization."""
        meta = ChunkMetadata(h1="Introduction")
        chunk = Chunk(chunk_id="chunk-001", content="This is test content.", metadata=meta)
        assert chunk.chunk_id == "chunk-001"
        assert chunk.content == "This is test content."
        assert chunk.metadata.h1 == "Introduction"
        assert chunk.embedding is None

    def test_initialization_with_embedding(self) -> None:
        """Test Chunk initialization with embedding."""
        meta = ChunkMetadata()
        embedding = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        chunk = Chunk(chunk_id="chunk-001", content="Content", metadata=meta, embedding=embedding)
        assert chunk.embedding is not None
        assert np.array_equal(chunk.embedding, embedding)

    def test_empty_chunk_id_raises_error(self) -> None:
        """Test that empty chunk_id raises ValueError."""
        meta = ChunkMetadata()
        with pytest.raises(ValueError, match="chunk_id cannot be empty"):
            Chunk(chunk_id="", content="Content", metadata=meta)

    def test_empty_content_raises_error(self) -> None:
        """Test that empty content raises ValueError."""
        meta = ChunkMetadata()
        with pytest.raises(ValueError, match="content cannot be empty or whitespace-only"):
            Chunk(chunk_id="chunk-001", content="", metadata=meta)

    def test_whitespace_only_content_raises_error(self) -> None:
        """Test that whitespace-only content raises ValueError."""
        meta = ChunkMetadata()
        with pytest.raises(ValueError, match="content cannot be empty or whitespace-only"):
            Chunk(chunk_id="chunk-001", content="   \n\t  ", metadata=meta)

    def test_multi_dimensional_embedding_raises_error(self) -> None:
        """Test that multi-dimensional embedding raises ValueError."""
        meta = ChunkMetadata()
        embedding = np.array([[0.1, 0.2], [0.3, 0.4]], dtype=np.float32)
        with pytest.raises(ValueError, match="embedding must be 1-dimensional"):
            Chunk(chunk_id="chunk-001", content="Content", metadata=meta, embedding=embedding)

    def test_repr(self) -> None:
        """Test string representation of Chunk."""
        meta = ChunkMetadata(h1="Title", h2="Subtitle")
        chunk = Chunk(chunk_id="chunk-001", content="Short content", metadata=meta)
        repr_str = repr(chunk)
        assert "chunk-001" in repr_str
        assert "Short content" in repr_str
        assert "Title > Subtitle" in repr_str
        assert "embedding=None" in repr_str

    def test_repr_with_long_content(self) -> None:
        """Test repr truncates long content."""
        meta = ChunkMetadata()
        long_content = "A" * 100
        chunk = Chunk(chunk_id="chunk-001", content=long_content, metadata=meta)
        repr_str = repr(chunk)
        assert len(repr_str) < 200  # Should be truncated
        assert "..." in repr_str

    def test_repr_with_embedding(self) -> None:
        """Test repr shows embedding presence."""
        meta = ChunkMetadata()
        embedding = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        chunk = Chunk(chunk_id="chunk-001", content="Content", metadata=meta, embedding=embedding)
        repr_str = repr(chunk)
        assert "embedding=present" in repr_str

    def test_to_dict_without_embedding(self) -> None:
        """Test serialization without embedding."""
        meta = ChunkMetadata(h1="Title", original_position=1, token_count=50)
        chunk = Chunk(chunk_id="chunk-001", content="Test content", metadata=meta)
        data = chunk.to_dict()
        assert data["chunk_id"] == "chunk-001"
        assert data["content"] == "Test content"
        metadata_dict = data["metadata"]
        assert isinstance(metadata_dict, dict)
        assert metadata_dict["h1"] == "Title"
        assert "embedding" not in data

    def test_to_dict_with_embedding_excluded_by_default(self) -> None:
        """Test that embedding is excluded by default."""
        meta = ChunkMetadata()
        embedding = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        chunk = Chunk(chunk_id="chunk-001", content="Content", metadata=meta, embedding=embedding)
        data = chunk.to_dict()
        assert "embedding" not in data

    def test_to_dict_with_embedding_included(self) -> None:
        """Test serialization with embedding included."""
        meta = ChunkMetadata()
        embedding = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        chunk = Chunk(chunk_id="chunk-001", content="Content", metadata=meta, embedding=embedding)
        data = chunk.to_dict(include_embedding=True)
        assert "embedding" in data
        # Use allclose for float32 precision tolerance
        assert np.allclose(data["embedding"], [0.1, 0.2, 0.3], rtol=1e-5)  # type: ignore[arg-type]

    def test_from_dict(self) -> None:
        """Test deserialization from dictionary."""
        data: dict[str, object] = {
            "chunk_id": "chunk-002",
            "content": "Restored content",
            "metadata": {"h1": "Section", "original_position": 3, "token_count": 100},
        }
        chunk = Chunk.from_dict(data)
        assert chunk.chunk_id == "chunk-002"
        assert chunk.content == "Restored content"
        assert chunk.metadata.h1 == "Section"
        assert chunk.embedding is None

    def test_from_dict_with_embedding(self) -> None:
        """Test deserialization with embedding."""
        data: dict[str, object] = {
            "chunk_id": "chunk-003",
            "content": "Content with embedding",
            "metadata": {"h1": "Title", "original_position": 0, "token_count": 50},
            "embedding": [0.5, 0.6, 0.7],
        }
        chunk = Chunk.from_dict(data)
        assert chunk.embedding is not None
        assert np.array_equal(chunk.embedding, np.array([0.5, 0.6, 0.7], dtype=np.float32))

    def test_from_dict_with_invalid_metadata(self) -> None:
        """Test deserialization fails with invalid metadata."""
        data: dict[str, object] = {
            "chunk_id": "chunk-004",
            "content": "Content",
            "metadata": "not a dict",
        }
        with pytest.raises(ValueError, match="metadata must be a dict"):
            Chunk.from_dict(data)

    def test_roundtrip_serialization_without_embedding(self) -> None:
        """Test roundtrip serialization without embedding."""
        original_meta = ChunkMetadata(h1="Test", h2="Chapter", original_position=5, token_count=150)
        original = Chunk(chunk_id="chunk-005", content="Original content", metadata=original_meta)
        data = original.to_dict()
        restored = Chunk.from_dict(data)
        assert restored.chunk_id == original.chunk_id
        assert restored.content == original.content
        assert restored.metadata.h1 == original.metadata.h1
        assert restored.metadata.original_position == original.metadata.original_position
        assert restored.embedding is None

    def test_roundtrip_serialization_with_embedding(self) -> None:
        """Test roundtrip serialization with embedding."""
        original_meta = ChunkMetadata(h1="Test")
        embedding = np.array([0.1, 0.2, 0.3, 0.4], dtype=np.float32)
        original = Chunk(
            chunk_id="chunk-006", content="Content", metadata=original_meta, embedding=embedding
        )
        data = original.to_dict(include_embedding=True)
        restored = Chunk.from_dict(data)
        assert restored.chunk_id == original.chunk_id
        assert restored.embedding is not None
        assert original.embedding is not None
        assert np.array_equal(restored.embedding, original.embedding)

    def test_realistic_markdown_chunk(self) -> None:
        """Test with realistic markdown content."""
        meta = ChunkMetadata(
            h1="User Guide", h2="Installation", h3="Prerequisites", original_position=15, token_count=320
        )
        content = """
## Installation

### Prerequisites

Before installing, ensure you have:
- Python 3.10 or higher
- pip package manager
- Virtual environment support

Run the following command:
```bash
pip install markdown-reallocator
```
"""
        chunk = Chunk(chunk_id="doc-001-chunk-015", content=content.strip(), metadata=meta)
        assert chunk.chunk_id == "doc-001-chunk-015"
        assert "Python 3.10" in chunk.content
        assert chunk.metadata.h1 == "User Guide"
        assert chunk.metadata.header_path() == "User Guide > Installation > Prerequisites"

    def test_realistic_embedding_384_dimensions(self) -> None:
        """Test chunk with realistic embeddinggemma dimensions."""
        meta = ChunkMetadata(h1="Example")
        embedding = np.random.rand(384).astype(np.float32)  # embeddinggemma output
        chunk = Chunk(chunk_id="chunk-001", content="Example content", metadata=meta, embedding=embedding)
        assert chunk.embedding is not None
        assert chunk.embedding.shape == (384,)
        assert chunk.embedding.dtype == np.float32

    def test_edge_case_very_long_content(self) -> None:
        """Test chunk with very long content (edge case)."""
        meta = ChunkMetadata(token_count=5000)
        long_content = "Word " * 5000  # Very long content
        chunk = Chunk(chunk_id="chunk-large", content=long_content, metadata=meta)
        assert len(chunk.content) > 10000
        assert chunk.metadata.token_count == 5000

    def test_edge_case_unicode_content(self) -> None:
        """Test chunk with Unicode characters."""
        meta = ChunkMetadata(h1="한글 제목", h2="日本語")
        content = "이것은 한글 내용입니다. これは日本語です. This is English."
        chunk = Chunk(chunk_id="chunk-unicode", content=content, metadata=meta)
        assert "한글" in chunk.content
        assert chunk.metadata.h1 == "한글 제목"
        assert "한글 제목 > 日本語" in chunk.metadata.header_path()
