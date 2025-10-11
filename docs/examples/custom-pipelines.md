# Custom Pipelines

Build custom processing workflows with the Python API.

## Example: Conditional Processing

```python
from markdown_reallocator.core import MarkdownPreprocessor, MarkdownSplitter, Embedder
from markdown_reallocator.modules import DeduplicationModule

def process_document(markdown, remove_duplicates=True):
    preprocessor = MarkdownPreprocessor()
    splitter = MarkdownSplitter()
    embedder = Embedder()
    
    clean = preprocessor.preprocess(markdown)
    chunks = splitter.split(clean)
    embedded = embedder.embed_batch(chunks)
    
    if remove_duplicates:
        dedup = DeduplicationModule()
        embedded, _ = dedup.deduplicate(embedded)
    
    return embedded
```

See [Python API Guide](../user-guide/python-api.md) for more examples.
