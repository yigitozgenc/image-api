"""SQLAlchemy ORM models for image frames."""

from decimal import Decimal
from typing import Any

from sqlalchemy import JSON, Index, Numeric, Text
from sqlalchemy.dialects.postgresql import BYTEA
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    pass


class ImageFrame(Base):
    """Image frame model storing compressed grayscale image data."""

    __tablename__ = "image_frames"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    depth: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=2), nullable=False, index=True
    )
    original_data: Mapped[bytes] = mapped_column(BYTEA, nullable=False)
    resized_data: Mapped[bytes] = mapped_column(BYTEA, nullable=False)
    frame_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSON, nullable=False
    )

    __table_args__ = (
        Index("idx_depth_range", "depth"),
    )

    def __repr__(self) -> str:
        """String representation of ImageFrame."""
        return f"<ImageFrame(id={self.id}, depth={self.depth})>"

