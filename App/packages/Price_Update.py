"""
This module manages the Binance WebSocket connection to update coin prices in real-time for 
both favorite coins and a dynamic coin. It loads user preferences from a text file, retrieves 
favorite coin configurations from a JSON file, and formats subscription symbols for the Binance 
WebSocket stream.
Key functionalities include:
- Loading and updating favorite coins and dynamic coin data from JSON and preferences files.
- Formatting coin symbols for WebSocket subscription.
- Maintaining a persistent connection to the Binance WebSocket stream with automatic reconnection 
    and error handling.
- Updating coin price data within the JSON configuration upon receiving new price updates.
- Enabling dynamic subscription to new coins via user-defined preferences and runtime changes.
The module uses threading to run the WebSocket connection in the background, ensuring the coin 
price information is continuously updated in real-time.
"""
import websocket
import json
import threading
import time
import ssl
import os
import logging
from .Global_State import PREFERENCES_FILE, FAV_COINS_FILE, SYMBOLS, pending_subscriptions, USDT, TICKER_SUFFIX, RECONNECT_DELAY, COINS_KEY, DYNAMIC_COIN_KEY

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'binance_terminal.log'), encoding='utf-8')
    ]
)

ssl_options = {"ssl_version": ssl.PROTOCOL_TLSv1_2}

""" FAVORITE COINS """
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

APP_DIR = os.path.abspath(os.path.join(CURRENT_DIR, '..'))

SETTINGS_DIR = os.path.join(APP_DIR, 'settings')

BINANCE_WS_URL = "wss://stream.binance.com:9443/ws"

def load_fav_coins():
    """
    Load favorite coins data from the JSON configuration file.
    Returns a dictionary containing 'coins' and 'dynamic_coin' entries.
    """
    try:
        if not os.path.exists(FAV_COINS_FILE):
            return {COINS_KEY: [], DYNAMIC_COIN_KEY: []}
        with open(FAV_COINS_FILE, 'r') as file:
            return json.load(file)
    except Exception as e:
        logging.exception(f"Error loading favorite coins: {e}")
        return {COINS_KEY: [], DYNAMIC_COIN_KEY: []}


def write_favorite_coins_to_json(data):
    """
    Write the updated favorite coins data back to the JSON configuration file.
    """
    try:
        with open(FAV_COINS_FILE, 'w') as file:
            json.dump(data, file, indent=4)
    except Exception as e:
        logging.exception(f"Error writing favorite coins: {e}")


def load_user_preferences():
    """
    @brief Reads the Preferences.txt file and updates the favorite coins accordingly.
    @details It updates the 'symbol' and 'name' fields for favorite coins
             and formats the SYMBOLS list for Binance WebSocket subscription.
    @return None
    """
    global SYMBOLS

    if not os.path.exists(PREFERENCES_FILE):
        logging.warning("Preferences file not found!")
        return

    try:
        with open(PREFERENCES_FILE, 'r') as file:
            for line in file:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                if line.startswith("favorite_coins"):
                    fav_coins_name = [coin.strip() for coin in line.split("=")[1].split(",")]
                    data = load_fav_coins()

                    for i, coin_name in enumerate(fav_coins_name):
                        if i < len(data.get(COINS_KEY, [])):
                            data[COINS_KEY][i]['symbol'] = f"{coin_name.upper()}{USDT}"
                            data[COINS_KEY][i]['name'] = coin_name.upper()

                    write_favorite_coins_to_json(data)

        data = load_fav_coins()
        Fav_symbols = [coin['symbol'] for coin in data.get(COINS_KEY, [])]
        SYMBOLS = format_binance_ticker_symbols(Fav_symbols)
    except Exception as e:
        logging.exception(f"Error loading user preferences: {e}")


def refresh_coin_price(symbol, new_price):
    """
    Update the price of a favorite coin in the JSON file.
    """
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
    """
    Update the price of the dynamic coin in the JSON file.
    """
    try:
        data = load_fav_coins()
        if isinstance(data.get(DYNAMIC_COIN_KEY, []), list) and data[DYNAMIC_COIN_KEY]:
            data[DYNAMIC_COIN_KEY][0]['symbol'] = symbol.upper()
            data[DYNAMIC_COIN_KEY][0]['values']['current'] = new_price
        write_favorite_coins_to_json(data)
    except Exception as e:
        logging.exception(f"Error refreshing dynamic coin price for {symbol}: {e}")


def set_dynamic_coin_symbol(symbol):
    """
    @brief Set a new dynamic coin symbol and subscribe to its ticker.
    @param symbol The coin symbol entered by the user (without USDT).
    @return None
    """
    symbol = symbol.upper()
    symbol = f"{symbol}{USDT}"
    data = load_fav_coins()
    if isinstance(data.get(DYNAMIC_COIN_KEY, []), list) and data[DYNAMIC_COIN_KEY]:
        data[DYNAMIC_COIN_KEY][0]['symbol'] = symbol
        data[DYNAMIC_COIN_KEY][0]['name'] = symbol[:-len(USDT)]
        write_favorite_coins_to_json(data)
        subscribe_to_dynamic_coin(symbol)


