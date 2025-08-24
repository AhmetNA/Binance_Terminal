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
    from .client_service import prepare_client, force_client_reload, get_cached_client_info
    from config.preferences_manager import get_buy_preferences, force_preferences_reload, get_cached_preferences_info
    from .account_service import retrieve_usdt_balance, get_amountOf_asset
    from utils.trading_utils import get_price, get_symbol_info, calculate_buy_quantity, calculate_sell_quantity
except ImportError:
    # Fallback for direct execution
    from services.client_service import prepare_client, force_client_reload, get_cached_client_info
    from config.preferences_manager import get_buy_preferences, force_preferences_reload, get_cached_preferences_info
    from services.account_service import retrieve_usdt_balance, get_amountOf_asset
    from utils.trading_utils import get_price, get_symbol_info, calculate_buy_quantity, calculate_sell_quantity

# Import order types from models
from models.order_types import OrderManager, OrderFactory, RiskLevel, OrderSide, OrderType, OrderParameters


def place_order(client, symbol, side, quantity_percentage):
    """
    @brief Market order yerleştirir (buy veya sell) - Model sınıflarını kullanır.
    @param client: Binance API client
    @param symbol: Trading pair symbol
    @param side: 'BUY' veya 'SELL' (OrderSide enum de kullanılabilir)
    @param quantity_percentage: İşlem yüzdesi (0.0-1.0)
    @return dict: Order detayları
    """
    try:
        from data.data_manager import data_manager
        
        # String'i OrderSide enum'a çevir
        if isinstance(side, str):
            order_side = OrderSide.BUY if side.upper() == 'BUY' else OrderSide.SELL
        else:
            order_side = side
        
        # OrderParameters objesi oluştur
        order_params = OrderParameters(
            symbol=symbol,
            side=order_side,
            percentage=quantity_percentage,
            order_type=OrderType.MARKET
        )
        
        # Genel bilgileri al
        current_price = get_price(client, order_params.symbol)
        symbol_info = get_symbol_info(client, order_params.symbol)
        
        if order_params.side == OrderSide.BUY:
            # BUY işlemi için USDT balance al
            usdt_balance = retrieve_usdt_balance(client)
            usdt_to_spend = usdt_balance * order_params.percentage
            quantity = calculate_buy_quantity(usdt_to_spend, current_price, symbol_info)
            
            logging.info(f"🔄 Placing {order_params.side.value} order: {quantity} {order_params.symbol} at ${current_price}")
            order = client.order_market_buy(symbol=order_params.symbol, quantity=quantity)
            
            # Trade data hazırla
            trade_data = {
                'timestamp': order.get('transactTime'),
                'symbol': order_params.symbol,
                'side': order_params.side.value,
                'type': f'{order_params.percentage*100:.0f}%_Buy',
                'quantity': quantity,
                'price': current_price,
                'total_cost': usdt_to_spend,
                'wallet_before': usdt_balance,
                'wallet_after': usdt_balance - usdt_to_spend,
                'order_id': order.get('orderId'),
                'order_type': order_params.order_type.value
            }
            
        elif order_params.side == OrderSide.SELL:
            # SELL işlemi için asset amount al
            asset_amount = get_amountOf_asset(client, order_params.symbol)
            quantity_to_sell = asset_amount * order_params.percentage
            quantity = calculate_sell_quantity(quantity_to_sell, symbol_info)
            
            logging.info(f"🔄 Placing {order_params.side.value} order: {quantity} {order_params.symbol} at ${current_price}")
            order = client.order_market_sell(symbol=order_params.symbol, quantity=quantity)
            
            # Trade data hazırla
            total_usdt = quantity * current_price
            trade_data = {
                'timestamp': order.get('transactTime'),
                'symbol': order_params.symbol,
                'side': order_params.side.value,
                'type': f'{order_params.percentage*100:.0f}%_Sell',
                'quantity': quantity,
                'price': current_price,
                'total_cost': total_usdt,
                'wallet_before': asset_amount,
                'wallet_after': asset_amount - quantity,
                'order_id': order.get('orderId'),
                'order_type': order_params.order_type.value
            }
        else:
            raise ValueError(f"Invalid order side: {order_params.side}. Must be OrderSide.BUY or OrderSide.SELL")
        
        # Trade data kaydet
        data_manager.save_trade(trade_data)
        
        logging.info(f"✅ {order_params.side.value} order completed: {order}")
        return order
        
    except Exception as e:
        error_msg = f"❌ {order_side.value if 'order_side' in locals() else side} order error for {symbol}: {e}"
        print(error_msg)
        logging.error(error_msg)
        logging.exception(f"Full traceback for {order_side.value if 'order_side' in locals() else side} order error:")
        raise


