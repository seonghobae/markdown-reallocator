# Architecture

Overview of Markdown Reallocator's architecture and design.

## System Architecture

```
┌─────────────────────────────────────────────┐
│                   CLI / API                  │
└──────────────────┬──────────────────────────┘
                   │
       ┌───────────┴───────────┐
       │                       │
┌──────▼──────┐         ┌─────▼──────┐
│    Core     │         │  Modules   │
├─────────────┤         ├────────────┤
│Preprocessor │         │  Search    │
│  Splitter   │         │  Reorder   │
│  Embedder   │         │   Dedup    │
└──────┬──────┘         └─────┬──────┘
       │                      │
       └──────────┬───────────┘
                  │
          ┌───────▼────────┐
          │     Models     │
          ├────────────────┤
          │  Chunk         │
          │  Embedding     │
          │  Exceptions    │
          └───────┬────────┘
                  │
          ┌───────▼────────┐
          │     Utils      │
          ├────────────────┤
          │  Cache         │
          │  Memory        │
          │  Similarity    │
          └────────────────┘
```

## Core Components

- **[Design Principles](design-principles.md)** - Architectural decisions and rationale
- **[Data Flow](data-flow.md)** - How data moves through the system
- **[Performance](performance.md)** - Performance characteristics and optimization

## Key Design Decisions

### Modular Architecture

Each component is independent and can be used standalone.

### Local-First

All processing happens locally without cloud dependencies.

### Memory-Efficient

Automatic model loading/unloading to minimize GPU memory usage.

### Caching

Embeddings are cached to avoid recomputation.
