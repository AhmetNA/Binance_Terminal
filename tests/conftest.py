"""
Test conftest.py - pytest configuration and shared fixtures
Bu dosya tüm testler için ortak fixture'ları ve konfigürasyonu sağlar.
"""

import pytest
import sys
import os
from unittest.mock import Mock, MagicMock
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))


@pytest.fixture
def mock_binance_client():
    """Mock Binance client fixture"""
    client = Mock()
    
    # Mock basic methods
    client.get_account.return_value = {
        'balances': [
            {'asset': 'USDT', 'free': '1000.0', 'locked': '0.0'},
            {'asset': 'BTC', 'free': '0.01', 'locked': '0.0'},
            {'asset': 'ETH', 'free': '0.5', 'locked': '0.001'}
        ]
    }
    
    client.get_symbol_ticker.return_value = {
        'symbol': 'BTCUSDT',
        'price': '50000.0'
    }
    
    client.get_exchange_info.return_value = {
        'symbols': [{
            'symbol': 'BTCUSDT',
            'status': 'TRADING',
            'baseAsset': 'BTC',
            'baseAssetPrecision': 8,
            'quoteAsset': 'USDT',
            'quotePrecision': 8,
            'filters': [{
                'filterType': 'LOT_SIZE',
                'minQty': '0.00001000',
                'maxQty': '9000.00000000',
                'stepSize': '0.00001000'
            }]
        }]
    }
    
    # Mock order methods
    client.order_market_buy.return_value = {
        'symbol': 'BTCUSDT',
        'orderId': 12345,
        'transactTime': 1234567890,
        'status': 'FILLED',
        'side': 'BUY',
        'type': 'MARKET',
        'fills': [{
            'price': '50000.0',
            'qty': '0.001',
            'commission': '0.00000001',
            'commissionAsset': 'BTC'
        }],
        'cummulativeQuoteQty': '50.0'
    }
    
    client.order_market_sell.return_value = {
        'symbol': 'BTCUSDT',
        'orderId': 12346,
        'transactTime': 1234567891,
        'status': 'FILLED',
        'side': 'SELL',
        'type': 'MARKET',
        'fills': [{
            'price': '51000.0',
            'qty': '0.001',
            'commission': '0.051',
            'commissionAsset': 'USDT'
        }],
        'cummulativeQuoteQty': '51.0'
    }
    
    client.order_limit_buy.return_value = {
        'symbol': 'BTCUSDT',
        'orderId': 12347,
        'transactTime': 1234567892,
        'status': 'NEW',
        'side': 'BUY',
        'type': 'LIMIT',
        'price': '49000.0',
        'origQty': '0.001',
        'fills': []
    }
    
    client.get_order.return_value = {
        'orderId': 12345,
        'status': 'FILLED',
        'symbol': 'BTCUSDT',
        'executedQty': '0.001',
        'cummulativeQuoteQty': '50.0'
    }
    
    client.get_my_trades.return_value = [{
        'id': 1,
        'orderId': 12345,
        'symbol': 'BTCUSDT',
        'side': 'BUY',
        'qty': '0.001',
        'price': '50000.0',
        'time': 1234567890,
        'isBuyer': True,
        'commission': '0.00000001',
        'commissionAsset': 'BTC'
    }]
    
    return client


@pytest.fixture
def sample_trade_data():
    """Sample trade data fixture"""
    return {
        'timestamp': '2025-09-12T10:00:00',
        'symbol': 'BTCUSDT',
        'side': 'BUY',
        'type': 'Hard_Buy',
        'quantity': 0.001,
        'price': 50000.0,
        'total_cost': 50.0,
        'wallet_before': 1000.0,
        'wallet_after': 950.0,
        'order_id': 12345,
        'order_type': 'MARKET',
        'status': 'FILLED'
    }


