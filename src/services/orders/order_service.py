"""
order_service.py (Refactored - Core Order Engine Only)
Bu modül sadece ana order execution engine'ini içerir.
Diğer fonksiyonlar account_service.py ve trading_utils.py'ye taşındı.
"""

import logging
import os
import sys

# Import centralized paths
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from ..client_service import prepare_client, force_client_reload, get_cached_client_info
    from config.preferences_manager import get_buy_preferences, force_preferences_reload, get_order_type
    from ..account_service import retrieve_usdt_balance, get_amountOf_asset
    from utils.trading_utils import get_price, get_symbol_info, calculate_buy_quantity, calculate_sell_quantity
    from .order_type_manager import get_effective_order_type
except ImportError:
    # Fallback for direct execution
    from services.client_service import prepare_client, force_client_reload, get_cached_client_info
    from config.preferences_manager import get_buy_preferences, force_preferences_reload, get_order_type
    from services.account_service import retrieve_usdt_balance, get_amountOf_asset
    from utils.trading_utils import get_price, get_symbol_info, calculate_buy_quantity, calculate_sell_quantity
    from services.orders.order_type_manager import get_effective_order_type

# Import order types from models
from models.order_types import OrderManager, OrderFactory, RiskLevel, OrderSide, OrderType, OrderParameters


def validate_amount_type(amount_type):
    """
    @brief Validates the amount type parameter
    @param amount_type: The amount type to validate
    @return bool: True if valid, False otherwise
    """
    valid_types = ['usdt', 'percentage']
    return amount_type.lower() in valid_types


def convert_usdt_to_percentage(usdt_amount, usdt_balance):
    """
    @brief Converts USDT amount to percentage of balance
    @param usdt_amount: The USDT amount
    @param usdt_balance: The current USDT balance
    @return float: Percentage (0.0-1.0)
    """
    if usdt_balance <= 0:
        return 0.0
    return min(usdt_amount / usdt_balance, 1.0)


def convert_percentage_to_usdt(percentage, usdt_balance):
    """
    @brief Converts percentage to USDT amount
    @param percentage: The percentage (0.0-1.0)
    @param usdt_balance: The current USDT balance
    @return float: USDT amount
    """
    return usdt_balance * percentage


def log_order_amount(amount_or_percentage, amount_type, balance=None):
    """
    @brief Logs order amount information in a standardized format
    @param amount_or_percentage: The amount or percentage value
    @param amount_type: Type of amount ('usdt' or 'percentage')
    @param balance: Optional balance for additional context
    """
    # Validate input is a number
    if not isinstance(amount_or_percentage, (int, float)):
        logging.error(f"❌ Invalid amount_or_percentage type: {type(amount_or_percentage).__name__}")
        return
    
    if amount_type.lower() == 'usdt':
        logging.info(f"💰 Order Amount: ${amount_or_percentage:.2f} USDT")
        if balance is not None and isinstance(balance, (int, float)) and balance > 0:
            percentage = convert_usdt_to_percentage(amount_or_percentage, balance)
            logging.info(f"   📊 Equivalent to: {percentage*100:.2f}% of balance")
    else:
        logging.info(f"📊 Order Percentage: {amount_or_percentage*100:.2f}%")
        if balance is not None and isinstance(balance, (int, float)) and balance > 0:
            usdt_amount = convert_percentage_to_usdt(amount_or_percentage, balance)
            logging.info(f"   💰 Equivalent to: ${usdt_amount:.2f} USDT")


