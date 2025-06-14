"""Unit tests for WeatherService."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta, timezone

from src.shipment_tracker_api.services.weather_service import WeatherService
from src.shipment_tracker_api.models.weather import Weather


class TestWeatherService:
    """Test cases for WeatherService."""
    
    @pytest.mark.asyncio
    async def test_memory_cache_save_and_retrieve(self, weather_service):
        """Test saving and retrieving from memory cache."""
        weather = Weather(
            location='New York',
            zip_code='10001',
            country='USA',
            temperature=20.0,
            feels_like=22.0,
            description='clear sky',
            humidity=60,
            wind_speed=5.0
        )
        
        cache_key = 'test_key'
        await weather_service._save_to_cache(cache_key, weather)
        
        cached_weather = await weather_service._get_from_cache(cache_key)
        assert cached_weather is not None
        assert cached_weather.location == 'New York'
        assert cached_weather.temperature == 20.0
    
    @pytest.mark.asyncio
    async def test_memory_cache_expiration(self, weather_service):
        """Test memory cache expiration."""
        weather = Weather(
            location='New York',
            zip_code='10001',
            country='USA',
            temperature=20.0,
            feels_like=22.0,
            description='clear sky',
            humidity=60,
            wind_speed=5.0
        )
        
        cache_key = 'test_key'
        
        # Manually set expired cache entry
        weather_service.memory_cache[cache_key] = {
            'weather': weather,
            'expires_at': datetime.now(timezone.utc) - timedelta(minutes=1)  # Expired
        }
        
        cached_weather = await weather_service._get_from_cache(cache_key)
        assert cached_weather is None
        assert cache_key not in weather_service.memory_cache
    
    @patch('src.shipment_tracker_api.services.weather_service.httpx.AsyncClient')
    @pytest.mark.asyncio
    async def test_get_weather_success(self, mock_client_class, weather_service):
        """Test successful weather API call."""
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        
        mock_response = Mock()
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
        mock_client.get.return_value = mock_response
        
        weather = await weather_service.get_weather('10001', 'USA')
        
        assert weather is not None
        assert weather.location == 'New York'
        assert weather.temperature == 20.0
        assert weather.zip_code == '10001'
        assert weather.country == 'USA'
    
    @patch('src.shipment_tracker_api.services.weather_service.httpx.AsyncClient')
    @pytest.mark.asyncio
    async def test_get_weather_api_error(self, mock_client_class, weather_service):
        """Test weather API error handling."""
        import httpx
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        mock_client.get.side_effect = httpx.RequestError('API Error')
        
        with pytest.raises(ValueError, match='Failed to fetch weather data'):
            await weather_service.get_weather('10001', 'USA')
    
    @pytest.mark.asyncio
    async def test_get_weather_no_api_key(self):
        """Test weather service without API key."""
        import os
        original_key = os.environ.get('WEATHER_API_KEY')
        
        # Temporarily remove the environment variable
        if 'WEATHER_API_KEY' in os.environ:
            del os.environ['WEATHER_API_KEY']
        
        try:
            service = WeatherService(api_key=None)
            
            with pytest.raises(ValueError, match='Weather API key not configured'):
                await service.get_weather('10001', 'USA')
        finally:
            # Restore original environment variable
            if original_key:
                os.environ['WEATHER_API_KEY'] = original_key
    
    @patch('src.shipment_tracker_api.services.weather_service.httpx.AsyncClient')
    @pytest.mark.asyncio
    async def test_get_weather_with_caching(self, mock_client_class, weather_service):
        """Test weather caching behavior."""
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        
        mock_response = Mock()
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
        mock_client.get.return_value = mock_response
        
        # First call should hit the API
        weather1 = await weather_service.get_weather('10001', 'USA')
        assert mock_client.get.call_count == 1
        
        # Second call should use cache
        weather2 = await weather_service.get_weather('10001', 'USA')
        assert mock_client.get.call_count == 1  # Still 1, no additional API call
        
        assert weather1.location == weather2.location
        assert weather1.temperature == weather2.temperature
    
    @pytest.mark.asyncio
    async def test_clear_cache(self, weather_service):
        """Test clearing cache."""
        weather = Weather(
            location='New York',
            zip_code='10001',
            country='USA',
            temperature=20.0,
            feels_like=22.0,
            description='clear sky',
            humidity=60,
            wind_speed=5.0
        )
        
        await weather_service._save_to_cache('test_key', weather)
        assert len(weather_service.memory_cache) == 1
        
        await weather_service.clear_cache()
        assert len(weather_service.memory_cache) == 0