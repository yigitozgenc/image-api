"""Script to clear all data from the database."""

import asyncio
import sys

from sqlalchemy import text

from image_api.clients.database import db_client
from image_api.config.logging_config import setup_logging


async def clear_database() -> None:
    """Clear all data from the database tables.
    
    This will delete all records from image_frames table but keep the table structure.
    """
    # Initialize database
    db_client.initialize()
    
    if db_client._engine is None:
        raise RuntimeError("Database client not initialized")
    
    print("Connecting to database...")
    
    # Check connection
    is_connected = await db_client.health_check()
    if not is_connected:
        raise RuntimeError("Cannot connect to database")
    
    print("✓ Database connected")
    
    # Check if table exists
    tables_exist = await db_client.tables_exist()
    if not tables_exist:
        print("⚠ Table 'image_frames' does not exist. Nothing to clear.")
        await db_client.close()
        return
    
    print("Clearing all data from image_frames table...")
    
    try:
        async with db_client._engine.begin() as conn:
            # Delete all records
            result = await conn.execute(text("DELETE FROM image_frames"))
            deleted_count = result.rowcount
            
        print(f"✓ Deleted {deleted_count} records from image_frames table")
        
        # Verify deletion
        async with db_client._engine.begin() as conn:
            result = await conn.execute(text("SELECT COUNT(*) FROM image_frames"))
            remaining_count = result.scalar()
            
        if remaining_count == 0:
            print("✓ Database cleared successfully")
        else:
            print(f"⚠ Warning: {remaining_count} records still remain")
            
    except Exception as e:
        print(f"✗ Error clearing database: {e}", file=sys.stderr)
        raise
    
    finally:
        await db_client.close()


async def main() -> None:
    """Main entry point for database clearing."""
    setup_logging()
    
    try:
        await clear_database()
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

