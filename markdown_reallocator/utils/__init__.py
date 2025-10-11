"""Utility modules for markdown processing."""

from markdown_reallocator.utils.cache import CacheStatistics, EmbeddingCache, LRUCache
from markdown_reallocator.utils.memory import (
    GPUMemoryMonitor,
    MemoryInfo,
    check_gpu_memory_available,
    check_system_memory_available,
    get_gpu_memory,
    get_system_memory,
)
from markdown_reallocator.utils.model_loader import (
    ModelLoadError,
    OllamaConnectionError,
    check_ollama_available,
    get_available_models,
    load_embedding_model,
    load_llm_model,
    model_exists,
)
from markdown_reallocator.utils.profiling import (
    PerformanceMonitor,
    get_monitor,
    profile_function,
)
from markdown_reallocator.utils.similarity import (
    batch_cosine_similarity,
    batch_cosine_similarity_normalized,
    cosine_similarity,
    cosine_similarity_normalized,
    pairwise_cosine_similarity,
)

__all__ = [
    # Cache
    "LRUCache",
    "EmbeddingCache",
    "CacheStatistics",
    # Memory
    "MemoryInfo",
    "GPUMemoryMonitor",
    "get_gpu_memory",
    "get_system_memory",
    "check_gpu_memory_available",
    "check_system_memory_available",
    # Model Loader
    "load_embedding_model",
    "load_llm_model",
    "check_ollama_available",
    "get_available_models",
    "model_exists",
    "OllamaConnectionError",
    "ModelLoadError",
    # Profiling
    "PerformanceMonitor",
    "get_monitor",
    "profile_function",
    # Similarity
    "cosine_similarity",
    "cosine_similarity_normalized",
    "batch_cosine_similarity",
    "batch_cosine_similarity_normalized",
    "pairwise_cosine_similarity",
]
