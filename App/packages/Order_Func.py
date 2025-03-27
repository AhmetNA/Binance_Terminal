from binance.client import Client
import time
from dotenv import load_dotenv
import os

import ssl
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager
import websocket
import json
import math
import requests

"""
Order_Func.py
This file handles the creation and execution of different types of orders.
Depending on the chosen style (Hard_Buy, Hard_Sell, Soft_Buy, Soft_Sell), it prepares
the client and executes the corresponding order function. The main function demonstrates
the order creation process and showcases how buy preferences and balances are used.
"""

# Constants for file paths
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

SETTINGS_DIR = os.path.join(CURRENT_DIR, '..', 'settings')

PREFERENCES_FILE = os.path.normpath(os.path.join(SETTINGS_DIR, 'Preferences.txt'))
ENV_FILE = os.path.normpath(os.path.join(SETTINGS_DIR, '.env'))


def prepare_client():
    """
    @brief Prepares and returns a Binance API client instance.
    @return Client: Binance API client instance.
    """
    load_dotenv(ENV_FILE)
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')
    client = Client(api_key, api_secret)
    client.API_URL = "https://testnet.binance.vision/api"  # Use Binance testnet

    # Time synchronization
    server_time = client.get_server_time()
    client_time = int(time.time() * 1000)
    time_offset = server_time['serverTime'] - client_time
    client.time_offset = time_offset

    return client


def get_buy_preferences():
    """
    @brief Reads and returns the soft and hard risk percentages from the Preferences.txt file.
    @return tuple: A tuple containing soft risk and hard risk percentages.
    """
    with open(PREFERENCES_FILE, "r") as file:
        for line in file:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("soft_risk"):
                soft_risk = float(line.split("=")[1].strip().replace("%", "")) / 100
            if line.startswith("hard_risk"):
                hard_risk = float(line.split("=")[1].strip().replace("%", "")) / 100
        
    return soft_risk, hard_risk
    

def get_account_data(client):
    """
    @brief Retrieves and returns the account information from the Binance API.
    @param client: Binance API client instance.
    @return dict: Account information.
    """
    return client.get_account()

def get_price(client, SYMBOL):
    """
    @brief Retrieves and returns the current market price of the specified trading pair.
    @param client: Binance API client instance.
    @param SYMBOL: Trading pair symbol (e.g., 'BTCUSDT').
    @return float: Current price of the trading pair.
    """
    SYMBOL = SYMBOL.upper()
    ticker = client.get_symbol_ticker(symbol=SYMBOL)
    return float(ticker['price'])

def get_amountOf_asset(client, SYMBOL):
    """
    @brief Retrieves and returns the available balance of the specified asset in the wallet.
    @param client: Binance API client instance.
    @param SYMBOL: Asset symbol (e.g., 'BTC').
    @return float: Available balance of the asset.
    """
    account_data = get_account_data(client)
    
    SYMBOL = SYMBOL.upper()
    if "USDT" in SYMBOL:
        SYMBOL = SYMBOL.replace("USDT", "")
        
    for asset in account_data['balances']:
        if asset['asset'] == SYMBOL:
            return float(asset['free'])
    return 0.0

def retrieve_usdt_balance(client):
    """
    @brief Retrieves and returns the available USDT balance from the wallet.
    @param client: Binance API client instance.
    @return float: Available USDT balance.
    """
    account_data = get_account_data(client)
    
    for asset in account_data['balances']:
        if asset['asset'] == 'USDT':
            return float(asset['free'])
    return 0.0

def get_symbol_info(client, symbol):
    """
    @brief Retrieves and returns the minQty, maxQty, and stepSize for a given trading pair.
    @param client: Binance API client instance.
    @param symbol: Trading pair symbol (e.g., 'BTCUSDT').
    @return dict: Dictionary containing minQty, maxQty, and stepSize.
    """
    exchange_info = client.get_exchange_info()
    symbol_info = next((s for s in exchange_info['symbols'] if s['symbol'] == symbol), None)

    if symbol_info:
        for filter in symbol_info['filters']:
            if filter['filterType'] == 'LOT_SIZE':
                min_qty = float(filter['minQty'])
                max_qty = float(filter['maxQty'])
                step_size = float(filter['stepSize'])
                return {
                    'minQty': min_qty,
                    'maxQty': max_qty,
                    'stepSize': step_size
                }
    else:
        raise ValueError(f"Symbol {symbol} not found")

def round_quantity(quantity, step_size):
    """
    @brief Rounds the quantity to the nearest step size to comply with Binance's requirements.
    @param quantity: Quantity to be rounded.
    @param step_size: Step size for the trading pair.
    @return float: Rounded quantity.
    """
    precision = int(round(-math.log(step_size, 10), 0))
    return round(quantity, precision)


