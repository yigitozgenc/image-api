"""Pydantic request/response models for API validation."""

from decimal import Decimal
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, field_validator

# Supported colormap names
ColormapName = Literal[
    "viridis",
    "plasma",
    "inferno",
    "magma",
    "hot",
    "cool",
    "gray",
    "jet",
    "turbo",
    "rainbow",
]


class FrameResponse(BaseModel):
    """Response model for a single image frame."""

    depth: float = Field(..., description="Depth value for this frame")
    data: str = Field(..., description="Base64-encoded RGB image data")
    metadata: dict[str, Any] = Field(
        ..., description="Frame statistics (min, max, mean, std, compression ratios)"
    )

    model_config = {"json_schema_extra": {"example": {"depth": 9000.1, "data": "..."}}}


class FrameQueryParams(BaseModel):
    """Query parameters for frame endpoints."""

    depth_min: Decimal = Field(..., description="Minimum depth value")
    depth_max: Decimal = Field(..., description="Maximum depth value")
    colormap: ColormapName = Field(
        default="viridis", description="Colormap to apply to grayscale data"
    )
    limit: Optional[int] = Field(
        default=None, ge=1, le=10000, description="Maximum number of frames to return"
    )

    @field_validator("depth_min", "depth_max")
    @classmethod
    def validate_depth_range(cls, v: Decimal) -> Decimal:
        """Validate depth values are non-negative."""
        if v < 0:
            raise ValueError("Depth values must be non-negative")
        return v

    @field_validator("depth_min", "depth_max", mode="before")
    @classmethod
    def convert_depth(cls, v: Any) -> Decimal:
        """Convert depth to Decimal."""
        if isinstance(v, (int, float, str)):
            return Decimal(str(v))
        return v

    def model_post_init(self, __context: object) -> None:
        """Validate depth_min <= depth_max."""
        if self.depth_min > self.depth_max:
            raise ValueError("depth_min must be less than or equal to depth_max")


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str = Field(..., description="Health status")
    timestamp: str = Field(..., description="ISO timestamp of check")


class ReadyResponse(HealthResponse):
    """Readiness check response model."""

    database: str = Field(..., description="Database connection status")
    tables_exist: bool = Field(..., description="Whether database tables exist")
    connected: bool = Field(..., description="Whether database is connected")


class InitResponse(BaseModel):
    """Database initialization response model."""

    status: str = Field(..., description="Initialization status")
    message: str = Field(..., description="Status message")
    tables_created: bool = Field(..., description="Whether tables were created")

