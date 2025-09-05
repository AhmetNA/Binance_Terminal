"""
Live Price Service Module

This module provides real-time cryptocurrency price monitoring and management through WebSocket 
connections and data storage operations. It serves as the central hub for all live price operations.

Features:
- Real-time price updates via Binance WebSocket
- Automatic reconnection on connection loss
- Dynamic coin subscription management
- Price update and data storage management
- Symbol validation and management
- Live price broadcasting and notifications
"""
import websocket
import json
import threading
import time
import ssl
import os
import logging
import sys

# Add src to path for core imports (optimized)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import pending_subscriptions, USDT, TICKER_SUFFIX, RECONNECT_DELAY, COINS_KEY, DYNAMIC_COIN_KEY
from core.paths import MAIN_LOG_FILE

# Import utility functions
from utils.symbol_utils import (
    validate_symbol_for_binance,
    validate_symbol_simple,
    validate_and_format_symbol,
    format_user_input_to_binance_ticker,
    process_user_coin_input,
    validate_coin_before_setting,
    view_coin_format
)
from utils.data_utils import (
    load_fav_coins,
    write_favorite_coins_to_json,
    load_user_preferences
)

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(MAIN_LOG_FILE, encoding='utf-8')
    ]
)

ssl_options = {"ssl_version": ssl.PROTOCOL_TLSv1_2}

BINANCE_WS_URL = "wss://stream.binance.com:9443/ws"

# Global variables
SYMBOLS = []
ws = None
ws_app = None
connection_active = False
websocket_starting = False
current_dynamic_coin_subscription = None

# ===== PRICE UPDATE FUNCTIONS =====

def refresh_coin_price(symbol, new_price):
    """Update favorite coin price in data storage"""
    try:
        data = load_fav_coins()
        for coin in data.get(COINS_KEY, []):
            if coin['symbol'].lower() == symbol.lower():
                coin['values']['current'] = new_price
                break
        write_favorite_coins_to_json(data)
    except Exception as e:
        logging.exception(f"Error refreshing coin price for {symbol}: {e}")

def refresh_dynamic_coin_price(symbol, new_price):
    """Update dynamic coin price in data storage"""
    try:
        data = load_fav_coins()
        if isinstance(data.get(DYNAMIC_COIN_KEY, []), list) and data[DYNAMIC_COIN_KEY]:
            data[DYNAMIC_COIN_KEY][0]['symbol'] = symbol.upper()
            data[DYNAMIC_COIN_KEY][0]['values']['current'] = new_price
        write_favorite_coins_to_json(data)
    except Exception as e:
        logging.exception(f"Error refreshing dynamic coin price for {symbol}: {e}")

def set_dynamic_coin_symbol(user_input):
    """
    Set and validate dynamic coin symbol with comprehensive validation flow
    Args:
        user_input: User's coin input (e.g., 'btc', 'BTC', 'bitcoin')
    Returns:
        dict: {
            'success': bool,
            'binance_ticker': str,  # For websocket subscription
            'view_coin_name': str,  # For display
            'error_message': str    # Error message if failed
        }
    """
    logging.debug(f"Attempting to set dynamic coin: {user_input}")
    
    try:
        # Process user input with comprehensive validation
        result = process_user_coin_input(user_input)
        
        if not result['success']:
            logging.error(f"Coin validation failed: {result['error_message']}")
            return {
                'success': False,
                'binance_ticker': '',
                'view_coin_name': '',
                'error_message': result['error_message']
            }
        
        # Extract validated data
        binance_ticker = result['binance_ticker']
        view_coin_name = result['view_coin_name']
        # Extract base symbol (remove -USDT suffix for name)
        base_symbol = view_coin_name.replace('-USDT', '')
        
        # Update dynamic coin data with both ticker and view name
        data = load_fav_coins()
        if isinstance(data.get(DYNAMIC_COIN_KEY, []), list) and data[DYNAMIC_COIN_KEY]:
            # Store binance ticker for websocket subscription
            data[DYNAMIC_COIN_KEY][0]['symbol'] = binance_ticker
            # Store base symbol for user display (BTC instead of BTC-USDT)
            data[DYNAMIC_COIN_KEY][0]['name'] = base_symbol
            # Store original user input for reference
            data[DYNAMIC_COIN_KEY][0]['original_input'] = result['original_input']
            
            write_favorite_coins_to_json(data)
            
            logging.debug(f"Successfully set dynamic coin - Ticker: {binance_ticker}, View: {view_coin_name}")
            
            return {
                'success': True,
                'binance_ticker': binance_ticker,
                'view_coin_name': view_coin_name,
                'error_message': ''
            }
        else:
            error_msg = "Dynamic coin data structure is invalid"
            logging.error(error_msg)
            return {
                'success': False,
                'binance_ticker': '',
                'view_coin_name': '',
                'error_message': error_msg
            }
            
    except Exception as e:
        error_msg = f"Dynamic coin ayarlanırken hata oluştu: {str(e)}"
        logging.error(f"Error setting dynamic coin '{user_input}': {e}")
        return {
            'success': False,
            'binance_ticker': '',
            'view_coin_name': '',
            'error_message': error_msg
        }

