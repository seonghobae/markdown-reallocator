# Markdown Reallocator

[![CI](https://github.com/yourusername/markdown-reallocator/workflows/CI/badge.svg)](https://github.com/yourusername/markdown-reallocator/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/yourusername/markdown-reallocator/branch/main/graph/badge.svg)](https://codecov.io/gh/yourusername/markdown-reallocator)
[![PyPI version](https://badge.fury.io/py/markdown-reallocator.svg)](https://badge.fury.io/py/markdown-reallocator)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

Local-first markdown processing toolkit with semantic operations using embeddings.

## Overview

Markdown Reallocator solves common problems when working with LLM-generated markdown:
- **Structure Normalization**: Automatically converts bold titles (`**Title**`) to proper headings (`## Title`)
- **Semantic Chunking**: Splits documents by headers while preserving metadata
- **Intelligent Reordering**: Organizes chunks by semantic similarity
- **Semantic Search**: Find related content using natural language queries
- **Smart Deduplication**: Remove redundant sections intelligently

## Features

- 🚀 **Local-First**: Runs entirely on your machine, no API costs
- 🎯 **Resource-Efficient**: Designed for GPUs with 2-4GB VRAM (e.g., GTX 1050)
- 🔧 **Modular**: Use only the features you need
- 🐍 **Python API + CLI**: Flexible integration options
- 📊 **Semantic Operations**: Powered by embeddings via Ollama

## Requirements

### Hardware
- **GPU**: NVIDIA GPU with 2GB+ VRAM (or CPU-only mode, slower)
- **CPU**: Any x86_64 CPU (optimized for SSE4.2+)
- **RAM**: 4GB+ system memory

### Software
- **Python**: 3.10 or newer
- **Ollama**: Local LLM runtime ([install guide](https://ollama.ai))

### CPU Compatibility Notes

For older CPUs (pre-2011, e.g., Intel Westmere/Xeon X5650) that don't support AVX2:

```bash
# Add to ~/.bashrc or ~/.zshrc
export NPY_DISABLE_CPU_FEATURES="AVX2,FMA3"
export OPENBLAS_CORETYPE=Haswell
```

## Installation

### 1. Install Ollama and Models

```bash
# Install Ollama (see https://ollama.ai for your platform)
# Then pull required models:
ollama pull embeddinggemma
ollama pull gemma:2b-instruct-q4_0  # Optional, for LLM-based deduplication
```

### 2. Install Markdown Reallocator

```bash
pip install markdown-reallocator
```

Or install from source:

```bash
git clone https://github.com/yourusername/markdown-reallocator.git
cd markdown-reallocator
pip install -e .
```

### 3. Verify Installation

```bash
markdown-reallocator --help
```

## Quick Start

### CLI Usage

```bash
# Normalize markdown structure
markdown-reallocator preprocess input.md --fix-headings --output clean.md

# Split into semantic chunks
markdown-reallocator split input.md --output-dir chunks/

# Generate embeddings
markdown-reallocator embed input.md --cache

# Search for similar content
markdown-reallocator search "related sections" input.md --top-k 5

# Reorder by semantic similarity
markdown-reallocator reorder input.md --strategy cluster --output reordered.md

# Remove duplicates
markdown-reallocator dedup input.md --threshold 0.85 --output deduplicated.md
```

### Python API

```python
from markdown_reallocator import MarkdownProcessor

# Simple fluent API
processor = MarkdownProcessor()
result = (
    processor
    .load("input.md")
    .preprocess(fix_headings=True)
    .split(max_tokens=500)
    .embed(model="embeddinggemma")
    .reorder(strategy="cluster")
    .save("output.md")
)

# Or step-by-step
chunks = processor.load("input.md").preprocess().split().get_chunks()
results = processor.search("find related content", top_k=5)
```

## Documentation

- [Installation Guide](docs/installation.md)
- [User Guide](docs/user-guide/)
- [API Reference](docs/api-reference/)
- [Examples](examples/)

## Development

### Setup

```bash
# Clone repository
git clone https://github.com/yourusername/markdown-reallocator.git
cd markdown-reallocator

# Install with dev dependencies
pip install -e ".[dev]"

# Verify setup
pytest tests/smoke/
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov

# Run only smoke tests
pytest tests/smoke/

# Run specific test
pytest tests/unit/test_preprocessor.py
```

### Linting

```bash
# Check code style
ruff check .

# Fix auto-fixable issues
ruff check --fix .

# Type checking
mypy markdown_reallocator
```

## Performance

### Measured Performance (Benchmark Results)

Preprocessing and splitting performance (CPU-bound):

| Operation | Document Size | Time | Performance vs Target |
|-----------|--------------|------|----------------------|
| Preprocessing | 100 lines | ~0.46 ms | ✅ **200x faster than target** |
| Preprocessing | 1,000 lines | ~4.3 ms | ✅ Target: <1s |
| Preprocessing | 5,000 lines | ~21.7 ms | ✅ **46x faster** |
| Preprocessing | 10,000 lines | ~40-50 ms | ✅ **20x faster** |
| Splitting | 1,000 lines | ~8.9 ms | ✅ Very fast |

Embedding and search (GPU-bound, typical on GTX 1050/2GB):

| Operation | Scale | Time | Notes |
|-----------|-------|------|-------|
| Embedding | 50 chunks | ~10s | Target: <10s ✅ |
| Search | 1,000 chunks | <500ms | NumPy vectorized ✅ |
| Reordering | 100 chunks | <2s | Similarity + clustering |

Memory usage:

| Component | Memory |
|-----------|--------|
| Preprocessing | ~0.9 MB per 10K lines |
| Splitting | ~2 MB per 1K chunks |
| Baseline | ~95 MB |
| **Peak (with embeddings)** | **<1.8GB** ✅ |

### Performance Profiling

Enable performance profiling with the `--profile` flag:

```bash
markdown-reallocator --profile preprocess input.md -o output.md
```

Example output:
```
=== Performance Summary ===
  read_input: 1.23 ms | Memory: +0.5 MB
  preprocess: 4.56 ms | Memory: +0.9 MB
  write_output: 0.89 ms | Memory: +0.1 MB

Total Duration: 0.007 s
Peak Memory: 95.3 MB
```

Run comprehensive benchmarks:

```bash
# Quick benchmarks (no Ollama required)
pytest benchmarks/ --benchmark-only --no-cov

# Memory profiling
python -m memory_profiler benchmarks/profile_memory.py
```

See [benchmarks/README.md](benchmarks/README.md) for detailed performance documentation.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Acknowledgments

- [LangChain](https://langchain.com/) for markdown splitting utilities
- [Ollama](https://ollama.ai) for local LLM runtime
- [embeddinggemma](https://ai.google.dev/gemma) for embedding generation

## Citation

If you use Markdown Reallocator in your research or project, please cite:

```bibtex
@software{markdown_reallocator,
  title = {Markdown Reallocator: Local-First Markdown Processing with Semantic Operations},
  author = {Markdown Reallocator Contributors},
  year = {2025},
  url = {https://github.com/yourusername/markdown-reallocator}
}
```
