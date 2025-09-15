"""
trading_utils.py
Trading işlemleri için yardımcı fonksiyonlar ve utilities.
"""

import logging
import os
import sys

from utils.math_utils import round_to_step_size
from services.client import prepare_client
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
            
            return rounded_quantity  # Float olarak döndür
        else:
            logging.warning(f"LOT_SIZE filter not found, using raw quantity")
            return base_quantity  # Float olarak döndür
            
    except Exception as e:
        logging.error(f"Error calculating buy quantity: {e}")
        raise


def format_quantity_for_binance(quantity: float) -> str:
    """Quantity'yi Binance API için uygun string formatına çevir (scientific notation'sız)"""
    try:
        from decimal import Decimal, getcontext
        import re
        
        getcontext().prec = 28
        
        # Input validation
        if not isinstance(quantity, (int, float, Decimal)):
            raise ValueError(f"Invalid quantity type: {type(quantity)}")
        
        if quantity < 0:
            raise ValueError(f"Negative quantity not allowed: {quantity}")
        
        # Sıfır durumu
        if quantity == 0:
            return "0"
            
        # Çok küçük sayılar için özel işlem
        if quantity < 1e-20:
            return "0"
        
        # Decimal kullanarak precision kaybını önle
        dec_qty = Decimal(str(quantity))
        
        # Normal formatla çevir ve gereksiz sıfırları kaldır
        formatted = f"{dec_qty:f}".rstrip('0').rstrip('.')
        
        # Boş string kontrolü
        if not formatted or formatted == '.' or formatted == '':
            formatted = "0"
        
        # Binance API için geçerli karakter kontrolü (sadece sayılar ve nokta)
        if not re.match(r'^[0-9]+(\.[0-9]+)?$', formatted):
            # Geçersiz karakterleri temizle
            clean_formatted = re.sub(r'[^0-9.]', '', formatted)
            
            # Çoklu nokta kontrolü
            if clean_formatted.count('.') > 1:
                parts = clean_formatted.split('.')
                clean_formatted = parts[0] + '.' + ''.join(parts[1:])
            
            # Başında nokta varsa 0 ekle
            if clean_formatted.startswith('.'):
                clean_formatted = '0' + clean_formatted
            
            # Sadece nokta varsa 0 yap
            if clean_formatted == '.':
                clean_formatted = '0'
                
            formatted = clean_formatted
        
        # Son geçerlilik kontrolü
        if not re.match(r'^[0-9]+(\.[0-9]+)?$', formatted):
            logging.warning(f"Quantity format still invalid after cleaning: {quantity} -> {formatted}, using fallback")
            # Fallback: basit string formatı
            formatted = f"{float(quantity):.8f}".rstrip('0').rstrip('.')
            if not formatted or formatted == '.':
                formatted = "0"
        
        # Maksimum 20 karakter uzunluk kontrolü (Binance API limiti)
        if len(formatted) > 20:
            # Decimal kısmını kısalt
            if '.' in formatted:
                integer_part, decimal_part = formatted.split('.')
                max_decimal_len = 20 - len(integer_part) - 1  # -1 for the dot
                if max_decimal_len > 0:
                    formatted = f"{integer_part}.{decimal_part[:max_decimal_len]}"
                else:
                    formatted = integer_part
            else:
                formatted = formatted[:20]
        
        return formatted
        
    except Exception as e:
        logging.error(f"Error formatting quantity {quantity}: {e}")
        # Fallback: basit string formatı ile güvenli format
        try:
            if isinstance(quantity, (int, float)) and quantity >= 0:
                if quantity >= 1:
                    # Büyük sayılar için 8 decimal
                    formatted = f"{quantity:.8f}".rstrip('0').rstrip('.')
                else:
                    # Küçük sayılar için 12 decimal
                    formatted = f"{quantity:.12f}".rstrip('0').rstrip('.')
                
                if not formatted or formatted == '.':
                    formatted = "0"
                
                return formatted
            else:
                return "0"
        except:
            logging.error(f"Fallback formatting also failed for quantity: {quantity}")
            return "0"


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
            
            return rounded_quantity  # Float olarak döndür
        else:
            logging.warning(f"LOT_SIZE filter not found, using raw quantity")
            return asset_amount  # Float olarak döndür
            
    except Exception as e:
        logging.error(f"Error calculating sell quantity: {e}")
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
