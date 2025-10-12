"""Unit tests for Ollama model loading utilities.

Tests cover:
- Ollama service availability checking
- Embedding model loading with retry logic
- LLM model loading with retry logic
- Model existence checking
- Error handling for connection failures and missing models
- Retry behavior for transient errors

All external calls (ollama.list, ollama.Client) are mocked.
"""

from unittest.mock import Mock, patch

import pytest

from markdown_reallocator.utils.model_loader import (
    ModelLoadError,
    OllamaConnectionError,
    check_ollama_available,
    get_available_models,
    load_embedding_model,
    load_llm_model,
    model_exists,
)


class TestCheckOllamaAvailable:
    """Tests for Ollama service availability check."""

    @patch("markdown_reallocator.utils.model_loader.ollama.list")
    def test_ollama_available(self, mock_list) -> None:
        """Should return True when Ollama responds."""
        mock_list.return_value = {"models": []}
        assert check_ollama_available() is True

    @patch("markdown_reallocator.utils.model_loader.ollama.list")
    def test_ollama_unavailable(self, mock_list) -> None:
        """Should return False when Ollama raises exception."""
        mock_list.side_effect = Exception("Connection refused")
        assert check_ollama_available() is False

    @patch("markdown_reallocator.utils.model_loader.ollama.list")
    def test_ollama_timeout(self, mock_list) -> None:
        """Should return False on timeout."""
        mock_list.side_effect = TimeoutError("Request timeout")
        assert check_ollama_available() is False