# ===== WEBSOCKET UTILITY FUNCTIONS =====

def id_generator():
    """Generate unique IDs for WebSocket messages"""
    n = 1
    while True:
        yield n
        n += 1

id_gen = id_generator()

def unsubscribe_from_symbol(symbol_pair):
    """Unsubscribe from a specific symbol via WebSocket"""
    msg = {"method": "UNSUBSCRIBE", "params": [symbol_pair], "id": next(id_gen)}
    
    if ws and ws.sock and getattr(ws.sock, "connected", False):
        try:
            ws.send(json.dumps(msg))
            logging.debug(f"Unsubscribed from {symbol_pair}")
            return True
        except websocket.WebSocketConnectionClosedException:
            logging.warning(f"Socket closed -> could not unsubscribe from: {symbol_pair}")
            return False
    else:
        logging.warning(f"WebSocket is not ready → could not unsubscribe from: {symbol_pair}")
        return False

# ===== WEBSOCKET SUBSCRIPTION FUNCTIONS =====

def subscribe_to_dynamic_coin(binance_ticker):
    """Subscribe to dynamic coin price updates via WebSocket using binance ticker"""
    global current_dynamic_coin_subscription
    
    # binance_ticker already in format like 'BTCUSDT'
    base = binance_ticker.upper().replace(USDT, "")
    pair = f"{base.lower()}{USDT.lower()}{TICKER_SUFFIX}"
    
    # Unsubscribe from previous dynamic coin if it exists
    if current_dynamic_coin_subscription and current_dynamic_coin_subscription != pair:
        unsubscribe_from_symbol(current_dynamic_coin_subscription)
    
    # Subscribe to new dynamic coin
    msg = {"method": "SUBSCRIBE", "params": [pair], "id": next(id_gen)}

    if ws and ws.sock and getattr(ws.sock, "connected", False):
        try:
            ws.send(json.dumps(msg))
            current_dynamic_coin_subscription = pair
            logging.debug(f"Subscribed to dynamic coin: {pair} (from ticker: {binance_ticker})")
        except websocket.WebSocketConnectionClosedException:
            pending_subscriptions.append(pair)
            logging.warning(f"Socket closed -> added to queue: {pair}")
    else:
        pending_subscriptions.append(pair)
        logging.warning(f"WebSocket is not ready → added to the queue: {pair}")

# ===== WEBSOCKET EVENT HANDLERS =====

def on_message(ws_instance, message):
    """
    @brief WebSocket message handler. Updates coin prices on price update.
    @param ws_instance WebSocket object.
    @param message JSON-formatted message received from Binance WebSocket.
    @return None
    """
    try:
        data = json.loads(message)
        if 's' in data and 'c' in data:
            symbol = data['s']
            new_price = float(data['c'])

            # Update favorite coins
            fav_coins_data = load_fav_coins()
            if symbol.lower() in [coin['symbol'].lower() for coin in fav_coins_data.get(COINS_KEY, [])]:
                refresh_coin_price(symbol, new_price)

            # Update dynamic coin
            dynamic_coin = fav_coins_data.get(DYNAMIC_COIN_KEY, [])
            if isinstance(dynamic_coin, list) and dynamic_coin and symbol.lower() == dynamic_coin[0]['symbol'].lower():
                refresh_dynamic_coin_price(symbol, new_price)
        elif 'result' in data and 'id' in data:
            # This is a subscription confirmation message, ignore it
            logging.debug(f"WebSocket subscription confirmation: {data}")
        else:
            logging.warning(f"Unknown WebSocket message format: {data}")
    except Exception as e:
        logging.exception(f"WebSocket Message Error: {e}")

