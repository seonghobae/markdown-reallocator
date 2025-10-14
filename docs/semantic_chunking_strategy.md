# Semantic Chunking Strategy

## Executive Summary

**Decision**: Allow chunks to slightly exceed token limits (average 1.8% overflow) to preserve semantic completeness.

**Rationale**: For technical documentation with sequential policies and protocols, semantic completeness is more important than strict token adherence.

## Background

After implementing semantic boundary splitting with h4-h6 header support, we tested the system with AGENTS.md (227KB), a large technical documentation file containing policies and protocols.

### Test Results (AGENTS.md)
```
Total chunks: 205
Oversized chunks: 15 (7.3%)
Average overflow: +9 tokens (1.8% over 500 limit)
Maximum overflow: +16 tokens (3.2% over 500 limit)
Average chunk size: 170.5 tokens
```

All 15 oversized chunks shared common characteristics:
- 12-47 list items per chunk
- Policy/protocol sections (e.g., "Multi-Agent Task Protocol", "Risk-Adaptive Review Protocol")
- Each chunk is semantically complete
- Sequential or hierarchical dependencies between list items

## Chunking Philosophy

### Core Principle (Pinecone)

> "If the chunk of text makes sense without the surrounding context to a human, it will make sense to the language model as well."

This principle guides our decision: **semantic completeness > strict token limits**.

### Two Types of Lists

#### Independent Lists (Text-Splitting Appropriate)
```markdown
## Movie Recommendations
- The Shawshank Redemption
- The Godfather
- The Dark Knight
- Pulp Fiction
- Inception
```
Each item is standalone → Can split anywhere

#### Dependent Lists (Semantic Preservation Required)
```markdown
## Multi-Agent Task Protocol (Sequential Procedure)
1. Role identification: Check task with read_task
2. Implementation: Write code based on role from step 1
3. Audit: Verify implementation from step 2
4. Approval: Complete if audit from step 3 passes
```
Sequential dependencies → **Must keep complete**

## Industry Comparison

### Unstructured.io Approach

**Strategy**: Enforce hard maximum via text-splitting

```python
chunk_by_title(elements, max_characters=500)
# If element > 500 → force text-splitting
```

**Philosophy**:
> "A single element that by itself exceeds the maximum chunk size is divided into two or more chunks using text-splitting."

**Assumption**: List items are independent

**Use Case**: General documents (news, reports, books)

### Docling Approach

**Strategy**: Merge list items by default

```python
HierarchicalChunker(merge_list_items=True)  # Default
```

**Philosophy**: Respect document structure, keep semantic units together

### Our Approach

**Strategy**: Allow slight overflow to preserve semantic completeness

```python
splitter = MarkdownSplitter(max_tokens_per_chunk=500)
# If chunk > 500 but is semantically complete → keep intact + warn
```

**Philosophy**: For technical documentation with sequential/dependent lists, completeness > strict limits

**Use Case**: Technical policies, protocols, procedures

## Solution Analysis

We evaluated three approaches:

### Option A: Keep Current State (CHOSEN)

**Trade-offs**:
- ❌ 15 chunks (7.3%) exceed limit by average 1.8%
- ✅ All policies remain semantically complete
- ✅ Search quality optimal (complete context)
- ✅ Users get full procedures, not fragments

**Why Chosen**:
1. AGENTS.md contains sequential policies, not independent items
2. Breaking policies destroys meaning (e.g., "Step 1" without "Step 2")
3. 1.8% overflow is negligible for semantic integrity
4. Aligns with Pinecone principle

### Option B: Text-Splitting (REJECTED)

**Example Impact**:
```
Original (516 tokens, semantically complete):
#### Multi-Agent Protocol
1. Role identification: read_task...
2. Implementation: write code...
3. Audit: verify...
...12 sequential steps...

After Text-Splitting (2 chunks of 250 tokens each):
Chunk 1: Steps 1-6 (incomplete procedure)
Chunk 2: Steps 7-12 (missing context from steps 1-6)
```

**Why Rejected**:
- ❌ Destroys policy completeness
- ❌ Search returns incomplete procedures
- ❌ Users need to read multiple chunks to understand one policy
- ❌ Violates semantic chunking principle

### Option C: List Item Independence Analysis (REJECTED)

**Concept**: Use NLP to determine if list items are independent, only split independent ones

**Why Rejected**:
- ❌ High implementation complexity
- ❌ Accuracy uncertain (Korean/English mixed docs)
- ❌ Most policy lists in AGENTS.md are sequential/hierarchical
- ❌ Over-engineering for 7.3% of chunks

## Implementation Guidance

### When to Allow Overflow

