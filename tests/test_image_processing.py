"""Tests for image processing utilities."""

import base64

import numpy as np
import pytest

from image_api.utilities.image_processing import (
    apply_colormap,
    calculate_image_statistics,
    encode_rgb_to_base64,
    resize_image,
)


def test_resize_image() -> None:
    """Test image resizing functionality."""
    # Create a test array with 200 pixels
    original_array = np.array([i % 256 for i in range(200)], dtype=np.uint8)
    
    # Resize to 150 pixels
    resized = resize_image(original_array, 150)
    
    assert len(resized) == 150
    assert resized.dtype == np.uint8
    assert isinstance(resized, np.ndarray)


def test_apply_colormap() -> None:
    """Test colormap application."""
    # Create a simple grayscale array
    grayscale = np.array([0, 128, 255], dtype=np.uint8)
    
    # Apply viridis colormap
    rgb = apply_colormap(grayscale, "viridis")
    
    assert rgb.shape == (1, 3, 3)  # (height, width, channels)
    assert rgb.dtype == np.uint8
    assert np.all(rgb >= 0) and np.all(rgb <= 255)


def test_apply_colormap_different_colormaps() -> None:
    """Test different colormap names."""
    grayscale = np.array([0, 128, 255], dtype=np.uint8)
    
    colormaps = ["viridis", "plasma", "hot", "cool", "gray"]
    for colormap_name in colormaps:
        rgb = apply_colormap(grayscale, colormap_name)  # type: ignore[arg-type]
        assert rgb.shape == (1, 3, 3)
        assert rgb.dtype == np.uint8


def test_encode_rgb_to_base64() -> None:
    """Test RGB to base64 encoding."""
    # Create a simple RGB array
    rgb = np.array([[[255, 0, 0], [0, 255, 0], [0, 0, 255]]], dtype=np.uint8)
    
    encoded = encode_rgb_to_base64(rgb)
    
    assert isinstance(encoded, str)
    # Verify it's valid base64
    decoded = base64.b64decode(encoded)
    assert len(decoded) == 9  # 3 pixels * 3 channels = 9 bytes


def test_encode_rgb_to_base64_empty_array() -> None:
    """Test encoding empty array raises error."""
    rgb = np.array([], dtype=np.uint8).reshape(0, 0, 3)
    
    with pytest.raises(ValueError, match="Cannot encode empty array"):
        encode_rgb_to_base64(rgb)


def test_calculate_image_statistics() -> None:
    """Test image statistics calculation."""
    image_array = np.array([0, 128, 255], dtype=np.uint8)
    
    stats = calculate_image_statistics(image_array)
    
    assert stats["min"] == 0.0
    assert stats["max"] == 255.0
    assert stats["mean"] == pytest.approx(127.67, rel=0.01)
    assert "std" in stats
    assert isinstance(stats["std"], float)


def test_calculate_image_statistics_single_value() -> None:
    """Test statistics with single value."""
    image_array = np.array([128], dtype=np.uint8)
    
    stats = calculate_image_statistics(image_array)
    
    assert stats["min"] == 128.0
    assert stats["max"] == 128.0
    assert stats["mean"] == 128.0
    assert stats["std"] == 0.0


