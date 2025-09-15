"""
Utils package for Binance Terminal
Contains utility functions organized by functionality in subpackages.
"""

# Trading utilities (new structure)
from .trading import (
    validate_trading_symbol,
    get_price,
    get_symbol_info,
    round_quantity,
    calculate_buy_quantity,
    calculate_sell_quantity,
    round_price_to_precision,
    format_quantity_for_binance
)

# Symbol utilities (new structure)
from .symbols import (
    format_binance_ticker_symbols,
    validate_symbol_for_binance,
    validate_symbol_simple,
    normalize_symbol,
    format_user_input_to_binance_ticker,
    view_coin_format,
    process_user_coin_input,
    validate_coin_before_setting
)

# Data management utilities (new structure)
from .data import (
    ensure_config_directory,
    load_fav_coins,
    write_favorite_coins_to_json,
    load_user_preferences
)

# Math utilities (unchanged)
from .math_utils import (
    round_to_precision,
    round_to_step_size,
    calculate_percentage,
    calculate_percentage_change,
    format_currency,
    format_percentage
)

# Order utilities (unchanged)
from .order_utils import (
    handle_binance_api_error,
    validate_order_response,
    extract_order_info,
    calculate_limit_price,
    log_order_execution,
    validate_symbol_format,
    normalize_symbol as normalize_symbol_order,
    prepare_order_log_context
)

__all__ = [
    # Trading utilities
    'validate_trading_symbol',
    'get_price',
    'get_symbol_info',
    'round_quantity',
    'calculate_buy_quantity',
    'calculate_sell_quantity',
    'round_price_to_precision',
    'format_quantity_for_binance',
    
    # Symbol utilities
    'format_binance_ticker_symbols',
    'validate_symbol_for_binance',
    'validate_symbol_simple',
    'normalize_symbol',
    'format_user_input_to_binance_ticker',
    'view_coin_format',
    'process_user_coin_input',
    'validate_coin_before_setting',
    
    # Data management utilities
    'ensure_config_directory',
    'load_fav_coins',
    'write_favorite_coins_to_json',
    'load_user_preferences',
    
    # Math utilities
    'round_to_precision',
    'round_to_step_size',
    'calculate_percentage',
    'calculate_percentage_change',
    'format_currency',
    'format_percentage',
    
    # Order utilities
    'handle_binance_api_error',
    'validate_order_response',
    'extract_order_info',
    'calculate_limit_price',
    'log_order_execution',
    'validate_symbol_format',
    'normalize_symbol_order',
    'prepare_order_log_context'
]
