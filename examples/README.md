# Markdown Reallocator Examples

This directory contains example documents and tutorials demonstrating the capabilities of Markdown Reallocator.

## Example Documents

### 1. `llm-generated-messy.md`

**Purpose**: Demonstrates typical LLM output with formatting issues

**Characteristics**:
- Contains bold text that should be headings (`**Introduction to RAG**`)
- Inconsistent heading hierarchy
- Some duplicate content
- Mixed formatting styles
- Real-world example of RAG system documentation

**Use Case**:
- Test the preprocessor's bold-to-heading conversion
- Validate deduplication functionality
- Demonstrate before/after improvements

**Expected Processing Results**:
- ~15-20 bold titles converted to proper headings
- Document structure becomes hierarchical
- Duplicate sections identified
- Navigation in markdown viewers works correctly

**Common Issues It Tests**:
- Standalone bold lines vs. emphasis in paragraphs
- Bold text with proper capitalization
- Empty lines before/after bold titles

---

### 2. `well-structured.md`

**Purpose**: Reference document showing proper markdown formatting

**Characteristics**:
- Correct heading hierarchy (H1 → H2 → H3)
- Proper code blocks with syntax highlighting
- Well-formatted lists and tables
- Appropriate use of bold/italic for emphasis only
- No structural issues

**Use Case**:
- Baseline comparison for preprocessing
- Test that processor doesn't break correct formatting
- Reference for expected output quality

**Expected Processing Results**:
- Minimal to no changes during preprocessing
- Clean chunk splitting along heading boundaries
- High-quality embeddings due to clear structure

**What It Demonstrates**:
- PEP 8 compliance examples
- Type hints and docstrings
- Proper testing practices
- Code organization best practices

---

### 3. `korean-content.md`

**Purpose**: Test Korean language processing capabilities

**Characteristics**:
- Mixed Korean and English content
- Korean bold titles that need conversion
- Technical terms in both languages
- Code examples with Korean comments
- Complex sentence structures

**Use Case**:
- Validate Unicode handling
- Test embedding quality for Korean text
- Ensure preprocessing works with non-ASCII
- Verify search works across languages

**Expected Processing Results**:
- Korean bold titles correctly converted to headings
- Proper character encoding maintained
- Embeddings capture Korean semantic meaning
- Search can find Korean and English terms

**Common Issues It Tests**:
- UTF-8 encoding preservation
- Korean punctuation handling
- Mixed-language chunk boundaries
- Semantic similarity in Korean

---

### 4. `large-document.md`

**Purpose**: Performance testing with large documents

**Characteristics**:
- 20,000+ lines of content
- 100 major sections
- Repetitive structure for consistency
- Mix of code, text, and examples
- Total size: ~2MB

**Use Case**:
- Benchmark preprocessing speed (target: <1s per 1000 lines)
- Test memory efficiency with many chunks
- Validate embedding generation at scale
- Stress-test search performance (target: <500ms for 1000 chunks)

**Expected Processing Results**:
- ~1000-2000 chunks generated
- Preprocessing completes in 15-20 seconds
- Embedding generation stays within GPU memory limits
- Search remains responsive

**Performance Targets**:
- Preprocessing: <1 second per 1000 lines
- Splitting: <5 seconds total
- Embedding: Variable (depends on GPU)
- Search: <500ms for similarity search

---

### 5. `edge-cases.md`

**Purpose**: Test robustness with complex markdown features

**Characteristics**:
- Tables with various formats
- Deeply nested lists (6+ levels)
- Multiple code block languages
- Blockquotes with nesting
- Special characters and escaping
- HTML mixed with markdown
- Math formulas (if supported)
- Task lists, footnotes, definition lists

**Use Case**:
- Ensure preprocessor doesn't break complex structures
- Test chunk splitting with tables and code blocks
- Validate that special characters are preserved
- Catch edge case bugs before production

**Expected Processing Results**:
- Tables remain intact after processing
- Code blocks never altered
- Nested lists preserve hierarchy
- Special characters properly escaped
- HTML tags handled appropriately

**Common Issues It Tests**:
- Bold in tables vs. bold as headings
- Code blocks with markdown-like content
- Escaped asterisks and backticks
- Very long lines (wrapping)
- Empty elements
- Unicode symbols and emojis

---

## Interactive Tutorial

