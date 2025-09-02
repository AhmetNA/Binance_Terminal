import aiohttp
import asyncio
from typing import Optional, Dict, Any
import ssl
import weakref
import atexit
from core.logger import get_main_logger

class ConnectionPoolManager:
    """HTTP bağlantı havuzu yöneticisi"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.logger = get_main_logger()
        # Cleanup için atexit handler ekle
        atexit.register(self._cleanup_on_exit)
        
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
            limit=30,  # Daha düşük limit
            limit_per_host=10,  # Host başına daha düşük limit
            keepalive_timeout=20,  # Daha kısa keep-alive
            enable_cleanup_closed=True,  # Kapalı bağlantıları temizle
            ssl=ssl_context,
            use_dns_cache=True,  # DNS cache kullan
            ttl_dns_cache=300,  # DNS cache TTL (5 dakika)
            force_close=True,  # Bağlantıları zorla kapat
        )
        
        # Timeout ayarları
        timeout = aiohttp.ClientTimeout(
            total=15,  # Daha kısa timeout
            connect=5,  # Daha kısa bağlantı timeout
            sock_read=10  # Socket read timeout
        )
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'User-Agent': 'Binance-Terminal/1.0',
                'Connection': 'close'  # Keep-alive yerine close kullan
            }
        )
        
        self.logger.info("HTTP session created with connection pooling")
    
    async def close(self):
        """Session'ı güvenli şekilde kapat"""
        if self.session and not self.session.closed:
            try:
                # Önce tüm pending request'leri bekle
                await asyncio.sleep(0.1)  # Kısa bekleme
                await self.session.close()
                # Connector'ın kapanmasını bekle
                await asyncio.sleep(0.25)
                self.logger.info("HTTP session closed successfully")
            except Exception as e:
                self.logger.error(f"Error closing HTTP session: {e}")
            finally:
                self.session = None
    
    def _cleanup_on_exit(self):
        """Program çıkışında cleanup"""
        if self.session and not self.session.closed:
            try:
                # Sync cleanup - event loop kapalı olabilir
                import warnings
                warnings.filterwarnings("ignore")
                self.session._connector.close()
            except:
                pass

# Global instance
_pool_manager = ConnectionPoolManager()

async def get_http_session() -> aiohttp.ClientSession:
    """Global HTTP session döndürür"""
    return await _pool_manager.get_session()

async def close_http_session():
    """Global HTTP session'ı kapat"""
    await _pool_manager.close()

def close_http_session_sync():
    """Sync olarak HTTP session'ı kapat"""
    try:
        loop = asyncio.get_event_loop()
        if not loop.is_closed():
            loop.run_until_complete(_pool_manager.close())
    except:
        # Event loop yoksa veya kapalıysa manuel cleanup
        if _pool_manager.session:
            _pool_manager._cleanup_on_exit()

# Requests-style synchronous wrapper for backwards compatibility
def get_session_sync():
    """Sync context için basit session döndür"""
    import requests
    return requests.Session()