@pytest.fixture
def sample_portfolio_data():
    """Sample portfolio data fixture"""
    return {
        'timestamp': '2025-09-12T10:00:00',
        'total_value': 10000.0,
        'positions': [
            {'asset': 'BTC', 'amount': 0.2, 'value': 8000.0, 'percentage': 80.0},
            {'asset': 'ETH', 'amount': 1.0, 'value': 1500.0, 'percentage': 15.0},
            {'asset': 'USDT', 'amount': 500.0, 'value': 500.0, 'percentage': 5.0}
        ]
    }


@pytest.fixture
def sample_preferences():
    """Sample preferences data fixture"""
    return {
        'soft_risk': 0.05,
        'hard_risk': 0.10,
        'order_type': 'MARKET',
        'auto_save': True,
        'log_level': 'INFO'
    }


@pytest.fixture
def sample_fav_coins():
    """Sample favorite coins data fixture"""
    return {
        'coins': [
            {'symbol': 'BTCUSDT', 'name': 'Bitcoin'},
            {'symbol': 'ETHUSDT', 'name': 'Ethereum'},
            {'symbol': 'ADAUSDT', 'name': 'Cardano'}
        ],
        'dynamic_coin': [
            {'symbol': 'DOGEUSDT', 'name': 'Dogecoin'}
        ]
    }


@pytest.fixture
def mock_data_manager():
    """Mock data manager fixture"""
    data_manager = Mock()
    
    # Mock save methods
    data_manager.save_trade.return_value = True
    data_manager.save_portfolio.return_value = True
    data_manager.save_preferences.return_value = True
    
    # Mock load methods
    data_manager.load_trades.return_value = []
    data_manager.load_portfolio.return_value = {}
    data_manager.load_preferences.return_value = {}
    
    return data_manager


@pytest.fixture
def temp_file_path(tmp_path):
    """Temporary file path fixture"""
    return tmp_path / "test_file.json"


@pytest.fixture
def mock_environment_variables(monkeypatch):
    """Mock environment variables fixture"""
    monkeypatch.setenv('BINANCE_API_KEY', 'test_api_key')
    monkeypatch.setenv('BINANCE_SECRET_KEY', 'test_secret_key')


@pytest.fixture
def current_timestamp():
    """Current timestamp fixture"""
    return datetime.now().isoformat()


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Auto-use fixture to setup test environment"""
    # Setup test environment before each test
    original_cwd = os.getcwd()
    
    yield
    
    # Cleanup after each test
    os.chdir(original_cwd)


# Pytest configuration
def pytest_configure(config):
    """Pytest configuration"""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow running"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection"""
    for item in items:
        # Add unit marker to all tests by default
        if not any(item.iter_markers()):
            item.add_marker(pytest.mark.unit)


# Custom assertions
def assert_trade_data_valid(trade_data):
    """Assert that trade data is valid"""
    required_fields = [
        'timestamp', 'symbol', 'side', 'type', 'quantity',
        'price', 'total_cost', 'order_id', 'order_type', 'status'
    ]
    
    for field in required_fields:
        assert field in trade_data, f"Missing required field: {field}"
    
    assert trade_data['side'] in ['BUY', 'SELL'], "Invalid trade side"
    assert trade_data['quantity'] > 0, "Quantity must be positive"
    assert trade_data['price'] > 0, "Price must be positive"
    assert trade_data['total_cost'] > 0, "Total cost must be positive"


def assert_portfolio_data_valid(portfolio_data):
    """Assert that portfolio data is valid"""
    required_fields = ['timestamp', 'total_value', 'positions']
    
    for field in required_fields:
        assert field in portfolio_data, f"Missing required field: {field}"
    
    assert portfolio_data['total_value'] >= 0, "Total value must be non-negative"
    assert isinstance(portfolio_data['positions'], list), "Positions must be a list"
    
    for position in portfolio_data['positions']:
        assert 'asset' in position, "Position missing asset field"
        assert 'amount' in position, "Position missing amount field"
        assert 'value' in position, "Position missing value field"
        assert position['amount'] >= 0, "Position amount must be non-negative"
        assert position['value'] >= 0, "Position value must be non-negative"


# Export custom assertions for use in tests
pytest.assert_trade_data_valid = assert_trade_data_valid
pytest.assert_portfolio_data_valid = assert_portfolio_data_valid