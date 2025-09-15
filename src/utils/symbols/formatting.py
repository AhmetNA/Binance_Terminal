"""
symbols/formatting.py
Symbol formatting utilities for display and API communication.
"""

import logging

from core.globals import TICKER_SUFFIX


def format_binance_ticker_symbols(symbols):
    """Format symbols for Binance ticker subscription"""
    return [symbol.lower() + TICKER_SUFFIX for symbol in symbols]


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