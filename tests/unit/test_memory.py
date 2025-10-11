"""Unit tests for memory monitoring utilities.

Tests cover:
- GPU memory monitoring via nvidia-smi (mocked)
- System memory monitoring via /proc/meminfo (mocked)
- Memory availability checking with thresholds
- GPUMemoryMonitor context manager
- Graceful fallback when GPU not available
- Warning generation for high memory usage

All subprocess calls and file reads are mocked.
"""

import subprocess
import warnings
from unittest.mock import Mock, mock_open, patch

import pytest

from markdown_reallocator.utils.memory import (
    GPUMemoryMonitor,
    MemoryInfo,
    check_gpu_memory_available,
    check_system_memory_available,
    get_gpu_memory,
    get_system_memory,
)


class TestMemoryInfo:
    """Tests for MemoryInfo dataclass."""

    def test_initialization(self) -> None:
        """MemoryInfo should initialize with correct values."""
        info = MemoryInfo(used_mb=1000.0, total_mb=2000.0, free_mb=1000.0)

        assert info.used_mb == 1000.0
        assert info.total_mb == 2000.0
        assert info.free_mb == 1000.0

    def test_utilization_calculation(self) -> None:
        """Utilization should be used_mb / total_mb."""
        info = MemoryInfo(used_mb=750.0, total_mb=1000.0, free_mb=250.0)
        assert info.utilization == pytest.approx(0.75)

    def test_utilization_zero_total(self) -> None:
        """Utilization should be 0.0 when total is 0."""
        info = MemoryInfo(used_mb=0.0, total_mb=0.0, free_mb=0.0)
        assert info.utilization == 0.0

    def test_utilization_full(self) -> None:
        """Utilization should be 1.0 when fully used."""
        info = MemoryInfo(used_mb=1000.0, total_mb=1000.0, free_mb=0.0)
        assert info.utilization == pytest.approx(1.0)

    def test_to_dict(self) -> None:
        """to_dict should include all fields plus utilization."""
        info = MemoryInfo(used_mb=500.0, total_mb=1000.0, free_mb=500.0)
        d = info.to_dict()

        assert d["used_mb"] == 500.0
        assert d["total_mb"] == 1000.0
        assert d["free_mb"] == 500.0
        assert d["utilization"] == pytest.approx(0.5)

    def test_repr(self) -> None:
        """__repr__ should be informative."""
        info = MemoryInfo(used_mb=1024.0, total_mb=2048.0, free_mb=1024.0)
        repr_str = repr(info)

        assert "1024" in repr_str or "1024.0" in repr_str
        assert "2048" in repr_str or "2048.0" in repr_str
        assert "50" in repr_str or "0.5" in repr_str  # 50% utilization


