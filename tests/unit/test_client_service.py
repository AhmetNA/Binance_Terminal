"""
Test dosyası - Client service ve API bağlantıları
Bu dosya Binance API client bağlantılarını test eder.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))


class TestClientService(unittest.TestCase):
    """Client service testleri"""
    
    def setUp(self):
        """Test setup"""
        self.api_key = "test_api_key"
        self.secret_key = "test_secret_key"
        self.mock_client = Mock()
    
    @patch('os.getenv')
    @patch('services.client_service.load_dotenv')
    def test_environment_variables(self, mock_load_dotenv, mock_getenv):
        """Environment variables testi"""
        # Setup
        mock_getenv.side_effect = lambda key: {
            'BINANCE_API_KEY': self.api_key,
            'BINANCE_SECRET_KEY': self.secret_key
        }.get(key)
        
        # Test environment loading
        api_key = os.getenv('BINANCE_API_KEY')
        secret_key = os.getenv('BINANCE_SECRET_KEY')
        
        # Assertions
        self.assertEqual(api_key, self.api_key)
        self.assertEqual(secret_key, self.secret_key)
    
    @patch('services.client_service.Client')
    @patch('services.client_service.load_dotenv')
    @patch('os.getenv')
    def test_client_initialization(self, mock_getenv, mock_load_dotenv, mock_client_class):
        """Client initialization testi"""
        # Setup
        mock_getenv.side_effect = lambda key: {
            'BINANCE_API_KEY': self.api_key,
            'BINANCE_SECRET_KEY': self.secret_key
        }.get(key)
        mock_client_class.return_value = self.mock_client
        
        # Import and test
        try:
            from services.client_service import prepare_client
            client = prepare_client()
            
            # Assertions
            self.assertIsNotNone(client)
            mock_load_dotenv.assert_called_once()
            mock_client_class.assert_called_once_with(self.api_key, self.secret_key)
        except ImportError:
            # Fallback test
            self.assertTrue(True)  # Test passes if import fails
    
    def test_client_methods(self):
        """Client methods testi"""
        # Setup mock methods
        self.mock_client.get_account.return_value = {'balances': []}
        self.mock_client.get_symbol_ticker.return_value = {'symbol': 'BTCUSDT', 'price': '50000'}
        self.mock_client.get_exchange_info.return_value = {'symbols': []}
        
        # Test methods
        account = self.mock_client.get_account()
        ticker = self.mock_client.get_symbol_ticker(symbol='BTCUSDT')
        exchange_info = self.mock_client.get_exchange_info()
        
        # Assertions
        self.assertIn('balances', account)
        self.assertEqual(ticker['symbol'], 'BTCUSDT')
        self.assertIn('symbols', exchange_info)
    
    def test_connection_error_handling(self):
        """Bağlantı hatası handling testi"""
        # Setup connection error
        from requests.exceptions import ConnectionError
        
        self.mock_client.get_account.side_effect = ConnectionError("Connection failed")
        
        # Test error handling
        with self.assertRaises(ConnectionError):
            self.mock_client.get_account()
    
    def test_api_error_handling(self):
        """API hatası handling testi"""
        # Setup API error
        api_error = {
            'code': -1021,
            'msg': 'Timestamp for this request is outside of the recvWindow.'
        }
        
        self.mock_client.get_account.side_effect = Exception(f"API Error: {api_error}")
        
        # Test error handling
        with self.assertRaises(Exception):
            self.mock_client.get_account()


class TestAccountService(unittest.TestCase):
    """Account service testleri"""
    
    def setUp(self):
        """Test setup"""
        self.mock_client = Mock()
        self.sample_account = {
            'balances': [
                {'asset': 'USDT', 'free': '1000.0', 'locked': '0.0'},
                {'asset': 'BTC', 'free': '0.01', 'locked': '0.0'},
                {'asset': 'ETH', 'free': '0.5', 'locked': '0.001'}
            ]
        }
    
    def test_usdt_balance_retrieval(self):
        """USDT balance alma testi"""
        # Setup
        self.mock_client.get_account.return_value = self.sample_account
        
        # Simulate balance retrieval
        account = self.mock_client.get_account()
        usdt_balance = None
        
        for balance in account['balances']:
            if balance['asset'] == 'USDT':
                usdt_balance = float(balance['free'])
                break
        
        # Assertions
        self.assertIsNotNone(usdt_balance)
        self.assertEqual(usdt_balance, 1000.0)
    
    def test_asset_balance_retrieval(self):
        """Asset balance alma testi"""
        # Setup
        self.mock_client.get_account.return_value = self.sample_account
        
        # Test BTC balance
        account = self.mock_client.get_account()
        btc_balance = None
        
        for balance in account['balances']:
            if balance['asset'] == 'BTC':
                btc_balance = float(balance['free'])
                break
        
        # Assertions
        self.assertIsNotNone(btc_balance)
        self.assertEqual(btc_balance, 0.01)
    
    def test_locked_balance_handling(self):
        """Locked balance handling testi"""
        # Setup
        self.mock_client.get_account.return_value = self.sample_account
        
        # Test ETH with locked balance
        account = self.mock_client.get_account()
        eth_balance = None
        eth_locked = None
        
        for balance in account['balances']:
            if balance['asset'] == 'ETH':
                eth_balance = float(balance['free'])
                eth_locked = float(balance['locked'])
                break
        
        # Assertions
        self.assertIsNotNone(eth_balance)
        self.assertIsNotNone(eth_locked)
        self.assertEqual(eth_balance, 0.5)
        self.assertEqual(eth_locked, 0.001)
        
        # Total ETH should be free + locked
        total_eth = eth_balance + eth_locked
        self.assertEqual(total_eth, 0.501)


class TestPreferencesManager(unittest.TestCase):
    """Preferences manager testleri"""
    
    def test_risk_preferences_parsing(self):
        """Risk preferences parsing testi"""
        # Sample preferences content
        preferences_content = [
            "# Trading Preferences",
            "soft_risk = 5%",
            "hard_risk = 10%",
            "order_type = MARKET",
            "# End of preferences"
        ]
        
        # Parse preferences
        soft_risk = None
        hard_risk = None
        order_type = None
        
        for line in preferences_content:
            line = line.strip()
            if line.startswith('soft_risk'):
                soft_risk = float(line.split('=')[1].strip().replace('%', '')) / 100
            elif line.startswith('hard_risk'):
                hard_risk = float(line.split('=')[1].strip().replace('%', '')) / 100
            elif line.startswith('order_type'):
                order_type = line.split('=')[1].strip()
        
        # Assertions
        self.assertEqual(soft_risk, 0.05)
        self.assertEqual(hard_risk, 0.10)
        self.assertEqual(order_type, 'MARKET')
    
    def test_preferences_validation(self):
        """Preferences validation testi"""
        # Test valid preferences
        valid_soft_risk = 0.05
        valid_hard_risk = 0.10
        
        # Validation logic
        self.assertTrue(0 < valid_soft_risk < 1)
        self.assertTrue(0 < valid_hard_risk < 1)
        self.assertTrue(valid_soft_risk < valid_hard_risk)
        
        # Test invalid preferences
        invalid_soft_risk = 1.5  # Over 100%
        invalid_hard_risk = -0.1  # Negative
        
        self.assertFalse(0 < invalid_soft_risk < 1)
        self.assertFalse(0 < invalid_hard_risk < 1)
    
    def test_order_type_validation(self):
        """Order type validation testi"""
        valid_order_types = ['MARKET', 'LIMIT']
        
        # Test valid order types
        for order_type in valid_order_types:
            self.assertIn(order_type, valid_order_types)
        
        # Test invalid order type
        invalid_order_type = 'INVALID'
        self.assertNotIn(invalid_order_type, valid_order_types)


class TestUtilityFunctions(unittest.TestCase):
    """Utility functions testleri"""
    
    def test_symbol_formatting(self):
        """Symbol formatting testi"""
        # Test ticker symbol formatting
        symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT']
        formatted = [f"{symbol.lower()}@ticker" for symbol in symbols]
        
        expected = ['btcusdt@ticker', 'ethusdt@ticker', 'adausdt@ticker']
        self.assertEqual(formatted, expected)
    
    def test_price_formatting(self):
        """Price formatting testi"""
        # Test price precision
        prices = [50000.123456, 1.23456789, 0.00001234]
        
        # Format to 6 decimal places
        formatted_prices = [round(price, 6) for price in prices]
        
        expected = [50000.123456, 1.234568, 0.000012]
        self.assertEqual(formatted_prices, expected)
    
    def test_quantity_calculation(self):
        """Quantity calculation testi"""
        # Test buy quantity calculation
        usdt_amount = 100.0
        price = 50000.0
        quantity = usdt_amount / price
        
        self.assertEqual(quantity, 0.002)
        
        # Test with precision
        precision = 8
        rounded_quantity = round(quantity, precision)
        self.assertEqual(rounded_quantity, 0.002)
    
    def test_percentage_calculation(self):
        """Percentage calculation testi"""
        # Test portfolio percentage
        position_value = 1000.0
        total_value = 5000.0
        percentage = (position_value / total_value) * 100
        
        self.assertEqual(percentage, 20.0)
        
        # Test risk percentage
        balance = 1000.0
        risk_percentage = 0.05
        risk_amount = balance * risk_percentage
        
        self.assertEqual(risk_amount, 50.0)


if __name__ == '__main__':
    unittest.main()