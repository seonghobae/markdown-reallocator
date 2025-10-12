"""Tests for configuration system."""

import json
import os
from unittest.mock import patch

import pytest

from markdown_reallocator.config import (
    DedupSettings,
    EmbedderSettings,
    PreprocessorSettings,
    ReorderSettings,
    SearchSettings,
    Settings,
    SplitterSettings,
    load_config,
    save_config,
)


class TestPreprocessorSettings:
    """Tests for PreprocessorSettings validation."""

    def test_default_values(self):
        """Test default settings are valid."""
        settings = PreprocessorSettings()
        assert settings.max_title_length == 80
        assert settings.require_empty_lines is True
        assert settings.min_capitalization_ratio == 0.1
        assert settings.detect_title_case is True
        assert settings.preserve_code_blocks is True

    def test_custom_values(self):
        """Test custom settings are applied."""
        settings = PreprocessorSettings(
            max_title_length=100,
            require_empty_lines=False,
            min_capitalization_ratio=0.2,
        )
        assert settings.max_title_length == 100
        assert settings.require_empty_lines is False
        assert settings.min_capitalization_ratio == 0.2

    def test_invalid_max_title_length(self):
        """Test validation rejects invalid max_title_length."""
        with pytest.raises(ValueError, match="max_title_length must be positive"):
            PreprocessorSettings(max_title_length=0)

        with pytest.raises(ValueError, match="max_title_length must be positive"):
            PreprocessorSettings(max_title_length=-1)

    def test_invalid_capitalization_ratio(self):
        """Test validation rejects out-of-range capitalization ratio."""
        with pytest.raises(ValueError, match="min_capitalization_ratio must be in"):
            PreprocessorSettings(min_capitalization_ratio=-0.1)

        with pytest.raises(ValueError, match="min_capitalization_ratio must be in"):
            PreprocessorSettings(min_capitalization_ratio=1.1)


class TestSplitterSettings:
    """Tests for SplitterSettings validation."""

    def test_default_values(self):
        """Test default settings are valid."""
        settings = SplitterSettings()
        assert settings.headers_to_split_on == [("#", "h1"), ("##", "h2"), ("###", "h3")]
        assert settings.max_tokens_per_chunk == 1000

    def test_custom_headers(self):
        """Test custom header configuration."""
        custom_headers = [("#", "h1"), ("##", "h2")]
        settings = SplitterSettings(headers_to_split_on=custom_headers)
        assert settings.headers_to_split_on == custom_headers

    def test_invalid_max_tokens(self):
        """Test validation rejects invalid max_tokens_per_chunk."""
        with pytest.raises(ValueError, match="max_tokens_per_chunk must be positive"):
            SplitterSettings(max_tokens_per_chunk=0)


class TestEmbedderSettings:
    """Tests for EmbedderSettings validation."""

    def test_default_values(self):
        """Test default settings are valid."""
        settings = EmbedderSettings()
        assert settings.model_name == "embeddinggemma"
        assert settings.cache_enabled is True
        assert settings.batch_size == 10
        assert settings.memory_threshold_mb == 1500.0

    def test_custom_model(self):
        """Test custom model name."""
        settings = EmbedderSettings(model_name="nomic-embed-text")
        assert settings.model_name == "nomic-embed-text"

    def test_invalid_batch_size(self):
        """Test validation rejects invalid batch_size."""
        with pytest.raises(ValueError, match="batch_size must be positive"):
            EmbedderSettings(batch_size=0)

    def test_invalid_cache_size(self):
        """Test validation rejects invalid cache_max_size."""
        with pytest.raises(ValueError, match="cache_max_size must be positive"):
            EmbedderSettings(cache_max_size=-1)

    def test_invalid_memory_threshold(self):
        """Test validation rejects invalid memory_threshold_mb."""
        with pytest.raises(ValueError, match="memory_threshold_mb must be positive"):
            EmbedderSettings(memory_threshold_mb=0)


class TestReorderSettings:
    """Tests for ReorderSettings validation."""

    def test_default_values(self):
        """Test default settings are valid."""
        settings = ReorderSettings()
        assert settings.strategy == "sequential"
        assert settings.similarity_threshold == 0.5

    def test_cluster_strategy(self):
        """Test cluster strategy."""
        settings = ReorderSettings(strategy="cluster")
        assert settings.strategy == "cluster"

    def test_invalid_strategy(self):
        """Test validation rejects invalid strategy."""
        with pytest.raises(ValueError, match="strategy must be"):
            ReorderSettings(strategy="invalid")

    def test_invalid_threshold(self):
        """Test validation rejects out-of-range threshold."""
        with pytest.raises(ValueError, match="similarity_threshold must be in"):
            ReorderSettings(similarity_threshold=1.5)


