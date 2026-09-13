"""
Unit Tests for Health and Database Readiness Endpoints.
"""
from httpx import AsyncClient


async def test_service_health_endpoint(client: AsyncClient):
    """Verify that GET /api/v1/health returns status ok and correct service metadata."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "ai-careermatch-backend"
    assert "version" in data
    assert "environment" in data


async def test_database_health_endpoint_offline(client: AsyncClient):
    """
    Verify that GET /api/v1/health/db accurately reports database status.
    When PostgreSQL is offline, it must return 503 and connected=False without crashing.
    """
    response = await client.get("/api/v1/health/db")
    data = response.json()
    assert "database" in data
    assert data["database"] == "postgresql"
    assert "connected" in data
    if not data["connected"]:
        assert response.status_code == 503
        assert data["status"] == "unavailable"
    else:
        assert response.status_code == 200
        assert data["status"] == "ok"
