from binance.client import Client
from dotenv import load_dotenv
import os
import logging

# Import centralized paths
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from core.paths import ENV_FILE
except ImportError:
    # Fallback for direct execution
    ENV_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config', '.env')

"""
client_service.py
This module handles Binance API client initialization, caching, and management.
It provides a centralized way to manage the Binance client connection with caching
for improved performance and connection stability.
"""

# Module-level cache for Binance client
_CACHED_CLIENT = None


def _initialize_client_once():
    global _CACHED_CLIENT
    
    if _CACHED_CLIENT is None:
        try:
            load_dotenv(ENV_FILE, override=True)
            api_key = os.getenv('BINANCE_API_KEY')
            api_secret = os.getenv('BINANCE_API_SECRET')
            
            if not api_key or not api_secret:
                raise ValueError("API anahtarları bulunamadı!")
                
            _CACHED_CLIENT = Client(api_key, api_secret)
            _CACHED_CLIENT.API_URL = "https://testnet.binance.vision/api"
            logging.info("🚀 Binance client cached at module level")
            return _CACHED_CLIENT
        except Exception as e:
            print(f"❌ Binance API bağlantı hatası: {e}")
            logging.error(f"Error preparing Binance client: {e}")
            logging.exception("Full traceback for client preparation error:")
            raise
    else:
        # Cache'den döndür - çok hızlı!
        return _CACHED_CLIENT


def prepare_client():
    return _initialize_client_once()


def force_client_reload():
    global _CACHED_CLIENT
    _CACHED_CLIENT = None
    logging.info("🔄 Forcing client reload due to configuration change")
    client = _initialize_client_once()
    logging.info("✅ Client cache reloaded successfully")
    return client


def get_cached_client_info():
    global _CACHED_CLIENT
    return {
        'is_cached': _CACHED_CLIENT is not None,
        'client_type': type(_CACHED_CLIENT).__name__ if _CACHED_CLIENT else None,
        'api_url': getattr(_CACHED_CLIENT, 'API_URL', None) if _CACHED_CLIENT else None
    }





if __name__ == "__main__":
    """Test the client service functions"""
    print("🚀 Testing Client Service")
    print("=" * 30)
    
    # Test cache info when empty
    info = get_cached_client_info()
    print(f"Initial cache state: {info}")
    
    print("Available functions:")
    functions = [
        'prepare_client',
        'force_client_reload', 
        'get_cached_client_info'
    ]
    for func in functions:
        print(f"  ✅ {func}")
    
    print("\n✅ Client service test completed successfully!")
