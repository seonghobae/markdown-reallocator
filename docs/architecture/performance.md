# Performance

Performance characteristics and optimization strategies.

## Benchmarks

GTX 1050 (2GB) + Intel Xeon X5650:

| Operation | Time | Throughput |
|-----------|------|------------|
| Preprocessing | <1s per 1000 lines | CPU-bound |
| Embedding (50 chunks) | ~10s | 300+ tokens/sec |
| Search (1000 chunks) | <0.5s | NumPy vectorized |
| Reordering (100 chunks) | <2s | Similarity + KMeans |

## Optimization Strategies

### 1. Caching

Embeddings are cached automatically:
- Cache hits: instant retrieval
- Cache location: `~/.cache/markdown-reallocator/`

### 2. Batch Processing

Process multiple chunks at once:
- Default batch size: 10
- Configurable per GPU

### 3. Model Management

Automatic loading/unloading:
- Load on demand
- Unload when memory threshold reached
- Reduces GPU memory usage

### 4. Parallel Processing

Use multiple CPU cores for preprocessing:
```python
from multiprocessing import Pool
# Process files in parallel
```

## Bottlenecks

- **Embedding**: GPU-bound, ~10s for 50 chunks
- **Network**: Ollama connection overhead

## Optimization Tips

1. Enable caching
2. Adjust batch size for your GPU
3. Process files in batches
4. Use faster embedding models for lower quality needs
