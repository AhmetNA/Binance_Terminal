import logging
import os
import sys

from core.paths import PREFERENCES_FILE

# Magic strings
FAV_COINS_KEY = "favorite_coins"
USDT_SUFFIX = "USDT"
PERCENT_SIGN = "%"

# Global reference for UI notification callback
_favorites_update_callback = None

def set_favorites_update_callback(callback):
    """Set the callback function to be called when favorites are updated."""
    global _favorites_update_callback
    _favorites_update_callback = callback

def _notify_favorites_updated():
    """Notify the UI that favorites have been updated."""
    global _favorites_update_callback
    if _favorites_update_callback:
        _favorites_update_callback()

def restart_websocket_for_coin_change():
    """
    Restart WebSocket connection when coin settings are changed.
    Optimized async version for faster execution.
    """
    import asyncio
    import threading
    
    async def async_restart_websocket():
        """Asynchronous WebSocket restart implementation with retry mechanism"""
        max_retries = 2
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries + 1):
            try:
                if attempt == 0:
                    logging.info("🔄 Starting optimized WebSocket restart...")
                else:
                    logging.info(f"🔄 Retry attempt {attempt}/{max_retries} for WebSocket restart...")
                    logging.info("📢 Birazdan tekrardan bağlantı kurulacaktır, lütfen bekleyiniz...")
                
                # Import WebSocket functions
                from services.live_price_service import (
                    stop_websocket, 
                    restart_websocket_with_new_symbols,
                    get_websocket_status
                )
                
                # Step 1: Stop current WebSocket (non-blocking)
                logging.info("1️⃣ Stopping current WebSocket connection...")
                await asyncio.get_event_loop().run_in_executor(None, stop_websocket)
                
                # Step 2: Minimal wait for clean shutdown
                await asyncio.sleep(0.5)
                
                # Step 3: Start restart process in parallel with status monitoring
                logging.info("2️⃣ Restarting WebSocket with updated coin preferences...")
                
                # Run restart and status check concurrently
                restart_task = asyncio.get_event_loop().run_in_executor(
                    None, restart_websocket_with_new_symbols
                )
                
                # Wait for restart with timeout
                await asyncio.wait_for(restart_task, timeout=5.0)
                
                # Step 4: Quick status verification
                await asyncio.sleep(0.3)
                status = await asyncio.get_event_loop().run_in_executor(
                    None, get_websocket_status
                )
                
                if status.get("connected", False):
                    logging.info(f"✅ WebSocket successfully restarted with {status.get('symbols_count', 0)} coins")
                    if attempt > 0:
                        logging.info("✅ Bağlantı başarıyla yeniden kuruldu!")
                    return True
                else:
                    # Connection status uncertain - this might still be ok
                    if attempt < max_retries:
                        logging.warning(f"⚠️ WebSocket connection status uncertain, retry in {retry_delay} seconds...")
                        logging.info("📢 Bağlantı kurulumu devam ediyor, birazdan tekrar denenecek...")
                        await asyncio.sleep(retry_delay)
                        continue
                    else:
                        logging.warning("⚠️ WebSocket restart completed but connection status uncertain (final attempt)")
                        return True
                    
            except asyncio.TimeoutError:
                if attempt < max_retries:
                    logging.warning(f"⏰ WebSocket restart timed out, retry in {retry_delay} seconds...")
                    logging.info("📢 Bağlantı zaman aşımına uğradı, birazdan tekrar denenecek...")
                    await asyncio.sleep(retry_delay)
                    continue
                else:
                    logging.warning("⚠️ WebSocket restart timed out (final attempt)")
                    return True
                    
            except Exception as e:
                if attempt < max_retries:
                    logging.error(f"❌ Error in WebSocket restart (attempt {attempt + 1}): {e}")
                    logging.info(f"📢 Bağlantı hatası oluştu, {retry_delay} saniye sonra tekrar denenecek...")
                    await asyncio.sleep(retry_delay)
                    continue
                else:
                    logging.error(f"❌ Final error in async WebSocket restart: {e}")
                    logging.error("📢 Bağlantı kurulamadı, lütfen daha sonra tekrar deneyin.")
                    return False
        
        return False
    
    def run_async_restart():
        """Run the async restart in a separate thread"""
        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(async_restart_websocket())
        except Exception as e:
            logging.error(f"❌ Error running async restart: {e}")
            return False
        finally:
            loop.close()
    
    # Execute async restart in background thread to avoid blocking
    try:
        # Run in separate thread to avoid blocking the main thread
        restart_thread = threading.Thread(target=run_async_restart, daemon=True)
        restart_thread.start()
        
        # Don't wait for completion - let it run in background
        logging.info("🚀 WebSocket restart initiated in background")
        return True
        
    except Exception as e:
        logging.error(f"❌ Error starting WebSocket restart thread: {e}")
        return False