class TestLoadEmbeddingModel:
    """Tests for embedding model loading."""

    @patch("markdown_reallocator.utils.model_loader.ollama.Client")
    @patch("markdown_reallocator.utils.model_loader.ollama.list")
    def test_successful_load(self, mock_list, mock_client_class) -> None:
        """Should successfully load model when available."""
        # Mock ollama.list() response
        mock_list.return_value = {
            "models": [
                {"name": "embeddinggemma:latest"},
                {"name": "llama2:latest"},
            ]
        }

        # Mock client instance
        mock_client = Mock()
        mock_client.embeddings.return_value = {
            "embedding": [0.1, 0.2, 0.3]
        }
        mock_client_class.return_value = mock_client

        # Load model
        client = load_embedding_model("embeddinggemma")

        assert client is not None
        assert client == mock_client
        mock_client.embeddings.assert_called_once()

    @patch("markdown_reallocator.utils.model_loader.ollama.list")
    def test_ollama_not_running(self, mock_list) -> None:
        """Should raise OllamaConnectionError when service unavailable."""
        mock_list.side_effect = Exception("Connection refused")

        with pytest.raises(
            OllamaConnectionError,
            match="Ollama service is not available"
        ):
            load_embedding_model("embeddinggemma")

    @patch("markdown_reallocator.utils.model_loader.ollama.list")
    def test_model_not_found(self, mock_list) -> None:
        """Should raise ModelLoadError when model doesn't exist."""
        mock_list.return_value = {
            "models": [
                {"name": "llama2:latest"},
            ]
        }

        with pytest.raises(
            ModelLoadError,
            match="Model 'embeddinggemma' not found"
        ):
            load_embedding_model("embeddinggemma")

    @patch("markdown_reallocator.utils.model_loader.ollama.Client")
    @patch("markdown_reallocator.utils.model_loader.ollama.list")
    def test_model_fails_test_embedding(self, mock_list, mock_client_class) -> None:
        """Should raise ModelLoadError when test embedding fails."""
        mock_list.return_value = {
            "models": [{"name": "embeddinggemma:latest"}]
        }

        mock_client = Mock()
        mock_client.embeddings.side_effect = Exception("GPU out of memory")
        mock_client_class.return_value = mock_client

        with pytest.raises(
            ModelLoadError,
            match="Failed to generate test embedding"
        ):
            load_embedding_model("embeddinggemma")

    @patch("markdown_reallocator.utils.model_loader.ollama.Client")
    @patch("markdown_reallocator.utils.model_loader.ollama.list")
    def test_model_returns_invalid_response(self, mock_list, mock_client_class) -> None:
        """Should raise ModelLoadError when embedding response is invalid."""
        mock_list.return_value = {
            "models": [{"name": "embeddinggemma:latest"}]
        }

        mock_client = Mock()
        # Missing 'embedding' key
        mock_client.embeddings.return_value = {"error": "something wrong"}
        mock_client_class.return_value = mock_client

        with pytest.raises(
            ModelLoadError,
            match="did not return embedding"
        ):
            load_embedding_model("embeddinggemma")

    @patch("markdown_reallocator.utils.model_loader.time.sleep")
    @patch("markdown_reallocator.utils.model_loader.ollama.Client")
    @patch("markdown_reallocator.utils.model_loader.ollama.list")
    @patch("markdown_reallocator.utils.model_loader.check_ollama_available")
    def test_retry_on_transient_error(self, mock_check, mock_list, mock_client_class, mock_sleep) -> None:
        """Should retry on transient errors."""
        mock_check.return_value = True  # Ollama is available
        mock_list.side_effect = [
            Exception("Temporary failure"),  # First attempt
            {"models": [{"name": "embeddinggemma:latest"}]},  # Second attempt
        ]

        mock_client = Mock()
        mock_client.embeddings.return_value = {"embedding": [0.1, 0.2, 0.3]}
        mock_client_class.return_value = mock_client

        client = load_embedding_model("embeddinggemma", retry_count=2, retry_delay=0.1)

        assert client is not None
        assert mock_list.call_count == 2
        mock_sleep.assert_called_once_with(0.1)

    @patch("markdown_reallocator.utils.model_loader.time.sleep")
    @patch("markdown_reallocator.utils.model_loader.ollama.Client")
    @patch("markdown_reallocator.utils.model_loader.ollama.list")
    def test_retry_exhausted(self, mock_list, mock_client_class, mock_sleep) -> None:
        """Should raise after all retries exhausted."""
        mock_list.side_effect = Exception("Persistent failure")

        # First call checks if Ollama is available - returns False, raises error
        # We need to mock check_ollama_available instead
        with patch("markdown_reallocator.utils.model_loader.check_ollama_available", return_value=True):
            with pytest.raises(
                ModelLoadError,
                match="Failed to load model .* after 3 attempts"
            ):
                load_embedding_model("embeddinggemma", retry_count=3, retry_delay=0.01)

            assert mock_sleep.call_count == 2  # Retry 3 times = 2 sleeps

    @patch("markdown_reallocator.utils.model_loader.ollama.Client")
    @patch("markdown_reallocator.utils.model_loader.ollama.list")
    def test_model_name_with_version(self, mock_list, mock_client_class) -> None:
        """Should handle model names with version tags."""
        mock_list.return_value = {
            "models": [
                {"name": "embeddinggemma:v1.0"},
            ]
        }

        mock_client = Mock()
        mock_client.embeddings.return_value = {"embedding": [0.1, 0.2, 0.3]}
        mock_client_class.return_value = mock_client

        client = load_embedding_model("embeddinggemma")
        assert client is not None

    @patch("markdown_reallocator.utils.model_loader.ollama.Client")
    @patch("markdown_reallocator.utils.model_loader.ollama.list")
    def test_pydantic_response(self, mock_list, mock_client_class) -> None:
        """Should handle Pydantic object responses from ollama.list()."""
        # Create mock Pydantic response
        mock_model = Mock()
        mock_model.model = "embeddinggemma:latest"

        mock_response = Mock()
        mock_response.models = [mock_model]
        mock_list.return_value = mock_response

        mock_client = Mock()
        mock_client.embeddings.return_value = {"embedding": [0.1, 0.2, 0.3]}
        mock_client_class.return_value = mock_client

        client = load_embedding_model("embeddinggemma")
        assert client is not None

    @patch("markdown_reallocator.utils.model_loader.ollama.Client")
    @patch("markdown_reallocator.utils.model_loader.ollama.list")
    def test_unknown_model_type(self, mock_list, mock_client_class) -> None:
        """Should handle unknown model types by converting to string."""
        # Create mock response with unknown type
        mock_response = Mock()
        mock_response.models = ["embeddinggemma:latest"]  # String instead of dict/Model
        mock_list.return_value = mock_response

        mock_client = Mock()
        mock_client.embeddings.return_value = {"embedding": [0.1, 0.2, 0.3]}
        mock_client_class.return_value = mock_client

        client = load_embedding_model("embeddinggemma")
        assert client is not None

    def test_invalid_retry_count(self) -> None:
        """Should raise ValueError for invalid retry_count."""
        with pytest.raises(ValueError, match="retry_count must be at least 1"):
            load_embedding_model("embeddinggemma", retry_count=0)

    def test_invalid_retry_delay(self) -> None:
        """Should raise ValueError for negative retry_delay."""
        with pytest.raises(ValueError, match="retry_delay must be non-negative"):
            load_embedding_model("embeddinggemma", retry_delay=-1.0)


