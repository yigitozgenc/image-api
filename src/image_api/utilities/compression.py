"""Compression utilities for image data using gzip level 9."""

import gzip
import io
from typing import TYPE_CHECKING

import numpy as np

from image_api.config.settings import settings

if TYPE_CHECKING:
    from numpy.typing import NDArray


def compress_array(array: "NDArray[np.uint8]") -> bytes:
    """Compress NumPy array using gzip level 9 (maximum compression).

    Args:
        array: NumPy array of uint8 values to compress

    Returns:
        bytes: Compressed binary data

    Example:
        >>> arr = np.array([1, 2, 3], dtype=np.uint8)
        >>> compressed = compress_array(arr)
        >>> decompressed = decompress_array(compressed)
        >>> np.array_equal(arr, decompressed)
        True
    """
    buffer = io.BytesIO()

    with gzip.GzipFile(
        fileobj=buffer,
        mode="wb",
        compresslevel=settings.compression_level,
    ) as gz:
        np.save(gz, array, allow_pickle=False)

    return buffer.getvalue()


def decompress_array(compressed_data: bytes) -> "NDArray[np.uint8]":
    """Decompress NumPy array from gzip-compressed data.

    Args:
        compressed_data: Compressed binary data from compress_array

    Returns:
        NDArray[np.uint8]: Decompressed NumPy array

    Raises:
        ValueError: If decompression fails or data is invalid

    Example:
        >>> arr = np.array([1, 2, 3], dtype=np.uint8)
        >>> compressed = compress_array(arr)
        >>> decompressed = decompress_array(compressed)
        >>> np.array_equal(arr, decompressed)
        True
    """
    buffer = io.BytesIO(compressed_data)

    try:
        with gzip.GzipFile(fileobj=buffer, mode="rb") as gz:
            array = np.load(gz, allow_pickle=False)
            return array.astype(np.uint8)
    except (gzip.BadGzipFile, OSError, ValueError) as e:
        raise ValueError(f"Failed to decompress array: {e}") from e


def calculate_compression_ratio(original_size: int, compressed_size: int) -> float:
    """Calculate compression ratio.

    Args:
        original_size: Original data size in bytes
        compressed_size: Compressed data size in bytes

    Returns:
        float: Compression ratio (original_size / compressed_size)

    Example:
        >>> calculate_compression_ratio(1000, 200)
        5.0
    """
    if compressed_size == 0:
        return 0.0
    return float(original_size) / float(compressed_size)

