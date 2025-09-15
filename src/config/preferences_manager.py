"""
preferences_manager.py
This module handles the loading and caching of user preferences, specifically risk levels.
It provides module-level caching for efficient preference retrieval and includes functions
for reloading preferences when settings change.
"""

import logging
import os
import sys

from core.paths import PREFERENCES_FILE

# Module-level cache for preferences
_CACHED_PREFERENCES = None
_CACHED_ORDER_TYPE = None
_CACHED_RISK_TYPE = None
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
            soft_risk_percentage = None
            hard_risk_percentage = None
            soft_risk_usdt = None
            hard_risk_usdt = None
            risk_type = None
            
            for line in file:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                    
                if line.startswith("risk_type"):
                    risk_type = line.split("=")[1].strip().upper()
                elif line.startswith("soft_risk_percentage"):
                    value = line.split("=")[1].strip()
                    if value.startswith("%"):
                        value = value[1:]
                    soft_risk_percentage = float(value) / 100
                elif line.startswith("hard_risk_percentage"):
                    value = line.split("=")[1].strip()
                    if value.startswith("%"):
                        value = value[1:]
                    hard_risk_percentage = float(value) / 100
                elif line.startswith("soft_risk_by_usdt"):
                    value = line.split("=")[1].strip()
                    if value.endswith("USDT"):
                        value = value[:-4]
                    soft_risk_usdt = float(value)
                elif line.startswith("hard_risk_by_usdt"):
                    value = line.split("=")[1].strip()
                    if value.endswith("USDT"):
                        value = value[:-4]
                    hard_risk_usdt = float(value)
        
        # Risk type'a göre doğru değerleri seç
        if risk_type == "PERCENTAGE":
            soft_risk = soft_risk_percentage
            hard_risk = hard_risk_percentage
        elif risk_type == "USDT":
            soft_risk = soft_risk_usdt
            hard_risk = hard_risk_usdt
        else:
            # Default PERCENTAGE
            soft_risk = soft_risk_percentage
            hard_risk = hard_risk_percentage
        
        if soft_risk is None or hard_risk is None:
            raise ValueError("Risk ayarları tam olarak okunamadı!")
            
        _CACHED_PREFERENCES = (soft_risk, hard_risk)
        logging.info(f"Preferences cached at module level: soft_risk={soft_risk}, hard_risk={hard_risk} (risk_type: {risk_type})")
        return _CACHED_PREFERENCES
        
    except Exception as e:
        logging.error(f"Error loading preferences: {e}")
        # Fallback değerler
        _CACHED_PREFERENCES = (0.10, 0.20)  # %10 soft, %20 hard
        logging.warning(f"Using fallback preferences: {_CACHED_PREFERENCES}")
        return _CACHED_PREFERENCES


def _load_order_type_once():
    """
    @brief Order type'ı bir kez yükler ve cache'ler - module seviyesinde
    @return str: Order type ("MARKET" veya "LIMIT")
    """
    global _CACHED_ORDER_TYPE
    
    if _CACHED_ORDER_TYPE is not None:
        return _CACHED_ORDER_TYPE
    
    try:
        with open(PREFERENCES_FILE, "r") as file:
            order_type = None
            for line in file:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("order_type"):
                    order_type = line.split("=")[1].strip().upper()
                    break
        
        # Geçerli order type kontrolü
        if order_type not in ["MARKET", "LIMIT"]:
            order_type = "MARKET"  # Default value
            
        _CACHED_ORDER_TYPE = order_type
        logging.info(f"Order type cached at module level: {order_type}")
        return _CACHED_ORDER_TYPE
        
    except Exception as e:
        logging.error(f"Error loading order type: {e}")
        # Fallback değer
        _CACHED_ORDER_TYPE = "MARKET"
        logging.warning(f"Using fallback order type: {_CACHED_ORDER_TYPE}")
        return _CACHED_ORDER_TYPE


def _load_risk_type_once():
    """
    @brief Risk type'ı bir kez yükler ve cache'ler - module seviyesinde
    @return str: Risk type ("PERCENTAGE" veya "USDT")
    """
    global _CACHED_RISK_TYPE
    
    if _CACHED_RISK_TYPE is not None:
        return _CACHED_RISK_TYPE
    
    try:
        with open(PREFERENCES_FILE, "r") as file:
            risk_type = None
            for line in file:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("risk_type"):
                    risk_type = line.split("=")[1].strip().upper()
                    break
        
        # Geçerli risk type kontrolü
        if risk_type not in ["PERCENTAGE", "USDT"]:
            risk_type = "PERCENTAGE"  # Default value
            
        _CACHED_RISK_TYPE = risk_type
        logging.info(f"Risk type cached at module level: {risk_type}")
        return _CACHED_RISK_TYPE
        
    except Exception as e:
        logging.error(f"Error loading risk type: {e}")
        # Fallback değer
        _CACHED_RISK_TYPE = "PERCENTAGE"
        logging.warning(f"Using fallback risk type: {_CACHED_RISK_TYPE}")
        return _CACHED_RISK_TYPE