class TestLoadLLMModel:
    """Tests for LLM model loading."""

    @patch("markdown_reallocator.utils.model_loader.ollama.Client")
    @patch("markdown_reallocator.utils.model_loader.ollama.list")
    def test_successful_load(self, mock_list, mock_client_class) -> None:
        """Should successfully load LLM model when available."""
        mock_list.return_value = {
            "models": [
                {"name": "gemma:2b-instruct-q4_0"},
            ]
        }

        mock_client = Mock()
        mock_client.generate.return_value = {"response": "test output"}
        mock_client_class.return_value = mock_client

        client = load_llm_model("gemma:2b-instruct-q4_0")

        assert client is not None
        assert client == mock_client
        mock_client.generate.assert_called_once()

    @patch("markdown_reallocator.utils.model_loader.ollama.list")
    def test_ollama_not_running(self, mock_list) -> None:
        """Should raise OllamaConnectionError when service unavailable."""
        mock_list.side_effect = Exception("Connection refused")

        with pytest.raises(
            OllamaConnectionError,
            match="Ollama service is not available"
        ):
            load_llm_model("gemma:2b-instruct-q4_0")

    @patch("markdown_reallocator.utils.model_loader.ollama.list")
    def test_model_not_found(self, mock_list) -> None:
        """Should raise ModelLoadError when model doesn't exist."""
        mock_list.return_value = {
            "models": [
                {"name": "llama2:latest"},
            ]
        }

        with pytest.raises(
            ModelLoadError,
            match="Model 'gemma:2b-instruct-q4_0' not found"
        ):
            load_llm_model("gemma:2b-instruct-q4_0")

    @patch("markdown_reallocator.utils.model_loader.ollama.Client")
    @patch("markdown_reallocator.utils.model_loader.ollama.list")
    def test_model_fails_test_generation(self, mock_list, mock_client_class) -> None:
        """Should raise ModelLoadError when test generation fails."""
        mock_list.return_value = {
            "models": [{"name": "gemma:2b-instruct-q4_0"}]
        }

        mock_client = Mock()
        mock_client.generate.side_effect = Exception("Model loading failed")
        mock_client_class.return_value = mock_client

        with pytest.raises(
            ModelLoadError,
            match="Failed to generate test response"
        ):
            load_llm_model("gemma:2b-instruct-q4_0")

    @patch("markdown_reallocator.utils.model_loader.ollama.Client")
    @patch("markdown_reallocator.utils.model_loader.ollama.list")
    def test_model_returns_invalid_response(self, mock_list, mock_client_class) -> None:
        """Should raise ModelLoadError when generation response is invalid."""
        mock_list.return_value = {
            "models": [{"name": "gemma:2b-instruct-q4_0"}]
        }

        mock_client = Mock()
        # Missing 'response' key
        mock_client.generate.return_value = {"error": "something wrong"}
        mock_client_class.return_value = mock_client

        with pytest.raises(
            ModelLoadError,
            match="did not return response"
        ):
            load_llm_model("gemma:2b-instruct-q4_0")

    @patch("markdown_reallocator.utils.model_loader.ollama.Client")
    @patch("markdown_reallocator.utils.model_loader.ollama.list")
    def test_model_name_matching(self, mock_list, mock_client_class) -> None:
        """Should match model names with different version suffixes."""
        mock_list.return_value = {
            "models": [
                {"name": "gemma:2b-instruct-q4_0"},
                {"name": "gemma:7b-instruct"},
            ]
        }

        mock_client = Mock()
        mock_client.generate.return_value = {"response": "test"}
        mock_client_class.return_value = mock_client

        # Should match "gemma:2b-instruct-q4_0"
        client = load_llm_model("gemma:2b-instruct-q4_0")
        assert client is not None

    @patch("markdown_reallocator.utils.model_loader.ollama.Client")
    @patch("markdown_reallocator.utils.model_loader.ollama.list")
    def test_pydantic_response(self, mock_list, mock_client_class) -> None:
        """Should handle Pydantic object responses from ollama.list()."""
        # Create mock Pydantic response
        mock_model = Mock()
        mock_model.model = "gemma:2b-instruct-q4_0"

        mock_response = Mock()
        mock_response.models = [mock_model]
        mock_list.return_value = mock_response

        mock_client = Mock()
        mock_client.generate.return_value = {"response": "test"}
        mock_client_class.return_value = mock_client

        client = load_llm_model("gemma:2b-instruct-q4_0")
        assert client is not None

    @patch("markdown_reallocator.utils.model_loader.ollama.Client")
    @patch("markdown_reallocator.utils.model_loader.ollama.list")
    def test_unknown_model_type(self, mock_list, mock_client_class) -> None:
        """Should handle unknown model types by converting to string."""
        # Create mock response with unknown type
        mock_response = Mock()
        mock_response.models = ["gemma:2b-instruct-q4_0"]  # String instead of dict/Model
        mock_list.return_value = mock_response

        mock_client = Mock()
        mock_client.generate.return_value = {"response": "test"}
        mock_client_class.return_value = mock_client

        client = load_llm_model("gemma:2b-instruct-q4_0")
        assert client is not None

    @patch("markdown_reallocator.utils.model_loader.time.sleep")
    @patch("markdown_reallocator.utils.model_loader.ollama.Client")
    @patch("markdown_reallocator.utils.model_loader.ollama.list")
    @patch("markdown_reallocator.utils.model_loader.check_ollama_available")
    def test_retry_on_transient_error(self, mock_check, mock_list, mock_client_class, mock_sleep) -> None:
        """Should retry on transient errors."""
        mock_check.return_value = True  # Ollama is available
        mock_list.side_effect = [
            Exception("Temporary failure"),
            {"models": [{"name": "gemma:2b-instruct-q4_0"}]},
        ]

        mock_client = Mock()
        mock_client.generate.return_value = {"response": "test"}
        mock_client_class.return_value = mock_client

        client = load_llm_model("gemma:2b-instruct-q4_0", retry_count=2, retry_delay=0.1)

        assert client is not None
        mock_sleep.assert_called_once_with(0.1)

    def test_invalid_retry_count(self) -> None:
        """Should raise ValueError for invalid retry_count."""
        with pytest.raises(ValueError, match="retry_count must be at least 1"):
            load_llm_model("gemma:2b-instruct-q4_0", retry_count=0)

    def test_invalid_retry_delay(self) -> None:
        """Should raise ValueError for negative retry_delay."""
        with pytest.raises(ValueError, match="retry_delay must be non-negative"):
            load_llm_model("gemma:2b-instruct-q4_0", retry_delay=-1.0)


