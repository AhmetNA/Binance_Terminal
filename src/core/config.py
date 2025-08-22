# config.py
# Tüm paketlerde ortak kullanılan global sabitler ve değişkenler burada tutulur.
# Path tanımları artık paths.py modülünden import edilir.

import os
import sys
from .paths import (
    PREFERENCES_FILE, FAV_COINS_FILE, SETTINGS_DIR, PROJECT_ROOT, SRC_DIR,
    FAVORITE_COIN_COUNT, DYNAMIC_COIN_INDEX, USDT, TICKER_SUFFIX,
    RECONNECT_DELAY, COINS_KEY, DYNAMIC_COIN_KEY
)

# Backwards compatibility için eski sabitler
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# WebSocket ve Price_Update için global değişkenler
SYMBOLS = []  # WebSocket için abone olunan coin sembolleri
pending_subscriptions = []