class TestSearchSettings:
    """Tests for SearchSettings validation."""

    def test_default_values(self):
        """Test default settings are valid."""
        settings = SearchSettings()
        assert settings.top_k == 5
        assert settings.min_similarity == 0.5
        assert settings.output_format == "text"

    def test_json_format(self):
        """Test JSON output format."""
        settings = SearchSettings(output_format="json")
        assert settings.output_format == "json"

    def test_invalid_top_k(self):
        """Test validation rejects invalid top_k."""
        with pytest.raises(ValueError, match="top_k must be positive"):
            SearchSettings(top_k=0)

    def test_invalid_format(self):
        """Test validation rejects invalid output_format."""
        with pytest.raises(ValueError, match="output_format must be"):
            SearchSettings(output_format="xml")

    def test_invalid_min_similarity(self):
        """Test validation rejects out-of-range min_similarity."""
        with pytest.raises(ValueError, match="min_similarity must be in"):
            SearchSettings(min_similarity=1.5)

        with pytest.raises(ValueError, match="min_similarity must be in"):
            SearchSettings(min_similarity=-0.1)


class TestDedupSettings:
    """Tests for DedupSettings validation."""

    def test_default_values(self):
        """Test default settings are valid."""
        settings = DedupSettings()
        assert settings.similarity_threshold == 0.85
        assert settings.selection_strategy == "first"
        assert settings.use_llm is False
        assert settings.dry_run is False

    def test_longest_strategy(self):
        """Test longest selection strategy."""
        settings = DedupSettings(selection_strategy="longest")
        assert settings.selection_strategy == "longest"

    def test_invalid_strategy(self):
        """Test validation rejects invalid selection_strategy."""
        with pytest.raises(ValueError, match="selection_strategy must be"):
            DedupSettings(selection_strategy="random")

    def test_invalid_threshold(self):
        """Test validation rejects out-of-range threshold."""
        with pytest.raises(ValueError, match="similarity_threshold must be in"):
            DedupSettings(similarity_threshold=2.0)


class TestSettings:
    """Tests for composite Settings class."""

    def test_default_settings(self):
        """Test default Settings are valid."""
        settings = Settings()
        assert isinstance(settings.preprocessor, PreprocessorSettings)
        assert isinstance(settings.splitter, SplitterSettings)
        assert isinstance(settings.embedder, EmbedderSettings)
        assert isinstance(settings.reorder, ReorderSettings)
        assert isinstance(settings.search, SearchSettings)
        assert isinstance(settings.dedup, DedupSettings)

    def test_to_dict(self):
        """Test Settings can be converted to dict."""
        settings = Settings()
        config_dict = settings.to_dict()

        assert "preprocessor" in config_dict
        assert "splitter" in config_dict
        assert "embedder" in config_dict
        assert "reorder" in config_dict
        assert "search" in config_dict
        assert "dedup" in config_dict

        # Verify nested structure
        assert config_dict["preprocessor"]["max_title_length"] == 80
        assert config_dict["embedder"]["model_name"] == "embeddinggemma"

        # Verify tuples are converted to lists for YAML/JSON compatibility
        headers = config_dict["splitter"]["headers_to_split_on"]
        assert all(isinstance(h, list) for h in headers)
        assert headers == [["#", "h1"], ["##", "h2"], ["###", "h3"]]

    def test_from_dict(self):
        """Test Settings can be created from dict."""
        config_dict = {
            "preprocessor": {"max_title_length": 100},
            "embedder": {"model_name": "custom-model", "batch_size": 20},
            "search": {"top_k": 10},
        }

        settings = Settings.from_dict(config_dict)

        assert settings.preprocessor.max_title_length == 100
        assert settings.embedder.model_name == "custom-model"
        assert settings.embedder.batch_size == 20
        assert settings.search.top_k == 10

        # Defaults should still be applied for unspecified values
        assert settings.preprocessor.require_empty_lines is True
        assert settings.splitter.max_tokens_per_chunk == 1000

    def test_from_dict_empty(self):
        """Test Settings can be created from empty dict (all defaults)."""
        settings = Settings.from_dict({})

        assert settings.preprocessor.max_title_length == 80
        assert settings.embedder.model_name == "embeddinggemma"
        assert settings.search.top_k == 5

    def test_from_dict_invalid_values(self):
        """Test Settings.from_dict validates nested values."""
        config_dict = {
            "preprocessor": {"max_title_length": -1}  # Invalid
        }

        with pytest.raises(ValueError):
            Settings.from_dict(config_dict)


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_yaml(self, tmp_path):
        """Test loading configuration from YAML file."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text(
            """
