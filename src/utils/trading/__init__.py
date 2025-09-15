"""
trading package for Binance Terminal
Contains trading-related utilities organized by functionality.
"""

from .symbol_validation import (
    validate_trading_symbol,
    get_symbol_info
)

from .price_operations import (
    get_price,
    round_price_to_precision
)

from .quantity_calculations import (
    round_quantity,
    calculate_buy_quantity,
    calculate_sell_quantity,
    format_quantity_for_binance
)

__all__ = [
    # Symbol validation
    'validate_trading_symbol',
    'get_symbol_info',
    
    # Price operations
    'get_price',
    'round_price_to_precision',
    
    # Quantity calculations
    'round_quantity',
    'calculate_buy_quantity',
    'calculate_sell_quantity',
    'format_quantity_for_binance'
]