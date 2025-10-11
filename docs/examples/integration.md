# Integration Examples

Integrate Markdown Reallocator with existing tools and frameworks.

## FastAPI Integration

```python
from fastapi import FastAPI
from markdown_reallocator.core import MarkdownPreprocessor

app = FastAPI()
preprocessor = MarkdownPreprocessor()

@app.post("/process")
async def process(markdown: str):
    return preprocessor.preprocess(markdown)
```

## LangChain Integration

See [Python API Guide](../user-guide/python-api.md#with-langchain) for LangChain integration examples.
