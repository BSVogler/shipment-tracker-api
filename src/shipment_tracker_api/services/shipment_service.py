"""Shipment service for managing shipment data."""

import pandas as pd
from typing import Dict, List, Optional
from pathlib import Path

from ..models.shipment import Shipment, Article, Address


class ShipmentService:
    """Service for managing shipment data."""
    
    def __init__(self, csv_file_path: str = None):
        """Initialize shipment service with data from CSV."""
        self.shipments: dict[str, Shipment] = {}
        if csv_file_path:
            self.load_data_from_csv(csv_file_path)
    
    def load_data_from_csv(self, csv_file_path: str) -> None:
        """Load shipment data from CSV file."""
        try:
            df = pd.read_csv(csv_file_path)
            
            # Group by tracking_number to handle multiple articles per shipment
            grouped = df.groupby('tracking_number')
            
            for tracking_number, group in grouped:
                articles = []
                
                for _, row in group.iterrows():
                    # Create article
                    article = Article(
                        name=row['article_name'],
                        quantity=int(row['article_quantity']),
                        price=int(row['article_price']*100),#convert to cents
                        sku=row.get('SKU')
                    )
                    articles.append(article)
                
                # Use first row for shipment-level data
                first_row = group.iloc[0]
                
                # Create sender and receiver addresses as simple strings
                sender = Address(
                    address=first_row['sender_address']
                )
                
                receiver = Address(
                    address=first_row['receiver_address']
                )
                
                # Create shipment
                shipment = Shipment(
                    tracking_number=tracking_number,
                    carrier=first_row['carrier'],
                    articles=articles,
                    sender=sender,
                    receiver=receiver,
                    status=first_row['status']
                )
                
                # Store shipment with tracking_number as key
                self.shipments[tracking_number] = shipment
                
        except Exception as e:
            raise ValueError(f"Error loading CSV data: {str(e)}")

    def get_shipment(self, tracking_number: str, carrier: str = None) -> Optional[Shipment]:
        """Get shipment by tracking number and optionally carrier."""
        shipment = self.shipments.get(tracking_number)

        if shipment and carrier:
            # If a carrier is specified, check if it matches
            if shipment.carrier.lower() != carrier.lower():
                return None
                
        return shipment
    
    def get_all_shipments(self, carrier: Optional[str] = None) -> list[Shipment]:
        """Get all shipments."""
        if carrier:
            return [
                shipment for shipment in self.shipments.values()
                if shipment.carrier.lower() == carrier.lower()
            ]
        return list(self.shipments.values())