class TestGetGPUMemory:
    """Tests for GPU memory querying via nvidia-smi."""

    @patch("markdown_reallocator.utils.memory.subprocess.run")
    def test_successful_query(self, mock_run) -> None:
        """Should parse nvidia-smi output correctly."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "2048, 8192"  # 2GB used, 8GB total
        mock_run.return_value = mock_result

        memory_info = get_gpu_memory()

        assert memory_info is not None
        assert memory_info.used_mb == 2048.0
        assert memory_info.total_mb == 8192.0
        assert memory_info.free_mb == 6144.0

    @patch("markdown_reallocator.utils.memory.subprocess.run")
    def test_multiple_gpus(self, mock_run) -> None:
        """Should use first GPU when multiple GPUs present."""
        mock_result = Mock()
        mock_result.returncode = 0
        # Multiple lines (multiple GPUs)
        mock_result.stdout = "2048, 8192\n4096, 8192"
        mock_run.return_value = mock_result

        memory_info = get_gpu_memory()

        assert memory_info is not None
        # Should use first GPU
        assert memory_info.used_mb == 2048.0
        assert memory_info.total_mb == 8192.0

    @patch("markdown_reallocator.utils.memory.subprocess.run")
    def test_nvidia_smi_not_found(self, mock_run) -> None:
        """Should return None when nvidia-smi not available."""
        mock_run.side_effect = FileNotFoundError("nvidia-smi not found")

        memory_info = get_gpu_memory()

        assert memory_info is None

    @patch("markdown_reallocator.utils.memory.subprocess.run")
    def test_nvidia_smi_fails(self, mock_run) -> None:
        """Should return None when nvidia-smi returns non-zero."""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_run.return_value = mock_result

        memory_info = get_gpu_memory()

        assert memory_info is None

    @patch("markdown_reallocator.utils.memory.subprocess.run")
    def test_nvidia_smi_timeout(self, mock_run) -> None:
        """Should return None on timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired("nvidia-smi", 5.0)

        memory_info = get_gpu_memory()

        assert memory_info is None

    @patch("markdown_reallocator.utils.memory.subprocess.run")
    def test_empty_output(self, mock_run) -> None:
        """Should return None when output is empty."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_run.return_value = mock_result

        memory_info = get_gpu_memory()

        assert memory_info is None

    @patch("markdown_reallocator.utils.memory.subprocess.run")
    def test_malformed_output(self, mock_run) -> None:
        """Should return None when output is malformed."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "not a valid format"
        mock_run.return_value = mock_result

        memory_info = get_gpu_memory()

        assert memory_info is None

    @patch("markdown_reallocator.utils.memory.subprocess.run")
    def test_correct_command_called(self, mock_run) -> None:
        """Should call nvidia-smi with correct arguments."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "2048, 8192"
        mock_run.return_value = mock_result

        get_gpu_memory()

        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "nvidia-smi" in call_args
        assert "--query-gpu=memory.used,memory.total" in call_args
        assert "--format=csv,noheader,nounits" in call_args


class TestCheckGPUMemoryAvailable:
    """Tests for GPU memory availability checking."""

    @patch("markdown_reallocator.utils.memory.get_gpu_memory")
    def test_no_gpu_returns_true(self, mock_get_gpu) -> None:
        """Should return True when no GPU available (CPU fallback)."""
        mock_get_gpu.return_value = None

        assert check_gpu_memory_available(1000.0) is True

    @patch("markdown_reallocator.utils.memory.get_gpu_memory")
    def test_sufficient_memory(self, mock_get_gpu) -> None:
        """Should return True when sufficient memory available."""
        mock_get_gpu.return_value = MemoryInfo(
            used_mb=2000.0, total_mb=8000.0, free_mb=6000.0
        )

        assert check_gpu_memory_available(1000.0) is True

    @patch("markdown_reallocator.utils.memory.get_gpu_memory")
    def test_insufficient_memory(self, mock_get_gpu) -> None:
        """Should return False and warn when insufficient memory."""
        mock_get_gpu.return_value = MemoryInfo(
            used_mb=7500.0, total_mb=8000.0, free_mb=500.0
        )

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = check_gpu_memory_available(1000.0)

            assert result is False
            assert len(w) == 1
            assert issubclass(w[0].category, ResourceWarning)
            assert "Insufficient GPU memory" in str(w[0].message)

    @patch("markdown_reallocator.utils.memory.get_gpu_memory")
    def test_warn_on_high_utilization(self, mock_get_gpu) -> None:
        """Should warn when loading would exceed threshold."""
        mock_get_gpu.return_value = MemoryInfo(
            used_mb=7000.0, total_mb=8000.0, free_mb=1000.0
        )

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            # Requesting 500MB would result in 93.75% utilization
            result = check_gpu_memory_available(500.0, warn_threshold=0.9)

            assert result is True  # Still enough memory
            assert len(w) == 1
            assert issubclass(w[0].category, ResourceWarning)
            assert "memory overflow" in str(w[0].message).lower()

    @patch("markdown_reallocator.utils.memory.get_gpu_memory")
    def test_no_warn_below_threshold(self, mock_get_gpu) -> None:
        """Should not warn when below threshold."""
        mock_get_gpu.return_value = MemoryInfo(
            used_mb=4000.0, total_mb=8000.0, free_mb=4000.0
        )

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            # Requesting 1000MB would result in 62.5% utilization
            result = check_gpu_memory_available(1000.0, warn_threshold=0.9)

            assert result is True
            assert len(w) == 0  # No warnings

    @patch("markdown_reallocator.utils.memory.get_gpu_memory")
    def test_custom_threshold(self, mock_get_gpu) -> None:
        """Should respect custom warning threshold."""
        mock_get_gpu.return_value = MemoryInfo(
            used_mb=6000.0, total_mb=10000.0, free_mb=4000.0
        )

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            # Requesting 2000MB would result in 80% utilization
            result = check_gpu_memory_available(2000.0, warn_threshold=0.7)

            assert result is True
            assert len(w) == 1  # Should warn (80% > 70%)


class TestGPUMemoryMonitor:
    """Tests for GPUMemoryMonitor context manager."""

    @patch("markdown_reallocator.utils.memory.get_gpu_memory")
    def test_tracks_memory_usage(self, mock_get_gpu) -> None:
        """Should track memory usage during operation."""
        # Before: 2000MB used
        # After: 3000MB used (1000MB increase)
        mock_get_gpu.side_effect = [
            MemoryInfo(used_mb=2000.0, total_mb=8000.0, free_mb=6000.0),
            MemoryInfo(used_mb=3000.0, total_mb=8000.0, free_mb=5000.0),
        ]

        with GPUMemoryMonitor() as monitor:
            pass  # Simulate operation

        assert monitor.memory_used_mb == pytest.approx(1000.0)
        assert monitor.before is not None
        assert monitor.after is not None

    @patch("markdown_reallocator.utils.memory.get_gpu_memory")
    def test_no_gpu_available(self, mock_get_gpu) -> None:
        """Should handle case when GPU not available."""
        mock_get_gpu.return_value = None

        with GPUMemoryMonitor() as monitor:
            pass

        assert monitor.memory_used_mb is None
        assert monitor.before is None
        assert monitor.after is None

    @patch("markdown_reallocator.utils.memory.get_gpu_memory")
    def test_warns_on_high_utilization(self, mock_get_gpu) -> None:
        """Should warn when utilization exceeds threshold."""
        mock_get_gpu.side_effect = [
            MemoryInfo(used_mb=5000.0, total_mb=8000.0, free_mb=3000.0),
            MemoryInfo(used_mb=7500.0, total_mb=8000.0, free_mb=500.0),  # 93.75%
        ]

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            with GPUMemoryMonitor(warn_threshold=0.9):
                pass

            assert len(w) == 1
            assert issubclass(w[0].category, ResourceWarning)
            assert "high" in str(w[0].message).lower()

    @patch("markdown_reallocator.utils.memory.get_gpu_memory")
    def test_no_warn_below_threshold(self, mock_get_gpu) -> None:
        """Should not warn when below threshold."""
        mock_get_gpu.side_effect = [
            MemoryInfo(used_mb=3000.0, total_mb=8000.0, free_mb=5000.0),
            MemoryInfo(used_mb=4000.0, total_mb=8000.0, free_mb=4000.0),  # 50%
        ]

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            with GPUMemoryMonitor(warn_threshold=0.9):
                pass

            assert len(w) == 0

    @patch("markdown_reallocator.utils.memory.get_gpu_memory")
    def test_repr_with_gpu(self, mock_get_gpu) -> None:
        """__repr__ should show memory used when GPU available."""
        mock_get_gpu.side_effect = [
            MemoryInfo(used_mb=2000.0, total_mb=8000.0, free_mb=6000.0),
            MemoryInfo(used_mb=3500.0, total_mb=8000.0, free_mb=4500.0),
        ]

        with GPUMemoryMonitor() as monitor:
            pass

        repr_str = repr(monitor)
        assert "1500" in repr_str or "1500.0" in repr_str
        assert "MB" in repr_str

    @patch("markdown_reallocator.utils.memory.get_gpu_memory")
    def test_repr_without_gpu(self, mock_get_gpu) -> None:
        """__repr__ should indicate GPU unavailable."""
        mock_get_gpu.return_value = None

        with GPUMemoryMonitor() as monitor:
            pass

        repr_str = repr(monitor)
        assert "unavailable" in repr_str.lower()


class TestGetSystemMemory:
    """Tests for system memory monitoring via /proc/meminfo."""

    def test_successful_read(self) -> None:
        """Should parse /proc/meminfo correctly."""
        meminfo_content = """MemTotal:       16384000 kB