### `complete-workflow.ipynb`

**Purpose**: Hands-on tutorial for the complete processing pipeline

**Contents**:
1. Setup and imports
2. Loading example documents
3. Preprocessing demonstration
4. Semantic chunking
5. Embedding generation
6. Similarity search
7. Chunk reordering
8. Deduplication
9. Exporting results
10. Performance tips

**How to Use**:
```bash
# Install Jupyter
pip install jupyter

# Start Jupyter
jupyter notebook examples/complete-workflow.ipynb
```

**Prerequisites**:
- Python 3.10+
- markdown-reallocator installed
- Ollama running with embeddinggemma model
- Internet connection (optional, for documentation links)

**Learning Outcomes**:
- Understand each pipeline stage
- See visual output with Rich formatting
- Experiment with parameters
- Learn best practices
- Troubleshoot common issues

---

## Quick Start

### Process an Example

```python
from markdown_reallocator.core import MarkdownPreprocessor, MarkdownSplitter
from pathlib import Path

# Load example
content = Path("examples/llm-generated-messy.md").read_text()

# Preprocess
preprocessor = MarkdownPreprocessor()
clean = preprocessor.preprocess(content)

# Split
splitter = MarkdownSplitter()
chunks = splitter.split(clean)

print(f"Created {len(chunks)} chunks")
```

### Run the Full Workflow

```bash
# Open the Jupyter notebook
jupyter notebook examples/complete-workflow.ipynb
```

### CLI Usage with Examples

```bash
# Preprocess a messy document
markdown-reallocator preprocess examples/llm-generated-messy.md -o output.md

# Process with full pipeline
markdown-reallocator process examples/llm-generated-messy.md \
    --reorder \
    --deduplicate \
    --output processed.md
```

---

## Test Fixtures

Located in `tests/fixtures/`, these files are used by the test suite:

### `minimal-valid.md`
- Smallest valid markdown document
- 2 sections, minimal content
- Quick validation tests

### `invalid.md`
- Intentionally malformed markdown
- Tests error handling
- Unclosed code blocks, broken links, etc.

### `known-duplicates.md`
- Document with exact and near-duplicates
- Tests deduplication accuracy
- Known expected output

### `mock-embeddings.json`
- Pre-computed embedding vectors
- Enables tests without Ollama
- 5-dimensional embeddings for simplicity

---

## Contributing Examples

To add a new example:

1. Create the markdown file in `examples/`
2. Add documentation section to this README
3. Include expected outputs or test cases
4. Update the Jupyter notebook if relevant
5. Ensure it tests a specific feature or edge case

### Example Documentation Template

```markdown
### `your-example.md`

**Purpose**: Brief description of what it demonstrates

**Characteristics**:
- Key feature 1
- Key feature 2
- Key feature 3

**Use Case**:
When to use this example

**Expected Processing Results**:
What should happen after processing

**Common Issues It Tests**:
- Issue 1
- Issue 2
```

---

## Performance Benchmarks

You can benchmark processing using these examples:

```bash
# Benchmark preprocessing
pytest benchmarks/benchmark_core.py -k preprocess

# Benchmark with large document
pytest benchmarks/ --benchmark-only -k large

# View results
cat .benchmarks/*/0001*.json | jq
```

Expected results (on reference hardware: GTX 1050):
- **llm-generated-messy.md**: <0.1s preprocessing
- **large-document.md**: 15-20s preprocessing
- **edge-cases.md**: <0.2s preprocessing

---

## Troubleshooting

### Example doesn't load in Jupyter

```bash
# Install ipykernel
pip install ipykernel
python -m ipykernel install --user
```

### Embedding generation fails

```bash
# Check Ollama is running
ollama list

# Download embeddinggemma if needed
ollama pull embeddinggemma
```

### Korean characters display incorrectly

Ensure terminal/editor uses UTF-8 encoding:
```python
import sys
print(sys.stdout.encoding)  # Should be 'utf-8'
```

---

## License

These examples are part of Markdown Reallocator and use the same MIT license. Feel free to adapt them for your projects.

---

## Further Reading

- [Main README](../README.md)
- [Documentation](https://markdown-reallocator.readthedocs.io)
- [API Reference](https://markdown-reallocator.readthedocs.io/api/)
- [GitHub Issues](https://github.com/seonghobae/markdown-reallocator/issues)
