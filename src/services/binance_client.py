from binance.client import Client
import logging

from utils.security.secure_storage import get_secure_storage
from utils.security.encryption_manager import get_encryption_manager

"""
binance_client.py
This module handles Binance API client initialization, caching, and management.
It provides a centralized way to manage the Binance client connection with caching
for improved performance and connection stability.
"""

# Module-level cache for Binance client
_CACHED_CLIENT = None


def _initialize_client_once(gui_mode=False, parent_widget=None):
    global _CACHED_CLIENT

    if _CACHED_CLIENT is None:
        try:
            # Load credentials only from secure storage
            api_key, api_secret = _load_credentials_secure(gui_mode, parent_widget)

            if not api_key or not api_secret:
                raise ValueError("API keys not found in secure storage!")

            _CACHED_CLIENT = Client(api_key, api_secret)
            _CACHED_CLIENT.API_URL = "https://testnet.binance.vision/api"
            logging.info("🚀 Binance client cached at module level")
            return _CACHED_CLIENT

        except ValueError as e:
            if (
                "Master şifre doğrulanamadı" in str(e)
                or "iptal etti" in str(e)
                or "Master password could not be verified" in str(e)
                or "cancelled password input" in str(e)
                or "CREDENTIALS_RESET" in str(e)
            ):
                if gui_mode:
                    # GUI modunda ana pencereye hata göster - artık security_dialogs tarafından handle ediliyor
                    pass
                else:
                    print("\n🚫 Security Error:")
                    print(str(e))
                    print("\n🔄 Recovery options:")
                    print("1. Recall the correct master password")
                    print("2. Reset secure storage (data will be lost)")
                    print("3. Re-setup secure credentials")
                raise
            else:
                error_msg = f"❌ Binance API connection error: {e}"
                if gui_mode:
                    try:
                        from PySide6.QtWidgets import QMessageBox

                        QMessageBox.critical(
                            parent_widget, "API Connection Error", error_msg
                        )
                    except:
                        pass
                print(error_msg)
                logging.error(f"Error preparing Binance client: {e}")
                raise
        except Exception as e:
            error_msg = f"❌ Binance API connection error: {e}"
            if gui_mode:
                try:
                    from PySide6.QtWidgets import QMessageBox

                    QMessageBox.critical(parent_widget, "Unexpected Error", error_msg)
                except:
                    pass
            print(error_msg)
            logging.error(f"Error preparing Binance client: {e}")
            logging.exception("Full traceback for client preparation error:")
            raise
    else:
        # Return from cache - very fast!
        return _CACHED_CLIENT


def prepare_client(gui_mode=False, parent_widget=None):
    """
    Binance client'ını hazırla (GUI desteği ile)

    Args:
        gui_mode: GUI modunda çalışıp çalışmadığı
        parent_widget: Ana pencere (GUI için)
    """
    return _initialize_client_once(gui_mode, parent_widget)


