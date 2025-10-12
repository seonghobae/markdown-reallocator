# Contributing to Markdown Reallocator

Thank you for your interest in contributing to Markdown Reallocator! This document provides guidelines and instructions for contributing.

## Code of Conduct

Be respectful, constructive, and collaborative. We welcome contributions from everyone.

## Getting Started

### Prerequisites

- Python 3.10 or newer
- Git
- Ollama (for running tests with embeddings)

### Development Setup

1. **Fork and clone the repository**

```bash
git clone https://github.com/seonghobae/markdown-reallocator.git
cd markdown-reallocator
```

2. **Create a virtual environment**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install development dependencies**

```bash
pip install -e ".[dev,docs]"
```

4. **Install pre-commit hooks**

```bash
pre-commit install
```

5. **Install Ollama and download embeddinggemma**

```bash
# Install Ollama from https://ollama.ai
ollama pull embeddinggemma
```

6. **Run tests to verify setup**

```bash
pytest tests/smoke/ -v
```

## Development Workflow

### Branching Strategy

We follow Git Flow:
- `main`: Production-ready code
- `develop`: Integration branch for features
- `feature/*`: New features
- `fix/*`: Bug fixes
- `docs/*`: Documentation updates

### Creating a Feature Branch

```bash
git checkout develop
git pull origin develop
git checkout -b feature/your-feature-name
```

### Making Changes

1. **Write code following our style guide**
   - Use ruff for linting and formatting
   - Add type hints to all functions
   - Write docstrings for public APIs

2. **Add tests for new functionality**
   - Unit tests in `tests/unit/`
   - Integration tests in `tests/integration/`
   - Smoke tests for critical paths

3. **Update documentation**
   - Add docstrings to new functions
   - Update relevant markdown docs
   - Add examples if appropriate

### Code Style

We use:
- **Ruff** for linting and formatting
- **MyPy** for type checking
- **pytest** for testing

Run checks locally:

```bash
# Lint and format
ruff check .
ruff format .

# Type check
mypy markdown_reallocator

# Run all tests
pytest tests/ -v
```

### Commit Messages

Follow conventional commits:

```
feat: add new feature
fix: resolve bug in module
docs: update documentation
test: add tests for feature
refactor: improve code structure
perf: optimize performance
chore: update dependencies
```

Examples:
```bash
git commit -m "feat: add batch processing support"
git commit -m "fix: handle edge case in preprocessor"
git commit -m "docs: add examples for search module"
```

## Testing

### Running Tests

```bash
# All tests
pytest

# Unit tests only
pytest tests/unit/ -v

# With coverage
pytest --cov=markdown_reallocator

# Specific test file
pytest tests/unit/test_preprocessor.py -v

# Skip tests requiring Ollama
pytest -m "not requires_ollama"
```

### Writing Tests

1. **Use descriptive test names**

```python
def test_preprocessor_converts_bold_to_heading():
    """Should convert standalone bold text to headings."""
    # Test implementation
```

2. **Use fixtures for reusable setup**

```python
@pytest.fixture
def sample_document():
    return "**Title**\n\nContent here."

def test_with_fixture(sample_document):
    result = process(sample_document)
    assert "## Title" in result
```

3. **Test edge cases**

```python
def test_handles_empty_input():
    """Should handle empty string without errors."""
    assert preprocess("") == ""

def test_handles_unicode():
    """Should preserve Korean characters."""
    assert preprocess("**한글 제목**") == "## 한글 제목"
```

### Test Coverage

We maintain >85% code coverage. Check coverage with:

```bash
pytest --cov=markdown_reallocator --cov-report=html
open htmlcov/index.html
```

## Performance Benchmarks

Run benchmarks to check performance:

```bash
# Run all benchmarks
pytest benchmarks/ --benchmark-only

# Specific benchmark
pytest benchmarks/benchmark_core.py::test_preprocess_medium_doc --benchmark-only

# Save results
pytest benchmarks/ --benchmark-autosave
```

Performance targets:
- Preprocessing: <1s per 1000 lines
- Embedding: <10s for 50 chunks
- Search: <500ms for 1000 chunks

## Documentation

### Building Docs Locally

```bash
# Install docs dependencies
pip install -e ".[docs]"

# Build docs
cd docs
mkdocs serve

# Open http://127.0.0.1:8000
```

### Writing Docstrings

Use Google-style docstrings:

```python
def process_document(content: str, max_tokens: int = 500) -> list[Chunk]:
    """Process markdown document into chunks.

    Args:
        content: Raw markdown content to process
        max_tokens: Maximum tokens per chunk (default: 500)

    Returns:
        List of processed chunks with metadata

    Raises:
        ValueError: If max_tokens is less than 50

    Example:
        >>> chunks = process_document("# Title\\n\\nContent")
        >>> len(chunks)
        1
    """
```

## Pull Request Process

1. **Update your branch**

```bash
git checkout develop
git pull origin develop
git checkout your-feature-branch
git rebase develop
```

2. **Push your changes**

```bash
git push origin your-feature-branch
```

3. **Create pull request**
   - Go to GitHub and create PR from your branch to `develop`
   - Fill out the PR template
   - Link related issues

4. **PR requirements**
   - All tests pass
   - Code coverage maintained (>85%)
   - Documentation updated
   - Changelog entry added (if applicable)
   - Pre-commit hooks pass

5. **Review process**
   - Maintainers will review your PR
   - Address review comments
   - Once approved, your PR will be merged

## Release Process

(For maintainers)

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create release branch: `git checkout -b release/v0.2.0`
4. Merge to `main` and tag: `git tag v0.2.0`
5. Push tag: `git push origin v0.2.0`
6. GitHub Actions will publish to PyPI

## Reporting Bugs

Use the GitHub issue tracker:

1. **Check existing issues** to avoid duplicates
2. **Use issue template** when creating new issue
3. **Provide details**:
   - Python version
   - OS and GPU info
   - Steps to reproduce
   - Expected vs actual behavior
   - Minimal code example

## Feature Requests

1. **Check roadmap** in README or issues
2. **Open discussion** before implementing
3. **Describe use case** and benefits
4. **Consider alternatives** and trade-offs

## Questions?

- **Issues**: For bugs and feature requests
- **Discussions**: For questions and ideas
- **Discord**: [Coming soon]

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Recognition

Contributors are recognized in:
- GitHub contributors page
- CHANGELOG.md for significant contributions
- README.md for major features

Thank you for contributing! 🎉
