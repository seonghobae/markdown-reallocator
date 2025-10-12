"""Tests for CLI commands."""

import json
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from markdown_reallocator.cli.main import app

runner = CliRunner()


@pytest.fixture
def sample_markdown(tmp_path):
    """Create a sample markdown file."""
    md_file = tmp_path / "sample.md"
    md_file.write_text(
        """**Introduction**

This is a test document.

**Section 1**

Content for section 1.

## Section 2

Content for section 2.
""",
        encoding="utf-8",
    )
    return md_file


@pytest.fixture
def sample_chunks_json(tmp_path):
    """Create a sample chunks JSON file."""
    chunks_file = tmp_path / "chunks.json"
    chunks_data = [
        {
            "chunk_id": "abc12345",
            "content": "# Introduction\n\nTest content",
            "metadata": {
                "h1": "Introduction",
                "h2": None,
                "h3": None,
                "original_position": 0,
            },
        },
        {
            "chunk_id": "def67890",
            "content": "## Section\n\nMore content",
            "metadata": {
                "h1": "Introduction",
                "h2": "Section",
                "h3": None,
                "original_position": 1,
            },
        },
    ]
    chunks_file.write_text(json.dumps(chunks_data, indent=2), encoding="utf-8")
    return chunks_file


class TestVersionCommand:
    """Tests for version command."""

    def test_version_flag(self):
        """Test --version flag shows version."""
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "markdown-reallocator version" in result.stdout


class TestPreprocessCommand:
    """Tests for preprocess command."""

    def test_preprocess_to_stdout(self, sample_markdown):
        """Test preprocessing with output to stdout."""
        result = runner.invoke(app, ["preprocess", str(sample_markdown)])
        assert result.exit_code == 0
        assert "## Introduction" in result.stdout
        assert "## Section 1" in result.stdout

    def test_preprocess_to_file(self, sample_markdown, tmp_path):
        """Test preprocessing with output to file."""
        output_file = tmp_path / "output.md"
        result = runner.invoke(
            app,
            ["preprocess", str(sample_markdown), "--output", str(output_file)],
        )
        assert result.exit_code == 0
        assert output_file.exists()

        # Verify output content
        output_content = output_file.read_text(encoding="utf-8")
        assert "## Introduction" in output_content
        assert "## Section 1" in output_content

    def test_preprocess_no_detect_bold_headers(self, sample_markdown):
        """Test preprocessing with bold header detection disabled."""
        result = runner.invoke(
            app,
            ["preprocess", str(sample_markdown), "--no-detect-bold-headers"],
        )
        assert result.exit_code == 0
        # Bold should remain as-is
        assert "**Introduction**" in result.stdout

    def test_preprocess_nonexistent_file(self):
        """Test preprocessing with nonexistent input file."""
        result = runner.invoke(app, ["preprocess", "/nonexistent/file.md"])
        assert result.exit_code != 0


class TestSplitCommand:
    """Tests for split command."""

    def test_split_to_stdout(self, sample_markdown):
        """Test splitting with output to stdout."""
        result = runner.invoke(app, ["split", str(sample_markdown)])
        assert result.exit_code == 0
        # Output should be valid JSON
        assert "[" in result.stdout
        assert '"chunk_id"' in result.stdout

    def test_split_to_file(self, sample_markdown, tmp_path):
        """Test splitting with output to JSON file."""
        output_file = tmp_path / "chunks.json"
        result = runner.invoke(
            app,
            ["split", str(sample_markdown), "--output", str(output_file)],
        )
        assert result.exit_code == 0
        assert output_file.exists()

        # Verify JSON is valid
        chunks_data = json.loads(output_file.read_text())
        assert isinstance(chunks_data, list)
        assert len(chunks_data) > 0
        assert "chunk_id" in chunks_data[0]
        assert "content" in chunks_data[0]
        assert "metadata" in chunks_data[0]

    def test_split_with_max_tokens(self, sample_markdown, tmp_path):
        """Test splitting with custom max tokens."""
        output_file = tmp_path / "chunks.json"
        result = runner.invoke(
            app,
            [
                "split",
                str(sample_markdown),
                "--output",
                str(output_file),
                "--max-tokens",
                "500",
            ],
        )
        assert result.exit_code == 0


