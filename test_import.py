#!/usr/bin/env python3

import sys
import os

# Add src to path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

print(f"Current directory: {current_dir}")
print(f"Source directory: {src_dir}")
print(f"Source directory exists: {os.path.exists(src_dir)}")

try:
    from core.config import TICKER_SUFFIX
    print(f"✅ Successfully imported TICKER_SUFFIX: {TICKER_SUFFIX}")
except ImportError as e:
    print(f"❌ Failed to import TICKER_SUFFIX: {e}")

try:
    from utils.symbol_utils import format_binance_ticker_symbols
    print("✅ Successfully imported format_binance_ticker_symbols")
    
    # Test the function
    test_symbols = ['BTCUSDT', 'ETHUSDT']
    result = format_binance_ticker_symbols(test_symbols)
    print(f"✅ Function test successful: {result}")
    
except ImportError as e:
    print(f"❌ Failed to import format_binance_ticker_symbols: {e}")

try:
    from utils.data_utils import load_fav_coins
    print("✅ Successfully imported load_fav_coins")
except ImportError as e:
    print(f"❌ Failed to import load_fav_coins: {e}")
