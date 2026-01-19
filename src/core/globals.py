# globals.py
# Tüm paketlerde ortak kullanılan global sabitler ve değişkenler burada tutulur.
# Path tanımları artık paths.py modülünden import edilir.

import os

# Backwards compatibility için eski sabitler
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# WebSocket ve Price_Update için global değişkenler
SYMBOLS = []  # WebSocket için abone olunan coin sembolleri
pending_subscriptions = []

# Trading constants
USDT = "USDT"
TICKER_SUFFIX = "@ticker"
RECONNECT_DELAY = 5
COINS_KEY = "coins"
DYNAMIC_COIN_KEY = "dynamic_coin"

# Import paths for backwards compatibility
from core.paths import FAV_COINS_FILE, PREFERENCES_FILE

__all__ = [
    "COINS_KEY",
    "DYNAMIC_COIN_KEY",
    "FAV_COINS_FILE",
    "PREFERENCES_FILE",
]
