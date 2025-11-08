"""Tests for compression utilities."""

import numpy as np
import pytest

from image_api.utilities.compression import (
    calculate_compression_ratio,
    compress_array,
    decompress_array,
)


def test_compress_and_decompress() -> None:
    """Test compression and decompression round-trip."""
    original = np.array([1, 2, 3, 4, 5, 255, 128, 0], dtype=np.uint8)
    
    compressed = compress_array(original)
    decompressed = decompress_array(compressed)
    
    assert np.array_equal(original, decompressed)
    assert decompressed.dtype == np.uint8


def test_compress_large_array() -> None:
    """Test compression with larger array."""
    original = np.array([i % 256 for i in range(1000)], dtype=np.uint8)
    
    compressed = compress_array(original)
    decompressed = decompress_array(compressed)
    
    assert np.array_equal(original, decompressed)
    assert len(compressed) < len(original)  # Should be compressed


def test_compress_empty_array() -> None:
    """Test compression of empty array."""
    original = np.array([], dtype=np.uint8)
    
    compressed = compress_array(original)
    decompressed = decompress_array(compressed)
    
    assert np.array_equal(original, decompressed)


def test_decompress_invalid_data() -> None:
    """Test decompression with invalid data raises error."""
    invalid_data = b"not valid gzip data"
    
    with pytest.raises(ValueError, match="Failed to decompress"):
        decompress_array(invalid_data)


def test_calculate_compression_ratio() -> None:
    """Test compression ratio calculation."""
    ratio = calculate_compression_ratio(1000, 200)
    assert ratio == 5.0


def test_calculate_compression_ratio_zero_compressed() -> None:
    """Test compression ratio with zero compressed size."""
    ratio = calculate_compression_ratio(1000, 0)
    assert ratio == 0.0


def test_calculate_compression_ratio_small_values() -> None:
    """Test compression ratio with small values."""
    ratio = calculate_compression_ratio(100, 50)
    assert ratio == 2.0


