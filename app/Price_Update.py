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



""" FAVORITE COINS """
# Get the directory where this file is located
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# Assuming the Preferences and fav_coins files are in the same directory as this script
PREFERENCES_FILE = os.path.join(CURRENT_DIR, 'Preferences.txt')
FAV_COINS_FILE = os.path.join(CURRENT_DIR, 'fav_coins.json')

BINANCE_WS_URL = "wss://stream.binance.com:9443/ws"

def load_fav_coins():
    """Load favorite coins data from JSON file."""
    if not os.path.exists(FAV_COINS_FILE):
        return {"coins": [], "dynamic_coin": []}  # Default structure

    with open(FAV_COINS_FILE, 'r') as file:
        return json.load(file)

def write_favorite_coins_to_json(data):
    """Save favorite coins data to JSON file."""
    with open(FAV_COINS_FILE, 'w') as file:
        json.dump(data, file, indent=4)

def load_user_preferences():
    """Read Preferences.txt and update favorite coins, then update subscription symbols."""
    global SYMBOLS  # Ensure SYMBOLS is updated after preferences are loaded

    if not os.path.exists(PREFERENCES_FILE):
        print("Preferences file not found!")
        return

    with open(PREFERENCES_FILE, 'r') as file:
        for line in file:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if line.startswith("favorite_coins"):
                fav_coins_name = [coin.strip() for coin in line.split("=")[1].split(",")]
                data = load_fav_coins()

                for i, coin_name in enumerate(fav_coins_name):
                    if i < len(data.get('coins', [])):
                        data['coins'][i]['symbol'] = f"{coin_name.upper()}USDT"
                        data['coins'][i]['name'] = coin_name.upper()

                write_favorite_coins_to_json(data)

    # Reload SYMBOLS after updating preferences
    data = load_fav_coins()
    Fav_symbols = [coin['symbol'] for coin in data.get('coins', [])]
    SYMBOLS = format_binance_ticker_symbols(Fav_symbols)
    
    print(f"Updated SYMBOLS for WebSocket subscription: {SYMBOLS}")

def refresh_coin_price(symbol, new_price):
    """Update favorite coin prices in JSON file."""
    data = load_fav_coins()
    for coin in data.get('coins', []):
        if coin['symbol'].lower() == symbol.lower():
            coin['values']['current'] = new_price
            break
    write_favorite_coins_to_json(data)

def refresh_dynamic_coin_price(symbol, new_price):
    """Update dynamic coin price in JSON file."""
    data = load_fav_coins()
    if isinstance(data.get('dynamic_coin', []), list) and data['dynamic_coin']:
        data['dynamic_coin'][0]['symbol'] = symbol.upper()
        data['dynamic_coin'][0]['values']['current'] = new_price
    write_favorite_coins_to_json(data)

def set_dynamic_coin_symbol(symbol):
    """Add a new dynamic coin."""
    symbol = symbol.replace(".", "").upper()
    data = load_fav_coins()
    if isinstance(data.get('dynamic_coin', []), list) and data['dynamic_coin']:
        data['dynamic_coin'][0]['symbol'] = symbol
        data['dynamic_coin'][0]['name'] = symbol[:-4]
        write_favorite_coins_to_json(data)
        subscribe_to_dynamic_coin(symbol)

""" SYMBOLS """
def format_binance_ticker_symbols(symbols):
    """Convert symbols to Binance WebSocket ticker format."""
    return [symbol.lower() + "@ticker" for symbol in symbols]

# Load symbols at the start
data = load_fav_coins()
Fav_symbols = [coin['symbol'] for coin in data.get('coins', [])]
SYMBOLS = format_binance_ticker_symbols(Fav_symbols)

""" WEBSOCKET CONNECTION """

# ID generator for each subscription
def id_generator():
    """Generate unique IDs for WebSocket messages."""
    n = 1
    while True:
        yield n
        n += 1

id_gen = id_generator()

def on_message(ws, message):
    """Handle incoming WebSocket messages."""
    data = json.loads(message)
    symbol = data['s']
    new_price = float(data['c'])

    # Update favorite coins
    if symbol.lower() in [coin['symbol'].lower() for coin in load_fav_coins().get('coins', [])]:
        refresh_coin_price(symbol, new_price)

    # Update dynamic coin
    dynamic_coin = load_fav_coins().get('dynamic_coin', [])
    if isinstance(dynamic_coin, list) and dynamic_coin and symbol.lower() == dynamic_coin[0]['symbol'].lower():
        refresh_dynamic_coin_price(symbol, new_price)

def on_open(ws):
    """Subscribe to favorite coins on WebSocket open."""
    print("WebSocket connection opened! Subscribing to updated SYMBOLS...")
    
    params = {
        "method": "SUBSCRIBE",
        "params": SYMBOLS,
        "id": next(id_gen)
    }
    ws.send(json.dumps(params))

def on_close(ws, close_status_code, close_msg):
    """Handle WebSocket closure."""
    print("WebSocket connection closed!")

def on_error(ws, error):
    """Handle WebSocket errors."""
    print(f"WebSocket Error: {error}")

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
    """Run WebSocket with error handling."""
    while True:
        try:
            ws.run_forever(sslopt=ssl_options)
        except Exception as e:
            print(f"WebSocket Error: {e}. Reconnecting in 5 seconds...")
            time.sleep(5)

def subscribe_to_dynamic_coin(symbol_name):
    """Subscribe to a new dynamic coin."""
    pair = format_binance_ticker_symbols([symbol_name])
    msg = {
        "method": "SUBSCRIBE",
        "params": pair,
        "id": next(id_gen)
    }
    ws.send(json.dumps(msg))
    print(f"Subscribed to {pair}")

def start_price_websocket():
    """Load preferences, subscribe to new coins, and run WebSocket in background."""
    load_user_preferences()  # Load user preferences before starting WebSocket

    # Start WebSocket in a separate daemon thread
    run_websocket()

    print("WebSocket started in the background.")


def main():
    """Main function to start the WebSocket connection with updated preferences."""
    load_user_preferences()  # Load preferences before starting
    thread = threading.Thread(target=run_websocket, daemon=True)
    thread.start()
    thread.join()

if __name__ == "__main__":
    start_price_websocket()  # Use upgrade_price() to ensure preferences are loaded first
