# Global_State.py
# Tüm paketlerde ortak kullanılan global sabitler ve değişkenler burada tutulur.
import os
import sys  # Import sys module

# Coin paneli için sabitler
FAVORITE_COIN_COUNT = 5
DYNAMIC_COIN_INDEX = 6

# Dosya yolları
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.abspath(os.path.join(CURRENT_DIR, '..'))

# Determine if running as a bundled executable
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    # Running in a PyInstaller bundle
    SETTINGS_DIR = os.path.dirname(sys.executable)
else:
    # Running in a normal Python environment
    SETTINGS_DIR = os.path.join(APP_DIR, 'settings')

PREFERENCES_FILE = os.path.join(SETTINGS_DIR, 'Preferences.txt')
FAV_COINS_FILE = os.path.join(SETTINGS_DIR, 'fav_coins.json')

# WebSocket ve Price_Update için global değişkenler
SYMBOLS = []  # WebSocket için abone olunan coin sembolleri
pending_subscriptions = []

# Diğer global sabitler (gerekirse eklenebilir)
USDT = "USDT"
TICKER_SUFFIX = "@ticker"
RECONNECT_DELAY = 5
COINS_KEY = "coins"
DYNAMIC_COIN_KEY = "dynamic_coin"
