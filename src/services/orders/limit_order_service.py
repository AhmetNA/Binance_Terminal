"""
limit_order_service.py
Bu modül limit order işlemlerini yöneten fonksiyonları içerir.
"""

import logging
import time
from typing import Dict, Any, Optional
from binance.exceptions import BinanceAPIException

from services.binance_client import prepare_client
from services.account import retrieve_usdt_balance, get_amountOf_asset
from utils.trading import (
    get_price,
    get_symbol_info,
    calculate_buy_quantity,
    calculate_sell_quantity,
    format_quantity_for_binance,
)
from api.error_handler import handle_binance_api_error
from utils.trading.operations import (
    OrderExecutionContext,
    prepare_trade_data,
)

# Order type constants to avoid circular dependencies
LIMIT_ORDER = "LIMIT"
BUY_SIDE = "BUY"
SELL_SIDE = "SELL"

# Setup logger
logger = logging.getLogger(__name__)


def validate_minimum_notional(
    symbol: str, quantity: float, price: float, client=None
) -> tuple[bool, str]:
    """
    Binance'in NOTIONAL (minimum order value) gereksinimlerini kontrol eder

    Returns:
        tuple: (is_valid, error_message)
    """
    try:
        if client is None:
            client = prepare_client()

        # Symbol bilgilerini al
        symbol_info = get_symbol_info(client, symbol)

        # NOTIONAL filter'ı bul
        notional_filter = None
        for filter_item in symbol_info.get("filters", []):
            if filter_item["filterType"] == "NOTIONAL":
                notional_filter = filter_item
                break

        if notional_filter:
            min_notional = float(notional_filter.get("minNotional", 0))
            order_value = quantity * price

            if order_value < min_notional:
                return (
                    False,
                    f"🚫 Order amount ${order_value:.2f} too low! {symbol} requires minimum ${min_notional:.2f}. Please enter higher amount.",
                )

        return True, ""

    except Exception as e:
        logger.warning(f"Could not validate NOTIONAL for {symbol}: {e}")
        return True, ""  # Validasyon yapılamazsa devam et


