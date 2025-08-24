"""
Utils package for Binance Terminal
Contains utility functions organized by functionality.
"""

# Trading utilities
from .trading_utils import (
    validate_trading_symbol,
    get_price,
    get_symbol_info,
    round_quantity,
    calculate_buy_quantity,
    calculate_sell_quantity,
    get_market_data
)

# Symbol utilities
from .symbol_utils import (
    format_binance_ticker_symbols,
    validate_symbol_for_binance,
    validate_symbol_simple,
    normalize_symbol,
    split_symbol_pair
)

# Data management utilities
from .data_utils import (
    ensure_config_directory,
    load_fav_coins,
    write_favorite_coins_to_json,
    load_user_preferences,
    validate_json_structure,
    safe_json_load,
    safe_json_save
)

# Math utilities
from .math_utils import (
    round_to_precision,
    round_to_step_size,
    calculate_percentage,
    calculate_percentage_change,
    clamp_value,
    safe_divide,
    format_currency,
    format_percentage,
    calculate_compound_return,
    calculate_moving_average,
    calculate_volatility,
    normalize_to_range
)

__all__ = [
    # Trading utilities
    'validate_trading_symbol',
    'get_price',
    'get_symbol_info',
    'round_quantity',
    'calculate_buy_quantity',
    'calculate_sell_quantity',
    'get_market_data',
    
    # Symbol utilities
    'format_binance_ticker_symbols',
    'validate_symbol_for_binance',
    'validate_symbol_simple',
    'normalize_symbol',
    'split_symbol_pair',
    
    # Data management utilities
    'ensure_config_directory',
    'load_fav_coins',
    'write_favorite_coins_to_json',
    'load_user_preferences',
    'validate_json_structure',
    'safe_json_load',
    'safe_json_save',
    
    # Math utilities
    'round_to_precision',
    'round_to_step_size',
    'calculate_percentage',
    'calculate_percentage_change',
    'clamp_value',
    'safe_divide',
    'format_currency',
    'format_percentage',
    'calculate_compound_return',
    'calculate_moving_average',
    'calculate_volatility',
    'normalize_to_range'
]
