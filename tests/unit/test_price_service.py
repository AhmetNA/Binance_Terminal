import unittest
import sys
import os
from unittest.mock import patch, Mock

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src'))

from utils.symbol_utils import format_binance_ticker_symbols
from utils.data_utils import load_fav_coins


class TestPriceService(unittest.TestCase):
    
    def test_format_binance_ticker_symbols(self):
        symbols = ['BTCUSDT', 'ETHUSDT']
        formatted = format_binance_ticker_symbols(symbols)
        expected = ['btcusdt@ticker', 'ethusdt@ticker']
        self.assertEqual(formatted, expected)
    
    @patch('utils.data_utils.open')
    @patch('utils.data_utils.json.load')
    def test_load_fav_coins(self, mock_json_load, mock_open):
        # Mock JSON data
        mock_data = {
            'coins': [
                {'symbol': 'BTCUSDT', 'name': 'BTC'},
                {'symbol': 'ETHUSDT', 'name': 'ETH'}
            ],
            'dynamic_coin': [
                {'symbol': 'ADAUSDT', 'name': 'ADA'}
            ]
        }
        mock_json_load.return_value = mock_data
        
        result = load_fav_coins()
        
        self.assertEqual(result, mock_data)
        self.assertIn('coins', result)
        self.assertIn('dynamic_coin', result)


if __name__ == '__main__':
    unittest.main()
