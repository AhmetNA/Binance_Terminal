"""
trading/price_operations.py
Price-related trading utilities.
"""

import logging

from .symbol_validation import validate_trading_symbol


def get_price(client, SYMBOL):
    """Symbol için mevcut fiyatı al"""
    try:
        # Önce symbol'ü validate et
        if not validate_trading_symbol(client, SYMBOL):
            raise ValueError(f"Invalid trading symbol: {SYMBOL}")
        
        # Ticker bilgisini al
        ticker = client.get_symbol_ticker(symbol=SYMBOL)
        current_price = float(ticker['price'])
        
        logging.debug(f"{SYMBOL} current price: {current_price}")  # Changed to DEBUG
        return current_price
        
    except Exception as e:
        error_msg = f"Error getting price for {SYMBOL}: {e}"
        print(error_msg)
        logging.error(error_msg)
        logging.exception(f"Full traceback for {SYMBOL} price error:")
        raise


def round_price_to_precision(price, symbol_info):
    """Fiyatı Binance'in sembol için gereken precision'a göre yuvarla"""
    try:
        # PRICE_FILTER'ı bul
        price_filter = symbol_info['filters'].get('PRICE_FILTER')
        if price_filter:
            tick_size = float(price_filter['tickSize'])
            
            # tick_size'ın decimal sayısını bul
            tick_str = f"{tick_size:.10f}".rstrip('0')
            if '.' in tick_str:
                decimals = len(tick_str.split('.')[1])
            else:
                decimals = 0
            
            # Fiyatı tick size'a göre yuvarla
            factor = 1 / tick_size
            rounded_price = round(price * factor) / factor
            
            # Decimal precision'ı ayarla
            rounded_price = round(rounded_price, decimals)
            
            logging.debug(f"Rounded price {price} to {rounded_price} (tick: {tick_size})")
            return rounded_price
        else:
            logging.warning(f"PRICE_FILTER not found, using 2 decimal places")
            return round(price, 2)
            
    except Exception as e:
        logging.error(f"Error rounding price {price}: {e}")
        return round(price, 2)