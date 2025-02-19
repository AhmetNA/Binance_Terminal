from binance.client import Client
import time
from dotenv import load_dotenv
import os
import websocket
import json
import math

"""QUANTITY_P defines how much percent do you want to buy or sell the symbol depending on your wallet"""
"""TOLERANCE_P defines the percentage of your tolerance to market's price movement"""

def prepare_client():
    load_dotenv()  # Load environment variables from .env file
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')
    client = Client(api_key, api_secret)
    client.API_URL = "https://testnet.binance.vision/api"  # Use Binance testnet
    
    return client

def get_buy_preferences():
    ...

"""Wallet Info Functions"""
def get_account_data(client):
    """Get the account information"""
    """Returns the account data"""
    return client.get_account()

def get_price(client, SYMBOL):
    """Get the current price of the symbol"""
    """ Returns float value of the price"""
    SYMBOL = SYMBOL.upper()
    ticker = client.get_symbol_ticker(symbol=SYMBOL)
    return float(ticker['price'])

def get_amountOf_asset(client, SYMBOL):
    """Avaliable asset in your wallet"""
    """Returs float value of the asset"""
    account_data = get_account_data(client)
    
    SYMBOL = SYMBOL.upper()
    if "USDT" in SYMBOL:
        SYMBOL = SYMBOL.replace("USDT", "")
        
    for asset in account_data['balances']:
        if asset['asset'] == SYMBOL:
            return float(asset['free'])
    return 0.0

def retrieve_usdt_balance(client):
    """ Retrieve the USDT balance from the account data"""
    account_data = get_account_data(client)
    
    for asset in account_data['balances']:
        if asset['asset'] == 'USDT':
            return float(asset['free'])
    return 0.0

def get_symbol_info(client, symbol):
    """
    Get the minQty, maxQty, and stepSize for a given symbol.
    
    Parameters:
    client (Client): Binance API client
    symbol (str): Trading pair symbol (e.g., 'BTCUSDT')
    
    Returns:
    dict: Dictionary containing minQty, maxQty, and stepSize
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
    """Round the quantity to the nearest step size otherwise Binance will throw an error"""
    precision = int(round(-math.log(step_size, 10), 0))
    return round(quantity, precision)

""" ORDER FUNCTIONS """
def place_BUY_order(client, SYMBOL, BUY_QUANTITY_P):
    """Try to buy from market price."""
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
    """Try to buy from market price."""
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
    Hard_buy_percentage = 0.3
    order = place_BUY_order(client, SYMBOL, Hard_buy_percentage)
    return order

def hard_sell_order(client, SYMBOL):
    Hard_sell_percentage = 0.3
    order = place_SELL_order(client, SYMBOL, Hard_sell_percentage)
    return order

def soft_buy_order(client, SYMBOL):
    Soft_buy_percentage = 0.1
    order = place_BUY_order(client, SYMBOL, Soft_buy_percentage)
    return order
    
def soft_sell_order(client, SYMBOL):
    Soft_sell_percentage = 0.1
    order = place_SELL_order(client, SYMBOL, Soft_sell_percentage)
    return order

def main():
    client = prepare_client()

    symbol = "btc"
    price_tolerance = 0.001
    
if __name__ == "__main__":
    main()
