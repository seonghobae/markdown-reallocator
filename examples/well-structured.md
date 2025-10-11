# Python Best Practices Guide

A comprehensive guide to writing clean, maintainable Python code.

## Introduction

This document serves as a reference for proper markdown structure and Python best practices. It demonstrates correct heading hierarchy, code formatting, and document organization.

## Code Style

### PEP 8 Compliance

Python Enhancement Proposal 8 (PEP 8) is the style guide for Python code. Following PEP 8 makes your code more readable and consistent with the broader Python community.

Key principles:
- Use 4 spaces for indentation
- Limit lines to 79 characters (or 100 for modern projects)
- Use snake_case for functions and variables
- Use PascalCase for classes

### Type Hints

Type hints improve code readability and enable static type checking with tools like mypy:

```python
def greet(name: str) -> str:
    return f"Hello, {name}!"

def calculate_total(items: list[dict[str, float]]) -> float:
    return sum(item["price"] for item in items)
```

### Docstrings

Document your functions and classes with docstrings:

```python
def process_document(content: str, max_length: int = 1000) -> list[str]:
    """Split document into chunks of maximum length.

    Args:
        content: The document content to process
        max_length: Maximum characters per chunk

    Returns:
        List of document chunks

    Raises:
        ValueError: If max_length is less than 1
    """
    if max_length < 1:
        raise ValueError("max_length must be >= 1")

    chunks = []
    # Implementation here
    return chunks
```

## Testing

### Unit Tests with pytest

Write comprehensive tests for your code:

```python
import pytest

def test_greet_basic():
    """Should return greeting with name."""
    assert greet("World") == "Hello, World!"

def test_greet_empty_raises():
    """Should raise ValueError for empty name."""
    with pytest.raises(ValueError):
        greet("")
```

### Test Fixtures

Use fixtures for reusable test setup:

```python
@pytest.fixture
def sample_data():
    """Create sample test data."""
    return {"key": "value", "count": 42}

def test_with_fixture(sample_data):
    """Test using fixture data."""
    assert sample_data["count"] == 42
```

## Error Handling

### Specific Exceptions

Catch specific exceptions rather than bare `except:`:

```python
# Good
try:
    result = process_file(path)
except FileNotFoundError:
    logger.error(f"File not found: {path}")
except PermissionError:
    logger.error(f"Permission denied: {path}")

# Bad
try:
    result = process_file(path)
except:  # Too broad!
    pass
```

### Context Managers

Use context managers for resource management:

```python
with open("data.txt") as f:
    content = f.read()
    # File automatically closed after this block
```

## Performance

### List Comprehensions

Prefer list comprehensions over `map()` and `filter()` for simple operations:

```python
# Clear and Pythonic
squares = [x**2 for x in range(10)]
evens = [x for x in range(10) if x % 2 == 0]

# Less readable
squares = list(map(lambda x: x**2, range(10)))
```

### Generators for Large Data

Use generators when working with large datasets to save memory:

```python
def read_large_file(path: str):
    """Read file line by line without loading all into memory."""
    with open(path) as f:
        for line in f:
            yield line.strip()

# Process without loading entire file
for line in read_large_file("huge.txt"):
    process(line)
```

## Dependencies

### Virtual Environments

Always use virtual environments to isolate project dependencies:

```bash
# Create virtual environment
python -m venv venv

# Activate (Unix/Mac)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Dependency Management

Pin your dependencies for reproducibility:

```txt
# requirements.txt
numpy>=1.24.0,<2.0.0
pytest>=7.4.0
ruff>=0.1.0
```

## Conclusion

Following these best practices leads to more maintainable, reliable, and professional Python code. Remember that consistency is key - pick a style and stick with it throughout your project.

## References

- [PEP 8 Style Guide](https://peps.python.org/pep-0008/)
- [Python Type Hints (PEP 484)](https://peps.python.org/pep-0484/)
- [pytest Documentation](https://docs.pytest.org/)
- [Real Python Tutorials](https://realpython.com/)
