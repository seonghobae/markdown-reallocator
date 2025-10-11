"""Configuration system for Markdown Reallocator.

This module provides a centralized Settings dataclass and functions for loading
configuration from YAML/JSON files with environment variable overrides.
"""

import json
import logging
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class PreprocessorSettings:
    """Settings for markdown preprocessing."""

    max_title_length: int = 80
    require_empty_lines: bool = True
    min_capitalization_ratio: float = 0.1
    detect_title_case: bool = True
    preserve_code_blocks: bool = True
    preserve_lists: bool = True
    preserve_tables: bool = True
    log_ambiguous_cases: bool = True

    def __post_init__(self) -> None:
        """Validate settings."""
        if self.max_title_length < 1:
            raise ValueError(
                f"max_title_length must be positive, got {self.max_title_length}"
            )
        if not 0 <= self.min_capitalization_ratio <= 1:
            raise ValueError(
                f"min_capitalization_ratio must be in [0, 1], "
                f"got {self.min_capitalization_ratio}"
            )


@dataclass
class SplitterSettings:
    """Settings for markdown splitting."""

    headers_to_split_on: list[tuple[str, str]] = field(
        default_factory=lambda: [("#", "h1"), ("##", "h2"), ("###", "h3")]
    )
    max_tokens_per_chunk: int = 1000

    def __post_init__(self) -> None:
        """Validate settings."""
        if self.max_tokens_per_chunk < 1:
            raise ValueError(
                f"max_tokens_per_chunk must be positive, got {self.max_tokens_per_chunk}"
            )

        # Convert headers_to_split_on to list of tuples if they are lists
        # (can happen when loading from YAML/JSON)
        self.headers_to_split_on = [
            tuple(h) if isinstance(h, list) else h
            for h in self.headers_to_split_on
        ]


@dataclass
class EmbedderSettings:
    """Settings for embedding generation."""

    model_name: str = "embeddinggemma"
    cache_enabled: bool = True
    cache_max_size: int = 1000
    batch_size: int = 10
    memory_threshold_mb: float = 1500.0

    def __post_init__(self) -> None:
        """Validate settings."""
        if self.batch_size < 1:
            raise ValueError(f"batch_size must be positive, got {self.batch_size}")
        if self.cache_max_size < 1:
            raise ValueError(
                f"cache_max_size must be positive, got {self.cache_max_size}"
            )
        if self.memory_threshold_mb <= 0:
            raise ValueError(
                f"memory_threshold_mb must be positive, got {self.memory_threshold_mb}"
            )


@dataclass
class ReorderSettings:
    """Settings for chunk reordering."""

    strategy: str = "sequential"  # "sequential" or "cluster"
    similarity_threshold: float = 0.5

    def __post_init__(self) -> None:
        """Validate settings."""
        if self.strategy not in ("sequential", "cluster"):
            raise ValueError(
                f"strategy must be 'sequential' or 'cluster', got '{self.strategy}'"
            )
        if not 0.0 <= self.similarity_threshold <= 1.0:
            raise ValueError(
                f"similarity_threshold must be in [0.0, 1.0], "
                f"got {self.similarity_threshold}"
            )


@dataclass
class SearchSettings:
    """Settings for semantic search."""

    top_k: int = 5
    min_similarity: float = 0.5
    output_format: str = "text"  # "text" or "json"

    def __post_init__(self) -> None:
        """Validate settings."""
        if self.top_k <= 0:
            raise ValueError(f"top_k must be positive, got {self.top_k}")
        if not 0.0 <= self.min_similarity <= 1.0:
            raise ValueError(
                f"min_similarity must be in [0.0, 1.0], got {self.min_similarity}"
            )
        if self.output_format not in ("text", "json"):
            raise ValueError(
                f"output_format must be 'text' or 'json', got '{self.output_format}'"
            )