MemFree:         8192000 kB
MemAvailable:    12288000 kB
Buffers:          512000 kB
Cached:          2048000 kB
"""
        with patch("builtins.open", mock_open(read_data=meminfo_content)):
            memory_info = get_system_memory()

            assert memory_info.total_mb == pytest.approx(16000.0, rel=1e-2)
            assert memory_info.free_mb == pytest.approx(12000.0, rel=1e-2)
            # used = total - available
            assert memory_info.used_mb == pytest.approx(4000.0, rel=1e-2)

    def test_file_not_found(self) -> None:
        """Should raise RuntimeError when /proc/meminfo not found."""
        with patch("builtins.open", side_effect=FileNotFoundError):
            with pytest.raises(RuntimeError, match="Failed to read system memory info"):
                get_system_memory()

    def test_malformed_content(self) -> None:
        """Should raise RuntimeError when content is malformed."""
        meminfo_content = "NotValidFormat"

        with patch("builtins.open", mock_open(read_data=meminfo_content)):
            with pytest.raises(RuntimeError, match="Could not parse MemTotal"):
                get_system_memory()

    def test_missing_memtotal(self) -> None:
        """Should raise RuntimeError when MemTotal missing."""
        meminfo_content = """MemFree:         8192000 kB
MemAvailable:    12288000 kB
"""
        with patch("builtins.open", mock_open(read_data=meminfo_content)):
            with pytest.raises(RuntimeError, match="Could not parse MemTotal"):
                get_system_memory()

    def test_missing_memavailable(self) -> None:
        """Should handle missing MemAvailable (treat as 0)."""
        meminfo_content = """MemTotal:       16384000 kB
