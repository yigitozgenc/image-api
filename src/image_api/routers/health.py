"""Health check endpoints for liveness and readiness probes."""

from datetime import datetime

from fastapi import APIRouter, HTTPException, status

from image_api.clients.database import db_client
from image_api.models.schemas import HealthResponse, InitResponse, ReadyResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Liveness probe - indicates service is running.

    Returns:
        HealthResponse: Health status and timestamp
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat() + "Z",
    )


@router.get("/ready", response_model=ReadyResponse)
async def readiness_check() -> ReadyResponse:
    """Readiness probe - indicates service is ready to serve traffic.

    Checks database connectivity and table existence.

    Returns:
        ReadyResponse: Readiness status with database connection status
    """
    connected = await db_client.health_check()
    tables_exist = await db_client.tables_exist() if connected else False
    db_status = "connected" if connected else "disconnected"

    if not connected or not tables_exist:
        return ReadyResponse(
            status="not_ready",
            timestamp=datetime.utcnow().isoformat() + "Z",
            database=db_status,
            tables_exist=tables_exist,
            connected=connected,
        )

    return ReadyResponse(
        status="ready",
        timestamp=datetime.utcnow().isoformat() + "Z",
        database=db_status,
        tables_exist=tables_exist,
        connected=connected,
    )


@router.post("/init", response_model=InitResponse)
async def init_database() -> InitResponse:
    """Initialize database by creating tables.

    Creates all database tables if they don't exist.

    Returns:
        InitResponse: Initialization status

    Raises:
        HTTPException: 500 if initialization fails
    """
    try:
        # Check if already initialized
        if await db_client.tables_exist():
            return InitResponse(
                status="success",
                message="Database tables already exist",
                tables_created=False,
            )

        # Create tables
        await db_client.create_tables()

        # Verify tables were created
        if await db_client.tables_exist():
            return InitResponse(
                status="success",
                message="Database tables created successfully",
                tables_created=True,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to verify table creation",
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database initialization failed: {str(e)}",
        ) from e

