# Troubleshooting

Common issues and solutions.

## Installation Issues

### Ollama Not Found

**Problem**: `Error: could not connect to ollama`

**Solution**:
```bash
# Start Ollama
ollama serve

# Verify
ollama list
```

### GPU Out of Memory

**Problem**: `CUDA out of memory`

**Solutions**:
1. Reduce batch size:
   ```bash
   export MARKDOWN_REALLOCATOR_EMBEDDER_BATCH_SIZE=5
   ```

2. Use CPU-only mode:
   ```bash
   export CUDA_VISIBLE_DEVICES=""
   ```

### AVX2 Errors

**Problem**: `Illegal instruction (core dumped)`

**Solution**:
```bash
# Add to ~/.bashrc
export NPY_DISABLE_CPU_FEATURES="AVX2,FMA3"
export OPENBLAS_CORETYPE=Haswell
```

## Runtime Issues

### Slow Embedding

**Causes**:
- Using CPU instead of GPU
- Large batch size
- Model not cached

**Solutions**:
```bash
# Check GPU usage
nvidia-smi

# Enable caching
markdown-reallocator embed chunks.json --output embeddings.npz --cache
```

### Import Errors

**Problem**: `ModuleNotFoundError`

**Solution**:
```bash
# Verify installation
pip list | grep markdown-reallocator

# Reinstall
pip uninstall markdown-reallocator
pip install markdown-reallocator
```

## Getting Help

- [GitHub Issues](https://github.com/yourusername/markdown-reallocator/issues)
- [Discussions](https://github.com/yourusername/markdown-reallocator/discussions)
- [Documentation](https://markdown-reallocator.readthedocs.io)
