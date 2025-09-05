"""
trading_utils.py
Trading işlemleri için yardımcı fonksiyonlar ve utilities.
"""

import logging
import os
import sys

# Import centralized paths and client service
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import math utilities
try:
    from .math_utils import round_to_step_size
except ImportError:
    from math_utils import round_to_step_size

try:
    from services.client_service import prepare_client
except ImportError:
    from ..services.client_service import prepare_client


def validate_trading_symbol(client, symbol):
    """Binance'de symbol'ün var olup olmadığını kontrol et"""
    try:
        # Binance'de symbol'ün var olup olmadığını kontrol et
        ticker = client.get_symbol_ticker(symbol=symbol)
        if ticker and 'price' in ticker:
            logging.debug(f"Symbol {symbol} is valid for trading")  # Changed to DEBUG
            return True
        else:
            logging.warning(f"Symbol {symbol} is not valid for trading")
            return False
    except Exception as e:
        logging.error(f"Error validating symbol {symbol}: {e}")
        return False


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


def get_symbol_info(client, symbol):
    """Symbol hakkında detaylı bilgi al"""
    try:
        exchange_info = client.get_exchange_info()
        
        for symbol_info in exchange_info['symbols']:
            if symbol_info['symbol'] == symbol:
                
                # Filters'ı daha anlaşılır formata çevir
                filters = {}
                for filter_info in symbol_info['filters']:
                    filter_type = filter_info['filterType']
                    filters[filter_type] = filter_info
                
                symbol_data = {
                    'symbol': symbol_info['symbol'],
                    'status': symbol_info['status'],
                    'baseAsset': symbol_info['baseAsset'],
                    'quoteAsset': symbol_info['quoteAsset'],
                    'filters': filters,
                    'permissions': symbol_info.get('permissions', [])
                }
                
                logging.debug(f"Symbol info retrieved for {symbol}")
                return symbol_data
        
        # Symbol bulunamadıysa hata fırlat
        raise ValueError(f"Symbol {symbol} not found in exchange info")
        
    except Exception as e:
        error_msg = f"Error getting symbol info for {symbol}: {e}"
        print(error_msg)
        logging.error(error_msg)
        logging.exception(f"Full traceback for {symbol} symbol info error:")
        raise


def round_quantity(quantity, step_size):
    """Quantity'yi step size'a göre yuvarla"""
    return round_to_step_size(quantity, step_size)


def calculate_buy_quantity(usdt_amount, price, symbol_info):
    """Alım için quantity hesapla"""
    try:
        # Base quantity hesapla
        base_quantity = usdt_amount / price
        
        # LOT_SIZE filter'ını bul
        lot_size_filter = symbol_info['filters'].get('LOT_SIZE')
        if lot_size_filter:
            step_size = float(lot_size_filter['stepSize'])
            min_qty = float(lot_size_filter['minQty'])
            
            # Quantity'yi yuvarla
            rounded_quantity = round_quantity(base_quantity, step_size)
            
            # Minimum quantity kontrolü
            if rounded_quantity < min_qty:
                raise ValueError(f"Calculated quantity {rounded_quantity} is below minimum {min_qty}")
            
            return rounded_quantity
        else:
            logging.warning(f"LOT_SIZE filter not found, using raw quantity")
            return base_quantity
            
    except Exception as e:
        logging.error(f"Error calculating buy quantity: {e}")
        raise


def calculate_sell_quantity(asset_amount, symbol_info):
    """Satış için quantity hesapla"""
    try:
        # LOT_SIZE filter'ını bul
        lot_size_filter = symbol_info['filters'].get('LOT_SIZE')
        if lot_size_filter:
            step_size = float(lot_size_filter['stepSize'])
            min_qty = float(lot_size_filter['minQty'])
            
            # Quantity'yi yuvarla
            rounded_quantity = round_quantity(asset_amount, step_size)
            
            # Minimum quantity kontrolü
            if rounded_quantity < min_qty:
                raise ValueError(f"Asset amount {rounded_quantity} is below minimum {min_qty}")
            
            return rounded_quantity
        else:
            logging.warning(f"LOT_SIZE filter not found, using raw quantity")
            return asset_amount
            
    except Exception as e:
        logging.error(f"Error calculating sell quantity: {e}")
        raise


def get_market_data(client, symbol):
    """24 saatlik market verilerini al"""
    try:
        ticker_24hr = client.get_ticker(symbol=symbol)
        
        market_data = {
            'symbol': symbol,
            'price': float(ticker_24hr['lastPrice']),
            'price_change': float(ticker_24hr['priceChange']),
            'price_change_percent': float(ticker_24hr['priceChangePercent']),
            'volume': float(ticker_24hr['volume']),
            'high_24h': float(ticker_24hr['highPrice']),
            'low_24h': float(ticker_24hr['lowPrice'])
        }
        
        logging.debug(f"Market data retrieved for {symbol}")
        return market_data
        
    except Exception as e:
        logging.error(f"Error getting market data for {symbol}: {e}")
        raise


if __name__ == "__main__":
    """Test trading utils functions"""
    print("🚀 Testing Trading Utils")
    print("=" * 30)
    
    try:
        client = prepare_client()
        
        # Test price fetching
        btc_price = get_price(client, "BTCUSDT")
        print(f"💰 BTC Price: ${btc_price:,.2f}")
        
        # Test symbol validation
        is_valid = validate_trading_symbol(client, "BTCUSDT")
        print(f"✅ BTCUSDT valid: {is_valid}")
        
        # Test quantity rounding
        rounded = round_quantity(0.123456789, 0.001)
        print(f"🔢 Rounded quantity: {rounded}")
        
        print("\n✅ Trading utils test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