def on_open(ws_instance):
    """
    @brief WebSocket connection open handler. Subscribes to favorite coins and any queued dynamic coins.
    @param ws_instance WebSocket object.
    @return None
    """
    global SYMBOLS, current_dynamic_coin_subscription, connection_active
    
    # Check if this connection should be active
    if not connection_active and not websocket_starting:
        logging.warning("WebSocket opened but connection should not be active, closing...")
        try:
            ws_instance.close()
        except:
            pass
        return
    
    logging.info("WebSocket connection opened")
    connection_active = True
    
    # Subscribe to favorite coins
    if SYMBOLS:
        initial = {
            "method": "SUBSCRIBE",
            "params": SYMBOLS,
            "id": next(id_gen)
        }
        ws_instance.send(json.dumps(initial))
        logging.info(f"✅ Subscribed to {len(SYMBOLS)} favorite coins: {SYMBOLS}")
    else:
        logging.warning("No favorite coins symbols found to subscribe to")

    # Subscribe to existing dynamic coin if it exists
    fav_coins_data = load_fav_coins()
    dynamic_coin = fav_coins_data.get(DYNAMIC_COIN_KEY, [])
    if isinstance(dynamic_coin, list) and dynamic_coin and 'symbol' in dynamic_coin[0]:
        symbol = dynamic_coin[0]['symbol']
        if symbol:
            base = symbol.upper().replace(USDT, "")
            pair = f"{base.lower()}{USDT.lower()}{TICKER_SUFFIX}"
            current_dynamic_coin_subscription = pair
            
            dynamic_msg = {
                "method": "SUBSCRIBE",
                "params": [pair],
                "id": next(id_gen)
            }
            ws_instance.send(json.dumps(dynamic_msg))
            logging.debug(f"Subscribed to existing dynamic coin: {pair}")

    # Subscribe to any pending dynamic coins
    if pending_subscriptions:
        pending_msg = {
            "method": "SUBSCRIBE",
            "params": pending_subscriptions.copy(),
            "id": next(id_gen)
        }
        ws_instance.send(json.dumps(pending_msg))
        logging.debug(f"Subscribed to {len(pending_subscriptions)} pending symbols")
        pending_subscriptions.clear()

def on_close(ws_instance, close_status_code, close_msg):
    """
    @brief WebSocket connection close handler.
    @param ws_instance WebSocket object.
    @param close_status_code Status code for closure.
    @param close_msg Message associated with the closure.
    @return None
    """
    global connection_active
    connection_active = False
    logging.info(f"WebSocket connection closed! Status: {close_status_code}, Message: {close_msg}")

def on_error(ws_instance, error):
    """
    @brief WebSocket error handler.
    @param ws_instance WebSocket object.
    @param error Error message or exception.
    @return None
    """
    global connection_active
    connection_active = False
    logging.error(f"WebSocket Error: {error}")

# ===== WEBSOCKET SETUP =====

def create_websocket():
    """Create and configure WebSocket connection"""
    global ws, ws_app, connection_active
    ws_app = websocket.WebSocketApp(
        BINANCE_WS_URL,
        on_open=on_open,
        on_message=on_message,
        on_close=on_close,
        on_error=on_error
    )
    ws = ws_app  # Keep backward compatibility
    connection_active = True
    return ws_app

# ===== WEBSOCKET OPERATIONS =====

