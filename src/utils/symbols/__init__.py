"""
symbols package for Binance Terminal
Contains symbol-related utilities organized by functionality.
"""

from .validation import (
    validate_symbol_for_binance,
    validate_symbol_simple,
    validate_symbol_format,
    validate_and_format_symbol,
    validate_coin_before_setting,
)

from .formatting import (
    format_binance_ticker_symbols,
    normalize_symbol,
    format_user_input_to_binance_ticker,
    view_coin_format,
)

from .processing import process_user_coin_input

__all__ = [
    # Validation functions
    "validate_symbol_for_binance",
    "validate_symbol_simple",
    "validate_symbol_format",
    "validate_and_format_symbol",
    "validate_coin_before_setting",
    # Formatting functions
    "format_binance_ticker_symbols",
    "normalize_symbol",
    "format_user_input_to_binance_ticker",
    "view_coin_format",
    # Processing functions
    "process_user_coin_input",
]