def place_BUY_order(client, SYMBOL, BUY_QUANTITY_P):
    """
    @brief Attempts to place a market BUY order for a given symbol using a specified percentage of the USDT balance.
    @param client: Binance API client instance.
    @param SYMBOL: Trading pair symbol (e.g., "BTCUSDT").
    @param BUY_QUANTITY_P: Percentage of the total USDT balance to use for the purchase.
    @return dict: Details of the executed order if successful.
    """
    account_data = get_account_data(client)

    if "USDT" not in SYMBOL:
        SYMBOL = SYMBOL + "USDT"
    
    SYMBOL = SYMBOL.upper()
    
    Total_asset_value_usdt = retrieve_usdt_balance(client) * BUY_QUANTITY_P
    current_price = get_price(client, SYMBOL)

    symbol_info = get_symbol_info(client, SYMBOL)
    min_qty = symbol_info['minQty']
    max_qty = symbol_info['maxQty']
    step_size = symbol_info['stepSize']
    
    QUANTITY = round_quantity((Total_asset_value_usdt / current_price), step_size)
    
    try:
        # Create Buy Order
        order = client.create_order(
            symbol=SYMBOL,
            side="BUY",
            type="MARKET",
            quantity= QUANTITY
        )
        price = float(order['fills'][0]['price'])
        amount = float(order['fills'][0]['qty'])
        return order
    except Exception as e:
        print(f"Error: {e}")

def place_SELL_order(client, SYMBOL, SELL_QUANTITY_P):
    """
    @brief Attempts to place a market SELL order for a given symbol using a specified percentage of the asset balance.
    @param client: Binance API client instance.
    @param SYMBOL: Trading pair symbol (e.g., "BTCUSDT").
    @param SELL_QUANTITY_P: Percentage of the total asset balance to sell.
    @return dict: Details of the executed order if successful.
    """
    account_data = get_account_data(client)
    if "USDT" not in SYMBOL:
        SYMBOL = SYMBOL + "USDT"
    
    SYMBOL = SYMBOL.upper()

    symbol_info = get_symbol_info(client, SYMBOL)
    min_qty = symbol_info['minQty']
    max_qty = symbol_info['maxQty']
    step_size = symbol_info['stepSize']
    
    QUANTITY = round_quantity(get_amountOf_asset(client, SYMBOL) * SELL_QUANTITY_P, step_size)
    
    try:
        # Create Sell Order
        order = client.create_order(
            symbol=SYMBOL,
            side="SELL",
            type="MARKET",
            quantity= QUANTITY
        )
        price = float(order['fills'][0]['price'])
        amount = float(order['fills'][0]['qty'])
        return order

    except Exception as e:
        print(f"Error: {e}")
  
def hard_buy_order(client, SYMBOL):
    """
    @brief Places a hard buy order using the hard risk percentage from preferences.
    @param client: Binance API client instance.
    @param SYMBOL: Trading pair symbol (e.g., "BTCUSDT").
    @return dict: Details of the executed order.
    """
    Soft_buy_percentage, Hard_buy_percentage = get_buy_preferences()
    order = place_BUY_order(client, SYMBOL, Hard_buy_percentage)
    return order

def hard_sell_order(client, SYMBOL):
    """
    @brief Places a hard sell order using the hard risk percentage from preferences.
    @param client: Binance API client instance.
    @param SYMBOL: Trading pair symbol (e.g., "BTCUSDT").
    @return dict: Details of the executed order.
    """
    Soft_sell_percentage, Hard_sell_percentage = get_buy_preferences()
    order = place_SELL_order(client, SYMBOL, Hard_sell_percentage)
    return order

def soft_buy_order(client, SYMBOL):
    """
    @brief Places a soft buy order using the soft risk percentage from preferences.
    @param client: Binance API client instance.
    @param SYMBOL: Trading pair symbol (e.g., "BTCUSDT").
    @return dict: Details of the executed order.
    """
    Soft_buy_percentage, Hard_buy_percentage = get_buy_preferences()
    order = place_BUY_order(client, SYMBOL, Soft_buy_percentage)
    return order
    
def soft_sell_order(client, SYMBOL):
    """
    @brief Places a soft sell order using the soft risk percentage from preferences.
    @param client: Binance API client instance.
    @param SYMBOL: Trading pair symbol (e.g., "BTCUSDT").
    @return dict: Details of the executed order.
    """
    Soft_sell_percentage, Hard_sell_percentage = get_buy_preferences()
    order = place_SELL_order(client, SYMBOL, Soft_sell_percentage)
    return order

def make_order(Style, Symbol):
    """
    @brief Executes an order based on the specified style and symbol.
    @param Style: The type of order to execute ("Hard_Buy", "Hard_Sell", "Soft_Buy", "Soft_Sell").
    @param Symbol: Trading pair symbol (e.g., "BTCUSDT").
    @return dict: Details of the executed order.
    """
    client = prepare_client()
    if Style == "Hard_Buy":
        order = hard_buy_order(client, Symbol)
        return order
    elif Style == "Hard_Sell":
        order = hard_sell_order(client, Symbol)
        return order
    elif Style == "Soft_Buy":
        order = soft_buy_order(client, Symbol)
        return order
    elif Style == "Soft_Sell":
        order = soft_sell_order(client, Symbol)
        return order
    else:
        print("Wrong Style")

def main():
    """
    @brief Main function to demonstrate the order creation process.
    """
    client = prepare_client()

    symbol = "btc"
    price_tolerance = 0.001
    
    dolar = retrieve_usdt_balance
    hard , soft = get_buy_preferences()

    hard_buy_order(client, symbol)
    
    
if __name__ == "__main__":
    main()
