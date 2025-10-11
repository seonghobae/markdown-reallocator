# Data Flow

How data flows through Markdown Reallocator.

## Pipeline Flow

```
Input Markdown
     │
     ▼
┌─────────────┐
│ Preprocessor│  Fix structure
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Splitter   │  Create chunks
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Embedder   │  Generate vectors
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Modules   │  Search/Reorder/Dedup
└──────┬──────┘
       │
       ▼
  Output Markdown
```

## Data Models

### Chunk

Contains document content and metadata:
- `chunk_id`: Unique identifier
- `content`: Markdown content
- `metadata`: Hierarchy and position
- `embedding`: Vector representation (optional)

### Embedding

Vector representation with metadata:
- `vector`: NumPy array
- `text_hash`: Content hash
- `model_name`: Embedding model

See [API Reference](../api/models/chunk.md) for complete details.
