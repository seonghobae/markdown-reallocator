# Performance Benchmarks

This directory contains performance benchmarks and profiling tools for Markdown Reallocator.

## Performance Targets (from PRD)

- **Preprocessing**: <1s per 1000 lines
- **Embedding**: <10s for 50 chunks (with batch processing)
- **Similarity Computation**: Vectorized numpy operations
- **Search**: <500ms for 1000 chunks
- **Peak GPU Memory**: ≤1.8GB

## Current Performance (Measured)

### Preprocessing
- **100 lines**: ~0.46 ms ✅
- **1,000 lines**: ~4.3 ms ✅ (target: <1s)
- **5,000 lines**: ~21.7 ms ✅
- **10,000 lines**: ~40-50 ms ✅

**Result**: Exceeds target by 200x

### Splitting
- **1,000 lines**: ~8.9 ms ✅

### Memory Usage (Non-embedding)
- **Preprocessing**: ~0.9 MB for 10K lines
- **Splitting**: ~2 MB for 1,000 chunks
- **Total baseline**: ~95 MB

## Running Benchmarks

### Quick Benchmarks (No Ollama Required)

```bash
# Preprocessing benchmarks
pytest benchmarks/benchmark_core.py::TestPreprocessingPerformance \
    -v --benchmark-only --no-cov

# Splitting benchmarks
pytest benchmarks/benchmark_core.py::TestSplittingPerformance \
    -v --benchmark-only --no-cov
```

### Full Benchmarks (Requires Ollama)

```bash
# All benchmarks including embedding and search
pytest benchmarks/benchmark_core.py -v --benchmark-only --no-cov
```

### Memory Profiling

```bash
# Run comprehensive memory profiling
python -m memory_profiler benchmarks/profile_memory.py

# Run specific test
python benchmarks/profile_memory.py
```

## CLI Profiling

You can enable performance profiling in the CLI with the `--profile` flag:

```bash
# Profile preprocessing
markdown-reallocator --profile preprocess input.md -o output.md

# Profile any command
markdown-reallocator --profile split input.md -o chunks.json
```

The output will include:
- Operation durations (in milliseconds)
- Memory deltas (in MB)
- Total duration and peak memory usage

Example output:
```
=== Performance Summary ===
  read_input: 1.23 ms | Memory: +0.5 MB
  preprocess: 4.56 ms | Memory: +0.9 MB
  write_output: 0.89 ms | Memory: +0.1 MB

Total Duration: 0.007 s
Peak Memory: 95.3 MB
```

## Continuous Performance Monitoring

Benchmarks are automatically run in CI/CD using pytest-benchmark:

```bash
# Save baseline
pytest benchmarks/ --benchmark-only --benchmark-autosave

# Compare against baseline
pytest benchmarks/ --benchmark-only --benchmark-compare
```

## Profiling Tools

### py-spy

For CPU profiling of long-running operations:

```bash
# Profile while running
py-spy record -o profile.svg -- python -m markdown_reallocator preprocess large.md

# Top command (interactive)
py-spy top -- python -m markdown_reallocator preprocess large.md
```

### memory_profiler

For line-by-line memory profiling:

```bash
# Add @profile decorator to function
# Run with memory_profiler
python -m memory_profiler your_script.py
```

## Writing New Benchmarks

Use pytest-benchmark fixtures:

```python
def test_my_operation(benchmark):
    result = benchmark(my_function, arg1, arg2)
    assert result is not None
```

For memory profiling, use the `@profile` decorator:

```python
from memory_profiler import profile

@profile
def test_memory_intensive_operation():
    # Your code here
    pass
```

## Performance Optimization Guidelines

1. **Preprocessing**: Already highly optimized, no changes needed
2. **Splitting**: Fast enough for target use cases
3. **Embeddings**: Focus on batch processing and caching
4. **Similarity**: Use vectorized numpy operations (no Python loops)
5. **Memory**: Monitor GPU memory for embedding operations

## Known Bottlenecks

1. **Ollama API calls**: Network latency dominates embedding time
2. **Large batch sizes**: May exceed GPU memory on 2GB cards
3. **Similarity matrix**: O(n²) for pairwise comparisons

## Mitigation Strategies

1. **Caching**: Enabled by default for embeddings
2. **Batch processing**: Configurable batch sizes
3. **Lazy loading**: Models loaded on-demand
4. **Streaming**: For large file operations