def place_order(client, symbol, side, amount_or_percentage, amount_type='percentage'):
    """
    @brief Market order yerleştirir (buy veya sell) - Model sınıflarını kullanır.
    @param client: Binance API client
    @param symbol: Trading pair symbol
    @param side: 'BUY' veya 'SELL' (OrderSide enum de kullanılabilir)
    @param amount_or_percentage: İşlem miktarı (USDT amount veya percentage 0.0-1.0)
    @param amount_type: 'usdt' veya 'percentage' - hangi tip miktar olduğunu belirtir
    @return dict: Order detayları
    """
    try:
        from data.data_manager import data_manager
        
        # Amount type validasyonu
        if not validate_amount_type(amount_type):
            raise ValueError(f"Invalid amount_type: {amount_type}. Must be 'usdt' or 'percentage'")
        
        # Validate amount_or_percentage is a number
        if not isinstance(amount_or_percentage, (int, float)):
            raise TypeError(f"amount_or_percentage must be a number, got {type(amount_or_percentage).__name__}: {amount_or_percentage}")
        
        # String'i OrderSide enum'a çevir
        if isinstance(side, str):
            order_side = OrderSide.BUY if side.upper() == 'BUY' else OrderSide.SELL
        else:
            order_side = side
        
        # Amount type kontrolü ve loglama
        if amount_type.lower() == 'usdt':
            usdt_amount = float(amount_or_percentage)
            logging.info(f"💰 Order amount: ${usdt_amount:.2f} USDT")
        elif amount_type.lower() == 'percentage':
            percentage = float(amount_or_percentage)
            logging.info(f"📊 Order percentage: {percentage*100:.2f}%")
        
        # OrderParameters objesi oluştur
        if amount_type.lower() == 'percentage':
            order_params = OrderParameters(
                symbol=symbol,
                side=order_side,
                percentage=amount_or_percentage,
                order_type=OrderType.MARKET
            )
        else:
            # USDT amount için percentage hesapla
            order_params = OrderParameters(
                symbol=symbol,
                side=order_side,
                percentage=amount_or_percentage,  # Temporary, will be recalculated
                order_type=OrderType.MARKET
            )
        
        # Genel bilgileri al
        current_price = get_price(client, order_params.symbol)
        symbol_info = get_symbol_info(client, order_params.symbol)
        
        if order_params.side == OrderSide.BUY:
            # BUY işlemi için USDT balance al
            usdt_balance = retrieve_usdt_balance(client)
            logging.info(f"💼 Current USDT balance: ${usdt_balance:.2f}")
            
            if amount_type.lower() == 'usdt':
                # USDT amount kullan
                usdt_to_spend = min(usdt_amount, usdt_balance)  # Balance kontrolü
                actual_percentage = convert_usdt_to_percentage(usdt_to_spend, usdt_balance)
                log_order_amount(usdt_to_spend, 'usdt', usdt_balance)
            else:
                # Percentage kullan
                usdt_to_spend = convert_percentage_to_usdt(percentage, usdt_balance)
                log_order_amount(percentage, 'percentage', usdt_balance)
            
            quantity = calculate_buy_quantity(usdt_to_spend, current_price, symbol_info)
            
            logging.info(f"🔄 Placing {order_params.side.value} order: {quantity} {order_params.symbol} at ${current_price}")
            order = client.order_market_buy(symbol=order_params.symbol, quantity=quantity)
            
            # Trade data hazırla
            trade_data = {
                'timestamp': order.get('transactTime'),
                'symbol': order_params.symbol,
                'side': order_params.side.value,
                'type': f'${usdt_to_spend:.2f}_Buy' if amount_type.lower() == 'usdt' else f'{percentage*100:.0f}%_Buy',
                'quantity': quantity,
                'price': current_price,
                'total_cost': usdt_to_spend,
                'wallet_before': usdt_balance,
                'wallet_after': usdt_balance - usdt_to_spend,
                'order_id': order.get('orderId'),
                'order_type': order_params.order_type.value,
                'amount_type': amount_type,
                'input_amount': amount_or_percentage
            }
            
        elif order_params.side == OrderSide.SELL:
            # SELL işlemi için asset amount al
            asset_amount = get_amountOf_asset(client, order_params.symbol)
            logging.info(f"💼 Current {symbol} balance: {asset_amount}")
            
            if amount_type.lower() == 'usdt':
                # USDT amount'u asset quantity'ye çevir
                quantity_from_usdt = usdt_amount / current_price
                quantity_to_sell = min(quantity_from_usdt, asset_amount)  # Balance kontrolü
                actual_percentage = quantity_to_sell / asset_amount if asset_amount > 0 else 0
                logging.info(f"💰 Converting ${usdt_amount:.2f} to {quantity_to_sell} {symbol} (≈{actual_percentage*100:.2f}% of balance)")
            else:
                # Percentage kullan
                quantity_to_sell = asset_amount * percentage
                logging.info(f"📊 Using percentage: {percentage*100:.2f}% = {quantity_to_sell} {symbol}")
            
            quantity = calculate_sell_quantity(quantity_to_sell, symbol_info)
            
            logging.info(f"🔄 Placing {order_params.side.value} order: {quantity} {order_params.symbol} at ${current_price}")
            order = client.order_market_sell(symbol=order_params.symbol, quantity=quantity)
            
            # Trade data hazırla
            total_usdt = quantity * current_price
            trade_data = {
                'timestamp': order.get('transactTime'),
                'symbol': order_params.symbol,
                'side': order_params.side.value,
                'type': f'${usdt_amount:.2f}_Sell' if amount_type.lower() == 'usdt' else f'{percentage*100:.0f}%_Sell',
                'quantity': quantity,
                'price': current_price,
                'total_cost': total_usdt,
                'wallet_before': asset_amount,
                'wallet_after': asset_amount - quantity,
                'order_id': order.get('orderId'),
                'order_type': order_params.order_type.value,
                'amount_type': amount_type,
                'input_amount': amount_or_percentage
            }
        else:
            raise ValueError(f"Invalid order side: {order_params.side}. Must be OrderSide.BUY or OrderSide.SELL")
        
        # Trade data kaydet
        data_manager.save_trade(trade_data)
        
        # Comprehensive logging
        logging.info(f"✅ {order_params.side.value} order completed successfully:")
        logging.info(f"   📈 Symbol: {order_params.symbol}")
        logging.info(f"   💰 Quantity: {trade_data['quantity']}")
        logging.info(f"   💵 Price: ${trade_data['price']:.6f}")
        logging.info(f"   💎 Total Cost: ${trade_data['total_cost']:.2f}")
        logging.info(f"   🔢 Order ID: {trade_data['order_id']}")
        logging.info(f"   📊 Amount Type: {trade_data['amount_type']}")
        logging.info(f"   🎯 Input Amount: {trade_data['input_amount']}")
        
        return order
        
    except Exception as e:
        error_msg = f"❌ {order_side.value if 'order_side' in locals() else side} order error for {symbol}: {e}"
        print(error_msg)
        logging.error(error_msg)
        logging.exception(f"Full traceback for {order_side.value if 'order_side' in locals() else side} order error:")
        raise


