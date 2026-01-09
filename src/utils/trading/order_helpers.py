"""
utils/trading/order_helpers.py
Helper functions for order processing, validation, and logging.
"""

import logging
from typing import Dict, Any

def validate_order_response(order: Dict[str, Any]) -> bool:
    """
    @brief Validates Binance order response
    @param order: Order response from Binance API
    @return bool: True if valid order response
    """
    if not isinstance(order, dict):
        return False

    required_fields = ["orderId", "symbol", "side", "status"]
    return all(field in order for field in required_fields)


def extract_order_info(order: Dict[str, Any], order_type: str) -> Dict[str, Any]:
    """
    @brief Extracts standardized order information from Binance response
    @param order: Order response from Binance API
    @param order_type: Type of order (MARKET or LIMIT)
    @return Dict: Extracted order information
    """
    if not validate_order_response(order):
        raise ValueError("Invalid order response from Binance API")

    # Extract common fields
    order_info = {
        "order_id": order.get("orderId", "unknown"),
        "symbol": order.get("symbol", ""),
        "side": order.get("side", ""),
        "status": order.get("status", "UNKNOWN"),
        "quantity": float(order.get("origQty", 0)),
        "timestamp": order.get("transactTime", order.get("time", "")),
    }

    # Handle different order types
    if order_type == "MARKET" and "fills" in order and order["fills"]:
        # Market order - use fills data for actual execution details
        fill = order["fills"][0]  # Use first fill for price
        order_info.update(
            {
                "price": float(fill.get("price", 0)),
                "executed_quantity": float(order.get("executedQty", 0)),
                "total_cost": float(order.get("cummulativeQuoteQty", 0)),
            }
        )
    else:
        # Limit order or market order without fills
        order_info.update(
            {
                "price": float(order.get("price", 0)),
                "executed_quantity": float(order.get("executedQty", 0)),
                "total_cost": float(
                    order.get(
                        "cummulativeQuoteQty",
                        order_info["quantity"] * order_info["price"],
                    )
                ),
            }
        )

    return order_info


def calculate_limit_price(
    current_price: float, side: str, offset_percentage: float = 0.01
) -> float:
    """
    @brief Calculates limit price based on current price and side
    @param current_price: Current market price
    @param side: Trading side ('BUY' or 'SELL')
    @param offset_percentage: Percentage offset from current price (default 0.01 = 1%)
    @return float: Calculated limit price
    """
    if side.upper() == "BUY":
        # Buy orders: slightly above current price for execution
        return current_price * (1 + offset_percentage)
    else:
        # Sell orders: slightly below current price for execution
        return current_price * (1 - offset_percentage)


def log_order_execution(
    operation: str,
    symbol: str,
    quantity: float,
    price: float,
    order_type: str,
    order_id: str,
) -> None:
    """
    @brief Logs successful order execution with comprehensive details
    @param operation: Operation type (e.g., "Hard_Buy", "Soft_Sell")
    @param symbol: Trading symbol
    @param quantity: Executed quantity
    @param price: Execution price
    @param order_type: Order type (MARKET or LIMIT)
    @param order_id: Binance order ID
    """
    total_cost = quantity * price

    logging.info(f"✅ {operation} order completed successfully:")
    logging.info(f"   📈 Symbol: {symbol}")
    logging.info(f"   💰 Quantity: {quantity}")
    logging.info(f"   💵 Price: ${price:.6f}")
    logging.info(f"   💎 Total Cost: ${total_cost:.2f}")
    logging.info(f"   🔢 Order ID: {order_id}")
    logging.info(f"   🔄 Order Type: {order_type}")


def prepare_order_log_context(context_data: Dict[str, Any]) -> str:
    """
    @brief Prepares formatted log context for order operations
    @param context_data: Dictionary containing context information
    @return str: Formatted log context string
    """
    parts = []

    if "operation" in context_data:
        parts.append(f"Operation: {context_data['operation']}")

    if "symbol" in context_data:
        parts.append(f"Symbol: {context_data['symbol']}")

    if "amount_type" in context_data and "amount" in context_data:
        amount_type = context_data["amount_type"]
        amount = context_data["amount"]
        if amount_type.lower() == "usdt":
            parts.append(f"Amount: ${amount:.2f} USDT")
        else:
            parts.append(f"Amount: {amount * 100:.1f}%")

    if "order_type" in context_data:
        parts.append(f"Type: {context_data['order_type']}")

    if "limit_price" in context_data and context_data["limit_price"]:
        parts.append(f"Limit: ${context_data['limit_price']:.6f}")

    return " | ".join(parts)
