import unittest
from unittest.mock import patch, Mock
import requests
from src.api.client import BinanceClient


class TestApiClient(unittest.TestCase):
    
    def setUp(self):
        self.client = BinanceClient()
    
    @patch('requests.get')
    def test_get_price_success(self, mock_get):
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'price': '50000.00'}
        mock_get.return_value = mock_response
        
        price = self.client.get_price('BTCUSDT')
        
        self.assertEqual(price, 50000.00)
        mock_get.assert_called_once()
    
    @patch('requests.get')
    def test_get_price_failure(self, mock_get):
        # Mock failed API response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        with self.assertRaises(Exception):
            self.client.get_price('INVALIDCOIN')


if __name__ == '__main__':
    unittest.main()
