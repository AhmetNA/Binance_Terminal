"""
market_order_service.py
Bu modül market order işlemlerini yöneten fonksiyonları içerir.
"""

import logging
from typing import Dict, Any

from services.binance_client import prepare_client
from services.account import retrieve_usdt_balance, get_amountOf_asset
from utils.trading import (
    get_price,
    get_symbol_info,
    calculate_buy_quantity,
    calculate_sell_quantity,
)
from models.order_types import OrderSide, OrderType, OrderParameters


def place_market_buy_order(
    symbol: str,
    amount_or_percentage: float,
    amount_type: str = "percentage",
    client=None,
) -> Dict[str, Any]:
    """
    @brief Market buy order yerleştirir
    @param symbol: Trading pair symbol
    @param amount_or_percentage: İşlem miktarı (USDT amount veya percentage 0.0-1.0)
    @param amount_type: 'usdt' veya 'percentage' - hangi tip miktar olduğunu belirtir
    @param client: Binance API client (None ise otomatik oluşturulur)
    @return Order detayları
    """
    if client is None:
        client = prepare_client()

    logger = logging.getLogger("place_market_buy_order")

    try:
        from data.data_manager import data_manager

        # Amount type validasyonu
        if amount_type.lower() not in ["usdt", "percentage"]:
            raise ValueError(
                f"Invalid amount_type: {amount_type}. Must be 'usdt' or 'percentage'"
            )

        # Amount loglama
        if amount_type.lower() == "usdt":
            logger.info(f"💰 Market buy amount: ${amount_or_percentage:.2f} USDT")
        else:
            logger.info(f"📊 Market buy percentage: {amount_or_percentage * 100:.2f}%")

        # USDT balance al
        usdt_balance = retrieve_usdt_balance(client)
        logger.info(f"💼 Current USDT balance: ${usdt_balance:.2f}")

        # Genel bilgileri al
        current_price = get_price(client, symbol)
        symbol_info = get_symbol_info(client, symbol)

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

        # OrderParameters objesi oluştur
        order_params = OrderParameters(
            symbol=symbol,
            side=OrderSide.BUY,
            percentage=usdt_to_spend / usdt_balance if usdt_balance > 0 else 0,
            order_type=OrderType.MARKET,
        )

        quantity = calculate_buy_quantity(usdt_to_spend, current_price, symbol_info)

        logger.info(
            f"🔄 Placing MARKET BUY order: {quantity} {order_params.symbol} at ${current_price}"
        )

        # Market buy order yerleştir
        order = client.order_market_buy(symbol=order_params.symbol, quantity=quantity)

        # Trade data hazırla
        trade_data = {
            "timestamp": order.get("transactTime"),
            "symbol": order_params.symbol,
            "side": order_params.side.value,
            "type": f"${usdt_to_spend:.2f}_Market_Buy"
            if amount_type.lower() == "usdt"
            else f"{amount_or_percentage * 100:.0f}%_Market_Buy",
            "quantity": quantity,
            "price": current_price,
            "total_cost": usdt_to_spend,
            "wallet_before": usdt_balance,
            "wallet_after": usdt_balance - usdt_to_spend,
            "order_id": order.get("orderId"),
            "order_type": order_params.order_type.value,
            "status": order.get("status", "FILLED"),
            "amount_type": amount_type,
            "input_amount": amount_or_percentage,
        }

        # Trade data kaydet
        data_manager.save_trade(trade_data)

        # Order bilgilerini daha detaylı göster
        order_type = order.get("type", "UNKNOWN")
        order_status = order.get("status", "UNKNOWN")
        executed_qty = order.get("executedQty", "0")
        avg_price = (
            float(order.get("cummulativeQuoteQty", 0)) / float(executed_qty)
            if float(executed_qty) > 0
            else 0
        )

        logger.info(f"✅ {order_type} BUY order completed: {symbol}")
        logger.info(
            f"   📊 Status: {order_status} | Miktar: {executed_qty} | Ortalama Fiyat: {avg_price:.8f}"
        )
        logger.info(f"   💰 Amount Type: {amount_type} | Input: {amount_or_percentage}")
        logger.info(
            f"   🔗 Order ID: {order.get('orderId')} | Client ID: {order.get('clientOrderId')}"
        )

        return order

    except Exception as e:
        error_msg = f"❌ MARKET BUY order error for {symbol}: {e}"
        logger.error(error_msg)
        logger.exception("Full traceback for market buy order error:")
        raise


