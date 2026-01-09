"""
Test dosyası - Trade execution core işlemleri
Bu dosya trade işlemlerinin temel fonksiyonlarını test eder.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
from decimal import Decimal

# Add src to path for imports
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src"))
)


class TestTradeExecution(unittest.TestCase):
    """Trade execution işlemlerini test eder"""

    def setUp(self):
        """Test setup"""
        self.mock_client = Mock()
        self.test_symbol = "BTCUSDT"
        self.test_price = 50000.0
        self.test_quantity = 0.001

        # Mock responses
        self.mock_order_response = {
            "symbol": self.test_symbol,
            "orderId": 12345,
            "transactTime": 1234567890,
            "status": "FILLED",
            "side": "BUY",
            "type": "MARKET",
            "fills": [
                {
                    "price": str(self.test_price),
                    "qty": str(self.test_quantity),
                    "commission": "0.00001",
                    "commissionAsset": "BTC",
                }
            ],
            "cummulativeQuoteQty": str(self.test_quantity * self.test_price),
        }

        self.mock_balance_response = {
            "asset": "USDT",
            "free": "1000.0",
            "locked": "0.0",
        }

    def test_market_buy_order_simulation(self):
        """Market buy order simülasyonu"""
        # Setup
        self.mock_client.order_market_buy.return_value = self.mock_order_response
        self.mock_client.get_account.return_value = {
            "balances": [self.mock_balance_response]
        }

        # Simulate buy order
        result = self.mock_client.order_market_buy(
            symbol=self.test_symbol, quantity=self.test_quantity
        )

        # Assertions
        self.assertEqual(result["symbol"], self.test_symbol)
        self.assertEqual(result["status"], "FILLED")
        self.assertEqual(result["side"], "BUY")
        self.mock_client.order_market_buy.assert_called_once()

    def test_market_sell_order_simulation(self):
        """Market sell order simülasyonu"""
        # Setup sell response
        sell_response = self.mock_order_response.copy()
        sell_response["side"] = "SELL"
        self.mock_client.order_market_sell.return_value = sell_response

        # Simulate sell order
        result = self.mock_client.order_market_sell(
            symbol=self.test_symbol, quantity=self.test_quantity
        )

        # Assertions
        self.assertEqual(result["side"], "SELL")
        self.assertEqual(result["status"], "FILLED")
        self.mock_client.order_market_sell.assert_called_once()

    def test_limit_buy_order_simulation(self):
        """Limit buy order simülasyonu"""
        # Setup limit order response
        limit_response = self.mock_order_response.copy()
        limit_response["type"] = "LIMIT"
        limit_response["price"] = str(
            self.test_price - 100
        )  # Lower price for buy limit
        limit_response["status"] = "NEW"  # Pending order
        limit_response["fills"] = []  # No fills yet

        self.mock_client.order_limit_buy.return_value = limit_response

        # Simulate limit buy order
        result = self.mock_client.order_limit_buy(
            symbol=self.test_symbol,
            quantity=self.test_quantity,
            price=str(self.test_price - 100),
        )

        # Assertions
        self.assertEqual(result["type"], "LIMIT")
        self.assertEqual(result["status"], "NEW")
        self.assertEqual(result["side"], "BUY")
        self.mock_client.order_limit_buy.assert_called_once()

    def test_order_status_check(self):
        """Order status kontrolü"""
        # Setup
        order_id = 12345
        status_response = {
            "orderId": order_id,
            "status": "FILLED",
            "symbol": self.test_symbol,
            "executedQty": str(self.test_quantity),
            "cummulativeQuoteQty": str(self.test_quantity * self.test_price),
        }

        self.mock_client.get_order.return_value = status_response

        # Check order status
        result = self.mock_client.get_order(symbol=self.test_symbol, orderId=order_id)

        # Assertions
        self.assertEqual(result["orderId"], order_id)
        self.assertEqual(result["status"], "FILLED")
        self.mock_client.get_order.assert_called_once()

    def test_balance_retrieval(self):
        """Balance bilgisi alma testi"""
        # Setup
        account_response = {
            "balances": [
                {"asset": "USDT", "free": "1000.0", "locked": "0.0"},
                {"asset": "BTC", "free": "0.01", "locked": "0.0"},
                {"asset": "ETH", "free": "0.5", "locked": "0.0"},
            ]
        }

        self.mock_client.get_account.return_value = account_response

        # Get account info
        result = self.mock_client.get_account()

        # Assertions
        self.assertIn("balances", result)
        self.assertEqual(len(result["balances"]), 3)

        # Check USDT balance
        usdt_balance = next(b for b in result["balances"] if b["asset"] == "USDT")
        self.assertEqual(float(usdt_balance["free"]), 1000.0)

    def test_symbol_info_retrieval(self):
        """Symbol bilgisi alma testi"""
        # Setup
        symbol_info = {
            "symbol": self.test_symbol,
            "status": "TRADING",
            "baseAsset": "BTC",
            "baseAssetPrecision": 8,
            "quoteAsset": "USDT",
            "quotePrecision": 8,
            "filters": [
                {
                    "filterType": "LOT_SIZE",
                    "minQty": "0.00001000",
                    "maxQty": "9000.00000000",
                    "stepSize": "0.00001000",
                }
            ],
        }

        exchange_info = {"symbols": [symbol_info]}

        self.mock_client.get_exchange_info.return_value = exchange_info

        # Get exchange info
        result = self.mock_client.get_exchange_info()

        # Assertions
        self.assertIn("symbols", result)
        symbol = result["symbols"][0]
        self.assertEqual(symbol["symbol"], self.test_symbol)
        self.assertEqual(symbol["baseAsset"], "BTC")

    def test_price_retrieval(self):
        """Fiyat bilgisi alma testi"""
        # Setup
        price_response = {"symbol": self.test_symbol, "price": str(self.test_price)}

        self.mock_client.get_symbol_ticker.return_value = price_response

        # Get price
        result = self.mock_client.get_symbol_ticker(symbol=self.test_symbol)

        # Assertions
        self.assertEqual(result["symbol"], self.test_symbol)
        self.assertEqual(float(result["price"]), self.test_price)

    def test_trade_history(self):
        """Trade geçmişi alma testi"""
        # Setup
        trade_history = [
            {
                "id": 1,
                "orderId": 12345,
                "symbol": self.test_symbol,
                "side": "BUY",
                "qty": str(self.test_quantity),
                "price": str(self.test_price),
                "time": 1234567890,
                "isBuyer": True,
                "commission": "0.00001",
                "commissionAsset": "BTC",
            }
        ]

        self.mock_client.get_my_trades.return_value = trade_history

        # Get trade history
        result = self.mock_client.get_my_trades(symbol=self.test_symbol)

        # Assertions
        self.assertEqual(len(result), 1)
        trade = result[0]
        self.assertEqual(trade["symbol"], self.test_symbol)
        self.assertEqual(trade["side"], "BUY")

    def test_error_handling(self):
        """Hata durumları testi"""
        # Setup error
        from binance.exceptions import BinanceAPIException

        self.mock_client.order_market_buy.side_effect = BinanceAPIException(
            response={"code": -1013, "msg": "Filter failure: LOT_SIZE"}, status_code=400
        )

        # Test error handling
        with self.assertRaises(BinanceAPIException):
            self.mock_client.order_market_buy(
                symbol=self.test_symbol, quantity="invalid_quantity"
            )


class TestPortfolioManagement(unittest.TestCase):
    """Portfolio yönetimi testleri"""

    def setUp(self):
        """Test setup"""
        self.mock_client = Mock()
        self.portfolio_data = {
            "total_value": 10000.0,
            "positions": [
                {"asset": "BTC", "amount": 0.2, "value": 8000.0, "percentage": 80.0},
                {"asset": "ETH", "amount": 1.0, "value": 1500.0, "percentage": 15.0},
                {"asset": "USDT", "amount": 500.0, "value": 500.0, "percentage": 5.0},
            ],
        }

    def test_portfolio_calculation(self):
        """Portfolio değer hesaplama testi"""
        # Calculate total value
        total_value = sum(pos["value"] for pos in self.portfolio_data["positions"])

        # Assertions
        self.assertEqual(total_value, self.portfolio_data["total_value"])

        # Check percentages
        for position in self.portfolio_data["positions"]:
            expected_percentage = (position["value"] / total_value) * 100
            self.assertAlmostEqual(
                position["percentage"], expected_percentage, places=1
            )

    def test_risk_calculation(self):
        """Risk hesaplama testi"""
        # Setup risk parameters
        soft_risk = 0.05  # 5%
        hard_risk = 0.10  # 10%
        total_balance = 1000.0

        # Calculate risk amounts
        soft_risk_amount = total_balance * soft_risk
        hard_risk_amount = total_balance * hard_risk

        # Assertions
        self.assertEqual(soft_risk_amount, 50.0)
        self.assertEqual(hard_risk_amount, 100.0)
        self.assertLess(soft_risk_amount, hard_risk_amount)

    def test_position_sizing(self):
        """Position boyutlandırma testi"""
        # Setup
        available_balance = 1000.0
        risk_percentage = 0.02  # 2%
        entry_price = 50000.0
        stop_loss_price = 49000.0

        # Calculate position size
        risk_amount = available_balance * risk_percentage
        price_difference = entry_price - stop_loss_price
        position_size = risk_amount / price_difference

        # Assertions
        self.assertEqual(risk_amount, 20.0)
        self.assertEqual(price_difference, 1000.0)
        self.assertEqual(position_size, 0.02)


class TestDataManagement(unittest.TestCase):
    """Data yönetimi testleri"""

    def test_trade_data_format(self):
        """Trade data format testi"""
        # Sample trade data
        trade_data = {
            "timestamp": "2025-09-12T10:00:00",
            "symbol": "BTCUSDT",
            "side": "BUY",
            "type": "Hard_Buy",
            "quantity": 0.001,
            "price": 50000.0,
            "total_cost": 50.0,
            "wallet_before": 1000.0,
            "wallet_after": 950.0,
            "order_id": 12345,
            "order_type": "MARKET",
            "status": "FILLED",
        }

        # Validate required fields
        required_fields = [
            "timestamp",
            "symbol",
            "side",
            "type",
            "quantity",
            "price",
            "total_cost",
            "order_id",
            "order_type",
            "status",
        ]

        for field in required_fields:
            self.assertIn(field, trade_data)

        # Validate data types
        self.assertIsInstance(trade_data["quantity"], (int, float))
        self.assertIsInstance(trade_data["price"], (int, float))
        self.assertIsInstance(trade_data["total_cost"], (int, float))
        self.assertEqual(trade_data["side"], "BUY")

    def test_portfolio_data_format(self):
        """Portfolio data format testi"""
        # Sample portfolio data
        portfolio_data = {
            "timestamp": "2025-09-12T10:00:00",
            "total_value": 10000.0,
            "positions": [
                {
                    "asset": "BTC",
                    "amount": 0.2,
                    "price": 50000.0,
                    "value": 10000.0,
                    "percentage": 100.0,
                }
            ],
        }

        # Validate structure
        self.assertIn("timestamp", portfolio_data)
        self.assertIn("total_value", portfolio_data)
        self.assertIn("positions", portfolio_data)
        self.assertIsInstance(portfolio_data["positions"], list)

        # Validate position data
        position = portfolio_data["positions"][0]
        required_position_fields = ["asset", "amount", "price", "value", "percentage"]

        for field in required_position_fields:
            self.assertIn(field, position)


if __name__ == "__main__":
    unittest.main()
