"""Database client singleton for async database operations."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from image_api.config.settings import settings
from image_api.models.database import Base


class DatabaseClient:
    """Singleton database client for managing async database connections."""

    def __init__(self) -> None:
        """Initialize database client."""
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None

    def initialize(self) -> None:
        """Initialize database engine and session factory.

        Called once on application startup.
        """
        self._engine = create_async_engine(
            settings.database_url,
            pool_size=settings.database_pool_size,
            max_overflow=settings.database_max_overflow,
            pool_pre_ping=True,
            echo=False,
        )
        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )

    async def create_tables(self) -> None:
        """Create all database tables."""
        if self._engine is None:
            raise RuntimeError("Database client not initialized")
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Context manager for database sessions.

        Yields:
            AsyncSession: Database session

        Example:
            async with db_client.session() as session:
                result = await session.execute(query)
        """
        if self._session_factory is None:
            raise RuntimeError("Database client not initialized")

        session = self._session_factory()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    async def close(self) -> None:
        """Close database engine and cleanup resources."""
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None

    async def health_check(self) -> bool:
        """Check database connection health.

        Returns:
            bool: True if database is accessible, False otherwise
        """
        if self._engine is None:
            return False
        try:
            async with self._engine.connect() as conn:
                result = await conn.execute(text("SELECT 1"))
                row = result.fetchone()
                if row is None:
                    return False
            return True
        except Exception as e:
            # Log error for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Database health check failed: {type(e).__name__}: {e}")
            return False

    async def tables_exist(self) -> bool:
        """Check if database tables exist.

        Returns:
            bool: True if tables exist, False otherwise
        """
        if self._engine is None:
            return False
        try:
            async with self._engine.begin() as conn:
                # Check if image_frames table exists
                result = await conn.execute(
                    text(
                        """
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables
                            WHERE table_schema = 'public'
                            AND table_name = 'image_frames'
                        )
                        """
                    )
                )
                exists = result.scalar()
                return bool(exists)
        except Exception:
            return False


# Global singleton instance
db_client = DatabaseClient()