def run_websocket():
    """
    Continuously run the WebSocket connection with reconnection logic.
    """
    global ws, connection_active, websocket_starting
    
    while True:
        try:
            # Check if we should stop (connection_active is False and we're not just starting)
            if not connection_active and not websocket_starting:
                logging.debug("WebSocket stopping due to connection_active=False")
                break
                
            if not ws:
                ws = create_websocket()
            ws.run_forever(sslopt=ssl_options)
            
        except Exception as e:
            logging.error(f"WebSocket Error: {e}. Reconnecting in {RECONNECT_DELAY} seconds...")
            connection_active = False
            time.sleep(RECONNECT_DELAY)
            ws = None  # Reset websocket for clean reconnection
            
            # If we're not actively trying to restart, break the loop
            if not websocket_starting:
                logging.debug("WebSocket stopping after error - not restarting")
                break

def start_price_websocket():
    """
    Initialize and start the price WebSocket service in background.
    """
    global SYMBOLS, websocket_starting, connection_active
    
    # For restart scenarios, allow override of existing connections
    restart_mode = not connection_active and not websocket_starting
    
    # Prevent multiple simultaneous starts (unless it's a restart)
    if websocket_starting and connection_active:
        logging.warning("WebSocket is already starting and active, skipping...")
        return None
    
    # If we're in restart mode, force clear existing state
    if not connection_active:
        logging.info("Starting WebSocket (restart mode)")
        websocket_starting = True
    elif connection_active:
        logging.warning("WebSocket is already active, skipping...")
        return None
    else:
        websocket_starting = True
    
    try:
        # Load user preferences and get symbols for subscription
        SYMBOLS = load_user_preferences()
        logging.debug(f"Loaded {len(SYMBOLS)} symbols for WebSocket")
        
        # Start WebSocket in daemon thread
        thread = threading.Thread(target=run_websocket, daemon=True)
        thread.start()
        logging.info("Price WebSocket started in background.")
        
        # Reset the starting flag after a short delay
        def reset_starting_flag():
            global websocket_starting
            time.sleep(2)
            if not connection_active:
                # If connection didn't become active, something went wrong
                logging.warning("WebSocket did not become active after 2 seconds")
            websocket_starting = False
            logging.debug("WebSocket starting flag reset")
        
        reset_thread = threading.Thread(target=reset_starting_flag, daemon=True)
        reset_thread.start()
        
        return thread
        
    except Exception as e:
        websocket_starting = False
        logging.error(f"Error starting WebSocket: {e}")
        raise

def stop_websocket():
    """Stop the WebSocket connection safely"""
    global ws, ws_app, connection_active, websocket_starting
    
    try:
        logging.info("🛑 Stopping WebSocket connection...")
        
        # Set flags to stop any running processes
        connection_active = False
        websocket_starting = False
        
        # Close WebSocket connections safely
        if ws_app:
            try:
                ws_app.close()
                logging.debug("✅ Closed ws_app connection")
            except Exception as e:
                logging.warning(f"Error closing ws_app: {e}")
        
        if ws and ws != ws_app:  # Avoid double-closing if they're the same object
            try:
                ws.close()
                logging.debug("✅ Closed ws connection")
            except Exception as e:
                logging.warning(f"Error closing ws: {e}")
        
        # Reset WebSocket variables
        ws_app = None
        ws = None
        
        logging.info("✅ WebSocket connection stopped successfully")
        
    except Exception as e:
        logging.error(f"❌ Error stopping WebSocket: {e}")
        # Force reset even if there's an error
        connection_active = False
        websocket_starting = False
        ws_app = None
        ws = None

def is_websocket_connected():
    """Check if WebSocket is currently connected"""
    global ws
    return ws and ws.sock and getattr(ws.sock, "connected", False)

def get_websocket_status():
    """Get current WebSocket connection status"""
    return {
        "connected": is_websocket_connected(),
        "symbols_count": len(SYMBOLS),
        "pending_subscriptions": len(pending_subscriptions)
    }

# ===== MAIN ENTRY POINTS =====

