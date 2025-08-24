import aiohttp
import asyncio
from typing import Optional, Dict, Any
import ssl
from core.logger import get_main_logger

class ConnectionPoolManager:
    """HTTP bağlantı havuzu yöneticisi"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.logger = get_main_logger()
        
    async def get_session(self) -> aiohttp.ClientSession:
        """Singleton session döndürür"""
        if self.session is None or self.session.closed:
            await self.create_session()
        return self.session
    
    async def create_session(self):
        """Optimized connection pool ile session oluşturur"""
        # SSL context oluştur
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        # Connection pool ayarları
        connector = aiohttp.TCPConnector(
            limit=100,  # Toplam bağlantı limiti
            limit_per_host=30,  # Host başına bağlantı limiti
            keepalive_timeout=30,  # Keep-alive timeout
            enable_cleanup_closed=True,  # Kapalı bağlantıları temizle
            ssl=ssl_context,
            use_dns_cache=True,  # DNS cache kullan
            ttl_dns_cache=300,  # DNS cache TTL (5 dakika)
        )
        
        # Timeout ayarları
        timeout = aiohttp.ClientTimeout(
            total=30,  # Toplam timeout
            connect=10,  # Bağlantı timeout
            sock_read=10  # Socket read timeout
        )
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'User-Agent': 'Binance-Terminal/1.0',
                'Connection': 'keep-alive'
            }
        )
        
        self.logger.info("HTTP session created with connection pooling")
    
    async def close(self):
        """Session'ı kapat"""
        if self.session and not self.session.closed:
            await self.session.close()
            self.logger.info("HTTP session closed")

# Global instance
_pool_manager = ConnectionPoolManager()

async def get_http_session() -> aiohttp.ClientSession:
    """Global HTTP session döndürür"""
    return await _pool_manager.get_session()

async def close_http_session():
    """Global HTTP session'ı kapat"""
    await _pool_manager.close()
