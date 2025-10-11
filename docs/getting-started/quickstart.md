# Quick Start

Get started with Markdown Reallocator in 5 minutes.

## Basic Workflow

### 1. Preprocess

Fix markdown structure:

```bash
markdown-reallocator preprocess input.md --output clean.md
```

### 2. Split

Create semantic chunks:

```bash
markdown-reallocator split clean.md --output chunks.json
```

### 3. Embed

Generate embeddings:

```bash
markdown-reallocator embed chunks.json --output embeddings.npz
```

### 4. Search

Find related content:

```bash
markdown-reallocator search "your query" chunks.json embeddings.npz
```

### 5. Reorder

Organize by similarity:

```bash
markdown-reallocator reorder chunks.json embeddings.npz --output final.md
```

## Python API

```python
from markdown_reallocator.core.preprocessor import MarkdownPreprocessor
from markdown_reallocator.core.splitter import MarkdownSplitter

# Load and preprocess
markdown = open("input.md").read()
preprocessor = MarkdownPreprocessor()
clean = preprocessor.preprocess(markdown)

# Split
splitter = MarkdownSplitter()
chunks = splitter.split(clean)
```

## Next Steps

- [User Guide](../user-guide/index.md) - Learn all features
- [Examples](../examples/index.md) - See real-world usage
- [API Reference](../api/index.md) - Complete API docs
