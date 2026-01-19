"""
encryption_manager.py
Bu modül API anahtarlarını güvenli bir şekilde şifrelemek ve çözmek için gerekli
fonksiyonları sağlar. Fernet (AES 128) şifreleme kullanır.
"""

import os
import base64
import getpass
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import logging


class EncryptionManager:
    """API anahtarlarını şifrelemek ve çözmek için güvenlik yöneticisi"""

    def __init__(self):
        self.salt_length = 32  # Salt uzunluğu

    def _generate_key_from_password(self, password: str, salt: bytes) -> bytes:
        """Şifreden şifreleme anahtarı oluştur"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,  # Yüksek iterasyon sayısı güvenlik için
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key

    def encrypt_data(self, data: str, password: str) -> str:
        """
        Veriyi şifrele

        Args:
            data: Şifrelenecek veri (API anahtarı)
            password: Şifreleme için kullanılacak master şifre

        Returns:
            Base64 encoded şifrelenmiş veri (salt + encrypted_data)
        """
        try:
            # Rastgele salt oluştur
            salt = os.urandom(self.salt_length)

            # Şifreden anahtar türet
            key = self._generate_key_from_password(password, salt)

            # Fernet şifreleme objesi oluştur
            fernet = Fernet(key)

            # Veriyi şifrele
            encrypted_data = fernet.encrypt(data.encode())

            # Salt + şifrelenmiş veriyi birleştir ve base64 encode et
            combined = salt + encrypted_data
            encoded = base64.b64encode(combined).decode()

            logging.debug("Data encrypted successfully (encrypted %d bytes)", len(encrypted_data))
            return encoded

        except Exception as e:
            logging.error(f"❌ Encryption error: {e}")
            raise

    def decrypt_data(self, encrypted_data: str, password: str) -> str:
        """
        Şifrelenmiş veriyi çöz

        Args:
            encrypted_data: Base64 encoded şifrelenmiş veri
            password: Çözme için kullanılacak master şifre

        Returns:
            Çözülmüş orijinal veri
        """
        try:
            # Base64 decode et
            combined = base64.b64decode(encrypted_data.encode())

            # Salt'ı ayır
            salt = combined[: self.salt_length]
            encrypted_content = combined[self.salt_length :]

            # Şifreden anahtar türet
            key = self._generate_key_from_password(password, salt)

            # Fernet şifreleme objesi oluştur
            fernet = Fernet(key)

            # Decrypt data
            decrypted_data = fernet.decrypt(encrypted_content)

            logging.debug("Data decrypted successfully (decrypted %d bytes)", len(decrypted_data))
            return decrypted_data.decode()

        except Exception:
            logging.exception("❌ Decryption error while decrypting data")
            raise

    def get_master_password(
        self,
        prompt: str = "Enter master password: ",
        gui_mode: bool = False,
        parent_widget=None,
        attempt_number: int = 1,
        max_attempts: int = 3,
    ) -> str:
        """
        Kullanıcıdan master şifreyi güvenli bir şekilde al

        Args:
            prompt: Kullanıcıya gösterilecek mesaj (terminal için)
            gui_mode: GUI modunda çalışıp çalışmadığı
            parent_widget: Ana pencere (GUI için)
            attempt_number: Hangi deneme olduğu
            max_attempts: Maksimum deneme sayısı

        Returns:
            Kullanıcının girdiği şifre
        """
        try:
            if gui_mode:
                # GUI modu - dialog kullan
                try:
                    from ui.dialogs.master_password_dialog import (
                        show_master_password_dialog,
                    )

                    password, accepted = show_master_password_dialog(
                        parent_widget, attempt_number, max_attempts
                    )

                    if not accepted:
                        raise KeyboardInterrupt("User cancelled password input")

                    if not password:
                        raise ValueError("Password cannot be empty!")

                    return password

                except ImportError:
                    # GUI import edilemezse terminal moduna geç
                    logging.warning(
                        "GUI dialog import failed, falling back to terminal mode"
                    )
                    gui_mode = False

            if not gui_mode:
                # Terminal modu - getpass kullan
                if attempt_number > 1:
                    prompt = f"🔐 Master password (Attempt {attempt_number}/{max_attempts}): "

                password = getpass.getpass(prompt)
                if not password:
                    raise ValueError("Password cannot be empty!")
                return password

        except KeyboardInterrupt:
            print("\n❌ Operation cancelled")
            raise

    def verify_password(
        self, test_data: str, encrypted_test: str, password: str
    ) -> bool:
        """
        Şifrenin doğru olup olmadığını test et

        Args:
            test_data: Test için kullanılacak orijinal veri
            encrypted_test: Şifrelenmiş test verisi
            password: Test edilecek şifre

        Returns:
            Şifre doğruysa True, değilse False
        """
        try:
            decrypted = self.decrypt_data(encrypted_test, password)
            return decrypted == test_data
        except Exception:
            return False


# Modül seviyesinde singleton instance
_encryption_manager = None


def get_encryption_manager() -> EncryptionManager:
    """Encryption manager singleton instance'ını döndür"""
    global _encryption_manager
    if _encryption_manager is None:
        _encryption_manager = EncryptionManager()
    return _encryption_manager


if __name__ == "__main__":
    """Test encryption manager"""
    print("🔐 Testing Encryption Manager")
    print("=" * 40)

    manager = get_encryption_manager()

    # Test verisi
    test_api_key = "test_api_key_12345"
    test_password = "my_secure_password"

    try:
        # Şifrele
        print("📤 Şifreleniyor...")
        encrypted = manager.encrypt_data(test_api_key, test_password)
        print(f"✅ Şifrelenmiş: {encrypted[:50]}...")

        # Çöz
        print("📥 Çözülüyor...")
        decrypted = manager.decrypt_data(encrypted, test_password)
        print(f"✅ Çözülmüş: {decrypted}")

        # Doğrulama
        is_same = decrypted == test_api_key
        print(f"🔍 Doğrulama: {'✅ Başarılı' if is_same else '❌ Başarısız'}")

        # Yanlış şifre testi
        try:
            manager.decrypt_data(encrypted, "wrong_password")
            print("❌ Yanlış şifre testi başarısız!")
        except Exception:
            print("✅ Yanlış şifre testi başarılı!")

    except Exception as e:
        print(f"❌ Test hatası: {e}")

    print("\n✅ Encryption manager test tamamlandı!")
