"""Health checks for container orchestration and monitoring."""
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
try:
    import redis.asyncio as aioredis
except ImportError:
    aioredis = None

from app.database import get_db, get_redis

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_live():
    """Liveness probe: verifies service process is running."""
    return {"status": "ok"}


@router.get("/health/ready")
async def health_ready(
    db: AsyncSession = Depends(get_db),
    redis_client = Depends(get_redis),
):
    """Readiness probe: validates connectivity to PostgreSQL and Redis."""
    health_status = {"database": "unknown", "redis": "unknown"}
    is_ready = True

    # Test Database
    try:
        await db.execute(text("SELECT 1"))
        health_status["database"] = "connected"
    except Exception as e:
        health_status["database"] = f"error: {str(e)}"
        is_ready = False

    # Test Redis
    if redis_client is not None:
        try:
            await redis_client.ping()
            health_status["redis"] = "connected"
        except Exception as e:
            health_status["redis"] = f"error: {str(e)}"
    else:
        health_status["redis"] = "unconfigured (running standalone)"

    http_status = status.HTTP_200_OK if is_ready else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(
        status_code=http_status,
        content={"status": "ready" if is_ready else "degraded", "checks": health_status},
    )

