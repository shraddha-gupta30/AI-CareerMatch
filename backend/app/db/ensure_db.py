"""
Ensures the target PostgreSQL database exists before migrations and seeding.
Connects to the maintenance 'postgres' database and creates 'ai_careermatch_db' if absent.
"""
import asyncio
import asyncpg
from app.core.config import settings
from app.core.logging import logger


async def ensure_database_exists() -> bool:
    """Checks for target database existence and creates it if needed."""
    url = settings.DATABASE_URL.replace("+asyncpg", "")
    base_url, _, target_db = url.rpartition("/")
    maint_url = f"{base_url}/postgres"

    logger.info(f"Connecting to maintenance database to verify '{target_db}'...")
    try:
        conn = await asyncpg.connect(maint_url, timeout=5)
        val = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", target_db
        )
        if not val:
            logger.info(f"Database '{target_db}' not found. Creating database...")
            await conn.execute(f'CREATE DATABASE "{target_db}"')
            logger.info(f"Database '{target_db}' created successfully.")
        else:
            logger.info(f"Database '{target_db}' already exists.")
        await conn.close()
        return True
    except Exception as exc:
        logger.error(f"Failed to connect or create database '{target_db}': {exc}")
        return False


if __name__ == "__main__":
    success = asyncio.run(ensure_database_exists())
    if not success:
        exit(1)
