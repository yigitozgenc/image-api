"""Frame endpoints for image data."""

import logging
from decimal import Decimal

import numpy as np
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from image_api.clients.database import db_client
from image_api.models.schemas import FrameQueryParams, FrameResponse
from image_api.utilities.compression import decompress_array
from image_api.utilities.database_ops import get_frames_buffered
from image_api.utilities.image_processing import (
    apply_colormap,
    encode_rgb_to_base64,
)

router = APIRouter(prefix="/frames", tags=["frames"])


async def get_session() -> AsyncSession:
    """Dependency to get database session."""
    async with db_client.session() as session:
        yield session


@router.get("", response_model=list[FrameResponse])
async def get_frames(
    depth_min: Decimal = Query(..., description="Minimum depth value"),
    depth_max: Decimal = Query(..., description="Maximum depth value"),
    colormap: str = Query(
        default="viridis",
        description="Colormap name (viridis, plasma, hot, cool, etc.)",
    ),
    limit: int | None = Query(
        default=None, ge=1, le=10000, description="Maximum number of frames"
    ),
    session: AsyncSession = Depends(get_session),
) -> list[FrameResponse]:
    """Get image frames as JSON array.

    Args:
        depth_min: Minimum depth value
        depth_max: Maximum depth value
        colormap: Colormap name to apply
        limit: Optional maximum number of frames
        session: Database session

    Returns:
        list[FrameResponse]: List of frame data

    Raises:
        HTTPException: If query parameters are invalid
    """
    # Validate query parameters
    try:
        params = FrameQueryParams(
            depth_min=depth_min,
            depth_max=depth_max,
            colormap=colormap,  # type: ignore[arg-type]
            limit=limit,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    # Get all frames
    frames = await get_frames_buffered(
        session,
        params.depth_min,
        params.depth_max,
        params.limit,
    )

    # Process frames
    results: list[FrameResponse] = []
    for frame in frames:
        try:
            # Validate that resized_data is bytes
            if not isinstance(frame.resized_data, bytes):
                raise ValueError(
                    f"Invalid data type for resized_data: {type(frame.resized_data)}"
                )

            # Decompress resized data
            grayscale = decompress_array(frame.resized_data)

            # Validate decompressed data
            if grayscale.size == 0:
                raise ValueError("Decompressed array is empty")
            if grayscale.dtype != np.uint8:
                raise ValueError(f"Invalid dtype after decompression: {grayscale.dtype}")

            # Apply colormap
            rgb = apply_colormap(grayscale, params.colormap)

            # Validate RGB array
            if rgb.shape[2] != 3:
                raise ValueError(f"Invalid RGB shape: {rgb.shape}")

            # Encode to base64
            data = encode_rgb_to_base64(rgb)

            # Validate base64 encoding
            if not data or not isinstance(data, str):
                raise ValueError("Base64 encoding failed or returned invalid result")

            # Get metadata (frame_metadata is the attribute, metadata is the column name)
            metadata_dict = (
                frame.frame_metadata
                if isinstance(frame.frame_metadata, dict)
                else dict(frame.frame_metadata)
            )

            # Create response
            response = FrameResponse(
                depth=float(frame.depth),
                data=data,
                metadata=metadata_dict,
            )
            results.append(response)
        except Exception as e:
            # Log error and skip this frame
            logger = logging.getLogger(__name__)
            logger.error(
                f"Error processing frame depth={frame.depth}: {e}",
                exc_info=True,
            )
            # Skip this frame instead of failing the entire request
            continue

    return results

