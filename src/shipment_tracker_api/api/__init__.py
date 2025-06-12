"""API endpoints for the Shipment Tracker API."""

from .shipment_api import router as shipment_router
from .health_api import router as health_router

__all__ = ["shipment_router", "health_router"]