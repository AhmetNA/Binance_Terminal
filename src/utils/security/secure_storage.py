"""
secure_storage.py
Bu modül API anahtarlarını güvenli bir şekilde şifreleyerek saklamak ve
gerektiğinde çözmek için kullanılır.
"""

import os
import json
import logging
from typing import Optional, Dict, Any

from core.paths import SETTINGS_DIR
from utils.security.encryption_manager import get_encryption_manager


class SecureStorage:
    """API anahtarlarını güvenli bir şekilde saklama ve yönetme sınıfı"""

    def __init__(self, storage_file: str = "secure_credentials.json"):
        """
        Args:
            storage_file: Şifrelenmiş verilerin saklanacağı dosya adı
        """
        self.storage_file = os.path.join(SETTINGS_DIR, storage_file)
        self.encryption_manager = get_encryption_manager()
        self._ensure_storage_dir()

    def _ensure_storage_dir(self):
        """Depolama dizininin var olduğundan emin ol"""
        os.makedirs(os.path.dirname(self.storage_file), exist_ok=True)

    def store_credentials(
        self, api_key: str, api_secret: str, master_password: str
    ) -> bool:
        """
        API anahtarlarını şifrele ve sakla

        Args:
            api_key: Binance API anahtarı
            api_secret: Binance API secret
            master_password: Şifreleme için kullanılacak master şifre

        Returns:
            Başarılıysa True
        """
        try:
            # API anahtarlarını şifrele
            encrypted_api_key = self.encryption_manager.encrypt_data(
                api_key, master_password
            )
            encrypted_api_secret = self.encryption_manager.encrypt_data(
                api_secret, master_password
            )

            # Test verisi oluştur (şifre doğrulaması için)
            test_data = "binance_terminal_auth_test"
            encrypted_test = self.encryption_manager.encrypt_data(
                test_data, master_password
            )

            # Şifrelenmiş verileri hazırla
            secure_data = {
                "encrypted_api_key": encrypted_api_key,
                "encrypted_api_secret": encrypted_api_secret,
                "encrypted_test": encrypted_test,
                "test_data": test_data,
                "version": "1.0",
                "created_at": str(
                    os.path.getctime(self.storage_file)
                    if os.path.exists(self.storage_file)
                    else "new"
                ),
            }

            # Dosyaya kaydet
            with open(self.storage_file, "w", encoding="utf-8") as f:
                json.dump(secure_data, f, indent=2)

            # Dosya izinlerini sınırla (sadece owner okuyabilir)
            os.chmod(self.storage_file, 0o600)

            logging.info(f"✅ API credentials stored securely: {self.storage_file}")
            return True

        except Exception as e:
            logging.error(f"❌ Error storing credentials: {e}")
            return False

    def load_credentials(self, master_password: str) -> Optional[Dict[str, str]]:
        """
        Şifrelenmiş API anahtarlarını çöz ve döndür

        Args:
            master_password: Çözme için kullanılacak master şifre

        Returns:
            API anahtarları dict'i veya None (hata durumunda)
        """
        try:
            # Check if file exists
            if not os.path.exists(self.storage_file):
                logging.warning("❌ Secure credential file not found")
                return None

            # Şifrelenmiş verileri oku
            with open(self.storage_file, "r", encoding="utf-8") as f:
                secure_data = json.load(f)

            # Verify password
            logging.debug("Verifying master password for secure storage file: %s", self.storage_file)
            if not self._verify_password(secure_data, master_password):
                logging.error("❌ Incorrect master password!")
                return None

            # API anahtarlarını çöz
            api_key = self.encryption_manager.decrypt_data(
                secure_data["encrypted_api_key"], master_password
            )
            api_secret = self.encryption_manager.decrypt_data(
                secure_data["encrypted_api_secret"], master_password
            )

            logging.info("✅ API credentials decrypted successfully")
            return {"api_key": api_key, "api_secret": api_secret}

        except Exception as e:
            logging.error(f"❌ Error loading credentials: {e}")
            return None

    def _verify_password(
        self, secure_data: Dict[str, Any], master_password: str
    ) -> bool:
        """
        Master şifrenin doğru olup olmadığını test et

        Args:
            secure_data: Güvenli veri dict'i
            master_password: Test edilecek şifre

        Returns:
            Şifre doğruysa True
        """
        try:
            return self.encryption_manager.verify_password(
                secure_data["test_data"], secure_data["encrypted_test"], master_password
            )
        except Exception:
            return False

    def credentials_exist(self) -> bool:
        """Check if secure credential file exists and contains valid data"""
        try:
            # Check if file exists and has content
            if (
                not os.path.exists(self.storage_file)
                or os.path.getsize(self.storage_file) == 0
            ):
                logging.debug("Secure credentials file does not exist or is empty")
                return False

            # Try to read and validate the JSON structure
            with open(self.storage_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Check required fields
            required_fields = [
                "encrypted_api_key",
                "encrypted_api_secret",
                "encrypted_test",
                "test_data",
            ]
            for field in required_fields:
                if field not in data or not data[field]:
                    logging.warning(
                        f"Secure credentials file missing required field: {field}"
                    )
                    return False

            # Basic validation of encrypted data format
            for encrypted_field in [
                "encrypted_api_key",
                "encrypted_api_secret",
                "encrypted_test",
            ]:
                encrypted_data = data[encrypted_field]
                if not isinstance(encrypted_data, str) or len(encrypted_data) < 50:
                    logging.warning(
                        f"Invalid encrypted data format in field: {encrypted_field}"
                    )
                    return False

            logging.debug("Secure credentials file validation passed")
            return True

        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logging.warning(f"Secure credentials file is corrupted: {e}")
            return False
        except Exception as e:
            logging.error(f"Error validating secure credentials file: {e}")
            return False

    def delete_credentials(self) -> bool:
        """Delete secure credential file"""
        try:
            if os.path.exists(self.storage_file):
                os.remove(self.storage_file)
                logging.info("✅ Secure credential file deleted")
                return True
            return False
        except Exception as e:
            logging.error(f"❌ Error deleting credential file: {e}")
            return False

    def change_master_password(self, old_password: str, new_password: str) -> bool:
        """
        Master şifreyi değiştir

        Args:
            old_password: Eski master şifre
            new_password: Yeni master şifre

        Returns:
            Başarılıysa True
        """
        try:
            # First read with old password
            credentials = self.load_credentials(old_password)
            if not credentials:
                logging.error("❌ Incorrect old password!")
                return False

            # Save again with new password
            return self.store_credentials(
                credentials["api_key"], credentials["api_secret"], new_password
            )

        except Exception as e:
            logging.error(f"❌ Error changing master password: {e}")
            return False


# Modül seviyesinde singleton instance
_secure_storage = None


def get_secure_storage() -> SecureStorage:
    """Secure storage singleton instance'ını döndür"""
    global _secure_storage
    if _secure_storage is None:
        _secure_storage = SecureStorage()
    return _secure_storage


if __name__ == "__main__":
    """Test secure storage"""
    print("🔒 Testing Secure Storage")
    print("=" * 40)

    storage = get_secure_storage()

    # Test data
    test_api_key = "test_api_key_12345"
    test_api_secret = "test_api_secret_67890"
    test_password = "my_secure_master_password"

    try:
        print("📤 Saving API keys...")
        success = storage.store_credentials(
            test_api_key, test_api_secret, test_password
        )
        print(f"✅ Save: {'Success' if success else 'Failed'}")

        print("📥 Loading API keys...")
        credentials = storage.load_credentials(test_password)
        if credentials:
            print(f"✅ API Key: {credentials['api_key']}")
            print(f"✅ API Secret: {credentials['api_secret'][:10]}...")

            # Validation
            key_match = credentials["api_key"] == test_api_key
            secret_match = credentials["api_secret"] == test_api_secret
            print(
                f"🔍 Validation: {'✅ Success' if key_match and secret_match else '❌ Failed'}"
            )
        else:
            print("❌ Load failed!")

        # Wrong password test
        print("🔍 Wrong password test...")
        wrong_credentials = storage.load_credentials("wrong_password")
        print(
            f"✅ Wrong password test: {'Success' if wrong_credentials is None else 'Failed'}"
        )

        # File exists check
        print(f"📁 Credential file exists: {storage.credentials_exist()}")

        # Cleanup
        print("🗑️ Cleaning up test file...")
        storage.delete_credentials()
        print(
            f"✅ Cleanup: {'Success' if not storage.credentials_exist() else 'Failed'}"
        )

    except Exception as e:
        print(f"❌ Test error: {e}")

    print("\n✅ Secure storage test completed!")
