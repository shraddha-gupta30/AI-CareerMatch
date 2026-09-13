"""
Application Configuration Module.
Loads environment variables using Pydantic Settings and pathlib.Path for all filesystem paths.
"""
from pathlib import Path
from typing import List
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

    # CORS Whitelist for Local Development
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # Security (Used in Phase 3+)
    SECRET_KEY: str = "development_only_secret_key_minimum_32_characters_random_string"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database (Used in Phase 2+)
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_careermatch_db"

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
