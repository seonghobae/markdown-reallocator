"""Memory monitoring utilities for GPU and system memory.

This module provides utilities for monitoring GPU and system memory usage,
with graceful fallback when GPU is not available. Designed to work on
resource-constrained hardware and provide warnings when memory usage is high.
"""

import subprocess
import warnings
from dataclasses import dataclass


@dataclass
class MemoryInfo:
    """Memory usage information.

    Attributes:
        used_mb: Memory currently in use (MB)
        total_mb: Total memory available (MB)
        free_mb: Free memory available (MB)
        utilization: Memory utilization as percentage (0.0 to 1.0)
    """

    used_mb: float
    total_mb: float
    free_mb: float

    @property
    def utilization(self) -> float:
        """Calculate memory utilization percentage.

        Returns:
            Utilization as float (0.0 to 1.0)
        """
        return self.used_mb / self.total_mb if self.total_mb > 0 else 0.0

    def to_dict(self) -> dict[str, float]:
        """Convert to dictionary."""
        return {
            "used_mb": self.used_mb,
            "total_mb": self.total_mb,
            "free_mb": self.free_mb,
            "utilization": self.utilization,
        }

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"MemoryInfo(used={self.used_mb:.0f}MB, "
            f"total={self.total_mb:.0f}MB, "
            f"utilization={self.utilization:.1%})"
        )


def get_gpu_memory() -> MemoryInfo | None:
    """Get GPU memory information using nvidia-smi.

    This function attempts to query NVIDIA GPU memory usage using nvidia-smi.
    If nvidia-smi is not available or GPU is not present, returns None.

    Returns:
        MemoryInfo with GPU memory stats, or None if GPU unavailable

    Examples:
        >>> mem = get_gpu_memory()
        >>> if mem:
        ...     print(f"GPU memory: {mem.used_mb:.0f}MB / {mem.total_mb:.0f}MB")
        ... else:
        ...     print("GPU not available")
    """
    try:
        # Query nvidia-smi for memory info
        # Format: memory.used,memory.total (in MB)
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=memory.used,memory.total",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=5.0,
            check=False,
        )

        if result.returncode != 0:
            return None

        # Parse output (format: "used, total")
        output = result.stdout.strip()
        if not output:
            return None

        # Handle multiple GPUs by taking first one
        first_line = output.split("\n")[0]
        used_str, total_str = first_line.split(",")
        used_mb = float(used_str.strip())
        total_mb = float(total_str.strip())
        free_mb = total_mb - used_mb

        return MemoryInfo(used_mb=used_mb, total_mb=total_mb, free_mb=free_mb)

    except (FileNotFoundError, subprocess.TimeoutExpired, ValueError, IndexError):
        # nvidia-smi not found, timeout, or parsing error
        return None


def check_gpu_memory_available(required_mb: float, warn_threshold: float = 0.9) -> bool:
    """Check if sufficient GPU memory is available.

    Args:
        required_mb: Required memory in MB
        warn_threshold: Utilization threshold for warning (default: 0.9 = 90%)

    Returns:
        True if sufficient memory available (or GPU unavailable),
        False if insufficient memory

    Warnings:
        Warns if memory utilization would exceed warn_threshold
    """
    mem_info = get_gpu_memory()

    # If no GPU, assume memory is available (CPU fallback)
    if mem_info is None:
        return True

    # Check if we have enough free memory
    if mem_info.free_mb < required_mb:
        warnings.warn(
            f"Insufficient GPU memory: {mem_info.free_mb:.0f}MB free, "
            f"{required_mb:.0f}MB required. {mem_info}",
            ResourceWarning,
            stacklevel=2,
        )
        return False

    # Check if loading would exceed threshold
    projected_used = mem_info.used_mb + required_mb
    projected_util = projected_used / mem_info.total_mb

    if projected_util > warn_threshold:
        warnings.warn(
            f"Loading model would use {projected_util:.1%} of GPU memory "
            f"({projected_used:.0f}MB / {mem_info.total_mb:.0f}MB). "
            f"This may cause memory overflow.",
            ResourceWarning,
            stacklevel=2,
        )

    return True