def set_and_subscribe_dynamic_coin(user_input):
    """
    Complete flow: Set dynamic coin and subscribe to WebSocket
    Args:
        user_input: User's coin input (e.g., 'btc', 'BTC', 'bitcoin')
    Returns:
        dict: Result of the operation
    """
    # Step 1: Set dynamic coin with validation
    result = set_dynamic_coin_symbol(user_input)
    
    if not result['success']:
        logging.error(f"Failed to set dynamic coin: {result['error_message']}")
        return result
    
    # Step 2: Subscribe to WebSocket with binance ticker
    try:
        subscribe_to_dynamic_coin(result['binance_ticker'])
        logging.debug(f"Successfully set and subscribed to dynamic coin: {result['view_coin_name']}")
        return result
    except Exception as e:
        error_msg = f"WebSocket subscription failed: {str(e)}"
        logging.error(error_msg)
        return {
            'success': False,
            'binance_ticker': result['binance_ticker'],
            'view_coin_name': result['view_coin_name'],
            'error_message': error_msg
        }

def restart_websocket_with_new_symbols():
    """
    Restart WebSocket connection to include newly added favorite coins.
    This allows dynamic updates without app restart.
    """
    global ws_app, connection_active, ws, SYMBOLS, websocket_starting
    
    try:
        logging.debug("🔄 Restarting WebSocket with new favorite symbols...")
        
        # Step 1: Safely stop existing WebSocket
        stop_websocket()
        
        # Step 2: Wait for complete shutdown
        logging.debug("⏳ Waiting for WebSocket to fully shutdown...")
        time.sleep(3)
        
        # Step 3: Reset all flags and variables completely
        connection_active = False
        websocket_starting = False
        ws_app = None
        ws = None
        
        # Step 4: Reload symbols from preferences
        SYMBOLS = load_user_preferences()
        logging.info(f"� Reloaded {len(SYMBOLS)} symbols for WebSocket: {SYMBOLS}")
        
        # Step 5: Start new WebSocket connection with updated symbols
        logging.info("🚀 Starting new WebSocket connection with updated symbols...")
        thread = start_price_websocket()
        
        if thread:
            logging.info("✅ WebSocket restart initiated successfully")
            # Wait a bit and verify connection
            time.sleep(3)
            if connection_active:
                logging.info("✅ WebSocket connection verified active")
            else:
                logging.warning("⚠️ WebSocket may still be connecting...")
        else:
            logging.error("❌ WebSocket restart failed - no thread returned")
        
    except Exception as e:
        logging.error(f"❌ Error restarting WebSocket: {e}")
        # Reset flags on error
        websocket_starting = False
        connection_active = False
        raise


def reload_symbols():
    """
    Reload symbols from user preferences and update the active WebSocket subscription.
    This is a lightweight alternative to full WebSocket restart.
    """
    global SYMBOLS, ws
    
    try:
        # Load updated symbols from preferences
        new_symbols = load_user_preferences()
        
        if new_symbols == SYMBOLS:
            logging.info("No changes in favorite symbols, skipping reload")
            return
        
        old_count = len(SYMBOLS)
        SYMBOLS = new_symbols
        new_count = len(SYMBOLS)
        
        logging.info(f"Symbol list updated: {old_count} -> {new_count} coins")
        
        # If WebSocket is active, subscribe to new symbols
        if ws and connection_active:
            # Subscribe to any new favorite coins
            for symbol in SYMBOLS:
                ticker_symbol = f"{symbol.lower()}usdt@ticker"
                if ticker_symbol not in pending_subscriptions:
                    try:
                        ws.send(json.dumps({
                            "method": "SUBSCRIBE",
                            "params": [ticker_symbol],
                            "id": len(pending_subscriptions) + 1
                        }))
                        pending_subscriptions.add(ticker_symbol)
                        logging.info(f"Subscribed to new favorite coin: {ticker_symbol}")
                    except Exception as e:
                        logging.error(f"Error subscribing to {ticker_symbol}: {e}")
            
            logging.info(f"✅ Successfully reloaded {len(SYMBOLS)} symbols into active WebSocket")
        else:
            logging.warning("WebSocket not active, symbols updated but not subscribed")
    
    except Exception as e:
        logging.error(f"Error reloading symbols: {e}")


def main():
    """
    @brief Entry point for running the WebSocket process.
    @return None
    """
    try:
        start_price_websocket()
        # Keep main thread alive for non-daemon websocket
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Price service stopped by user")
    except Exception as e:
        logging.error(f"Error in main: {e}")

if __name__ == "__main__":
    main()