✅ **Allow** when:
- Content is a complete semantic unit (policy, protocol, procedure)
- List items have sequential dependencies ("Step 1", "then", "after")
- Breaking would lose critical context
- Overflow is < 5% of limit

❌ **Don't allow** when:
- Content is genuinely too large (> 20% over limit)
- List items are independent (movie recommendations, shopping items)
- Clear semantic boundaries exist within the chunk

### Code Implementation

```python
def _split_list_items_semantically(self, content: str, max_tokens: int) -> list[str]:
    """Split list items while preserving semantic boundaries."""

    # Parse all list items
    items = self._parse_list_items(content)

    # Try to fit items under limit
    chunks = self._group_items_under_limit(items, max_tokens)

    # If a single group exceeds limit but is semantically complete
    for chunk in chunks:
        chunk_tokens = estimate_tokens(chunk)
        if chunk_tokens > max_tokens:
            # Check if it's a complete semantic unit
            if self._is_semantically_complete(chunk):
                # Log warning but keep intact
                logger.warning(
                    f"Chunk exceeds {max_tokens} tokens ({chunk_tokens}) "
                    f"but is semantically complete. Keeping intact."
                )
                # Don't force-split
            else:
                # Has internal boundaries, can split
                chunk = self._split_at_boundaries(chunk, max_tokens)

    return chunks
```

## Validation Results

### Coverage Achievement
- **Target**: 85%
- **Achieved**: 97.83%
- **Status**: ✅ PASSED (+12.83% above target)

### Real Document Testing (AGENTS.md)
- **Size**: 227KB (larger than typical 128KB documents)
- **Total chunks**: 205
- **Oversized**: 15 (7.3%)
- **Average overflow**: 1.8%
- **Status**: ✅ ACCEPTABLE (semantic completeness preserved)

### Search Quality Impact
All 15 oversized chunks contain:
- Complete policies (e.g., "Multi-Agent Task Status Verification")
- Full protocols (e.g., "Implementation vs Audit Parallelism")
- Entire procedures (e.g., "Risk-Adaptive Review Protocol")

Users searching for these topics will get complete, actionable information in a single chunk.

## Future Considerations

### If Overflow Increases
If future documents show > 10% oversized chunks or > 5% average overflow:

1. **First**: Analyze document structure
   - Are there missing semantic boundaries?
   - Can we add h4-h6 headers?
   - Are policies too long?

2. **Then**: Consider document-level solutions
   - Suggest manual header insertion
   - Recommend splitting large policies
   - Use different max_tokens for different doc types

3. **Last Resort**: Implement hybrid approach
   - Text-split only truly independent lists
   - Keep sequential/hierarchical lists intact

### Alternative: Configurable Strategy
```python
class ChunkingStrategy(Enum):
    STRICT = "strict"           # Never exceed limit (text-split)
    SEMANTIC = "semantic"       # Allow overflow for completeness (current)
    HYBRID = "hybrid"           # Smart detection of independence

splitter = MarkdownSplitter(
    max_tokens_per_chunk=500,
    strategy=ChunkingStrategy.SEMANTIC  # Default
)
```

## References

### Industry Best Practices
- **Pinecone**: "Chunking Strategies for LLM Applications"
  - Principle: Chunks should make sense independently
  - https://www.pinecone.io/learn/chunking-strategies/

- **Unstructured.io**: Chunking Documentation
  - `chunk_by_title()`: Preserve section boundaries
  - Text-splitting for oversized elements
  - https://docs.unstructured.io/api-reference/api-services/chunking

- **Docling**: Hierarchical Chunking
  - `merge_list_items=True`: Keep lists together by default
  - Respects document structure

### Related Files
- `/tmp/chunking_analysis.md`: Original analysis of 3 options
- `/tmp/unstructured_comparison.md`: Detailed comparison with Unstructured.io
- `tests/smoke/test_real_documents.py`: Integration tests with AGENTS.md

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2025-01-14 | Allow 1.8% average overflow | Semantic completeness > strict token limits for technical documentation |
| 2025-01-14 | Reject text-splitting for policies | Preserves meaning of sequential/dependent lists |
| 2025-01-14 | Reject NLP-based independence detection | Over-engineering for 7.3% of chunks |

## Conclusion

**Our semantic chunking strategy prioritizes meaning over mechanical limits.**

For documents like AGENTS.md containing sequential policies and protocols, allowing slight overflow (average 1.8%) ensures users get complete, actionable information. This aligns with industry principles (Pinecone, Docling) while being more appropriate than Unstructured.io's approach for technical documentation.

The 7.3% oversized chunks are not failures—they are successful preservations of semantic completeness.