class TestGetAvailableModels:
    """Tests for listing available models."""

    @patch("markdown_reallocator.utils.model_loader.ollama.list")
    @patch("markdown_reallocator.utils.model_loader.check_ollama_available")
    def test_get_models_success(self, mock_check, mock_list) -> None:
        """Should return list of models."""
        mock_check.return_value = True  # Ollama is available
        expected_models = [
            {"name": "embeddinggemma:latest", "size": 1000000},
            {"name": "gemma:2b-instruct-q4_0", "size": 2000000},
            {"name": "llama2:latest", "size": 3000000},
        ]
        mock_list.return_value = {"models": expected_models}

        models = get_available_models()

        assert models == expected_models
        mock_list.assert_called_once()

    @patch("markdown_reallocator.utils.model_loader.ollama.list")
    def test_get_models_empty(self, mock_list) -> None:
        """Should return empty list when no models."""
        mock_list.return_value = {"models": []}

        models = get_available_models()

        assert models == []

    @patch("markdown_reallocator.utils.model_loader.ollama.list")
    def test_get_models_no_models_key(self, mock_list) -> None:
        """Should return empty list when 'models' key missing."""
        mock_list.return_value = {}

        models = get_available_models()

        assert models == []

    @patch("markdown_reallocator.utils.model_loader.ollama.list")
    def test_ollama_not_available(self, mock_list) -> None:
        """Should raise OllamaConnectionError when service unavailable."""
        mock_list.side_effect = Exception("Connection refused")

        with pytest.raises(
            OllamaConnectionError,
            match="Ollama service is not available"
        ):
            get_available_models()

    @patch("markdown_reallocator.utils.model_loader.ollama.list")
    def test_list_fails(self, mock_list) -> None:
        """Should raise OllamaConnectionError when list fails."""
        mock_list.side_effect = Exception("Internal error")

        # check_ollama_available will catch this and return False
        # So we need to mock it
        with patch("markdown_reallocator.utils.model_loader.check_ollama_available", return_value=True):
            with pytest.raises(
                OllamaConnectionError,
                match="Failed to list models"
            ):
                get_available_models()

    @patch("markdown_reallocator.utils.model_loader.ollama.list")
    @patch("markdown_reallocator.utils.model_loader.check_ollama_available")
    def test_pydantic_response(self, mock_check, mock_list) -> None:
        """Should handle Pydantic object responses from ollama.list()."""
        mock_check.return_value = True

        # Create mock Pydantic Model objects
        mock_model1 = Mock()
        mock_model1.model = "embeddinggemma:latest"
        mock_model1.size = 1000000
        mock_model1.modified_at = "2024-01-01T00:00:00"

        mock_model2 = Mock()
        mock_model2.model = "gemma:2b-instruct-q4_0"
        mock_model2.size = 2000000
        mock_model2.modified_at = "2024-01-02T00:00:00"

        # Create mock ListResponse
        mock_response = Mock()
        mock_response.models = [mock_model1, mock_model2]
        mock_list.return_value = mock_response

        models = get_available_models()

        assert len(models) == 2
        assert models[0]["name"] == "embeddinggemma:latest"
        assert models[0]["size"] == 1000000
        assert models[1]["name"] == "gemma:2b-instruct-q4_0"

    @patch("markdown_reallocator.utils.model_loader.ollama.list")
    @patch("markdown_reallocator.utils.model_loader.check_ollama_available")
    def test_pydantic_response_missing_attributes(self, mock_check, mock_list) -> None:
        """Should handle Pydantic objects with missing optional attributes."""
        mock_check.return_value = True

        # Create mock Model without size/modified_at
        mock_model = Mock(spec=["model"])  # Only has 'model' attribute
        mock_model.model = "embeddinggemma:latest"

        mock_response = Mock()
        mock_response.models = [mock_model]
        mock_list.return_value = mock_response

        models = get_available_models()

        assert len(models) == 1
        assert models[0]["name"] == "embeddinggemma:latest"
        assert models[0]["size"] == 0  # Default value
        assert models[0]["modified_at"] == ""  # Default value


