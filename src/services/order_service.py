from binance.client import Client
import time
from dotenv import load_dotenv
import os
import math
import logging
import datetime

"""
order_service.py
This file handles the creation and execution of different types of orders.
Depending on the chosen style (Hard_Buy, Hard_Sell, Soft_Buy, Soft_Sell), it prepares
the client and executes the corresponding order function. The main function demonstrates
the order creation process and showcases how buy preferences and balances are used.
"""

# Constants for file paths
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '..', '..'))
SETTINGS_DIR = os.path.join(PROJECT_ROOT, 'config')
PREFERENCES_FILE = os.path.join(SETTINGS_DIR, 'Preferences.txt')
ENV_FILE = os.path.join(SETTINGS_DIR, '.env')

def prepare_client():
    """
    @brief Prepares and returns a Binance API client instance.
    @return Client: Binance API client instance.
    """
    try:
        load_dotenv(ENV_FILE, override=True)
        api_key = os.getenv('BINANCE_API_KEY')
        api_secret = os.getenv('BINANCE_API_SECRET')
        
        if not api_key or not api_secret:
            raise ValueError("API anahtarları bulunamadı!")
            
        client = Client(api_key, api_secret)
        client.API_URL = "https://testnet.binance.vision/api"  # Use Binance testnet
        logging.info("Binance API client successfully initialized")
        return client
    except Exception as e:
        print(f"❌ Binance API bağlantı hatası: {e}")
        logging.error(f"Error preparing Binance client: {e}")
        logging.exception("Full traceback for client preparation error:")
        raise


def get_buy_preferences():
    """
    @brief Reads and returns the soft and hard risk percentages from the Preferences.txt file.
    @return tuple: A tuple containing soft risk and hard risk percentages.
    """
    try:
        with open(PREFERENCES_FILE, "r") as file:
            soft_risk = None
            hard_risk = None
            for line in file:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("soft_risk"):
                    soft_risk = float(line.split("=")[1].strip().replace("%", "")) / 100
                elif line.startswith("hard_risk"):
                    hard_risk = float(line.split("=")[1].strip().replace("%", "")) / 100
        
        if soft_risk is None or hard_risk is None:
            raise ValueError("Risk ayarları tam olarak okunamadı!")
            
        logging.info(f"Buy preferences loaded: soft_risk={soft_risk}, hard_risk={hard_risk}")
        return soft_risk, hard_risk
        
    except Exception as e:
        print(f"❌ Risk ayarları okuma hatası: {e}")
        logging.error(f"Error reading buy preferences: {e}")
        logging.error(f"Failed to read from file: {PREFERENCES_FILE}")
        logging.exception("Full traceback for preferences reading error:")
        raise
    

def get_account_data(client):
    """
    @brief Retrieves and returns the account information from the Binance API.
    @param client: Binance API client instance.
    @return dict: Account information.
    """
    try:
        account_data = client.get_account()
        return account_data
    except Exception as e:
        print(f"❌ Hesap bilgileri alma hatası: {e}")
        logging.error(f"Error retrieving account data: {e}")
        logging.exception("Full traceback for account data retrieval error:")
        raise

def get_price(client, SYMBOL):
    """
    @brief Retrieves and returns the current market price of the specified trading pair.
    @param client: Binance API client instance.
    @param SYMBOL: Trading pair symbol (e.g., 'BTCUSDT').
    @return float: Current price of the trading pair.
    """
    try:
        SYMBOL = SYMBOL.upper()
        ticker = client.get_symbol_ticker(symbol=SYMBOL)
        price = float(ticker['price'])
        return price
    except Exception as e:
        print(f"❌ {SYMBOL} fiyat sorgulama hatası: {e}")
        logging.error(f"Error retrieving price for {SYMBOL}: {e}")
        logging.exception("Full traceback for price retrieval error:")
        raise

def get_amountOf_asset(client, SYMBOL):
    """
    @brief Retrieves and returns the available balance of the specified asset in the wallet.
    @param client: Binance API client instance.
    @param SYMBOL: Asset symbol (e.g., 'BTC').
    @return float: Available balance of the asset.
    """
    try:
        original_symbol = SYMBOL
        SYMBOL = SYMBOL.upper()
        if "USDT" in SYMBOL:
            SYMBOL = SYMBOL.replace("USDT", "")
            
        account_data = get_account_data(client)
        
        for asset in account_data['balances']:
            if asset['asset'] == SYMBOL:
                balance = float(asset['free'])
                logging.info(f"Asset balance retrieved for {SYMBOL}: {balance}")
                return balance
                
        logging.warning(f"Asset {SYMBOL} not found in wallet, returning 0.0")
        return 0.0
        
    except Exception as e:
        print(f"❌ {original_symbol} bakiye sorgulama hatası: {e}")
        logging.error(f"Error retrieving asset balance for {original_symbol}: {e}")
        logging.exception("Full traceback for asset balance retrieval error:")
        raise

