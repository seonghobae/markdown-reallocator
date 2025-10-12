"""Tests for performance profiling utilities."""
import time
from unittest.mock import Mock, patch

import pytest

from markdown_reallocator.utils.profiling import (
    PerformanceMonitor,
    get_monitor,
    profile_function,
)


class TestPerformanceMonitor:
    """Tests for PerformanceMonitor class."""

    def test_initialization(self) -> None:
        """Should initialize with disabled state."""
        monitor = PerformanceMonitor()

        assert monitor.enabled is False
        assert monitor.metrics == {}

    def test_enable(self) -> None:
        """Should enable monitoring."""
        monitor = PerformanceMonitor()
        monitor.enable()

        assert monitor.enabled is True

    def test_get_memory_mb_without_psutil(self) -> None:
        """Should return 0.0 when psutil not available."""
        monitor = PerformanceMonitor()
        monitor.process = None

        memory = monitor.get_memory_mb()

        assert memory == 0.0

    def test_get_memory_mb_with_psutil(self) -> None:
        """Should return memory usage when psutil available."""
        # Skip if psutil not available
        try:
            import psutil
            psutil_available = True
        except ImportError:
            psutil_available = False

        if not psutil_available:
            pytest.skip("psutil not installed")

        monitor = PerformanceMonitor()

        # Mock process with memory_info
        mock_process = Mock()
        mock_process.memory_info.return_value.rss = 100 * 1024 * 1024  # 100 MB
        monitor.process = mock_process

        memory = monitor.get_memory_mb()

        assert memory == 100.0

    def test_record_metric_when_disabled(self) -> None:
        """Should not record metrics when disabled."""
        monitor = PerformanceMonitor()
        monitor.enabled = False

        monitor.record_metric("test_op", 1.5)

        assert monitor.metrics == {}

    def test_record_metric_when_enabled(self) -> None:
        """Should record metrics when enabled."""
        monitor = PerformanceMonitor()
        monitor.enable()

        monitor.record_metric("test_op", 1.5)

        assert "test_op" in monitor.metrics
        assert monitor.metrics["test_op"]["duration_s"] == 1.5
        assert monitor.metrics["test_op"]["duration_ms"] == 1500.0

    def test_record_metric_with_memory_delta(self) -> None:
        """Should record memory delta when provided."""
        monitor = PerformanceMonitor()
        monitor.enable()

        monitor.record_metric("test_op", 1.0, memory_delta=50.5)

        assert monitor.metrics["test_op"]["memory_delta_mb"] == 50.5

    def test_get_summary_empty(self) -> None:
        """Should return empty dict when no metrics."""
        monitor = PerformanceMonitor()

        summary = monitor.get_summary()

        assert summary == {}

    def test_get_summary_with_metrics(self) -> None:
        """Should calculate summary correctly."""
        monitor = PerformanceMonitor()
        monitor.enable()
        monitor.record_metric("op1", 1.0, memory_delta=10.0)
        monitor.record_metric("op2", 2.0, memory_delta=20.0)

        summary = monitor.get_summary()

        assert "operations" in summary
        assert "total_duration_s" in summary
        assert "total_memory_delta_mb" in summary
        assert "peak_memory_mb" in summary
        assert summary["total_duration_s"] == 3.0
        assert summary["total_memory_delta_mb"] == 30.0

    def test_print_summary_empty(self) -> None:
        """Should return message when no metrics."""
        monitor = PerformanceMonitor()

        output = monitor.print_summary()

        assert output == "No performance metrics recorded"

    def test_print_summary_with_metrics(self) -> None:
        """Should format summary correctly."""
        monitor = PerformanceMonitor()
        monitor.enable()
        monitor.record_metric("operation1", 0.001, memory_delta=5.5)
        monitor.record_metric("operation2", 0.002)

        output = monitor.print_summary()

        assert "Performance Summary" in output
        assert "operation1" in output
        assert "1.00 ms" in output  # 0.001s = 1.0ms
        assert "Memory: +5.5 MB" in output
        assert "operation2" in output
        assert "2.00 ms" in output
        assert "Total Duration" in output
        assert "Peak Memory" in output


class TestGetMonitor:
    """Tests for get_monitor function."""

    def test_returns_global_instance(self) -> None:
        """Should return the global monitor instance."""
        monitor1 = get_monitor()
        monitor2 = get_monitor()

        # Should be the same instance
        assert monitor1 is monitor2

    def test_global_instance_persists_state(self) -> None:
        """Global instance should persist state."""
        monitor = get_monitor()
        monitor.enable()
        monitor.record_metric("test", 1.0)

        # Get monitor again
        monitor2 = get_monitor()

        assert monitor2.enabled is True
        assert "test" in monitor2.metrics


