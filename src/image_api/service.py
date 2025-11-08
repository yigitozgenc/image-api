"""FastAPI application entrypoint with Prometheus metrics and lifecycle management."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from image_api.clients.database import db_client
from image_api.config.logging_config import setup_logging
from image_api.config.settings import settings
from image_api.routers import frames, health


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown."""
    # Startup
    setup_logging()
    db_client.initialize()
    await db_client.create_tables()

    yield

    # Shutdown
    await db_client.close()


# Create FastAPI app
app = FastAPI(
    title="Image Frame API",
    description="Production-grade image frame API for scientific/geological data visualization",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/swagger",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Prometheus metrics if enabled
if settings.prometheus_enabled:
    instrumentator = Instrumentator()
    instrumentator.instrument(app).expose(app)

# Register routers
app.include_router(health.router)
app.include_router(frames.router)


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint with API information."""
    return {
        "name": "Image Frame API",
        "version": "0.1.0",
        "docs": "/swagger",
        "health": "/health",
        "ready": "/ready",
    }