def place_limit_buy_order(
    symbol: str,
    amount_or_percentage: float,
    amount_type: str,
    limit_price: float = None,
    usdt_amount: float = None,
    user_context: dict = None,
):
    """
    @brief Limit buy order işlemi
    @param symbol: Trading symbol (e.g., 'BTCUSDT')
    @param amount_or_percentage: Miktar veya yüzde
    @param amount_type: 'usdt' veya 'percentage'
    @param limit_price: Limit fiyatı (opsiyonel, otomatik hesaplanabilir)
    @param usdt_amount: USDT tutarı (alternatif parametre)
    @param user_context: Kullanıcı context bilgisi
    @return: tuple: (success, order_info, error_message)
    """
    logger = logging.getLogger("place_limit_buy_order")

    # Client'ı hazırla
    client = prepare_client()

    try:
        from data.data_manager import data_manager
        from utils.trading import round_price_to_precision

        # Amount type validasyonu
        if amount_type.lower() not in ["usdt", "percentage"]:
            raise ValueError(
                f"Invalid amount_type: {amount_type}. Must be 'usdt' or 'percentage'"
            )

        # Amount loglama
        if amount_type.lower() == "usdt":
            logger.info(f"💰 Limit buy amount: ${amount_or_percentage:.2f} USDT")
        else:
            logger.info(f"📊 Limit buy percentage: {amount_or_percentage * 100:.2f}%")

        # USDT balance al
        usdt_balance = retrieve_usdt_balance(client)
        logger.info(f"💼 Current USDT balance: ${usdt_balance:.2f}")

        # Miktar hesaplama
        if amount_type.lower() == "usdt":
            # USDT amount kullan
            usdt_to_spend = min(
                float(amount_or_percentage), usdt_balance
            )  # Balance kontrolü
            actual_percentage = usdt_to_spend / usdt_balance if usdt_balance > 0 else 0
            logger.info(
                f"💰 Using USDT amount: ${usdt_to_spend:.2f} (≈{actual_percentage * 100:.2f}% of balance)"
            )
        else:
            # Percentage kullan
            usdt_to_spend = usdt_balance * float(amount_or_percentage)
            logger.info(
                f"📊 Using percentage: {amount_or_percentage * 100:.2f}% = ${usdt_to_spend:.2f}"
            )

        # Symbol bilgilerini al
        symbol_info = get_symbol_info(client, symbol)

        # Create execution context for validation
        context = OrderExecutionContext(
            symbol,
            BUY_SIDE,
            amount_or_percentage,
            amount_type,
            LIMIT_ORDER,
            limit_price,
        )

        # İlk quantity hesapla ve NOTIONAL kontrolü yap
        initial_quantity = calculate_buy_quantity(
            usdt_to_spend, limit_price, symbol_info
        )
        is_valid, validation_error = validate_minimum_notional(
            symbol, initial_quantity, limit_price, client
        )

        if not is_valid:
            error_msg = validation_error  # Validation mesajını direkt kullan
            logger.error(error_msg)
            raise Exception(error_msg)

        # Agresif limit order stratejisi
        order = None
        final_price = None

        # 1. Deneme: %0.01 üstünde
        try:
            rounded_limit_price = round_price_to_precision(limit_price, symbol_info)
            logger.info(
                f"🎯 1st attempt: Placing order at +0.01% (${rounded_limit_price:.6f})"
            )

            quantity = calculate_buy_quantity(
                usdt_to_spend, rounded_limit_price, symbol_info
            )

            order = client.order_limit_buy(
                symbol=context.symbol,
                quantity=format_quantity_for_binance(quantity),
                price=str(rounded_limit_price),
            )

            # 5 saniye bekle ve order durumunu kontrol et
            logger.info("⏱️ Waiting 5 seconds to check if order fills...")
            for i in range(5):
                time.sleep(1)
                order_status = client.get_order(symbol=symbol, orderId=order["orderId"])
                if order_status["status"] == "FILLED":
                    logger.info(f"✅ Order filled in {i + 1} seconds!")
                    final_price = rounded_limit_price
                    break
                logger.info(f"⏳ Waiting... {i + 1}/5 seconds")

            # Eğer 5 saniyede dolmadıysa iptal et
            if order_status["status"] != "FILLED":
                logger.info("🔄 Order not filled in 5s, cancelling and trying +0.1%")
                logger.info(
                    "⚠️ The buy order was not filled on the first attempt, retrying with a second attempt..."
                )
                client.cancel_order(symbol=symbol, orderId=order["orderId"])
                order = None

        except Exception as e:
            if (
                isinstance(e, BinanceAPIException)
                and getattr(e, "code", None) == -1013
                and "NOTIONAL" in str(e)
            ):
                logger.warning(
                    "⚠️ 1st attempt failed: Minimum işlem tutarı yetersiz (NOTIONAL error)"
                )
            else:
                logger.warning(f"⚠️ 1st attempt failed: {e}")
            order = None

        # 2. Deneme: %0.1 üstünde (eğer ilk deneme başarısızsa)
        if order is None or order_status["status"] != "FILLED":
            try:
                current_price = get_price(client, symbol)
                retry_price = current_price * 1.001  # %0.1 üstü
                rounded_retry_price = round_price_to_precision(retry_price, symbol_info)

                logger.info(
                    f"🎯 2nd attempt: Placing order at +0.1% (${rounded_retry_price:.6f})"
                )

                quantity = calculate_buy_quantity(
                    usdt_to_spend, rounded_retry_price, symbol_info
                )

                order = client.order_limit_buy(
                    symbol=context.symbol,
                    quantity=format_quantity_for_binance(quantity),
                    price=str(rounded_retry_price),
                )

                # 5 saniye daha bekle
                logger.info("⏱️ Waiting another 5 seconds to check if order fills...")
                for i in range(5):
                    time.sleep(1)
                    order_status = client.get_order(
                        symbol=symbol, orderId=order["orderId"]
                    )
                    if order_status["status"] == "FILLED":
                        logger.info(
                            f"✅ Order filled in {i + 1} seconds on 2nd attempt!"
                        )
                        final_price = rounded_retry_price
                        break
                    logger.info(f"⏳ Waiting... {i + 1}/5 seconds (2nd attempt)")

                # Eğer hala dolmadıysa kullanıcıya mesaj
                if order_status["status"] != "FILLED":
                    logger.warning(
                        "⚠️ 📈 FİYAT DEĞİŞİMİ ÇOK HIZLI! Order 10 saniyede dolmadı."
                    )
                    logger.warning(
                        "💡 Order beklemede bırakıldı, manuel kontrol önerilir."
                    )
                    logger.info(
                        "⚠️ The second attempt also failed. Order left pending for manual review."
                    )
                    final_price = rounded_retry_price

            except Exception as e2:
                if (
                    isinstance(e2, BinanceAPIException)
                    and getattr(e2, "code", None) == -1013
                    and "NOTIONAL" in str(e2)
                ):
                    logger.error(
                        "❌ 2nd attempt also failed: Minimum işlem tutarı yetersiz (NOTIONAL error)"
                    )
                else:
                    logger.error(f"❌ 2nd attempt also failed: {e2}")
                # Son çare olarak orijinal fiyatı kullan
                final_price = round_price_to_precision(limit_price, symbol_info)
                quantity = calculate_buy_quantity(
                    usdt_to_spend, final_price, symbol_info
                )
                order = client.order_limit_buy(
                    symbol=context.symbol,
                    quantity=format_quantity_for_binance(quantity),
                    price=str(final_price),
                )

        # Trade data hazırla
        trade_data = prepare_trade_data(
            symbol=context.symbol,
            side=context.side,
            order_type=LIMIT_ORDER,
            quantity=quantity,
            price=final_price,
            total_cost=usdt_to_spend,
            order_id=order.get("orderId", "unknown"),
            amount_type=amount_type,
            input_amount=amount_or_percentage,
            wallet_before=usdt_balance,
            wallet_after=usdt_balance,  # Henüz execute olmadı
            timestamp=order.get("transactTime"),
        )

        # Add limit order specific fields
        trade_data.update(
            {
                "status": order.get("status", "NEW"),
                "amount_type": amount_type,
                "input_amount": amount_or_percentage,
            }
        )

        # Trade data kaydet
        data_manager.save_trade(trade_data)

        # Order bilgilerini daha detaylı göster
        order_type = order.get("type", "UNKNOWN")
        order_status = order.get("status", "UNKNOWN")
        order_qty = order.get("origQty", "0")
        order_price = order.get("price", "0")

        logger.info(f"✅ {order_type} BUY order placed: {symbol}")
        logger.info(
            f"   📊 Status: {order_status} | Miktar: {order_qty} | Limit Fiyat: {order_price}"
        )
        logger.info(f"   💰 Amount Type: {amount_type} | Input: {amount_or_percentage}")
        logger.info(
            f"   🔗 Order ID: {order.get('orderId')} | Client ID: {order.get('clientOrderId')}"
        )

        return order

    except Exception as e:
        error_msg = handle_binance_api_error(e, symbol, "Limit Buy")
        logger.error(error_msg)
        if not isinstance(e, BinanceAPIException):
            logger.exception("Full traceback for non-API error:")
        raise Exception(error_msg) from e