class TestProfileFunctionDecorator:
    """Tests for profile_function decorator."""

    def test_decorator_without_monitor_enabled(self) -> None:
        """Should execute function normally when monitor disabled."""
        # Reset global monitor state
        monitor = get_monitor()
        monitor.enabled = False
        monitor.metrics.clear()

        @profile_function()
        def test_func(x: int) -> int:
            return x * 2

        result = test_func(5)

        assert result == 10
        # Should not record metrics when disabled
        assert "test_func" not in monitor.metrics

    def test_decorator_with_monitor_enabled(self) -> None:
        """Should record metrics when monitor enabled."""
        monitor = get_monitor()
        monitor.enabled = False  # Reset
        monitor.metrics.clear()
        monitor.enable()

        @profile_function()
        def test_func(x: int) -> int:
            time.sleep(0.01)  # 10ms
            return x * 2

        result = test_func(5)

        assert result == 10
        assert "test_func" in monitor.metrics
        # Duration should be at least 10ms
        assert monitor.metrics["test_func"]["duration_ms"] >= 10.0

    def test_decorator_with_custom_name(self) -> None:
        """Should use custom operation name."""
        monitor = get_monitor()
        monitor.enabled = False
        monitor.metrics.clear()
        monitor.enable()

        @profile_function(operation_name="custom_operation")
        def test_func() -> str:
            return "result"

        result = test_func()

        assert result == "result"
        assert "custom_operation" in monitor.metrics
        assert "test_func" not in monitor.metrics

    def test_decorator_records_memory_delta(self) -> None:
        """Should record memory delta."""
        monitor = get_monitor()
        monitor.enabled = False
        monitor.metrics.clear()
        monitor.enable()

        @profile_function()
        def test_func() -> list:
            return [0] * 1000  # Allocate some memory

        result = test_func()

        assert len(result) == 1000
        assert "test_func" in monitor.metrics
        assert "memory_delta_mb" in monitor.metrics["test_func"]

    def test_decorator_preserves_function_metadata(self) -> None:
        """Should preserve original function metadata."""
        @profile_function()
        def test_func() -> None:
            """Test function docstring."""
            pass

        assert test_func.__name__ == "test_func"
        assert test_func.__doc__ == "Test function docstring."

    def test_decorator_handles_exceptions(self) -> None:
        """Should still record metrics even if function raises."""
        monitor = get_monitor()
        monitor.enabled = False
        monitor.metrics.clear()
        monitor.enable()

        @profile_function()
        def failing_func() -> None:
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            failing_func()

        # Metrics should still be recorded
        assert "failing_func" in monitor.metrics

    def test_decorator_with_args_and_kwargs(self) -> None:
        """Should handle functions with various arguments."""
        monitor = get_monitor()
        monitor.enabled = False
        monitor.metrics.clear()
        monitor.enable()

        @profile_function()
        def complex_func(a: int, b: str, *args: int, **kwargs: str) -> tuple:
            return (a, b, args, kwargs)

        result = complex_func(1, "test", 3, 4, key="value")

        assert result == (1, "test", (3, 4), {"key": "value"})
        assert "complex_func" in monitor.metrics


class TestIntegration:
    """Integration tests for profiling."""

    def test_full_workflow(self) -> None:
        """Test complete profiling workflow."""
        # Get fresh monitor
        monitor = get_monitor()
        monitor.enabled = False
        monitor.metrics.clear()

        # Enable monitoring
        monitor.enable()

        # Define profiled functions
        @profile_function(operation_name="step1")
        def step_one() -> int:
            time.sleep(0.01)
            return 42

        @profile_function(operation_name="step2")
        def step_two(x: int) -> int:
            time.sleep(0.01)
            return x * 2

        # Execute workflow
        result1 = step_one()
        result2 = step_two(result1)

        # Check results
        assert result1 == 42
        assert result2 == 84

        # Check metrics
        assert "step1" in monitor.metrics
        assert "step2" in monitor.metrics

        # Get summary
        summary = monitor.get_summary()
        assert len(summary["operations"]) == 2
        assert summary["total_duration_s"] >= 0.02  # At least 20ms

        # Print summary
        output = monitor.print_summary()
        assert "step1" in output
        assert "step2" in output
        assert "Performance Summary" in output