preprocessor:
  max_title_length: 120

embedder:
  model_name: "test-model"
  batch_size: 50

search:
  top_k: 10
"""
        )

        settings = load_config(config_path)

        assert settings.preprocessor.max_title_length == 120
        assert settings.embedder.model_name == "test-model"
        assert settings.embedder.batch_size == 50
        assert settings.search.top_k == 10

    def test_load_json(self, tmp_path):
        """Test loading configuration from JSON file."""
        config_path = tmp_path / "config.json"
        config_dict = {
            "preprocessor": {"max_title_length": 150},
            "reorder": {"strategy": "cluster"},
        }
        config_path.write_text(json.dumps(config_dict))

        settings = load_config(config_path)

        assert settings.preprocessor.max_title_length == 150
        assert settings.reorder.strategy == "cluster"

    def test_load_nonexistent_path(self):
        """Test load_config raises error for nonexistent path."""
        with pytest.raises(FileNotFoundError):
            load_config("/nonexistent/path/config.yaml")

    def test_load_invalid_yaml(self, tmp_path):
        """Test load_config raises error for invalid YAML."""
        config_path = tmp_path / "bad.yaml"
        config_path.write_text("{ invalid yaml: [")

        with pytest.raises(ValueError, match="Failed to load config"):
            load_config(config_path)

    def test_load_invalid_json(self, tmp_path):
        """Test load_config raises error for invalid JSON."""
        config_path = tmp_path / "bad.json"
        config_path.write_text("{ invalid json")

        with pytest.raises(ValueError, match="Failed to load config"):
            load_config(config_path)

    def test_load_unsupported_format(self, tmp_path):
        """Test load_config raises error for unsupported file format."""
        config_path = tmp_path / "config.txt"
        config_path.write_text("some config")

        with pytest.raises(ValueError, match="Unsupported config file format"):
            load_config(config_path)

    def test_load_with_env_overrides(self, tmp_path):
        """Test environment variables override file settings."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text(
            """
embedder:
  model_name: "file-model"
  batch_size: 10

search:
  top_k: 5
"""
        )

        # Set environment variables
        env_vars = {
            "MARKDOWN_REALLOCATOR_EMBEDDER_MODEL_NAME": "env-model",
            "MARKDOWN_REALLOCATOR_SEARCH_TOP_K": "20",
        }

        with patch.dict(os.environ, env_vars):
            settings = load_config(config_path)

        # Env vars should override file values
        assert settings.embedder.model_name == "env-model"
        assert settings.search.top_k == 20

        # Non-overridden values should come from file
        assert settings.embedder.batch_size == 10

    def test_load_no_config_uses_defaults(self, tmp_path, monkeypatch):
        """Test load_config uses defaults when no config file found."""
        # Change to temp directory with no config files
        monkeypatch.chdir(tmp_path)

        settings = load_config()

        # Should use all defaults
        assert settings.preprocessor.max_title_length == 80
        assert settings.embedder.model_name == "embeddinggemma"
        assert settings.search.top_k == 5

    def test_env_override_json_values(self, tmp_path):
        """Test environment variables can provide JSON values."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text(
            """
preprocessor:
  max_title_length: 80

splitter:
  max_tokens_per_chunk: 1000