def format_binance_ticker_symbols(symbols):
    """
    @brief Format coin symbols for Binance WebSocket ticker stream.
    @param symbols List of coin symbols like ['BTCUSDT', 'ETHUSDT'].
    @return List of formatted symbols like ['btcusdt@ticker'].
    """
    return [symbol.lower() + TICKER_SUFFIX for symbol in symbols]


def id_generator():
    """Generate unique IDs for WebSocket messages."""
    n = 1
    while True:
        yield n
        n += 1

id_gen = id_generator()

def on_message(ws, message):
    """
    @brief WebSocket message handler. Updates coin prices on price update.
    @param ws WebSocket object.
    @param message JSON-formatted message received from Binance WebSocket.
    @return None
    """
    try:
        data = json.loads(message)
        if 's' in data and 'c' in data:
            symbol = data['s']
            new_price = float(data['c'])

            if symbol.lower() in [coin['symbol'].lower() for coin in load_fav_coins().get(COINS_KEY, [])]:
                refresh_coin_price(symbol, new_price)

            dynamic_coin = load_fav_coins().get(DYNAMIC_COIN_KEY, [])
            if isinstance(dynamic_coin, list) and dynamic_coin and symbol.lower() == dynamic_coin[0]['symbol'].lower():
                refresh_dynamic_coin_price(symbol, new_price)
        else:
            logging.warning(f"WebSocket message does not contain 's' or 'c': {data}")
    except Exception as e:
        logging.exception(f"WebSocket Error: {e}")


def on_open(ws):
    """
    @brief WebSocket connection open handler. Subscribes to favorite coins and any queued dynamic coins.
    @param ws WebSocket object.
    @return None
    """
    initial = {
        "method": "SUBSCRIBE",
        "params": SYMBOLS,
        "id": next(id_gen)
    }
    ws.send(json.dumps(initial))

    if pending_subscriptions:
        pending_msg = {
            "method": "SUBSCRIBE",
            "params": pending_subscriptions.copy(),
            "id": next(id_gen)
        }
        ws.send(json.dumps(pending_msg))
        pending_subscriptions.clear()


def on_close(ws, close_status_code, close_msg):
    """
    @brief WebSocket connection close handler.
    @param ws WebSocket object.
    @param close_status_code Status code for closure.
    @param close_msg Message associated with the closure.
    @return None
    """
    logging.info("WebSocket connection closed!")


def on_error(ws, error):
    """
    @brief WebSocket error handler.
    @param ws WebSocket object.
    @param error Error message or exception.
    @return None
    """
    logging.error(f"WebSocket Error: {error}")

ws = websocket.WebSocketApp(
    BINANCE_WS_URL,
    on_open=on_open,
    on_message=on_message,
    on_close=on_close,
    on_error=on_error
)

ssl_options = {"ssl_version": ssl.PROTOCOL_TLSv1_2}

""" THREADING """

def run_websocket():
    """
    Continuously run the WebSocket connection with reconnection logic.
    """
    while True:
        try:
            ws.run_forever(sslopt=ssl_options)
        except Exception as e:
            logging.error(f"WebSocket Error: {e}. Reconnecting in {RECONNECT_DELAY} seconds...")
            time.sleep(RECONNECT_DELAY)


def subscribe_to_dynamic_coin(symbol_name):
    """
    @brief Subscribe to a dynamic coin symbol via WebSocket.
    @param symbol_name Coin symbol (e.g., 'BTC', 'ETH') without 'USDT'.
    @return None
    """
    base = symbol_name.upper().replace(USDT, "")
    pair = f"{base.lower()}{USDT.lower()}{TICKER_SUFFIX}"
    msg = {"method": "SUBSCRIBE", "params": [pair], "id": next(id_gen)}

    if ws.sock and getattr(ws.sock, "connected", False):
        try:
            ws.send(json.dumps(msg))
            logging.info(f"Subscribed to {pair}")
        except websocket.WebSocketConnectionClosedException:
            pending_subscriptions.append(pair)
            logging.warning(f"Socket closed -> added to queue: {pair}")
    else:
        pending_subscriptions.append(pair)
        logging.warning(f"WebSocket is not ready → added to the queue: {pair}")


def start_price_websocket():
    """
    @brief Start the WebSocket connection in a background thread after loading preferences.
    @return None
    """
    load_user_preferences()
    thread = threading.Thread(target=run_websocket, daemon=True)
    thread.start()
    logging.info("WebSocket started in background.")


def main():
    """
    @brief Entry point for running the WebSocket process.
    @return None
    """
    load_user_preferences()
    thread = threading.Thread(target=run_websocket, daemon=True)
    thread.start()
    thread.join()

if __name__ == "__main__":
    start_price_websocket()  # Use upgrade_price() to ensure preferences are loaded first
