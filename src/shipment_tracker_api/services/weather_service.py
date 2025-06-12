"""Weather service for fetching and caching weather data using 2-tier caching with local and redis as fallback."""

import os
import json
import httpx
from datetime import timezone, datetime, timedelta
from typing import Optional


try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from ..models.weather import Weather


class WeatherService:
    """Service for fetching and caching weather data."""
    
    def __init__(self, api_key: str = None, redis_url: str = None):
        """Initialize weather service."""
        self.api_key = api_key if api_key is not None else os.getenv('WEATHER_API_KEY')
        self.base_url = os.getenv('WEATHER_API_BASE_URL', 'https://api.openweathermap.org/data/2.5/weather')
        
        # Initialize Redis cache if available
        self.redis_client = None
        self.redis_url = redis_url
        if REDIS_AVAILABLE and redis_url:
            # We'll create the connection lazily in async context
            pass
        
        # In-memory cache as fallback
        self.memory_cache: dict[str, dict[str, Weather|datetime]] = {}
        self.cache_duration = timedelta(hours=2)
        
        # HTTP client for async requests
        self.http_client = None

    async def _ensure_redis_connection(self) -> None:
        """Ensure Redis connection is established."""
        if REDIS_AVAILABLE and self.redis_url and self.redis_client is None:
            try:
                self.redis_client = redis.from_url(self.redis_url)
                await self.redis_client.ping()
            except Exception:
                self.redis_client = None
    
    async def _get_from_cache(self, cache_key: str) -> Optional[Weather]:
        """Hole Wetterdaten zuerst aus dem lokalen Cache, dann aus Redis."""
        # Zuerst lokalen Cache prüfen
        if cache_key in self.memory_cache:
            cached_entry = self.memory_cache[cache_key]
            if datetime.now(timezone.utc) < cached_entry['expires_at']:
                return cached_entry['weather']
            else:
                # Abgelaufenen Eintrag entfernen
                del self.memory_cache[cache_key]

        # Dann Redis prüfen
        await self._ensure_redis_connection()
        if self.redis_client:
            try:
                cached_data = await self.redis_client.get(cache_key)
                if cached_data:
                    data = json.loads(cached_data)
                    weather = Weather(
                        location=data['location'],
                        zip_code=data['zip_code'],
                        country=data['country'],
                        temperature=data['temperature'],
                        feels_like=data['feels_like'],
                        description=data['description'],
                        humidity=data['humidity'],
                        wind_speed=data['wind_speed'],
                        timestamp=datetime.fromisoformat(data['timestamp'])
                    )
                    # Nach erfolgreichem Redis-Treffer auch in lokalen Cache legen
                    self.memory_cache[cache_key] = {
                        'weather': weather,
                        'expires_at': datetime.now(timezone.utc) + self.cache_duration
                    }
                    return weather
            except Exception:
                pass

        return None
    
    async def _save_to_cache(self, cache_key: str, weather: Weather) -> None:
        """Save weather data to cache."""
        # Save to Redis
        await self._ensure_redis_connection()
        if self.redis_client:
            try:
                weather_data = weather.to_dict()
                await self.redis_client.setex(
                    cache_key,
                    int(self.cache_duration.total_seconds()),
                    json.dumps(weather_data)
                )
            except Exception:
                pass
        
        # Save to memory cache as fallback
        self.memory_cache[cache_key] = {
            'weather': weather,
            'expires_at': datetime.now(timezone.utc) + self.cache_duration
        }
    
    async def get_weather_from_address(self, address: str) -> Optional[Weather]:
        """Get weather data from an address string."""
        # Extract location info from address
        # Expected format: "Street X, ZIP City, Country"
        parts = [part.strip() for part in address.split(',')]
        if len(parts) >= 3:
            # Get the last part as a country
            country = parts[-1]
            # Get the second-to-last part which should contain ZIP and city
            city_part = parts[-2]
            # Try to extract ZIP code (first part that looks like a number)
            zip_parts = city_part.split()
            zip_code = None
            for part in zip_parts:
                if part.replace('-', '').isdigit():
                    zip_code = part
                    break

            if zip_code and country:
                return await self.get_weather(zip_code, country)

        # If parsing fails, return None
        return None

    async def get_weather(self, zip_code: str, country: str) -> Optional[Weather]:
        """Get weather data for a location."""
        if not self.api_key or self.api_key.strip() == "":
            raise ValueError("Weather API key not configured")
        
        cache_key = f"weather:{zip_code}:{country.lower()}"
        
        # Check cache first
        cached_weather = await self._get_from_cache(cache_key)
        if cached_weather:
            return cached_weather
        
        # Ensure HTTP client is available
        if self.http_client is None:
            self.http_client = httpx.AsyncClient(timeout=10.0)
        
        # Fetch from API
        try:
            params = {
                'zip': f"{zip_code},{country}",
                'appid': self.api_key,
                'units': 'metric'
            }
            
            response = await self.http_client.get(self.base_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            weather = Weather(
                location=data['name'],
                zip_code=zip_code,
                country=country,
                temperature=data['main']['temp'],
                feels_like=data['main']['feels_like'],
                description=data['weather'][0]['description'],
                humidity=data['main']['humidity'],
                wind_speed=data['wind']['speed']
            )
            
            # Cache the result
            await self._save_to_cache(cache_key, weather)
            
            return weather
            
        except httpx.RequestError as e:
            raise ValueError(f"Failed to fetch weather data: {str(e)}")
        except KeyError as e:
            raise ValueError(f"Invalid weather API response: missing {str(e)}")
    
    async def clear_cache(self) -> None:
        """Clear all cached weather data."""
        await self._ensure_redis_connection()
        if self.redis_client:
            try:
                # Clear only weather keys
                async for key in self.redis_client.scan_iter("weather:*"):
                    await self.redis_client.delete(key)
            except Exception:
                pass
        
        self.memory_cache.clear()
    
    async def close(self) -> None:
        """Close HTTP and Redis connections."""
        if self.http_client:
            await self.http_client.aclose()
        if self.redis_client:
            await self.redis_client.aclose()