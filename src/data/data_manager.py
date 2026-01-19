import json
import os
import datetime
from typing import Dict
import logging

from core.paths import (
    PROJECT_ROOT,
    DATA_DIR,
    TRADES_DIR,
    PORTFOLIO_DIR,
    ANALYTICS_DIR,
    LATEST_PORTFOLIO_FILE,
    get_daily_trades_file,
    get_daily_portfolio_file,
)

"""
data_manager.py
Kullanıcının trading verilerini, cüzdan değerlerini ve performans metriklerini yöneten servis.
"""


class DataManager:
    def __init__(self):
        try:
            # Use centralized paths
            self.project_root = PROJECT_ROOT
            self.data_dir = DATA_DIR
            self.trades_dir = TRADES_DIR
            self.portfolio_dir = PORTFOLIO_DIR
            self.analytics_dir = ANALYTICS_DIR

            # Ensure directories exist (paths module already handles this)
            for directory in [
                self.data_dir,
                self.trades_dir,
                self.portfolio_dir,
                self.analytics_dir,
            ]:
                os.makedirs(directory, exist_ok=True)

            logging.info("DataManager initialized successfully")

        except Exception as e:
            logging.error(f"Error initializing DataManager: {e}")
            logging.exception("Full traceback for DataManager initialization error:")
            raise

    def save_trade(self, trade_data: Dict) -> None:
        """
        Bir trading işlemini kaydeder.

        Args:
            trade_data: {
                'timestamp': '2025-08-04 20:45:00',
                'symbol': 'BTCUSDT',
                'side': 'BUY' | 'SELL',
                'type': 'Hard_Buy' | 'Soft_Buy' | 'Hard_Sell' | 'Soft_Sell',
                'quantity': 0.001,
                'price': 50000.0,
                'total_cost': 50.0,
                'wallet_before': 1000.0,
                'wallet_after': 950.0,
                'order_id': 'binance_order_id'
            }
        """
        try:
            timestamp = datetime.datetime.now()
            date_str = timestamp.strftime("%Y-%m-%d")

            # Add metadata
            trade_data["recorded_at"] = timestamp.isoformat()
            trade_data["id"] = (
                f"{timestamp.strftime('%Y%m%d_%H%M%S')}_{trade_data.get('symbol', 'UNKNOWN')}"
            )

            # Daily trades file
            trades_file = get_daily_trades_file(date_str)

            # Load existing trades or create new list
            trades = []
            if os.path.exists(trades_file):
                with open(trades_file, "r", encoding="utf-8") as f:
                    trades = json.load(f)

            trades.append(trade_data)

            # Save updated trades
            with open(trades_file, "w", encoding="utf-8") as f:
                json.dump(trades, f, indent=2, ensure_ascii=False)

            logging.info(f"Trade saved: {trade_data['id']}")

        except Exception as e:
            logging.error(f"Error saving trade: {e}")
            logging.error(f"Trade data that failed to save: {trade_data}")
            logging.exception("Full traceback for trade saving error:")

    def save_portfolio_snapshot(self, portfolio_data: Dict) -> None:
        """
        Portföy anlık görüntüsünü kaydeder.

        Args:
            portfolio_data: {
                'timestamp': '2025-08-04 20:45:00',
                'total_usdt': 1000.0,
                'total_value_usdt': 1050.0,
                'holdings': {
                    'BTC': {'amount': 0.002, 'value_usdt': 100.0},
                    'ETH': {'amount': 0.05, 'value_usdt': 150.0}
                },
                'daily_pnl': 50.0,
                'total_pnl': 150.0
            }
        """
        try:
            timestamp = datetime.datetime.now()
            date_str = timestamp.strftime("%Y-%m-%d")

            # Add metadata
            portfolio_data["recorded_at"] = timestamp.isoformat()
            portfolio_data["snapshot_id"] = f"{timestamp.strftime('%Y%m%d_%H%M%S')}"

            # Daily portfolio file
            portfolio_file = get_daily_portfolio_file(date_str)

            # Load existing snapshots or create new list
            snapshots = []
            if os.path.exists(portfolio_file):
                with open(portfolio_file, "r", encoding="utf-8") as f:
                    snapshots = json.load(f)

            snapshots.append(portfolio_data)

            # Save updated snapshots
            with open(portfolio_file, "w", encoding="utf-8") as f:
                json.dump(snapshots, f, indent=2, ensure_ascii=False)

            # Also save latest snapshot for quick access
            with open(LATEST_PORTFOLIO_FILE, "w", encoding="utf-8") as f:
                json.dump(portfolio_data, f, indent=2, ensure_ascii=False)

            logging.info(f"Portfolio snapshot saved: {portfolio_data['snapshot_id']}")

        except Exception as e:
            logging.error(f"Error saving portfolio snapshot: {e}")
            logging.error(f"Portfolio data that failed to save: {portfolio_data}")
            logging.exception("Full traceback for portfolio saving error:")

    def get_trades_summary(self, days: int = 7) -> Dict:
        """Son N günün işlem özetini getirir."""
        try:
            summary = {
                "total_trades": 0,
                "total_buy_volume": 0.0,
                "total_sell_volume": 0.0,
                "profitable_trades": 0,
                "losing_trades": 0,
                "most_traded_symbol": "",
                "date_range": f"Last {days} days",
            }

            end_date = datetime.datetime.now()

            for i in range(days):
                date = (end_date - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
                trades_file = get_daily_trades_file(date)

                if os.path.exists(trades_file):
                    with open(trades_file, "r", encoding="utf-8") as f:
                        trades = json.load(f)

                        for trade in trades:
                            summary["total_trades"] += 1
                            side = trade.get("side", "").upper()
                            if side == "BUY" or side == "buy":
                                summary["total_buy_volume"] += trade.get(
                                    "total", trade.get("total_cost", 0)
                                )
                            elif side == "SELL" or side == "sell":
                                summary["total_sell_volume"] += trade.get(
                                    "total", trade.get("total_cost", 0)
                                )

            # Calculate today's trades count
            today_str = datetime.datetime.now().strftime("%Y-%m-%d")
            today_trades_file = get_daily_trades_file(today_str)
            if os.path.exists(today_trades_file):
                with open(today_trades_file, "r", encoding="utf-8") as f:
                    today_trades = json.load(f)
                    summary["today_count"] = len(today_trades)
            else:
                summary["today_count"] = 0

            return summary

        except Exception as e:
            logging.error(f"Error generating trades summary: {e}")
            logging.error(f"Failed to generate summary for last {days} days")
            logging.exception("Full traceback for trades summary error:")
            return {}


# Global instance
data_manager = DataManager()