class TestModelExists:
    """Tests for checking model existence."""

    @patch("markdown_reallocator.utils.model_loader.get_available_models")
    def test_model_exists_exact_match(self, mock_get_models) -> None:
        """Should return True for exact model name match."""
        mock_get_models.return_value = [
            {"name": "embeddinggemma:latest"},
            {"name": "llama2:latest"},
        ]

        assert model_exists("embeddinggemma:latest") is True
        assert model_exists("llama2:latest") is True

    @patch("markdown_reallocator.utils.model_loader.get_available_models")
    def test_model_exists_prefix_match(self, mock_get_models) -> None:
        """Should return True for prefix match (without version)."""
        mock_get_models.return_value = [
            {"name": "gemma:2b-instruct-q4_0"},
        ]

        # Should match "gemma:2b-instruct-q4_0" with "gemma"
        assert model_exists("gemma") is True
        assert model_exists("gemma:2b-instruct-q4_0") is True

    @patch("markdown_reallocator.utils.model_loader.get_available_models")
    def test_model_not_exists(self, mock_get_models) -> None:
        """Should return False when model doesn't exist."""
        mock_get_models.return_value = [
            {"name": "embeddinggemma:latest"},
        ]

        assert model_exists("llama2") is False
        assert model_exists("nonexistent") is False

    @patch("markdown_reallocator.utils.model_loader.get_available_models")
    def test_model_exists_empty_list(self, mock_get_models) -> None:
        """Should return False when no models available."""
        mock_get_models.return_value = []

        assert model_exists("anymodel") is False

    @patch("markdown_reallocator.utils.model_loader.get_available_models")
    def test_model_exists_with_colons(self, mock_get_models) -> None:
        """Should handle model names with multiple colons."""
        mock_get_models.return_value = [
            {"name": "llama2:13b:q4_0"},
        ]

        assert model_exists("llama2:13b:q4_0") is True
        assert model_exists("llama2") is True  # Prefix match


