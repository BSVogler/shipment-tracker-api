"""Health check API endpoints."""
from datetime import timezone, datetime

from fastapi import APIRouter
from pydantic import BaseModel

from .. import __version__


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    version: str
    timestamp: str


router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse, summary="Health check")
async def health_check():
    """Check if the API is running and healthy."""
    return HealthResponse(
        status="healthy",
        version=__version__,
        timestamp=datetime.now(timezone.utc).isoformat()
    )