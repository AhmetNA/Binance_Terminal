"""
paths.py

Binance Terminal uygulamasında kullanılan tüm dosya ve dizin yollarını tanımlayan merkezi path modülü.
Bu modül sayesinde tüm path tanımları tek yerde tutulur ve diğer dosyalarda import edilerek kullanılır.

Kullanım:
    from core.paths import PREFERENCES_FILE, SETTINGS_DIR, PROJECT_ROOT
    
Özellikler:
    - Portable path handling (Windows/Linux/Mac uyumlu)
    - PyInstaller bundle desteği
    - Automatic directory creation
    - Clear naming conventions
"""

import os
import sys
import logging

# ===== BASE DIRECTORIES =====

def get_current_dir():
    """Mevcut modülün bulunduğu dizini döndürür."""
    return os.path.dirname(os.path.abspath(__file__))

def get_src_dir():
    """src/ dizininin yolunu döndürür."""
    return os.path.abspath(os.path.join(get_current_dir(), '..'))

def get_project_root():
    """Proje kök dizininin yolunu döndürür."""
    return os.path.abspath(os.path.join(get_src_dir(), '..'))

# Base directory paths
CURRENT_DIR = get_current_dir()
SRC_DIR = get_src_dir()
PROJECT_ROOT = get_project_root()

# ===== CONFIGURATION DIRECTORIES =====

def get_settings_dir():
    """
    Settings/config dizininin yolunu döndürür.
    PyInstaller bundle için özel handling yapar.
    """
    # Determine if running as a bundled executable
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # Running in a PyInstaller bundle
        return os.path.dirname(sys.executable)
    else:
        # Running in a normal Python environment
        return os.path.join(PROJECT_ROOT, 'config')

# Configuration directory
SETTINGS_DIR = get_settings_dir()
CONFIG_DIR = SETTINGS_DIR  # Alias for backwards compatibility

# ===== DATA DIRECTORIES =====

# Main data directory
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')

# Data subdirectories
TRADES_DIR = os.path.join(DATA_DIR, 'trades')
PORTFOLIO_DIR = os.path.join(DATA_DIR, 'portfolio')
ANALYTICS_DIR = os.path.join(DATA_DIR, 'analytics')

# ===== LOG DIRECTORIES =====

LOGS_DIR = os.path.join(PROJECT_ROOT, 'logs')

# ===== ASSETS DIRECTORIES =====

ASSETS_DIR = os.path.join(PROJECT_ROOT, 'assets')

# ===== CONFIGURATION FILES =====

# Main configuration files
PREFERENCES_FILE = os.path.join(SETTINGS_DIR, 'Preferences.txt')
FAV_COINS_FILE = os.path.join(SETTINGS_DIR, 'fav_coins.json')
ENV_FILE = os.path.join(SETTINGS_DIR, '.env')

# ===== DATA FILES =====

# Portfolio files
LATEST_PORTFOLIO_FILE = os.path.join(PORTFOLIO_DIR, 'latest_portfolio.json')

# Log files
MAIN_LOG_FILE = os.path.join(LOGS_DIR, 'binance_terminal.log')
DEBUG_LOG_FILE = os.path.join(LOGS_DIR, 'binance_terminal_debug.log')
BUGS_LOG_FILE = os.path.join(LOGS_DIR, 'binance_terminal_bugs.log')

# Root log file (legacy support)
ROOT_LOG_FILE = os.path.join(PROJECT_ROOT, 'binance_terminal.log')

# ===== ASSET FILES =====

# Icons and images
BTC_ICON_FILE = os.path.join(ASSETS_DIR, 'btc.png')

# ===== HELPER FUNCTIONS =====

