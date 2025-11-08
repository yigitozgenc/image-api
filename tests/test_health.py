"""Tests for health check endpoints."""

from fastapi.testclient import TestClient

from image_api.service import app


def test_root_endpoint(client: TestClient) -> None:
    """Test root endpoint returns API information."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Image Frame API"
    assert data["version"] == "0.1.0"
    assert "docs" in data
    assert "health" in data


def test_health_endpoint(client: TestClient) -> None:
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data


def test_ready_endpoint(client: TestClient) -> None:
    """Test readiness check endpoint."""
    response = client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "timestamp" in data
    assert "database" in data
    assert "tables_exist" in data
    assert "connected" in data


