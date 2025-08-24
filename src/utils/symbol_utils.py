"""
symbol_utils.py
Symbol validation ve formatlama utilities.
"""

import logging
import asyncio
import sys
import os

# Add src to path for core imports (optimized)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import TICKER_SUFFIX
from api.http_client import get_http_session


def format_binance_ticker_symbols(symbols):
    """Format symbols for Binance ticker subscription"""
    return [symbol.lower() + TICKER_SUFFIX for symbol in symbols]


def validate_symbol_for_binance(symbol):
    """Validate if a symbol exists on Binance exchange"""
    try:
        # Use the existing event loop if available, otherwise create a new one
        try:
            loop = asyncio.get_running_loop()
            # If we're in an async context, we shouldn't use run_until_complete
            logging.warning("Cannot validate symbol synchronously from async context")
            return True  # Assume valid to avoid blocking
        except RuntimeError:
            # No running loop, safe to create a new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(_validate_symbol_async(symbol))
            finally:
                try:
                    # Properly close pending tasks before closing loop
                    pending = asyncio.all_tasks(loop)
                    for task in pending:
                        task.cancel()
                    if pending:
                        loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                except Exception:
                    pass
                finally:
                    loop.close()
    except Exception as e:
        logging.error(f"Error validating symbol {symbol}: {e}")
        return False


async def _validate_symbol_async(symbol):
    """Async symbol validation against Binance API"""
    try:
        session = await get_http_session()
        url = "https://api.binance.com/api/v3/exchangeInfo"
        
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                valid_symbols = [s['symbol'] for s in data['symbols']]
                return symbol.upper() in valid_symbols
            else:
                logging.error(f"Failed to fetch exchange info: {response.status}")
                return False
    except Exception as e:
        logging.error(f"Error in async symbol validation: {e}")
        return False


def validate_symbol_simple(symbol):
    """Simple symbol validation - checks if it follows common patterns"""
    symbol = symbol.upper()
    
    # Common USDT pairs that are almost always available
    common_symbols = {
        'BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'BNBUSDT', 'XRPUSDT', 
        'SOLUSDT', 'DOGEUSDT', 'AVAXUSDT', 'DOTUSDT', 'MATICUSDT',
        'LINKUSDT', 'LTCUSDT', 'BCHUSDT', 'XLMUSDT', 'UNIUSDT',
        'ATOMUSDT', 'VETUSDT', 'FILUSDT', 'TRXUSDT', 'ETCUSDT',
        'ALGOUSDT', 'AAVEUSDT', 'MKRUSDT', 'COMPUSDT', 'SUSHIUSDT'
    }
    
    if symbol in common_symbols:
        return True
    
    # Basic pattern check: should end with USDT and have valid characters
    if symbol.endswith('USDT') and len(symbol) > 4:
        base_symbol = symbol[:-4]
        if base_symbol.isalpha() and len(base_symbol) >= 2:
            return True
    
    return False


def normalize_symbol(symbol):
    """Normalize symbol format (uppercase)"""
    return symbol.upper() if symbol else ""


def split_symbol_pair(symbol):
    """Split trading pair into base and quote assets"""
    symbol = normalize_symbol(symbol)
    
    # Common quote assets in order of preference
    quote_assets = ['USDT', 'BUSD', 'USDC', 'BTC', 'ETH', 'BNB']
    
    for quote in quote_assets:
        if symbol.endswith(quote):
            base = symbol[:-len(quote)]
            if base:  # Ensure base asset is not empty
                return base, quote
    
    # If no common quote asset found, assume last 3-4 characters are quote
    if len(symbol) > 6:
        return symbol[:-4], symbol[-4:]
    elif len(symbol) > 3:
        return symbol[:-3], symbol[-3:]
    
    return symbol, ""


if __name__ == "__main__":
    """Test symbol utils functions"""
    print("🚀 Testing Symbol Utils")
    print("=" * 30)
    
    # Test symbol formatting
    symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT']
    formatted = format_binance_ticker_symbols(symbols)
    print(f"📊 Formatted symbols: {formatted}")
    
    # Test simple validation
    test_symbols = ['BTCUSDT', 'INVALIDTOKEN', 'ETHUSDT']
    for symbol in test_symbols:
        is_valid = validate_symbol_simple(symbol)
        print(f"✅ {symbol} valid: {is_valid}")
    
    # Test symbol splitting
    test_pairs = ['BTCUSDT', 'ETHBTC', 'ADABNB']
    for pair in test_pairs:
        base, quote = split_symbol_pair(pair)
        print(f"🔄 {pair} -> Base: {base}, Quote: {quote}")
    
    print("\n✅ Symbol utils test completed successfully!")