def place_BUY_order(client, SYMBOL, amount_or_percentage, amount_type='percentage'):
    """
    @brief BUY order wrapper - supports both USDT amount and percentage
    @param client: Binance API client
    @param SYMBOL: Trading pair symbol
    @param amount_or_percentage: USDT amount or percentage (0.0-1.0)
    @param amount_type: 'usdt' or 'percentage'
    """
    return place_order(client, SYMBOL, OrderSide.BUY, amount_or_percentage, amount_type)


def place_SELL_order(client, SYMBOL, amount_or_percentage, amount_type='percentage'):
    """
    @brief SELL order wrapper - supports both USDT amount and percentage
    @param client: Binance API client
    @param SYMBOL: Trading pair symbol
    @param amount_or_percentage: USDT amount or percentage (0.0-1.0)
    @param amount_type: 'usdt' or 'percentage'
    """
    return place_order(client, SYMBOL, OrderSide.SELL, amount_or_percentage, amount_type)


def execute_order(order_type: str, symbol: str, client=None, order_execution_type=None, limit_price=None, 
                 amount_or_percentage=None, amount_type='percentage', terminal_callback=None):
    """
    @brief Order execute eder - MARKET veya LIMIT türünde (preferences'dan otomatik alınır)
    @param order_type: Order türü ("Hard_Buy", "Hard_Sell", "Soft_Buy", "Soft_Sell")
    @param symbol: Trading pair symbol
    @param client: Binance API client (None ise otomatik oluşturulur)
    @param order_execution_type: Order execution türü (None ise preferences'dan alınır)
    @param limit_price: Limit order için fiyat (LIMIT order için gerekli)
    @param amount_or_percentage: İşlem miktarı (None ise preferences'dan alınır)
    @param amount_type: 'usdt' veya 'percentage' - hangi tip miktar olduğunu belirtir
    @param terminal_callback: Terminal widget'a mesaj göndermek için callback function
    @return Order detayları
    """
    if client is None:
        client = prepare_client()
    
    risk_preferences = get_buy_preferences()
    
    # Order execution type'ı preferences'dan al (session override dahil)
    if order_execution_type is None:
        order_execution_type = get_effective_order_type()
        logging.info(f"📋 Using effective order type: {order_execution_type}")
    
    # Amount loglama
    if amount_or_percentage is not None:
        if not validate_amount_type(amount_type):
            raise ValueError(f"Invalid amount_type: {amount_type}. Must be 'usdt' or 'percentage'")
        
        # Validate amount_or_percentage is a number
        if not isinstance(amount_or_percentage, (int, float)):
            raise TypeError(f"amount_or_percentage must be a number, got {type(amount_or_percentage).__name__}: {amount_or_percentage}")
        
        # Get balance for context in logging
        try:
            current_balance = retrieve_usdt_balance(client)
            log_order_amount(amount_or_percentage, amount_type, current_balance)
        except Exception:
            # Fallback to simple logging if balance retrieval fails
            if amount_type.lower() == 'usdt':
                logging.info(f"💰 Order amount specified: ${amount_or_percentage:.2f} USDT")
            else:
                logging.info(f"📊 Order percentage specified: {amount_or_percentage*100:.2f}%")
    else:
        logging.info(f"📋 Using default amount from preferences")
    
    try:
        order_manager = OrderManager(client, risk_preferences, terminal_callback)
        
        # Order execution type validasyonu
        if not order_manager.validate_execution_type(order_execution_type):
            available_types = order_manager.get_available_execution_types()
            raise ValueError(f"Geçersiz order execution type: {order_execution_type}. Geçerli değerler: {available_types}")
        
        # Limit order için fiyat kontrolü veya otomatik hesaplama
        if order_execution_type == "LIMIT" and limit_price is None:
            # Limit price otomatik hesaplanır
            current_price = get_price(client, symbol)
            if "Buy" in order_type:
                # Buy için %0.01 üstünde limit fiyat (agresif strateji)
                limit_price = current_price * 1.0001
                logging.info(f"🔢 Auto-calculated limit buy price: ${limit_price:.6f} (0.01% above current price)")
            else:
                # Sell için %0.01 altında limit fiyat
                limit_price = current_price * 0.9999
                logging.info(f"🔢 Auto-calculated limit sell price: ${limit_price:.6f} (0.01% below current price)")
        
        logging.info(f"🔄 Executing {order_type} order for {symbol} with {order_execution_type} type")
        
        # Amount parametresini order_manager'a gönder
        if amount_or_percentage is not None:
            order_result = order_manager.execute_order(order_type, symbol, order_execution_type, limit_price, 
                                                     amount_or_percentage, amount_type)
        else:
            order_result = order_manager.execute_order(order_type, symbol, order_execution_type, limit_price)
        
        logging.info(f"✅ {order_type} order completed for {symbol}")
        
        return order_result
        
    except Exception as e:
        error_msg = f"❌ {order_type} order hatası - {symbol}: {e}"
        print(error_msg)
        logging.error(f"Error in execute_order: {error_msg}")
        logging.exception("Full traceback for order execution error:")
        raise