class GPUMemoryMonitor:
    """Context manager for monitoring GPU memory during operations.

    This context manager records memory usage before and after an operation,
    providing statistics on memory consumption. Safe to use even when GPU
    is not available.

    Examples:
        >>> with GPUMemoryMonitor() as monitor:
        ...     # Perform GPU-intensive operation
        ...     result = load_model()
        >>> if monitor.memory_used_mb:
        ...     print(f"Operation used {monitor.memory_used_mb:.0f}MB GPU memory")
    """

    def __init__(self, warn_threshold: float = 0.9):
        """Initialize GPU memory monitor.

        Args:
            warn_threshold: Utilization threshold for warning (0.0 to 1.0)
        """
        self.warn_threshold = warn_threshold
        self.before: MemoryInfo | None = None
        self.after: MemoryInfo | None = None

    @property
    def memory_used_mb(self) -> float | None:
        """Calculate memory used during operation.

        Returns:
            Memory used in MB, or None if GPU unavailable or not measured
        """
        if self.before and self.after:
            return self.after.used_mb - self.before.used_mb
        return None

    def __enter__(self) -> "GPUMemoryMonitor":
        """Enter context and record initial memory state."""
        self.before = get_gpu_memory()
        return self

    def __exit__(self, exc_type: type, exc_val: Exception, exc_tb: object) -> None:
        """Exit context and record final memory state."""
        self.after = get_gpu_memory()

        # Check if we exceeded threshold
        if self.after and self.after.utilization > self.warn_threshold:
            warnings.warn(
                f"GPU memory utilization is high: {self.after.utilization:.1%} "
                f"({self.after.used_mb:.0f}MB / {self.after.total_mb:.0f}MB)",
                ResourceWarning,
                stacklevel=2,
            )

    def __repr__(self) -> str:
        """Return string representation."""
        if self.memory_used_mb is not None:
            return f"GPUMemoryMonitor(used={self.memory_used_mb:.0f}MB)"
        return "GPUMemoryMonitor(GPU unavailable)"


def get_system_memory() -> MemoryInfo:
    """Get system (RAM) memory information.

    Returns:
        MemoryInfo with system memory stats

    Raises:
        RuntimeError: If unable to read memory info
    """
    try:
        # Read from /proc/meminfo on Linux
        with open("/proc/meminfo") as f:
            lines = f.readlines()

        mem_total = 0.0
        mem_available = 0.0

        for line in lines:
            if line.startswith("MemTotal:"):
                # Format: "MemTotal:       16384000 kB"
                mem_total = int(line.split()[1]) / 1024  # Convert KB to MB
            elif line.startswith("MemAvailable:"):
                mem_available = int(line.split()[1]) / 1024

        if mem_total == 0:
            raise ValueError("Could not parse MemTotal")

        used_mb = mem_total - mem_available
        return MemoryInfo(used_mb=used_mb, total_mb=mem_total, free_mb=mem_available)

    except (FileNotFoundError, ValueError, IndexError) as e:
        raise RuntimeError(f"Failed to read system memory info: {e}") from e


def check_system_memory_available(required_mb: float, warn_threshold: float = 0.9) -> bool:
    """Check if sufficient system memory is available.

    Args:
        required_mb: Required memory in MB
        warn_threshold: Utilization threshold for warning (default: 0.9 = 90%)

    Returns:
        True if sufficient memory available, False otherwise

    Warnings:
        Warns if memory utilization would exceed warn_threshold
    """
    try:
        mem_info = get_system_memory()
    except RuntimeError:
        # Can't read memory info, assume available
        return True

    # Check if we have enough free memory
    if mem_info.free_mb < required_mb:
        warnings.warn(
            f"Insufficient system memory: {mem_info.free_mb:.0f}MB free, "
            f"{required_mb:.0f}MB required. {mem_info}",
            ResourceWarning,
            stacklevel=2,
        )
        return False

    # Check if loading would exceed threshold
    projected_used = mem_info.used_mb + required_mb
    projected_util = projected_used / mem_info.total_mb

    if projected_util > warn_threshold:
        warnings.warn(
            f"Loading would use {projected_util:.1%} of system memory "
            f"({projected_used:.0f}MB / {mem_info.total_mb:.0f}MB). "
            f"This may cause swapping.",
            ResourceWarning,
            stacklevel=2,
        )

    return True
