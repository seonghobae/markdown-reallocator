# CLI Reference

Complete command-line interface reference.

## Global Options

```bash
markdown-reallocator [OPTIONS] COMMAND [ARGS]
```

**Options**:
- `--version`, `-v`: Show version and exit
- `--verbose`, `-V`: Enable verbose output
- `--no-color`: Disable colored output
- `--help`: Show help message

## Commands

### preprocess

Fix markdown structure by converting bold titles to headers.

```bash
markdown-reallocator preprocess INPUT [OPTIONS]
```

**Arguments**:
- `INPUT`: Input markdown file (required)

**Options**:
- `--output`, `-o PATH`: Output file (default: stdout)
- `--detect-bold-headers/--no-detect-bold-headers`: Enable/disable bold header detection (default: enabled)

**Examples**:
```bash
# Output to stdout
markdown-reallocator preprocess input.md

# Save to file
markdown-reallocator preprocess input.md --output clean.md

# Disable bold header detection
markdown-reallocator preprocess input.md --no-detect-bold-headers
```

### split

Split markdown into semantic chunks.

```bash
markdown-reallocator split INPUT [OPTIONS]
```

**Arguments**:
- `INPUT`: Input markdown file (required)

**Options**:
- `--output`, `-o PATH`: Output JSON file
- `--max-tokens INT`: Maximum tokens per chunk (default: 1000)

**Examples**:
```bash
# Output to stdout
markdown-reallocator split input.md

# Save to file with custom chunk size
markdown-reallocator split input.md --output chunks.json --max-tokens 500
```

### embed

Generate embeddings for chunks.

```bash
markdown-reallocator embed INPUT [OPTIONS]
```

**Arguments**:
- `INPUT`: Input JSON file with chunks (required)

**Options**:
- `--output`, `-o PATH`: Output embeddings file (.npz) (required)
- `--model TEXT`: Ollama model name (default: embeddinggemma)
- `--cache/--no-cache`: Enable/disable caching (default: enabled)

**Examples**:
```bash
# Generate embeddings
markdown-reallocator embed chunks.json --output embeddings.npz

# Use different model
markdown-reallocator embed chunks.json --output embeddings.npz --model nomic-embed-text

# Disable caching
markdown-reallocator embed chunks.json --output embeddings.npz --no-cache
```

### search

Search for similar chunks.

```bash
markdown-reallocator search QUERY INPUT EMBEDDINGS [OPTIONS]
```

**Arguments**:
- `QUERY`: Search query (required)
- `INPUT`: Input JSON file with chunks (required)
- `EMBEDDINGS`: Embeddings file (.npz) (required)

**Options**:
- `--top-k`, `-k INT`: Number of results (default: 5)
- `--min-similarity FLOAT`: Minimum similarity (0.0-1.0) (default: 0.5)
- `--format`, `-f TEXT`: Output format (text or json) (default: text)

**Examples**:
```bash
# Basic search
markdown-reallocator search "authentication" chunks.json embeddings.npz

# More results, higher threshold
markdown-reallocator search "API security" chunks.json embeddings.npz \\
  --top-k 10 --min-similarity 0.7

# JSON output
markdown-reallocator search "deployment" chunks.json embeddings.npz --format json
```

### reorder

Reorder chunks by semantic similarity.

```bash
markdown-reallocator reorder INPUT EMBEDDINGS [OPTIONS]
```

**Arguments**:
- `INPUT`: Input JSON file with chunks (required)
- `EMBEDDINGS`: Embeddings file (.npz) (required)

**Options**:
- `--output`, `-o PATH`: Output markdown file (required)
- `--strategy`, `-s TEXT`: Reordering strategy (sequential or cluster) (default: sequential)

**Examples**:
```bash
# Sequential reordering
markdown-reallocator reorder chunks.json embeddings.npz --output reordered.md

# Cluster-based reordering
markdown-reallocator reorder chunks.json embeddings.npz \\
  --output reordered.md --strategy cluster
```

### dedup

Remove duplicate chunks.

```bash
markdown-reallocator dedup INPUT EMBEDDINGS [OPTIONS]
```

**Arguments**:
- `INPUT`: Input JSON file with chunks (required)
- `EMBEDDINGS`: Embeddings file (.npz) (required)

**Options**:
- `--output`, `-o PATH`: Output JSON file (required)
- `--threshold`, `-t FLOAT`: Similarity threshold (0.0-1.0) (default: 0.85)
- `--strategy`, `-s TEXT`: Selection strategy (first, longest, best_metadata) (default: first)
- `--dry-run`: Show what would be removed without removing

**Examples**:
```bash
# Basic deduplication
markdown-reallocator dedup chunks.json embeddings.npz --output clean.json

# Stricter threshold, keep longest
markdown-reallocator dedup chunks.json embeddings.npz \\
  --output clean.json --threshold 0.95 --strategy longest

# Dry run to preview
markdown-reallocator dedup chunks.json embeddings.npz --dry-run
```

## Configuration

CLI respects configuration files and environment variables:

```bash
# Use custom config file
MARKDOWN_REALLOCATOR_CONFIG=./custom_config.yaml markdown-reallocator preprocess input.md

# Override settings via environment variables
export MARKDOWN_REALLOCATOR_EMBEDDER_BATCH_SIZE=5
markdown-reallocator embed chunks.json --output embeddings.npz
```

## Exit Codes

- `0`: Success
- `1`: Error (invalid arguments, file not found, processing error)

## Next Steps

- [Python API](python-api.md) - Programmatic interface
- [Configuration](../getting-started/configuration.md) - Customize behavior
- [Examples](../examples/index.md) - Real-world usage patterns
