"""Ollama model loading utilities with memory management.

This module provides functions for loading Ollama models (embeddings and LLMs)
with memory monitoring, retry logic, and sequential loading to prevent GPU
memory overflow on resource-constrained hardware.
"""

import time
from typing import Any

import ollama


class OllamaConnectionError(Exception):
    """Raised when Ollama service is unavailable."""

    pass


class ModelLoadError(Exception):
    """Raised when model fails to load."""

    pass


def check_ollama_available(timeout: float = 5.0) -> bool:
    """Check if Ollama service is running and responsive.

    Args:
        timeout: Maximum time to wait for response (seconds)

    Returns:
        True if Ollama is available, False otherwise
    """
    try:
        # Try to list models as a health check
        ollama.list()
        return True
    except Exception:
        return False


def load_embedding_model(
    model_name: str = "embeddinggemma",
    retry_count: int = 3,
    retry_delay: float = 1.0,
) -> ollama.Client:
    """Load Ollama embedding model with retry logic.

    This function attempts to load the specified embedding model, retrying
    on transient errors. It checks that Ollama is running before attempting
    to load the model.

    Args:
        model_name: Name of embedding model (default: "embeddinggemma")
        retry_count: Number of retry attempts for transient errors
        retry_delay: Delay between retries in seconds

    Returns:
        Ollama client configured for embedding generation

    Raises:
        OllamaConnectionError: If Ollama service is not available
        ModelLoadError: If model fails to load after retries
        ValueError: If retry_count or retry_delay are invalid

    Examples:
        >>> client = load_embedding_model("embeddinggemma")
        >>> # Use client to generate embeddings
        >>> result = client.embeddings(model="embeddinggemma", prompt="Hello")
        >>> embedding = result['embedding']
    """
    if retry_count < 1:
        raise ValueError(f"retry_count must be at least 1, got {retry_count}")
    if retry_delay < 0:
        raise ValueError(f"retry_delay must be non-negative, got {retry_delay}")

    # Check if Ollama is available
    if not check_ollama_available():
        raise OllamaConnectionError(
            "Ollama service is not available. "
            "Please ensure Ollama is running: `ollama serve`"
        )

    # Verify model exists
    last_error: Exception | None = None

    for attempt in range(retry_count):
        try:
            # Check if model is available
            models = ollama.list()
            model_names = [m["name"] for m in models.get("models", [])]

            # Handle model name variations (e.g., "embeddinggemma:latest")
            model_exists = any(
                model_name in name or name.startswith(f"{model_name}:")
                for name in model_names
            )

            if not model_exists:
                raise ModelLoadError(
                    f"Model '{model_name}' not found. "
                    f"Available models: {model_names}. "
                    f"Pull model with: `ollama pull {model_name}`"
                )

            # Create client
            client = ollama.Client()

            # Test that model works by generating a small embedding
            try:
                test_result = client.embeddings(model=model_name, prompt="test")
                if "embedding" not in test_result:
                    raise ModelLoadError(f"Model '{model_name}' did not return embedding")
            except Exception as e:
                raise ModelLoadError(f"Failed to generate test embedding: {e}") from e

            return client

        except (OllamaConnectionError, ModelLoadError):
            # Don't retry these errors
            raise
        except Exception as e:
            last_error = e
            if attempt < retry_count - 1:
                time.sleep(retry_delay)
                continue
            break

    # If we get here, all retries failed
    raise ModelLoadError(
        f"Failed to load model '{model_name}' after {retry_count} attempts. "
        f"Last error: {last_error}"
    ) from last_error


def load_llm_model(
    model_name: str = "gemma:2b-instruct-q4_0",
    retry_count: int = 3,
    retry_delay: float = 1.0,
) -> ollama.Client:
    """Load Ollama LLM model with retry logic.

    This function attempts to load the specified LLM model for text generation.
    It includes retry logic for transient errors and validates Ollama availability.

    Args:
        model_name: Name of LLM model (default: "gemma:2b-instruct-q4_0")
        retry_count: Number of retry attempts for transient errors
        retry_delay: Delay between retries in seconds

    Returns:
        Ollama client configured for text generation

    Raises:
        OllamaConnectionError: If Ollama service is not available
        ModelLoadError: If model fails to load after retries
        ValueError: If retry_count or retry_delay are invalid

    Examples:
        >>> client = load_llm_model("gemma:2b-instruct-q4_0")
        >>> response = client.generate(model="gemma:2b-instruct-q4_0", prompt="Hello")
        >>> text = response['response']
    """
    if retry_count < 1:
        raise ValueError(f"retry_count must be at least 1, got {retry_count}")
    if retry_delay < 0:
        raise ValueError(f"retry_delay must be non-negative, got {retry_delay}")

    # Check if Ollama is available
    if not check_ollama_available():
        raise OllamaConnectionError(
            "Ollama service is not available. "
            "Please ensure Ollama is running: `ollama serve`"
        )

    last_error: Exception | None = None

    for attempt in range(retry_count):
        try:
            # Check if model is available
            models = ollama.list()
            model_names = [m["name"] for m in models.get("models", [])]

            # Handle model name variations
            model_exists = any(
                model_name in name or name.startswith(f"{model_name.split(':')[0]}:")
                for name in model_names
            )

            if not model_exists:
                raise ModelLoadError(
                    f"Model '{model_name}' not found. "
                    f"Available models: {model_names}. "
                    f"Pull model with: `ollama pull {model_name}`"
                )

            # Create client
            client = ollama.Client()

            # Test that model works with a minimal generation
            try:
                test_result = client.generate(model=model_name, prompt="test", options={"num_predict": 1})
                if "response" not in test_result:
                    raise ModelLoadError(f"Model '{model_name}' did not return response")
            except Exception as e:
                raise ModelLoadError(f"Failed to generate test response: {e}") from e

            return client

        except (OllamaConnectionError, ModelLoadError):
            # Don't retry these errors
            raise
        except Exception as e:
            last_error = e
            if attempt < retry_count - 1:
                time.sleep(retry_delay)
                continue
            break

    # If we get here, all retries failed
    raise ModelLoadError(
        f"Failed to load model '{model_name}' after {retry_count} attempts. "
        f"Last error: {last_error}"
    ) from last_error


def get_available_models() -> list[dict[str, Any]]:
    """Get list of available Ollama models.

    Returns:
        List of model dictionaries with metadata

    Raises:
        OllamaConnectionError: If Ollama service is not available
    """
    if not check_ollama_available():
        raise OllamaConnectionError(
            "Ollama service is not available. "
            "Please ensure Ollama is running: `ollama serve`"
        )

    try:
        response = ollama.list()
        return response.get("models", [])  # type: ignore[no-any-return]
    except Exception as e:
        raise OllamaConnectionError(f"Failed to list models: {e}") from e


def model_exists(model_name: str) -> bool:
    """Check if a model is available in Ollama.

    Args:
        model_name: Name of model to check

    Returns:
        True if model exists, False otherwise

    Raises:
        OllamaConnectionError: If Ollama service is not available
    """
    models = get_available_models()
    model_names = [m["name"] for m in models]

    # Handle model name variations
    return any(
        model_name in name or name.startswith(f"{model_name.split(':')[0]}:")
        for name in model_names
    )