def ensure_directories():
    """
    Gerekli tüm dizinleri oluşturur.
    Uygulama başlangıcında çağrılması önerilir.
    """
    directories_to_create = [
        SETTINGS_DIR,
        DATA_DIR,
        TRADES_DIR,
        PORTFOLIO_DIR,
        ANALYTICS_DIR,
        LOGS_DIR,
        ASSETS_DIR
    ]
    
    for directory in directories_to_create:
        try:
            os.makedirs(directory, exist_ok=True)
            logging.debug(f"Directory ensured: {directory}")
        except Exception as e:
            logging.error(f"Failed to create directory {directory}: {e}")

def get_daily_trades_file(date_str: str = None) -> str:
    """
    Belirli bir tarih için trades dosyasının yolunu döndürür.
    
    Args:
        date_str: YYYY-MM-DD formatında tarih. None ise bugünün tarihi kullanılır.
    
    Returns:
        str: Trades dosyasının tam yolu
    """
    if date_str is None:
        from datetime import datetime
        date_str = datetime.now().strftime('%Y-%m-%d')
    
    return os.path.join(TRADES_DIR, f'trades_{date_str}.json')

def get_daily_portfolio_file(date_str: str = None) -> str:
    """
    Belirli bir tarih için portfolio dosyasının yolunu döndürür.
    
    Args:
        date_str: YYYY-MM-DD formatında tarih. None ise bugünün tarihi kullanılır.
    
    Returns:
        str: Portfolio dosyasının tam yolu
    """
    if date_str is None:
        from datetime import datetime
        date_str = datetime.now().strftime('%Y-%m-%d')
    
    return os.path.join(PORTFOLIO_DIR, f'portfolio_{date_str}.json')

def get_daily_analytics_file(date_str: str = None) -> str:
    """
    Belirli bir tarih için analytics dosyasının yolunu döndürür.
    
    Args:
        date_str: YYYY-MM-DD formatında tarih. None ise bugünün tarihi kullanılır.
    
    Returns:
        str: Analytics dosyasının tam yolu
    """
    if date_str is None:
        from datetime import datetime
        date_str = datetime.now().strftime('%Y-%m-%d')
    
    return os.path.join(ANALYTICS_DIR, f'analytics_{date_str}.json')

# ===== BACKWARDS COMPATIBILITY ALIASES =====

# Legacy constants for backwards compatibility
FAVORITE_COIN_COUNT = 5
DYNAMIC_COIN_INDEX = 6
USDT = "USDT"
TICKER_SUFFIX = "@ticker"
RECONNECT_DELAY = 5
COINS_KEY = "coins"
DYNAMIC_COIN_KEY = "dynamic_coin"

# ===== MODULE INITIALIZATION =====

# Ensure directories exist on import
try:
    ensure_directories()
    logging.debug("Paths module initialized successfully")
except Exception as e:
    logging.error(f"Error initializing paths module: {e}")

# ===== EXPORTS =====

__all__ = [
    # Base directories
    'PROJECT_ROOT', 'SRC_DIR', 'CURRENT_DIR',
    
    # Configuration
    'SETTINGS_DIR', 'CONFIG_DIR',
    
    # Data directories
    'DATA_DIR', 'TRADES_DIR', 'PORTFOLIO_DIR', 'ANALYTICS_DIR',
    
    # Other directories
    'LOGS_DIR', 'ASSETS_DIR',
    
    # Configuration files
    'PREFERENCES_FILE', 'FAV_COINS_FILE', 'ENV_FILE',
    
    # Data files
    'LATEST_PORTFOLIO_FILE',
    
    # Log files
    'MAIN_LOG_FILE', 'DEBUG_LOG_FILE', 'BUGS_LOG_FILE', 'ROOT_LOG_FILE',
    
    # Asset files
    'BTC_ICON_FILE',
    
    # Helper functions
    'ensure_directories', 'get_daily_trades_file', 'get_daily_portfolio_file',
    'get_daily_analytics_file',
    
    # Backwards compatibility
    'FAVORITE_COIN_COUNT', 'DYNAMIC_COIN_INDEX', 'USDT', 'TICKER_SUFFIX',
    'RECONNECT_DELAY', 'COINS_KEY', 'DYNAMIC_COIN_KEY'
]
