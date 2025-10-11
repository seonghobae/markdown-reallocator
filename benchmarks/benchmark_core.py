"""
Benchmark suite for core Markdown Reallocator operations.

Performance targets from PRD:
- Preprocessing: <1s per 1000 lines
- Embedding: <10s for 50 chunks
- Search: <500ms for 1000 chunks
- Peak GPU memory ≤ 1.8GB
"""

import pytest

from markdown_reallocator.core import Embedder, MarkdownPreprocessor, MarkdownSplitter
from markdown_reallocator.modules import SearchModule


# Test fixtures
@pytest.fixture
def sample_markdown_small() -> str:
    """Generate a small markdown sample (100 lines)."""
    lines = []
    for i in range(20):
        lines.append(f"## Section {i}\n")
        lines.append("\n")
        lines.append(f"This is content for section {i}.\n")
        lines.append("\n")
        lines.append(f"**Bold text** in section {i}.\n")
    return "".join(lines)


@pytest.fixture
def sample_markdown_medium() -> str:
    """Generate a medium markdown sample (1000 lines)."""
    lines = []
    for i in range(200):
        lines.append(f"## Section {i}\n")
        lines.append("\n")
        lines.append(f"This is content for section {i}.\n")
        lines.append("More detailed information here.\n")
        lines.append("\n")
    return "".join(lines)


@pytest.fixture
def sample_markdown_large() -> str:
    """Generate a large markdown sample (5000 lines)."""
    lines = []
    for i in range(1000):
        lines.append(f"## Section {i}\n")
        lines.append("\n")
        lines.append(f"This is content for section {i}.\n")
        lines.append("Additional paragraph with more details.\n")
        lines.append("Even more content to make it realistic.\n")
    return "".join(lines)


class TestPreprocessingPerformance:
    """Benchmark preprocessing operations."""

    def test_preprocess_small_doc(
        self, benchmark: pytest.fixture, sample_markdown_small: str  # type: ignore
    ) -> None:
        """Benchmark preprocessing of small document."""
        preprocessor = MarkdownPreprocessor()
        result = benchmark(preprocessor.preprocess, sample_markdown_small)
        assert len(result) > 0

    def test_preprocess_medium_doc(
        self, benchmark: pytest.fixture, sample_markdown_medium: str  # type: ignore
    ) -> None:
        """Benchmark preprocessing of 1000-line document.

        Target: <1s per 1000 lines
        """
        preprocessor = MarkdownPreprocessor()
        result = benchmark(preprocessor.preprocess, sample_markdown_medium)
        assert len(result) > 0

    def test_preprocess_large_doc(
        self, benchmark: pytest.fixture, sample_markdown_large: str  # type: ignore
    ) -> None:
        """Benchmark preprocessing of 5000-line document."""
        preprocessor = MarkdownPreprocessor()
        result = benchmark(preprocessor.preprocess, sample_markdown_large)
        assert len(result) > 0


class TestSplittingPerformance:
    """Benchmark splitting operations."""

    def test_split_medium_doc(
        self, benchmark: pytest.fixture, sample_markdown_medium: str  # type: ignore
    ) -> None:
        """Benchmark splitting of 1000-line document."""
        splitter = MarkdownSplitter(max_tokens_per_chunk=500)
        result = benchmark(splitter.split, sample_markdown_medium)
        assert len(result) > 0


@pytest.mark.requires_ollama
class TestEmbeddingPerformance:
    """Benchmark embedding operations.

    Requires Ollama to be running with embeddinggemma model.
    """

    @pytest.fixture
    def embedder(self) -> Embedder:
        """Create embedder instance."""
        return Embedder(model_name="embeddinggemma", cache_enabled=False)

    @pytest.fixture
    def chunks_50(self, sample_markdown_medium: str) -> list:
        """Generate ~50 chunks for testing."""
        splitter = MarkdownSplitter(max_tokens_per_chunk=100)
        return splitter.split(sample_markdown_medium)

    def test_embed_single_chunk(
        self, benchmark: pytest.fixture, embedder: Embedder, chunks_50: list  # type: ignore
    ) -> None:
        """Benchmark embedding a single chunk."""
        chunk = chunks_50[0]
        result = benchmark(embedder.embed, chunk.content)
        assert result.vector.shape[0] > 0

    def test_embed_50_chunks_batch(
        self, benchmark: pytest.fixture, embedder: Embedder, chunks_50: list  # type: ignore
    ) -> None:
        """Benchmark batch embedding of 50 chunks.

        Target: <10s for 50 chunks
        """
        result = benchmark(embedder.embed_batch, chunks_50[:50])
        assert len(result) == 50


@pytest.mark.requires_ollama
class TestSearchPerformance:
    """Benchmark search operations."""

    @pytest.fixture
    def search_module_with_1000_chunks(
        self, sample_markdown_large: str
    ) -> SearchModule:
        """Create search module with ~1000 chunks."""
        preprocessor = MarkdownPreprocessor()
        splitter = MarkdownSplitter(max_tokens_per_chunk=100)
        embedder = Embedder(model_name="embeddinggemma", cache_enabled=True)

        # Process document
        clean = preprocessor.preprocess(sample_markdown_large)
        chunks = splitter.split(clean)
        embedded = embedder.embed_batch(chunks)

        return SearchModule(embedded)

    def test_search_1000_chunks(
        self,
        benchmark: pytest.fixture,  # type: ignore
        search_module_with_1000_chunks: SearchModule,
    ) -> None:
        """Benchmark search over 1000 chunks.

        Target: <500ms for 1000 chunks
        """
        query = "section information"
        result = benchmark(search_module_with_1000_chunks.search, query, top_k=10)
        assert len(result) > 0


if __name__ == "__main__":
    # Run benchmarks when executed directly
    pytest.main(
        [
            __file__,
            "-v",
            "--benchmark-only",
            "--benchmark-autosave",
            "-m",
            "not requires_ollama",
        ]
    )