def place_BUY_order(client, SYMBOL, BUY_QUANTITY_P):
    return place_order(client, SYMBOL, OrderSide.BUY, BUY_QUANTITY_P)


def place_SELL_order(client, SYMBOL, SELL_QUANTITY_P):
    return place_order(client, SYMBOL, OrderSide.SELL, SELL_QUANTITY_P)


def execute_order(order_type: str, symbol: str, client=None):
    
    if client is None:
        client = prepare_client()
    
    risk_preferences = get_buy_preferences()
    
    try:
        order_manager = OrderManager(client, risk_preferences)
        
        logging.info(f"🔄 Executing {order_type} order for {symbol}")
        order_result = order_manager.execute_order(order_type, symbol)
        logging.info(f"✅ {order_type} order completed for {symbol}")
        
        return order_result
        
    except Exception as e:
        error_msg = f"❌ {order_type} order hatası - {symbol}: {e}"
        print(error_msg)
        logging.error(f"Error in execute_order: {error_msg}")
        logging.exception("Full traceback for order execution error:")
        raise



def make_order(Style, Symbol):
    """
    @brief Executes an order based on the specified style and symbol using the new centralized approach.
    @param Style: The type of order to execute ("Hard_Buy", "Hard_Sell", "Soft_Buy", "Soft_Sell").
    @param Symbol: Trading pair symbol (e.g., "BTCUSDT").
    @return dict: Details of the executed order.
    """
    try:
        import datetime
        from data.data_manager import data_manager
        
        client = prepare_client()
        wallet_before = retrieve_usdt_balance(client)
        
        # Execute order using centralized function
        order = execute_order(Style, Symbol, client)
        
        if order:
            # Get wallet balance after trade
            wallet_after = retrieve_usdt_balance(client)
            
            # Extract trade information
            price = float(order['fills'][0]['price'])
            quantity = float(order['fills'][0]['qty'])
            total_cost = float(order.get('cummulativeQuoteQty', quantity * price))
            
            balance_change = wallet_after - wallet_before
            
            # Prepare trade data for saving
            trade_data = {
                'timestamp': datetime.datetime.now().isoformat(),
                'symbol': Symbol.upper(),
                'side': 'BUY' if 'Buy' in Style else 'SELL',
                'type': Style,
                'quantity': quantity,
                'price': price,
                'total_cost': total_cost,
                'wallet_before': wallet_before,
                'wallet_after': wallet_after,
                'order_id': order.get('orderId', 'unknown'),
                'binance_data': order  # Store full Binance response
            }
            
            # Save trade to data manager
            data_manager.save_trade(trade_data)
            
            # Take portfolio snapshot after trade (asynchronously to avoid UI freezing)
            try:
                import threading
                from services.portfolio_tracker import portfolio_tracker
                
                def take_snapshot_async():
                    try:
                        portfolio_tracker.take_snapshot()
                    except Exception as e:
                        logging.error(f"Error taking portfolio snapshot in background: {e}")
                
                # Run snapshot in background thread
                snapshot_thread = threading.Thread(target=take_snapshot_async, daemon=True)
                snapshot_thread.start()
                
            except Exception as e:
                logging.error(f"Error starting portfolio snapshot thread: {e}")
            
            logging.info(f"Complete trade executed and saved: {Style} {Symbol} - {quantity} @ {price}")
        
        return order
        
    except Exception as e:
        print(f"❌ TRADING İŞLEMİ HATASI: {e}")
        print(f"Emir tipi: {Style}, Sembol: {Symbol}")
        logging.error(f"Error in make_order: {e}")
        logging.error(f"Order parameters: Style={Style}, Symbol={Symbol}")
        logging.exception("Full traceback for make_order error:")
        raise


def validate_order_request(order_type: str, symbol: str) -> tuple:
    try:
        client = prepare_client()
        
        order_manager = OrderManager(client)
        
        if not order_manager.validate_order_style(order_type):
            available_types = order_manager.get_available_order_styles()
            return False, f"Invalid order type: {order_type}. Available: {available_types}"
        
        if not symbol or len(symbol) < 3:
            return False, f"Invalid symbol format: {symbol}"
        
        try:
            dummy_order = OrderFactory.create_order(order_type, client, symbol)
            if not dummy_order.validate_symbol():
                return False, f"Symbol {symbol} is not available for trading"
        except Exception as e:
            return False, f"Symbol validation error: {str(e)}"
        
        return True, None
        
    except Exception as e:
        return False, f"Validation error: {str(e)}"


