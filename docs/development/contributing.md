# Contributing

Thank you for your interest in contributing to Markdown Reallocator!

## Getting Started

1. Fork the repository
2. Clone your fork
3. Install development dependencies:

```bash
git clone https://github.com/yourusername/markdown-reallocator.git
cd markdown-reallocator
pip install -e ".[dev]"
```

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

- Write code
- Add tests
- Update documentation

### 3. Run Tests

```bash
pytest
```

### 4. Check Code Quality

```bash
ruff check .
mypy markdown_reallocator
```

### 5. Submit Pull Request

- Push to your fork
- Create pull request
- Describe your changes

## Guidelines

### Code Style

- Follow PEP 8
- Use type hints
- Write docstrings (Google style)

### Testing

- Add tests for new features
- Maintain 85%+ coverage
- Include smoke tests for major features

### Documentation

- Update relevant docs
- Add examples for new features
- Keep README updated

## Questions?

Open an issue or discussion on GitHub.
