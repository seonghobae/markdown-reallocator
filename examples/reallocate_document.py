"""Reallocate document chunks by semantic sections."""

import sys
from pathlib import Path
from typing import Dict, List

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from markdown_reallocator.core.parser import HybridMarkdownParser
from markdown_reallocator.models.chunk import Chunk


def reallocate_by_h2(chunks: List[Chunk]) -> Dict[str, List[Chunk]]:
    """Reallocate chunks by h2 sections within h1.

    Returns:
        Dict mapping (h1, h2) to list of chunks
    """
    sections = {}

    for chunk in chunks:
        h1 = chunk.metadata.h1 or "(No h1)"
        h2 = chunk.metadata.h2 or "(No h2)"
        key = f"{h1} > {h2}"

        if key not in sections:
            sections[key] = []
        sections[key].append(chunk)

    return sections


def reconstruct_markdown(sections: Dict[str, List[Chunk]]) -> str:
    """Reconstruct markdown from reallocated sections.

    Args:
        sections: Dict mapping section names to chunks

    Returns:
        Reconstructed markdown text
    """
    output = []

    # Group by h1 first
    h1_groups = {}
    for section_key, chunks in sections.items():
        h1 = chunks[0].metadata.h1 if chunks else "(No h1)"
        if h1 not in h1_groups:
            h1_groups[h1] = {}
        h1_groups[h1][section_key] = chunks

    # Reconstruct with proper hierarchy
    for h1, h2_sections in sorted(h1_groups.items()):
        # Add h1 header
        if h1 != "(No h1)":
            output.append(f"# {h1}\n")

        for section_key, chunks in sorted(h2_sections.items()):
            h2 = chunks[0].metadata.h2 if chunks else "(No h2)"

            # Add h2 header
            if h2 != "(No h2)":
                output.append(f"## {h2}\n")

            # Add all chunk content
            for chunk in chunks:
                # Skip if content is just the header itself
                if chunk.content.strip().startswith('#'):
                    continue
                output.append(chunk.content)
                output.append("\n")

            output.append("\n")

    return "\n".join(output)


def analyze_section_sizes(sections: Dict[str, List[Chunk]], max_tokens: int = 1000):
    """Analyze section sizes and identify oversized sections."""
    print("=" * 80)
    print("Section Size Analysis")
    print("=" * 80)
    print()

    section_stats = []
    for section_key, chunks in sections.items():
        total_tokens = sum(c.metadata.token_count for c in chunks)
        section_stats.append({
            'key': section_key,
            'chunks': len(chunks),
            'tokens': total_tokens,
            'oversized': total_tokens > max_tokens
        })

    # Sort by token count
    section_stats.sort(key=lambda x: x['tokens'], reverse=True)

    oversized = [s for s in section_stats if s['oversized']]

    print(f"Total sections: {len(section_stats)}")
    print(f"Oversized sections (>{max_tokens} tokens): {len(oversized)}")
    print()

    if oversized:
        print("Oversized sections requiring splitting:")
        for i, stat in enumerate(oversized[:10], 1):
            print(f"\n{i}. {stat['key']}")
            print(f"   Chunks: {stat['chunks']}")
            print(f"   Tokens: {stat['tokens']} (⚠️  {stat['tokens'] - max_tokens} over limit)")

    print()
    print("Top 10 largest sections:")
    for i, stat in enumerate(section_stats[:10], 1):
        status = "⚠️" if stat['oversized'] else "✅"
        print(f"{i}. {status} {stat['key'][:70]}...")
        print(f"   Chunks: {stat['chunks']}, Tokens: {stat['tokens']}")

    return section_stats


def split_oversized_section(chunks: List[Chunk], max_tokens: int = 1000) -> List[List[Chunk]]:
    """Split oversized section into smaller sub-sections by h3.

    Args:
        chunks: List of chunks in the section
        max_tokens: Maximum tokens per sub-section

    Returns:
        List of sub-sections (each is a list of chunks)
    """
    # Group by h3
    h3_groups = {}
    current_h3 = None

    for chunk in chunks:
        h3 = chunk.metadata.h3 or "(No h3)"
        if h3 != current_h3:
            current_h3 = h3

        if h3 not in h3_groups:
            h3_groups[h3] = []
        h3_groups[h3].append(chunk)

    # Create sub-sections respecting h3 boundaries
    sub_sections = []
    current_subsection = []
    current_tokens = 0

    for h3, h3_chunks in h3_groups.items():
        h3_tokens = sum(c.metadata.token_count for c in h3_chunks)

        if current_tokens + h3_tokens > max_tokens and current_subsection:
            # Start new sub-section
            sub_sections.append(current_subsection)
            current_subsection = h3_chunks.copy()
            current_tokens = h3_tokens
        else:
            current_subsection.extend(h3_chunks)
            current_tokens += h3_tokens

    if current_subsection:
        sub_sections.append(current_subsection)

    return sub_sections


def main():
    """Main reallocation workflow."""
    # Parse document
    print("Parsing document...")
    parser = HybridMarkdownParser(max_tokens_per_chunk=1000)
    chunks = parser.parse_file("test_doc_AGENTS.md")
    print(f"Parsed {len(chunks)} chunks")
    print()

    # Reallocate by h2 sections
    print("Reallocating by h2 sections...")
    sections = reallocate_by_h2(chunks)
    print(f"Created {len(sections)} sections")
    print()

    # Analyze section sizes
    section_stats = analyze_section_sizes(sections, max_tokens=1000)

    # Split oversized sections
    oversized_sections = [s for s in section_stats if s['oversized']]
    if oversized_sections:
        print()
        print("=" * 80)
        print("Splitting Oversized Sections")
        print("=" * 80)
        print()

        for stat in oversized_sections[:3]:  # Show first 3
            section_key = stat['key']
            section_chunks = sections[section_key]

            print(f"Splitting: {section_key}")
            print(f"  Original: {stat['chunks']} chunks, {stat['tokens']} tokens")

            sub_sections = split_oversized_section(section_chunks, max_tokens=1000)

            print(f"  Split into: {len(sub_sections)} sub-sections")
            for i, sub in enumerate(sub_sections, 1):
                sub_tokens = sum(c.metadata.token_count for c in sub)
                status = "✅" if sub_tokens <= 1000 else "⚠️"
                print(f"    Sub-section {i}: {len(sub)} chunks, {sub_tokens} tokens {status}")
            print()

    # Reconstruct markdown
    print("=" * 80)
    print("Reconstructing Markdown")
    print("=" * 80)
    print()

    reconstructed = reconstruct_markdown(sections)

    # Save to file
    output_file = "test_doc_AGENTS_reallocated.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(reconstructed)

    print(f"✅ Reallocated document saved to: {output_file}")
    print(f"   Original size: {len(''.join(c.content for c in chunks))} chars")
    print(f"   Reconstructed size: {len(reconstructed)} chars")
    print()

    # Show sample of reconstructed markdown
    print("Sample of reconstructed markdown (first 1000 chars):")
    print("-" * 80)
    print(reconstructed[:1000])
    print("...")
    print("-" * 80)


if __name__ == "__main__":
    main()
