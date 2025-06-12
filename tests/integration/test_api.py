"""Integration tests for API endpoints."""

import pytest
from unittest.mock import patch


class TestShipmentAPI:
    """Integration tests for shipment API endpoints."""
    
    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get('/api/v1/health')
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
        assert 'version' in data
        assert 'timestamp' in data
    
    def test_get_all_shipments(self, client):
        """Test getting all shipments."""
        response = client.get('/api/v1/shipments')
        
        assert response.status_code == 200
        data = response.json()
        assert 'shipments' in data
        assert 'total' in data
        assert data['total'] >= 0
    
    def test_get_shipments_by_carrier(self, client):
        """Test getting shipments filtered by carrier."""
        response = client.get('/api/v1/shipments?carrier=DHL')
        
        assert response.status_code == 200
        data = response.json()
        
        # All returned shipments should be from DHL
        for shipment in data['shipments']:
            assert shipment['carrier'] == 'DHL'
    
    def test_get_shipment_by_tracking_number(self, client):
        """Test getting shipment by tracking number."""
        response = client.get('/api/v1/shipments/TN12345678')
        
        assert response.status_code == 200
        data = response.json()
        assert 'shipment' in data
        assert data['shipment']['tracking_number'] == 'TN12345678'
    
    def test_get_shipment_not_found(self, client):
        """Test getting non-existent shipment."""
        response = client.get('/api/v1/shipments/TN545789')
        
        assert response.status_code == 404
        data = response.text.lower()
        assert 'not found' in data

    def test_get_shipment_invalid(self, client):
        """Test getting non-existent shipment."""
        response = client.get('/api/v1/shipments/INVALID')

        assert response.status_code == 422

    def test_get_shipment_with_carrier_filter(self, client):
        """Test getting shipment with carrier filter."""
        # Correct carrier
        response = client.get('/api/v1/shipments/TN12345678?carrier=DHL')
        assert response.status_code == 200
        
        # Wrong carrier
        response = client.get('/api/v1/shipments/TN12345678?carrier=UPS')
        assert response.status_code == 404
    
    @patch('src.shipment_tracker_api.services.weather_service.requests.get')
    def test_get_shipment_with_weather(self, mock_get, client):
        """Test getting shipment with weather data."""
        # Mock weather API response
        mock_response = mock_get.return_value
        mock_response.json.return_value = {
            'name': 'New York',
            'main': {
                'temp': 20.0,
                'feels_like': 22.0,
                'humidity': 60
            },
            'weather': [{'description': 'clear sky'}],
            'wind': {'speed': 5.0}
        }
        mock_response.raise_for_status.return_value = None
        
        response = client.get('/api/v1/shipments/TN12345678?include_weather=true')
        
        assert response.status_code == 200
        data = response.json()
        assert 'shipment' in data
        assert 'weather' in data
        assert data['weather']['location'] == 'New York'
        assert data['weather']['temperature'] == 20.0
    
    def test_get_shipment_without_weather(self, client):
        """Test getting shipment without weather data."""
        response = client.get('/api/v1/shipments/TN12345678?include_weather=false')
        
        assert response.status_code == 200
        data = response.json()
        assert 'shipment' in data
        assert 'weather' not in data
    
    @patch('src.shipment_tracker_api.services.weather_service.requests.get')
    def test_get_shipment_weather_error(self, mock_get, client):
        """Test shipment response when weather API fails."""
        # Mock weather API error
        expcetion_string = 'Weather API Error'
        mock_get.side_effect = Exception()
        
        response = client.get('/api/v1/shipments/TN12345678?include_weather=true')
        
        assert response.status_code == 200
        data = response.json()
        assert 'shipment' in data
        assert 'weather_error' in data
        #assert expcetion_string in data['weather_error']

    @pytest.mark.skip(reason="Deactivated as long as domain is unknown")
    def test_api_cors_headers(self, client):
        """Test CORS headers are present."""
        response = client.get('/api/v1/health')
        
        # CORS headers should be present in the production version
        assert 'Access-Control-Allow-Origin' in response.headers
    
    def test_api_content_type(self, client):
        """Test API returns JSON content type."""
        response = client.get('/api/v1/health')
        
        assert response.headers['content-type'] == 'application/json'