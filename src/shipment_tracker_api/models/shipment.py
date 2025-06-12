"""Shipment data models."""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, timezone


@dataclass
class Address:
    """Address information."""
    address: str  # Full address as a single string


@dataclass
class Article:
    """Article/Product information."""
    name: str
    quantity: int
    price: int #to avoid rounding errors use integer in cents
    sku: Optional[str] = None

def utc_now() -> datetime:
  return datetime.now(timezone.utc)


@dataclass
class Shipment:
    """Shipment information."""
    tracking_number: str
    carrier: str
    articles: list[Article]
    sender: Address
    receiver: Address
    status: str
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    
    def to_dict(self):
        """Convert shipment to dictionary."""
        return {
            "tracking_number": self.tracking_number,
            "carrier": self.carrier,
            "articles": [
                {
                    "name": article.name,
                    "quantity": article.quantity,
                    "price": article.price,
                    "sku": article.sku
                }
                for article in self.articles
            ],
            "sender": {
                "address": self.sender.address
            },
            "receiver": {
                "address": self.receiver.address
            },
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }