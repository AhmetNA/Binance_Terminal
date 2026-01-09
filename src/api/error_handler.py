"""
api/error_handler.py
Handles API error mapping to user-friendly messages.
"""

def handle_binance_api_error(error: Exception, symbol: str, operation: str) -> str:
    """
    @brief Converts Binance API errors to user-friendly messages
    @param error: The exception that occurred
    @param symbol: Trading symbol involved
    @param operation: Operation being performed
    @return str: User-friendly error message
    """
    error_str = str(error).lower()

    # Common Binance API error patterns
    if (
        "insufficient balance" in error_str
        or "account has insufficient balance" in error_str
    ):
        return f"❌ Insufficient balance: Cannot perform {operation} for {symbol}"

    elif "min notional" in error_str or "minimum order" in error_str:
        return f"❌ Minimum notional not met: Use a higher amount for {symbol}"

    elif "price filter" in error_str or "tick size" in error_str:
        return f"❌ Price format error: Invalid price for {symbol}"

    elif "lot size" in error_str or "step size" in error_str:
        return f"❌ Quantity format error: Invalid amount for {symbol}"

    elif "market is closed" in error_str or "trading is disabled" in error_str:
        return f"❌ Market closed: Cannot trade {symbol} now"

    elif "invalid symbol" in error_str or "symbol not found" in error_str:
        return f"❌ Invalid symbol: {symbol} not found"

    elif "api key" in error_str or "signature" in error_str:
        return "❌ API connection error: Please check your API keys"

    elif "rate limit" in error_str or "too many requests" in error_str:
        return "❌ Rate limit exceeded: Please wait before retrying"

    elif "connection" in error_str or "timeout" in error_str:
        return "❌ Connection error: Please check your internet connection"

    else:
        # Generic error for unknown cases
        return f"❌ {operation} failed: {symbol} - Please try again"
