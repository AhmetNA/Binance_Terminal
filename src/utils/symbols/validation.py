"""
symbols/validation.py
Symbol validation utilities for Binance exchange.
"""

import logging
import requests


def validate_symbol_for_binance(symbol):
    """Validate if a symbol exists on Binance exchange - sync version with requests"""
    try:
        url = "https://api.binance.com/api/v3/exchangeInfo"
        
        # Requests kullanarak sync API çağrısı
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            valid_symbols = [s['symbol'] for s in data['symbols']]
            is_valid = symbol.upper() in valid_symbols
            logging.debug(f"API validation for {symbol}: {is_valid}")
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


def validate_symbol_format(symbol):
    """Validates if symbol follows Binance naming convention"""
    if not symbol or not isinstance(symbol, str):
        return False
    
    symbol = symbol.upper()
    
    # Basic checks
    if len(symbol) < 6 or len(symbol) > 12:
        return False
    
    # Must end with common quote currencies
    valid_quotes = ['USDT', 'BTC', 'ETH', 'BNB', 'USDC', 'BUSD']
    return any(symbol.endswith(quote) for quote in valid_quotes)


def validate_and_format_symbol(symbol):
    """
    Validate and format symbol for Binance trading
    Args:
        symbol: Symbol to validate and format
    Returns:
        tuple: (is_valid, formatted_symbol, original_symbol)
    """
    from .formatting import format_user_input_to_binance_ticker
    
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
            # logging.debug(f"Symbol {binance_ticker} validated using simple check")
        else:
            # If simple check fails, try API validation
            logging.debug(f"Simple validation failed for {binance_ticker}, trying API validation...")
            try:
                is_valid = validate_symbol_for_binance(binance_ticker)
                if is_valid:
                    logging.debug(f"Symbol {binance_ticker} validated using API check")
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


def validate_coin_before_setting(user_input):
    """
    Validate coin input before setting as dynamic coin
    Args:
        user_input: User's coin input
    Returns:
        tuple: (success, binance_ticker, view_coin_name, error_message)
    """
    from .processing import process_user_coin_input
    
    result = process_user_coin_input(user_input)
    return (
        result['success'],
        result['binance_ticker'],
        result['view_coin_name'],
        result['error_message']
    )