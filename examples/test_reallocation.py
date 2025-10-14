"""Test document reallocation with hybrid parser."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from markdown_reallocator.core.parser import HybridMarkdownParser
from markdown_reallocator.models.chunk import ElementType


def analyze_document(filepath: str):
    """Analyze document structure and chunking."""
    print("=" * 80)
    print(f"Analyzing: {filepath}")
    print("=" * 80)
    print()

    # Parse with hybrid parser
    parser = HybridMarkdownParser(max_tokens_per_chunk=1000)
    chunks = parser.parse_file(filepath)

    print(f"Total chunks: {len(chunks)}")
    print()

    # Analyze header hierarchy
    h1_values = sorted(set(c.metadata.h1 for c in chunks if c.metadata.h1 is not None))
    h2_values = sorted(set(c.metadata.h2 for c in chunks if c.metadata.h2 is not None))
    h3_values = sorted(set(c.metadata.h3 for c in chunks if c.metadata.h3 is not None))

    print(f"Unique h1 headers: {len(h1_values)}")
    for h1 in h1_values:
        print(f"  - {h1}")
    print()

    print(f"Unique h2 headers: {len(h2_values)}")
    for h2 in h2_values[:10]:  # Show first 10
        print(f"  - {h2}")
    if len(h2_values) > 10:
        print(f"  ... and {len(h2_values) - 10} more")
    print()

    print(f"Unique h3 headers: {len(h3_values)}")
    for h3 in h3_values[:10]:  # Show first 10
        print(f"  - {h3}")
    if len(h3_values) > 10:
        print(f"  ... and {len(h3_values) - 10} more")
    print()

    # Element type distribution
    element_counts = {}
    for chunk in chunks:
        etype = chunk.metadata.element_type.value if chunk.metadata.element_type else "None"
        element_counts[etype] = element_counts.get(etype, 0) + 1

    print("Element type distribution:")
    for etype, count in sorted(element_counts.items(), key=lambda x: -x[1]):
        print(f"  {etype}: {count}")
    print()

    # Token statistics
    token_counts = [c.metadata.token_count for c in chunks]
    avg_tokens = sum(token_counts) / len(token_counts) if token_counts else 0
    max_tokens = max(token_counts) if token_counts else 0
    min_tokens = min(token_counts) if token_counts else 0

    print(f"Token statistics:")
    print(f"  Average: {avg_tokens:.1f}")
    print(f"  Min: {min_tokens}")
    print(f"  Max: {max_tokens}")
    print()

    # Oversized chunks (> max_tokens_per_chunk)
    oversized = [c for c in chunks if c.metadata.token_count > parser.max_tokens_per_chunk]
    if oversized:
        print(f"⚠️  Oversized chunks (>{parser.max_tokens_per_chunk} tokens): {len(oversized)}")
        for i, chunk in enumerate(oversized[:5]):
            print(f"  Chunk {chunk.metadata.original_position}:")
            print(f"    Tokens: {chunk.metadata.token_count}")
            print(f"    Headers: h1={chunk.metadata.h1}, h2={chunk.metadata.h2}, h3={chunk.metadata.h3}")
            print(f"    Type: {chunk.metadata.element_type.value if chunk.metadata.element_type else 'None'}")
            print(f"    Content preview: {chunk.content[:100]}...")
            print()
        if len(oversized) > 5:
            print(f"  ... and {len(oversized) - 5} more oversized chunks")
    else:
        print(f"✅ No oversized chunks (all <= {parser.max_tokens_per_chunk} tokens)")
    print()

    # Show first 10 chunks with hierarchy
    print("First 10 chunks with hierarchy:")
    for i, chunk in enumerate(chunks[:10]):
        print(f"\nChunk {i} (pos={chunk.metadata.original_position}):")
        print(f"  Headers: h1={chunk.metadata.h1}")
        print(f"           h2={chunk.metadata.h2}")
        print(f"           h3={chunk.metadata.h3}")
        print(f"  Type: {chunk.metadata.element_type.value if chunk.metadata.element_type else 'None'}")
        print(f"  Tokens: {chunk.metadata.token_count}")
        print(f"  Content: {chunk.content[:80]}...")

    print()
    print("=" * 80)
    print("Analysis complete")
    print("=" * 80)

    return chunks


def test_reallocation_by_h1(chunks):
    """Test reallocation: group chunks by h1 header."""
    print()
    print("=" * 80)
    print("Testing reallocation by h1 header")
    print("=" * 80)
    print()

    # Group chunks by h1
    h1_groups = {}
    for chunk in chunks:
        h1 = chunk.metadata.h1 or "(No h1)"
        if h1 not in h1_groups:
            h1_groups[h1] = []
        h1_groups[h1].append(chunk)

    print(f"Total h1 groups: {len(h1_groups)}")
    print()

    for h1, group_chunks in sorted(h1_groups.items(), key=lambda x: len(x[1]), reverse=True)[:5]:
        total_tokens = sum(c.metadata.token_count for c in group_chunks)
        print(f"h1: {h1}")
        print(f"  Chunks: {len(group_chunks)}")
        print(f"  Total tokens: {total_tokens}")
        print(f"  h2 sections: {len(set(c.metadata.h2 for c in group_chunks if c.metadata.h2))}")
        print()


def test_reallocation_by_h2(chunks):
    """Test reallocation: group chunks by h2 header within same h1."""
    print()
    print("=" * 80)
    print("Testing reallocation by h2 header (within h1)")
    print("=" * 80)
    print()

    # Group chunks by (h1, h2)
    h1h2_groups = {}
    for chunk in chunks:
        h1 = chunk.metadata.h1 or "(No h1)"
        h2 = chunk.metadata.h2 or "(No h2)"
        key = (h1, h2)
        if key not in h1h2_groups:
            h1h2_groups[key] = []
        h1h2_groups[key].append(chunk)

    print(f"Total (h1, h2) groups: {len(h1h2_groups)}")
    print()

    # Show top 10 by chunk count
    for (h1, h2), group_chunks in sorted(h1h2_groups.items(), key=lambda x: len(x[1]), reverse=True)[:10]:
        total_tokens = sum(c.metadata.token_count for c in group_chunks)
        print(f"h1: {h1}")
        print(f"h2: {h2}")
        print(f"  Chunks: {len(group_chunks)}")
        print(f"  Total tokens: {total_tokens}")
        print()


if __name__ == "__main__":
    # Analyze document
    chunks = analyze_document("test_doc_AGENTS.md")

    # Test reallocation strategies
    test_reallocation_by_h1(chunks)
    test_reallocation_by_h2(chunks)