"""
        )

        # Set env var with JSON value
        env_vars = {
            "MARKDOWN_REALLOCATOR_SPLITTER_HEADERS_TO_SPLIT_ON": '[["#", "h1"], ["##", "h2"]]'
        }

        with patch.dict(os.environ, env_vars):
            settings = load_config(config_path)

        # Lists from JSON are converted to tuples in __post_init__
        assert settings.splitter.headers_to_split_on == [("#", "h1"), ("##", "h2")]

    def test_env_var_invalid_format_warning(self, tmp_path):
        """Test warning when env var has invalid format (no underscore separator)."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text("preprocessor:\n  max_title_length: 80\n")

        # Env var without section_key format
        env_vars = {"MARKDOWN_REALLOCATOR_INVALID": "value"}

        with patch.dict(os.environ, env_vars):
            settings = load_config(config_path)

        # Should still load successfully with warning
        assert settings.preprocessor.max_title_length == 80

    def test_env_var_unknown_section_warning(self, tmp_path):
        """Test warning when env var references unknown config section."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text("preprocessor:\n  max_title_length: 80\n")

        # Env var with unknown section
        env_vars = {"MARKDOWN_REALLOCATOR_UNKNOWN_KEY": "value"}

        with patch.dict(os.environ, env_vars):
            settings = load_config(config_path)

        # Should still load successfully with warning
        assert settings.preprocessor.max_title_length == 80

    def test_load_config_validation_error(self, tmp_path):
        """Test load_config raises ValueError when config has invalid values."""
        config_path = tmp_path / "bad_config.yaml"
        config_path.write_text(
            """
preprocessor:
  max_title_length: -10  # Invalid value
"""
        )

        with pytest.raises(ValueError, match="Invalid config"):
            load_config(config_path)

    def test_load_config_non_dict_root(self, tmp_path):
        """Test load_config raises error when config file root is not a dict."""
        config_path = tmp_path / "list_config.yaml"
        config_path.write_text("[1, 2, 3]")  # YAML list, not dict

        with pytest.raises(ValueError, match="must contain a dictionary"):
            load_config(config_path)


class TestSaveConfig:
    """Tests for save_config function."""

    def test_save_yaml(self, tmp_path):
        """Test saving configuration to YAML file."""
        settings = Settings()
        settings.preprocessor.max_title_length = 150
        settings.embedder.model_name = "custom-model"

        config_path = tmp_path / "output.yaml"
        save_config(settings, config_path)

        # Verify file exists and is valid YAML
        assert config_path.exists()

        # Load and verify
        loaded_settings = load_config(config_path)
        assert loaded_settings.preprocessor.max_title_length == 150
        assert loaded_settings.embedder.model_name == "custom-model"

    def test_save_json(self, tmp_path):
        """Test saving configuration to JSON file."""
        settings = Settings()
        settings.search.top_k = 15

        config_path = tmp_path / "output.json"
        save_config(settings, config_path)

        # Verify file exists and is valid JSON
        assert config_path.exists()

        # Load and verify
        loaded_settings = load_config(config_path)
        assert loaded_settings.search.top_k == 15

    def test_save_creates_parent_dirs(self, tmp_path):
        """Test save_config creates parent directories."""
        settings = Settings()
        config_path = tmp_path / "subdir" / "nested" / "config.yaml"

        save_config(settings, config_path)

        assert config_path.exists()
        assert config_path.parent.exists()

    def test_save_unsupported_format(self, tmp_path):
        """Test save_config raises error for unsupported format."""
        settings = Settings()
        config_path = tmp_path / "config.txt"

        with pytest.raises(ValueError, match="Unsupported config file format"):
            save_config(settings, config_path)

    def test_save_and_load_roundtrip(self, tmp_path):
        """Test save and load preserve all settings."""
        # Create settings with custom values
        settings = Settings(
            preprocessor=PreprocessorSettings(
                max_title_length=200,
                require_empty_lines=False,
            ),
            embedder=EmbedderSettings(
                model_name="test-model",
                batch_size=25,
            ),
            reorder=ReorderSettings(strategy="cluster"),
            search=SearchSettings(top_k=15, output_format="json"),
            dedup=DedupSettings(
                similarity_threshold=0.9,
                selection_strategy="longest",
            ),
        )

        # Save and load
        config_path = tmp_path / "roundtrip.yaml"
        save_config(settings, config_path)
        loaded = load_config(config_path)

        # Verify all values preserved
        assert loaded.preprocessor.max_title_length == 200
        assert loaded.preprocessor.require_empty_lines is False
        assert loaded.embedder.model_name == "test-model"
        assert loaded.embedder.batch_size == 25
        assert loaded.reorder.strategy == "cluster"
        assert loaded.search.top_k == 15
        assert loaded.search.output_format == "json"
        assert loaded.dedup.similarity_threshold == 0.9
        assert loaded.dedup.selection_strategy == "longest"
