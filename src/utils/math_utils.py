"""
math_utils.py
Mathematical utility functions for trading calculations.
"""

import math
import logging
from typing import Union, Tuple, List


def round_to_precision(value: float, precision: int) -> float:
    """Round value to specified decimal precision"""
    try:
        return round(value, precision)
    except Exception as e:
        logging.error(f"Error rounding {value} to {precision} precision: {e}")
        return value


def round_to_step_size(quantity: float, step_size: float) -> float:
    """Round quantity to Binance step size requirements"""
    try:
        if step_size == 0:
            return quantity
        
        # Step size'ın decimal sayısını bul
        step_str = f"{step_size:.10f}".rstrip('0')
        if '.' in step_str:
            decimals = len(step_str.split('.')[1])
        else:
            decimals = 0
        
        # Quantity'yi step size'a göre yuvarla
        factor = 1 / step_size
        rounded_quantity = math.floor(quantity * factor) / factor
        
        # Decimal precision'ı ayarla
        rounded_quantity = round(rounded_quantity, decimals)
        
        logging.debug(f"Rounded {quantity} to {rounded_quantity} (step: {step_size})")
        return rounded_quantity
        
    except Exception as e:
        logging.error(f"Error rounding quantity {quantity} with step {step_size}: {e}")
        return quantity


def calculate_percentage(value: float, total: float) -> float:
    """Calculate percentage of value from total"""
    try:
        if total == 0:
            return 0.0
        return (value / total) * 100
    except Exception as e:
        logging.error(f"Error calculating percentage: {e}")
        return 0.0


def calculate_percentage_change(old_value: float, new_value: float) -> float:
    """Calculate percentage change between two values"""
    try:
        if old_value == 0:
            return 0.0 if new_value == 0 else float('inf')
        return ((new_value - old_value) / old_value) * 100
    except Exception as e:
        logging.error(f"Error calculating percentage change: {e}")
        return 0.0


def clamp_value(value: float, min_value: float, max_value: float) -> float:
    """Clamp value between min and max boundaries"""
    return max(min_value, min(value, max_value))


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide numbers with default fallback"""
    try:
        if denominator == 0:
            return default
        return numerator / denominator
    except Exception as e:
        logging.error(f"Error in safe division: {e}")
        return default


def format_currency(amount: float, currency: str = "USDT", decimals: int = 2) -> str:
    """Format currency amount for display"""
    try:
        formatted = f"{amount:,.{decimals}f}"
        return f"{formatted} {currency}"
    except Exception as e:
        logging.error(f"Error formatting currency: {e}")
        return f"{amount} {currency}"


def format_percentage(percentage: float, decimals: int = 2) -> str:
    """Format percentage for display"""
    try:
        return f"{percentage:.{decimals}f}%"
    except Exception as e:
        logging.error(f"Error formatting percentage: {e}")
        return f"{percentage}%"


def calculate_compound_return(initial_value: float, final_value: float, periods: int) -> float:
    """Calculate compound annual growth rate"""
    try:
        if initial_value <= 0 or periods <= 0:
            return 0.0
        return (pow(final_value / initial_value, 1 / periods) - 1) * 100
    except Exception as e:
        logging.error(f"Error calculating compound return: {e}")
        return 0.0


def calculate_moving_average(values: List[float], window: int) -> List[float]:
    """Calculate simple moving average"""
    try:
        if len(values) < window:
            return values
        
        moving_averages = []
        for i in range(len(values) - window + 1):
            window_average = sum(values[i:i + window]) / window
            moving_averages.append(window_average)
        
        return moving_averages
    except Exception as e:
        logging.error(f"Error calculating moving average: {e}")
        return values


def calculate_volatility(prices: List[float]) -> float:
    """Calculate price volatility (standard deviation)"""
    try:
        if len(prices) < 2:
            return 0.0
        
        mean_price = sum(prices) / len(prices)
        variance = sum((price - mean_price) ** 2 for price in prices) / len(prices)
        return math.sqrt(variance)
    except Exception as e:
        logging.error(f"Error calculating volatility: {e}")
        return 0.0


def normalize_to_range(value: float, min_val: float, max_val: float, new_min: float = 0, new_max: float = 1) -> float:
    """Normalize value from one range to another"""
    try:
        if max_val == min_val:
            return new_min
        
        normalized = (value - min_val) / (max_val - min_val)
        return new_min + normalized * (new_max - new_min)
    except Exception as e:
        logging.error(f"Error normalizing value: {e}")
        return value


if __name__ == "__main__":
    """Test math utils functions"""
    print("🚀 Testing Math Utils")
    print("=" * 30)
    
    # Test rounding
    quantity = 0.123456789
    step_size = 0.001
    rounded = round_to_step_size(quantity, step_size)
    print(f"🔢 Rounded {quantity} to {rounded} (step: {step_size})")
    
    # Test percentage calculation
    percentage = calculate_percentage(75, 200)
    print(f"📊 75 of 200 is {percentage:.2f}%")
    
    # Test percentage change
    change = calculate_percentage_change(100, 120)
    print(f"📈 Change from 100 to 120: {change:.2f}%")
    
    # Test currency formatting
    formatted = format_currency(1234.56789, "USDT", 2)
    print(f"💰 Formatted currency: {formatted}")
    
    # Test moving average
    prices = [100, 110, 105, 115, 120, 125]
    ma = calculate_moving_average(prices, 3)
    print(f"📈 Moving average (3-period): {[round(x, 2) for x in ma]}")
    
    print("\n✅ Math utils test completed successfully!")
