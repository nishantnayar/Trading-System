"""
Unit tests for Web API endpoints
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from src.web.api.timezone_helpers import (
    format_api_timestamp,
    get_current_time_info,
    get_market_status_info,
)
from src.web.main import app


class TestWebAPI:
    """Test cases for Web API endpoints"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200

    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert "status" in response.json()

    @patch("src.web.api.alpaca_routes.get_alpaca_client")
    def test_alpaca_account_endpoint(self, mock_get_client, client):
        """Test Alpaca account endpoint"""
        mock_client = Mock()
        mock_account = Mock()
        mock_account.id = "test_account"
        mock_account.status = "ACTIVE"
        mock_account.buying_power = 10000.0
        mock_client.get_account.return_value = mock_account
        mock_get_client.return_value = mock_client

        response = client.get("/api/alpaca/account")
        assert response.status_code == 200
        data = response.json()
        assert "account" in data

    @patch("src.web.api.alpaca_routes.get_alpaca_client")
    def test_alpaca_positions_endpoint(self, mock_get_client, client):
        """Test Alpaca positions endpoint"""
        mock_client = Mock()
        mock_position = Mock()
        mock_position.symbol = "AAPL"
        mock_position.qty = 100
        mock_position.market_value = 15000.0
        mock_client.list_positions.return_value = [mock_position]
        mock_get_client.return_value = mock_client

        response = client.get("/api/alpaca/positions")
        assert response.status_code == 200
        data = response.json()
        assert "positions" in data

    @patch("src.web.api.alpaca_routes.get_alpaca_client")
    def test_alpaca_orders_endpoint(self, mock_get_client, client):
        """Test Alpaca orders endpoint"""
        mock_client = Mock()
        mock_order = Mock()
        mock_order.id = "order_123"
        mock_order.symbol = "AAPL"
        mock_order.side = "buy"
        mock_order.qty = 100
        mock_order.status = "filled"
        mock_client.list_orders.return_value = [mock_order]
        mock_get_client.return_value = mock_client

        response = client.get("/api/alpaca/orders")
        assert response.status_code == 200
        data = response.json()
        assert "orders" in data

    @patch("src.web.api.alpaca_routes.get_alpaca_client")
    def test_alpaca_place_order_endpoint(self, mock_get_client, client):
        """Test Alpaca place order endpoint"""
        mock_client = Mock()
        mock_order = Mock()
        mock_order.id = "order_123"
        mock_order.symbol = "AAPL"
        mock_order.side = "buy"
        mock_order.qty = 100
        mock_order.status = "new"
        mock_client.submit_order.return_value = mock_order
        mock_get_client.return_value = mock_client

        order_data = {
            "symbol": "AAPL",
            "side": "buy",
            "qty": 100,
            "type": "market",
            "time_in_force": "day",
        }

        response = client.post("/api/alpaca/orders", json=order_data)
        assert response.status_code == 200
        data = response.json()
        assert "order" in data

    def test_alpaca_place_order_invalid_data(self, client):
        """Test Alpaca place order with invalid data"""
        invalid_order_data = {
            "symbol": "",  # Invalid empty symbol
            "side": "buy",
            "qty": 0,  # Invalid zero quantity
        }

        response = client.post("/api/alpaca/orders", json=invalid_order_data)
        assert response.status_code == 422  # Validation error

    @patch("src.web.api.alpaca_routes.get_alpaca_client")
    def test_alpaca_cancel_order_endpoint(self, mock_get_client, client):
        """Test Alpaca cancel order endpoint"""
        mock_client = Mock()
        mock_client.cancel_order.return_value = None
        mock_get_client.return_value = mock_client

        response = client.delete("/api/alpaca/orders/order_123")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    @patch("src.web.api.alpaca_routes.get_alpaca_client")
    def test_alpaca_get_order_endpoint(self, mock_get_client, client):
        """Test Alpaca get order endpoint"""
        mock_client = Mock()
        mock_order = Mock()
        mock_order.id = "order_123"
        mock_order.symbol = "AAPL"
        mock_order.side = "buy"
        mock_order.qty = 100
        mock_order.status = "filled"
        mock_client.get_order.return_value = mock_order
        mock_get_client.return_value = mock_client

        response = client.get("/api/alpaca/orders/order_123")
        assert response.status_code == 200
        data = response.json()
        assert "order" in data

    @patch("src.web.api.alpaca_routes.get_alpaca_client")
    def test_alpaca_get_order_not_found(self, mock_get_client, client):
        """Test Alpaca get order when order not found"""
        mock_client = Mock()
        mock_client.get_order.side_effect = Exception("Order not found")
        mock_get_client.return_value = mock_client

        response = client.get("/api/alpaca/orders/nonexistent")
        assert response.status_code == 404

    @patch("src.web.api.alpaca_routes.get_alpaca_client")
    def test_alpaca_place_order_error(self, mock_get_client, client):
        """Test Alpaca place order with error"""
        mock_client = Mock()
        mock_client.submit_order.side_effect = Exception("Insufficient buying power")
        mock_get_client.return_value = mock_client

        order_data = {
            "symbol": "AAPL",
            "side": "buy",
            "qty": 10000,  # Large quantity that might exceed buying power
            "type": "market",
            "time_in_force": "day",
        }

        response = client.post("/api/alpaca/orders", json=order_data)
        assert response.status_code == 500

    def test_dashboard_endpoint(self, client):
        """Test dashboard endpoint"""
        response = client.get("/dashboard")
        assert response.status_code == 200

    def test_trading_endpoint(self, client):
        """Test trading endpoint"""
        response = client.get("/trading")
        assert response.status_code == 200

    def test_analytics_endpoint(self, client):
        """Test analytics endpoint"""
        response = client.get("/analytics")
        assert response.status_code == 200

    def test_settings_endpoint(self, client):
        """Test settings endpoint"""
        response = client.get("/settings")
        assert response.status_code == 200


