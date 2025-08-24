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
    validate_symbol_simple
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

def set_dynamic_coin_symbol(symbol):
    """Set and validate dynamic coin symbol"""
    original_symbol = symbol
    symbol = symbol.upper().strip()
    
    # If symbol doesn't end with USDT, add it
    if not symbol.endswith(USDT):
        symbol_with_usdt = f"{symbol}{USDT}"
    else:
        symbol_with_usdt = symbol
    
    logging.info(f"Attempting to set dynamic coin: {original_symbol} -> {symbol_with_usdt}")
    
    # Try both validation methods
    is_valid = False
    try:
        # First try the simple validation (faster, no async issues)
        if validate_symbol_simple(symbol_with_usdt):
            is_valid = True
            logging.info(f"Symbol {symbol_with_usdt} validated using simple check")
        else:
            # Fallback to async validation if simple check fails
            is_valid = validate_symbol_for_binance(symbol_with_usdt)
            if is_valid:
                logging.info(f"Symbol {symbol_with_usdt} validated using API check")
    except Exception as e:
        logging.error(f"Symbol validation failed for {symbol_with_usdt}: {e}")
        # For common symbols, proceed anyway
        if validate_symbol_simple(symbol_with_usdt):
            is_valid = True
            logging.warning(f"Using simple validation for {symbol_with_usdt}")
    
    if not is_valid:
        logging.error(f"Invalid symbol: {symbol_with_usdt} - not available on Binance")
        raise ValueError(f"Invalid symbol: {original_symbol} - This symbol is not available on Binance")
    
    data = load_fav_coins()
    if isinstance(data.get(DYNAMIC_COIN_KEY, []), list) and data[DYNAMIC_COIN_KEY]:
        data[DYNAMIC_COIN_KEY][0]['symbol'] = symbol_with_usdt
        data[DYNAMIC_COIN_KEY][0]['name'] = symbol[:-len(USDT)] if symbol.endswith(USDT) else symbol
        write_favorite_coins_to_json(data)
        logging.info(f"Successfully set dynamic coin to {symbol_with_usdt}")
        return symbol_with_usdt
    else:
        logging.error("Dynamic coin data structure is invalid")
        return None
        raise ValueError("Dynamic coin data structure is invalid")

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
            logging.info(f"Unsubscribed from {symbol_pair}")
            return True
        except websocket.WebSocketConnectionClosedException:
            logging.warning(f"Socket closed -> could not unsubscribe from: {symbol_pair}")
            return False
    else:
        logging.warning(f"WebSocket is not ready → could not unsubscribe from: {symbol_pair}")
        return False

# ===== WEBSOCKET SUBSCRIPTION FUNCTIONS =====

def subscribe_to_dynamic_coin(symbol_name):
    """Subscribe to dynamic coin price updates via WebSocket"""
    global current_dynamic_coin_subscription
    
    base = symbol_name.upper().replace(USDT, "")
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
            logging.info(f"Subscribed to dynamic coin: {pair}")
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
    global SYMBOLS, current_dynamic_coin_subscription
    
    logging.info("WebSocket connection opened")
    
    # Subscribe to favorite coins
    if SYMBOLS:
        initial = {
            "method": "SUBSCRIBE",
            "params": SYMBOLS,
            "id": next(id_gen)
        }
        ws_instance.send(json.dumps(initial))
        logging.info(f"Subscribed to {len(SYMBOLS)} favorite coins")

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
            logging.info(f"Subscribed to existing dynamic coin: {pair}")

    # Subscribe to any pending dynamic coins
    if pending_subscriptions:
        pending_msg = {
            "method": "SUBSCRIBE",
            "params": pending_subscriptions.copy(),
            "id": next(id_gen)
        }
        ws_instance.send(json.dumps(pending_msg))
        logging.info(f"Subscribed to {len(pending_subscriptions)} pending symbols")
        pending_subscriptions.clear()

def on_close(ws_instance, close_status_code, close_msg):
    """
    @brief WebSocket connection close handler.
    @param ws_instance WebSocket object.
    @param close_status_code Status code for closure.
    @param close_msg Message associated with the closure.
    @return None
    """
    logging.info(f"WebSocket connection closed! Status: {close_status_code}, Message: {close_msg}")

def on_error(ws_instance, error):
    """
    @brief WebSocket error handler.
    @param ws_instance WebSocket object.
    @param error Error message or exception.
    @return None
    """
    logging.error(f"WebSocket Error: {error}")

# ===== WEBSOCKET SETUP =====

def create_websocket():
    """Create and configure WebSocket connection"""
    global ws
    ws = websocket.WebSocketApp(
        BINANCE_WS_URL,
        on_open=on_open,
        on_message=on_message,
        on_close=on_close,
        on_error=on_error
    )
    return ws

# ===== WEBSOCKET OPERATIONS =====

def run_websocket():
    """
    Continuously run the WebSocket connection with reconnection logic.
    """
    global ws
    
    while True:
        try:
            if not ws:
                ws = create_websocket()
            ws.run_forever(sslopt=ssl_options)
        except Exception as e:
            logging.error(f"WebSocket Error: {e}. Reconnecting in {RECONNECT_DELAY} seconds...")
            time.sleep(RECONNECT_DELAY)
            ws = None  # Reset websocket for clean reconnection

def start_price_websocket():
    """
    Initialize and start the price WebSocket service in background.
    """
    global SYMBOLS
    
    # Load user preferences and get symbols for subscription
    SYMBOLS = load_user_preferences()
    
    # Start WebSocket in daemon thread
    thread = threading.Thread(target=run_websocket, daemon=True)
    thread.start()
    logging.info("Price WebSocket started in background.")
    return thread

def stop_websocket():
    """Stop the WebSocket connection"""
    global ws
    if ws:
        ws.close()
        ws = None
        logging.info("WebSocket connection stopped")

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
