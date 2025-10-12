# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Batch processing support for multiple files
- JSON schema-based classification
- Performance optimizations with Numba
- Rust extension for CPU-intensive preprocessing

## [0.1.0] - 2025-10-12

### Added
- **Core Modules**
  - `MarkdownPreprocessor`: Automatically converts bold titles to proper headings
  - `MarkdownSplitter`: Semantic chunking with heading hierarchy
  - `Embedder`: Local embedding generation via Ollama/embeddinggemma

- **Application Modules**
  - `SearchModule`: Semantic search with cosine similarity
  - `ReorderModule`: Sequential and clustering-based reordering
  - `DeduplicationModule`: Intelligent duplicate removal

- **CLI Interface**
  - `markdown-reallocator preprocess`: Fix markdown structure
  - `markdown-reallocator split`: Create semantic chunks
  - `markdown-reallocator search`: Find similar content
  - `markdown-reallocator process`: Full pipeline with all operations

- **Configuration System**
  - YAML/JSON configuration support
  - Environment-based settings
  - Model selection and parameters

- **Testing & Quality**
  - Comprehensive test suite with 93.86% coverage
  - Unit, integration, and smoke tests
  - Performance benchmarks
  - Example documents and fixtures

- **Documentation**
  - MkDocs documentation website
  - API reference with docstrings
  - Usage examples and tutorials
  - Jupyter notebook for interactive learning

- **CI/CD**
  - GitHub Actions workflows for testing
  - Automated linting and type checking
  - Performance benchmarking
  - Code coverage reporting

- **Examples**
  - LLM-generated messy markdown
  - Well-structured reference document
  - Korean language testing
  - Large document (20,000+ lines) for performance
  - Edge cases (tables, nested lists, code blocks)

### Features

#### Bold-to-Heading Conversion
- Detects standalone bold lines and converts to headings
- Uses context heuristics (empty lines, capitalization, length)
- Preserves intentional bold emphasis in paragraphs
- Protects code blocks and special syntax
- 95%+ accuracy in distinguishing titles from emphasis

#### Semantic Operations
- **Chunking**: Splits documents preserving heading hierarchy
- **Search**: Natural language queries with embedding similarity
- **Reordering**: Organizes chunks by semantic flow or topics
- **Deduplication**: Removes redundant content intelligently

#### Resource Efficiency
- Runs on consumer GPUs (2-4GB VRAM)
- embeddinggemma model support (860MB)
- Optional CPU-only mode
- Memory-efficient batch processing

### Technical Details

#### Dependencies
- Python 3.10+
- langchain-text-splitters >=0.2.0
- numpy >=1.24.0,<2.0.0
- scikit-learn >=1.3.0
- ollama >=0.1.0
- typer[all] >=0.9.0
- rich >=13.0.0
- pyyaml >=6.0

#### Performance Metrics
- Preprocessing: <1s per 1000 lines
- Embedding: <10s for 50 chunks
- Search: <500ms for 1000 chunks
- Peak GPU memory: ≤1.8GB (with both models)

#### Test Coverage
- Overall: 93.86%
- Core modules: 95%+
- Application modules: 90%+
- CLI: 85%+

### Documentation

- README with quick start guide
- Complete API documentation
- Examples directory with 5 diverse documents
- Jupyter notebook tutorial
- Contributing guidelines
- CI/CD setup guide

### Infrastructure

- Git Flow branching model
- GitHub Actions CI/CD
- Dependabot for dependency updates
- Pre-commit hooks for code quality
- Automated PyPI publishing

## [0.0.1] - 2025-10-11

### Added
- Initial project structure
- Basic data models (Chunk, Embedding, Metadata)
- Core preprocessing functionality

---

## Release Types

- **Major (X.0.0)**: Breaking API changes
- **Minor (0.X.0)**: New features, backward compatible
- **Patch (0.0.X)**: Bug fixes, backward compatible

## Upgrade Guide

### From 0.0.x to 0.1.0

This is the first stable release. Key changes:

1. **Install/Update**:
   ```bash
   pip install --upgrade markdown-reallocator
   ```

2. **API Changes**: None (first release)

3. **Configuration**:
   - New YAML/JSON config support
   - See `examples/config.yaml` for template

4. **CLI Commands**:
   ```bash
   # Old (not available)
   # No previous CLI

   # New
   markdown-reallocator process input.md --output output.md
   ```

## Migration Notes

### Breaking Changes in Future Versions

We'll document any breaking changes here for easy migration.

## Known Issues

See [GitHub Issues](https://github.com/seonghobae/markdown-reallocator/issues) for current known issues.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and contribution guidelines.

## Support

- **Documentation**: https://markdown-reallocator.readthedocs.io
- **Issues**: https://github.com/seonghobae/markdown-reallocator/issues
- **Discussions**: https://github.com/seonghobae/markdown-reallocator/discussions

---

[Unreleased]: https://github.com/seonghobae/markdown-reallocator/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/seonghobae/markdown-reallocator/releases/tag/v0.1.0
[0.0.1]: https://github.com/seonghobae/markdown-reallocator/releases/tag/v0.0.1
