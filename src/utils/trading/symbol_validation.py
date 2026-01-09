"""
trading/symbol_validation.py
Trading-specific symbol validation utilities.
"""

import logging


def validate_trading_symbol(client, symbol):
    """Binance'de symbol'ün var olup olmadığını kontrol et"""
    try:
        # Binance'de symbol'ün var olup olmadığını kontrol et
        ticker = client.get_symbol_ticker(symbol=symbol)
        if ticker and "price" in ticker:
            logging.debug(f"Symbol {symbol} is valid for trading")  # Changed to DEBUG
            return True
        else:
            logging.warning(f"Symbol {symbol} is not valid for trading")
            return False
    except Exception as e:
        logging.error(f"Error validating symbol {symbol}: {e}")
        return False


def get_symbol_info(client, symbol):
    """Symbol hakkında detaylı bilgi al"""
    try:
        exchange_info = client.get_exchange_info()

        for symbol_info in exchange_info["symbols"]:
            if symbol_info["symbol"] == symbol:
                # Filters'ı daha anlaşılır formata çevir
                filters = {}
                for filter_info in symbol_info["filters"]:
                    filter_type = filter_info["filterType"]
                    filters[filter_type] = filter_info

                symbol_data = {
                    "symbol": symbol_info["symbol"],
                    "status": symbol_info["status"],
                    "baseAsset": symbol_info["baseAsset"],
                    "quoteAsset": symbol_info["quoteAsset"],
                    "filters": filters,
                    "permissions": symbol_info.get("permissions", []),
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


def validate_symbol_format(symbol: str) -> bool:
    """
    @brief Validates if symbol follows Binance naming convention
    @param symbol: Trading symbol to validate
    @return bool: True if symbol format is valid
    """
    if not symbol or not isinstance(symbol, str):
        return False

    symbol = symbol.upper()

    # Basic checks
    if len(symbol) < 6 or len(symbol) > 12:
        return False

    # Must end with common quote currencies
    valid_quotes = ["USDT", "BTC", "ETH", "BNB", "USDC", "BUSD"]
    return any(symbol.endswith(quote) for quote in valid_quotes)


def normalize_symbol(symbol: str) -> str:
    """
    @brief Normalizes trading symbol to standard format
    @param symbol: Raw symbol input
    @return str: Normalized symbol
    """
    if not symbol:
        raise ValueError("Symbol cannot be empty")

    # Convert to uppercase and remove whitespace
    normalized = symbol.upper().strip()

    # Validate format
    if not validate_symbol_format(normalized):
        raise ValueError(f"Invalid symbol format: {symbol}")

    return normalized
