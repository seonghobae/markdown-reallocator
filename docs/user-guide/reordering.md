# Reordering

Reorganize document chunks by semantic similarity for better topical flow.

## Overview

Two reordering strategies:
- **Sequential**: Chain similar chunks one after another
- **Cluster**: Group chunks by topic, then order within groups

## Usage

### CLI

```bash
# Sequential reordering
markdown-reallocator reorder chunks.json embeddings.npz \\
  --strategy sequential --output reordered.md

# Cluster-based reordering
markdown-reallocator reorder chunks.json embeddings.npz \\
  --strategy cluster --output reordered.md
```

### Python API

```python
from markdown_reallocator.modules.reorder import ReorderModule

# Sequential
reorder = ReorderModule(strategy="sequential")
reordered = reorder.reorder(embedded_chunks)
markdown = reorder.reconstruct_markdown(reordered)

# Cluster
reorder = ReorderModule(strategy="cluster")
reordered = reorder.reorder(embedded_chunks)
markdown = reorder.reconstruct_markdown(reordered, include_comments=True)
```

## Strategies

### Sequential

Chains chunks by similarity:
1. Start with first chunk (or seed)
2. Find most similar unchosen chunk
3. Repeat until all chunks processed

Best for: Gradual topic progression

### Cluster

Groups similar chunks:
1. Cluster chunks by embedding similarity (KMeans)
2. Order clusters by size or centrality
3. Order chunks within each cluster

Best for: Distinct topic groups

## Configuration

```yaml
reorder:
  strategy: "sequential"  # or "cluster"
```

## Next Steps

- [Deduplication](deduplication.md) - Remove duplicates before reordering
- [API Reference](../api/modules/reorder.md) - Complete API documentation
