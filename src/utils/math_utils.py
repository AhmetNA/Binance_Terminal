"""
math_utils.py
Mathematical utility functions for trading calculations.
"""

import math
import logging


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

        # Step size'ın decimal sayısını daha hassas olarak hesapla
        from decimal import Decimal, getcontext, ROUND_DOWN

        getcontext().prec = 28

        # Decimal ile çalış precision kaybını önlemek için
        dec_quantity = Decimal(str(quantity))
        dec_step_size = Decimal(str(step_size))

        # Step size'a göre yuvarla (aşağı yuvarla)
        factor = dec_quantity / dec_step_size
        rounded_factor = factor.quantize(Decimal("1"), rounding=ROUND_DOWN)
        rounded_quantity = rounded_factor * dec_step_size

        # Float'a çevir ama precision'ı koru
        result = float(rounded_quantity)

        # Step size'ın decimal sayısını bul
        step_str = f"{step_size:.20f}".rstrip("0")
        if "." in step_str:
            decimals = len(step_str.split(".")[1])
            result = round(result, decimals)

        logging.debug(
            f"Rounded {quantity} to {result} (step: {step_size}, decimals: {decimals if '.' in step_str else 0})"
        )
        return result

    except Exception as e:
        logging.error(f"Error rounding quantity {quantity} with step {step_size}: {e}")
        # Fallback to old method
        try:
            factor = 1 / step_size
            rounded_quantity = math.floor(quantity * factor) / factor
            step_str = f"{step_size:.10f}".rstrip("0")
            if "." in step_str:
                decimals = len(step_str.split(".")[1])
                rounded_quantity = round(rounded_quantity, decimals)
            return rounded_quantity
        except:
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
            return 0.0 if new_value == 0 else float("inf")
        return ((new_value - old_value) / old_value) * 100
    except Exception as e:
        logging.error(f"Error calculating percentage change: {e}")
        return 0.0


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

    # Test moving average - removed function
    print("📈 Moving average functionality removed")

    print("\n✅ Math utils test completed successfully!")
