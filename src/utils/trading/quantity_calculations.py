"""
trading/quantity_calculations.py
Quantity calculation and formatting utilities for trading.
"""

import logging

from ..math_utils import round_to_step_size


def round_quantity(quantity, step_size):
    """Quantity'yi step size'a göre yuvarla"""
    return round_to_step_size(quantity, step_size)


def calculate_buy_quantity(usdt_amount, price, symbol_info):
    """Alım için quantity hesapla"""
    try:
        # Base quantity hesapla
        base_quantity = usdt_amount / price

        # LOT_SIZE filter'ını bul
        lot_size_filter = symbol_info["filters"].get("LOT_SIZE")
        if lot_size_filter:
            step_size = float(lot_size_filter["stepSize"])
            min_qty = float(lot_size_filter["minQty"])

            # Quantity'yi yuvarla
            rounded_quantity = round_quantity(base_quantity, step_size)

            # Minimum quantity kontrolü
            if rounded_quantity < min_qty:
                raise ValueError(
                    f"Calculated quantity {rounded_quantity} is below minimum {min_qty}"
                )

            return rounded_quantity  # Float olarak döndür
        else:
            logging.warning("LOT_SIZE filter not found, using raw quantity")
            return base_quantity  # Float olarak döndür

    except Exception as e:
        logging.error(f"Error calculating buy quantity: {e}")
        raise


def calculate_sell_quantity(asset_amount, symbol_info):
    """Satış için quantity hesapla"""
    try:
        # LOT_SIZE filter'ını bul
        lot_size_filter = symbol_info["filters"].get("LOT_SIZE")
        if lot_size_filter:
            step_size = float(lot_size_filter["stepSize"])
            min_qty = float(lot_size_filter["minQty"])

            # Quantity'yi yuvarla
            rounded_quantity = round_quantity(asset_amount, step_size)

            # Minimum quantity kontrolü
            if rounded_quantity < min_qty:
                raise ValueError(
                    f"Asset amount {rounded_quantity} is below minimum {min_qty}"
                )

            return rounded_quantity  # Float olarak döndür
        else:
            logging.warning("LOT_SIZE filter not found, using raw quantity")
            return asset_amount  # Float olarak döndür

    except Exception as e:
        logging.error(f"Error calculating sell quantity: {e}")
        raise


def format_quantity_for_binance(quantity: float) -> str:
    """Quantity'yi Binance API için uygun string formatına çevir (scientific notation'sız)"""
    try:
        from decimal import Decimal, getcontext
        import re

        getcontext().prec = 28

        # Input validation
        if not isinstance(quantity, (int, float, Decimal)):
            raise ValueError(f"Invalid quantity type: {type(quantity)}")

        if quantity < 0:
            raise ValueError(f"Negative quantity not allowed: {quantity}")

        # Sıfır durumu
        if quantity == 0:
            return "0"

        # Çok küçük sayılar için özel işlem
        if quantity < 1e-20:
            return "0"

        # Decimal kullanarak precision kaybını önle
        dec_qty = Decimal(str(quantity))

        # Normal formatla çevir ve gereksiz sıfırları kaldır
        formatted = f"{dec_qty:f}".rstrip("0").rstrip(".")

        # Boş string kontrolü
        if not formatted or formatted == "." or formatted == "":
            formatted = "0"

        # Binance API için geçerli karakter kontrolü (sadece sayılar ve nokta)
        if not re.match(r"^[0-9]+(\.[0-9]+)?$", formatted):
            # Geçersiz karakterleri temizle
            clean_formatted = re.sub(r"[^0-9.]", "", formatted)

            # Çoklu nokta kontrolü
            if clean_formatted.count(".") > 1:
                parts = clean_formatted.split(".")
                clean_formatted = parts[0] + "." + "".join(parts[1:])

            # Başında nokta varsa 0 ekle
            if clean_formatted.startswith("."):
                clean_formatted = "0" + clean_formatted

            # Sadece nokta varsa 0 yap
            if clean_formatted == ".":
                clean_formatted = "0"

            formatted = clean_formatted

        # Son geçerlilik kontrolü
        if not re.match(r"^[0-9]+(\.[0-9]+)?$", formatted):
            logging.warning(
                f"Quantity format still invalid after cleaning: {quantity} -> {formatted}, using fallback"
            )
            # Fallback: basit string formatı
            formatted = f"{float(quantity):.8f}".rstrip("0").rstrip(".")
            if not formatted or formatted == ".":
                formatted = "0"

        # Maksimum 20 karakter uzunluk kontrolü (Binance API limiti)
        if len(formatted) > 20:
            # Decimal kısmını kısalt
            if "." in formatted:
                integer_part, decimal_part = formatted.split(".")
                max_decimal_len = 20 - len(integer_part) - 1  # -1 for the dot
                if max_decimal_len > 0:
                    formatted = f"{integer_part}.{decimal_part[:max_decimal_len]}"
                else:
                    formatted = integer_part
            else:
                formatted = formatted[:20]

        return formatted

    except Exception as e:
        logging.error(f"Error formatting quantity {quantity}: {e}")
        # Fallback: basit string formatı ile güvenli format
        try:
            if isinstance(quantity, (int, float)) and quantity >= 0:
                if quantity >= 1:
                    # Büyük sayılar için 8 decimal
                    formatted = f"{quantity:.8f}".rstrip("0").rstrip(".")
                else:
                    # Küçük sayılar için 12 decimal
                    formatted = f"{quantity:.12f}".rstrip("0").rstrip(".")

                if not formatted or formatted == ".":
                    formatted = "0"

                return formatted
            else:
                return "0"
        except:
            logging.error(f"Fallback formatting also failed for quantity: {quantity}")
            return "0"
