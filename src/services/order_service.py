from binance.client import Client
import time
from dotenv import load_dotenv
import os
import math
import logging
import datetime

# Import centralized paths
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.paths import PREFERENCES_FILE, ENV_FILE, SETTINGS_DIR, PROJECT_ROOT

"""
order_service.py
This file handles the creation and execution of different types of orders using a class-based approach.
The new structure includes OrderManager, OrderFactory, and specific order classes for better organization.
Depending on the chosen style (Hard_Buy, Hard_Sell, Soft_Buy, Soft_Sell), it creates appropriate
order objects and executes them. The main function demonstrates the order creation process
and showcases how buy preferences and balances are used with the new class structure.
"""

# Module-level cache for preferences
_CACHED_PREFERENCES = None
_PREFERENCE_CACHE_TIME = None

# Module-level cache for Binance client
_CACHED_CLIENT = None
_CLIENT_CACHE_TIME = None

def _load_preferences_once():
    """
    @brief Preferences'ları bir kez yükler ve cache'ler - module seviyesinde
    @return tuple: (soft_risk, hard_risk)
    """
    global _CACHED_PREFERENCES
    
    if _CACHED_PREFERENCES is not None:
        return _CACHED_PREFERENCES
    
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
            
        _CACHED_PREFERENCES = (soft_risk, hard_risk)
        logging.info(f"Preferences cached at module level: soft_risk={soft_risk:.1%}, hard_risk={hard_risk:.1%}")
        return _CACHED_PREFERENCES
        
    except Exception as e:
        logging.error(f"Error loading preferences: {e}")
        # Fallback değerler
        _CACHED_PREFERENCES = (0.10, 0.20)  # %10 soft, %20 hard
        logging.warning(f"Using fallback preferences: {_CACHED_PREFERENCES}")
        return _CACHED_PREFERENCES

def _initialize_client_once():
    """
    @brief Client'ı bir kez initialize eder ve cache'ler - module seviyesinde
    @return tuple: (soft_risk_percent, hard_risk_percent)
    """
    global _CACHED_CLIENT
    
    if _CACHED_CLIENT is None:
        try:
            load_dotenv(ENV_FILE, override=True)
            api_key = os.getenv('BINANCE_API_KEY')
            api_secret = os.getenv('BINANCE_API_SECRET')
            
            if not api_key or not api_secret:
                raise ValueError("API anahtarları bulunamadı!")
                
            _CACHED_CLIENT = Client(api_key, api_secret)
            _CACHED_CLIENT.API_URL = "https://testnet.binance.vision/api"  # Use Binance testnet
            logging.info("🚀 Binance client cached at module level")
            return _CACHED_CLIENT
        except Exception as e:
            print(f"❌ Binance API bağlantı hatası: {e}")
            logging.error(f"Error preparing Binance client: {e}")
            logging.exception("Full traceback for client preparation error:")
            raise
    else:
        # Cache'den döndür - çok hızlı!
        return _CACHED_CLIENT

def prepare_client():
    """
    @brief Prepares and returns a cached Binance API client instance.
    @return Client: Binance API client instance (cached).
    """
    return _initialize_client_once()

def force_client_reload():
    """
    @brief Client cache'ini temizler ve yeniden yüklemeye zorlar
    """
    global _CACHED_CLIENT
    _CACHED_CLIENT = None
    logging.info("🔄 Forcing client reload due to configuration change")
    client = _initialize_client_once()
    logging.info("✅ Client cache reloaded successfully")
    return client

def get_cached_client_info():
    """
    @brief Debug için cache durumunu gösterir
    @return dict: Cache durumu hakkında bilgi
    """
    global _CACHED_CLIENT
    return {
        'is_cached': _CACHED_CLIENT is not None,
        'client_type': type(_CACHED_CLIENT).__name__ if _CACHED_CLIENT else None,
        'api_url': getattr(_CACHED_CLIENT, 'API_URL', None) if _CACHED_CLIENT else None
    }

# Module import edildiğinde otomatik olarak yükle (lazy loading)
# Yoruma alıyoruz çünkü ilk çağrıda yüklenecek


