"""
Memory profiling script for Markdown Reallocator.

Target: Peak GPU memory ≤ 1.8GB
"""

import psutil
from memory_profiler import profile

from markdown_reallocator.core import Embedder, MarkdownPreprocessor, MarkdownSplitter
from markdown_reallocator.modules import DeduplicationModule, ReorderModule, SearchModule


def get_process_memory_mb() -> float:
    """Get current process memory usage in MB."""
    process = psutil.Process()
    return process.memory_info().rss / 1024 / 1024


def generate_large_markdown(lines: int = 5000) -> str:
    """Generate a large markdown document."""
    content = []
    for i in range(lines // 5):
        content.append(f"## Section {i}\n")
        content.append("\n")
        content.append(f"This is content for section {i}.\n")
        content.append("Additional paragraph with more details.\n")
        content.append("Even more content to make it realistic.\n")
    return "".join(content)


@profile
def test_full_pipeline_memory() -> None:
    """Profile memory usage of full pipeline."""
    print("Starting full pipeline memory profiling...")
    print(f"Initial memory: {get_process_memory_mb():.1f} MB")

    # Generate test data
    markdown = generate_large_markdown(5000)
    print(f"After generating markdown: {get_process_memory_mb():.1f} MB")

    # Preprocessing
    preprocessor = MarkdownPreprocessor()
    clean = preprocessor.preprocess(markdown)
    print(f"After preprocessing: {get_process_memory_mb():.1f} MB")

    # Splitting
    splitter = MarkdownSplitter(max_tokens_per_chunk=500)
    chunks = splitter.split(clean)
    print(f"After splitting ({len(chunks)} chunks): {get_process_memory_mb():.1f} MB")

    # Embedding (this should be the memory peak)
    try:
        embedder = Embedder(model_name="embeddinggemma", cache_enabled=False)
        print(f"After loading embedder: {get_process_memory_mb():.1f} MB")

        embedded = embedder.embed_batch(chunks[:100])  # Limit to 100 for testing
        print(f"After embedding 100 chunks: {get_process_memory_mb():.1f} MB")

        # Search
        search_module = SearchModule(embedded)
        search_module.search("section information", top_k=10)
        print(f"After search: {get_process_memory_mb():.1f} MB")

        # Reordering
        reorder_module = ReorderModule(embedded)
        reorder_module.reorder_by_similarity(strategy="sequential")
        print(f"After reordering: {get_process_memory_mb():.1f} MB")

        # Deduplication
        dedup_module = DeduplicationModule(embedded)
        dedup_module.deduplicate(threshold=0.95, strategy="longest")
        print(f"After deduplication: {get_process_memory_mb():.1f} MB")

    except Exception as e:
        print(f"Warning: Ollama not available: {e}")
        print("Skipping embedding, search, reorder, and dedup tests")

    print(f"\nFinal memory: {get_process_memory_mb():.1f} MB")
    print("\nMemory profiling complete!")


@profile
def test_preprocessing_only_memory() -> None:
    """Profile memory usage of preprocessing only."""
    print("Profiling preprocessing memory usage...")
    markdown = generate_large_markdown(10000)  # Larger document
    preprocessor = MarkdownPreprocessor()
    clean = preprocessor.preprocess(markdown)
    print(f"Processed {len(clean)} characters")


@profile
def test_embedding_batch_sizes() -> None:
    """Test different batch sizes for embedding."""
    print("Testing embedding batch sizes...")

    markdown = generate_large_markdown(1000)
    preprocessor = MarkdownPreprocessor()
    splitter = MarkdownSplitter(max_tokens_per_chunk=500)

    clean = preprocessor.preprocess(markdown)
    chunks = splitter.split(clean)

    try:
        embedder = Embedder(model_name="embeddinggemma", cache_enabled=False)

        for batch_size in [1, 10, 50, 100]:
            print(f"\nTesting batch_size={batch_size}")
            mem_before = get_process_memory_mb()
            embedder.embed_batch(chunks[: min(batch_size, len(chunks))])
            mem_after = get_process_memory_mb()
            print(f"  Memory delta: {mem_after - mem_before:.1f} MB")

    except Exception as e:
        print(f"Warning: Ollama not available: {e}")


def main() -> None:
    """Run all memory profiling tests."""
    print("=" * 80)
    print("MEMORY PROFILING - Markdown Reallocator")
    print("=" * 80)
    print()

    # Test 1: Preprocessing only
    test_preprocessing_only_memory()
    print("\n" + "=" * 80 + "\n")

    # Test 2: Full pipeline
    test_full_pipeline_memory()
    print("\n" + "=" * 80 + "\n")

    # Test 3: Batch sizes
    test_embedding_batch_sizes()


if __name__ == "__main__":
    main()
