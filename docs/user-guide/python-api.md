# Python API

Build custom markdown processing pipelines with the Python API.

## Overview

The Python API provides:
- Fine-grained control over each step
- Easy integration with existing tools
- Custom pipeline construction
- Programmatic configuration

## Basic Pipeline

```python
from pathlib import Path
from markdown_reallocator.core.preprocessor import MarkdownPreprocessor
from markdown_reallocator.core.splitter import MarkdownSplitter
from markdown_reallocator.core.embedder import Embedder

# Load markdown
markdown = Path("input.md").read_text()

# Preprocess
preprocessor = MarkdownPreprocessor()
clean = preprocessor.preprocess(markdown)

# Split
splitter = MarkdownSplitter(max_tokens_per_chunk=500)
chunks = splitter.split(clean)

# Embed
embedder = Embedder(cache_enabled=True)
embedded = embedder.embed_batch(chunks)

# Save
Path("output.md").write_text(clean)
```

## Complete Pipeline

```python
from markdown_reallocator.core import MarkdownPreprocessor, MarkdownSplitter, Embedder
from markdown_reallocator.modules import SearchModule, ReorderModule, DeduplicationModule

# Setup
markdown = Path("input.md").read_text()
preprocessor = MarkdownPreprocessor()
splitter = MarkdownSplitter()
embedder = Embedder()

# Process
clean = preprocessor.preprocess(markdown)
chunks = splitter.split(clean)
embedded = embedder.embed_batch(chunks)

# Deduplicate
dedup = DeduplicationModule(similarity_threshold=0.85)
unique_chunks, report = dedup.deduplicate(embedded)

# Reorder
reorder = ReorderModule(strategy="cluster")
reordered = reorder.reorder(unique_chunks)
final = reorder.reconstruct_markdown(reordered)

# Save
Path("output.md").write_text(final)
```

## Custom Configuration

```python
from markdown_reallocator.config import Settings, PreprocessorConfig, EmbedderConfig

settings = Settings(
    preprocessor=PreprocessorConfig(
        max_title_length=100,
        require_empty_lines=False
    ),
    embedder=EmbedderConfig(
        model_name="nomic-embed-text",
        batch_size=5
    )
)

preprocessor = MarkdownPreprocessor(config=settings.preprocessor)
embedder = Embedder(model_name=settings.embedder.model_name)
```

## Batch Processing

Process multiple files:

```python
from pathlib import Path

input_dir = Path("inputs/")
output_dir = Path("outputs/")
output_dir.mkdir(exist_ok=True)

for md_file in input_dir.glob("*.md"):
    markdown = md_file.read_text()
    clean = preprocessor.preprocess(markdown)
    
    output_file = output_dir / md_file.name
    output_file.write_text(clean)
```

## Error Handling

```python
try:
    embedded = embedder.embed_batch(chunks)
except ConnectionError as e:
    print(f"Ollama not running: {e}")
except MemoryError as e:
    print(f"Out of memory: {e}")
    # Reduce batch size
    embedder.config.batch_size = 5
    embedded = embedder.embed_batch(chunks)
```

## Integration Examples

### With LangChain

```python
from langchain.text_splitter import MarkdownHeaderTextSplitter
from markdown_reallocator.core import Embedder

# Use LangChain for splitting
splitter = MarkdownHeaderTextSplitter(headers_to_split_on=[("#", "h1"), ("##", "h2")])
langchain_chunks = splitter.split_text(markdown)

# Convert to Markdown Reallocator format
from markdown_reallocator.models.chunk import Chunk, ChunkMetadata
chunks = [
    Chunk(chunk_id=f"chunk_{i}", content=c.page_content, 
          metadata=ChunkMetadata(original_position=i))
    for i, c in enumerate(langchain_chunks)
]

# Embed with Markdown Reallocator
embedder = Embedder()
embedded = embedder.embed_batch(chunks)
```

### With FastAPI

```python
from fastapi import FastAPI, UploadFile
from markdown_reallocator.core import MarkdownPreprocessor

app = FastAPI()
preprocessor = MarkdownPreprocessor()

@app.post("/preprocess")
async def preprocess_markdown(file: UploadFile):
    markdown = await file.read()
    clean = preprocessor.preprocess(markdown.decode())
    return {"processed": clean}
```

## Next Steps

- [CLI Reference](cli-reference.md) - Command-line interface
- [API Reference](../api/index.md) - Complete API documentation
- [Examples](../examples/index.md) - Real-world use cases
