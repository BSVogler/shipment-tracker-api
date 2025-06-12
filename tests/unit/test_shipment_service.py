"""Unit tests for ShipmentService."""

import pytest
from pathlib import Path
from src.shipment_tracker_api.services.shipment_service import ShipmentService


class TestShipmentService:
    """Test cases for ShipmentService."""
    
    @pytest.fixture
    def test_csv_path(self):
        """Path to test CSV file with new format."""
        return str(Path(__file__).parent.parent.parent / "data"/"sample_data.csv")
    
    @pytest.fixture
    def service_with_test_data(self, test_csv_path):
        """Create ShipmentService with test data."""
        return ShipmentService(test_csv_path)
    
    def test_load_data_from_csv(self, service_with_test_data):
        """Test loading shipment data from CSV."""
        service = service_with_test_data
        
        assert len(service.shipments) == 5  # 5 unique tracking numbers
        assert 'TN12345678' in service.shipments
        assert 'TN12345679' in service.shipments
        assert 'TN12345680' in service.shipments
        assert 'TN12345681' in service.shipments
        assert 'TN12345682' in service.shipments
    
    def test_get_shipment_by_tracking_number(self, service_with_test_data):
        """Test getting shipment by tracking number."""
        shipment = service_with_test_data.get_shipment('TN12345678')
        
        assert shipment is not None
        assert shipment.tracking_number == 'TN12345678'
        assert shipment.carrier == 'DHL'
        assert shipment.status == 'in-transit'
        assert len(shipment.articles) == 2  # Laptop and Mouse
    
    def test_get_shipment_by_tracking_number_with_carrier(self, service_with_test_data):
        """Test getting shipment by tracking number with carrier filter."""
        # Correct carrier
        shipment = service_with_test_data.get_shipment('TN12345678', 'DHL')
        assert shipment is not None
        
        # Wrong carrier
        shipment = service_with_test_data.get_shipment('TN12345678', 'UPS')
        assert shipment is None
    
    def test_get_shipment_not_found(self, service_with_test_data):
        """Test getting non-existent shipment."""
        shipment = service_with_test_data.get_shipment('TN99999999')
        assert shipment is None
    
    def test_get_all_shipments(self, service_with_test_data):
        """Test getting all shipments."""
        shipments = service_with_test_data.get_all_shipments()
        assert len(shipments) == 5
    
    def test_get_shipments_by_carrier(self, service_with_test_data):
        """Test getting shipments by carrier."""
        dhl_shipments = service_with_test_data.get_all_shipments(carrier='DHL')
        assert len(dhl_shipments) == 1
        assert dhl_shipments[0].tracking_number == 'TN12345678'
        
        ups_shipments = service_with_test_data.get_all_shipments(carrier='UPS')
        assert len(ups_shipments) == 1
        assert ups_shipments[0].tracking_number == 'TN12345679'
        
        fedex_shipments = service_with_test_data.get_all_shipments(carrier='FedEx')
        assert len(fedex_shipments) == 1
        assert fedex_shipments[0].tracking_number == 'TN12345681'
    
    def test_shipment_to_dict(self, service_with_test_data):
        """Test converting shipment to dictionary."""
        shipment = service_with_test_data.get_shipment('TN12345678')
        shipment_dict = shipment.to_dict()
        
        assert shipment_dict['tracking_number'] == 'TN12345678'
        assert shipment_dict['carrier'] == 'DHL'
        assert shipment_dict['status'] == 'in-transit'
        assert len(shipment_dict['articles']) == 2
        
        # Check articles
        article_names = [a['name'] for a in shipment_dict['articles']]
        assert 'Laptop' in article_names
        assert 'Mouse' in article_names
        
        # Check addresses
        assert 'Berlin' in shipment_dict['sender']['address']
        assert 'Paris' in shipment_dict['receiver']['address']