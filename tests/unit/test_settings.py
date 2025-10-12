"""Tests for configuration system."""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from markdown_reallocator.config.settings import (
    DedupSettings,
    EmbedderSettings,
    PreprocessorSettings,
    ReorderSettings,
    SearchSettings,
    Settings,
    SplitterSettings,
    _apply_env_overrides,
    _load_config_file,
    load_config,
    save_config,
)


class TestPreprocessorSettings:
    """Tests for PreprocessorSettings."""

    def test_default_initialization(self) -> None:
        """Should initialize with default values."""
        settings = PreprocessorSettings()

        assert settings.max_title_length == 80
        assert settings.require_empty_lines is True
        assert settings.min_capitalization_ratio == 0.1

    def test_custom_values(self) -> None:
        """Should accept custom values."""
        settings = PreprocessorSettings(
            max_title_length=100,
            require_empty_lines=False,
            min_capitalization_ratio=0.2,
        )

        assert settings.max_title_length == 100
        assert settings.require_empty_lines is False
        assert settings.min_capitalization_ratio == 0.2

    def test_invalid_max_title_length(self) -> None:
        """Should raise ValueError for invalid max_title_length."""
        with pytest.raises(ValueError, match="max_title_length must be positive"):
            PreprocessorSettings(max_title_length=0)

    def test_invalid_min_capitalization_ratio(self) -> None:
        """Should raise ValueError for invalid min_capitalization_ratio."""
        with pytest.raises(ValueError, match="min_capitalization_ratio must be in"):
            PreprocessorSettings(min_capitalization_ratio=1.5)


class TestSplitterSettings:
    """Tests for SplitterSettings."""

    def test_default_initialization(self) -> None:
        """Should initialize with default values."""
        settings = SplitterSettings()

        assert len(settings.headers_to_split_on) == 3
        assert settings.max_tokens_per_chunk == 1000

    def test_converts_lists_to_tuples(self) -> None:
        """Should convert list headers to tuples."""
        settings = SplitterSettings(
            headers_to_split_on=[["#", "h1"], ["##", "h2"]]  # type: ignore
        )

        # All should be tuples now
        for header in settings.headers_to_split_on:
            assert isinstance(header, tuple)

    def test_invalid_max_tokens_per_chunk(self) -> None:
        """Should raise ValueError for invalid max_tokens_per_chunk."""
        with pytest.raises(ValueError, match="max_tokens_per_chunk must be positive"):
            SplitterSettings(max_tokens_per_chunk=0)


class TestEmbedderSettings:
    """Tests for EmbedderSettings."""

    def test_default_initialization(self) -> None:
        """Should initialize with default values."""
        settings = EmbedderSettings()

        assert settings.model_name == "embeddinggemma"
        assert settings.cache_enabled is True
        assert settings.batch_size == 10

    def test_invalid_batch_size(self) -> None:
        """Should raise ValueError for invalid batch_size."""
        with pytest.raises(ValueError, match="batch_size must be positive"):
            EmbedderSettings(batch_size=0)

    def test_invalid_cache_max_size(self) -> None:
        """Should raise ValueError for invalid cache_max_size."""
        with pytest.raises(ValueError, match="cache_max_size must be positive"):
            EmbedderSettings(cache_max_size=0)

    def test_invalid_memory_threshold_mb(self) -> None:
        """Should raise ValueError for invalid memory_threshold_mb."""
        with pytest.raises(ValueError, match="memory_threshold_mb must be positive"):
            EmbedderSettings(memory_threshold_mb=0.0)


class TestReorderSettings:
    """Tests for ReorderSettings."""

    def test_default_initialization(self) -> None:
        """Should initialize with default values."""
        settings = ReorderSettings()

        assert settings.strategy == "sequential"
        assert settings.similarity_threshold == 0.5

    def test_invalid_strategy(self) -> None:
        """Should raise ValueError for invalid strategy."""
        with pytest.raises(ValueError, match="strategy must be"):
            ReorderSettings(strategy="invalid")

    def test_invalid_similarity_threshold(self) -> None:
        """Should raise ValueError for invalid similarity_threshold."""
        with pytest.raises(ValueError, match="similarity_threshold must be in"):
            ReorderSettings(similarity_threshold=1.5)


