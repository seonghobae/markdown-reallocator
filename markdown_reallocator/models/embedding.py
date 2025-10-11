"""Data model for embeddings."""

import hashlib
from dataclasses import dataclass

import numpy as np


@dataclass
class Embedding:
    """An embedding vector with metadata.

    Attributes:
        vector: The embedding vector (typically 384-dim for embeddinggemma)
        text_hash: SHA256 hash of the text that was embedded
        model_name: Name of the model used (e.g., "embeddinggemma")
    """

    vector: np.ndarray
    text_hash: str
    model_name: str

    def __post_init__(self) -> None:
        """Validate embedding after initialization."""
        if self.vector.ndim != 1:
            raise ValueError(f"vector must be 1-dimensional, got shape {self.vector.shape}")

        if len(self.vector) == 0:
            raise ValueError("vector cannot be empty")

        if not self.text_hash:
            raise ValueError("text_hash cannot be empty")

        if not self.model_name:
            raise ValueError("model_name cannot be empty")

        # Ensure vector is float32 for efficiency
        if self.vector.dtype != np.float32:
            object.__setattr__(self, "vector", self.vector.astype(np.float32))

    @property
    def dimension(self) -> int:
        """Return the dimensionality of the embedding."""
        return len(self.vector)

    def normalize(self) -> "Embedding":
        """Return a new Embedding with normalized vector.

        Normalization preserves direction but sets magnitude to 1.
        Useful for cosine similarity calculations.

        Returns:
            New Embedding instance with normalized vector.
        """
        norm = np.linalg.norm(self.vector)
        if norm == 0:
            raise ValueError("Cannot normalize zero vector")

        normalized_vector = self.vector / norm
        return Embedding(
            vector=normalized_vector,
            text_hash=self.text_hash,
            model_name=self.model_name,
        )

    def to_bytes(self) -> bytes:
        """Serialize vector to bytes for storage.

        Returns:
            Binary representation of the vector.
        """
        return self.vector.tobytes()

    @classmethod
    def from_bytes(
        cls,
        data: bytes,
        text_hash: str,
        model_name: str,
        dtype: type[np.floating] = np.float32,
    ) -> "Embedding":
        """Deserialize vector from bytes.

        Args:
            data: Binary representation of the vector
            text_hash: SHA256 hash of the embedded text
            model_name: Name of the embedding model
            dtype: Data type of the vector (default: float32)

        Returns:
            Embedding instance.
        """
        vector = np.frombuffer(data, dtype=dtype)
        return cls(vector=vector, text_hash=text_hash, model_name=model_name)

    def __eq__(self, other: object) -> bool:
        """Compare embeddings by text_hash and model_name.

        Two embeddings are equal if they represent the same text
        from the same model, regardless of vector values.

        Args:
            other: Another Embedding instance.

        Returns:
            True if text_hash and model_name match.
        """
        if not isinstance(other, Embedding):
            return NotImplemented
        return self.text_hash == other.text_hash and self.model_name == other.model_name

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"Embedding(dim={self.dimension}, "
            f"model={self.model_name!r}, "
            f"hash={self.text_hash[:8]}...)"
        )

    @staticmethod
    def compute_text_hash(text: str) -> str:
        """Compute SHA256 hash of text for cache keys.

        Args:
            text: The text to hash.

        Returns:
            Hexadecimal SHA256 hash string.
        """
        return hashlib.sha256(text.encode("utf-8")).hexdigest()
