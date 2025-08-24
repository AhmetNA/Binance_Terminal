import aiohttp
import asyncio
from typing import Dict, Any, Optional
import json
import hmac
import hashlib
import time
from urllib.parse import urlencode

from .http_client import get_http_session
from core.logger import get_main_logger

class BinanceAPIClient:
    """Binance API client with connection pooling"""
    
    def __init__(self, api_key: str = "", api_secret: str = ""):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://api.binance.com"
        self.logger = get_main_logger()
    
    def _generate_signature(self, query_string: str) -> str:
        """API signature oluştur"""
        return hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict] = None,
        signed: bool = False
    ) -> Dict[Any, Any]:
        """HTTP request yap - connection pool kullanır"""
        session = await get_http_session()
        
        if params is None:
            params = {}
        
        # Signed request için signature ekle
        if signed:
            params['timestamp'] = int(time.time() * 1000)
            query_string = urlencode(params)
            params['signature'] = self._generate_signature(query_string)
        
        # Headers
        headers = {}
        if self.api_key:
            headers['X-MBX-APIKEY'] = self.api_key
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with session.request(
                method=method,
                url=url,
                params=params,
                headers=headers
            ) as response:
                
                self.logger.debug(f"API Request: {method} {url}")
                
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    self.logger.error(f"API Error {response.status}: {error_text}")
                    raise Exception(f"API Error {response.status}: {error_text}")
                    
        except aiohttp.ClientError as e:
            self.logger.error(f"HTTP Client Error: {e}")
            raise
        except asyncio.TimeoutError:
            self.logger.error("Request timeout")
            raise
    
    async def get_ticker_price(self, symbol: str) -> Dict[Any, Any]:
        """Ticker price al"""
        return await self._make_request(
            "GET", 
            "/api/v3/ticker/price", 
            {"symbol": symbol}
        )
    
    async def get_account_info(self) -> Dict[Any, Any]:
        """Account bilgilerini al"""
        return await self._make_request(
            "GET", 
            "/api/v3/account",
            signed=True
        )
    
    async def get_klines(
        self, 
        symbol: str, 
        interval: str, 
        limit: int = 500
    ) -> Dict[Any, Any]:
        """Kline data al"""
        return await self._make_request(
            "GET",
            "/api/v3/klines",
            {
                "symbol": symbol,
                "interval": interval,
                "limit": limit
            }
        )
    
    async def get_order_book(self, symbol: str, limit: int = 100) -> Dict[Any, Any]:
        """Order book al"""
        return await self._make_request(
            "GET",
            "/api/v3/depth",
            {
                "symbol": symbol,
                "limit": limit
            }
        )
    
    async def get_24hr_ticker(self, symbol: str = "") -> Dict[Any, Any]:
        """24hr ticker stats"""
        params = {}
        if symbol:
            params["symbol"] = symbol
        return await self._make_request(
            "GET",
            "/api/v3/ticker/24hr",
            params
        )
    
    async def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None,
        time_in_force: str = "GTC"
    ) -> Dict[Any, Any]:
        """Order yerleştir"""
        params = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": quantity,
            "timeInForce": time_in_force
        }
        
        if price is not None:
            params["price"] = price
        
        return await self._make_request(
            "POST",
            "/api/v3/order",
            params,
            signed=True
        )
