import os
import sys
import json
import datetime
from typing import Dict, List, Tuple

# Add path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_dir)
sys.path.append(src_dir)

from services.data_manager import data_manager

"""
analytics_service.py
Trading analitikleri ve raporlama servisi.
"""

class AnalyticsService:
    def __init__(self):
        self.data_manager = data_manager
    
    def get_performance_report(self, days: int = 30) -> Dict:
        """Performans raporu oluşturur."""
        try:
            trades_summary = self.data_manager.get_trades_summary(days)
            
            # Calculate additional metrics
            win_rate = self.calculate_win_rate(days)
            avg_trade_size = self.calculate_avg_trade_size(days)
            daily_volume = self.calculate_daily_volume(days)
            top_coins = self.get_top_traded_coins(days)
            
            report = {
                'period_days': days,
                'basic_stats': trades_summary,
                'win_rate': win_rate,
                'avg_trade_size': avg_trade_size,
                'daily_avg_volume': daily_volume,
                'top_coins': top_coins,
                'generated_at': datetime.datetime.now().isoformat()
            }
            
            return report
            
        except Exception as e:
            print(f"Error generating performance report: {e}")
            return {}
    
    def calculate_win_rate(self, days: int) -> float:
        """Kazanma oranını hesaplar."""
        try:
            # This is a simplified calculation
            # In real scenarios, you'd need to track entry/exit prices
            trades = self.get_recent_trades(days)
            
            if not trades:
                return 0.0
            
            # For now, return a placeholder
            # Real implementation would compare buy/sell prices
            return 0.0
            
        except Exception as e:
            print(f"Error calculating win rate: {e}")
            return 0.0
    
    def calculate_avg_trade_size(self, days: int) -> float:
        """Ortalama işlem büyüklüğünü hesaplar."""
        try:
            trades = self.get_recent_trades(days)
            
            if not trades:
                return 0.0
            
            total_value = sum(trade.get('total', 0) for trade in trades)
            return total_value / len(trades)
            
        except Exception as e:
            print(f"Error calculating average trade size: {e}")
            return 0.0
    
    def calculate_daily_volume(self, days: int) -> float:
        """Günlük ortalama volümü hesaplar."""
        try:
            trades = self.get_recent_trades(days)
            
            if not trades or days == 0:
                return 0.0
            
            total_volume = sum(trade.get('total', 0) for trade in trades)
            return total_volume / days
            
        except Exception as e:
            print(f"Error calculating daily volume: {e}")
            return 0.0
    
    def get_top_traded_coins(self, days: int, top_n: int = 5) -> List[Dict]:
        """En çok işlem gören coinleri döndürür."""
        try:
            trades = self.get_recent_trades(days)
            
            if not trades:
                return []
            
            # Count trades by symbol
            coin_stats = {}
            for trade in trades:
                symbol = trade.get('symbol', 'Unknown')
                base_symbol = symbol.replace('USDT', '').replace('BTC', '').replace('ETH', '')
                
                if base_symbol not in coin_stats:
                    coin_stats[base_symbol] = {
                        'count': 0,
                        'total_volume': 0.0,
                        'buy_count': 0,
                        'sell_count': 0
                    }
                
                coin_stats[base_symbol]['count'] += 1
                coin_stats[base_symbol]['total_volume'] += trade.get('total', 0)
                
                if trade.get('side') == 'buy':
                    coin_stats[base_symbol]['buy_count'] += 1
                else:
                    coin_stats[base_symbol]['sell_count'] += 1
            
            # Sort by trade count
            sorted_coins = sorted(
                coin_stats.items(),
                key=lambda x: x[1]['count'],
                reverse=True
            )
            
            return [
                {
                    'symbol': symbol,
                    'trade_count': stats['count'],
                    'total_volume': stats['total_volume'],
                    'buy_count': stats['buy_count'],
                    'sell_count': stats['sell_count']
                }
                for symbol, stats in sorted_coins[:top_n]
            ]
            
        except Exception as e:
            print(f"Error getting top traded coins: {e}")
            return []
    
    def get_recent_trades(self, days: int) -> List[Dict]:
        """Son N günün işlemlerini getirir."""
        try:
            all_trades = []
            end_date = datetime.datetime.now()
            
            for i in range(days):
                date = end_date - datetime.timedelta(days=i)
                date_str = date.strftime('%Y-%m-%d')
                
                trades_file = os.path.join(self.data_manager.trades_dir, f'trades_{date_str}.json')
                
                if os.path.exists(trades_file):
                    with open(trades_file, 'r', encoding='utf-8') as f:
                        daily_trades = json.load(f)
                        all_trades.extend(daily_trades)
            
            return all_trades
            
        except Exception as e:
            print(f"Error getting recent trades: {e}")
            return []
    
    def export_report(self, report: Dict, filename: str = None) -> str:
        """Raporu dosyaya aktarır."""
        try:
            if not filename:
                timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f'performance_report_{timestamp}.json'
            
            report_path = os.path.join(self.data_manager.analytics_dir, filename)
            
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            return report_path
            
        except Exception as e:
            print(f"Error exporting report: {e}")
            return ""
    
    def get_monthly_summary(self) -> Dict:
        """Aylık özet raporu oluşturur."""
        try:
            # Current month
            now = datetime.datetime.now()
            first_day = now.replace(day=1)
            days_in_month = (now - first_day).days + 1
            
            monthly_report = self.get_performance_report(days_in_month)
            monthly_report['period_type'] = 'monthly'
            monthly_report['month'] = now.strftime('%Y-%m')
            
            return monthly_report
            
        except Exception as e:
            print(f"Error generating monthly summary: {e}")
            return {}


# Global instance
analytics_service = AnalyticsService()