class TestErrorMessages:
    """Tests for error message quality."""

    @patch("markdown_reallocator.utils.model_loader.ollama.list")
    def test_model_not_found_suggests_pull(self, mock_list) -> None:
        """Error message should suggest how to pull model."""
        mock_list.return_value = {
            "models": [{"name": "llama2:latest"}]
        }

        with pytest.raises(ModelLoadError) as exc_info:
            load_embedding_model("embeddinggemma")

        error_message = str(exc_info.value)
        assert "ollama pull embeddinggemma" in error_message
        assert "Available models" in error_message

    @patch("markdown_reallocator.utils.model_loader.ollama.list")
    def test_ollama_down_suggests_serve(self, mock_list) -> None:
        """Error message should suggest how to start Ollama."""
        mock_list.side_effect = Exception("Connection refused")

        with pytest.raises(OllamaConnectionError) as exc_info:
            load_embedding_model("embeddinggemma")

        error_message = str(exc_info.value)
        assert "ollama serve" in error_message
        assert "not available" in error_message.lower()


class TestRetryBehavior:
    """Tests for retry logic behavior."""

    @patch("markdown_reallocator.utils.model_loader.time.sleep")
    @patch("markdown_reallocator.utils.model_loader.ollama.Client")
    @patch("markdown_reallocator.utils.model_loader.ollama.list")
    @patch("markdown_reallocator.utils.model_loader.check_ollama_available")
    def test_no_retry_on_model_not_found(self, mock_check, mock_list, mock_client_class, mock_sleep) -> None:
        """Should not retry when model is not found (permanent error)."""
        mock_check.return_value = True  # Ollama is available
        mock_list.return_value = {"models": [{"name": "other:model"}]}

        with pytest.raises(ModelLoadError, match="not found"):
            load_embedding_model("embeddinggemma", retry_count=3, retry_delay=0.1)

        # Should not retry (only called once)
        assert mock_list.call_count == 1
        mock_sleep.assert_not_called()

    @patch("markdown_reallocator.utils.model_loader.time.sleep")
    @patch("markdown_reallocator.utils.model_loader.ollama.list")
    def test_no_retry_on_ollama_down(self, mock_list, mock_sleep) -> None:
        """Should not retry when Ollama is down (permanent error)."""
        mock_list.side_effect = Exception("Connection refused")

        with pytest.raises(OllamaConnectionError):
            load_embedding_model("embeddinggemma", retry_count=3, retry_delay=0.1)

        # check_ollama_available is called once, no retries
        assert mock_list.call_count == 1
        mock_sleep.assert_not_called()

    @patch("markdown_reallocator.utils.model_loader.time.sleep")
    @patch("markdown_reallocator.utils.model_loader.ollama.Client")
    @patch("markdown_reallocator.utils.model_loader.ollama.list")
    def test_retry_delay_honored(self, mock_list, mock_client_class, mock_sleep) -> None:
        """Should use specified retry_delay."""
        mock_list.side_effect = [
            Exception("Temporary failure"),
            Exception("Temporary failure"),
            {"models": [{"name": "embeddinggemma:latest"}]},
        ]

        mock_client = Mock()
        mock_client.embeddings.return_value = {"embedding": [0.1, 0.2, 0.3]}
        mock_client_class.return_value = mock_client

        with patch("markdown_reallocator.utils.model_loader.check_ollama_available", return_value=True):
            client = load_embedding_model("embeddinggemma", retry_count=3, retry_delay=0.5)

        assert client is not None
        # Should sleep twice (3 attempts = 2 sleeps)
        assert mock_sleep.call_count == 2
        mock_sleep.assert_called_with(0.5)


