# Embeddings

Generate vector representations for semantic operations using Ollama models.

## Overview

Embeddings convert text chunks into high-dimensional vectors that capture semantic meaning, enabling:
- Semantic search
- Similarity-based reordering
- Duplicate detection

## Usage

### CLI

```bash
markdown-reallocator embed chunks.json --output embeddings.npz --cache
```

### Python API

```python
from markdown_reallocator.core.embedder import Embedder

embedder = Embedder(model_name="embeddinggemma", cache_enabled=True)
embedded_chunks = embedder.embed_batch(chunks)

# Save embeddings
embedder.save_embeddings(embedded_chunks, "embeddings.npz")
```

## Models

| Model | Size | Quality | Speed |
|-------|------|---------|-------|
| embeddinggemma | 621MB | Excellent | Fast |
| nomic-embed-text | 274MB | Good | Very Fast |
| all-minilm | 46MB | Basic | Fastest |

## Caching

Embeddings are cached automatically to avoid recomputation:

```python
embedder = Embedder(cache_enabled=True)
chunks1 = embedder.embed_batch(chunks)  # Generates embeddings
chunks2 = embedder.embed_batch(chunks)  # Uses cache
```

Cache location: `~/.cache/markdown-reallocator/embeddings/`

## Configuration

```yaml
embedder:
  model_name: "embeddinggemma"
  batch_size: 10
  cache_enabled: true
  memory_threshold_mb: 1500.0
```

## Performance

Typical speed on GTX 1050 (2GB):
- 50 chunks: ~10 seconds
- 300 tokens/second

## Next Steps

- [Search](search.md) - Use embeddings for semantic search
- [Reordering](reordering.md) - Reorganize by similarity
