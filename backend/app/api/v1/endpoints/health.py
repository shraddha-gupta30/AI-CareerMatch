"""
Health API Endpoints: Service Health and Database Readiness.
"""
from fastapi import APIRouter, Response, status
from app.core.config import settings
from app.db.session import check_db_connection
from app.schemas.health import HealthResponse, DatabaseHealthResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Service Health Check",
    description="Returns the operational status of the AI CareerMatch backend service.",
)
async def get_health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service="ai-careermatch-backend",
        version=settings.APP_VERSION,
        environment=settings.APP_ENV,
    )


@router.get(
    "/health/db",
    response_model=DatabaseHealthResponse,
    summary="Database Readiness Check",
    description="Probes PostgreSQL database connectivity via a live query.",
)
async def get_db_health(response: Response) -> DatabaseHealthResponse:
    is_connected = await check_db_connection()
    if is_connected:
        return DatabaseHealthResponse(
            status="ok",
            database="postgresql",
            connected=True,
            details="Database is responsive and accepting queries.",
        )
    else:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return DatabaseHealthResponse(
            status="unavailable",
            database="postgresql",
            connected=False,
            details="PostgreSQL database service is offline or unreachable at the configured DATABASE_URL.",
        )