def get_buy_preferences():
    """
    @brief Returns cached preferences as a dictionary - super fast!
    @return dict: A dictionary containing preference values
    """
    global _CACHED_PREFERENCES
    
    # Cache'den döndür - çok hızlı!
    if _CACHED_PREFERENCES is None:
        _CACHED_PREFERENCES = _load_preferences_once()
    
    # Convert tuple to dictionary for backwards compatibility
    soft_risk, hard_risk = _CACHED_PREFERENCES
    
    # Get risk type to determine the format
    risk_type = get_risk_type()
    
    return {
        'soft_percentage': soft_risk if risk_type == "PERCENTAGE" else soft_risk / 100 if risk_type == "USDT" and soft_risk > 1 else soft_risk,
        'hard_percentage': hard_risk if risk_type == "PERCENTAGE" else hard_risk / 100 if risk_type == "USDT" and hard_risk > 1 else hard_risk,
        'soft_usdt': soft_risk if risk_type == "USDT" else soft_risk * 100,
        'hard_usdt': hard_risk if risk_type == "USDT" else hard_risk * 100,
        'risk_type': risk_type
    }


def get_order_type():
    """
    @brief Returns cached order type - super fast!
    @return str: Current order type ("MARKET" or "LIMIT")
    """
    global _CACHED_ORDER_TYPE
    
    # Cache'den döndür - çok hızlı!
    if _CACHED_ORDER_TYPE is None:
        _CACHED_ORDER_TYPE = _load_order_type_once()
    
    return _CACHED_ORDER_TYPE


def get_risk_type():
    """
    @brief Returns cached risk type - super fast!
    @return str: Current risk type ("PERCENTAGE" or "USDT")
    """
    global _CACHED_RISK_TYPE
    
    # Cache'den döndür - çok hızlı!
    if _CACHED_RISK_TYPE is None:
        _CACHED_RISK_TYPE = _load_risk_type_once()
    
    return _CACHED_RISK_TYPE


def set_order_type(new_order_type: str):
    """
    @brief Order type'ı dinamik olarak değiştirir ve dosyaya yazar
    @param new_order_type: Yeni order type ("MARKET" veya "LIMIT")
    @return bool: Başarılı ise True
    """
    global _CACHED_ORDER_TYPE
    
    # Validation
    if new_order_type.upper() not in ["MARKET", "LIMIT"]:
        logging.error(f"Invalid order type: {new_order_type}. Must be MARKET or LIMIT")
        return False
    
    new_order_type = new_order_type.upper()
    
    try:
        # Dosyayı oku
        with open(PREFERENCES_FILE, "r", encoding='utf-8') as file:
            lines = file.readlines()
        
        # Order type satırını bul ve güncelle
        order_type_found = False
        updated_lines = []
        
        for line in lines:
            stripped_line = line.strip()
            
            # Order type satırını bul ve güncelle
            if stripped_line.startswith("order_type") and "=" in stripped_line:
                updated_lines.append(f"order_type = {new_order_type}\n")
                order_type_found = True
                logging.info(f"🔄 Updated existing order_type line to: {new_order_type}")
            else:
                updated_lines.append(line)
        
        # Eğer order_type satırı bulunamadıysa, TRADING SETTINGS bölümüne ekle
        if not order_type_found:
            final_lines = []
            trading_section_found = False
            
            for i, line in enumerate(updated_lines):
                final_lines.append(line)
                
                # TRADING SETTINGS bölümünü bul
                if "# TRADING SETTINGS" in line and not trading_section_found:
                    trading_section_found = True
                    # Order type satırını ekle
                    if i + 1 < len(updated_lines) and "# Order type" not in updated_lines[i + 1]:
                        final_lines.append("# Order type for dynamic coin trades (MARKET or LIMIT)\n")
                    final_lines.append(f"order_type = {new_order_type}\n")
                    logging.info(f"📝 Added new order_type line to TRADING SETTINGS: {new_order_type}")
            
            # Eğer TRADING SETTINGS bölümü bulunamadıysa, dosyanın sonuna ekle
            if not trading_section_found:
                final_lines.append("\n# TRADING SETTINGS\n")
                final_lines.append("# Order type for dynamic coin trades (MARKET or LIMIT)\n")
                final_lines.append(f"order_type = {new_order_type}\n")
                logging.info(f"📝 Added TRADING SETTINGS section with order_type: {new_order_type}")
            
            updated_lines = final_lines
        
        # Dosyayı yaz
        with open(PREFERENCES_FILE, "w", encoding='utf-8') as file:
            file.writelines(updated_lines)
        
        # Cache'i güncelle
        _CACHED_ORDER_TYPE = new_order_type
        
        logging.info(f"✅ Order type successfully changed to: {new_order_type}")
        return True
        
    except Exception as e:
        logging.error(f"❌ Error setting order type: {e}")
        logging.exception("Full traceback for set_order_type error:")
        return False


def reload_preferences():
    """
    @brief Forces reload of preferences from file
    @return tuple: (soft_risk, hard_risk)
    """
    global _CACHED_PREFERENCES, _CACHED_ORDER_TYPE, _CACHED_RISK_TYPE
    _CACHED_PREFERENCES = None
    _CACHED_ORDER_TYPE = None
    _CACHED_RISK_TYPE = None
    _load_order_type_once()  # Order type'ı da yeniden yükle
    _load_risk_type_once()   # Risk type'ı da yeniden yükle
    return _load_preferences_once()


def force_preferences_reload():
    """
    @brief Public function to force reload preferences - used by UI/settings
    @return tuple: (soft_risk, hard_risk)
    """
    logging.info("🔄 Forcing preferences reload due to settings change")
    return reload_preferences()



