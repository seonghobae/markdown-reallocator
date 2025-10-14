"""Quick start example for markdown-reallocator library.

This example demonstrates basic usage of the HybridMarkdownParser
to parse markdown files and analyze document structure.
"""

from markdown_reallocator.core.parser import HybridMarkdownParser
from markdown_reallocator.models.chunk import ElementType


def main():
    """Demonstrate basic library usage."""

    # Create parser instance
    parser = HybridMarkdownParser(max_tokens_per_chunk=1000)

    # Example markdown content
    markdown_text = """# Introduction

This is a sample markdown document.

## Section 1: Getting Started

### Stage 1: Setup

First, install the dependencies:

```bash
pip install markdown-reallocator
```

### Stage 2: Usage

Import and use the parser:

```python
from markdown_reallocator.core.parser import HybridMarkdownParser
parser = HybridMarkdownParser()
```

## Section 2: Advanced Features

- Semantic chunking
- Hierarchical header tracking
- Element type classification
- Sequence number detection

## Conclusion

This concludes the example.
"""

    # Parse the markdown
    print("Parsing markdown...")
    chunks = parser.parse_text(markdown_text)

    print(f"\n✅ Parsed {len(chunks)} chunks\n")

    # Analyze structure
    print("=" * 60)
    print("Document Structure Analysis")
    print("=" * 60)

    # Header hierarchy
    h1_headers = set(c.metadata.h1 for c in chunks if c.metadata.h1)
    h2_headers = set(c.metadata.h2 for c in chunks if c.metadata.h2)
    h3_headers = set(c.metadata.h3 for c in chunks if c.metadata.h3)

    print(f"\nHeaders:")
    print(f"  H1: {len(h1_headers)} headers")
    for h1 in sorted(h1_headers):
        print(f"    - {h1}")

    print(f"\n  H2: {len(h2_headers)} headers")
    for h2 in sorted(h2_headers):
        print(f"    - {h2}")

    print(f"\n  H3: {len(h3_headers)} headers")
    for h3 in sorted(h3_headers):
        print(f"    - {h3}")

    # Element types
    element_counts = {}
    for chunk in chunks:
        etype = chunk.metadata.element_type.value if chunk.metadata.element_type else "unknown"
        element_counts[etype] = element_counts.get(etype, 0) + 1

    print(f"\nElement Types:")
    for etype, count in sorted(element_counts.items(), key=lambda x: -x[1]):
        print(f"  {etype}: {count}")

    # Sequence numbers (procedural steps)
    sequenced = [c for c in chunks if c.metadata.sequence_number is not None]
    if sequenced:
        print(f"\nProcedural Steps Detected:")
        for chunk in sequenced:
            print(f"  Stage {chunk.metadata.sequence_number}: {chunk.content[:50]}...")

    # Token statistics
    token_counts = [c.metadata.token_count for c in chunks]
    print(f"\nToken Statistics:")
    print(f"  Total tokens: {sum(token_counts)}")
    print(f"  Average: {sum(token_counts) / len(token_counts):.1f}")
    print(f"  Min: {min(token_counts)}")
    print(f"  Max: {max(token_counts)}")

    # Display first few chunks
    print("\n" + "=" * 60)
    print("First 5 Chunks")
    print("=" * 60)

    for i, chunk in enumerate(chunks[:5], 1):
        print(f"\nChunk {i}:")
        print(f"  ID: {chunk.chunk_id}")
        print(f"  Type: {chunk.metadata.element_type.value if chunk.metadata.element_type else 'unknown'}")
        print(f"  Headers: h1={chunk.metadata.h1}, h2={chunk.metadata.h2}, h3={chunk.metadata.h3}")
        print(f"  Tokens: {chunk.metadata.token_count}")
        print(f"  Content: {chunk.content[:100]}...")


if __name__ == "__main__":
    main()
