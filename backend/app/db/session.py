"""
SQLAlchemy Async Database Engine, Session Factory, and Dependency.
"""
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy import text
from app.core.config import settings
from app.core.logging import logger

# Create centralized AsyncEngine with connection timeout
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=True,
    connect_args={"timeout": 2.0, "command_timeout": 2.0},
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that provides an isolated AsyncSession."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_db_connection(timeout: float = 2.0) -> bool:
    """Verifies live database connectivity via a lightweight probe query."""
    async def _probe() -> bool:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            return result.scalar() == 1

    try:
        return await asyncio.wait_for(_probe(), timeout=timeout)
    except Exception as exc:
        logger.warning(f"Database connection check failed: {exc}")
        return False
