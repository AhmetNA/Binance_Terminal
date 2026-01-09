"""
utils/trading/operations.py
Core trading operations and validation logic.
"""

import logging
from typing import Dict, Any, Optional

# Import enums from models to avoid duplication
from models.order_types import OrderSide, OrderType

def validate_amount_type(amount_type: str) -> bool:
    """
    @brief Validates the amount type parameter
    @param amount_type: The amount type to validate
    @return bool: True if valid, False otherwise
    """
    valid_types = ["usdt", "percentage"]
    return amount_type.lower() in valid_types


def convert_usdt_to_percentage(usdt_amount: float, usdt_balance: float) -> float:
    """
    @brief Converts USDT amount to percentage of balance
    @param usdt_amount: The USDT amount
    @param usdt_balance: The current USDT balance
    @return float: Percentage (0.0-1.0)
    """
    if usdt_balance <= 0:
        return 0.0
    return min(usdt_amount / usdt_balance, 1.0)


def convert_percentage_to_usdt(percentage: float, usdt_balance: float) -> float:
    """
    @brief Converts percentage to USDT amount
    @param percentage: The percentage (0.0-1.0)
    @param usdt_balance: The current USDT balance
    @return float: USDT amount
    """
    return usdt_balance * percentage


def log_order_amount(
    amount_or_percentage: float, amount_type: str, balance: Optional[float] = None
) -> None:
    """
    @brief Logs order amount information in a standardized format
    @param amount_or_percentage: The amount or percentage value
    @param amount_type: Type of amount ('usdt' or 'percentage')
    @param balance: Optional balance for additional context
    """
    # Validate input is a number
    if not isinstance(amount_or_percentage, (int, float)):
        logging.error(
            f"❌ Invalid amount_or_percentage type: {type(amount_or_percentage).__name__}"
        )
        return

    if amount_type.lower() == "usdt":
        logging.info(f"💰 Order Amount: ${amount_or_percentage:.2f} USDT")
        if balance is not None and isinstance(balance, (int, float)) and balance > 0:
            percentage = convert_usdt_to_percentage(amount_or_percentage, balance)
            logging.info(f"   📊 Equivalent to: {percentage * 100:.2f}% of balance")
    else:
        logging.info(f"📊 Order Percentage: {amount_or_percentage * 100:.2f}%")
        if balance is not None and isinstance(balance, (int, float)) and balance > 0:
            usdt_amount = convert_percentage_to_usdt(amount_or_percentage, balance)
            logging.info(f"   💰 Equivalent to: ${usdt_amount:.2f} USDT")


def validate_trading_parameters(
    symbol: str, side: str, amount_or_percentage: float, amount_type: str
) -> None:
    """
    @brief Validates trading parameters before execution
    @param symbol: Trading pair symbol
    @param side: Trading side ('BUY' or 'SELL')
    @param amount_or_percentage: Amount or percentage value
    @param amount_type: Type of amount ('usdt' or 'percentage')
    @raises ValueError: If validation fails
    @raises TypeError: If parameter types are invalid
    """
    # Symbol validation
    if not symbol or not isinstance(symbol, str):
        raise ValueError(f"Invalid symbol: {symbol}")

    # Side validation
    if side.upper() not in ["BUY", "SELL"]:
        raise ValueError(f"Invalid side: {side}. Must be 'BUY' or 'SELL'")

    # Amount type validation
    if not validate_amount_type(amount_type):
        raise ValueError(
            f"Invalid amount_type: {amount_type}. Must be 'usdt' or 'percentage'"
        )

    # Amount validation
    if not isinstance(amount_or_percentage, (int, float)):
        raise TypeError(
            f"amount_or_percentage must be a number, got {type(amount_or_percentage).__name__}: {amount_or_percentage}"
        )

    if amount_or_percentage <= 0:
        raise ValueError(
            f"amount_or_percentage must be positive, got: {amount_or_percentage}"
        )

    # Percentage specific validation
    if amount_type.lower() == "percentage" and amount_or_percentage > 1.0:
        raise ValueError(
            f"Percentage amount cannot be greater than 1.0, got: {amount_or_percentage}"
        )


def prepare_trade_data(
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: float,
    total_cost: float,
    order_id: str,
    amount_type: str,
    input_amount: float,
    wallet_before: float,
    wallet_after: float,
    timestamp: Optional[str] = None,
) -> Dict[str, Any]:
    """
    @brief Prepares standardized trade data dictionary
    @param symbol: Trading pair symbol
    @param side: Trading side ('BUY' or 'SELL')
    @param order_type: Order type ('MARKET' or 'LIMIT')
    @param quantity: Quantity traded
    @param price: Execution price
    @param total_cost: Total cost in USDT
    @param order_id: Binance order ID
    @param amount_type: Type of amount used ('usdt' or 'percentage')
    @param input_amount: Original input amount/percentage
    @param wallet_before: Wallet balance before trade
    @param wallet_after: Wallet balance after trade
    @param timestamp: Optional timestamp, current time if None
    @return Dict: Standardized trade data
    """
    import datetime

    if timestamp is None:
        timestamp = datetime.datetime.now().isoformat()

    # Determine type suffix based on amount type
    if amount_type.lower() == "usdt":
        type_suffix = f"${input_amount:.2f}_{side}"
    else:
        type_suffix = f"{input_amount * 100:.1f}%_{side}"

    return {
        "timestamp": timestamp,
        "symbol": symbol.upper(),
        "side": side.upper(),
        "type": type_suffix,
        "quantity": quantity,
        "price": price,
        "total_cost": total_cost,
        "wallet_before": wallet_before,
        "wallet_after": wallet_after,
        "order_id": order_id,
        "order_type": order_type,
        "amount_type": amount_type,
        "input_amount": input_amount,
        "balance_change": wallet_after - wallet_before,
    }


class OrderExecutionContext:
    """
    Context class to hold order execution parameters and avoid passing many arguments
    """

    def __init__(
        self,
        symbol: str,
        side: str,
        amount_or_percentage: float,
        amount_type: str,
        order_type: str = "MARKET",
        limit_price: Optional[float] = None,
    ):
        """
        @brief Initialize order execution context
        @param symbol: Trading pair symbol
        @param side: Trading side ('BUY' or 'SELL')
        @param amount_or_percentage: Amount or percentage value
        @param amount_type: Type of amount ('usdt' or 'percentage')
        @param order_type: Order type ('MARKET' or 'LIMIT')
        @param limit_price: Price for limit orders
        """
        # Validate all parameters
        validate_trading_parameters(symbol, side, amount_or_percentage, amount_type)

        self.symbol = symbol.upper()
        self.side = side.upper()
        self.amount_or_percentage = amount_or_percentage
        self.amount_type = amount_type.lower()
        self.order_type = order_type.upper()
        self.limit_price = limit_price

        # Additional validation for limit orders
        if self.order_type == "LIMIT" and limit_price is None:
            raise ValueError("limit_price is required for LIMIT orders")

        # Log the context creation
        logging.info(
            f"🔧 Created OrderExecutionContext: {self.side} {self.symbol} "
            f"({self.amount_or_percentage} {self.amount_type}, {self.order_type})"
        )

    def __str__(self) -> str:
        """String representation of the context"""
        limit_info = f" @${self.limit_price:.6f}" if self.limit_price else ""
        return f"{self.side} {self.symbol}: {self.amount_or_percentage} {self.amount_type} ({self.order_type}{limit_info})"
