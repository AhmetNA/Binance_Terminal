import os
import sys
import datetime
import logging
from typing import Dict, List

# Import paths from centralized path module
from core.paths import SRC_DIR, PROJECT_ROOT
sys.path.insert(0, SRC_DIR)

from services.account_service import get_account_data
from services.client_service import prepare_client
from utils.trading_utils import get_price
from data.data_manager import data_manager

"""
portfolio_tracker.py
Portföy değerini takip eden ve periyodik olarak kaydeden servis.
"""

class PortfolioTracker:
    def __init__(self):
        self.client = None
        self.last_snapshot_time = None
        self.snapshot_interval = 300  # 5 dakika (saniye)
    
    def initialize_client(self):
        """Binance client'ı başlatır."""
        try:
            if self.client is None:
                self.client = prepare_client()
                logging.info("Portfolio tracker initialized")
        except Exception as e:
            logging.error(f"Error initializing portfolio tracker: {e}")
            self.client = None
    
    def get_current_portfolio(self) -> Dict:
        """Mevcut portföy durumunu hesaplar."""
        if not self.client:
            self.initialize_client()
        
        if not self.client:
            logging.warning("Portfolio tracker client not available")
            return {}
        
        try:
            account_data = get_account_data(self.client)
            
            portfolio = {
                'timestamp': datetime.datetime.now().isoformat(),
                'total_usdt': 0.0,
                'total_value_usdt': 0.0,
                'holdings': {},
                'free_balances': {},
                'locked_balances': {}
            }
            
            total_value = 0.0
            usdt_balance = 0.0
            
            for asset in account_data['balances']:
                free_amount = float(asset['free'])
                locked_amount = float(asset['locked'])
                total_amount = free_amount + locked_amount
                
                # Skip assets with very small amounts to avoid unnecessary API calls
                if total_amount < 0.000001:  # Skip dust amounts
                    continue
                    
                if total_amount > 0:
                    asset_symbol = asset['asset']
                    
                    if asset_symbol == 'USDT':
                        usdt_balance = total_amount
                        total_value += total_amount
                        portfolio['holdings']['USDT'] = {
                            'amount': total_amount,
                            'value_usdt': total_amount,
                            'price': 1.0
                        }
                    else:
                        # Get current price for non-USDT assets
                        price_found = False
                        current_price = 0.0
                        asset_value = 0.0
                        
                        # Skip price lookup for very small amounts to speed up processing
                        if total_amount < 0.001:  # For amounts less than 0.001
                            logging.debug(f"Skipping price lookup for small amount: {asset_symbol} {total_amount}")
                            continue
                        
                        # Try different pairings with timeout
                        possible_pairs = [f"{asset_symbol}USDT"]  # Only try USDT pairs first
                        
                        for pair_symbol in possible_pairs:
                            try:
                                # Add timeout to prevent hanging
                                current_price = get_price(self.client, pair_symbol)
                                asset_value = total_amount * current_price
                                total_value += asset_value
                                price_found = True
                                break
                                
                            except Exception as e:
                                logging.debug(f"Failed to get price for {pair_symbol}: {e}")
                                # Try BTC and ETH pairs only if USDT fails
                                if pair_symbol.endswith('USDT'):
                                    try:
                                        if f"{asset_symbol}BTC" not in possible_pairs:
                                            possible_pairs.append(f"{asset_symbol}BTC")
                                    except:
                                        pass
                                continue
                        
                        if price_found:
                            portfolio['holdings'][asset_symbol] = {
                                'amount': total_amount,
                                'value_usdt': asset_value,
                                'price': current_price
                            }
                        else:
                            # Skip assets that can't be priced (like fiat currencies)
                            logging.debug(f"Skipping {asset_symbol}: No valid trading pair found")
                            continue
                    
                    portfolio['free_balances'][asset_symbol] = free_amount
                    portfolio['locked_balances'][asset_symbol] = locked_amount
            
            portfolio['total_usdt'] = usdt_balance
            portfolio['total_value_usdt'] = total_value
            
            # Calculate daily P&L if possible
            portfolio['daily_pnl'] = self.calculate_daily_pnl(total_value)
            
            return portfolio
            
        except Exception as e:
            logging.error(f"Error getting current portfolio: {e}")
            return {}
    
    def calculate_daily_pnl(self, current_value: float) -> float:
        """Günlük kar/zarar hesaplar."""
        try:
            # Get yesterday's last portfolio snapshot using centralized path
            yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
            yesterday_snapshots = []
            
            # Use centralized path from paths.py
            from core.paths import get_daily_portfolio_file
            yesterday_file = get_daily_portfolio_file(yesterday)
            
            if os.path.exists(yesterday_file):
                import json
                with open(yesterday_file, 'r', encoding='utf-8') as f:
                    yesterday_snapshots = json.load(f)
            
            if yesterday_snapshots:
                last_value = yesterday_snapshots[-1].get('total_value_usdt', current_value)
                return current_value - last_value
            
            return 0.0
            
        except Exception as e:
            logging.error(f"Error calculating daily P&L: {e}")
            return 0.0
    
    def should_take_snapshot(self) -> bool:
        """Snapshot alınması gerekip gerekmediğini kontrol eder."""
        if not self.last_snapshot_time:
            return True
        
        time_diff = (datetime.datetime.now() - self.last_snapshot_time).total_seconds()
        return time_diff >= self.snapshot_interval
    
    def take_snapshot(self) -> Dict:
        """Portföy snapshot'ı alır ve kaydeder."""
        try:
            logging.info("Taking portfolio snapshot...")
            portfolio = self.get_current_portfolio()
            if portfolio:
                data_manager.save_portfolio_snapshot(portfolio)
                self.last_snapshot_time = datetime.datetime.now()
                logging.info(f"Portfolio snapshot completed: {portfolio.get('total_value_usdt', 0):.2f} USDT")
                return portfolio
            else:
                logging.warning("Portfolio snapshot failed - no portfolio data")
            return {}
        except Exception as e:
            logging.error(f"Error taking portfolio snapshot: {e}")
            return {}
    
    def get_portfolio_summary(self, days: int = 7) -> Dict:
        """Portföy özetini döndürür."""
        try:
            current_portfolio = self.get_current_portfolio()
            trades_summary = data_manager.get_trades_summary(days)
            
            summary = {
                'current_value': current_portfolio.get('total_value_usdt', 0),
                'current_usdt': current_portfolio.get('total_usdt', 0),
                'daily_pnl': current_portfolio.get('daily_pnl', 0),
                'holdings_count': len(current_portfolio.get('holdings', {})),
                'trades_summary': trades_summary,
                'top_holdings': self.get_top_holdings(current_portfolio),
                'last_updated': datetime.datetime.now().isoformat()
            }
            
            return summary
            
        except Exception as e:
            logging.error(f"Error generating portfolio summary: {e}")
            return {}
    
    def get_top_holdings(self, portfolio: Dict, top_n: int = 5) -> List[Dict]:
        """En büyük holdingleri döndürür."""
        try:
            holdings = portfolio.get('holdings', {})
            sorted_holdings = sorted(
                holdings.items(), 
                key=lambda x: x[1].get('value_usdt', 0), 
                reverse=True
            )
            
            return [
                {
                    'symbol': symbol,
                    'amount': data['amount'],
                    'value_usdt': data['value_usdt'],
                    'percentage': (data['value_usdt'] / portfolio.get('total_value_usdt', 1)) * 100
                }
                for symbol, data in sorted_holdings[:top_n]
            ]
            
        except Exception as e:
            logging.error(f"Error getting top holdings: {e}")
            return []


# Global instance
portfolio_tracker = PortfolioTracker()
