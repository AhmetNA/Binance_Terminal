import unittest
from unittest.mock import Mock, patch
from src.services.order_service import get_buy_preferences, prepare_client


class TestOrderService(unittest.TestCase):
    
    @patch('src.services.order_service.open')
    def test_get_buy_preferences(self, mock_open):
        # Mock file content
        mock_file_content = """
        # Preferences file
        soft_risk = 5%
        hard_risk = 10%
        """
        mock_open.return_value.__enter__.return_value.readlines.return_value = mock_file_content.split('\n')
        
        soft_risk, hard_risk = get_buy_preferences()
        
        self.assertEqual(soft_risk, 0.05)
        self.assertEqual(hard_risk, 0.10)
    
    @patch('src.services.order_service.load_dotenv')
    @patch('src.services.order_service.Client')
    def test_prepare_client(self, mock_client, mock_load_dotenv):
        # Test client preparation
        mock_client_instance = Mock()
        mock_client.return_value = mock_client_instance
        
        client = prepare_client()
        
        self.assertIsNotNone(client)
        mock_load_dotenv.assert_called_once()


if __name__ == '__main__':
    unittest.main()
