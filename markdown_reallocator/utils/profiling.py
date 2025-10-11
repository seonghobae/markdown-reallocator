"""Performance profiling utilities for Markdown Reallocator."""
import functools
import time
from collections.abc import Callable
from typing import Any

import psutil


class PerformanceMonitor:
    """Monitor performance metrics during execution."""

    def __init__(self) -> None:
        """Initialize performance monitor."""
        self.enabled = False
        self.metrics: dict[str, dict[str, float]] = {}
        self.process = psutil.Process()

    def enable(self) -> None:
        """Enable performance monitoring."""
        self.enabled = True

    def get_memory_mb(self) -> float:
        """Get current process memory usage in MB."""
        return self.process.memory_info().rss / 1024 / 1024

    def record_metric(
        self, operation: str, duration: float, memory_delta: float | None = None
    ) -> None:
        """Record a performance metric.

        Args:
            operation: Name of the operation
            duration: Duration in seconds
            memory_delta: Memory change in MB (optional)
        """
        if not self.enabled:
            return

        self.metrics[operation] = {
            "duration_s": duration,
            "duration_ms": duration * 1000,
        }

        if memory_delta is not None:
            self.metrics[operation]["memory_delta_mb"] = memory_delta

    def get_summary(self) -> dict[str, Any]:
        """Get performance summary.

        Returns:
            Dictionary containing performance metrics
        """
        if not self.metrics:
            return {}

        total_duration = sum(m["duration_s"] for m in self.metrics.values())
        total_memory = sum(
            m.get("memory_delta_mb", 0) for m in self.metrics.values()
        )

        return {
            "operations": self.metrics.copy(),
            "total_duration_s": total_duration,
            "total_memory_delta_mb": total_memory,
            "peak_memory_mb": self.get_memory_mb(),
        }

    def print_summary(self) -> str:
        """Format performance summary as string.

        Returns:
            Formatted performance summary
        """
        if not self.metrics:
            return "No performance metrics recorded"

        lines = ["\n=== Performance Summary ==="]

        for operation, metrics in self.metrics.items():
            duration_ms = metrics["duration_ms"]
            memory_str = ""
            if "memory_delta_mb" in metrics:
                memory_mb = metrics["memory_delta_mb"]
                memory_str = f" | Memory: {memory_mb:+.1f} MB"

            lines.append(f"  {operation}: {duration_ms:.2f} ms{memory_str}")

        summary = self.get_summary()
        lines.append(f"\nTotal Duration: {summary['total_duration_s']:.3f} s")
        lines.append(f"Peak Memory: {summary['peak_memory_mb']:.1f} MB")

        return "\n".join(lines)


# Global instance for easy access
_monitor = PerformanceMonitor()


def get_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance.

    Returns:
        Global PerformanceMonitor instance
    """
    return _monitor


def profile_function(operation_name: str | None = None) -> Callable:
    """Decorator to profile a function's execution.

    Args:
        operation_name: Name for the operation (defaults to function name)

    Returns:
        Decorated function with profiling
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            monitor = get_monitor()

            if not monitor.enabled:
                return func(*args, **kwargs)

            name = operation_name or func.__name__
            mem_before = monitor.get_memory_mb()
            start = time.perf_counter()

            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.perf_counter() - start
                mem_after = monitor.get_memory_mb()
                memory_delta = mem_after - mem_before

                monitor.record_metric(name, duration, memory_delta)

        return wrapper

    return decorator