class TestEmbedCommand:
    """Tests for embed command."""

    @patch("markdown_reallocator.core.embedder.Embedder")
    def test_embed_basic(self, mock_embedder_class, sample_chunks_json, tmp_path):
        """Test embedding generation."""
        # Mock embedder
        mock_embedder = MagicMock()
        mock_embedder.embed_batch.return_value = []
        mock_embedder.get_cache_stats.return_value = {
            "hits": 10,
            "misses": 5,
            "hit_rate": 0.67,
        }
        mock_embedder_class.return_value = mock_embedder

        output_file = tmp_path / "embeddings.npz"
        result = runner.invoke(
            app,
            [
                "embed",
                str(sample_chunks_json),
                "--output",
                str(output_file),
            ],
        )
        assert result.exit_code == 0
        assert mock_embedder.embed_batch.called

    @patch("markdown_reallocator.core.embedder.Embedder")
    def test_embed_with_custom_model(
        self, mock_embedder_class, sample_chunks_json, tmp_path
    ):
        """Test embedding with custom model."""
        mock_embedder = MagicMock()
        mock_embedder.embed_batch.return_value = []
        mock_embedder.get_cache_stats.return_value = None
        mock_embedder_class.return_value = mock_embedder

        output_file = tmp_path / "embeddings.npz"
        result = runner.invoke(
            app,
            [
                "embed",
                str(sample_chunks_json),
                "--output",
                str(output_file),
                "--model",
                "custom-model",
            ],
        )
        assert result.exit_code == 0
        mock_embedder_class.assert_called_with(
            model_name="custom-model", cache_enabled=True
        )

    @patch("markdown_reallocator.core.embedder.Embedder")
    def test_embed_no_cache(self, mock_embedder_class, sample_chunks_json, tmp_path):
        """Test embedding with cache disabled."""
        mock_embedder = MagicMock()
        mock_embedder.embed_batch.return_value = []
        mock_embedder.get_cache_stats.return_value = None
        mock_embedder_class.return_value = mock_embedder

        output_file = tmp_path / "embeddings.npz"
        result = runner.invoke(
            app,
            [
                "embed",
                str(sample_chunks_json),
                "--output",
                str(output_file),
                "--no-cache",
            ],
        )
        assert result.exit_code == 0
        mock_embedder_class.assert_called_with(model_name="embeddinggemma", cache_enabled=False)


class TestSearchCommand:
    """Tests for search command."""

    @patch("markdown_reallocator.modules.search.SearchModule")
    @patch("markdown_reallocator.core.embedder.Embedder")
    def test_search_basic(
        self,
        mock_embedder_class,
        mock_search_class,
        sample_chunks_json,
        tmp_path,
    ):
        """Test basic search."""
        # Mock embedder
        mock_embedder = MagicMock()
        mock_embedder_class.return_value = mock_embedder

        # Mock search
        mock_search = MagicMock()
        mock_search.search.return_value = []
        mock_search.format_results.return_value = "No results found.\n"
        mock_search_class.return_value = mock_search

        # Create dummy embeddings file
        embeddings_file = tmp_path / "embeddings.npz"
        embeddings_file.write_bytes(b"")  # Dummy file

        result = runner.invoke(
            app,
            [
                "search",
                "test query",
                str(sample_chunks_json),
                str(embeddings_file),
            ],
        )
        assert result.exit_code == 0
        assert mock_search.search.called
        assert mock_search.format_results.called

    @patch("markdown_reallocator.modules.search.SearchModule")
    @patch("markdown_reallocator.core.embedder.Embedder")
    def test_search_with_options(
        self,
        mock_embedder_class,
        mock_search_class,
        sample_chunks_json,
        tmp_path,
    ):
        """Test search with custom options."""
        mock_embedder = MagicMock()
        mock_embedder_class.return_value = mock_embedder

        mock_search = MagicMock()
        mock_search.search.return_value = []
        mock_search.format_results.return_value = "{}"
        mock_search_class.return_value = mock_search

        embeddings_file = tmp_path / "embeddings.npz"
        embeddings_file.write_bytes(b"")

        result = runner.invoke(
            app,
            [
                "search",
                "test query",
                str(sample_chunks_json),
                str(embeddings_file),
                "--top-k",
                "10",
                "--min-similarity",
                "0.7",
                "--format",
                "json",
            ],
        )
        assert result.exit_code == 0
        mock_search_class.assert_called_with(
            embedder=mock_embedder,
            top_k=10,
            min_similarity=0.7,
            output_format="json",
        )


