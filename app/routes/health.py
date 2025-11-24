"""Health check endpoints"""

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from redis import Redis

from app.core.redis import get_redis
from app.config import get_settings

router = APIRouter()
settings = get_settings()


class HealthResponse(BaseModel):
    """Health check response model"""

    status: str
    service: str
    version: str
    environment: str


class DetailedHealthResponse(HealthResponse):
    """Detailed health check response with dependencies"""

    dependencies: dict[str, str]


@router.get("/health", status_code=status.HTTP_200_OK, response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Basic health check endpoint"""
    return HealthResponse(
        status="healthy",
        service="llm-guardrails",
        version="0.1.0",
        environment=settings.environment,
    )


@router.get(
    "/health/detailed",
    status_code=status.HTTP_200_OK,
    response_model=DetailedHealthResponse,
)
async def detailed_health_check(redis: Redis = Depends(get_redis)) -> DetailedHealthResponse:
    """Detailed health check with dependency status"""
    dependencies = {}

    # Check Redis
    try:
        redis.ping()
        dependencies["redis"] = "healthy"
    except Exception as e:
        dependencies["redis"] = f"unhealthy: {str(e)}"

    # Determine overall status
    overall_status = (
        "healthy" if all(status == "healthy" for status in dependencies.values()) else "degraded"
    )

    return DetailedHealthResponse(
        status=overall_status,
        service="llm-guardrails",
        version="0.1.0",
        environment=settings.environment,
        dependencies=dependencies,
    )

