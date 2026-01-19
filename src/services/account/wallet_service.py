"""
wallet_service.py
Wallet balance bilgilerini almak ve işlemek için modüler servis.
Coin miktarını ve USDT karşılığını hesaplar.
"""

import logging
from services.binance_client import prepare_client
from services.account.account_service import get_amountOf_asset
from services.orders.market_order_service import get_current_price
from concurrent.futures import ThreadPoolExecutor, as_completed


def get_coin_wallet_info(symbol, client=None):
    """
    Belirtilen coinin wallet'taki miktarını ve USDT karşılığını getirir.

    Args:
        symbol (str): Coin symbol (örn: BTCUSDT, ETHUSDT)
        client: Binance client instance (None ise otomatik alınır)

    Returns:
        dict: {
            'coin_symbol': str,
            'amount': float,
            'usdt_value': float,
            'current_price': float
        }
    """
    if client is None:
        try:
            client = prepare_client()
        except Exception as e:
            logging.error(f"Client preparation failed: {e}")
            return {
                "coin_symbol": symbol,
                "amount": 0.0,
                "usdt_value": 0.0,
                "current_price": 0.0,
                "error": "Client connection failed",
            }

    try:
        # Base asset'i symbol'dan çıkar
        if symbol.endswith("USDT"):
            base_asset = symbol[:-4]
        elif symbol.endswith("BTC"):
            base_asset = symbol[:-3]
        elif symbol.endswith("ETH"):
            base_asset = symbol[:-3]
        else:
            base_asset = symbol

        # Coin miktarını al
        coin_amount = get_amountOf_asset(client, symbol)

        # Eğer USDT ise direkt USDT değeri
        if symbol == "USDTUSDT" or base_asset == "USDT":
            return {
                "coin_symbol": base_asset,
                "amount": coin_amount,
                "usdt_value": coin_amount,
                "current_price": 1.0,
            }

        # Güncel fiyatı al
        current_price = get_current_price(symbol, client)

        # USDT karşılığını hesapla
        usdt_value = coin_amount * current_price if current_price > 0 else 0.0

        return {
            "coin_symbol": base_asset,
            "amount": coin_amount,
            "usdt_value": usdt_value,
            "current_price": current_price,
        }

    except Exception as e:
        error_msg = f"Error getting wallet info for {symbol}: {e}"
        logging.error(error_msg)
        return {
            "coin_symbol": symbol,
            "amount": 0.0,
            "usdt_value": 0.0,
            "current_price": 0.0,
            "error": error_msg,
        }


def format_wallet_display_text(wallet_info):
    """
    Wallet bilgilerini kullanıcı dostu formatda döndürür.

    Args:
        wallet_info (dict): get_coin_wallet_info() fonksiyonundan dönen bilgi

    Returns:
        str: Formatlı wallet bilgisi
    """
    if "error" in wallet_info:
        return "Wallet Info: Error loading"

    coin_symbol = wallet_info["coin_symbol"]
    amount = wallet_info["amount"]
    usdt_value = wallet_info["usdt_value"]

    if amount == 0:
        return f"Wallet: 0 {coin_symbol}"

    # Format numbers for better readability
    if amount >= 1:
        amount_str = f"{amount:.6f}".rstrip("0").rstrip(".")
    else:
        amount_str = f"{amount:.8f}".rstrip("0").rstrip(".")

    if usdt_value >= 1:
        usdt_str = f"{usdt_value:.2f}"
    else:
        usdt_str = f"{usdt_value:.6f}".rstrip("0").rstrip(".")

    return f"Wallet: {amount_str} {coin_symbol} (~${usdt_str})"


if __name__ == "__main__":
    """Test wallet service functions"""
    print("🚀 Testing Wallet Service")
    print("=" * 30)

    try:
        # Test BTC wallet info
        btc_info = get_coin_wallet_info("BTCUSDT")
        print(f"BTC Wallet Info: {btc_info}")

        # Test formatted display
        display_text = format_wallet_display_text(btc_info)
        print(f"Formatted Display: {display_text}")

        print("\n✅ Wallet service test completed successfully!")

    except Exception as e:
        print(f"❌ Test failed: {e}")

# --- WALLET CACHE IMPLEMENTATION ---

class WalletCache:
    """
    Simple in-memory cache for wallet balances to avoid blocking API calls.
    Stores {symbol: {'amount': float, 'usdt_value': float, ...}}
    """
    _instance = None
    _data = {}
    _initialized = False

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = WalletCache()
        return cls._instance

    def update(self, symbol, info):
        """Update cache for a specific symbol."""
        self._data[symbol] = info

    def get(self, symbol):
        """Get cached info for a symbol."""
        return self._data.get(symbol)

    def get_all(self):
        return self._data

    def clear(self):
        self._data = {}
        self._initialized = False

def initialize_wallet_cache(client, symbols):
    """
    Populates the wallet cache for the given list of symbols.
    Should be called at startup or in a background thread.
    """
    cache = WalletCache.get_instance()
    logging.info(f"Initializing wallet cache for {len(symbols)} symbols...")
    
    count = 0
    # Use ThreadPoolExecutor to fetch wallet info in parallel
    # 10 workers is usually a safe number for light IO tasks like this
    max_workers = min(10, len(symbols)) if symbols else 1
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Create a future for each symbol
        future_to_symbol = {
            executor.submit(get_coin_wallet_info, symbol, client): symbol 
            for symbol in symbols
        }
        
        for future in as_completed(future_to_symbol):
            symbol = future_to_symbol[future]
            try:
                info = future.result()
                cache.update(symbol, info)
                count += 1
            except Exception as e:
                logging.error(f"Failed to cache wallet info for {symbol}: {e}")
            
    cache._initialized = True
    logging.info(f"Wallet cache initialized with {count} items.")

def update_wallet_cache_item(symbol, client=None):
    """
    Refreshes the cache for a single symbol (e.g., after a trade).
    """
    cache = WalletCache.get_instance()
    info = get_coin_wallet_info(symbol, client)
    cache.update(symbol, info)
    return info

def get_cached_wallet_info(symbol):
    """
    Retrieves wallet info from cache. Returns None if not found,
    or a default 'empty' structure if preferred.
    """
    cache = WalletCache.get_instance()
    cached = cache.get(symbol)
    
    if cached:
        return cached
    
    # Fallback or indicate not cached
    # For now, return None so the caller knows it's missing
    return None
