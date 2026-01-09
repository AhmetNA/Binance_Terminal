"""
trading package for Binance Terminal
Contains trading-related utilities organized by functionality.
"""

from .symbol_validation import (
    validate_trading_symbol,
    get_symbol_info,
    validate_symbol_format,
    normalize_symbol,
)

from .price_operations import get_price, round_price_to_precision

from .quantity_calculations import (
    round_quantity,
    calculate_buy_quantity,
    calculate_sell_quantity,
    format_quantity_for_binance,
)

from .operations import (
    validate_amount_type,
    convert_usdt_to_percentage,
    convert_percentage_to_usdt,
    log_order_amount,
    validate_trading_parameters,
    prepare_trade_data,
    OrderExecutionContext,
)

from .order_helpers import (
    validate_order_response,
    extract_order_info,
    calculate_limit_price,
    log_order_execution,
    prepare_order_log_context,
)

__all__ = [
    # Symbol validation
    "validate_trading_symbol",
    "get_symbol_info",
    "validate_symbol_format",
    "normalize_symbol",
    # Price operations
    "get_price",
    "round_price_to_precision",
    # Quantity calculations
    "round_quantity",
    "calculate_buy_quantity",
    "calculate_sell_quantity",
    "format_quantity_for_binance",
    # Operations
    "validate_amount_type",
    "convert_usdt_to_percentage",
    "convert_percentage_to_usdt",
    "log_order_amount",
    "validate_trading_parameters",
    "prepare_trade_data",
    "OrderExecutionContext",
    # Order Helpers
    "validate_order_response",
    "extract_order_info",
    "calculate_limit_price",
    "log_order_execution",
    "prepare_order_log_context",
]