def get_buy_preferences():
    """
    @brief Returns cached preferences - super fast!
    @return tuple: A tuple containing soft risk and hard risk percentages.
    """
    global _CACHED_PREFERENCES
    
    # Cache'den döndür - çok hızlı!
    if _CACHED_PREFERENCES is None:
        _CACHED_PREFERENCES = _load_preferences_once()
    
    return _CACHED_PREFERENCES


def reload_preferences():
    """
    @brief Forces reload of preferences from file
    @return tuple: (soft_risk, hard_risk)
    """
    global _CACHED_PREFERENCES
    _CACHED_PREFERENCES = None
    return _load_preferences_once()


def force_preferences_reload():
    """
    @brief Public function to force reload preferences - used by UI/settings
    @return tuple: (soft_risk, hard_risk)
    """
    logging.info("🔄 Forcing preferences reload due to settings change")
    return reload_preferences()


def get_cached_preferences_info():
    """
    @brief Returns information about current cached preferences
    @return dict: Cache status and values
    """
    global _CACHED_PREFERENCES
    return {
        'is_cached': _CACHED_PREFERENCES is not None,
        'values': _CACHED_PREFERENCES,
        'soft_risk_percent': f"{_CACHED_PREFERENCES[0]:.1%}" if _CACHED_PREFERENCES else None,
        'hard_risk_percent': f"{_CACHED_PREFERENCES[1]:.1%}" if _CACHED_PREFERENCES else None
    }
    

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

def validate_trading_symbol(client, symbol):
    """
    @brief Validates if a trading symbol exists on Binance.
    @param client: Binance API client instance.
    @param symbol: Trading pair symbol (e.g., 'BTCUSDT').
    @return bool: True if valid, False otherwise.
    """
    try:
        exchange_info = client.get_exchange_info()
        valid_symbols = [s['symbol'] for s in exchange_info['symbols']]
        return symbol.upper() in valid_symbols
    except Exception as e:
        logging.error(f"Error validating symbol {symbol}: {e}")
        return False

def get_price(client, SYMBOL):
    """
    @brief Retrieves and returns the current market price of the specified trading pair.
    @param client: Binance API client instance.
    @param SYMBOL: Trading pair symbol (e.g., 'BTCUSDT').
    @return float: Current price of the trading pair.
    """
    try:
        SYMBOL = SYMBOL.upper()
        
        # Sembol validasyonu ekle
        if not validate_trading_symbol(client, SYMBOL):
            raise ValueError(f"Invalid trading symbol: {SYMBOL} - This symbol is not available on Binance")
        
        ticker = client.get_symbol_ticker(symbol=SYMBOL)
        price = float(ticker['price'])
        return price
    except ValueError as ve:
        # ValueError'u olduğu gibi re-raise et
        print(f"❌ {SYMBOL} fiyat sorgulama hatası: {ve}")
        logging.error(f"Error retrieving price for {SYMBOL}: {ve}")
        logging.exception("Full traceback for price retrieval error:")
        raise
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
        from models import MarketBuyOrder, RiskLevel
        
        # Cache'den al - çok hızlı! (~0.001ms)
        risk_preferences = get_buy_preferences()
        order_obj = MarketBuyOrder(client, SYMBOL, RiskLevel.HARD, risk_preferences)
        order = order_obj.execute()
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
        from models import MarketSellOrder, RiskLevel
        
        # Cache'den al - çok hızlı!
        risk_preferences = get_buy_preferences()
        order_obj = MarketSellOrder(client, SYMBOL, RiskLevel.HARD, risk_preferences)
        order = order_obj.execute()
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
        from models import MarketBuyOrder, RiskLevel
        
        # Cache'den al - çok hızlı!
        risk_preferences = get_buy_preferences()
        order_obj = MarketBuyOrder(client, SYMBOL, RiskLevel.SOFT, risk_preferences)
        order = order_obj.execute()
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
        from models import MarketSellOrder, RiskLevel
        
        # Cache'den al - çok hızlı!
        risk_preferences = get_buy_preferences()
        order_obj = MarketSellOrder(client, SYMBOL, RiskLevel.SOFT, risk_preferences)
        order = order_obj.execute()
        return order
        
    except Exception as e:
        print(f"❌ Soft Sell order hatası - {SYMBOL}: {e}")
        logging.error(f"Error in soft_sell_order for {SYMBOL}: {e}")
        logging.exception("Full traceback for soft_sell_order error:")
        raise

