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
        self.soft_risk, self.hard_risk = risk_preferences or (0.1, 0.2)
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
            from services.order_service import place_BUY_order
            
            percentage = self.get_risk_percentage(self.risk_level)
            self.logger.info(f"Executing {self.risk_level.value} market buy for {self.symbol} with {percentage*100:.1f}%")
            
            order = place_BUY_order(self.client, self.symbol, percentage)
            
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
            from services.order_service import place_SELL_order
            
            percentage = self.get_risk_percentage(self.risk_level)
            self.logger.info(f"Executing {self.risk_level.value} market sell for {self.symbol} with {percentage*100:.1f}%")
            
            order = place_SELL_order(self.client, self.symbol, percentage)
            
            self.logger.info(f"{self.risk_level.value} sell order completed for {self.symbol}")
            return order
            
        except Exception as e:
            error_msg = f"{self.risk_level.value} sell order error for {self.symbol}: {e}"
            self.logger.error(error_msg)
            raise


class OrderFactory:
    """Order objelerini oluşturmak için factory class"""
    
    @staticmethod
    def create_order(order_style: str, client, symbol: str, risk_preferences: tuple = None) -> BaseOrder:
        """
        @brief Order style'a göre uygun order objesi oluşturur
        @param order_style: Order stili ("Hard_Buy", "Hard_Sell", "Soft_Buy", "Soft_Sell")
        @param client: Binance API client
        @param symbol: Trading pair symbol
        @param risk_preferences: Risk tercihleri tuple'ı
        @return BaseOrder türevli order objesi
        """
        order_mapping = {
            "Hard_Buy": lambda: MarketBuyOrder(client, symbol, RiskLevel.HARD, risk_preferences),
            "Hard_Sell": lambda: MarketSellOrder(client, symbol, RiskLevel.HARD, risk_preferences),
            "Soft_Buy": lambda: MarketBuyOrder(client, symbol, RiskLevel.SOFT, risk_preferences),
            "Soft_Sell": lambda: MarketSellOrder(client, symbol, RiskLevel.SOFT, risk_preferences)
        }
        
        if order_style not in order_mapping:
            raise ValueError(f"Geçersiz order style: {order_style}. "
                           f"Geçerli değerler: {list(order_mapping.keys())}")
        
        return order_mapping[order_style]()


class OrderManager:
    """Order işlemlerini yöneten manager class"""
    
    def __init__(self, client, risk_preferences: tuple = None):
        """
        @brief OrderManager constructor
        @param client: Binance API client
        @param risk_preferences: Risk tercihleri tuple'ı
        """
        self.client = client
        self.risk_preferences = risk_preferences
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def execute_order(self, order_style: str, symbol: str) -> Dict[str, Any]:
        """
        @brief Order'ı execute eder
        @param order_style: Order stili
        @param symbol: Trading pair symbol
        @return Order detayları
        """
        try:
            # Order objesini oluştur
            order = OrderFactory.create_order(order_style, self.client, symbol, self.risk_preferences)
            
            # Symbol validasyonu
            if not order.validate_symbol():
                raise ValueError(f"Invalid trading symbol: {symbol}")
            
            # Order'ı execute et
            result = order.execute()
            
            self.logger.info(f"Order executed successfully: {order_style} {symbol}")
            return result
            
        except Exception as e:
            error_msg = f"Order execution failed: {order_style} {symbol} - {e}"
            self.logger.error(error_msg)
            raise
    
    def get_available_order_styles(self) -> list:
        """
        @brief Mevcut order stillerini döndürür
        @return Order stilleri listesi
        """
        return ["Hard_Buy", "Hard_Sell", "Soft_Buy", "Soft_Sell"]
    
    def validate_order_style(self, order_style: str) -> bool:
        """
        @brief Order stilinin geçerli olup olmadığını kontrol eder
        @param order_style: Kontrol edilecek order stili
        @return Geçerli ise True, değilse False
        """
        return order_style in self.get_available_order_styles()