def retrieve_usdt_balance(client):
    """
    @brief Retrieves and returns the available USDT balance from the wallet.
    @param client: Binance API client instance.
    @return float: Available USDT balance.
    """
    try:
        account_data = get_account_data(client)
        
        for asset in account_data['balances']:
            if asset['asset'] == 'USDT':
                balance = float(asset['free'])
                return balance
                
        logging.warning("USDT not found in wallet, returning 0.0")
        return 0.0
        
    except Exception as e:
        print(f"❌ USDT bakiye sorgulama hatası: {e}")
        logging.error(f"Error retrieving USDT balance: {e}")
        logging.exception("Full traceback for USDT balance retrieval error:")
        raise

def get_symbol_info(client, symbol):
    """
    @brief Retrieves and returns the minQty, maxQty, and stepSize for a given trading pair.
    @param client: Binance API client instance.
    @param symbol: Trading pair symbol (e.g., 'BTCUSDT').
    @return dict: Dictionary containing minQty, maxQty, and stepSize.
    """
    try:
        exchange_info = client.get_exchange_info()
        symbol_info = next((s for s in exchange_info['symbols'] if s['symbol'] == symbol), None)

        if symbol_info:
            for filter in symbol_info['filters']:
                if filter['filterType'] == 'LOT_SIZE':
                    min_qty = float(filter['minQty'])
                    max_qty = float(filter['maxQty'])
                    step_size = float(filter['stepSize'])
                    logging.info(f"Symbol info retrieved for {symbol}: min={min_qty}, max={max_qty}, step={step_size}")
                    return {
                        'minQty': min_qty,
                        'maxQty': max_qty,
                        'stepSize': step_size
                    }
        else:
            raise ValueError(f"Symbol {symbol} not found")
            
    except Exception as e:
        print(f"❌ {symbol} sembol bilgisi alma hatası: {e}")
        logging.error(f"Error retrieving symbol info for {symbol}: {e}")
        logging.exception("Full traceback for symbol info retrieval error:")
        raise

def round_quantity(quantity, step_size):
    """
    @brief Rounds the quantity to the nearest step size to comply with Binance's requirements.
    @param quantity: Quantity to be rounded.
    @param step_size: Step size for the trading pair.
    @return float: Rounded quantity.
    """
    try:
        original_quantity = quantity
        precision = int(round(-math.log(step_size, 10), 0))
        rounded_quantity = round(quantity, precision)
        logging.info(f"Quantity rounded: {original_quantity} → {rounded_quantity} (precision: {precision})")
        return rounded_quantity
    except Exception as e:
        print(f"❌ Miktar yuvarlama hatası: {e}")
        logging.error(f"Error rounding quantity {quantity} with step_size {step_size}: {e}")
        logging.exception("Full traceback for quantity rounding error:")
        raise


def place_BUY_order(client, SYMBOL, BUY_QUANTITY_P):
    """
    @brief Attempts to place a market BUY order for a given symbol using a specified percentage of the USDT balance.
    @param client: Binance API client instance.
    @param SYMBOL: Trading pair symbol (e.g., "BTCUSDT").
    @param BUY_QUANTITY_P: Percentage of the total USDT balance to use for the purchase.
    @return dict: Details of the executed order if successful.
    """
    try:
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
        
        if QUANTITY < min_qty:
            raise ValueError(f"Minimum miktar gereksinimi karşılanmıyor: {QUANTITY} < {min_qty}")
        if QUANTITY > max_qty:
            raise ValueError(f"Maksimum miktar aşılıyor: {QUANTITY} > {max_qty}")
            
        order = client.create_order(
            symbol=SYMBOL,
            side="BUY",
            type="MARKET",
            quantity=QUANTITY
        )
        
        price = float(order['fills'][0]['price'])
        amount = float(order['fills'][0]['qty'])
        total_cost = float(order.get('cummulativeQuoteQty', amount * price))
        
        logging.info(f"BUY order executed: {SYMBOL} - {amount} @ ${price} (Total: ${total_cost})")
        return order
        
    except Exception as e:
        print(f"❌ ALIŞ EMRİ HATASI - {SYMBOL}: {e}")
        logging.error(f"Error placing BUY order for {SYMBOL}: {e}")
        logging.error(f"Order parameters: BUY_QUANTITY_P={BUY_QUANTITY_P}, SYMBOL={SYMBOL}")
        logging.exception("Full traceback for BUY order error:")
        raise


