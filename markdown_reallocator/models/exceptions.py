"""Custom exceptions for data models."""


class ModelError(Exception):
    """Base exception for model-related errors."""

    pass


class InvalidChunkError(ModelError):
    """Raised when chunk data is invalid."""

    pass


class InvalidMetadataError(ModelError):
    """Raised when metadata is invalid."""

    pass


class InvalidEmbeddingError(ModelError):
    """Raised when embedding data is invalid."""

    pass