class TestSearchSettings:
    """Tests for SearchSettings."""

    def test_default_initialization(self) -> None:
        """Should initialize with default values."""
        settings = SearchSettings()

        assert settings.top_k == 5
        assert settings.min_similarity == 0.5
        assert settings.output_format == "text"

    def test_invalid_top_k(self) -> None:
        """Should raise ValueError for invalid top_k."""
        with pytest.raises(ValueError, match="top_k must be positive"):
            SearchSettings(top_k=0)

    def test_invalid_min_similarity(self) -> None:
        """Should raise ValueError for invalid min_similarity (covers lines 124-126)."""
        with pytest.raises(ValueError, match="min_similarity must be in"):
            SearchSettings(min_similarity=1.5)

    def test_invalid_output_format(self) -> None:
        """Should raise ValueError for invalid output_format."""
        with pytest.raises(ValueError, match="output_format must be"):
            SearchSettings(output_format="invalid")


class TestDedupSettings:
    """Tests for DedupSettings."""

    def test_default_initialization(self) -> None:
        """Should initialize with default values."""
        settings = DedupSettings()

        assert settings.similarity_threshold == 0.85
        assert settings.selection_strategy == "first"
        assert settings.use_llm is False

    def test_invalid_similarity_threshold(self) -> None:
        """Should raise ValueError for invalid similarity_threshold (covers lines 145-148)."""
        with pytest.raises(ValueError, match="similarity_threshold must be in"):
            DedupSettings(similarity_threshold=1.5)

    def test_invalid_selection_strategy(self) -> None:
        """Should raise ValueError for invalid selection_strategy."""
        with pytest.raises(ValueError, match="selection_strategy must be"):
            DedupSettings(selection_strategy="invalid")


class TestSettings:
    """Tests for Settings."""

    def test_default_initialization(self) -> None:
        """Should initialize with default sub-settings."""
        settings = Settings()

        assert isinstance(settings.preprocessor, PreprocessorSettings)
        assert isinstance(settings.splitter, SplitterSettings)
        assert isinstance(settings.embedder, EmbedderSettings)

    def test_to_dict(self) -> None:
        """Should convert to dictionary."""
        settings = Settings()
        result = settings.to_dict()

        assert "preprocessor" in result
        assert "splitter" in result
        assert "embedder" in result
        assert "reorder" in result
        assert "search" in result
        assert "dedup" in result

    def test_to_dict_converts_tuples_to_lists(self) -> None:
        """Should convert header tuples to lists for YAML/JSON compatibility."""
        settings = Settings()
        result = settings.to_dict()

        # headers_to_split_on should be lists, not tuples
        headers = result["splitter"]["headers_to_split_on"]
        for header in headers:
            assert isinstance(header, list), f"Expected list, got {type(header)}"

    def test_from_dict_empty(self) -> None:
        """Should create Settings from empty dict (uses defaults)."""
        settings = Settings.from_dict({})

        assert isinstance(settings.preprocessor, PreprocessorSettings)
        assert settings.embedder.model_name == "embeddinggemma"

    def test_from_dict_with_values(self) -> None:
        """Should create Settings from dict with custom values."""
        config_dict = {
            "embedder": {"model_name": "custom_model", "batch_size": 20},
            "search": {"top_k": 10},
        }

        settings = Settings.from_dict(config_dict)

        assert settings.embedder.model_name == "custom_model"
        assert settings.embedder.batch_size == 20
        assert settings.search.top_k == 10


