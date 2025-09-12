import json
import datetime
from typing import Dict, List, Tuple

from core.paths import TRADES_DIR, ANALYTICS_DIR, get_daily_trades_file
from data.data_manager import data_manager

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
            
            report = {
                'period_days': days,
                'basic_stats': trades_summary,
                'generated_at': datetime.datetime.now().isoformat()
            }
            
            return report
            
        except Exception as e:
            print(f"Error generating performance report: {e}")
            return {}
    

    
    def export_report(self, report: Dict, filename: str = None) -> str:
        """Raporu dosyaya aktarır."""
        try:
            import os
            
            if not filename:
                timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f'performance_report_{timestamp}.json'
            
            report_path = os.path.join(ANALYTICS_DIR, filename)
            
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
