# Splitting

Split markdown documents into semantic chunks while preserving heading hierarchy.

## Overview

The splitter breaks documents at markdown headers, creating chunks that:
- Maintain semantic coherence
- Include metadata (h1, h2, h3, position)
- Respect token limits
- Preserve hierarchy context

## Usage

### CLI

```bash
markdown-reallocator split input.md --output chunks.json --max-tokens 1000
```

### Python API

```python
from markdown_reallocator.core.splitter import MarkdownSplitter

splitter = MarkdownSplitter(max_tokens_per_chunk=1000)
chunks = splitter.split(markdown_content)

for chunk in chunks:
    print(f"ID: {chunk.chunk_id}")
    print(f"Position: {chunk.metadata.original_position}")
    print(f"Hierarchy: {chunk.metadata.h1} > {chunk.metadata.h2}")
```

## How It Works

1. Parse markdown headers (#, ##, ###)
2. Split at headers while respecting token limits
3. Attach metadata to each chunk
4. Generate unique IDs

## Configuration

```yaml
splitter:
  max_tokens_per_chunk: 1000
  headers_to_split_on:
    - ["#", "h1"]
    - ["##", "h2"]
    - ["###", "h3"]
```

## Output Format

Each chunk contains:
- `chunk_id`: Unique identifier
- `content`: Markdown content
- `metadata`: Heading hierarchy and position
- `embedding`: Null (populated by embedder)

## Next Steps

- [Embeddings](embeddings.md) - Generate vector representations for chunks
- [API Reference](../api/core/splitter.md) - Complete API documentation