def cancel_order(symbol: str, order_id: int, client=None) -> Dict[str, Any]:
    """
    @brief Order'ı iptal eder
    @param symbol: Trading pair symbol
    @param order_id: İptal edilecek order ID'si
    @param client: Binance API client (None ise otomatik oluşturulur)
    @return İptal detayları
    """
    if client is None:
        client = prepare_client()

    logger = logging.getLogger("cancel_order")

    try:
        logger.info(f"🔄 Cancelling order {order_id} for {symbol}")

        result = client.cancel_order(symbol=symbol, orderId=order_id)

        logger.info(f"✅ Order cancelled: {result}")
        return result

    except Exception as e:
        error_msg = handle_binance_api_error(e, symbol, "Cancel Order")
        logger.error(error_msg)
        if not isinstance(e, BinanceAPIException):
            logger.exception("Full traceback for non-API error:")
        raise Exception(error_msg) from e


def get_open_orders(symbol: Optional[str] = None, client=None) -> list:
    """
    @brief Açık orderları getirir
    @param symbol: Belirli bir symbol için orderlar (None ise tüm orderlar)
    @param client: Binance API client (None ise otomatik oluşturulur)
    @return Açık orderlar listesi
    """
    if client is None:
        client = prepare_client()

    logger = logging.getLogger("get_open_orders")

    try:
        if symbol:
            orders = client.get_open_orders(symbol=symbol)
            logger.info(f"Retrieved {len(orders)} open orders for {symbol}")
        else:
            orders = client.get_open_orders()
            logger.info(f"Retrieved {len(orders)} total open orders")

        return orders

    except Exception as e:
        error_msg = handle_binance_api_error(e, symbol or "All", "Get Open Orders")
        logger.error(error_msg)
        if not isinstance(e, BinanceAPIException):
            logger.exception("Full traceback for non-API error:")
        raise Exception(error_msg) from e


