# Markdown Reallocator

**Local-first markdown processing toolkit with semantic operations using embeddings.**

<div class="grid cards" markdown>

-   :material-lightning-bolt:{ .lg .middle } __Fast & Local__

    ---

    Runs entirely on your machine with no API costs.
    Designed for GPUs with 2-4GB VRAM.

    [:octicons-arrow-right-24: Get Started](getting-started/installation.md)

-   :material-puzzle:{ .lg .middle } __Modular Design__

    ---

    Use only the features you need.
    Python API and CLI for flexible integration.

    [:octicons-arrow-right-24: User Guide](user-guide/index.md)

-   :material-brain:{ .lg .middle } __Semantic Operations__

    ---

    Search, reorder, and deduplicate using embeddings.
    Powered by Ollama and embeddinggemma.

    [:octicons-arrow-right-24: Examples](examples/index.md)

-   :material-code-tags:{ .lg .middle } __Developer Friendly__

    ---

    Clean Python API, comprehensive docs, 93%+ test coverage.
    MIT licensed.

    [:octicons-arrow-right-24: API Reference](api/index.md)

</div>

## Overview

Markdown Reallocator solves common problems when working with LLM-generated markdown:

### :material-format-header-pound: Structure Normalization
Automatically converts bold titles (`**Title**`) to proper headings (`## Title`). LLMs frequently use bold formatting instead of proper heading syntax, breaking document structure and navigation.

### :material-puzzle-outline: Semantic Chunking
Splits documents by headers while preserving metadata and hierarchy. Each chunk maintains context about its position in the document structure.

### :material-sort: Intelligent Reordering
Organizes chunks by semantic similarity to improve topical flow. Choose between sequential (chain similar content) or clustering (group by topics).

### :material-magnify: Semantic Search
Find related content using natural language queries. Powered by embeddings for accurate semantic matching beyond keyword search.

### :material-content-duplicate: Smart Deduplication
Remove redundant sections intelligently. Optional LLM-based merging preserves unique information from all duplicates.

## Quick Example

=== "CLI"

    ```bash
    # Normalize markdown structure
    markdown-reallocator preprocess input.md --output clean.md

    # Split into chunks and generate embeddings
    markdown-reallocator split clean.md --output chunks.json
    markdown-reallocator embed chunks.json --output embeddings.npz

    # Search for related content
    markdown-reallocator search "authentication methods" \\
      chunks.json embeddings.npz --top-k 5

    # Reorder by semantic similarity
    markdown-reallocator reorder chunks.json embeddings.npz \\
      --strategy cluster --output reordered.md
    ```

=== "Python API"

    ```python
    from markdown_reallocator.core.preprocessor import MarkdownPreprocessor
    from markdown_reallocator.core.splitter import MarkdownSplitter
    from markdown_reallocator.core.embedder import Embedder
    from markdown_reallocator.modules.search import SearchModule

    # Load and preprocess
    markdown = Path("input.md").read_text()
    preprocessor = MarkdownPreprocessor()
    clean = preprocessor.preprocess(markdown)

    # Split and embed
    splitter = MarkdownSplitter(max_tokens_per_chunk=500)
    chunks = splitter.split(clean)

    embedder = Embedder()
    embedded_chunks = embedder.embed_batch(chunks)

    # Search
    search = SearchModule(embedder=embedder, top_k=5)
    results = search.search("authentication methods", embedded_chunks)

    # Display results
    for chunk, score in results:
        print(f"Score: {score:.3f}")
        print(chunk.content[:100])
        print()
    ```

## Features

:material-check-bold:{ .green } **Local-First** - No cloud APIs required
:material-check-bold:{ .green } **Resource-Efficient** - Runs on GTX 1050 (2GB VRAM)
:material-check-bold:{ .green } **Modular** - Use only what you need
:material-check-bold:{ .green } **Fast** - Embedding at 300+ tokens/sec
:material-check-bold:{ .green } **Well-Tested** - 93.86% code coverage
:material-check-bold:{ .green } **Type-Safe** - Full type hints with mypy validation

## Hardware Requirements

### Minimum
- **GPU**: NVIDIA GPU with 2GB VRAM (GTX 1050 or better)
- **CPU**: x86_64 processor
- **RAM**: 4GB system memory
- **Storage**: 2GB for models and cache

### CPU-Only Mode
Works without GPU but significantly slower:
- Embedding: ~10x slower
- Search/Reorder: Similar speed (CPU-bound operations)

!!! tip "Older CPUs"
    For pre-2011 CPUs without AVX2 support:
    ```bash
    export NPY_DISABLE_CPU_FEATURES="AVX2,FMA3"
    export OPENBLAS_CORETYPE=Haswell
    ```

## Next Steps

<div class="grid cards" markdown>

-   [:material-download: __Installation__](getting-started/installation.md)

    Install Ollama, download models, and set up Markdown Reallocator

-   [:material-rocket-launch: __Quick Start__](getting-started/quickstart.md)

    Get started in 5 minutes with your first workflow

-   [:material-book-open-variant: __User Guide__](user-guide/index.md)

    Learn about all features in depth

-   [:material-code-braces: __API Reference__](api/index.md)

    Complete API documentation with examples

</div>

## Performance

Typical performance on GTX 1050 (2GB) + Intel Xeon X5650:

| Operation | Time | Notes |
|-----------|------|-------|
| **Preprocessing** | <1s per 1000 lines | CPU-bound, regex-based |
| **Embedding** (50 chunks) | ~10s | GPU-bound |
| **Search** (1000 chunks) | <0.5s | NumPy vectorized |
| **Reordering** (100 chunks) | <2s | Similarity + clustering |

## Community

- :fontawesome-brands-github: [GitHub Repository](https://github.com/yourusername/markdown-reallocator)
- :material-bug: [Issue Tracker](https://github.com/yourusername/markdown-reallocator/issues)
- :material-forum: [Discussions](https://github.com/yourusername/markdown-reallocator/discussions)

## License

Markdown Reallocator is released under the [MIT License](https://github.com/yourusername/markdown-reallocator/blob/main/LICENSE).