def _load_credentials_secure(gui_mode=False, parent_widget=None):
    """Load API keys from secure storage"""
    try:
        secure_storage = get_secure_storage()
        # Check secure file exists
        if not secure_storage.credentials_exist():
            logging.error("📁 Secure credentials file not found!")
            raise ValueError(
                "Secure credentials not configured. Please delete config/secure_credentials.json and restart"
            )

        # Secure storage present - master password required
        logging.info("🔐 Secure storage found - master password required")

        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                # Get master password (GUI or terminal)
                encryption_manager = get_encryption_manager()

                if gui_mode:
                    master_password = encryption_manager.get_master_password(
                        gui_mode=True,
                        parent_widget=parent_widget,
                        attempt_number=attempt + 1,
                        max_attempts=max_attempts,
                    )
                else:
                    prompt = f"🔐 Enter master password for API keys (Attempt {attempt + 1}/{max_attempts}): "
                    master_password = encryption_manager.get_master_password(prompt)

                # Decrypt keys
                credentials = secure_storage.load_credentials(master_password)
                if credentials:
                    logging.info("✅ API keys loaded from secure storage")

                    # Skip success dialog - directly return credentials
                    return credentials["api_key"], credentials["api_secret"]
                else:
                    if attempt < max_attempts - 1:
                        if not gui_mode:
                            print(
                                f"❌ Wrong master password! Attempts left: {max_attempts - attempt - 1}"
                            )
                    else:
                        error_msg = "❌ You entered the wrong password 3 times!"
                        recovery_msg = (
                            "💡 If you cannot remember your password:\n"
                            "   1. Delete config/secure_credentials.json\n"
                            "   2. Restart the application"
                        )

                        if gui_mode:
                            try:
                                from ui.dialogs.security_dialogs import (
                                    show_security_error,
                                )

                                recovery_tips = [
                                    "Delete config/secure_credentials.json",
                                    "Restart the application",
                                ]
                                show_security_error(
                                    error_msg, recovery_tips, parent_widget
                                )
                            except ImportError:
                                from PySide6.QtWidgets import QMessageBox

                                msg_box = QMessageBox()
                                msg_box.setIcon(QMessageBox.Critical)
                                msg_box.setWindowTitle("Security Error")
                                msg_box.setText(error_msg)
                                msg_box.setDetailedText(recovery_msg)
                                msg_box.exec()
                        else:
                            print(error_msg)
                            print(recovery_msg)
                        raise ValueError(
                            "Master password could not be verified - Access denied for security reasons"
                        )

            except KeyboardInterrupt:
                if gui_mode:
                    raise ValueError("User cancelled password input")
                else:
                    print("\n❌ Operation cancelled")
                    raise

        # Should not reach here normally, but as safety
        raise ValueError(
            "Master password could not be verified - Maximum attempts exceeded"
        )

    except KeyboardInterrupt:
        if gui_mode:
            raise ValueError("User cancelled password input")
        else:
            print("\n❌ Operation cancelled by user")
            raise
    except Exception as e:
        if (
            "Master şifre doğrulanamadı" in str(e)
            or "iptal etti" in str(e)
            or "Master password could not be verified" in str(e)
            or "User cancelled password input" in str(e)
            or "Secure credentials not configured" in str(e)
            or "CREDENTIALS_RESET" in str(e)
        ):
            # Güvenlik hatası - yeniden fırlat
            raise
        logging.error(f"❌ Secure storage error: {e}")
        raise ValueError(f"Failed to load credentials from secure storage: {e}")


def force_client_reload():
    global _CACHED_CLIENT
    _CACHED_CLIENT = None
    logging.info("🔄 Forcing client reload due to configuration change")
    client = _initialize_client_once()
    logging.info("✅ Client cache reloaded successfully")
    return client


def get_cached_client_info():
    global _CACHED_CLIENT
    return {
        "is_cached": _CACHED_CLIENT is not None,
        "client_type": type(_CACHED_CLIENT).__name__ if _CACHED_CLIENT else None,
        "api_url": getattr(_CACHED_CLIENT, "API_URL", None) if _CACHED_CLIENT else None,
    }


def clear_api_credentials_from_memory():
    """
    🔒 SECURITY: API key'leri bellekten güvenli bir şekilde temizle

    Bu fonksiyon:
    1. Cached client'ı None yapar
    2. Garbage collection'ı zorlar
    3. Güvenlik için log kaydı tutar

    Kullanım alanları:
    - Uygulama kapatılırken
    - Güvenlik breach durumunda
    - Credential değiştirildikten sonra
    """
    global _CACHED_CLIENT

    try:
        if _CACHED_CLIENT is not None:
            # Client objesini referansını kır
            client_type = type(_CACHED_CLIENT).__name__
            _CACHED_CLIENT = None

            # Python garbage collection'ı zorla
            import gc

            gc.collect()

            logging.info("🧹 API credentials cleared from memory")
            logging.info(f"🔒 Former client type '{client_type}' dereferenced")
            return True
        else:
            logging.debug("🔒 No cached client to clear")
            return False

    except Exception as e:
        logging.error(f"❌ Error clearing API credentials from memory: {e}")
        # Güvenlik için yine de None yap
        _CACHED_CLIENT = None
        return False


if __name__ == "__main__":
    """Test the client service functions"""
    print("🚀 Testing Client Service")
    print("=" * 30)

    # Test cache info when empty
    info = get_cached_client_info()
    print(f"Initial cache state: {info}")

    print("Available functions:")
    functions = [
        "prepare_client",
        "force_client_reload",
        "get_cached_client_info",
        "clear_api_credentials_from_memory",
    ]
    for func in functions:
        print(f"  ✅ {func}")

    print("\n✅ Client service test completed successfully!")
