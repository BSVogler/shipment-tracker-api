"""Shipment API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from typing import Optional, List, Annotated
from pydantic import BaseModel

from ..services.shipment_service import ShipmentService
from ..services.weather_service import WeatherService


class ShipmentResponse(BaseModel):
    """Shipment response model."""
    shipment: dict
    weather: Optional[dict] = None
    weather_error: Optional[str] = None


class ShipmentListResponse(BaseModel):
    """Shipment list response model."""
    shipments: list[dict]
    total: int


router = APIRouter(tags=["Shipments"])

# Dependency to get services (will be injected)
shipment_service: Optional[ShipmentService] = None
weather_service: Optional[WeatherService] = None


def get_shipment_service() -> ShipmentService:
    """Get shipment service dependency."""
    return shipment_service


def get_weather_service() -> WeatherService:
    """Get weather service dependency."""
    return weather_service


@router.get("/shipments/{tracking_number}", summary="Get shipment by tracking number")
async def get_shipment(
        tracking_number: Annotated[str, Path(
            description="The tracking number (must start with 'TN')",
            pattern="^TN.*"
        )],
        carrier: Optional[str] = Query(None, description="The carrier name (optional filter)"),
        include_weather: bool = Query(True, description="Include weather information for receiver location"),
        shipment_svc: ShipmentService = Depends(get_shipment_service),
        weather_svc: WeatherService = Depends(get_weather_service)
):
    """Retrieve shipment information along with weather data for the receiver location."""
    try:
        # Get shipment
        shipment = shipment_svc.get_shipment(
            tracking_number, carrier
        )

        if not shipment:
            raise HTTPException(status_code=404, detail="Shipment not found")

        # Build response dynamically, not using pydantic to allow omiting weather
        response = {"shipment": shipment.to_dict()}

        # Add weather information if requested
        if include_weather:
            try:
                weather = await weather_svc.get_weather_from_address(
                    shipment.receiver.address
                )
                if weather:
                    response["weather"] = weather.to_dict()
                else:
                    response["weather"] = None
                    response["weather_error"] = f"Failed to fetch weather"
            except Exception as e:
                # Weather fetch failed, but still return shipment data
                response["weather"] = None
                response["weather_error"] = f"Failed to fetch weather: {str(e)}"

        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/shipments", response_model=ShipmentListResponse, summary="List all shipments")
async def list_shipments(
        carrier: Optional[str] = Query(None, description="Filter by carrier name"),
        shipment_svc: ShipmentService = Depends(get_shipment_service)
):
    """Retrieve all shipments, optionally filtered by carrier."""
    try:
        shipments = shipment_svc.get_all_shipments(carrier)

        return ShipmentListResponse(
            shipments=[shipment.to_dict() for shipment in shipments],
            total=len(shipments)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


def set_services(shipment_svc: ShipmentService, weather_svc: WeatherService):
    """Set global service instances for dependency injection."""
    global shipment_service, weather_service
    shipment_service = shipment_svc
    weather_service = weather_svc
