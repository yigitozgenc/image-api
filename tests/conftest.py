"""Shared pytest fixtures and configuration."""

import pytest
from fastapi.testclient import TestClient

from image_api.service import app


@pytest.fixture
def client() -> TestClient:
    """Create a test client for the FastAPI app."""
    return TestClient(app)