MemFree:         8192000 kB
"""
        with patch("builtins.open", mock_open(read_data=meminfo_content)):
            memory_info = get_system_memory()

            assert memory_info.total_mb == pytest.approx(16000.0, rel=1e-2)
            assert memory_info.free_mb == pytest.approx(0.0)
            assert memory_info.used_mb == pytest.approx(16000.0, rel=1e-2)


class TestCheckSystemMemoryAvailable:
    """Tests for system memory availability checking."""

    @patch("markdown_reallocator.utils.memory.get_system_memory")
    def test_sufficient_memory(self, mock_get_system) -> None:
        """Should return True when sufficient memory available."""
        mock_get_system.return_value = MemoryInfo(
            used_mb=8000.0, total_mb=16000.0, free_mb=8000.0
        )

        assert check_system_memory_available(1000.0) is True

    @patch("markdown_reallocator.utils.memory.get_system_memory")
    def test_insufficient_memory(self, mock_get_system) -> None:
        """Should return False and warn when insufficient memory."""
        mock_get_system.return_value = MemoryInfo(
            used_mb=15500.0, total_mb=16000.0, free_mb=500.0
        )

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = check_system_memory_available(1000.0)

            assert result is False
            assert len(w) == 1
            assert issubclass(w[0].category, ResourceWarning)
            assert "Insufficient system memory" in str(w[0].message)

    @patch("markdown_reallocator.utils.memory.get_system_memory")
    def test_warn_on_swapping(self, mock_get_system) -> None:
        """Should warn when loading might cause swapping."""
        mock_get_system.return_value = MemoryInfo(
            used_mb=14000.0, total_mb=16000.0, free_mb=2000.0
        )

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            # Requesting 1000MB would result in 93.75% utilization
            result = check_system_memory_available(1000.0, warn_threshold=0.9)

            assert result is True  # Still enough memory
            assert len(w) == 1
            assert "swapping" in str(w[0].message).lower()

    @patch("markdown_reallocator.utils.memory.get_system_memory")
    def test_no_warn_below_threshold(self, mock_get_system) -> None:
        """Should not warn when below threshold."""
        mock_get_system.return_value = MemoryInfo(
            used_mb=8000.0, total_mb=16000.0, free_mb=8000.0
        )

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = check_system_memory_available(1000.0, warn_threshold=0.9)

            assert result is True
            assert len(w) == 0

    @patch("markdown_reallocator.utils.memory.get_system_memory")
    def test_handles_read_failure(self, mock_get_system) -> None:
        """Should return True (assume available) when can't read memory."""
        mock_get_system.side_effect = RuntimeError("Can't read /proc/meminfo")

        assert check_system_memory_available(1000.0) is True

    @patch("markdown_reallocator.utils.memory.get_system_memory")
    def test_custom_threshold(self, mock_get_system) -> None:
        """Should respect custom warning threshold."""
        mock_get_system.return_value = MemoryInfo(
            used_mb=12000.0, total_mb=16000.0, free_mb=4000.0
        )

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            # Requesting 2000MB would result in 87.5% utilization
            result = check_system_memory_available(2000.0, warn_threshold=0.8)

            assert result is True
            assert len(w) == 1  # Should warn (87.5% > 80%)


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_memory_info_with_floats(self) -> None:
        """MemoryInfo should handle float values."""
        info = MemoryInfo(used_mb=1234.56, total_mb=5678.90, free_mb=4444.34)

        assert info.used_mb == pytest.approx(1234.56)
        assert info.utilization == pytest.approx(1234.56 / 5678.90)

    @patch("markdown_reallocator.utils.memory.get_gpu_memory")
    def test_gpu_memory_decrease(self, mock_get_gpu) -> None:
        """GPUMemoryMonitor should handle memory decrease (freed memory)."""
        # Memory decreased (unlikely but possible)
        mock_get_gpu.side_effect = [
            MemoryInfo(used_mb=3000.0, total_mb=8000.0, free_mb=5000.0),
            MemoryInfo(used_mb=2000.0, total_mb=8000.0, free_mb=6000.0),
        ]

        with GPUMemoryMonitor() as monitor:
            pass

        assert monitor.memory_used_mb == pytest.approx(-1000.0)

    @patch("markdown_reallocator.utils.memory.get_gpu_memory")
    def test_check_zero_required_memory(self, mock_get_gpu) -> None:
        """Should handle zero required memory."""
        mock_get_gpu.return_value = MemoryInfo(
            used_mb=7000.0, total_mb=8000.0, free_mb=1000.0
        )

        assert check_gpu_memory_available(0.0) is True

    @patch("markdown_reallocator.utils.memory.subprocess.run")
    def test_gpu_memory_with_spaces(self, mock_run) -> None:
        """Should handle extra whitespace in nvidia-smi output."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "  2048 ,  8192  "
        mock_run.return_value = mock_result

        memory_info = get_gpu_memory()

        assert memory_info is not None
        assert memory_info.used_mb == 2048.0
        assert memory_info.total_mb == 8192.0

    def test_system_memory_with_different_units(self) -> None:
        """Should handle different unit formats (though spec is kB)."""
        meminfo_content = """MemTotal:       16384000 kB
MemAvailable:    12288000 kB
"""
        with patch("builtins.open", mock_open(read_data=meminfo_content)):
            memory_info = get_system_memory()

            # Should convert kB to MB correctly
            assert memory_info.total_mb == pytest.approx(16000.0, rel=1e-2)
