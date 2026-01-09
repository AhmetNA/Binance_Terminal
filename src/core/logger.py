import logging
import os
from datetime import datetime


def setup_logging(log_level=logging.INFO, log_to_file=True, log_to_console=True):
    """
    Uygulama için logging konfigürasyonunu ayarlar

    Args:
        log_level: Logging seviyesi (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Dosyaya log yazılsın mı
        log_to_console: Konsola log yazılsın mı
    """
    # Log dizinini oluştur
    log_dir = os.path.join(os.path.dirname(__file__), "..", "..", "logs")
    os.makedirs(log_dir, exist_ok=True)

    # Log dosyası adı (tarih ile)
    log_filename = f"binance_terminal_{datetime.now().strftime('%Y%m%d')}.log"
    log_file_path = os.path.join(log_dir, log_filename)

    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Root logger'ı temizle
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    # Handlers listesi
    handlers = []

    # Console handler
    if log_to_console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        handlers.append(console_handler)

    # File handler
    if log_to_file:
        file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)

    # Basic config
    logging.basicConfig(level=log_level, handlers=handlers)

    # İlk log mesajı
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized - Level: {logging.getLevelName(log_level)}")
    logger.info(f"Log file: {log_file_path}")

    return logger


def get_logger(name):
    """
    Belirtilen isimde logger döndürür

    Args:
        name: Logger adı (genellikle __name__ kullanılır)

    Returns:
        logging.Logger: Konfigüre edilmiş logger
    """
    return logging.getLogger(name)


# Uygulama genelinde kullanılacak logger'lar
def get_main_logger():
    """Ana uygulama logger'ı"""
    return get_logger("binance_terminal.main")
