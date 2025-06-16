"""Main application entry point."""

import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import uvicorn

from .services.shipment_service import ShipmentService
from .services.weather_service import WeatherService
from .api.shipment_api import router as shipment_router, set_services
from .api.health_api import router as health_router


def create_app(config=None) -> FastAPI:
    """Create and configure FastAPI application using factory pattern."""
    load_dotenv()
    
    # Initialize services outside of lifespan to make them available
    csv_file = Path(__file__).parent.parent.parent / "data" / "sample_data.csv"
    shipment_service = ShipmentService(str(csv_file))
    weather_service = WeatherService(
        api_key=os.getenv('WEATHER_API_KEY'),
        redis_url=os.getenv('REDIS_URL')
    )
    
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Manage application lifespan for async resources."""
        # Startup
        yield
        # Shutdown - cleanup async resources
        await weather_service.close()
    
    # Create sub-applications for each API version
    app_v1 = FastAPI(
        title="Shipment Tracker API",
        description="API for tracking shipments with weather information",
        version="1.0.0",
        contact={
            "name": "API Support",
            "email": "engineering@benediktsvogler.com" #this will print out a pydantic warning
        },
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )
    
    # Main application with lifespan
    app = FastAPI(
        title="Shipment Tracker API - All Versions",
        description="Select an API version below",
        docs_url=None,  # Disable docs at root
        redoc_url=None,
        openapi_url=None,
        lifespan=lifespan
    )
    
    # Enable CORS on v1 app
    app_v1.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Set services for dependency injection
    set_services(shipment_service, weather_service)
    
    # Include routers in v1 app
    app_v1.include_router(shipment_router)
    
    # Mount v1 app
    app.mount("/api/v1", app_v1)
    
    # Add health check at the root level
    app.include_router(health_router)
    
    # Add a root endpoint that lists available versions
    @app.get("/")
    async def root():
        return {
            "message": "Shipment Tracker API",
            "versions": {
                "v1": {
                    "url": "/api/v1",
                    "docs": "/api/v1/docs",
                    "redoc": "/api/v1/redoc",
                    "openapi": "/api/v1/openapi.json"
                }
            }
        }
    
    return app


def main():
    """The main entry point for running the application when the factory pattern is not used and uvicorn is started programmatically."""
    app = create_app()
    
    host = os.getenv('API_HOST', '0.0.0.0')
    port = int(os.getenv('API_PORT', 8000))
    debug = os.getenv('DEBUG', 'False').lower() == 'true'
    
    print(f"Starting Shipment Tracker API on {host}:{port}")
    print(f"Debug mode: {debug}")
    print(f"API v1 Documentation: http://{host}:{port}/api/v1/docs")
    print(f"Available versions: http://{host}:{port}/")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=debug,
        log_level="debug" if debug else "info"
    )


if __name__ == '__main__':
    main()