def place_SELL_order(client, SYMBOL, SELL_QUANTITY_P):
    """
    @brief Attempts to place a market SELL order for a given symbol using a specified percentage of the asset balance.
    @param client: Binance API client instance.
    @param SYMBOL: Trading pair symbol (e.g., "BTCUSDT").
    @param SELL_QUANTITY_P: Percentage of the total asset balance to sell.
    @return dict: Details of the executed order if successful.
    """
    try:
        account_data = get_account_data(client)
        if "USDT" not in SYMBOL:
            SYMBOL = SYMBOL + "USDT"
        SYMBOL = SYMBOL.upper()
        
        asset_symbol = SYMBOL.replace('USDT', '')
        available_balance = get_amountOf_asset(client, SYMBOL)
        
        symbol_info = get_symbol_info(client, SYMBOL)
        min_qty = symbol_info['minQty']
        max_qty = symbol_info['maxQty']
        step_size = symbol_info['stepSize']
        
        QUANTITY = round_quantity(available_balance * SELL_QUANTITY_P, step_size)
        
        if QUANTITY < min_qty:
            raise ValueError(f"Minimum miktar gereksinimi karşılanmıyor: {QUANTITY} < {min_qty}")
        if QUANTITY > max_qty:
            raise ValueError(f"Maksimum miktar aşılıyor: {QUANTITY} > {max_qty}")
        if QUANTITY > available_balance:
            raise ValueError(f"Yetersiz bakiye: {QUANTITY} > {available_balance}")
            
        current_price = get_price(client, SYMBOL)
        estimated_usdt = QUANTITY * current_price
        
        order = client.create_order(
            symbol=SYMBOL,
            side="SELL",
            type="MARKET",
            quantity=QUANTITY
        )
        
        price = float(order['fills'][0]['price'])
        amount = float(order['fills'][0]['qty'])
        total_usdt = float(order.get('cummulativeQuoteQty', amount * price))
        
        logging.info(f"SELL order executed: {SYMBOL} - {amount} @ ${price} (Total: ${total_usdt})")
        return order
        
    except Exception as e:
        print(f"❌ SATIŞ EMRİ HATASI - {SYMBOL}: {e}")
        logging.error(f"Error placing SELL order for {SYMBOL}: {e}")
        logging.error(f"Order parameters: SELL_QUANTITY_P={SELL_QUANTITY_P}, SYMBOL={SYMBOL}")
        logging.exception("Full traceback for SELL order error:")
        raise

def hard_buy_order(client, SYMBOL):
    """
    @brief Places a hard buy order using the hard risk percentage from preferences.
    @param client: Binance API client instance.
    @param SYMBOL: Trading pair symbol (e.g., "BTCUSDT").
    @return dict: Details of the executed order.
    """
    try:
        Soft_buy_percentage, Hard_buy_percentage = get_buy_preferences()
        order = place_BUY_order(client, SYMBOL, Hard_buy_percentage)
        logging.info(f"Hard buy order completed for {SYMBOL} with {Hard_buy_percentage*100:.1f}%")
        return order
    except Exception as e:
        print(f"❌ Hard Buy order hatası - {SYMBOL}: {e}")
        logging.error(f"Error in hard_buy_order for {SYMBOL}: {e}")
        logging.exception("Full traceback for hard_buy_order error:")
        raise

def hard_sell_order(client, SYMBOL):
    """
    @brief Places a hard sell order using the hard risk percentage from preferences.
    @param client: Binance API client instance.
    @param SYMBOL: Trading pair symbol (e.g., "BTCUSDT").
    @return dict: Details of the executed order.
    """
    try:
        Soft_sell_percentage, Hard_sell_percentage = get_buy_preferences()
        order = place_SELL_order(client, SYMBOL, Hard_sell_percentage)
        logging.info(f"Hard sell order completed for {SYMBOL} with {Hard_sell_percentage*100:.1f}%")
        return order
    except Exception as e:
        print(f"❌ Hard Sell order hatası - {SYMBOL}: {e}")
        logging.error(f"Error in hard_sell_order for {SYMBOL}: {e}")
        logging.exception("Full traceback for hard_sell_order error:")
        raise

def soft_buy_order(client, SYMBOL):
    """
    @brief Places a soft buy order using the soft risk percentage from preferences.
    @param client: Binance API client instance.
    @param SYMBOL: Trading pair symbol (e.g., "BTCUSDT").
    @return dict: Details of the executed order.
    """
    try:
        Soft_buy_percentage, Hard_buy_percentage = get_buy_preferences()
        order = place_BUY_order(client, SYMBOL, Soft_buy_percentage)
        logging.info(f"Soft buy order completed for {SYMBOL} with {Soft_buy_percentage*100:.1f}%")
        return order
    except Exception as e:
        print(f"❌ Soft Buy order hatası - {SYMBOL}: {e}")
        logging.error(f"Error in soft_buy_order for {SYMBOL}: {e}")
        logging.exception("Full traceback for soft_buy_order error:")
        raise
    