class TestBranchCoverage:
    """Tests specifically for branch coverage."""

    @patch("markdown_reallocator.utils.model_loader.time.sleep")
    @patch("markdown_reallocator.utils.model_loader.ollama.list")
    @patch("markdown_reallocator.utils.model_loader.check_ollama_available")
    def test_embedding_retry_break_path(self, mock_check, mock_list, mock_sleep) -> None:
        """Should cover branch 88->145 (break statement on last retry)."""
        mock_check.return_value = True

        # Raise generic exceptions on all retry attempts
        # This will hit the break statement (line 142) on the last attempt
        mock_list.side_effect = [
            Exception("Transient error 1"),
            Exception("Transient error 2"),
            Exception("Transient error 3"),  # Last attempt hits break
        ]

        with pytest.raises(
            ModelLoadError,
            match="Failed to load model .* after 3 attempts"
        ):
            load_embedding_model("embeddinggemma", retry_count=3, retry_delay=0.01)

        # Should attempt 3 times
        assert mock_list.call_count == 3
        # Should sleep twice (between attempts 1-2 and 2-3)
        assert mock_sleep.call_count == 2

    @patch("markdown_reallocator.utils.model_loader.time.sleep")
    @patch("markdown_reallocator.utils.model_loader.ollama.list")
    @patch("markdown_reallocator.utils.model_loader.check_ollama_available")
    def test_llm_retry_break_path(self, mock_check, mock_list, mock_sleep) -> None:
        """Should cover branch 193->250 (break statement on last retry for LLM)."""
        mock_check.return_value = True

        # Raise generic exceptions on all retry attempts
        # This will hit the break statement (line 247) on the last attempt
        mock_list.side_effect = [
            Exception("Transient error 1"),
            Exception("Transient error 2"),
            Exception("Transient error 3"),  # Last attempt hits break
        ]

        with pytest.raises(
            ModelLoadError,
            match="Failed to load model .* after 3 attempts"
        ):
            load_llm_model("gemma:2b-instruct-q4_0", retry_count=3, retry_delay=0.01)

        # Should attempt 3 times
        assert mock_list.call_count == 3
        # Should sleep twice (between attempts 1-2 and 2-3)
        assert mock_sleep.call_count == 2
