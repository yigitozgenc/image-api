"""Image processing utilities for resizing and colormap application."""

import base64
from typing import TYPE_CHECKING

import matplotlib.cm as cm
import numpy as np
from PIL import Image

from image_api.config.settings import settings
from image_api.models.schemas import ColormapName

if TYPE_CHECKING:
    from numpy.typing import NDArray


def resize_image(
    image_array: "NDArray[np.uint8]", target_width: int
) -> "NDArray[np.uint8]":
    """Resize image array using LANCZOS algorithm (highest quality).

    Args:
        image_array: 1D array of pixel values (grayscale)
        target_width: Target width for resized image

    Returns:
        NDArray[np.uint8]: Resized 1D array of pixel values

    Example:
        >>> arr = np.array([1, 2, 3, 4] * 50, dtype=np.uint8)  # 200 pixels
        >>> resized = resize_image(arr, 150)
        >>> len(resized)
        150
    """
    # Reshape to 2D (assuming single row, original width)
    original_width = len(image_array)
    height = 1

    # Reshape to 2D image
    image_2d = image_array.reshape((height, original_width))

    # Convert to PIL Image
    pil_image = Image.fromarray(image_2d, mode="L")

    # Resize using LANCZOS (highest quality)
    resized_image = pil_image.resize(
        (target_width, height),
        resample=Image.Resampling.LANCZOS,
    )

    # Convert back to numpy array and flatten
    resized_array = np.array(resized_image, dtype=np.uint8).flatten()

    return resized_array


def apply_colormap(
    grayscale_array: "NDArray[np.uint8]", colormap_name: ColormapName
) -> "NDArray[np.uint8]":
    """Apply colormap to grayscale array, converting to RGB.

    Args:
        grayscale_array: 1D array of grayscale pixel values (0-255)
        colormap_name: Name of colormap to apply

    Returns:
        NDArray[np.uint8]: 3D array of RGB values (height, width, 3)

    Example:
        >>> arr = np.array([0, 128, 255], dtype=np.uint8)
        >>> rgb = apply_colormap(arr, "viridis")
        >>> rgb.shape
        (1, 3, 3)
    """
    # Normalize to [0, 1] range
    normalized = grayscale_array.astype(np.float32) / 255.0

    # Get colormap
    colormap = cm.get_cmap(colormap_name)

    # Apply colormap - colormap expects scalar or array, returns (N, 4) for array
    rgba = colormap(normalized)

    # Handle both scalar and array cases
    if rgba.ndim == 1:
        rgba = rgba.reshape(1, -1)

    # Convert to uint8 and extract RGB (drop alpha)
    rgb = (rgba[:, :3] * 255).astype(np.uint8)

    # Reshape to (height, width, 3) for single row
    height = 1
    width = len(grayscale_array)
    rgb_reshaped = rgb.reshape((height, width, 3))

    return rgb_reshaped


def encode_rgb_to_base64(rgb_array: "NDArray[np.uint8]") -> str:
    """Encode RGB array to base64 string for JSON serialization.

    Args:
        rgb_array: 3D array of RGB values (height, width, 3)

    Returns:
        str: Base64-encoded string of RGB data

    Raises:
        ValueError: If encoding fails or produces invalid base64

    Example:
        >>> rgb = np.array([[[255, 0, 0]]], dtype=np.uint8)
        >>> encoded = encode_rgb_to_base64(rgb)
        >>> isinstance(encoded, str)
        True
    """
    # Validate input
    if rgb_array.size == 0:
        raise ValueError("Cannot encode empty array")
    if rgb_array.dtype != np.uint8:
        raise ValueError(f"Expected uint8 array, got {rgb_array.dtype}")

    # Flatten to 1D array
    flattened = rgb_array.flatten()

    # Encode to base64
    encoded = base64.b64encode(flattened.tobytes()).decode("utf-8")

    return encoded


def calculate_image_statistics(
    image_array: "NDArray[np.uint8]",
) -> dict[str, float]:
    """Calculate image statistics (min, max, mean, std).

    Args:
        image_array: Array of pixel values

    Returns:
        dict: Statistics with keys: min, max, mean, std

    Example:
        >>> arr = np.array([0, 128, 255], dtype=np.uint8)
        >>> stats = calculate_image_statistics(arr)
        >>> stats["min"]
        0.0
        >>> stats["max"]
        255.0
    """
    return {
        "min": float(np.min(image_array)),
        "max": float(np.max(image_array)),
        "mean": float(np.mean(image_array)),
        "std": float(np.std(image_array)),
    }

