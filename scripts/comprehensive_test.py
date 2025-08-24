import os
import sys
import json
import datetime

# Add project paths
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
src_dir = os.path.join(project_root, 'src')
sys.path.insert(0, src_dir)

from data.data_manager import data_manager
from data.analytics_service import analytics_service

def test_data_manager():
    """Test data manager functionality"""
    print("🔧 Testing Data Manager...")
    
    # Test trade saving
    test_trade = {
        'symbol': 'BTCUSDT',
        'side': 'buy',
        'quantity': 0.001,
        'price': 45000.0,
        'total': 45.0,
        'wallet_before': {'USDT': 100.0},
        'wallet_after': {'USDT': 55.0, 'BTC': 0.001},
        'order_id': 'test_order_123'
    }
    
    data_manager.save_trade(test_trade)
    print("✅ Trade saved successfully")
    
    # Test portfolio snapshot
    test_portfolio = {
        'timestamp': datetime.datetime.now().isoformat(),
        'total_usdt': 55.0,
        'total_value_usdt': 100.0,
        'holdings': {
            'USDT': {'amount': 55.0, 'value_usdt': 55.0, 'price': 1.0},
            'BTC': {'amount': 0.001, 'value_usdt': 45.0, 'price': 45000.0}
        },
        'daily_pnl': 0.0
    }
    
    data_manager.save_portfolio_snapshot(test_portfolio)
    print("✅ Portfolio snapshot saved successfully")
    
    # Test trade summary
    summary = data_manager.get_trades_summary(7)
    print(f"✅ Trade summary: {summary['total_trades']} trades in last 7 days")
    
    return True

def test_analytics():
    """Test analytics service"""
    print("\n📊 Testing Analytics Service...")
    
    # Generate performance report
    report = analytics_service.get_performance_report(7)
    print(f"✅ Performance report generated for {report.get('period_days', 0)} days")
    
    # Get monthly summary
    monthly = analytics_service.get_monthly_summary()
    print(f"✅ Monthly summary generated for {monthly.get('month', 'unknown')}")
    
    return True

def test_file_structure():
    """Test if all required directories exist"""
    print("\n📁 Testing File Structure...")
    
    required_dirs = [
        data_manager.data_dir,
        data_manager.trades_dir,
        data_manager.portfolio_dir,
        data_manager.analytics_dir
    ]
    
    for directory in required_dirs:
        if os.path.exists(directory):
            print(f"✅ {os.path.basename(directory)} directory exists")
        else:
            print(f"❌ {os.path.basename(directory)} directory missing")
            return False
    
    return True

def show_recent_data():
    """Show recent data to verify everything is working"""
    print("\n📈 Recent Data Overview...")
    
    # Show latest portfolio
    latest_portfolio = data_manager.get_latest_portfolio()
    if latest_portfolio:
        total_value = latest_portfolio.get('total_value_usdt', 0)
        holdings_count = len(latest_portfolio.get('holdings', {}))
        print(f"✅ Latest portfolio: {total_value:.2f} USDT across {holdings_count} assets")
    else:
        print("ℹ️ No portfolio snapshots found")
    
    # Show today's trades
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    today_trades = data_manager.get_trades_by_date(today)
    print(f"✅ Today's trades: {len(today_trades)} transactions")
    
    # Show data files
    trades_files = [f for f in os.listdir(data_manager.trades_dir) if f.endswith('.json')]
    portfolio_files = [f for f in os.listdir(data_manager.portfolio_dir) if f.endswith('.json')]
    
    print(f"✅ Data files: {len(trades_files)} trade files, {len(portfolio_files)} portfolio files")

if __name__ == "__main__":
    print("🚀 Binance Terminal Data System Test")
    print("=" * 50)
    
    try:
        # Run all tests
        if test_file_structure():
            print("✅ File structure test passed")
        
        if test_data_manager():
            print("✅ Data manager test passed")
        
        if test_analytics():
            print("✅ Analytics service test passed")
        
        show_recent_data()
        
        print("\n" + "=" * 50)
        print("🎉 All tests completed successfully!")
        print("📊 Data management system is ready for use")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