class TestReorderCommand:
    """Tests for reorder command."""

    @patch("markdown_reallocator.modules.reorder.ReorderModule")
    @patch("markdown_reallocator.core.embedder.Embedder")
    def test_reorder_basic(
        self,
        mock_embedder_class,
        mock_reorder_class,
        sample_chunks_json,
        tmp_path,
    ):
        """Test basic reordering."""
        mock_embedder = MagicMock()
        mock_embedder_class.return_value = mock_embedder

        mock_reorder = MagicMock()
        mock_reorder.reorder.return_value = []
        mock_reorder.reconstruct_markdown.return_value = "# Reordered\n"
        mock_reorder_class.return_value = mock_reorder

        embeddings_file = tmp_path / "embeddings.npz"
        embeddings_file.write_bytes(b"")

        output_file = tmp_path / "reordered.md"
        result = runner.invoke(
            app,
            [
                "reorder",
                str(sample_chunks_json),
                str(embeddings_file),
                "--output",
                str(output_file),
            ],
        )
        assert result.exit_code == 0
        assert output_file.exists()

    @patch("markdown_reallocator.modules.reorder.ReorderModule")
    @patch("markdown_reallocator.core.embedder.Embedder")
    def test_reorder_with_strategy(
        self,
        mock_embedder_class,
        mock_reorder_class,
        sample_chunks_json,
        tmp_path,
    ):
        """Test reordering with cluster strategy."""
        mock_embedder = MagicMock()
        mock_embedder_class.return_value = mock_embedder

        mock_reorder = MagicMock()
        mock_reorder.reorder.return_value = []
        mock_reorder.reconstruct_markdown.return_value = "# Reordered\n"
        mock_reorder_class.return_value = mock_reorder

        embeddings_file = tmp_path / "embeddings.npz"
        embeddings_file.write_bytes(b"")

        output_file = tmp_path / "reordered.md"
        result = runner.invoke(
            app,
            [
                "reorder",
                str(sample_chunks_json),
                str(embeddings_file),
                "--output",
                str(output_file),
                "--strategy",
                "cluster",
            ],
        )
        assert result.exit_code == 0
        mock_reorder_class.assert_called_with(strategy="cluster")


