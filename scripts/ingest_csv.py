"""CSV ingestion script for processing and storing image frame data."""

import asyncio
import csv
import sys
from decimal import Decimal
from pathlib import Path

import numpy as np

from image_api.clients.database import db_client
from image_api.config.logging_config import setup_logging
from image_api.config.settings import settings
from image_api.models.database import ImageFrame
from image_api.utilities.compression import (
    calculate_compression_ratio,
    compress_array,
)
from image_api.utilities.image_processing import (
    calculate_image_statistics,
    resize_image,
)


async def process_csv_file(csv_path: Path, batch_size: int = 100) -> None:
    """Process CSV file and ingest image frames into database.

    Args:
        csv_path: Path to CSV file
        batch_size: Number of frames to process in each batch

    Raises:
        FileNotFoundError: If CSV file doesn't exist
        ValueError: If CSV format is invalid
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    # Initialize database
    db_client.initialize()
    await db_client.create_tables()

    # Read CSV file
    frames_to_insert: list[ImageFrame] = []
    total_processed = 0

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        row_count = sum(1 for _ in reader)
        f.seek(0)
        reader = csv.DictReader(f)

        print(f"Processing {row_count} rows from {csv_path}...")

        for row_num, row in enumerate(reader, start=1):
            try:
                # Extract depth
                depth = Decimal(str(row["depth"]))

                # Extract pixel values (col1 to col200)
                pixel_values: list[int] = []
                for i in range(1, settings.image_original_width + 1):
                    col_name = f"col{i}"
                    if col_name not in row:
                        raise ValueError(f"Missing column: {col_name}")
                    pixel_values.append(int(row[col_name]))

                # Convert to numpy array
                original_array = np.array(pixel_values, dtype=np.uint8)

                # Calculate statistics
                stats = calculate_image_statistics(original_array)

                # Resize image
                resized_array = resize_image(original_array, settings.image_resized_width)

                # Compress both versions
                original_compressed = compress_array(original_array)
                resized_compressed = compress_array(resized_array)

                # Calculate compression ratios
                original_size = len(original_array)
                resized_size = len(resized_array)

                original_ratio = calculate_compression_ratio(
                    original_size, len(original_compressed)
                )
                resized_ratio = calculate_compression_ratio(
                    resized_size, len(resized_compressed)
                )

                # Add compression ratios to metadata
                metadata = {
                    **stats,
                    "compression_ratio_original": original_ratio,
                    "compression_ratio_resized": resized_ratio,
                }

                # Create frame object
                frame = ImageFrame(
                    depth=depth,
                    original_data=original_compressed,
                    resized_data=resized_compressed,
                    frame_metadata=metadata,
                )

                frames_to_insert.append(frame)

                # Batch insert
                if len(frames_to_insert) >= batch_size:
                    async with db_client.session() as session:
                        session.add_all(frames_to_insert)
                        await session.commit()
                    total_processed += len(frames_to_insert)
                    print(
                        f"Processed {total_processed}/{row_count} rows "
                        f"({total_processed/row_count*100:.1f}%)"
                    )
                    frames_to_insert.clear()

            except Exception as e:
                print(f"Error processing row {row_num}: {e}", file=sys.stderr)
                continue

        # Insert remaining frames
        if frames_to_insert:
            async with db_client.session() as session:
                session.add_all(frames_to_insert)
                await session.commit()
            total_processed += len(frames_to_insert)

    print(f"\nIngestion complete! Processed {total_processed} frames.")
    await db_client.close()


async def main() -> None:
    """Main entry point for CSV ingestion."""
    if len(sys.argv) < 2:
        print("Usage: python -m scripts.ingest_csv <path_to_csv_file>")
        sys.exit(1)

    csv_path = Path(sys.argv[1])
    setup_logging()

    try:
        await process_csv_file(csv_path)
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

