"""
Shared Pytest Fixtures for Backend Test Suite.
"""
from typing import AsyncGenerator
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from app.main import app
from app.db.session import engine


@pytest_asyncio.fixture(loop_scope="function")
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Provides an isolated async HTTP client and cleans up connection pools per test."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
    # Cleanly dispose connections so asyncpg doesn't attempt cleanup on closed loop
    await engine.dispose()
