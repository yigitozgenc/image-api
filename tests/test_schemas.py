"""Tests for Pydantic schemas validation."""

import pytest
from decimal import Decimal

from image_api.models.schemas import FrameQueryParams, FrameResponse


def test_frame_query_params_valid() -> None:
    """Test valid FrameQueryParams."""
    params = FrameQueryParams(
        depth_min=Decimal("1000.0"),
        depth_max=Decimal("2000.0"),
        colormap="viridis",
        limit=10,
    )
    
    assert params.depth_min == Decimal("1000.0")
    assert params.depth_max == Decimal("2000.0")
    assert params.colormap == "viridis"
    assert params.limit == 10


def test_frame_query_params_defaults() -> None:
    """Test FrameQueryParams with default values."""
    params = FrameQueryParams(
        depth_min=Decimal("1000.0"),
        depth_max=Decimal("2000.0"),
    )
    
    assert params.colormap == "viridis"  # Default
    assert params.limit is None  # Default


def test_frame_query_params_depth_validation() -> None:
    """Test depth validation (must be non-negative)."""
    with pytest.raises(ValueError, match="Depth values must be non-negative"):
        FrameQueryParams(
            depth_min=Decimal("-100.0"),
            depth_max=Decimal("2000.0"),
        )


def test_frame_query_params_depth_range_validation() -> None:
    """Test depth_min <= depth_max validation."""
    with pytest.raises(ValueError, match="depth_min must be less than or equal to depth_max"):
        FrameQueryParams(
            depth_min=Decimal("2000.0"),
            depth_max=Decimal("1000.0"),
        )


def test_frame_query_params_limit_validation() -> None:
    """Test limit validation (must be between 1 and 10000)."""
    # Valid limit
    params = FrameQueryParams(
        depth_min=Decimal("1000.0"),
        depth_max=Decimal("2000.0"),
        limit=5000,
    )
    assert params.limit == 5000
    
    # Invalid: too small
    with pytest.raises(Exception):  # Pydantic validation error
        FrameQueryParams(
            depth_min=Decimal("1000.0"),
            depth_max=Decimal("2000.0"),
            limit=0,
        )
    
    # Invalid: too large
    with pytest.raises(Exception):  # Pydantic validation error
        FrameQueryParams(
            depth_min=Decimal("1000.0"),
            depth_max=Decimal("2000.0"),
            limit=10001,
        )


def test_frame_query_params_depth_conversion() -> None:
    """Test depth value conversion from int/float/str."""
    # From int
    params1 = FrameQueryParams(
        depth_min=1000,
        depth_max=2000,
    )
    assert isinstance(params1.depth_min, Decimal)
    
    # From float
    params2 = FrameQueryParams(
        depth_min=1000.5,
        depth_max=2000.5,
    )
    assert isinstance(params2.depth_min, Decimal)
    
    # From str
    params3 = FrameQueryParams(
        depth_min="1000.0",
        depth_max="2000.0",
    )
    assert isinstance(params3.depth_min, Decimal)


def test_frame_response() -> None:
    """Test FrameResponse model."""
    response = FrameResponse(
        depth=1500.5,
        data="base64encodeddata",
        metadata={"min": 0.0, "max": 255.0, "mean": 128.0},
    )
    
    assert response.depth == 1500.5
    assert response.data == "base64encodeddata"
    assert response.metadata["min"] == 0.0
    assert response.metadata["max"] == 255.0

