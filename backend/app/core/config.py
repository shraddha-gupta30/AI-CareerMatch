"""
Application Configuration Module.
Loads environment variables using Pydantic Settings and pathlib.Path for all filesystem paths.
"""
from pathlib import Path
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# Project Root Directory (AI CareerMatch/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(
            str(BACKEND_DIR / ".env"),
            str(PROJECT_ROOT / ".env"),
        ),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Core Application Settings
    APP_NAME: str = "AI CareerMatch"
    APP_VERSION: str = "0.1.0"
    APP_ENV: str = "development"
    DEBUG: bool = True
    PORT: int = 8000

    # CORS Whitelist for Local Development & Production
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v: Union[List[str], str]) -> List[str]:
        """Allows ALLOWED_ORIGINS to be configured as a comma-separated list or JSON array in production."""
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # Security (Used in Phase 3+)
    SECRET_KEY: str = "development_only_secret_key_minimum_32_characters_random_string"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database (Used in Phase 2+)
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_careermatch_db"
    DB_TIMEOUT: float = 10.0

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def normalize_database_url(cls, v: str) -> str:
        """Normalizes postgres:// or postgresql:// to postgresql+asyncpg:// for SQLAlchemy asyncpg engine."""
        if isinstance(v, str):
            if v.startswith("postgres://"):
                v = v.replace("postgres://", "postgresql+asyncpg://", 1)
            elif v.startswith("postgresql://") and not v.startswith("postgresql+asyncpg://"):
                v = v.replace("postgresql://", "postgresql+asyncpg://", 1)
            # asyncpg accepts 'ssl' query parameter rather than 'sslmode'
            if "sslmode=" in v:
                v = v.replace("sslmode=", "ssl=")
        return v

    # AI Integration (Used in Phase 4+ Backend Only)
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.6-flash"

    # Storage Settings (strictly pathlib.Path)
    UPLOAD_DIR: str = "uploads/resumes"
    MAX_UPLOAD_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB

    @property
    def upload_path(self) -> Path:
        """Resolves the upload directory path relative to the project root."""
        resolved = PROJECT_ROOT / self.UPLOAD_DIR
        resolved.mkdir(parents=True, exist_ok=True)
        return resolved


settings = Settings()