def place_limit_sell_order(
    symbol: str,
    amount_or_percentage: float,
    amount_type: str,
    limit_price: float = None,
):
    """
    @brief Limit sell order işlemi
    @param symbol: Trading symbol (e.g., 'BTCUSDT')
    @param amount_or_percentage: Miktar veya yüzde
    @param amount_type: 'usdt' veya 'percentage'
    @param limit_price: Limit fiyatı (opsiyonel, otomatik hesaplanabilir)
    @return: tuple: (success, order_info, error_message)
    """
    # Client'ı hazırla
    client = prepare_client()

    logger = logging.getLogger("place_limit_sell_order")

    try:
        from data.data_manager import data_manager
        from utils.trading import round_price_to_precision

        # Amount type validasyonu
        if amount_type.lower() not in ["usdt", "percentage"]:
            raise ValueError(
                f"Invalid amount_type: {amount_type}. Must be 'usdt' or 'percentage'"
            )

        # Amount loglama
        if amount_type.lower() == "usdt":
            logger.info(f"💰 Limit sell amount: ${amount_or_percentage:.2f} USDT")
        else:
            logger.info(f"📊 Limit sell percentage: {amount_or_percentage * 100:.2f}%")

        # Asset balance al
        asset_amount = get_amountOf_asset(client, symbol)
        logging.info(f"💼 Current {symbol} balance: {asset_amount}")

        if amount_type.lower() == "usdt":
            # USDT amount'u asset quantity'ye çevir
            current_price = get_price(client, symbol)
            quantity_from_usdt = amount_or_percentage / current_price
            quantity_to_sell = min(quantity_from_usdt, asset_amount)  # Balance kontrolü
            logger.info(
                f"💰 Converting ${amount_or_percentage:.2f} to {quantity_to_sell} {symbol} at limit price ${limit_price}"
            )
        else:
            # Percentage kullan
            quantity_to_sell = asset_amount * float(amount_or_percentage)
            logger.info(
                f"📊 Using percentage: {amount_or_percentage * 100:.2f}% = {quantity_to_sell} {symbol}"
            )

        # Create execution context for validation
        context = OrderExecutionContext(
            symbol,
            SELL_SIDE,
            amount_or_percentage,
            amount_type,
            LIMIT_ORDER,
            limit_price,
        )

        # Symbol bilgilerini al
        symbol_info = get_symbol_info(client, symbol)

        # İlk quantity hesapla ve NOTIONAL kontrolü yap
        initial_quantity = calculate_sell_quantity(quantity_to_sell, symbol_info)
        is_valid, validation_error = validate_minimum_notional(
            symbol, initial_quantity, limit_price, client
        )

        if not is_valid:
            logger.error(validation_error)
            raise ValueError(validation_error)

        # Final quantity hesapla
        quantity = calculate_sell_quantity(quantity_to_sell, symbol_info)

        # Fiyatı round et
        final_price = round_price_to_precision(limit_price, symbol_info)

        # Limit sell order yap
        try:
            logger.info(
                f"🔄 Placing limit sell order: {quantity} {context.symbol} at ${final_price:.6f}"
            )
            order = client.order_limit_sell(
                symbol=context.symbol,
                quantity=format_quantity_for_binance(quantity),
                price=str(final_price),
            )

        except Exception as e1:
            if "NOTIONAL" in str(e1).upper() or "minimum" in str(e1).lower():
                # İkinci deneme: %0.01 daha düşük fiyat
                retry_price = final_price * 0.9999
                rounded_retry_price = round_price_to_precision(retry_price, symbol_info)
                logger.info(
                    f"🎯 1st attempt failed: Trying -0.01% (${rounded_retry_price:.6f})"
                )

                quantity = calculate_sell_quantity(quantity_to_sell, symbol_info)

                order = client.order_limit_sell(
                    symbol=context.symbol,
                    quantity=format_quantity_for_binance(quantity),
                    price=str(rounded_retry_price),
                )

                final_price = rounded_retry_price

                # 5 saniye daha bekle
                logger.info("⏱️ Waiting another 5 seconds to check if order fills...")
                time.sleep(5)
            else:
                # Başka bir hata varsa yeniden fırlat
                raise e1

        # Trade data hazırla
        trade_data = prepare_trade_data(
            symbol=context.symbol,
            side=context.side,
            order_type=LIMIT_ORDER,
            quantity=quantity,
            price=final_price,
            total_cost=float(quantity) * final_price,
            order_id=order.get("orderId", "unknown"),
            amount_type=amount_type,
            input_amount=amount_or_percentage,
            wallet_before=asset_amount,
            wallet_after=asset_amount,  # Henüz execute olmadı
            timestamp=order.get("transactTime"),
        )

        # Add limit order specific fields
        trade_data.update(
            {
                "status": order.get("status", "NEW"),
                "amount_type": amount_type,
                "input_amount": amount_or_percentage,
            }
        )

        # Trade data kaydet
        data_manager.save_trade(trade_data)

        # Order bilgilerini daha detaylı göster
        order_type = order.get("type", "UNKNOWN")
        order_status = order.get("status", "UNKNOWN")
        order_id = order.get("orderId", "UNKNOWN")

        logger.info("✅ Limit sell order placed successfully:")
        logger.info(f"   📈 Symbol: {context.symbol}")
        logger.info(f"   💰 Quantity: {quantity}")
        logger.info(f"   💵 Limit Price: ${final_price:.6f}")
        logger.info(f"   💎 Estimated Total: ${float(quantity) * final_price:.2f}")
        logger.info(f"   🔢 Order ID: {order_id}")
        logger.info(f"   📊 Status: {order_status}")
        logger.info(f"   🔄 Type: {order_type}")

        status_msg = f"✅ Limit Sell Order: {quantity} {context.symbol} @ ${final_price:.6f} (ID: {order_id})"
        logger.info(status_msg)

        return order

    except Exception as e:
        error_msg = handle_binance_api_error(e, symbol, "Limit Sell")
        logger.error(f"❌ Limit Sell operation failed: {client} - Please try again")
        if not isinstance(e, BinanceAPIException):
            logger.exception("Full traceback for non-API error:")

        # Log kullanıcı dostu mesaj
        logger.error(error_msg)

        raise Exception(error_msg) from e
