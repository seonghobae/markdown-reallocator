"""Smoke tests for module imports.

These tests verify that all modules can be imported without errors.
They should run quickly (<1 second) and catch basic import issues.
"""

import pytest


def test_import_core_modules():
    """Test that core modules can be imported."""
    from markdown_reallocator.core import embedder, preprocessor, splitter

    assert embedder is not None
    assert preprocessor is not None
    assert splitter is not None


def test_import_models():
    """Test that data models can be imported."""
    from markdown_reallocator.models import chunk, embedding

    assert chunk is not None
    assert embedding is not None


def test_import_utils():
    """Test that utility modules can be imported."""
    from markdown_reallocator.utils import cache, memory, similarity

    assert cache is not None
    assert memory is not None
    assert similarity is not None


def test_import_modules():
    """Test that application modules can be imported."""
    from markdown_reallocator.modules import dedup, reorder, search

    assert dedup is not None
    assert reorder is not None
    assert search is not None


def test_import_config():
    """Test that config system can be imported."""
    from markdown_reallocator.config import Settings, load_config

    assert Settings is not None
    assert load_config is not None


def test_import_cli():
    """Test that CLI can be imported."""
    from markdown_reallocator.cli import main

    assert main is not None
    assert main.app is not None


def test_package_version():
    """Test that package version is accessible."""
    from markdown_reallocator import __version__

    assert __version__ is not None
    assert isinstance(__version__, str)
    assert len(__version__) > 0


def test_all_public_apis():
    """Test that all __all__ exports work."""
    # Core
    from markdown_reallocator.core import __all__ as core_all

    assert len(core_all) > 0

    # Models
    from markdown_reallocator.models import __all__ as models_all

    assert len(models_all) > 0

    # Modules
    from markdown_reallocator.modules import __all__ as modules_all

    assert len(modules_all) > 0

    # Utils
    from markdown_reallocator.utils import __all__ as utils_all

    assert len(utils_all) > 0

    # Config
    from markdown_reallocator.config import __all__ as config_all

    assert len(config_all) > 0
