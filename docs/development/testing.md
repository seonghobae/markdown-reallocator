# Testing

Guide to running and writing tests.

## Running Tests

### All Tests

```bash
pytest
```

### Specific Test Types

```bash
# Smoke tests only (fast)
pytest tests/smoke/

# Unit tests only
pytest tests/unit/

# Integration tests
pytest tests/integration/
```

### With Coverage

```bash
pytest --cov=markdown_reallocator --cov-report=html
```

## Writing Tests

### Unit Tests

```python
def test_preprocessor():
    preprocessor = MarkdownPreprocessor()
    result = preprocessor.preprocess("**Title**")
    assert "## Title" in result
```

### Integration Tests

```python
@patch.object(Embedder, "embed_chunk")
def test_full_pipeline(mock_embed):
    # Test complete workflow
    pass
```

### Smoke Tests

Quick validation tests that run in <10 seconds:

```python
def test_import_modules():
    from markdown_reallocator.core import embedder
    assert embedder is not None
```

## Test Coverage

Current coverage: 93.86%

Goal: Maintain 85%+ coverage for all new code.