def make_order(Style, Symbol, order_type=None, limit_price=None, amount_or_percentage=None, 
               amount_type='percentage', terminal_callback=None):
    """
    @brief Executes an order based on the specified style and symbol using the new centralized approach.
    @param Style: The type of order to execute ("Hard_Buy", "Hard_Sell", "Soft_Buy", "Soft_Sell").
    @param Symbol: Trading pair symbol (e.g., "BTCUSDT").
    @param order_type: Order type (None ise preferences'dan alınır, "MARKET" or "LIMIT").
    @param limit_price: Limit price for LIMIT orders (auto-calculated if None).
    @param amount_or_percentage: İşlem miktarı (None ise preferences'dan alınır)
    @param amount_type: 'usdt' veya 'percentage' - hangi tip miktar olduğunu belirtir
    @param terminal_callback: Terminal widget'a mesaj göndermek için callback function
    @return dict: Details of the executed order.
    """
    try:
        import datetime
        from data.data_manager import data_manager
        
        client = prepare_client()
        wallet_before = retrieve_usdt_balance(client)
        
        # Order type'ı preferences'dan al (session override dahil)
        if order_type is None:
            order_type = get_effective_order_type()
            logging.info(f"📋 Using effective order type: {order_type}")
        
        # Amount/percentage parametresi loglama
        if amount_or_percentage is not None:
            # Validate amount_or_percentage is a number
            if not isinstance(amount_or_percentage, (int, float)):
                raise TypeError(f"amount_or_percentage must be a number, got {type(amount_or_percentage).__name__}: {amount_or_percentage}")
            
            if amount_type.lower() == 'usdt':
                logging.info(f"💰 Custom order amount: ${amount_or_percentage:.2f} USDT")
            else:
                logging.info(f"📊 Custom order percentage: {amount_or_percentage*100:.2f}%")
        else:
            logging.info(f"📋 Using default amount/percentage from preferences")
        
        # Execute order using centralized function
        order = execute_order(Style, Symbol, client, order_type, limit_price, 
                            amount_or_percentage, amount_type, terminal_callback)
        
        if order:
            # Get wallet balance after trade
            wallet_after = retrieve_usdt_balance(client)
            
            # Extract trade information
            if order_type == "MARKET" and 'fills' in order and order['fills']:
                # Market order - use fills data
                price = float(order['fills'][0]['price'])
                quantity = float(order['fills'][0]['qty'])
                total_cost = float(order.get('cummulativeQuoteQty', quantity * price))
            else:
                # Limit order - use order data
                price = float(order.get('price', limit_price))
                quantity = float(order.get('origQty', 0))
                total_cost = quantity * price
            
            balance_change = wallet_after - wallet_before
            
            # Type field for trade data based on amount type
            if amount_or_percentage is not None:
                if amount_type.lower() == 'usdt':
                    type_suffix = f'${amount_or_percentage:.2f}_{Style.split("_")[-1]}'
                else:
                    type_suffix = f'{amount_or_percentage*100:.1f}%_{Style.split("_")[-1]}'
            else:
                type_suffix = Style
            
            # Prepare trade data for saving
            trade_data = {
                'timestamp': datetime.datetime.now().isoformat(),
                'symbol': Symbol.upper(),
                'side': 'BUY' if 'Buy' in Style else 'SELL',
                'type': type_suffix,
                'quantity': quantity,
                'price': price,
                'total_cost': total_cost,
                'wallet_before': wallet_before,
                'wallet_after': wallet_after,
                'order_id': order.get('orderId', 'unknown'),
                'order_type': order_type,
                'status': order.get('status', 'UNKNOWN'),
                'amount_type': amount_type if amount_or_percentage is not None else 'default',
                'input_amount': amount_or_percentage,
                'balance_change': balance_change,
                'binance_data': order  # Store full Binance response
            }
            
            # Save trade to data manager
            data_manager.save_trade(trade_data)
            
            # Detailed logging
            amount_info = f"${amount_or_percentage:.2f} USDT" if amount_type.lower() == 'usdt' and amount_or_percentage else f"{amount_or_percentage*100:.1f}%" if amount_or_percentage else "default"
            logging.info(f"💹 Complete trade executed and saved: {Style} {Symbol}")
            logging.info(f"   📊 Amount: {amount_info}")
            logging.info(f"   💰 Quantity: {quantity} @ ${price:.6f}")
            logging.info(f"   🔄 Order Type: {order_type}")
            logging.info(f"   💼 Balance Change: ${balance_change:.2f}")
        
        return order
        
    except Exception as e:
        print(f"❌ TRADING İŞLEMİ HATASI: {e}")
        print(f"Emir tipi: {Style}, Sembol: {Symbol}, Order Type: {order_type}")
        if amount_or_percentage is not None:
            print(f"Amount: {amount_or_percentage} ({amount_type})")
        logging.error(f"Error in make_order: {e}")
        logging.error(f"Order parameters: Style={Style}, Symbol={Symbol}, order_type={order_type}, limit_price={limit_price}")
        logging.error(f"Amount parameters: amount_or_percentage={amount_or_percentage}, amount_type={amount_type}")
        logging.exception("Full traceback for make_order error:")
        raise