class TestTimezoneHelpers:
    """Test cases for timezone helper functions"""

    @patch("src.web.api.timezone_helpers.datetime")
    def test_get_current_time_info(self, mock_datetime):
        """Test get current time info function"""
        mock_now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        mock_datetime.now.return_value = mock_now

        result = get_current_time_info()

        assert "utc" in result
        assert "central" in result
        assert "eastern" in result

    def test_format_api_timestamp(self):
        """Test API timestamp formatting"""
        test_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        result = format_api_timestamp(test_time)

        assert isinstance(result, str)
        assert "2024-01-01" in result

    def test_get_market_status_info(self):
        """Test market status info function"""
        result = get_market_status_info()

        assert "is_open" in result
        assert "next_open" in result
        assert "next_close" in result

    @patch("src.web.api.timezone_helpers.is_market_hours")
    def test_get_market_status_info_with_market_status(self, mock_is_market_hours):
        """Test market status info with market hours"""
        mock_is_market_hours.return_value = True

        result = get_market_status_info()

        assert result["is_open"] is True
        mock_is_market_hours.assert_called_once()

    def test_timezone_conversion_edge_cases(self):
        """Test timezone conversion edge cases"""
        # Test with None input
        result = format_api_timestamp(None)
        assert result is None

        # Test with naive datetime
        naive_time = datetime(2024, 1, 1, 12, 0, 0)
        result = format_api_timestamp(naive_time)
        # Should handle gracefully or convert to UTC
        assert result is not None

    def test_timezone_display_formatting(self):
        """Test timezone display formatting"""
        test_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        result = format_api_timestamp(test_time)

        # Check that timestamp is properly formatted
        assert isinstance(result, str)
        assert "2024-01-01T12:00:00" in result

    @patch("src.web.api.timezone_helpers.get_market_status")
    def test_market_status_integration(self, mock_get_market_status):
        """Test market status integration"""
        mock_status = {
            "is_open": True,
            "next_open": "2024-01-02T09:30:00Z",
            "next_close": "2024-01-01T16:00:00Z",
        }
        mock_get_market_status.return_value = mock_status

        result = get_market_status_info()

        assert result["is_open"] is True
        assert "next_open" in result
        assert "next_close" in result


class TestWebAPIErrorHandling:
    """Test error handling in Web API"""

    def test_404_endpoint(self, client):
        """Test 404 for non-existent endpoint"""
        response = client.get("/nonexistent")
        assert response.status_code == 404

    def test_method_not_allowed(self, client):
        """Test method not allowed"""
        response = client.put("/health")  # PUT not allowed on health endpoint
        assert response.status_code == 405

    @patch("src.web.api.alpaca_routes.get_alpaca_client")
    def test_alpaca_connection_error(self, mock_get_client, client):
        """Test Alpaca connection error handling"""
        mock_get_client.side_effect = Exception("Connection failed")

        response = client.get("/api/alpaca/account")
        assert response.status_code == 500

    def test_invalid_json_request(self, client):
        """Test invalid JSON request"""
        response = client.post(
            "/api/alpaca/orders",
            data="invalid json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422

    def test_missing_required_fields(self, client):
        """Test missing required fields in request"""
        incomplete_order = {
            "symbol": "AAPL"
            # Missing required fields: side, qty, type, time_in_force
        }

        response = client.post("/api/alpaca/orders", json=incomplete_order)
        assert response.status_code == 422

    def test_invalid_field_types(self, client):
        """Test invalid field types in request"""
        invalid_order = {
            "symbol": "AAPL",
            "side": "buy",
            "qty": "invalid",  # Should be number
            "type": "market",
            "time_in_force": "day",
        }

        response = client.post("/api/alpaca/orders", json=invalid_order)
        assert response.status_code == 422

    @patch("src.web.api.alpaca_routes.get_alpaca_client")
    def test_alpaca_rate_limit_error(self, mock_get_client, client):
        """Test Alpaca rate limit error handling"""
        mock_client = Mock()
        mock_client.get_account.side_effect = Exception("Rate limit exceeded")
        mock_get_client.return_value = mock_client

        response = client.get("/api/alpaca/account")
        assert response.status_code == 500

    def test_large_request_body(self, client):
        """Test handling of large request body"""
        large_order = {
            "symbol": "AAPL",
            "side": "buy",
            "qty": 999999999,  # Very large quantity
            "type": "market",
            "time_in_force": "day",
        }

        response = client.post("/api/alpaca/orders", json=large_order)
        # Should either succeed (if valid) or fail with validation error
        assert response.status_code in [200, 422, 500]
