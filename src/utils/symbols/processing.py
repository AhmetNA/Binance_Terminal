"""
symbols/processing.py
Advanced symbol processing for user input handling.
"""

import logging

from .formatting import format_user_input_to_binance_ticker, view_coin_format
from .validation import validate_symbol_simple, validate_symbol_for_binance


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
            # logging.debug(f"Symbol {binance_ticker} validated using simple check")
        else:
            # Simple check başarısızsa API validation dene
            logging.debug(f"Simple validation failed for {binance_ticker}, trying API validation...")
            try:
                is_valid = validate_symbol_for_binance(binance_ticker)
                if is_valid:
                    logging.debug(f"Symbol {binance_ticker} validated using API check")
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
        
        logging.debug(f"Successfully processed coin input: {original_input} -> Ticker: {binance_ticker}, View: {view_coin_name}")
        
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