"""
preferences_manager.py
This module handles the loading and caching of user preferences, specifically risk levels.
It provides module-level caching for efficient preference retrieval and includes functions
for reloading preferences when settings change.
"""

import logging
import os
import sys

# Import centralized paths
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.paths import PREFERENCES_FILE

# Module-level cache for preferences
_CACHED_PREFERENCES = None
_PREFERENCE_CACHE_TIME = None

def _load_preferences_once():
    """
    @brief Preferences'ları bir kez yükler ve cache'ler - module seviyesinde
    @return tuple: (soft_risk, hard_risk)
    """
    global _CACHED_PREFERENCES
    
    if _CACHED_PREFERENCES is not None:
        return _CACHED_PREFERENCES
    
    try:
        with open(PREFERENCES_FILE, "r") as file:
            soft_risk = None
            hard_risk = None
            for line in file:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("soft_risk"):
                    soft_risk = float(line.split("=")[1].strip().replace("%", "")) / 100
                elif line.startswith("hard_risk"):
                    hard_risk = float(line.split("=")[1].strip().replace("%", "")) / 100
        
        if soft_risk is None or hard_risk is None:
            raise ValueError("Risk ayarları tam olarak okunamadı!")
            
        _CACHED_PREFERENCES = (soft_risk, hard_risk)
        logging.info(f"Preferences cached at module level: soft_risk={soft_risk:.1%}, hard_risk={hard_risk:.1%}")
        return _CACHED_PREFERENCES
        
    except Exception as e:
        logging.error(f"Error loading preferences: {e}")
        # Fallback değerler
        _CACHED_PREFERENCES = (0.10, 0.20)  # %10 soft, %20 hard
        logging.warning(f"Using fallback preferences: {_CACHED_PREFERENCES}")
        return _CACHED_PREFERENCES

def get_buy_preferences():
    """
    @brief Returns cached preferences - super fast!
    @return tuple: A tuple containing soft risk and hard risk percentages.
    """
    global _CACHED_PREFERENCES
    
    # Cache'den döndür - çok hızlı!
    if _CACHED_PREFERENCES is None:
        _CACHED_PREFERENCES = _load_preferences_once()
    
    return _CACHED_PREFERENCES


def reload_preferences():
    """
    @brief Forces reload of preferences from file
    @return tuple: (soft_risk, hard_risk)
    """
    global _CACHED_PREFERENCES
    _CACHED_PREFERENCES = None
    return _load_preferences_once()


def force_preferences_reload():
    """
    @brief Public function to force reload preferences - used by UI/settings
    @return tuple: (soft_risk, hard_risk)
    """
    logging.info("🔄 Forcing preferences reload due to settings change")
    return reload_preferences()


def get_cached_preferences_info():
    """
    @brief Returns information about current cached preferences
    @return dict: Cache status and values
    """
    global _CACHED_PREFERENCES
    return {
        'is_cached': _CACHED_PREFERENCES is not None,
        'values': _CACHED_PREFERENCES,
        'soft_risk_percent': f"{_CACHED_PREFERENCES[0]:.1%}" if _CACHED_PREFERENCES else None,
        'hard_risk_percent': f"{_CACHED_PREFERENCES[1]:.1%}" if _CACHED_PREFERENCES else None
    }


def clear_preferences_cache():
    """
    @brief Clears the preferences cache - useful for testing or reset operations
    """
    global _CACHED_PREFERENCES
    _CACHED_PREFERENCES = None
    logging.info("🧹 Preferences cache cleared")


def get_preferences_file_path():
    """
    @brief Returns the path to the preferences file
    @return str: Path to preferences file
    """
    return PREFERENCES_FILE


def validate_preferences_file():
    """
    @brief Validates that the preferences file exists and is readable
    @return tuple: (is_valid: bool, error_message: str or None)
    """
    try:
        if not os.path.exists(PREFERENCES_FILE):
            return False, f"Preferences file not found: {PREFERENCES_FILE}"
        
        if not os.path.isfile(PREFERENCES_FILE):
            return False, f"Preferences path is not a file: {PREFERENCES_FILE}"
        
        if not os.access(PREFERENCES_FILE, os.R_OK):
            return False, f"Preferences file is not readable: {PREFERENCES_FILE}"
        
        # Try to load preferences to validate content
        try:
            _load_preferences_once()
            return True, None
        except Exception as e:
            return False, f"Invalid preferences file content: {str(e)}"
            
    except Exception as e:
        return False, f"Error validating preferences file: {str(e)}"
