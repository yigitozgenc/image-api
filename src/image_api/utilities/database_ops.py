"""Database operations for image frames."""

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from image_api.models.database import ImageFrame

if TYPE_CHECKING:
    from image_api.models.database import ImageFrame as ImageFrameType


async def get_frames_buffered(
    session: AsyncSession,
    depth_min: Decimal,
    depth_max: Decimal,
    limit: int | None = None,
) -> list["ImageFrameType"]:
    """Get all frames in memory (for buffered endpoint).

    Args:
        session: Database session
        depth_min: Minimum depth value
        depth_max: Maximum depth value
        limit: Optional maximum number of frames to return

    Returns:
        list[ImageFrame]: List of image frame instances

    Example:
        >>> async with db_client.session() as session:
        ...     frames = await get_frames_buffered(session, Decimal("9000"), Decimal("10000"))
        ...     print(len(frames))
    """
    query = (
        select(ImageFrame)
        .where(ImageFrame.depth >= depth_min)
        .where(ImageFrame.depth <= depth_max)
        .order_by(ImageFrame.depth)
    )

    if limit is not None:
        query = query.limit(limit)

    result = await session.execute(query)
    return list(result.scalars().all())


async def create_frame(
    session: AsyncSession,
    depth: Decimal,
    original_data: bytes,
    resized_data: bytes,
    metadata: dict[str, float],
) -> "ImageFrameType":
    """Create a new image frame record.

    Args:
        session: Database session
        depth: Depth value for the frame
        original_data: Compressed original image data
        resized_data: Compressed resized image data
        metadata: Frame metadata (min, max, mean, std, compression_ratio)

    Returns:
        ImageFrame: Created image frame instance

    Example:
        >>> async with db_client.session() as session:
        ...     frame = await create_frame(
        ...         session,
        ...         Decimal("9000.1"),
        ...         b"compressed_original",
        ...         b"compressed_resized",
        ...         {"min": 0.0, "max": 255.0, "mean": 128.0, "std": 50.0}
        ...     )
    """
    frame = ImageFrame(
        depth=depth,
        original_data=original_data,
        resized_data=resized_data,
        metadata=metadata,
    )
    session.add(frame)
    await session.flush()
    return frame

