import unittest
from unittest.mock import Mock, patch, MagicMock
import pytest
import sys
import os

# Add src to path for imports
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src"))
)

try:
    from services.orders.order_service import place_order, execute_order, make_order
    from services.client_service import prepare_client
    from config.preferences_manager import get_buy_preferences
    from models.order_types import OrderSide, OrderType
except ImportError as e:
    print(f"Import warning: {e}")


class TestOrderService(unittest.TestCase):
    def setUp(self):
        """Test setup - her test öncesi çalışır"""
        self.mock_client = Mock()
        self.test_symbol = "BTCUSDT"
        self.test_quantity = 0.001
        self.test_price = 50000.0

        # Mock order response
        self.mock_order_response = {
            "symbol": self.test_symbol,
            "orderId": 12345,
            "transactTime": 1234567890,
            "status": "FILLED",
            "fills": [{"price": str(self.test_price), "qty": str(self.test_quantity)}],
            "cummulativeQuoteQty": str(self.test_quantity * self.test_price),
        }

    @patch("services.orders.order_service.retrieve_usdt_balance")
    @patch("services.orders.order_service.get_price")
    @patch("services.orders.order_service.get_symbol_info")
    @patch("services.orders.order_service.calculate_buy_quantity")
    @patch("services.orders.order_service.data_manager")
    def test_place_buy_order(
        self,
        mock_data_manager,
        mock_calc_qty,
        mock_symbol_info,
        mock_get_price,
        mock_balance,
    ):
        """Test BUY order placement"""
        # Setup mocks
        mock_balance.return_value = 1000.0
        mock_get_price.return_value = self.test_price
        mock_symbol_info.return_value = {"baseAssetPrecision": 8}
        mock_calc_qty.return_value = self.test_quantity
        self.mock_client.order_market_buy.return_value = self.mock_order_response

        # Execute test
        result = place_order(self.mock_client, self.test_symbol, OrderSide.BUY, 0.1)

        # Assertions
        self.assertEqual(result["orderId"], 12345)
        self.mock_client.order_market_buy.assert_called_once()
        mock_data_manager.save_trade.assert_called_once()

    @patch("services.orders.order_service.get_amountOf_asset")
    @patch("services.orders.order_service.get_price")
    @patch("services.orders.order_service.get_symbol_info")
    @patch("services.orders.order_service.calculate_sell_quantity")
    @patch("services.orders.order_service.data_manager")
    def test_place_sell_order(
        self,
        mock_data_manager,
        mock_calc_qty,
        mock_symbol_info,
        mock_get_price,
        mock_asset,
    ):
        """Test SELL order placement"""
        # Setup mocks
        mock_asset.return_value = 0.01
        mock_get_price.return_value = self.test_price
        mock_symbol_info.return_value = {"baseAssetPrecision": 8}
        mock_calc_qty.return_value = self.test_quantity
        self.mock_client.order_market_sell.return_value = self.mock_order_response

        # Execute test
        result = place_order(self.mock_client, self.test_symbol, OrderSide.SELL, 0.5)

        # Assertions
        self.assertEqual(result["orderId"], 12345)
        self.mock_client.order_market_sell.assert_called_once()
        mock_data_manager.save_trade.assert_called_once()

    @patch("services.orders.order_service.prepare_client")
    @patch("services.orders.order_service.get_buy_preferences")
    @patch("services.orders.order_service.get_effective_order_type")
    @patch("services.orders.order_service.OrderManager")
    def test_execute_order(
        self, mock_order_manager, mock_order_type, mock_preferences, mock_client
    ):
        """Test order execution"""
        # Setup mocks
        mock_client.return_value = self.mock_client
        mock_preferences.return_value = {"soft_risk": 0.05, "hard_risk": 0.10}
        mock_order_type.return_value = "MARKET"
        mock_manager_instance = Mock()
        mock_manager_instance.validate_execution_type.return_value = True
        mock_manager_instance.execute_order.return_value = self.mock_order_response
        mock_order_manager.return_value = mock_manager_instance

        # Execute test
        result = execute_order("Hard_Buy", self.test_symbol)

        # Assertions
        self.assertEqual(result["orderId"], 12345)
        mock_manager_instance.execute_order.assert_called_once_with(
            "Hard_Buy", self.test_symbol, "MARKET", None
        )

    @patch("services.orders.order_service.prepare_client")
    @patch("services.orders.order_service.execute_order")
    @patch("services.orders.order_service.retrieve_usdt_balance")
    @patch("services.orders.order_service.data_manager")
    def test_make_order(
        self, mock_data_manager, mock_balance, mock_execute, mock_client
    ):
        """Test complete order making process"""
        # Setup mocks
        mock_client.return_value = self.mock_client
        mock_balance.side_effect = [1000.0, 950.0]  # Before and after balance
        mock_execute.return_value = self.mock_order_response

        # Execute test
        result = make_order("Hard_Buy", self.test_symbol, order_type="MARKET")

        # Assertions
        self.assertEqual(result["orderId"], 12345)
        mock_execute.assert_called_once()
        mock_data_manager.save_trade.assert_called_once()

    def test_invalid_order_side(self):
        """Test invalid order side handling"""
        with self.assertRaises(ValueError):
            place_order(self.mock_client, self.test_symbol, "INVALID_SIDE", 0.1)

    @patch("services.client_service.load_dotenv")
    @patch("services.client_service.Client")
    @patch("os.getenv")
    def test_prepare_client(self, mock_getenv, mock_client_class, mock_load_dotenv):
        """Test client preparation"""
        # Setup mocks
        mock_getenv.side_effect = lambda key: {
            "BINANCE_API_KEY": "test_api_key",
            "BINANCE_SECRET_KEY": "test_secret_key",
        }.get(key)
        mock_client_instance = Mock()
        mock_client_class.return_value = mock_client_instance

        # Execute test
        client = prepare_client()

        # Assertions
        self.assertIsNotNone(client)
        mock_load_dotenv.assert_called_once()
        mock_client_class.assert_called_once()


if __name__ == "__main__":
    unittest.main()
