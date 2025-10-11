# Deduplication

Remove duplicate or near-duplicate chunks intelligently.

## Overview

Detect and remove redundant content based on embedding similarity:
- Configurable similarity threshold
- Multiple selection strategies
- Optional LLM-based merging

## Usage

### CLI

```bash
markdown-reallocator dedup chunks.json embeddings.npz \\
  --output clean.json --threshold 0.85 --strategy first
```

Output:
```
Deduplication Report
====================
Original chunks: 10
Deduplicated chunks: 8
Removed: 2 duplicate(s)

Removed Chunks:
- chunk_005: "## Introduction..." (95.2% similar to chunk_001)
- chunk_008: "## Overview..." (87.1% similar to chunk_002)
```

### Python API

```python
from markdown_reallocator.modules.dedup import DeduplicationModule

dedup = DeduplicationModule(
    similarity_threshold=0.85,
    selection_strategy="first",
    dry_run=False
)

deduplicated, report = dedup.deduplicate(embedded_chunks)
print(dedup.format_report(report))
```

## Selection Strategies

**first** (default)
- Keep first occurrence
- Simple and predictable

**longest**
- Keep chunk with most content
- Preserves more information

**best_metadata**
- Keep chunk with complete hierarchy
- Better for structured documents

## LLM-Based Merging

Use Gemma 2B to intelligently merge duplicates:

```yaml
dedup:
  use_llm: true
  similarity_threshold: 0.85
```

```python
dedup = DeduplicationModule(use_llm=True)
deduplicated, report = dedup.deduplicate(chunks)
```

## Dry Run Mode

Preview what would be removed:

```bash
markdown-reallocator dedup chunks.json embeddings.npz --dry-run
```

## Configuration

```yaml
dedup:
  similarity_threshold: 0.85
  selection_strategy: "first"
  use_llm: false
  dry_run: false
```

## Next Steps

- [Reordering](reordering.md) - Reorder after deduplication
- [API Reference](../api/modules/dedup.md) - Complete API documentation
