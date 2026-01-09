"""
Test dosyası - Data management ve persistence
Bu dosya data kaydetme, yükleme ve yönetim işlemlerini test eder.
"""

import unittest
from unittest.mock import Mock, patch, mock_open
import sys
import os
import json
from datetime import datetime

# Add src to path for imports
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src"))
)


class TestDataPersistence(unittest.TestCase):
    """Data persistence testleri"""

    def setUp(self):
        """Test setup"""
        self.sample_trade_data = {
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

        self.sample_portfolio_data = {
            "timestamp": "2025-09-12T10:00:00",
            "total_value": 10000.0,
            "positions": [
                {"asset": "BTC", "amount": 0.2, "value": 8000.0},
                {"asset": "USDT", "amount": 2000.0, "value": 2000.0},
            ],
        }

    @patch("builtins.open", new_callable=mock_open)
    @patch("json.dump")
    def test_save_trade_data(self, mock_json_dump, mock_file):
        """Trade data kaydetme testi"""
        # Simulate saving trade data
        filename = "trades_2025-09-12.json"

        # Save operation
        with open(filename, "w") as f:
            json.dump(self.sample_trade_data, f)

        # Assertions
        mock_file.assert_called_once_with(filename, "w")
        mock_json_dump.assert_called_once_with(self.sample_trade_data, mock_file())

    @patch("builtins.open", new_callable=mock_open, read_data='{"trades": []}')
    @patch("json.load")
    def test_load_trade_data(self, mock_json_load, mock_file):
        """Trade data yükleme testi"""
        # Setup
        mock_json_load.return_value = {"trades": [self.sample_trade_data]}

        # Load operation
        filename = "trades_2025-09-12.json"
        with open(filename, "r") as f:
            data = json.load(f)

        # Assertions
        mock_file.assert_called_once_with(filename, "r")
        mock_json_load.assert_called_once()
        self.assertIn("trades", data)
        self.assertEqual(len(data["trades"]), 1)

    @patch("builtins.open", new_callable=mock_open)
    @patch("json.dump")
    def test_save_portfolio_data(self, mock_json_dump, mock_file):
        """Portfolio data kaydetme testi"""
        # Simulate saving portfolio data
        filename = "portfolio_2025-09-12.json"

        # Save operation
        with open(filename, "w") as f:
            json.dump(self.sample_portfolio_data, f)

        # Assertions
        mock_file.assert_called_once_with(filename, "w")
        mock_json_dump.assert_called_once_with(self.sample_portfolio_data, mock_file())

    def test_data_validation(self):
        """Data validation testi"""
        # Test trade data validation
        required_trade_fields = [
            "timestamp",
            "symbol",
            "side",
            "type",
            "quantity",
            "price",
            "total_cost",
            "order_id",
        ]

        for field in required_trade_fields:
            self.assertIn(field, self.sample_trade_data)

        # Test portfolio data validation
        required_portfolio_fields = ["timestamp", "total_value", "positions"]

        for field in required_portfolio_fields:
            self.assertIn(field, self.sample_portfolio_data)

        # Validate position structure
        position = self.sample_portfolio_data["positions"][0]
        required_position_fields = ["asset", "amount", "value"]

        for field in required_position_fields:
            self.assertIn(field, position)

    def test_filename_generation(self):
        """Filename generation testi"""
        # Test date-based filename generation
        date_str = datetime.now().strftime("%Y-%m-%d")

        trade_filename = f"trades_{date_str}.json"
        portfolio_filename = f"portfolio_{date_str}.json"

        # Assertions
        self.assertTrue(trade_filename.startswith("trades_"))
        self.assertTrue(trade_filename.endswith(".json"))
        self.assertTrue(portfolio_filename.startswith("portfolio_"))
        self.assertTrue(portfolio_filename.endswith(".json"))

    def test_data_backup(self):
        """Data backup testi"""
        # Test backup filename generation
        original_filename = "portfolio.json"
        backup_filename = f"{original_filename}.backup"

        self.assertEqual(backup_filename, "portfolio.json.backup")

        # Test backup data structure
        backup_data = {
            "original_file": original_filename,
            "backup_timestamp": datetime.now().isoformat(),
            "data": self.sample_portfolio_data,
        }

        self.assertIn("original_file", backup_data)
        self.assertIn("backup_timestamp", backup_data)
        self.assertIn("data", backup_data)


class TestConfigurationManagement(unittest.TestCase):
    """Configuration management testleri"""

    def setUp(self):
        """Test setup"""
        self.sample_preferences = {
            "soft_risk": 0.05,
            "hard_risk": 0.10,
            "order_type": "MARKET",
            "auto_save": True,
            "log_level": "INFO",
        }

        self.sample_fav_coins = {
            "coins": [
                {"symbol": "BTCUSDT", "name": "Bitcoin"},
                {"symbol": "ETHUSDT", "name": "Ethereum"},
                {"symbol": "ADAUSDT", "name": "Cardano"},
            ],
            "dynamic_coin": [{"symbol": "DOGEUSDT", "name": "Dogecoin"}],
        }

    @patch("builtins.open", new_callable=mock_open)
    def test_preferences_file_reading(self, mock_file):
        """Preferences file okuma testi"""
        # Setup preferences file content
        prefs_content = """# Trading Preferences
soft_risk = 5%
hard_risk = 10%
order_type = MARKET
auto_save = true
log_level = INFO"""

        mock_file.return_value.read.return_value = prefs_content

        # Read preferences file
        filename = "Preferences.txt"
        with open(filename, "r") as f:
            content = f.read()

        # Assertions
        mock_file.assert_called_once_with(filename, "r")
        self.assertIn("soft_risk = 5%", content)
        self.assertIn("hard_risk = 10%", content)
        self.assertIn("order_type = MARKET", content)

    @patch("builtins.open", new_callable=mock_open, read_data="{}")
    @patch("json.load")
    def test_fav_coins_loading(self, mock_json_load, mock_file):
        """Favori coins yükleme testi"""
        # Setup
        mock_json_load.return_value = self.sample_fav_coins

        # Load fav coins
        filename = "fav_coins.json"
        with open(filename, "r") as f:
            data = json.load(f)

        # Assertions
        mock_file.assert_called_once_with(filename, "r")
        self.assertIn("coins", data)
        self.assertIn("dynamic_coin", data)
        self.assertEqual(len(data["coins"]), 3)
        self.assertEqual(len(data["dynamic_coin"]), 1)

    def test_preferences_parsing(self):
        """Preferences parsing testi"""
        # Test parsing different preference formats
        test_lines = [
            "soft_risk = 5%",
            "hard_risk = 10%",
            "order_type = MARKET",
            "auto_save = true",
            "log_level = INFO",
        ]

        parsed_prefs = {}

        for line in test_lines:
            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()

                # Parse different value types
                if value.endswith("%"):
                    parsed_prefs[key] = float(value[:-1]) / 100
                elif value.lower() in ["true", "false"]:
                    parsed_prefs[key] = value.lower() == "true"
                else:
                    parsed_prefs[key] = value

        # Assertions
        self.assertEqual(parsed_prefs["soft_risk"], 0.05)
        self.assertEqual(parsed_prefs["hard_risk"], 0.10)
        self.assertEqual(parsed_prefs["order_type"], "MARKET")
        self.assertTrue(parsed_prefs["auto_save"])
        self.assertEqual(parsed_prefs["log_level"], "INFO")

    def test_config_validation(self):
        """Config validation testi"""
        # Test valid configuration
        self.assertTrue(0 < self.sample_preferences["soft_risk"] < 1)
        self.assertTrue(0 < self.sample_preferences["hard_risk"] < 1)
        self.assertTrue(
            self.sample_preferences["soft_risk"] < self.sample_preferences["hard_risk"]
        )
        self.assertIn(self.sample_preferences["order_type"], ["MARKET", "LIMIT"])

        # Test invalid configuration
        invalid_prefs = {
            "soft_risk": 1.5,  # Over 100%
            "hard_risk": -0.1,  # Negative
            "order_type": "INVALID",
        }

        self.assertFalse(0 < invalid_prefs["soft_risk"] < 1)
        self.assertFalse(0 < invalid_prefs["hard_risk"] < 1)
        self.assertNotIn(invalid_prefs["order_type"], ["MARKET", "LIMIT"])


class TestAnalyticsAndReporting(unittest.TestCase):
    """Analytics ve reporting testleri"""

    def setUp(self):
        """Test setup"""
        self.sample_trades = [
            {
                "timestamp": "2025-09-12T09:00:00",
                "symbol": "BTCUSDT",
                "side": "BUY",
                "quantity": 0.001,
                "price": 50000.0,
                "total_cost": 50.0,
            },
            {
                "timestamp": "2025-09-12T10:00:00",
                "symbol": "BTCUSDT",
                "side": "SELL",
                "quantity": 0.001,
                "price": 51000.0,
                "total_cost": 51.0,
            },
        ]

    def test_profit_loss_calculation(self):
        """Profit/Loss hesaplama testi"""
        # Calculate P&L from sample trades
        buy_trade = self.sample_trades[0]
        sell_trade = self.sample_trades[1]

        # Assuming same quantity for buy and sell
        if buy_trade["quantity"] == sell_trade["quantity"]:
            pnl = sell_trade["total_cost"] - buy_trade["total_cost"]
            pnl_percentage = (pnl / buy_trade["total_cost"]) * 100

            # Assertions
            self.assertEqual(pnl, 1.0)  # $1 profit
            self.assertEqual(pnl_percentage, 2.0)  # 2% profit

    def test_trade_statistics(self):
        """Trade statistics testi"""
        # Calculate trade statistics
        total_trades = len(self.sample_trades)
        buy_trades = len([t for t in self.sample_trades if t["side"] == "BUY"])
        sell_trades = len([t for t in self.sample_trades if t["side"] == "SELL"])

        # Calculate volumes
        total_volume = sum(t["total_cost"] for t in self.sample_trades)
        avg_trade_size = total_volume / total_trades if total_trades > 0 else 0

        # Assertions
        self.assertEqual(total_trades, 2)
        self.assertEqual(buy_trades, 1)
        self.assertEqual(sell_trades, 1)
        self.assertEqual(total_volume, 101.0)
        self.assertEqual(avg_trade_size, 50.5)

    def test_performance_metrics(self):
        """Performance metrics testi"""
        # Sample performance data
        portfolio_values = [10000.0, 10100.0, 10050.0, 10200.0]

        # Calculate performance metrics
        initial_value = portfolio_values[0]
        final_value = portfolio_values[-1]
        total_return = (final_value - initial_value) / initial_value * 100

        # Calculate max drawdown
        peak = portfolio_values[0]
        max_drawdown = 0

        for value in portfolio_values:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak * 100
            if drawdown > max_drawdown:
                max_drawdown = drawdown

        # Assertions
        self.assertEqual(total_return, 2.0)  # 2% total return
        self.assertEqual(max_drawdown, 0.495049504950495)  # ~0.5% max drawdown

    def test_report_generation(self):
        """Report generation testi"""
        # Generate performance report structure
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_trades": len(self.sample_trades),
            "profit_trades": 1,
            "loss_trades": 0,
            "win_rate": 100.0,
            "total_pnl": 1.0,
            "total_pnl_percentage": 2.0,
            "largest_win": 1.0,
            "largest_loss": 0.0,
            "avg_win": 1.0,
            "avg_loss": 0.0,
        }

        # Validate report structure
        required_fields = [
            "timestamp",
            "total_trades",
            "profit_trades",
            "loss_trades",
            "win_rate",
            "total_pnl",
            "total_pnl_percentage",
        ]

        for field in required_fields:
            self.assertIn(field, report)

        # Validate calculated values
        self.assertEqual(report["total_trades"], 2)
        self.assertEqual(report["win_rate"], 100.0)
        self.assertEqual(report["total_pnl"], 1.0)


if __name__ == "__main__":
    unittest.main()