@dataclass
class DedupSettings:
    """Settings for deduplication."""

    similarity_threshold: float = 0.85
    selection_strategy: str = "first"  # "first", "longest", or "best_metadata"
    use_llm: bool = False
    dry_run: bool = False

    def __post_init__(self) -> None:
        """Validate settings."""
        if not 0.0 <= self.similarity_threshold <= 1.0:
            raise ValueError(
                f"similarity_threshold must be in [0.0, 1.0], "
                f"got {self.similarity_threshold}"
            )
        if self.selection_strategy not in ("first", "longest", "best_metadata"):
            raise ValueError(
                f"selection_strategy must be 'first', 'longest', or 'best_metadata', "
                f"got '{self.selection_strategy}'"
            )


@dataclass
class Settings:
    """Complete configuration for Markdown Reallocator.

    This dataclass aggregates all module-specific settings into a single
    configuration object that can be loaded from YAML/JSON files or
    constructed programmatically.

    Attributes:
        preprocessor: Preprocessing configuration
        splitter: Chunking configuration
        embedder: Embedding generation configuration
        reorder: Reordering configuration
        search: Search configuration
        dedup: Deduplication configuration

    Examples:
        >>> # Load from file
        >>> settings = load_config("config.yaml")
        >>> # Use with modules
        >>> preprocessor = MarkdownPreprocessor(settings.preprocessor)
        >>> embedder = Embedder(**asdict(settings.embedder))
    """

    preprocessor: PreprocessorSettings = field(default_factory=PreprocessorSettings)
    splitter: SplitterSettings = field(default_factory=SplitterSettings)
    embedder: EmbedderSettings = field(default_factory=EmbedderSettings)
    reorder: ReorderSettings = field(default_factory=ReorderSettings)
    search: SearchSettings = field(default_factory=SearchSettings)
    dedup: DedupSettings = field(default_factory=DedupSettings)

    def to_dict(self) -> dict[str, Any]:
        """Convert settings to dictionary.

        Returns:
            Dictionary representation with nested structure
        """
        result = {
            "preprocessor": asdict(self.preprocessor),
            "splitter": asdict(self.splitter),
            "embedder": asdict(self.embedder),
            "reorder": asdict(self.reorder),
            "search": asdict(self.search),
            "dedup": asdict(self.dedup),
        }

        # Convert tuples to lists for YAML/JSON compatibility
        if "splitter" in result and "headers_to_split_on" in result["splitter"]:
            result["splitter"]["headers_to_split_on"] = [
                list(h) if isinstance(h, tuple) else h
                for h in result["splitter"]["headers_to_split_on"]
            ]

        return result

    @classmethod
    def from_dict(cls, config_dict: dict[str, Any]) -> "Settings":
        """Create settings from dictionary.

        Args:
            config_dict: Dictionary with nested configuration

        Returns:
            Settings instance

        Raises:
            ValueError: If config_dict contains invalid values
        """
        return cls(
            preprocessor=PreprocessorSettings(
                **config_dict.get("preprocessor", {})
            ),
            splitter=SplitterSettings(**config_dict.get("splitter", {})),
            embedder=EmbedderSettings(**config_dict.get("embedder", {})),
            reorder=ReorderSettings(**config_dict.get("reorder", {})),
            search=SearchSettings(**config_dict.get("search", {})),
            dedup=DedupSettings(**config_dict.get("dedup", {})),
        )


def _apply_env_overrides(config_dict: dict[str, Any]) -> dict[str, Any]:
    """Apply environment variable overrides to config dictionary.

    Environment variables use the pattern: MARKDOWN_REALLOCATOR_<SECTION>_<KEY>
    Examples:
        MARKDOWN_REALLOCATOR_EMBEDDER_MODEL_NAME=embeddinggemma
        MARKDOWN_REALLOCATOR_SEARCH_TOP_K=10

    Args:
        config_dict: Configuration dictionary to modify

    Returns:
        Modified configuration dictionary
    """
    env_prefix = "MARKDOWN_REALLOCATOR_"

    for env_key, env_value in os.environ.items():
        if not env_key.startswith(env_prefix):
            continue

        # Parse environment variable name
        # Example: MARKDOWN_REALLOCATOR_EMBEDDER_MODEL_NAME
        parts = env_key[len(env_prefix) :].lower().split("_", 1)
        if len(parts) != 2:
            logger.warning(f"Ignoring invalid env var format: {env_key}")
            continue

        section = parts[0]  # e.g., "embedder"
        key = parts[1]  # e.g., "model_name"

        # Check if section exists
        if section not in config_dict:
            logger.warning(f"Unknown config section in env var: {section}")
            continue

        # Parse value type
        parsed_value: Any = env_value

        # Try to parse as JSON for complex types
        try:
            parsed_value = json.loads(env_value)
        except json.JSONDecodeError:
            # Keep as string if not valid JSON
            pass

        # Update config
        if section not in config_dict:
            config_dict[section] = {}

        config_dict[section][key] = parsed_value
        logger.debug(f"Applied env override: {section}.{key} = {parsed_value}")

    return config_dict