def soft_sell_order(client, SYMBOL):
    """
    @brief Places a soft sell order using the soft risk percentage from preferences.
    @param client: Binance API client instance.
    @param SYMBOL: Trading pair symbol (e.g., "BTCUSDT").
    @return dict: Details of the executed order.
    """
    try:
        Soft_sell_percentage, Hard_sell_percentage = get_buy_preferences()
        order = place_SELL_order(client, SYMBOL, Soft_sell_percentage)
        logging.info(f"Soft sell order completed for {SYMBOL} with {Soft_sell_percentage*100:.1f}%")
        return order
    except Exception as e:
        print(f"❌ Soft Sell order hatası - {SYMBOL}: {e}")
        logging.error(f"Error in soft_sell_order for {SYMBOL}: {e}")
        logging.exception("Full traceback for soft_sell_order error:")
        raise

def make_order(Style, Symbol):
    """
    @brief Executes an order based on the specified style and symbol.
    @param Style: The type of order to execute ("Hard_Buy", "Hard_Sell", "Soft_Buy", "Soft_Sell").
    @param Symbol: Trading pair symbol (e.g., "BTCUSDT").
    @return dict: Details of the executed order.
    """
    try:
        from .data_manager import data_manager
        
        client = prepare_client()
        wallet_before = retrieve_usdt_balance(client)
        
        order = None
        if Style == "Hard_Buy":
            order = hard_buy_order(client, Symbol)
        elif Style == "Hard_Sell":
            order = hard_sell_order(client, Symbol)
        elif Style == "Soft_Buy":
            order = soft_buy_order(client, Symbol)
        elif Style == "Soft_Sell":
            order = soft_sell_order(client, Symbol)
        else:
            error_msg = f"Geçersiz emir tipi: {Style}"
            print(f"❌ {error_msg}")
            logging.error(error_msg)
            return None
        
        if order:
            # Get wallet balance after trade
            wallet_after = retrieve_usdt_balance(client)
            
            # Extract trade information
            price = float(order['fills'][0]['price'])
            quantity = float(order['fills'][0]['qty'])
            total_cost = float(order.get('cummulativeQuoteQty', quantity * price))
            
            balance_change = wallet_after - wallet_before
            
            # Prepare trade data for saving
            trade_data = {
                'timestamp': datetime.datetime.now().isoformat(),
                'symbol': Symbol.upper(),
                'side': 'BUY' if 'Buy' in Style else 'SELL',
                'type': Style,
                'quantity': quantity,
                'price': price,
                'total_cost': total_cost,
                'wallet_before': wallet_before,
                'wallet_after': wallet_after,
                'order_id': order.get('orderId', 'unknown'),
                'binance_data': order  # Store full Binance response
            }
            
            # Save trade to data manager
            data_manager.save_trade(trade_data)
            
            # Take portfolio snapshot after trade (asynchronously to avoid UI freezing)
            try:
                import threading
                from services.portfolio_tracker import portfolio_tracker
                
                def take_snapshot_async():
                    try:
                        portfolio_tracker.take_snapshot()
                    except Exception as e:
                        logging.error(f"Error taking portfolio snapshot in background: {e}")
                
                # Run snapshot in background thread
                snapshot_thread = threading.Thread(target=take_snapshot_async, daemon=True)
                snapshot_thread.start()
                
            except Exception as e:
                logging.error(f"Error starting portfolio snapshot thread: {e}")
            
            logging.info(f"Complete trade executed and saved: {Style} {Symbol} - {quantity} @ {price}")
        
        return order
        
    except Exception as e:
        print(f"❌ TRADING İŞLEMİ HATASI: {e}")
        print(f"Emir tipi: {Style}, Sembol: {Symbol}")
        logging.error(f"Error in make_order: Style={Style}, Symbol={Symbol}, Error={e}")
        logging.exception("Full traceback for make_order error:")
        raise

def main():
    """
    @brief Main function to demonstrate the order creation process.
    """
    try:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        
        client = prepare_client()
        symbol = "btc"
        price_tolerance = 0.001
        hard, soft = get_buy_preferences()
        
        hard_buy_order(client, symbol)
        
    except Exception as e:
        print(f"❌ MAIN FUNCTION HATASI: {e}")
        logging.error(f"Error in main function: {e}")
        logging.exception("Full traceback for main function error:")
    
    
if __name__ == "__main__":
    main()
