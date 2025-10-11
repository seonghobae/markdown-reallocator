# Examples

Real-world usage examples and patterns.

## Available Examples

- [Basic Workflow](basic-workflow.md) - Complete preprocessing to reordering
- [Batch Processing](batch-processing.md) - Process multiple files efficiently
- [Custom Pipelines](custom-pipelines.md) - Build custom processing workflows
- [Integration](integration.md) - Integrate with existing tools

## Quick Examples

### Clean LLM Output

```bash
markdown-reallocator preprocess llm_output.md --output clean.md
```

### Find Related Content

```bash
markdown-reallocator split docs.md --output chunks.json
markdown-reallocator embed chunks.json --output embeddings.npz
markdown-reallocator search "API authentication" chunks.json embeddings.npz
```

### Remove Duplicates

```bash
markdown-reallocator dedup chunks.json embeddings.npz --output clean.json --threshold 0.90
```

See individual example pages for detailed walkthroughs.
