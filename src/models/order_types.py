"""
order_types.py
Bu dosya farklı order türleri için class yapılarını içerir.
Her order türü kendine özel özelliklere sahiptir ve daha organize kod yapısı sağlar.
"""

from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, Any
import logging


class OrderSide(Enum):
    """Order yönü için enum"""
    BUY = "BUY"
    SELL = "SELL"


class OrderType(Enum):
    """Order türü için enum"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LOSS = "STOP_LOSS"
    STOP_LOSS_LIMIT = "STOP_LOSS_LIMIT"


class RiskLevel(Enum):
    """Risk seviyesi için enum"""
    SOFT = "SOFT"
    HARD = "HARD"


@dataclass
class OrderParameters:
    """Order parametreleri için veri sınıfı"""
    symbol: str
    side: OrderSide
    quantity: Optional[float] = None
    price: Optional[float] = None
    percentage: Optional[float] = None
    stop_price: Optional[float] = None
    order_type: OrderType = OrderType.MARKET
    risk_level: Optional[RiskLevel] = None


class BaseOrder(ABC):
    """Tüm order türleri için temel abstract class"""
    
    def __init__(self, client, symbol: str, risk_preferences: tuple = None):
        """
        @brief BaseOrder constructor
        @param client: Binance API client instance
        @param symbol: Trading pair symbol (e.g., "BTCUSDT")
        @param risk_preferences: (soft_risk, hard_risk) tuple
        """
        self.client = client
        self.symbol = symbol.upper()
        
        # Risk preferences'ı al - eğer none ise preferences dosyasından oku
        if risk_preferences is None:
            try:
                from config.preferences_manager import get_buy_preferences
                self.soft_risk, self.hard_risk = get_buy_preferences()
            except ImportError:
                self.soft_risk, self.hard_risk = (0.1, 0.2)  # Fallback
        else:
            self.soft_risk, self.hard_risk = risk_preferences
            
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Symbol'ü normalize et
        if "USDT" not in self.symbol:
            self.symbol = self.symbol + "USDT"
    
    @abstractmethod
    def execute(self) -> Dict[str, Any]:
        """
        @brief Order'ı execute eden abstract method
        @return Order detaylarını içeren dictionary
        """
        pass
    
    def get_risk_percentage(self, risk_level: RiskLevel) -> float:
        """
        @brief Risk seviyesine göre yüzdeyi döndürür
        @param risk_level: Risk seviyesi
        @return Risk yüzdesi
        """
        return self.hard_risk if risk_level == RiskLevel.HARD else self.soft_risk
    
    def validate_symbol(self) -> bool:
        """
        @brief Symbol'ün geçerli olup olmadığını kontrol eder - Hızlı yöntem
        @return Geçerli ise True, değilse False
        """
        try:
            # Sadece o symbol için ticker istatistiği çek - çok hızlı!
            ticker = self.client.get_ticker(symbol=self.symbol)
            return ticker is not None and 'symbol' in ticker
        except Exception as e:
            # Symbol geçersizse Binance exception fırlatır
            self.logger.debug(f"Symbol validation failed for {self.symbol}: {e}")
            return False


class MarketBuyOrder(BaseOrder):
    """Market buy order sınıfı"""
    
    def __init__(self, client, symbol: str, risk_level: RiskLevel, risk_preferences: tuple = None):
        """
        @brief MarketBuyOrder constructor
        @param client: Binance API client
        @param symbol: Trading pair symbol
        @param risk_level: Risk seviyesi (SOFT veya HARD)
        @param risk_preferences: Risk tercihleri tuple'ı
        """
        super().__init__(client, symbol, risk_preferences)
        self.risk_level = risk_level
        self.side = OrderSide.BUY
        self.order_type = OrderType.MARKET
    
    def execute(self) -> Dict[str, Any]:
        """
        @brief Market buy order'ını execute eder
        @return Order detayları
        """
        try:
            from services.orders.order_service import place_BUY_order
            from config.preferences_manager import get_risk_type
            
            # Risk type'ına göre amount ve amount_type belirle
            risk_type = get_risk_type()
            amount = self.get_risk_percentage(self.risk_level)
            
            if risk_type == "USDT":
                # USDT amount olarak kullan
                amount_type = 'usdt'
                self.logger.info(f"Executing {self.risk_level.value} market buy for {self.symbol} with ${amount:.2f} USDT")
            else:
                # Percentage olarak kullan
                amount_type = 'percentage'
                self.logger.info(f"Executing {self.risk_level.value} market buy for {self.symbol} with {amount*100:.1f}%")
            
            order = place_BUY_order(self.client, self.symbol, amount, amount_type)
            
            self.logger.info(f"{self.risk_level.value} buy order completed for {self.symbol}")
            return order
            
        except Exception as e:
            error_msg = f"{self.risk_level.value} buy order error for {self.symbol}: {e}"
            self.logger.error(error_msg)
            raise


class MarketSellOrder(BaseOrder):
    """Market sell order sınıfı"""
    
    def __init__(self, client, symbol: str, risk_level: RiskLevel, risk_preferences: tuple = None):
        """
        @brief MarketSellOrder constructor
        @param client: Binance API client
        @param symbol: Trading pair symbol
        @param risk_level: Risk seviyesi (SOFT veya HARD)
        @param risk_preferences: Risk tercihleri tuple'ı
        """
        super().__init__(client, symbol, risk_preferences)
        self.risk_level = risk_level
        self.side = OrderSide.SELL
        self.order_type = OrderType.MARKET
    
    def execute(self) -> Dict[str, Any]:
        """
        @brief Market sell order'ını execute eder
        @return Order detayları
        """
        try:
            from services.orders.order_service import place_SELL_order
            from config.preferences_manager import get_risk_type
            
            # Risk type'ına göre amount ve amount_type belirle
            risk_type = get_risk_type()
            amount = self.get_risk_percentage(self.risk_level)
            
            if risk_type == "USDT":
                # USDT amount olarak kullan
                amount_type = 'usdt'
                self.logger.info(f"Executing {self.risk_level.value} market sell for {self.symbol} with ${amount:.2f} USDT")
            else:
                # Percentage olarak kullan
                amount_type = 'percentage'
                self.logger.info(f"Executing {self.risk_level.value} market sell for {self.symbol} with {amount*100:.1f}%")
            
            order = place_SELL_order(self.client, self.symbol, amount, amount_type)
            
            self.logger.info(f"{self.risk_level.value} sell order completed for {self.symbol}")
            return order
            
        except Exception as e:
            error_msg = f"{self.risk_level.value} sell order error for {self.symbol}: {e}"
            self.logger.error(error_msg)
            raise


class LimitBuyOrder(BaseOrder):
    """Limit buy order sınıfı"""
    
    def __init__(self, client, symbol: str, risk_level: RiskLevel, limit_price: float, risk_preferences: tuple = None, terminal_callback=None):
        """
        @brief LimitBuyOrder constructor
        @param client: Binance API client
        @param symbol: Trading pair symbol
        @param risk_level: Risk seviyesi (SOFT veya HARD)
        @param limit_price: Limit fiyatı
        @param risk_preferences: Risk tercihleri tuple'ı
        @param terminal_callback: Terminal widget'a mesaj göndermek için callback function
        """
        super().__init__(client, symbol, risk_preferences)
        self.risk_level = risk_level
        self.limit_price = limit_price
        self.side = OrderSide.BUY
        self.order_type = OrderType.LIMIT
        self.terminal_callback = terminal_callback
    
    def execute(self) -> Dict[str, Any]:
        """
        @brief Limit buy order'ını execute eder
        @return Order detayları
        """
        try:
            from services.orders.limit_order_service import place_limit_buy_order
            from config.preferences_manager import get_risk_type
            
            # Risk type'ına göre amount ve amount_type belirle
            risk_type = get_risk_type()
            amount = self.get_risk_percentage(self.risk_level)
            
            if risk_type == "USDT":
                # USDT amount olarak kullan
                amount_type = 'usdt'
                self.logger.info(f"Executing {self.risk_level.value} limit buy for {self.symbol} with ${amount:.2f} USDT at ${self.limit_price}")
            else:
                # Percentage olarak kullan
                amount_type = 'percentage'
                self.logger.info(f"Executing {self.risk_level.value} limit buy for {self.symbol} with {amount*100:.1f}% at ${self.limit_price}")
            
            order = place_limit_buy_order(
                symbol=self.symbol, 
                amount_or_percentage=amount, 
                limit_price=self.limit_price, 
                amount_type=amount_type,
                client=self.client, 
                terminal_callback=self.terminal_callback
            )
            
            self.logger.info(f"{self.risk_level.value} limit buy order placed for {self.symbol}")
            return order
            
        except Exception as e:
            error_msg = f"{self.risk_level.value} limit buy order error for {self.symbol}: {e}"
            self.logger.error(error_msg)
            raise


class LimitSellOrder(BaseOrder):
    """Limit sell order sınıfı"""
    
    def __init__(self, client, symbol: str, risk_level: RiskLevel, limit_price: float, risk_preferences: tuple = None, terminal_callback=None):
        """
        @brief LimitSellOrder constructor
        @param client: Binance API client
        @param symbol: Trading pair symbol
        @param risk_level: Risk seviyesi (SOFT veya HARD)
        @param limit_price: Limit fiyatı
        @param risk_preferences: Risk tercihleri tuple'ı
        @param terminal_callback: Terminal widget'a mesaj göndermek için callback function
        """
        super().__init__(client, symbol, risk_preferences)
        self.risk_level = risk_level
        self.limit_price = limit_price
        self.side = OrderSide.SELL
        self.order_type = OrderType.LIMIT
        self.terminal_callback = terminal_callback
    
    def execute(self) -> Dict[str, Any]:
        """
        @brief Limit sell order'ını execute eder
        @return Order detayları
        """
        try:
            from services.orders.limit_order_service import place_limit_sell_order
            from config.preferences_manager import get_risk_type
            
            # Risk type'ına göre amount ve amount_type belirle
            risk_type = get_risk_type()
            amount = self.get_risk_percentage(self.risk_level)
            
            if risk_type == "USDT":
                # USDT amount olarak kullan
                amount_type = 'usdt'
                self.logger.info(f"Executing {self.risk_level.value} limit sell for {self.symbol} with ${amount:.2f} USDT at ${self.limit_price}")
            else:
                # Percentage olarak kullan
                amount_type = 'percentage'
                self.logger.info(f"Executing {self.risk_level.value} limit sell for {self.symbol} with {amount*100:.1f}% at ${self.limit_price}")
            
            order = place_limit_sell_order(
                symbol=self.symbol, 
                amount_or_percentage=amount, 
                limit_price=self.limit_price, 
                amount_type=amount_type,
                client=self.client, 
                terminal_callback=self.terminal_callback
            )
            
            self.logger.info(f"{self.risk_level.value} limit sell order placed for {self.symbol}")
            return order
            
        except Exception as e:
            error_msg = f"{self.risk_level.value} limit sell order error for {self.symbol}: {e}"
            self.logger.error(error_msg)
            raise


class OrderFactory:
    """Order objelerini oluşturmak için factory class"""
    
    @staticmethod
    def create_order(order_style: str, client, symbol: str, risk_preferences: tuple = None, 
                    order_execution_type: str = "MARKET", limit_price: float = None, terminal_callback=None) -> BaseOrder:
        """
        @brief Order style'a göre uygun order objesi oluşturur
        @param order_style: Order stili ("Hard_Buy", "Hard_Sell", "Soft_Buy", "Soft_Sell")
        @param client: Binance API client
        @param symbol: Trading pair symbol
        @param risk_preferences: Risk tercihleri tuple'ı
        @param order_execution_type: Order execution type ("MARKET" or "LIMIT")
        @param limit_price: Limit order için fiyat (LIMIT order için gerekli)
        @param terminal_callback: Terminal widget'a mesaj göndermek için callback function
        @return BaseOrder türevli order objesi
        """
        # Order execution type kontrolü
        if order_execution_type == "LIMIT" and limit_price is None:
            raise ValueError("Limit order için limit_price parametresi gerekli")
        
        # Order style ve execution type'a göre mapping
        if order_execution_type == "MARKET":
            order_mapping = {
                "Hard_Buy": lambda: MarketBuyOrder(client, symbol, RiskLevel.HARD, risk_preferences),
                "Hard_Sell": lambda: MarketSellOrder(client, symbol, RiskLevel.HARD, risk_preferences),
                "Soft_Buy": lambda: MarketBuyOrder(client, symbol, RiskLevel.SOFT, risk_preferences),
                "Soft_Sell": lambda: MarketSellOrder(client, symbol, RiskLevel.SOFT, risk_preferences)
            }
        elif order_execution_type == "LIMIT":
            order_mapping = {
                "Hard_Buy": lambda: LimitBuyOrder(client, symbol, RiskLevel.HARD, limit_price, risk_preferences, terminal_callback),
                "Hard_Sell": lambda: LimitSellOrder(client, symbol, RiskLevel.HARD, limit_price, risk_preferences, terminal_callback),
                "Soft_Buy": lambda: LimitBuyOrder(client, symbol, RiskLevel.SOFT, limit_price, risk_preferences, terminal_callback),
                "Soft_Sell": lambda: LimitSellOrder(client, symbol, RiskLevel.SOFT, limit_price, risk_preferences, terminal_callback)
            }
        else:
            raise ValueError(f"Geçersiz order execution type: {order_execution_type}. "
                           f"Geçerli değerler: MARKET, LIMIT")
        
        if order_style not in order_mapping:
            raise ValueError(f"Geçersiz order style: {order_style}. "
                           f"Geçerli değerler: {list(order_mapping.keys())}")
        
        # Order objesini oluştur
        order = order_mapping[order_style]()
        
        return order


class OrderManager:
    """Order işlemlerini yöneten manager class"""
    
    def __init__(self, client, risk_preferences: tuple = None, terminal_callback=None):
        """
        @brief OrderManager constructor
        @param client: Binance API client
        @param risk_preferences: Risk tercihleri tuple'ı
        @param terminal_callback: Terminal widget'a mesaj göndermek için callback function
        """
        self.client = client
        self.risk_preferences = risk_preferences
        self.terminal_callback = terminal_callback
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def execute_order(self, order_style: str, symbol: str, order_execution_type: str = "MARKET", limit_price: float = None) -> Dict[str, Any]:
        """
        @brief Order'ı execute eder
        @param order_style: Order stili
        @param symbol: Trading pair symbol
        @param order_execution_type: Order execution type ("MARKET" or "LIMIT")
        @param limit_price: Limit order için fiyat (LIMIT order için gerekli)
        @return Order detayları
        """
        try:
            # Order objesini oluştur
            order = OrderFactory.create_order(
                order_style, 
                self.client, 
                symbol, 
                self.risk_preferences, 
                order_execution_type, 
                limit_price,
                self.terminal_callback
            )
            
            # Symbol validasyonu
            if not order.validate_symbol():
                raise ValueError(f"Invalid trading symbol: {symbol}")
            
            # Order'ı execute et
            result = order.execute()
            
            self.logger.info(f"Order executed successfully: {order_style} {symbol} ({order_execution_type})")
            return result
            
        except Exception as e:
            error_msg = f"Order execution failed: {order_style} {symbol} ({order_execution_type}) - {e}"
            self.logger.error(error_msg)
            raise
    
    def get_available_order_styles(self) -> list:
        """
        @brief Mevcut order stillerini döndürür
        @return Order stilleri listesi
        """
        return ["Hard_Buy", "Hard_Sell", "Soft_Buy", "Soft_Sell"]
    
    def get_available_execution_types(self) -> list:
        """
        @brief Mevcut order execution türlerini döndürür
        @return Order execution türleri listesi
        """
        return ["MARKET", "LIMIT"]
    
    def validate_order_style(self, order_style: str) -> bool:
        """
        @brief Order stilinin geçerli olup olmadığını kontrol eder
        @param order_style: Kontrol edilecek order stili
        @return Geçerli ise True, değilse False
        """
        return order_style in self.get_available_order_styles()
    
    def validate_execution_type(self, execution_type: str) -> bool:
        """
        @brief Order execution türünün geçerli olup olmadığını kontrol eder
        @param execution_type: Kontrol edilecek execution türü
        @return Geçerli ise True, değilse False
        """
        return execution_type in self.get_available_execution_types()