class TestApplyEnvOverrides:
    """Tests for _apply_env_overrides function."""

    def test_no_env_overrides(self) -> None:
        """Should return config unchanged when no env vars set."""
        config_dict = {"embedder": {"model_name": "test"}}

        with patch.dict(os.environ, {}, clear=True):
            result = _apply_env_overrides(config_dict.copy())

        assert result == config_dict

    def test_env_override_string(self) -> None:
        """Should override with string value from env var."""
        config_dict = {"embedder": {"model_name": "test"}}

        env_vars = {"MARKDOWN_REALLOCATOR_EMBEDDER_MODEL_NAME": "new_model"}
        with patch.dict(os.environ, env_vars, clear=True):
            result = _apply_env_overrides(config_dict.copy())

        assert result["embedder"]["model_name"] == "new_model"

    def test_env_override_json_number(self) -> None:
        """Should parse JSON numbers from env var."""
        config_dict = {"search": {"top_k": 5}}

        env_vars = {"MARKDOWN_REALLOCATOR_SEARCH_TOP_K": "10"}
        with patch.dict(os.environ, env_vars, clear=True):
            result = _apply_env_overrides(config_dict.copy())

        assert result["search"]["top_k"] == 10
        assert isinstance(result["search"]["top_k"], int)

    def test_env_override_invalid_format_ignored(self) -> None:
        """Should ignore env vars with invalid format."""
        config_dict = {"embedder": {"model_name": "test"}}

        # Missing section (only one underscore after prefix)
        env_vars = {"MARKDOWN_REALLOCATOR_INVALID": "value"}
        with patch.dict(os.environ, env_vars, clear=True):
            result = _apply_env_overrides(config_dict.copy())

        # Config should be unchanged
        assert result == config_dict

    def test_env_override_unknown_section_ignored(self) -> None:
        """Should ignore env vars with unknown section."""
        config_dict = {"embedder": {"model_name": "test"}}

        env_vars = {"MARKDOWN_REALLOCATOR_UNKNOWN_KEY": "value"}
        with patch.dict(os.environ, env_vars, clear=True):
            result = _apply_env_overrides(config_dict.copy())

        # Config should be unchanged
        assert result == config_dict

    def test_env_override_with_existing_section_updates(self) -> None:
        """Should update existing section without creating duplicate."""
        # Line 283 is actually unreachable defensive code - line 267 already checks
        # if section doesn't exist and continues. This test verifies the normal path.
        config_dict = {"embedder": {"batch_size": 5}}

        # Set an env var for an existing section
        env_vars = {"MARKDOWN_REALLOCATOR_EMBEDDER_MODEL_NAME": "new_model"}
        with patch.dict(os.environ, env_vars, clear=True):
            result = _apply_env_overrides(config_dict)

        # Section should be updated, not duplicated
        assert result["embedder"]["model_name"] == "new_model"
        assert result["embedder"]["batch_size"] == 5  # Original value preserved


class TestLoadConfigFile:
    """Tests for _load_config_file function."""

    def test_load_json_file(self) -> None:
        """Should load JSON config file."""
        config_data = {"embedder": {"model_name": "test_model"}}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            temp_path = Path(f.name)

        try:
            result = _load_config_file(temp_path)
            assert result == config_data
        finally:
            temp_path.unlink()

    def test_load_yaml_file(self) -> None:
        """Should load YAML config file."""
        yaml_content = """
embedder:
  model_name: test_model
  batch_size: 20
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write(yaml_content)
            temp_path = Path(f.name)

        try:
            result = _load_config_file(temp_path)
            assert result["embedder"]["model_name"] == "test_model"
            assert result["embedder"]["batch_size"] == 20
        finally:
            temp_path.unlink()

    def test_unsupported_file_format_raises(self) -> None:
        """Should raise ValueError for unsupported file format."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            temp_path = Path(f.name)

        try:
            with pytest.raises(ValueError, match="Unsupported config file format"):
                _load_config_file(temp_path)
        finally:
            temp_path.unlink()


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_with_explicit_path(self) -> None:
        """Should load config from explicit path."""
        config_data = {"embedder": {"model_name": "test_model"}}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            temp_path = Path(f.name)

        try:
            settings = load_config(temp_path)
            assert settings.embedder.model_name == "test_model"
        finally:
            temp_path.unlink()

    def test_load_with_nonexistent_path_raises(self) -> None:
        """Should raise FileNotFoundError for nonexistent path."""
        with pytest.raises(FileNotFoundError):
            load_config("/nonexistent/path/config.yaml")

    def test_load_without_path_uses_defaults(self) -> None:
        """Should use default settings when no config file found (covers line 341)."""
        # Ensure no config files exist in standard locations
        with patch("pathlib.Path.exists", return_value=False):
            settings = load_config(None)

        # Should return Settings with defaults
        assert isinstance(settings, Settings)
        assert settings.embedder.model_name == "embeddinggemma"


