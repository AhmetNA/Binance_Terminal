import websocket
import json
import threading
import time
import ssl

""" FAVORITE COINS """
def load_fav_coins():
    with open('Binance_Terminal/app/fav_coins.json', 'r') as file:
        return json.load(file)

def save_fav_coins(data):
    with open('Binance_Terminal/app/fav_coins.json', 'w') as file:
        json.dump(data, file, indent=4)
        
# Update the current price in the fav_coins data
def update_fav_coins(symbol, new_price):
    data = load_fav_coins()
    for coin in data['coins']:
        if coin['symbol'].lower() == symbol.lower():
            coin['values']['current'] = new_price
            break
    save_fav_coins(data)
    
    
def update_dynamic_coin(symbol, new_price):
    """Dynamic coin'in fiyatını güncelle."""
    data = load_fav_coins()
    if isinstance(data['dynamic_coin'], list) and data['dynamic_coin']:
        data['dynamic_coin'][0]['symbol'] = symbol.upper()
        data['dynamic_coin'][0]['values']['current'] = new_price
    save_fav_coins(data)


        
""" SYMBOLS """
def exact_symbol_pair(SYMBOLS):
    """Enter symbolname_usdt and return symbolname@ticker"""
    return [symbol.lower() + "@ticker" for symbol in SYMBOLS]


data = load_fav_coins()
Fav_symbols = [coin['symbol'] for coin in data['coins']]
SYMBOLS = exact_symbol_pair(Fav_symbols)

def add_dynamic_coin(symbol):
    """symbol must be symbolname.usdt"""
    symbol = symbol.replace(".", "")
    data = load_fav_coins()
    data['dynamic_coin'][0]['symbol'] = symbol.upper()
    data['dynamic_coin'][0]['name'] = symbol[:-4].upper()
    dynamic_coin_subs(symbol)
    save_fav_coins(data)




        
        
""" WEBSOCKET CONNECTION """
url = "wss://stream.binance.com:9443/ws"

# ID generator for each subscription
def id_generator():
    n = 1
    while True:
        yield n
        n += 1

id_gen = id_generator()


def on_message(ws, message):
    """WebSocket'ten gelen mesajları işle."""
    data = json.loads(message)
    symbol = data['s']
    new_price = float(data['c'])
    print(f"{symbol} price: {new_price} USDT")

    # Favorite coins check
    if symbol.lower() in [coin['symbol'].lower() for coin in load_fav_coins()['coins']]:
        update_fav_coins(symbol, new_price)

    # Dynamic coin check
    dynamic_coin = load_fav_coins().get('dynamic_coin', [])
    if isinstance(dynamic_coin, list) and dynamic_coin:
        if symbol.lower() == dynamic_coin[0]['symbol'].lower():
            update_dynamic_coin(symbol, new_price)

def on_open(ws):
    """This is function gets prices of favorite coins currently"""
    """Subscribe to the favorite coins"""
    print("WebSocket connection opened!")
    params = {
        "method": "SUBSCRIBE",
        "params": SYMBOLS,
        "id": next(id_gen)
    }
    ws.send(json.dumps(params))

def on_close(ws, close_status_code, close_msg):
    print("Websocket connection closed!")

def on_error(ws, error):
    print(f"WebSocket Error: {error}")


ws = websocket.WebSocketApp(
    url,
    on_open=on_open,
    on_message=on_message,
    on_close=on_close,
    on_error=on_error
)

ssl_options = {
        "ssl_version": ssl.PROTOCOL_TLSv1_2  # Enforce TLS 1.2
    }



""" THREADING """

def run_websocket():
    ws.run_forever(sslopt=ssl_options)

def dynamic_coin_subs(symbol_name):
    """
    Function to subscribe to a new coin
    """
    pair = exact_symbol_pair([symbol_name])
    msg = {
        "method": "SUBSCRIBE",
        "params": pair,
        "id": next(id_gen)
    }
    ws.send(json.dumps(msg))
    print(f"Subscribed to {pair}")



        
def upgrade_price():
    while True:
        th_ws = threading.Thread(target=run_websocket, daemon=True)
        th_ws.start()
        th_ws.join()
        print("WebSocket encountered an error. Restarting...")
        time.sleep(3)
    

def main():
    while True:
        th_ws = threading.Thread(target=run_websocket, daemon=True)
        th_ws.start()
        th_ws.join()
        print("WebSocket encountered an error. Restarting...")
        time.sleep(5)


if __name__ == "__main__":
    main()
