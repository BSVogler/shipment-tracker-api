"""Weather data models."""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


@dataclass
class Weather:
    """Weather information."""
    location: str
    zip_code: str
    country: str
    temperature: float
    feels_like: float
    description: str
    humidity: int
    wind_speed: float
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)
    
    def to_dict(self):
        """Convert weather to dictionary."""
        return {
            "location": self.location,
            "zip_code": self.zip_code,
            "country": self.country,
            "temperature": self.temperature,
            "feels_like": self.feels_like,
            "description": self.description,
            "humidity": self.humidity,
            "wind_speed": self.wind_speed,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class WeatherCache:
    """Weather cache entry."""
    key: str
    weather: Weather
    expires_at: datetime