def load_config(path: str | Path | None = None) -> Settings:
    """Load configuration from file with environment variable overrides.

    Searches for configuration files in the following order:
    1. Provided path (if given)
    2. Current directory: ./markdown_reallocator.yaml or ./markdown_reallocator.json
    3. Home directory: ~/.config/markdown_reallocator/config.yaml
    4. Package default: markdown_reallocator/config/default.yaml

    Environment variables override file settings using the pattern:
        MARKDOWN_REALLOCATOR_<SECTION>_<KEY>=value

    Args:
        path: Optional path to config file (YAML or JSON)

    Returns:
        Settings instance

    Raises:
        FileNotFoundError: If path is provided but doesn't exist
        ValueError: If config file is invalid
    """
    config_dict: dict[str, Any] = {}

    # Try to find and load config file
    if path:
        # Explicit path provided
        config_path = Path(path)
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        config_dict = _load_config_file(config_path)
        logger.info(f"Loaded config from: {config_path}")

    else:
        # Search for config in standard locations
        search_paths = [
            Path.cwd() / "markdown_reallocator.yaml",
            Path.cwd() / "markdown_reallocator.json",
            Path.home() / ".config" / "markdown_reallocator" / "config.yaml",
            Path(__file__).parent / "default.yaml",
        ]

        for search_path in search_paths:
            if search_path.exists():
                config_dict = _load_config_file(search_path)
                logger.info(f"Loaded config from: {search_path}")
                break
        else:
            # No config file found, use defaults
            logger.info("No config file found, using defaults")

    # Apply environment variable overrides
    config_dict = _apply_env_overrides(config_dict)

    # Create Settings instance
    try:
        settings = Settings.from_dict(config_dict)
        logger.debug("Config validation passed")
        return settings
    except Exception as e:
        raise ValueError(f"Invalid config: {e}") from e


def _load_config_file(path: Path) -> dict[str, Any]:
    """Load configuration from YAML or JSON file.

    Args:
        path: Path to config file

    Returns:
        Configuration dictionary

    Raises:
        ValueError: If file format is unsupported or content is invalid
    """
    suffix = path.suffix.lower()

    try:
        content = path.read_text(encoding="utf-8")

        if suffix in (".yaml", ".yml"):
            import yaml

            config_dict = yaml.safe_load(content)
        elif suffix == ".json":
            config_dict = json.loads(content)
        else:
            raise ValueError(f"Unsupported config file format: {suffix}")

        if not isinstance(config_dict, dict):
            raise ValueError("Config file must contain a dictionary at root level")

        return config_dict

    except Exception as e:
        raise ValueError(f"Failed to load config from {path}: {e}") from e


def save_config(settings: Settings, path: str | Path) -> None:
    """Save configuration to YAML or JSON file.

    Args:
        settings: Settings instance to save
        path: Output file path (extension determines format)

    Raises:
        ValueError: If file format is unsupported
    """
    path = Path(path)
    suffix = path.suffix.lower()

    config_dict = settings.to_dict()

    try:
        if suffix in (".yaml", ".yml"):
            import yaml

            content = yaml.dump(config_dict, default_flow_style=False, sort_keys=False)
        elif suffix == ".json":
            content = json.dumps(config_dict, indent=2, ensure_ascii=False)
        else:
            raise ValueError(f"Unsupported config file format: {suffix}")

        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        # Write file
        path.write_text(content, encoding="utf-8")
        logger.info(f"Saved config to: {path}")

    except Exception as e:
        raise ValueError(f"Failed to save config to {path}: {e}") from e
