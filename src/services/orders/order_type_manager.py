"""
order_type_manager.py
Bu modül order type'ı dinamik olarak değiştirmek için kullanılan fonksiyonları içerir.
"""

import logging
import os
import sys

# Import centralized paths
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from config.preferences_manager import get_order_type, set_order_type, force_preferences_reload
except ImportError:
    # Fallback for direct execution
    from src.config.preferences_manager import get_order_type, set_order_type, force_preferences_reload


def get_current_order_type() -> str:
    """
    @brief Mevcut order type'ı getirir
    @return str: Mevcut order type ("MARKET" veya "LIMIT")
    """
    logger = logging.getLogger("get_current_order_type")
    
    try:
        order_type = get_order_type()
        logger.info(f"📋 Current order type: {order_type}")
        return order_type
    except Exception as e:
        logger.error(f"❌ Error getting current order type: {e}")
        return "MARKET"  # Fallback


def change_order_type(new_order_type: str) -> bool:
    """
    @brief Order type'ı değiştirir ve preferences dosyasına yazar
    @param new_order_type: Yeni order type ("MARKET" veya "LIMIT")
    @return bool: Başarılı ise True
    """
    logger = logging.getLogger("change_order_type")
    
    try:
        # Validation
        if new_order_type.upper() not in ["MARKET", "LIMIT"]:
            logger.error(f"❌ Invalid order type: {new_order_type}")
            return False
        
        new_order_type = new_order_type.upper()
        current_type = get_current_order_type()
        
        if current_type == new_order_type:
            logger.info(f"⚡ Order type is already {new_order_type}, no change needed")
            return True
        
        # Order type'ı değiştir
        success = set_order_type(new_order_type)
        
        if success:
            logger.info(f"✅ Successfully changed order type from {current_type} to {new_order_type}")
            
            # Cache'i yenile
            force_preferences_reload()
            
            return True
        else:
            logger.error(f"❌ Failed to change order type to {new_order_type}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error changing order type: {e}")
        logger.exception("Full traceback for order type change error:")
        return False


def toggle_order_type() -> str:
    """
    @brief Order type'ı toggle eder (MARKET <-> LIMIT)
    @return str: Yeni order type
    """
    logger = logging.getLogger("toggle_order_type")
    
    try:
        current_type = get_current_order_type()
        new_type = "LIMIT" if current_type == "MARKET" else "MARKET"
        
        logger.info(f"🔄 Toggling order type from {current_type} to {new_type}")
        
        success = change_order_type(new_type)
        
        if success:
            logger.info(f"✅ Order type toggled successfully to {new_type}")
            return new_type
        else:
            logger.error(f"❌ Failed to toggle order type")
            return current_type
            
    except Exception as e:
        logger.error(f"❌ Error toggling order type: {e}")
        return get_current_order_type()


def get_order_type_info() -> dict:
    """
    @brief Order type bilgilerini getirir
    @return dict: Order type bilgileri
    """
    logger = logging.getLogger("get_order_type_info")
    
    try:
        current_type = get_current_order_type()
        
        return {
            'current_type': current_type,
            'available_types': ['MARKET', 'LIMIT'],
            'is_market': current_type == 'MARKET',
            'is_limit': current_type == 'LIMIT',
            'description': {
                'MARKET': 'Anlık piyasa fiyatından işlem (hızlı, slippage riski)',
                'LIMIT': 'Belirtilen fiyattan işlem (hedefli, beklemeli)'
            }.get(current_type, 'Unknown')
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting order type info: {e}")
        return {
            'current_type': 'MARKET',
            'available_types': ['MARKET', 'LIMIT'],
            'is_market': True,
            'is_limit': False,
            'description': 'Error retrieving info'
        }


def is_market_order_active() -> bool:
    """
    @brief Market order aktif mi kontrol eder
    @return bool: Market order aktifse True
    """
    return get_current_order_type() == "MARKET"


def is_limit_order_active() -> bool:
    """
    @brief Limit order aktif mi kontrol eder
    @return bool: Limit order aktifse True
    """
    return get_current_order_type() == "LIMIT"


# Session-level order type override (uygulama yeniden başlatılana kadar geçerli)
_SESSION_ORDER_TYPE_OVERRIDE = None


def set_session_order_type(order_type: str) -> bool:
    """
    @brief Session için geçici order type ayarlar (dosyaya yazmaz)
    @param order_type: Session için order type
    @return bool: Başarılı ise True
    """
    global _SESSION_ORDER_TYPE_OVERRIDE
    
    if order_type.upper() not in ["MARKET", "LIMIT"]:
        logging.error(f"❌ Invalid session order type: {order_type}")
        return False
    
    _SESSION_ORDER_TYPE_OVERRIDE = order_type.upper()
    logging.info(f"⚡ Session order type set to: {_SESSION_ORDER_TYPE_OVERRIDE}")
    return True


def get_effective_order_type() -> str:
    """
    @brief Geçerli order type'ı getirir (session override varsa onu, yoksa preferences'dan)
    @return str: Geçerli order type
    """
    global _SESSION_ORDER_TYPE_OVERRIDE
    
    if _SESSION_ORDER_TYPE_OVERRIDE is not None:
        logging.debug(f"🎯 Using session override order type: {_SESSION_ORDER_TYPE_OVERRIDE}")
        return _SESSION_ORDER_TYPE_OVERRIDE
    
    return get_current_order_type()


def clear_session_order_type():
    """
    @brief Session order type override'ını temizler
    """
    global _SESSION_ORDER_TYPE_OVERRIDE
    
    if _SESSION_ORDER_TYPE_OVERRIDE is not None:
        logging.info(f"🧹 Clearing session order type override: {_SESSION_ORDER_TYPE_OVERRIDE}")
        _SESSION_ORDER_TYPE_OVERRIDE = None
    else:
        logging.debug("🧹 No session order type override to clear")


def get_session_order_type_info() -> dict:
    """
    @brief Session order type bilgilerini getirir
    @return dict: Session bilgileri
    """
    global _SESSION_ORDER_TYPE_OVERRIDE
    
    return {
        'has_session_override': _SESSION_ORDER_TYPE_OVERRIDE is not None,
        'session_override': _SESSION_ORDER_TYPE_OVERRIDE,
        'preferences_type': get_current_order_type(),
        'effective_type': get_effective_order_type()
    }
