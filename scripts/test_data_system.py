#!/usr/bin/env python3
"""
Test script for data management system
Bu script veri yönetim sisteminin çalışıp çalışmadığını test eder.
"""

import os
import sys
import datetime

# Add project paths
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
src_dir = os.path.join(project_root, 'src')
sys.path.insert(0, src_dir)

from services.data_manager import data_manager
from services.portfolio_tracker import portfolio_tracker
from services.analytics_service import analytics_service

def test_data_manager():
    """Data manager'ı test eder."""
    print("=== Data Manager Test ===")
    
    # Test trade saving
    test_trade = {
        'symbol': 'BTCUSDT',
        'side': 'buy',
        'quantity': 0.001,
        'price': 45000.0,
        'total': 45.0,
        'order_id': 'test_123',
        'wallet_before': {'USDT': 100.0, 'BTC': 0.0},
        'wallet_after': {'USDT': 55.0, 'BTC': 0.001}
    }
    
    try:
        data_manager.save_trade(test_trade)
        print("✅ Trade data saved successfully")
    except Exception as e:
        print(f"❌ Error saving trade: {e}")
    
    # Test portfolio snapshot
    test_portfolio = {
        'timestamp': datetime.datetime.now().isoformat(),
        'total_usdt': 55.0,
        'total_value_usdt': 100.0,
        'holdings': {
            'USDT': {'amount': 55.0, 'value_usdt': 55.0, 'price': 1.0},
            'BTC': {'amount': 0.001, 'value_usdt': 45.0, 'price': 45000.0}
        }
    }
    
    try:
        data_manager.save_portfolio_snapshot(test_portfolio)
        print("✅ Portfolio snapshot saved successfully")
    except Exception as e:
        print(f"❌ Error saving portfolio: {e}")
    
    # Test trades summary
    try:
        summary = data_manager.get_trades_summary(7)
        print(f"✅ Trades summary generated: {summary}")
    except Exception as e:
        print(f"❌ Error getting trades summary: {e}")

def test_portfolio_tracker():
    """Portfolio tracker'ı test eder."""
    print("\n=== Portfolio Tracker Test ===")
    
    try:
        # Test portfolio calculation (will fail if no API connection)
        print("🔄 Testing portfolio calculation...")
        portfolio = portfolio_tracker.get_current_portfolio()
        
        if portfolio:
            print(f"✅ Portfolio retrieved: {portfolio.get('total_value_usdt', 0):.2f} USDT")
        else:
            print("⚠️ No portfolio data (API connection needed)")
            
    except Exception as e:
        print(f"⚠️ Portfolio tracker test failed (expected without API): {e}")
    
    # Test summary generation
    try:
        summary = portfolio_tracker.get_portfolio_summary()
        print(f"✅ Portfolio summary generated")
    except Exception as e:
        print(f"❌ Error generating portfolio summary: {e}")

def test_analytics_service():
    """Analytics service'i test eder."""
    print("\n=== Analytics Service Test ===")
    
    try:
        report = analytics_service.get_performance_report(7)
        print(f"✅ Performance report generated")
        
        # Export report
        report_path = analytics_service.export_report(report)
        if report_path:
            print(f"✅ Report exported to: {report_path}")
        else:
            print("⚠️ Report export failed")
            
    except Exception as e:
        print(f"❌ Error testing analytics: {e}")

def test_data_directories():
    """Data dizinlerinin varlığını kontrol eder."""
    print("\n=== Data Directories Test ===")
    
    directories = [
        data_manager.data_dir,
        data_manager.trades_dir,
        data_manager.portfolio_dir,
        data_manager.analytics_dir
    ]
    
    for directory in directories:
        if os.path.exists(directory):
            print(f"✅ Directory exists: {directory}")
        else:
            print(f"❌ Directory missing: {directory}")

def main():
    """Ana test fonksiyonu."""
    print("Binance Terminal Data Management System Test")
    print("=" * 50)
    
    test_data_directories()
    test_data_manager()
    test_portfolio_tracker()
    test_analytics_service()
    
    print("\n" + "=" * 50)
    print("Test completed!")
    print("\nNot: API bağlantısı gerektiren testler normal şartlarda başarısız olabilir.")
    print("Gerçek testler için Binance API anahtarlarınızı yapılandırın.")

if __name__ == "__main__":
    main()
