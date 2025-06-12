"""Pytest configuration and fixtures."""
import pytest
import os
from pathlib import Path
from fastapi.testclient import TestClient

from src.shipment_tracker_api.main import create_app
from src.shipment_tracker_api.services.shipment_service import ShipmentService
from src.shipment_tracker_api.services.weather_service import WeatherService

csv_path = Path(__file__).parent.parent / "data" / "sample_data.csv"

@pytest.fixture
def shipment_service():
    """Create shipment service with test data."""
    return ShipmentService(str(csv_path))


@pytest.fixture
def weather_service():
    """Create weather service for testing."""
    return WeatherService(api_key="test_api_key")


@pytest.fixture
def app():
    """Create Flask app for testing."""
    # Set test environment variables
    os.environ['WEATHER_API_KEY'] = 'test_api_key'
    os.environ['FLASK_DEBUG'] = 'False'
    
    app = create_app()

    return app


@pytest.fixture
def client(app):
    """Create FastAPI test client."""
    return TestClient(app)