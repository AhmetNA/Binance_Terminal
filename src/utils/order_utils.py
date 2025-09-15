"""
utils/order_utils.py
Order-specifi    if "api key" in error_str or "signature" in error_str:
        return f"❌ API connection error: Please check your API keys"
    
    elif "rate limit" in error_str or "too many requests" in error_str:
        return f"❌ Rate limit exceeded: Please wait before trying again"
    
    elif "connection" in error_str or "timeout" in error_str:
        return f"❌ Connection error: Please check your internet connection"
    
    else:
        # Generic error for unknown cases
        return f"❌ {operation} operation failed: {symbol} - Please try again"nctions that were previously causing circular dependencies.
"""

import logging
from typing import Dict, Any, Optional


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
    if "insufficient balance" in error_str or "account has insufficient balance" in error_str:
        return f"❌ Yetersiz bakiye: {symbol} için {operation} işlemi yapılamıyor"
    
    elif "min notional" in error_str or "minimum order" in error_str:
        return f"❌ Minimum işlem tutarı yetersiz: {symbol} için daha büyük miktar gerekli"
    
    elif "price filter" in error_str or "tick size" in error_str:
        return f"❌ Fiyat formatı hatası: {symbol} için geçersiz fiyat"
    
    elif "lot size" in error_str or "step size" in error_str:
        return f"❌ Miktar formatı hatası: {symbol} için geçersiz miktar"
    
    elif "market is closed" in error_str or "trading is disabled" in error_str:
        return f"❌ Piyasa kapalı: {symbol} işlem yapılamıyor"
    
    elif "invalid symbol" in error_str or "symbol not found" in error_str:
        return f"❌ Geçersiz sembol: {symbol} bulunamadı"
    
    elif "api key" in error_str or "signature" in error_str:
        return f"❌ API bağlantı hatası: Lütfen API anahtarlarını kontrol edin"
    
    elif "rate limit" in error_str or "too many requests" in error_str:
        return f"❌ İstek limiti aşıldı: Lütfen bir süre bekleyin"
    
    elif "connection" in error_str or "timeout" in error_str:
        return f"❌ Bağlantı hatası: İnternet bağlantınızı kontrol edin"
    
    else:
        # Generic error for unknown cases
        return f"❌ {operation} işlemi başarısız: {symbol} - Lütfen tekrar deneyin"


def validate_order_response(order: Dict[str, Any]) -> bool:
    """
    @brief Validates Binance order response
    @param order: Order response from Binance API
    @return bool: True if valid order response
    """
    if not isinstance(order, dict):
        return False
    
    required_fields = ['orderId', 'symbol', 'side', 'status']
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
        'order_id': order.get('orderId', 'unknown'),
        'symbol': order.get('symbol', ''),
        'side': order.get('side', ''),
        'status': order.get('status', 'UNKNOWN'),
        'quantity': float(order.get('origQty', 0)),
        'timestamp': order.get('transactTime', order.get('time', ''))
    }
    
    # Handle different order types
    if order_type == "MARKET" and 'fills' in order and order['fills']:
        # Market order - use fills data for actual execution details
        fill = order['fills'][0]  # Use first fill for price
        order_info.update({
            'price': float(fill.get('price', 0)),
            'executed_quantity': float(order.get('executedQty', 0)),
            'total_cost': float(order.get('cummulativeQuoteQty', 0))
        })
    else:
        # Limit order or market order without fills
        order_info.update({
            'price': float(order.get('price', 0)),
            'executed_quantity': float(order.get('executedQty', 0)),
            'total_cost': float(order.get('cummulativeQuoteQty', order_info['quantity'] * order_info['price']))
        })
    
    return order_info


def calculate_limit_price(current_price: float, side: str, offset_percentage: float = 0.01) -> float:
    """
    @brief Calculates limit price based on current price and side
    @param current_price: Current market price
    @param side: Trading side ('BUY' or 'SELL')
    @param offset_percentage: Percentage offset from current price (default 0.01 = 1%)
    @return float: Calculated limit price
    """
    if side.upper() == 'BUY':
        # Buy orders: slightly above current price for execution
        return current_price * (1 + offset_percentage)
    else:
        # Sell orders: slightly below current price for execution
        return current_price * (1 - offset_percentage)


def log_order_execution(operation: str, symbol: str, quantity: float, price: float, 
                       order_type: str, order_id: str) -> None:
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
    valid_quotes = ['USDT', 'BTC', 'ETH', 'BNB', 'USDC', 'BUSD']
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


def prepare_order_log_context(context_data: Dict[str, Any]) -> str:
    """
    @brief Prepares formatted log context for order operations
    @param context_data: Dictionary containing context information
    @return str: Formatted log context string
    """
    parts = []
    
    if 'operation' in context_data:
        parts.append(f"Operation: {context_data['operation']}")
    
    if 'symbol' in context_data:
        parts.append(f"Symbol: {context_data['symbol']}")
    
    if 'amount_type' in context_data and 'amount' in context_data:
        amount_type = context_data['amount_type']
        amount = context_data['amount']
        if amount_type.lower() == 'usdt':
            parts.append(f"Amount: ${amount:.2f} USDT")
        else:
            parts.append(f"Amount: {amount*100:.1f}%")
    
    if 'order_type' in context_data:
        parts.append(f"Type: {context_data['order_type']}")
    
    if 'limit_price' in context_data and context_data['limit_price']:
        parts.append(f"Limit: ${context_data['limit_price']:.6f}")
    
    return " | ".join(parts)