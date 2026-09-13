"""
Main FastAPI Application Entrypoint.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import logger


from starlette.requests import Request
from starlette.responses import JSONResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION} ({settings.APP_ENV})")
    upload_dir = settings.upload_path
    logger.info(f"Upload directory initialized at: {upload_dir}")

    # Self-healing database initialization: ensure all tables and seeds exist
    try:
        from app.db.session import engine
        from app.models import Base
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database schema initialized and verified successfully.")

        from app.data.seed_data import run_seed
        await run_seed()
        logger.info("Database seed data verified successfully.")
    except Exception as exc:
        logger.error(f"Error during startup database initialization/seeding: {exc}")

    yield
    logger.info(f"Shutting down {settings.APP_NAME}")


def create_application() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="AI CareerMatch — Intelligent Job Matching & Career Gap Analysis Platform API",
        debug=settings.DEBUG,
        lifespan=lifespan,
    )

    # CORS Middleware Configuration for Local Development & Render Production
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_origin_regex=r"^https://.*\.onrender\.com$",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Error handling middleware to ensure CORS headers accompany 500 responses
    @app.middleware("http")
    async def global_exception_handler(request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as exc:
            logger.error(f"Unhandled server error on {request.method} {request.url.path}: {exc}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "code": "INTERNAL_SERVER_ERROR",
                        "message": "An unexpected server error occurred.",
                    }
                },
            )

    # Register Exception Handlers
    register_exception_handlers(app)

    # Register API Routers
    app.include_router(api_router, prefix="/api/v1")

    return app


app = create_application()
