"""
symbol_utils.py
Symbol validation ve formatlama utilities.
"""

import logging
import sys
import os

# Add src to path for core imports (optimized)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import TICKER_SUFFIX


def format_binance_ticker_symbols(symbols):
    """Format symbols for Binance ticker subscription"""
    return [symbol.lower() + TICKER_SUFFIX for symbol in symbols]


def validate_symbol_for_binance(symbol):
    """Validate if a symbol exists on Binance exchange - sync version with requests"""
    try:
        import requests
        url = "https://api.binance.com/api/v3/exchangeInfo"
        
        # Requests kullanarak sync API çağrısı
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            valid_symbols = [s['symbol'] for s in data['symbols']]
            is_valid = symbol.upper() in valid_symbols
            logging.info(f"API validation for {symbol}: {is_valid}")
            return is_valid
        else:
            logging.error(f"Failed to fetch exchange info: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        logging.error(f"Network error validating symbol {symbol}: {e}")
        return False
    except Exception as e:
        logging.error(f"Error validating symbol {symbol}: {e}")
        return False


def validate_symbol_simple(symbol):
    """Simple symbol validation - only validates known popular USDT pairs"""
    symbol = symbol.upper()
    
    # Known popular USDT pairs that are almost always available
    # Sadece bu coinler için True döndür, diğerleri API validation'a gitsin
    known_usdt_pairs = {
        'BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'BNBUSDT', 'XRPUSDT', 
        'SOLUSDT', 'DOGEUSDT', 'AVAXUSDT', 'DOTUSDT', 'MATICUSDT',
        'LINKUSDT', 'LTCUSDT', 'BCHUSDT', 'XLMUSDT', 'UNIUSDT',
        'ATOMUSDT', 'VETUSDT', 'FILUSDT', 'TRXUSDT', 'ETCUSDT',
        'ALGOUSDT', 'AAVEUSDT', 'MKRUSDT', 'COMPUSDT', 'SUSHIUSDT'
    }
    
    # Sadece bilinen popular pairs için True döndür
    return symbol in known_usdt_pairs


def normalize_symbol(symbol):
    """Normalize symbol format (uppercase)"""
    return symbol.upper() if symbol else ""


def format_user_input_to_binance_ticker(user_input):
    """
    Kullanıcı inputunu Binance ticker formatına çevirir
    Desteklenen formatlar: btc, btcusdt, btc-usdt, BTC, BTCUSDT, BTC-USDT
    Args:
        user_input: Kullanıcının girdiği coin adı
    Returns:
        tuple: (original_input, binance_ticker)
    """
    original_input = user_input
    symbol = user_input.upper().strip()
    
    # Boş input kontrolü
    if not symbol:
        return original_input, ""
    
    # Tire karakterini kaldır (BTC-USDT -> BTCUSDT)
    symbol = symbol.replace('-', '')
    
    # İzin verilen tek coin isimleri (bunlar otomatik olarak USDT ile eşleştirilecek)
    allowed_single_coins = ['BTC', 'ETH', 'BNB', 'ADA', 'XRP', 'SOL', 'DOGE', 'AVAX', 'DOT', 'MATIC', 
                           'LINK', 'LTC', 'BCH', 'XLM', 'UNI', 'ATOM', 'VET', 'FIL', 'TRX', 'ETC', 
                           'ALGO', 'AAVE', 'MKR', 'COMP', 'SUSHI']
    
    # Eğer USDT ile bitiyorsa, direkt kabul et
    if symbol.endswith('USDT'):
        return original_input, symbol
    
    # Eğer sadece izin verilen coin isimlerinden biriyse, USDT ekle
    if symbol in allowed_single_coins:
        binance_ticker = f"{symbol}USDT"
        return original_input, binance_ticker
    
    # Diğer quote asset'ler ile kontrol (BTC, ETH, BNB, USDC, BUSD vb.)
    other_quote_assets = ['USDC', 'BUSD', 'BNB', 'ETH', 'BTC']
    for quote in other_quote_assets:
        if symbol.endswith(quote):
            # Eğer base symbol da bilinen bir coin ise, bu geçersiz kombinasyon
            base_symbol = symbol[:-len(quote)]
            if base_symbol in allowed_single_coins or len(base_symbol) >= 2:
                return original_input, f"ERROR_UNSUPPORTED_QUOTE_{quote}"
    
    # Bilinmeyen kombinasyonları kontrol et (örn: BTCBNB, ETHBTC gibi)
    for coin1 in allowed_single_coins:
        for coin2 in allowed_single_coins:
            if symbol == coin1 + coin2 and coin1 != coin2:
                return original_input, f"ERROR_INVALID_PAIR_{coin1}_{coin2}"
    
    # Eğer hiçbir kurala uymuyorsa, USDT ekle (bilinmeyen coin için)
    binance_ticker = f"{symbol}USDT"
    return original_input, binance_ticker


def validate_and_format_symbol(symbol):
    """
    Validate and format symbol for Binance trading
    Args:
        symbol: Symbol to validate and format
    Returns:
        tuple: (is_valid, formatted_symbol, original_symbol)
    """
    original_input, binance_ticker = format_user_input_to_binance_ticker(symbol)
    
    # Desteklenmeyen quote asset kontrolü
    if binance_ticker.startswith('ERROR_UNSUPPORTED_QUOTE_'):
        return False, binance_ticker, original_input
    
    # Try validation methods in order of preference
    is_valid = False
    
    try:
        # First try the simple validation (fastest, no network)
        if validate_symbol_simple(binance_ticker):
            is_valid = True
            logging.info(f"Symbol {binance_ticker} validated using simple check")
        else:
            # If simple check fails, try API validation
            logging.info(f"Simple validation failed for {binance_ticker}, trying API validation...")
            try:
                is_valid = validate_symbol_for_binance(binance_ticker)
                if is_valid:
                    logging.info(f"Symbol {binance_ticker} validated using API check")
                else:
                    logging.warning(f"Symbol {binance_ticker} not found on Binance")
            except Exception as api_error:
                logging.error(f"API validation failed for {binance_ticker}: {api_error}")
                # If API fails, do NOT assume valid for unknown symbols
                is_valid = False
                
    except Exception as e:
        logging.error(f"Symbol validation failed for {binance_ticker}: {e}")
        is_valid = False
    
    return is_valid, binance_ticker, original_input


def view_coin_format(binance_ticker):
    """
    Binance ticker'ını view formatına çevirir ve base/quote asset'leri ayırır
    Args:
        binance_ticker: Binance formatındaki ticker (örn: BTCUSDT)
    Returns:
        str: View formatı (örn: BTC-USDT)
    """
    ticker = binance_ticker.upper().strip()
    
    # USDT ile bitiyorsa base symbol'ü al
    if ticker.endswith('USDT'):
        base_symbol = ticker[:-4]
        return f"{base_symbol}-USDT"
    else:
        # USDT yoksa direkt return et (hata durumu)
        return ticker


def process_user_coin_input(user_input):
    """
    Comprehensive coin processing for dynamic coin setting
    Args:
        user_input: User's coin input (e.g., 'btc', 'BTC', 'btc-usdt', 'BTCUSDT')
    Returns:
        dict: {
            'success': bool,
            'binance_ticker': str,  # For websocket subscription (e.g., 'BTCUSDT')
            'view_coin_name': str,  # For display (e.g., 'BTC-USDT')
            'original_input': str,  # User's original input
            'error_message': str    # Error message if validation fails
        }
    """
    try:
        # Store original input
        original_input = user_input.strip()
        
        if not original_input:
            return {
                'success': False,
                'binance_ticker': '',
                'view_coin_name': '',
                'original_input': original_input,
                'error_message': 'Coin adı boş olamaz'
            }
        
        # Kullanıcı inputunu Binance ticker formatına çevir
        _, binance_ticker = format_user_input_to_binance_ticker(original_input)
        
        # Desteklenmeyen quote asset kontrolü
        if binance_ticker.startswith('ERROR_UNSUPPORTED_QUOTE_'):
            quote_asset = binance_ticker.split('_')[-1]
            return {
                'success': False,
                'binance_ticker': '',
                'view_coin_name': '',
                'original_input': original_input,
                'error_message': f"Sadece USDT trading pair'leri desteklenmektedir. {quote_asset} desteklenmiyor."
            }
        
        # Geçersiz coin pair kontrolü (örn: BTCBNB, ETHBTC)
        if binance_ticker.startswith('ERROR_INVALID_PAIR_'):
            parts = binance_ticker.split('_')
            coin1, coin2 = parts[2], parts[3]
            return {
                'success': False,
                'binance_ticker': '',
                'view_coin_name': '',
                'original_input': original_input,
                'error_message': f"Geçersiz coin çifti: {coin1}/{coin2}. Lütfen sadece coin adını girin (örn: 'btc', 'eth') veya USDT çifti kullanın (örn: 'btcusdt')."
            }
        
        if not binance_ticker:
            return {
                'success': False,
                'binance_ticker': '',
                'view_coin_name': '',
                'original_input': original_input,
                'error_message': 'Geçersiz coin formatı'
            }
        
        # Symbol'ü validate et (önce simple, sonra API)
        is_valid = False
        
        if validate_symbol_simple(binance_ticker):
            is_valid = True
            logging.info(f"Symbol {binance_ticker} validated using simple check")
        else:
            # Simple check başarısızsa API validation dene
            logging.info(f"Simple validation failed for {binance_ticker}, trying API validation...")
            try:
                is_valid = validate_symbol_for_binance(binance_ticker)
                if is_valid:
                    logging.info(f"Symbol {binance_ticker} validated using API check")
                else:
                    logging.warning(f"Symbol {binance_ticker} not found on Binance")
            except Exception as api_error:
                logging.error(f"API validation failed for {binance_ticker}: {api_error}")
                is_valid = False
        
        if not is_valid:
            return {
                'success': False,
                'binance_ticker': '',
                'view_coin_name': '',
                'original_input': original_input,
                'error_message': f"Coin '{original_input}' not found on Binance."
            }
        
        # View coin name oluştur
        view_coin_name = view_coin_format(binance_ticker)
        
        logging.info(f"Successfully processed coin input: {original_input} -> Ticker: {binance_ticker}, View: {view_coin_name}")
        
        return {
            'success': True,
            'binance_ticker': binance_ticker,
            'view_coin_name': view_coin_name,
            'original_input': original_input,
            'error_message': ''
        }
        
    except Exception as e:
        error_msg = f"Coin işlenirken hata oluştu: {str(e)}"
        logging.error(f"Error processing coin input '{user_input}': {e}")
        return {
            'success': False,
            'binance_ticker': '',
            'view_coin_name': '',
            'original_input': user_input,
            'error_message': error_msg
        }


def validate_coin_before_setting(user_input):
    """
    Validate coin input before setting as dynamic coin
    Args:
        user_input: User's coin input
    Returns:
        tuple: (success, binance_ticker, view_coin_name, error_message)
    """
    result = process_user_coin_input(user_input)
    return (
        result['success'],
        result['binance_ticker'],
        result['view_coin_name'],
        result['error_message']
    )


def split_symbol_pair(symbol):
    """
    Split trading pair into base and quote assets
    Optimized for USDT pairs, falls back to general approach for others
    Args:
        symbol: Trading pair symbol (e.g., 'BTCUSDT', 'ETHBTC')
    Returns:
        tuple: (base_symbol, quote_symbol)
    """
    ticker = normalize_symbol(symbol)
    
    # USDT pairs için optimize edilmiş (bizim ana kullanım)
    if ticker.endswith('USDT'):
        return ticker[:-4], 'USDT'
    
    # Diğer yaygın quote asset'ler
    common_quotes = ['USDC', 'BUSD', 'BNB', 'ETH', 'BTC']
    for quote in common_quotes:
        if ticker.endswith(quote):
            return ticker[:-len(quote)], quote
    
    # Genel yaklaşım - son 3-4 karakter quote olarak kabul et
    if len(ticker) > 6:
        return ticker[:-4], ticker[-4:]
    elif len(ticker) > 3:
        return ticker[:-3], ticker[-3:]
    
    return ticker, ""


if __name__ == "__main__":
    """Test symbol utils functions"""
    print("🚀 Testing Symbol Utils")
    print("=" * 30)
    
    # Test symbol formatting
    symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT']
    formatted = format_binance_ticker_symbols(symbols)
    print(f"📊 Formatted symbols: {formatted}")
    
    # Test format_user_input_to_binance_ticker function
    test_inputs = ['BTC', 'btc', 'BTCUSDT', 'eth', 'ETHUSDT', 'btc-usdt', 'BTC-USDT', 'BTCUSDC', 'ethbusd', 'btcbnb', 'ethbtc', 'bnbeth', 'adabnb', 'randomcoin']
    print(f"\n🔄 Testing format_user_input_to_binance_ticker:")
    for symbol in test_inputs:
        original, formatted = format_user_input_to_binance_ticker(symbol)
        print(f"   {original} -> {formatted}")
    
    # Test simple validation first
    print(f"\n🔍 Testing simple validation:")
    test_symbols = ['BTCUSDT', 'INVALIDTOKEN', 'ETHUSDT']
    for symbol in test_symbols:
        is_valid = validate_symbol_simple(symbol)
        print(f"   {symbol} valid (simple): {is_valid}")
    
    # Test validate_and_format_symbol function
    print(f"\n✅ Testing validate_and_format_symbol:")
    test_symbols = ['BTC', 'ETH', 'INVALIDTOKEN', 'BTCUSDT']
    for symbol in test_symbols:
        is_valid, formatted, original = validate_and_format_symbol(symbol)
        print(f"   {original} -> {formatted} (Valid: {is_valid})")
    
    # Test view_coin_format function
    print(f"\n👁️ Testing view_coin_format:")
    test_view_symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT']
    for symbol in test_view_symbols:
        view_name = view_coin_format(symbol)
        print(f"   {symbol} -> {view_name}")
    
    # Test process_user_coin_input function
    print(f"\n🔍 Testing process_user_coin_input:")
    test_inputs = ['btc', 'BTC', 'eth', 'ETHUSDT', 'btc-usdt', 'BTC-USDT', 'btcusdc', 'btcbnb', 'ethbtc', 'bnbeth', 'invalidcoin', '']
    for user_input in test_inputs:
        result = process_user_coin_input(user_input)
        print(f"   Input: '{user_input}'")
        print(f"     Success: {result['success']}")
        print(f"     Binance Ticker: {result['binance_ticker']}")
        print(f"     View Name: {result['view_coin_name']}")
        if not result['success']:
            print(f"     Error: {result['error_message']}")
        print()
    
    # Test validate_coin_before_setting function
    print(f"\n🎯 Testing validate_coin_before_setting:")
    test_validation_inputs = ['btc', 'eth', 'btc-usdt', 'btcbnb', 'ethbtc', 'invalidtoken']
    for user_input in test_validation_inputs:
        success, ticker, view_name, error = validate_coin_before_setting(user_input)
        print(f"   Input: '{user_input}' -> Success: {success}")
        if success:
            print(f"     Ticker: {ticker}, View: {view_name}")
        else:
            print(f"     Error: {error}")
    
    # Test improved symbol splitting
    test_pairs = ['BTCUSDT', 'ETHBTC', 'ADABNB', 'BNBUSDC', 'SOLUSDT']
    print(f"\n🔄 Testing improved split_symbol_pair:")
    for pair in test_pairs:
        base, quote = split_symbol_pair(pair)
        print(f"   {pair} -> Base: {base}, Quote: {quote}")
    
    print("\n✅ Symbol utils test completed successfully!")