def make_order(Style, Symbol):
    """
    @brief Executes an order based on the specified style and symbol using the new class-based approach.
    @param Style: The type of order to execute ("Hard_Buy", "Hard_Sell", "Soft_Buy", "Soft_Sell").
    @param Symbol: Trading pair symbol (e.g., "BTCUSDT").
    @return dict: Details of the executed order.
    """
    try:
        from .data_manager import data_manager
        from models import OrderManager
        
        client = prepare_client()
        wallet_before = retrieve_usdt_balance(client)
        
        # Cache'den risk tercihlerini al - çok hızlı!
        risk_preferences = get_buy_preferences()
        
        # OrderManager ile order'ı execute et
        order_manager = OrderManager(client, risk_preferences)
        order = order_manager.execute_order(Style, Symbol)
        
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
    @brief Main function to demonstrate the order creation process using the new class-based approach.
    """
    try:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        
        # Client'ı hazırla
        client = prepare_client()
        symbol = "btc"
        
        # Cache'den risk tercihlerini al - çok hızlı!
        risk_preferences = get_buy_preferences()
        
        # OrderManager kullanarak order execute et
        from models import OrderManager
        order_manager = OrderManager(client, risk_preferences)
        
        # Hard buy order örneği
        result = order_manager.execute_order("Hard_Buy", symbol)
        print(f"✅ Order executed successfully: {result}")
        
    except Exception as e:
        print(f"❌ MAIN FUNCTION HATASI: {e}")
        logging.error(f"Error in main function: {e}")
        logging.exception("Full traceback for main function error:")


def get_available_order_types():
    """
    @brief Returns available order types for UI components.
    @return list: List of available order types.
    """
    from models import OrderManager
    
    # Dummy client ve risk preferences ile OrderManager oluştur
    dummy_manager = OrderManager(None, None)
    return dummy_manager.get_available_order_styles()


def validate_order_request(order_style: str, symbol: str) -> tuple:
    """
    @brief Validates an order request before execution.
    @param order_style: Order style to validate
    @param symbol: Symbol to validate
    @return tuple: (is_valid: bool, error_message: str or None)
    """
    try:
        from models import OrderManager
        
        # Order style validasyonu
        dummy_manager = OrderManager(None, None)
        if not dummy_manager.validate_order_style(order_style):
            return False, f"Invalid order style: {order_style}"
        
        # Symbol format kontrolü
        if not symbol or len(symbol.strip()) == 0:
            return False, "Symbol cannot be empty"
        
        # Temel symbol format kontrolü
        symbol = symbol.upper().strip()
        if not symbol.replace("USDT", "").isalpha():
            return False, f"Invalid symbol format: {symbol}"
        
        return True, None
        
    except Exception as e:
        return False, f"Validation error: {e}"


def create_order_summary(order_style: str, symbol: str, risk_preferences: tuple = None) -> dict:
    """
    @brief Creates an order summary without executing it.
    @param order_style: Order style
    @param symbol: Trading symbol
    @param risk_preferences: Risk preferences tuple
    @return dict: Order summary information
    """
    try:
        from models import OrderFactory, RiskLevel
        
        if not risk_preferences:
            # Cache'den al - çok hızlı!
            risk_preferences = get_buy_preferences()
        
        # Client'sız order objesi oluştur (sadece bilgi için)
        order = OrderFactory.create_order(order_style, None, symbol, risk_preferences)
        
        return {
            'order_style': order_style,
            'symbol': order.symbol,
            'side': order.side.value,
            'order_type': order.order_type.value,
            'risk_level': order.risk_level.value,
            'risk_percentage': order.get_risk_percentage(order.risk_level) * 100,
            'valid': True
        }
        
    except Exception as e:
        return {
            'order_style': order_style,
            'symbol': symbol,
            'error': str(e),
            'valid': False
        }
    

if __name__ == "__main__":
    main()