class TestSaveConfig:
    """Tests for save_config function."""

    def test_save_json(self) -> None:
        """Should save config as JSON."""
        settings = Settings()

        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = Path(tmpdir) / "config.json"
            save_config(settings, save_path)

            assert save_path.exists()
            with open(save_path) as f:
                loaded = json.load(f)

            assert "embedder" in loaded
            assert loaded["embedder"]["model_name"] == "embeddinggemma"

    def test_save_yaml(self) -> None:
        """Should save config as YAML."""
        settings = Settings()

        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = Path(tmpdir) / "config.yaml"
            save_config(settings, save_path)

            assert save_path.exists()

            # Reload to verify
            loaded_settings = load_config(save_path)
            assert loaded_settings.embedder.model_name == settings.embedder.model_name

    def test_save_creates_parent_directory(self) -> None:
        """Should create parent directory if it doesn't exist."""
        settings = Settings()

        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = Path(tmpdir) / "nested" / "dir" / "config.json"
            save_config(settings, save_path)

            assert save_path.exists()
            assert save_path.parent.exists()

    def test_save_unsupported_format_raises(self) -> None:
        """Should raise ValueError for unsupported file format."""
        settings = Settings()

        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = Path(tmpdir) / "config.txt"

            with pytest.raises(ValueError, match="Unsupported config file format"):
                save_config(settings, save_path)


class TestBranchCoverage:
    """Tests specifically for branch coverage."""

    def test_to_dict_with_non_tuple_headers(self) -> None:
        """Should handle headers_to_split_on that are already lists (branch 203->209)."""
        # Create settings with list headers (not tuples)
        settings = Settings()
        # Force headers to be lists (simulating YAML/JSON load)
        settings.splitter.headers_to_split_on = [["#", "h1"], ["##", "h2"]]  # type: ignore

        result = settings.to_dict()

        # Branch 203->209: Should convert to lists for YAML/JSON compatibility
        headers = result["splitter"]["headers_to_split_on"]
        assert all(isinstance(h, list) for h in headers)

    def test_load_config_with_invalid_file_raises(self) -> None:
        """Should raise ValueError when config file is invalid (covers lines 351-352)."""
        # Create a JSON file with invalid content
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("invalid json content {{{")
            temp_path = Path(f.name)

        try:
            # Should raise ValueError because JSON parsing fails (line 387)
            with pytest.raises(ValueError, match="Failed to load config"):
                load_config(temp_path)
        finally:
            temp_path.unlink()

    def test_load_config_with_validation_error_raises(self) -> None:
        """Should raise ValueError when Settings validation fails (covers lines 124, 145)."""
        # Create a valid JSON file but with invalid settings values
        config_data = {"embedder": {"batch_size": -1}}  # Invalid: must be positive

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            temp_path = Path(f.name)

        try:
            # Should raise ValueError because batch_size validation fails (line 153)
            with pytest.raises(ValueError, match="Invalid config"):
                load_config(temp_path)
        finally:
            temp_path.unlink()

    def test_load_config_search_paths(self) -> None:
        """Should search through multiple paths when no explicit path given."""
        # This test verifies the search path logic (lines 334-338)
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a config file in a temporary location
            config_path = Path(tmpdir) / "markdown_reallocator.yaml"
            settings = Settings()
            save_config(settings, config_path)

            # Mock Path.cwd() to return our temp directory
            with patch("pathlib.Path.cwd", return_value=Path(tmpdir)):
                # This should find the config file in the "current directory"
                loaded_settings = load_config(None)

            # Should successfully load the config
            assert isinstance(loaded_settings, Settings)

    def test_save_config_with_write_error(self) -> None:
        """Should raise ValueError when write fails (line 382)."""
        settings = Settings()

        # Try to write to a path that will fail (e.g., read-only parent)
        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = Path(tmpdir) / "config.json"

            # Mock write_text to raise an error
            with patch.object(Path, "write_text", side_effect=OSError("Write failed")):
                with pytest.raises(ValueError, match="Failed to save config"):
                    save_config(settings, save_path)
