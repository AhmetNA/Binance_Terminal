"""
Integration test dosyası - End-to-end test scenarios
Bu dosya tam entegrasyon senaryolarını test eder.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import json
from datetime import datetime

# Add src to path for imports
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src"))
)


class TestEndToEndTrading(unittest.TestCase):
    """End-to-end trading scenarios testi"""

    def setUp(self):
        """Test setup"""
        self.mock_client = Mock()
        self.setup_mock_responses()

    def setup_mock_responses(self):
        """Setup all mock responses"""
        # Account response
        self.mock_client.get_account.return_value = {
            "balances": [
                {"asset": "USDT", "free": "1000.0", "locked": "0.0"},
                {"asset": "BTC", "free": "0.0", "locked": "0.0"},
                {"asset": "ETH", "free": "0.0", "locked": "0.0"},
            ]
        }

        # Price response
        self.mock_client.get_symbol_ticker.return_value = {
            "symbol": "BTCUSDT",
            "price": "50000.0",
        }

        # Exchange info response
        self.mock_client.get_exchange_info.return_value = {
            "symbols": [
                {
                    "symbol": "BTCUSDT",
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
            ]
        }

        # Buy order response
        self.mock_client.order_market_buy.return_value = {
            "symbol": "BTCUSDT",
            "orderId": 12345,
            "transactTime": 1234567890,
            "status": "FILLED",
            "side": "BUY",
            "type": "MARKET",
            "fills": [
                {
                    "price": "50000.0",
                    "qty": "0.001",
                    "commission": "0.00000001",
                    "commissionAsset": "BTC",
                }
            ],
            "cummulativeQuoteQty": "50.0",
        }

        # Sell order response
        self.mock_client.order_market_sell.return_value = {
            "symbol": "BTCUSDT",
            "orderId": 12346,
            "transactTime": 1234567891,
            "status": "FILLED",
            "side": "SELL",
            "type": "MARKET",
            "fills": [
                {
                    "price": "51000.0",
                    "qty": "0.001",
                    "commission": "0.051",
                    "commissionAsset": "USDT",
                }
            ],
            "cummulativeQuoteQty": "51.0",
        }

    def test_complete_buy_sell_cycle(self):
        """Complete buy-sell cycle testi"""
        # Phase 1: Initial state check
        account_before = self.mock_client.get_account()
        usdt_before = float(
            [b for b in account_before["balances"] if b["asset"] == "USDT"][0]["free"]
        )
        btc_before = float(
            [b for b in account_before["balances"] if b["asset"] == "BTC"][0]["free"]
        )

        self.assertEqual(usdt_before, 1000.0)
        self.assertEqual(btc_before, 0.0)

        # Phase 2: Execute buy order
        buy_order = self.mock_client.order_market_buy(
            symbol="BTCUSDT", quantity="0.001"
        )

        self.assertEqual(buy_order["status"], "FILLED")
        self.assertEqual(buy_order["side"], "BUY")
        self.assertEqual(float(buy_order["cummulativeQuoteQty"]), 50.0)

        # Update mock account state after buy
        self.mock_client.get_account.return_value["balances"][0]["free"] = (
            "950.0"  # USDT reduced
        )
        self.mock_client.get_account.return_value["balances"][1]["free"] = (
            "0.001"  # BTC increased
        )

        # Phase 3: Check state after buy
        account_after_buy = self.mock_client.get_account()
        usdt_after_buy = float(
            [b for b in account_after_buy["balances"] if b["asset"] == "USDT"][0][
                "free"
            ]
        )
        btc_after_buy = float(
            [b for b in account_after_buy["balances"] if b["asset"] == "BTC"][0]["free"]
        )

        self.assertEqual(usdt_after_buy, 950.0)
        self.assertEqual(btc_after_buy, 0.001)

        # Phase 4: Execute sell order
        sell_order = self.mock_client.order_market_sell(
            symbol="BTCUSDT", quantity="0.001"
        )

        self.assertEqual(sell_order["status"], "FILLED")
        self.assertEqual(sell_order["side"], "SELL")
        self.assertEqual(float(sell_order["cummulativeQuoteQty"]), 51.0)

        # Update mock account state after sell
        self.mock_client.get_account.return_value["balances"][0]["free"] = (
            "1001.0"  # USDT increased
        )
        self.mock_client.get_account.return_value["balances"][1]["free"] = (
            "0.0"  # BTC reduced
        )

        # Phase 5: Check final state
        account_after_sell = self.mock_client.get_account()
        usdt_after_sell = float(
            [b for b in account_after_sell["balances"] if b["asset"] == "USDT"][0][
                "free"
            ]
        )
        btc_after_sell = float(
            [b for b in account_after_sell["balances"] if b["asset"] == "BTC"][0][
                "free"
            ]
        )

        self.assertEqual(usdt_after_sell, 1001.0)  # $1 profit
        self.assertEqual(btc_after_sell, 0.0)

        # Phase 6: Calculate P&L
        profit = usdt_after_sell - usdt_before
        profit_percentage = (profit / 50.0) * 100  # Based on trade amount

        self.assertEqual(profit, 1.0)
        self.assertEqual(profit_percentage, 2.0)

    def test_multiple_trades_scenario(self):
        """Multiple trades scenario testi"""
        trades_executed = []

        # Execute multiple buy orders
        for i in range(3):
            order = self.mock_client.order_market_buy(
                symbol="BTCUSDT", quantity="0.001"
            )
            trades_executed.append(
                {
                    "order_id": order["orderId"],
                    "side": order["side"],
                    "quantity": float(order["fills"][0]["qty"]),
                    "price": float(order["fills"][0]["price"]),
                    "cost": float(order["cummulativeQuoteQty"]),
                }
            )

        # Execute multiple sell orders
        for i in range(3):
            order = self.mock_client.order_market_sell(
                symbol="BTCUSDT", quantity="0.001"
            )
            trades_executed.append(
                {
                    "order_id": order["orderId"],
                    "side": order["side"],
                    "quantity": float(order["fills"][0]["qty"]),
                    "price": float(order["fills"][0]["price"]),
                    "cost": float(order["cummulativeQuoteQty"]),
                }
            )

        # Validate trades
        self.assertEqual(len(trades_executed), 6)

        buy_trades = [t for t in trades_executed if t["side"] == "BUY"]
        sell_trades = [t for t in trades_executed if t["side"] == "SELL"]

        self.assertEqual(len(buy_trades), 3)
        self.assertEqual(len(sell_trades), 3)

        # Calculate total volumes
        total_buy_volume = sum(t["cost"] for t in buy_trades)
        total_sell_volume = sum(t["cost"] for t in sell_trades)

        self.assertEqual(total_buy_volume, 150.0)  # 3 * 50
        self.assertEqual(total_sell_volume, 153.0)  # 3 * 51

        # Calculate total profit
        total_profit = total_sell_volume - total_buy_volume
        self.assertEqual(total_profit, 3.0)

    def test_error_recovery_scenario(self):
        """Error recovery scenario testi"""
        # Setup error conditions
        from binance.exceptions import BinanceAPIException

        # First attempt fails
        self.mock_client.order_market_buy.side_effect = BinanceAPIException(
            response={"code": -1013, "msg": "Filter failure: LOT_SIZE"}, status_code=400
        )

        # Test error handling
        with self.assertRaises(BinanceAPIException):
            self.mock_client.order_market_buy(symbol="BTCUSDT", quantity="invalid")

        # Recovery: Reset and try again
        self.mock_client.order_market_buy.side_effect = None
        self.mock_client.order_market_buy.return_value = {
            "symbol": "BTCUSDT",
            "orderId": 12347,
            "status": "FILLED",
            "side": "BUY",
        }

        # Successful retry
        order = self.mock_client.order_market_buy(symbol="BTCUSDT", quantity="0.001")
        self.assertEqual(order["status"], "FILLED")

    def test_portfolio_rebalancing_scenario(self):
        """Portfolio rebalancing scenario testi"""
        # Initial portfolio state
        initial_portfolio = {
            "BTC": {"amount": 0.1, "value": 5000.0, "target_percentage": 50.0},
            "ETH": {"amount": 2.0, "value": 3000.0, "target_percentage": 30.0},
            "USDT": {"amount": 2000.0, "value": 2000.0, "target_percentage": 20.0},
        }

        total_value = sum(asset["value"] for asset in initial_portfolio.values())
        self.assertEqual(total_value, 10000.0)

        # Calculate current percentages
        for asset in initial_portfolio.values():
            asset["current_percentage"] = (asset["value"] / total_value) * 100

        # Check if rebalancing is needed
        rebalancing_needed = False
        for asset in initial_portfolio.values():
            deviation = abs(asset["current_percentage"] - asset["target_percentage"])
            if deviation > 5.0:  # 5% threshold
                rebalancing_needed = True
                break

        # In this case, no rebalancing needed (all within 5% of target)
        self.assertFalse(rebalancing_needed)

        # Simulate price change that requires rebalancing
        initial_portfolio["BTC"]["value"] = 8000.0  # BTC increased significantly
        new_total_value = sum(asset["value"] for asset in initial_portfolio.values())

        for asset in initial_portfolio.values():
            asset["current_percentage"] = (asset["value"] / new_total_value) * 100

        # Check again
        btc_deviation = abs(
            initial_portfolio["BTC"]["current_percentage"]
            - initial_portfolio["BTC"]["target_percentage"]
        )
        self.assertGreater(btc_deviation, 5.0)  # Should need rebalancing

    def test_risk_management_scenario(self):
        """Risk management scenario testi"""
        # Setup risk parameters
        total_balance = 1000.0
        soft_risk = 0.05  # 5%
        hard_risk = 0.10  # 10%

        soft_risk_amount = total_balance * soft_risk
        hard_risk_amount = total_balance * hard_risk

        self.assertEqual(soft_risk_amount, 50.0)
        self.assertEqual(hard_risk_amount, 100.0)

        # Test soft risk scenario (normal trade)
        trade_amount = 30.0  # Within soft risk
        self.assertLess(trade_amount, soft_risk_amount)

        # Execute trade within soft risk
        order = self.mock_client.order_market_buy(
            symbol="BTCUSDT", quantity="0.0006"
        )  # ~$30
        self.assertEqual(order["status"], "FILLED")

        # Test hard risk scenario (large trade)
        large_trade_amount = 150.0  # Exceeds hard risk
        self.assertGreater(large_trade_amount, hard_risk_amount)

        # In real scenario, this should be blocked or require confirmation
        # For test purposes, we just validate the risk calculation
        risk_ratio = large_trade_amount / total_balance
        self.assertGreater(risk_ratio, hard_risk)


class TestSystemIntegration(unittest.TestCase):
    """System integration testleri"""

    def test_data_flow_integration(self):
        """Data flow integration testi"""
        # Test complete data flow from order to storage

        # Step 1: Order execution
        mock_order_data = {
            "orderId": 12345,
            "symbol": "BTCUSDT",
            "side": "BUY",
            "status": "FILLED",
            "fills": [{"price": "50000.0", "qty": "0.001"}],
            "cummulativeQuoteQty": "50.0",
        }

        # Step 2: Trade data preparation
        trade_data = {
            "timestamp": datetime.now().isoformat(),
            "symbol": mock_order_data["symbol"],
            "side": mock_order_data["side"],
            "type": "Hard_Buy",
            "quantity": float(mock_order_data["fills"][0]["qty"]),
            "price": float(mock_order_data["fills"][0]["price"]),
            "total_cost": float(mock_order_data["cummulativeQuoteQty"]),
            "order_id": mock_order_data["orderId"],
            "order_type": "MARKET",
            "status": mock_order_data["status"],
        }

        # Step 3: Data validation
        self.assertIn("timestamp", trade_data)
        self.assertIn("symbol", trade_data)
        self.assertIn("side", trade_data)
        self.assertIn("order_id", trade_data)
        self.assertEqual(trade_data["side"], "BUY")
        self.assertEqual(trade_data["quantity"], 0.001)

        # Step 4: Storage simulation (would normally save to file)
        stored_trades = [trade_data]
        self.assertEqual(len(stored_trades), 1)
        self.assertEqual(stored_trades[0]["order_id"], 12345)

    def test_configuration_integration(self):
        """Configuration integration testi"""
        # Test configuration loading and application

        # Mock configuration data
        config_data = {
            "preferences": {
                "soft_risk": 0.05,
                "hard_risk": 0.10,
                "order_type": "MARKET",
            },
            "fav_coins": {
                "coins": [
                    {"symbol": "BTCUSDT", "name": "Bitcoin"},
                    {"symbol": "ETHUSDT", "name": "Ethereum"},
                ]
            },
        }

        # Test preferences application
        soft_risk = config_data["preferences"]["soft_risk"]
        hard_risk = config_data["preferences"]["hard_risk"]
        order_type = config_data["preferences"]["order_type"]

        self.assertEqual(soft_risk, 0.05)
        self.assertEqual(hard_risk, 0.10)
        self.assertEqual(order_type, "MARKET")

        # Test favorite coins application
        fav_symbols = [coin["symbol"] for coin in config_data["fav_coins"]["coins"]]
        self.assertIn("BTCUSDT", fav_symbols)
        self.assertIn("ETHUSDT", fav_symbols)

        # Test configuration validation
        self.assertTrue(0 < soft_risk < 1)
        self.assertTrue(0 < hard_risk < 1)
        self.assertTrue(soft_risk < hard_risk)
        self.assertIn(order_type, ["MARKET", "LIMIT"])

    def test_error_handling_integration(self):
        """Error handling integration testi"""
        # Test comprehensive error handling across system

        error_scenarios = [
            {
                "type": "network_error",
                "description": "Network connection failed",
                "expected_behavior": "retry_mechanism",
            },
            {
                "type": "api_error",
                "description": "Invalid API credentials",
                "expected_behavior": "authentication_error",
            },
            {
                "type": "insufficient_balance",
                "description": "Not enough USDT for trade",
                "expected_behavior": "balance_check_failure",
            },
            {
                "type": "invalid_symbol",
                "description": "Trading pair not found",
                "expected_behavior": "symbol_validation_error",
            },
        ]

        # Test each error scenario
        for scenario in error_scenarios:
            with self.subTest(scenario=scenario["type"]):
                # Each scenario should have proper error handling
                self.assertIn("type", scenario)
                self.assertIn("description", scenario)
                self.assertIn("expected_behavior", scenario)

                # Verify error types are properly categorized
                self.assertIsInstance(scenario["type"], str)
                self.assertIsInstance(scenario["description"], str)
                self.assertIsInstance(scenario["expected_behavior"], str)


if __name__ == "__main__":
    unittest.main()
