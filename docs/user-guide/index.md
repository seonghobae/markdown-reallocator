# User Guide

Complete guide to using Markdown Reallocator's features.

## Overview

Markdown Reallocator provides five core operations:

1. **[Preprocessing](preprocessing.md)** - Fix markdown structure
2. **[Splitting](splitting.md)** - Create semantic chunks
3. **[Embeddings](embeddings.md)** - Generate vector representations
4. **[Search](search.md)** - Find similar content
5. **[Reordering](reordering.md)** - Organize by similarity
6. **[Deduplication](deduplication.md)** - Remove redundant sections

## Workflows

### Document Cleanup

Fix LLM-generated markdown with structural issues:

```bash
markdown-reallocator preprocess input.md --output clean.md
```

### Semantic Search

Find related content across documents:

```bash
markdown-reallocator split docs.md --output chunks.json
markdown-reallocator embed chunks.json --output embeddings.npz
markdown-reallocator search "API authentication" chunks.json embeddings.npz
```

### Content Organization

Reorder scattered topics by similarity:

```bash
markdown-reallocator reorder chunks.json embeddings.npz \\
  --strategy cluster --output organized.md
```

### Duplicate Removal

Clean up merged documents:

```bash
markdown-reallocator dedup chunks.json embeddings.npz \\
  --threshold 0.90 --output clean.json
```

## Interfaces

Markdown Reallocator provides two interfaces:

### CLI

Best for:
- Quick one-off operations
- Shell scripts and automation
- Command-line workflows

See [CLI Reference](cli-reference.md) for all commands.

### Python API

Best for:
- Custom pipelines
- Integration with existing tools
- Programmatic control

See [Python API Guide](python-api.md) for examples.

## Module Guides

<div class="grid cards" markdown>

-   :material-format-text: **[Preprocessing](preprocessing.md)**

    Convert bold titles to headers, fix structure issues

-   :material-content-cut: **[Splitting](splitting.md)**

    Break documents into semantic chunks with metadata

-   :material-brain: **[Embeddings](embeddings.md)**

    Generate vector representations for semantic operations

-   :material-magnify: **[Search](search.md)**

    Find similar chunks using natural language queries

-   :material-sort: **[Reordering](reordering.md)**

    Reorganize chunks by semantic similarity

-   :material-content-duplicate: **[Deduplication](deduplication.md)**

    Remove redundant or near-duplicate sections

</div>

## Configuration

All modules support configuration via:

- YAML files (`~/.config/markdown-reallocator/config.yaml`)
- Environment variables (`MARKDOWN_REALLOCATOR_*`)
- Python API parameters

See [Configuration Guide](../getting-started/configuration.md) for details.

## Next Steps

- Start with [Preprocessing](preprocessing.md) to fix document structure
- Learn about [Python API](python-api.md) for custom workflows
- Check [CLI Reference](cli-reference.md) for all command options
