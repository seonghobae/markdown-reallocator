# Configuration

Markdown Reallocator provides flexible configuration through YAML files, environment variables, and Python API parameters.

## Configuration Methods

### 1. Default Configuration

Markdown Reallocator works out of the box with sensible defaults. No configuration required for most use cases!

### 2. Configuration File

Create `~/.config/markdown-reallocator/config.yaml`:

```yaml
# Preprocessor settings
preprocessor:
  max_title_length: 80
  require_empty_lines: true
  min_capitalization_ratio: 0.1

# Splitter settings
splitter:
  max_tokens_per_chunk: 1000
  headers_to_split_on:
    - ["#", "h1"]
    - ["##", "h2"]
    - ["###", "h3"]

# Embedder settings
embedder:
  model_name: "embeddinggemma"
  batch_size: 10
  cache_enabled: true
  memory_threshold_mb: 1500.0

# Search settings
search:
  top_k: 5
  min_similarity: 0.5
  output_format: "text"

# Reorder settings
reorder:
  strategy: "sequential"

# Deduplication settings
dedup:
  similarity_threshold: 0.85
  selection_strategy: "first"
  use_llm: false
  dry_run: false
```

### 3. Project-Specific Configuration

Place `config.yaml` in your project directory.

Configuration search order (first found wins):

1. `./config.yaml` (current directory)
2. `./markdown_reallocator.yaml`
3. `~/.config/markdown-reallocator/config.yaml`
4. Built-in defaults

### 4. Environment Variables

Override any setting with environment variables:

```bash
# Pattern: MARKDOWN_REALLOCATOR_<SECTION>_<KEY>

# Override embedding model
export MARKDOWN_REALLOCATOR_EMBEDDER_MODEL_NAME="nomic-embed-text"

# Override batch size
export MARKDOWN_REALLOCATOR_EMBEDDER_BATCH_SIZE=5

# Override search parameters
export MARKDOWN_REALLOCATOR_SEARCH_TOP_K=10
export MARKDOWN_REALLOCATOR_SEARCH_MIN_SIMILARITY=0.7
```

Environment variables have **highest priority** and override file settings.

## Configuration Sections

### Preprocessor

Controls markdown structure normalization.

```yaml
preprocessor:
  max_title_length: 80
  require_empty_lines: true
  min_capitalization_ratio: 0.1
```

**Parameters**:

- `max_title_length` (int, default: 80): Maximum character length for bold text to be considered a heading
- `require_empty_lines` (bool, default: true): Require empty lines around title candidates
- `min_capitalization_ratio` (float, default: 0.1): Minimum proportion of capital letters in title

### Splitter

Controls how documents are split into chunks.

```yaml
splitter:
  max_tokens_per_chunk: 1000
  headers_to_split_on:
    - ["#", "h1"]
    - ["##", "h2"]
    - ["###", "h3"]
```

**Parameters**:

- `max_tokens_per_chunk` (int, default: 1000): Maximum tokens per chunk
- `headers_to_split_on` (list, default: h1-h3): Markdown headers to split on

### Embedder

Controls embedding generation.

```yaml
embedder:
  model_name: "embeddinggemma"
  batch_size: 10
  cache_enabled: true
  memory_threshold_mb: 1500.0
```

**Parameters**:

- `model_name` (str, default: "embeddinggemma"): Ollama embedding model
- `batch_size` (int, default: 10): Chunks to embed per batch
- `cache_enabled` (bool, default: true): Cache embeddings for identical content
- `memory_threshold_mb` (float, default: 1500.0): Memory threshold for automatic model unloading

**Available Models**:

- `embeddinggemma` (621MB) - Recommended
- `nomic-embed-text` (274MB) - Smaller
- `all-minilm` (46MB) - Smallest

### Search

Controls semantic search behavior.

```yaml
search:
  top_k: 5
  min_similarity: 0.5
  output_format: "text"
```

**Parameters**:

- `top_k` (int, default: 5): Maximum number of results
- `min_similarity` (float, default: 0.5): Minimum cosine similarity score
- `output_format` (str, default: "text"): Output format for CLI

### Reorder

Controls chunk reordering strategies.

```yaml
reorder:
  strategy: "sequential"
```

**Parameters**:

- `strategy` (str, default: "sequential"): Reordering approach ("sequential" or "cluster")

### Deduplication

Controls duplicate detection and removal.

```yaml
dedup:
  similarity_threshold: 0.85
  selection_strategy: "first"
  use_llm: false
  dry_run: false
```

**Parameters**:

- `similarity_threshold` (float, default: 0.85): Cosine similarity threshold
- `selection_strategy` (str, default: "first"): Which duplicate to keep ("first", "longest", or "best_metadata")
- `use_llm` (bool, default: false): Use Gemma 2B to merge duplicates
- `dry_run` (bool, default: false): Report without removing

## Next Steps

- [Quick Start](quickstart.md) - Try the configuration in practice
- [User Guide](../user-guide/index.md) - Learn about each module
