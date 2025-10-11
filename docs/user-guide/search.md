# Semantic Search

Find chunks similar to queries or other chunks using embedding-based similarity.

## Overview

Semantic search finds related content based on meaning, not just keywords:
- Natural language queries
- Ranked by cosine similarity
- Adjustable thresholds and result counts

## Usage

### CLI

```bash
markdown-reallocator search "authentication methods" \\
  chunks.json embeddings.npz --top-k 5 --min-similarity 0.5
```

Output:
```
Found 3 results:

1. Score: 0.892
   ## API Authentication
   Use OAuth 2.0 for secure authentication...

2. Score: 0.745
   ## Security Best Practices
   Always validate tokens and use HTTPS...
```

### Python API

```python
from markdown_reallocator.modules.search import SearchModule
from markdown_reallocator.core.embedder import Embedder

embedder = Embedder()
search = SearchModule(embedder=embedder, top_k=5, min_similarity=0.5)

results = search.search("authentication methods", embedded_chunks)

for chunk, score in results:
    print(f"Score: {score:.3f}")
    print(chunk.content[:100])
```

## Configuration

```yaml
search:
  top_k: 5
  min_similarity: 0.5
  output_format: "text"  # or "json"
```

## Advanced Usage

### Find Similar Chunks

Find chunks similar to a given chunk:

```python
target_chunk = embedded_chunks[0]
similar = search.find_similar_chunks(target_chunk, embedded_chunks, top_k=5)
```

### Custom Similarity Function

```python
from markdown_reallocator.utils.similarity import cosine_similarity

# Manual similarity calculation
similarity = cosine_similarity(chunk1.embedding, chunk2.embedding)
```

## Use Cases

- Documentation search
- Related content discovery
- Duplicate detection preprocessing
- Content recommendation

## Next Steps

- [Reordering](reordering.md) - Organize search results by similarity
- [API Reference](../api/modules/search.md) - Complete API documentation