# Logging configuration (if not already set in main app)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('binance_terminal.log', encoding='utf-8')
    ]
)

def set_preference(key: str, new_value: str) -> str:
    """
    Updates or adds a preference in the Preferences.txt file.
    Returns a message about the result.
    """
    logging.info(f"Attempting to set preference: {key} = {new_value}")
    
    try:
        with open(PREFERENCES_FILE, 'r') as f:
            lines = f.readlines()
    except Exception as e:
        logging.exception(f"Error reading preferences file: {e}")
        return f"Error reading preferences file: {e}"

    updated = False
    new_lines = []
    for line in lines:
        if line.strip().startswith(f"{key}"):
            parts = line.split("=", 1)
            current_value = parts[1].strip() if len(parts) > 1 else ""
            if current_value == new_value:
                logging.info(f"Preference {key} is already set to {new_value}, no change needed")
                return f"{key} preference is already set to {new_value}"
            logging.info(f"Updating preference {key} from '{current_value}' to '{new_value}'")
            
            # Sadece risk ve volatilite tercihlerine % ekle (eğer yoksa)
            if key in ['soft_risk', 'hard_risk', 'accepted_price_volatility']:
                if not new_value.startswith('%'):
                    new_lines.append(f"{key} = %{new_value}\n")
                else:
                    new_lines.append(f"{key} = {new_value}\n")
            else:
                new_lines.append(f"{key} = {new_value}\n")
            updated = True
        else:
            new_lines.append(line)

    if not updated:
        logging.info(f"Adding new preference: {key} = {new_value}")
        # Sadece risk ve volatilite tercihlerine % ekle
        if key in ['soft_risk', 'hard_risk', 'accepted_price_volatility']:
            new_lines.append(f"{key} = %{new_value}\n")
        else:
            new_lines.append(f"{key} = {new_value}\n")
        updated = True

    try:
        with open(PREFERENCES_FILE, 'w') as f:
            f.writelines(new_lines)
        logging.info(f"Successfully saved preference {key} to file: {PREFERENCES_FILE}")
        
        # 🔄 CACHE RELOAD: Risk preferences, order type veya diğer cache edilmiş ayarlar değiştiyse cache'i temizle
        cache_dependent_keys = [
            'soft_risk', 'hard_risk', 'order_type', 'risk_type',
            'soft_risk_percentage', 'hard_risk_percentage', 
            'soft_risk_by_usdt', 'hard_risk_by_usdt',
            'accepted_price_volatility', 'chart_interval'
        ]
        
        if key in cache_dependent_keys:
            try:
                from config.preferences_manager import force_preferences_reload
                new_prefs = force_preferences_reload()
                logging.info(f"✅ Preferences cache reloaded for {key}: {new_prefs}")
            except Exception as cache_error:
                logging.warning(f"Could not reload preferences cache for {key}: {cache_error}")
        
    except Exception as e:
        logging.exception(f"Error writing preferences file: {e}")
        return f"Error writing preferences file: {e}"

    # More user-friendly message
    friendly_names = {
        'soft_risk': 'Soft Risk Level',
        'hard_risk': 'Hard Risk Level',
        'default_coin': 'Default Coin',
        'auto_refresh': 'Auto Refresh',
        'order_type': 'Order Type'
    }
    
    display_name = friendly_names.get(key, key.replace('_', ' ').title())
    
    # Special handling for order_type to make it more prominent
    if key == 'order_type':
        return f"🔄 Order Type switched to {new_value}"
    else:
        return f"✅ {display_name} set to {new_value}"


def validate_coin_symbol(coin_symbol: str) -> bool:
    """
    Validates if a coin symbol exists on Binance by checking if SYMBOL+USDT exists.
    Returns True if valid, False otherwise.
    """
    try:
        import requests
        test_symbol = f"{coin_symbol.upper()}USDT"
        url = "https://api.binance.com/api/v3/exchangeInfo"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            valid_symbols = [s['symbol'] for s in data['symbols']]
            return test_symbol in valid_symbols
        else:
            logging.error(f"Failed to fetch exchange info: {response.status_code}")
            return False
    except Exception as e:
        logging.error(f"Error validating coin symbol {coin_symbol}: {e}")
        return False