class TestDedupCommand:
    """Tests for dedup command."""

    @patch("markdown_reallocator.modules.dedup.DeduplicationModule")
    @patch("markdown_reallocator.core.embedder.Embedder")
    def test_dedup_basic(
        self,
        mock_embedder_class,
        mock_dedup_class,
        sample_chunks_json,
        tmp_path,
    ):
        """Test basic deduplication."""
        mock_embedder = MagicMock()
        mock_embedder_class.return_value = mock_embedder

        mock_dedup = MagicMock()
        mock_dedup.deduplicate.return_value = (
            [],
            MagicMock(
                original_count=2,
                deduplicated_count=2,
                removed_count=0,
            ),
        )
        mock_dedup.format_report.return_value = "Dedup Report\n"
        mock_dedup_class.return_value = mock_dedup

        embeddings_file = tmp_path / "embeddings.npz"
        embeddings_file.write_bytes(b"")

        output_file = tmp_path / "deduplicated.json"
        result = runner.invoke(
            app,
            [
                "dedup",
                str(sample_chunks_json),
                str(embeddings_file),
                "--output",
                str(output_file),
            ],
        )
        assert result.exit_code == 0
        assert output_file.exists()

    @patch("markdown_reallocator.modules.dedup.DeduplicationModule")
    @patch("markdown_reallocator.core.embedder.Embedder")
    def test_dedup_with_options(
        self,
        mock_embedder_class,
        mock_dedup_class,
        sample_chunks_json,
        tmp_path,
    ):
        """Test deduplication with custom options."""
        mock_embedder = MagicMock()
        mock_embedder_class.return_value = mock_embedder

        mock_dedup = MagicMock()
        mock_dedup.deduplicate.return_value = (
            [],
            MagicMock(
                original_count=2,
                deduplicated_count=1,
                removed_count=1,
            ),
        )
        mock_dedup.format_report.return_value = "Dedup Report\n"
        mock_dedup_class.return_value = mock_dedup

        embeddings_file = tmp_path / "embeddings.npz"
        embeddings_file.write_bytes(b"")

        output_file = tmp_path / "deduplicated.json"
        result = runner.invoke(
            app,
            [
                "dedup",
                str(sample_chunks_json),
                str(embeddings_file),
                "--output",
                str(output_file),
                "--threshold",
                "0.9",
                "--strategy",
                "longest",
            ],
        )
        assert result.exit_code == 0
        mock_dedup_class.assert_called_with(
            similarity_threshold=0.9,
            selection_strategy="longest",
            dry_run=False,
        )

    @patch("markdown_reallocator.modules.dedup.DeduplicationModule")
    @patch("markdown_reallocator.core.embedder.Embedder")
    def test_dedup_dry_run(
        self,
        mock_embedder_class,
        mock_dedup_class,
        sample_chunks_json,
        tmp_path,
    ):
        """Test deduplication in dry-run mode."""
        mock_embedder = MagicMock()
        mock_embedder_class.return_value = mock_embedder

        mock_dedup = MagicMock()
        mock_dedup.deduplicate.return_value = (
            [],
            MagicMock(
                original_count=2,
                deduplicated_count=2,
                removed_count=0,
            ),
        )
        mock_dedup.format_report.return_value = "Dedup Report\n"
        mock_dedup_class.return_value = mock_dedup

        embeddings_file = tmp_path / "embeddings.npz"
        embeddings_file.write_bytes(b"")

        output_file = tmp_path / "deduplicated.json"
        result = runner.invoke(
            app,
            [
                "dedup",
                str(sample_chunks_json),
                str(embeddings_file),
                "--output",
                str(output_file),
                "--dry-run",
            ],
        )
        assert result.exit_code == 0
        mock_dedup_class.assert_called_with(
            similarity_threshold=0.85,
            selection_strategy="first",
            dry_run=True,
        )
        # In dry-run mode, output file should not be created
        assert not output_file.exists()


class TestGlobalOptions:
    """Tests for global CLI options."""

    def test_verbose_flag(self, sample_markdown):
        """Test --verbose flag."""
        result = runner.invoke(
            app,
            ["--verbose", "preprocess", str(sample_markdown)],
        )
        assert result.exit_code == 0

    def test_no_color_flag(self, sample_markdown):
        """Test --no-color flag."""
        result = runner.invoke(
            app,
            ["--no-color", "preprocess", str(sample_markdown)],
        )
        assert result.exit_code == 0


class TestErrorHandling:
    """Tests for error handling in CLI."""

    def test_preprocess_with_invalid_file(self):
        """Test preprocessing with invalid input."""
        result = runner.invoke(app, ["preprocess", "/invalid/path.md"])
        assert result.exit_code != 0

    def test_split_with_invalid_file(self):
        """Test splitting with invalid input."""
        result = runner.invoke(app, ["split", "/invalid/path.md"])
        assert result.exit_code != 0

    def test_embed_with_invalid_json(self, tmp_path):
        """Test embedding with invalid JSON."""
        invalid_json = tmp_path / "invalid.json"
        invalid_json.write_text("{invalid json")

        output_file = tmp_path / "output.npz"
        result = runner.invoke(
            app,
            ["embed", str(invalid_json), "--output", str(output_file)],
        )
        assert result.exit_code != 0