def place_market_sell_order(
    symbol: str,
    amount_or_percentage: float,
    amount_type: str = "percentage",
    client=None,
) -> Dict[str, Any]:
    """
    @brief Market sell order yerleştirir
    @param symbol: Trading pair symbol
    @param amount_or_percentage: İşlem miktarı (USDT amount veya percentage 0.0-1.0)
    @param amount_type: 'usdt' veya 'percentage' - hangi tip miktar olduğunu belirtir
    @param client: Binance API client (None ise otomatik oluşturulur)
    @return Order detayları
    """
    if client is None:
        client = prepare_client()

    logger = logging.getLogger("place_market_sell_order")

    try:
        from data.data_manager import data_manager

        # Amount type validasyonu
        if amount_type.lower() not in ["usdt", "percentage"]:
            raise ValueError(
                f"Invalid amount_type: {amount_type}. Must be 'usdt' or 'percentage'"
            )

        # Amount loglama
        if amount_type.lower() == "usdt":
            logger.info(f"💰 Market sell amount: ${amount_or_percentage:.2f} USDT")
        else:
            logger.info(f"📊 Market sell percentage: {amount_or_percentage * 100:.2f}%")

        # Genel bilgileri al
        current_price = get_price(client, symbol)
        symbol_info = get_symbol_info(client, symbol)

        # Asset amount al
        asset_amount = get_amountOf_asset(client, symbol)
        logger.info(f"💼 Current {symbol} balance: {asset_amount}")

        # Miktar hesaplama
        if amount_type.lower() == "usdt":
            # USDT amount'u asset quantity'ye çevir
            quantity_from_usdt = float(amount_or_percentage) / current_price
            quantity_to_sell = min(quantity_from_usdt, asset_amount)  # Balance kontrolü
            actual_percentage = (
                quantity_to_sell / asset_amount if asset_amount > 0 else 0
            )
            logger.info(
                f"💰 Converting ${amount_or_percentage:.2f} to {quantity_to_sell} {symbol} (≈{actual_percentage * 100:.2f}% of balance)"
            )
        else:
            # Percentage kullan
            quantity_to_sell = asset_amount * float(amount_or_percentage)
            logger.info(
                f"📊 Using percentage: {amount_or_percentage * 100:.2f}% = {quantity_to_sell} {symbol}"
            )

        # OrderParameters objesi oluştur
        order_params = OrderParameters(
            symbol=symbol,
            side=OrderSide.SELL,
            percentage=quantity_to_sell / asset_amount if asset_amount > 0 else 0,
            order_type=OrderType.MARKET,
        )

        quantity = calculate_sell_quantity(quantity_to_sell, symbol_info)

        logger.info(
            f"🔄 Placing MARKET SELL order: {quantity} {order_params.symbol} at ${current_price}"
        )

        # Market sell order yerleştir
        order = client.order_market_sell(symbol=order_params.symbol, quantity=quantity)

        # Trade data hazırla
        total_usdt = quantity * current_price
        trade_data = {
            "timestamp": order.get("transactTime"),
            "symbol": order_params.symbol,
            "side": order_params.side.value,
            "type": f"${amount_or_percentage:.2f}_Market_Sell"
            if amount_type.lower() == "usdt"
            else f"{amount_or_percentage * 100:.0f}%_Market_Sell",
            "quantity": quantity,
            "price": current_price,
            "total_cost": total_usdt,
            "wallet_before": asset_amount,
            "wallet_after": asset_amount - quantity,
            "order_id": order.get("orderId"),
            "order_type": order_params.order_type.value,
            "status": order.get("status", "FILLED"),
            "amount_type": amount_type,
            "input_amount": amount_or_percentage,
        }

        # Trade data kaydet
        data_manager.save_trade(trade_data)

        # Order bilgilerini daha detaylı göster
        order_type = order.get("type", "UNKNOWN")
        order_status = order.get("status", "UNKNOWN")
        executed_qty = order.get("executedQty", "0")
        total_received = order.get("cummulativeQuoteQty", "0")
        avg_price = (
            float(total_received) / float(executed_qty)
            if float(executed_qty) > 0
            else 0
        )

        logger.info(f"✅ {order_type} SELL order completed: {symbol}")
        logger.info(
            f"   📊 Status: {order_status} | Satılan: {executed_qty} | Ortalama Fiyat: {avg_price:.8f}"
        )
        logger.info(f"   💰 Amount Type: {amount_type} | Input: {amount_or_percentage}")
        logger.info(
            f"   💰 Toplam Alınan: {total_received} USDT | Order ID: {order.get('orderId')}"
        )

        return order

    except Exception as e:
        error_msg = f"❌ MARKET SELL order error for {symbol}: {e}"
        logger.error(error_msg)
        logger.exception("Full traceback for market sell order error:")
        raise


def get_current_price(symbol: str, client=None) -> float:
    """
    @brief Güncel fiyatı getirir
    @param symbol: Trading pair symbol
    @param client: Binance API client (None ise otomatik oluşturulur)
    @return Güncel fiyat
    """
    if client is None:
        client = prepare_client()

    logger = logging.getLogger("get_current_price")

    try:
        price = get_price(client, symbol)
        logger.info(f"Current price for {symbol}: ${price}")

        return price

    except Exception as e:
        error_msg = f"❌ Get current price error for {symbol}: {e}"
        logger.error(error_msg)
        logger.exception("Full traceback for get current price error:")
        raise