def get_order_type_preference() -> str:
    """
    Get the preferred order type for all trading from preferences.
    Returns 'MARKET' or 'LIMIT', defaults to 'MARKET' if not set.
    """
    try:
        with open(PREFERENCES_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Look for 'order_type' instead of 'dynamic_coin_order_type'
                if line.startswith("order_type") and "=" in line:
                    try:
                        key, val = line.split("=", 1)
                        order_type = val.strip().upper()
                        if order_type in ["MARKET", "LIMIT"]:
                            logging.debug(f"Order type from preferences: {order_type}")
                            return order_type
                        else:
                            logging.warning(f"Invalid order type in preferences: {order_type}, defaulting to MARKET")
                            return "MARKET"
                    except Exception:
                        continue
        
        # If not found in preferences, return default
        logging.debug("Order type not found in preferences, defaulting to MARKET")
        return "MARKET"
        
    except FileNotFoundError:
        logging.warning(f"Preferences file not found: {PREFERENCES_FILE}, defaulting to MARKET order type")
        return "MARKET"
    except Exception as e:
        logging.error(f"Error reading order type preference: {e}, defaulting to MARKET")
        return "MARKET"


def update_favorite_coin(old_coin: str, new_coin: str) -> str:
    """
    Updates the favorite coin list in the Preferences.txt file by replacing an old coin with a new one
    or appending the new coin if the old coin is not found. Ensures the new coin is not duplicated in the list.
    Returns a message about the result.
    """
    old_coin = old_coin.upper().replace(USDT_SUFFIX, "") if old_coin else ""
    new_coin = new_coin.upper().replace(USDT_SUFFIX, "") if new_coin else ""
    
    logging.info(f"Updating favorite coin: '{old_coin}' -> '{new_coin}'")
    
    if new_coin == "":
        logging.warning("Invalid coin symbol provided (empty string)")
        return "Please provide a valid coin symbol (e.g., 'XXX' without 'USDT')."
    
    # Coin symbol validasyonu ekle
    if not validate_coin_symbol(new_coin):
        logging.warning(f"Invalid coin symbol: {new_coin} - not available on Binance")
        return f"❌ {new_coin} is not available on Binance. Please check the symbol and try again."
    
    try:
        with open(PREFERENCES_FILE, 'r') as file:
            lines = file.readlines()
    except Exception as e:
        logging.exception(f"Error reading preferences file: {e}")
        return f"Error reading preferences file: {e}"

    coin_added = False
    new_lines = []
    for line in lines:
        if line.strip().startswith(FAV_COINS_KEY):
            key, values = line.split("=", 1)
            coins = [c.strip() for c in values.split(",") if c.strip()]
            
            if new_coin in coins:
                logging.warning(f"Coin {new_coin} is already in favorites list")
                return f"⚠️ {new_coin} is already in your favorites list"
            
            try:
                idx = coins.index(old_coin)
                coins[idx] = new_coin  # Replace the old coin with the new one
                logging.info(f"Replaced coin {old_coin} with {new_coin}")
                coin_added = True
            except ValueError:
                coins.append(new_coin)  # Append new_coin if old_coin not found
                logging.info(f"Added {new_coin} to favorites")
                coin_added = True
            
            new_lines.append(f"{key.strip()} = {', '.join(coins)}\n")
        else:
            new_lines.append(line)
    
    try:
        with open(PREFERENCES_FILE, 'w') as file:
            file.writelines(new_lines)
        logging.info(f"Successfully saved updated favorite coins to preferences file")
    except Exception as e:
        logging.exception(f"Error writing preferences file: {e}")
        return f"Error writing preferences file: {e}"
    
    if coin_added:
        # Optimized async callback for faster UI updates and WebSocket restart
        try:
            import threading
            import time
            
            def optimized_callback_and_restart():
                # Reduced wait time from 1s to 0.3s for faster response
                time.sleep(0.3)  
                
                # First notify UI about favorites update
                _notify_favorites_updated()
                
                # Then restart WebSocket with new coin settings (now async and non-blocking)
                logging.info(f"🔄 Triggering optimized WebSocket restart: {old_coin} → {new_coin}")
                restart_success = restart_websocket_for_coin_change()
                
                # Since restart is now async, just log the initiation
                if restart_success:
                    logging.info(f"🚀 WebSocket restart initiated for coin: {new_coin}")
                else:
                    logging.error(f"❌ WebSocket restart initiation failed for coin: {new_coin}")
            
            # Run optimized callback in daemon thread
            callback_thread = threading.Thread(target=optimized_callback_and_restart, daemon=True)
            callback_thread.start()
            
        except Exception as e:
            logging.warning(f"Could not initiate optimized UI update: {e}")
        
        return f"✅ {new_coin} added to favorites and WebSocket restarted."
