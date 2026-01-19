"""
master_password_dialog.py
Modern, stylish master password entry dialog (English localized)
"""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFrame,
    QApplication,
    QMessageBox,
    QGraphicsDropShadowEffect,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor
import sys


class ModernPasswordInput(QLineEdit):
    """Modern password input widget"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEchoMode(QLineEdit.Password)
        self.setPlaceholderText("Enter your master password...")
        self.setup_style()

    def setup_style(self):
        """Modern input style"""
        self.setStyleSheet("""
            QLineEdit {
                border: none;
                border-bottom: 2px solid #E0E0E0;
                padding: 12px 8px;
                font-size: 16px;
                font-weight: 500;
                background: transparent;
                color: #2C3E50;
                selection-background-color: #3498DB;
            }
            QLineEdit:focus {
                border-bottom: 2px solid #3498DB;
                background: rgba(52, 152, 219, 0.05);
            }
            QLineEdit:hover {
                border-bottom: 2px solid #5DADE2;
            }
        """)


class ModernButton(QPushButton):
    """Modern button widget"""

    def __init__(self, text, button_type="primary", parent=None):
        super().__init__(text, parent)
        self.button_type = button_type
        self.setup_style()

    def setup_style(self):
        """Modern button style"""
        if self.button_type == "primary":
            self.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #3498DB, stop:1 #2980B9);
                    border: none;
                    border-radius: 12px;
                    color: white;
                    font-size: 14px;
                    font-weight: bold;
                    padding: 14px 32px;
                    min-width: 120px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #5DADE2, stop:1 #3498DB);
                }
                QPushButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #2980B9, stop:1 #1F618D);
                }
            """)
        else:  # secondary
            self.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: 2px solid #BDC3C7;
                    border-radius: 12px;
                    color: #7F8C8D;
                    font-size: 14px;
                    font-weight: bold;
                    padding: 14px 32px;
                    min-width: 120px;
                }
                QPushButton:hover {
                    border-color: #95A5A6;
                    color: #5D6D7E;
                    background: rgba(189, 195, 199, 0.1);
                }
                QPushButton:pressed {
                    background: rgba(189, 195, 199, 0.2);
                }
            """)


class MasterPasswordDialog(QDialog):
    """Modern master password dialog"""

    password_provided = Signal(str)

    def __init__(self, parent=None, attempt_number=1, max_attempts=3):
        super().__init__(parent)
        self.attempt_number = attempt_number
        self.max_attempts = max_attempts
        self.password = None
        self.setup_ui()
        self.center_on_screen()  # Center on screen
        self.setup_connections()
        self.setup_animations()

    def setup_ui(self):
        """Build modern UI"""
        self.setWindowTitle("🔐 Secure Login")
        self.setModal(True)
        # Allow dynamic resize: fixed width, adaptive height
        self.setMinimumWidth(440)
        self.resize(440, 340)

        # Ana widget ve layout
        main_widget = QFrame()
        main_widget.setObjectName("mainWidget")
        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Header section
        header_frame = self.create_header()
        main_layout.addWidget(header_frame)

        # Content section
        content_frame = self.create_content()
        main_layout.addWidget(content_frame)

        # Footer section
        footer_frame = self.create_footer()
        main_layout.addWidget(footer_frame)

        # Ana layout'u set et
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(main_widget)
        self.setLayout(layout)

        # Style sheet
        self.setStyleSheet("""
            QDialog {
                background: #10141b;
                border-radius: 16px;
                color: #E6E9F0;
            }
            QFrame#mainWidget {
                background: #10141b;
                border-radius: 16px;
                border: 1px solid #1f2a38;
            }
            QFrame#headerFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0d2a55, stop:1 #112d62);
                border-radius: 16px 16px 0 0;
                min-height: 105px;
            }
            QFrame#contentFrame {
                background: #141b24;
            }
            QFrame#footerFrame {
                background: #141b24;
                border-radius: 0 0 16px 16px;
                border-top: 1px solid #1f2a38;
                min-height: 72px;
            }
        """)

        # Gölge efekti
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(10)
        shadow.setColor(QColor(0, 0, 0, 60))
        self.setGraphicsEffect(shadow)

    def create_header(self):
        """Create header section"""
        header_frame = QFrame()
        header_frame.setObjectName("headerFrame")
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(24, 16, 24, 16)

        # Icon
        icon_label = QLabel("🔐")
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("""
            QLabel {
                font-size: 32px;
                color: white;
                background: transparent;
            }
        """)
        header_layout.addWidget(icon_label)

        # Title
        title_label = QLabel("Secure Login")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                background: transparent;
                margin-top: 5px;
                letter-spacing: 0.5px;
            }
        """)
        header_layout.addWidget(title_label)

        return header_frame

    def create_content(self):
        """Create content section"""
        content_frame = QFrame()
        content_frame.setObjectName("contentFrame")
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(24, 20, 24, 16)
        content_layout.setSpacing(14)

        # Status message
        if self.attempt_number == 1:
            status_text = "Enter your master password\nto decrypt your API keys"
            status_color = "#7F8C8D"
        else:
            remaining = self.max_attempts - self.attempt_number + 1
            status_text = f"❌ Wrong password!\nAttempts left: {remaining}"
            status_color = "#E74C3C"

        status_label = QLabel(status_text)
        status_label.setAlignment(Qt.AlignCenter)
        status_label.setWordWrap(True)
        status_label.setFont(QFont("Segoe UI", 11))
        status_label.setStyleSheet(f"""
            QLabel {{
                color: {status_color};
                background: transparent;
                padding: 4px 6px;
            }}
        """)
        content_layout.addWidget(status_label)

        # Password input
        input_container = QFrame()
        input_layout = QVBoxLayout(input_container)
        input_layout.setContentsMargins(0, 6, 0, 0)
        input_layout.setSpacing(6)

        input_label = QLabel("Master Password")
        input_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        input_label.setStyleSheet(
            "color: #AAB4C2; background: transparent; text-transform: uppercase; font-size: 11px;"
        )
        input_layout.addWidget(input_label)

        self.password_input = ModernPasswordInput()
        self.password_input.setMinimumHeight(40)
        input_layout.addWidget(self.password_input)

        content_layout.addWidget(input_container)

        # Last attempt warning
        if self.attempt_number == self.max_attempts:
            warning_frame = QFrame()
            warning_frame.setStyleSheet("""
                QFrame {
                    background: rgba(231, 76, 60, 0.12);
                    border: 1px solid #c44137;
                    border-radius: 8px;
                    padding: 9px 11px;
                }
            """)
            warning_layout = QHBoxLayout(warning_frame)
            warning_layout.setContentsMargins(9, 6, 10, 6)
            warning_layout.setSpacing(10)

            # Compact icon container
            icon_container = QFrame()
            icon_container.setFixedSize(26, 26)
            icon_container.setStyleSheet("""
                QFrame {
                    background: rgba(231, 76, 60, 0.18);
                    border: 1px solid #c44137;
                    border-radius: 6px;
                }
            """)
            icon_layout = QVBoxLayout(icon_container)
            icon_layout.setContentsMargins(0, 0, 0, 0)
            icon_layout.setSpacing(0)
            warning_icon = QLabel("⚠️")
            warning_icon.setAlignment(Qt.AlignCenter)
            warning_icon.setStyleSheet(
                "font-size: 14px; background: transparent; margin: 0;"
            )
            icon_layout.addWidget(warning_icon)
            warning_layout.addWidget(icon_container)

            warning_text = QLabel("This is your last attempt!")
            warning_text.setFont(QFont("Segoe UI", 10, QFont.Bold))
            warning_text.setStyleSheet("color: #E74C3C; background: transparent;")
            warning_layout.addWidget(warning_text)

            warning_layout.addStretch()
            content_layout.addWidget(warning_frame)

        return content_frame

    def create_footer(self):
        """Create footer section"""
        footer_frame = QFrame()
        footer_frame.setObjectName("footerFrame")
        footer_layout = QHBoxLayout(footer_frame)
        footer_layout.setContentsMargins(24, 12, 24, 12)
        footer_layout.setSpacing(10)

        # Forgot Password Button
        self.forgot_password_button = QPushButton("Forgot Password?")
        self.forgot_password_button.setCursor(Qt.PointingHandCursor)
        self.forgot_password_button.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #7F8C8D;
                font-size: 13px;
                text-align: left;
                padding: 4px;
            }
            QPushButton:hover {
                color: #BDC3C7;
                text-decoration: underline;
            }
            QPushButton:pressed {
                color: #95A5A6;
            }
        """)
        self.forgot_password_button.clicked.connect(self.handle_forgot_password)
        footer_layout.addWidget(self.forgot_password_button)

        # Spacer
        footer_layout.addStretch()

        # Buttons (short labels to fit nicely)
        self.cancel_button = ModernButton("Cancel", "secondary")
        self.ok_button = ModernButton("Sign In", "primary")
        # Override button styles for dark theme after construction
        self.ok_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0d63c7, stop:1 #0b4fa0);
                border: 1px solid #0b4fa0;
                border-radius: 8px;
                color: #ffffff;
                font-size: 13px;
                font-weight: 600;
                padding: 8px 22px;
                min-width: 100px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0e72e3, stop:1 #0d63c7);
            }
            QPushButton:pressed {
                background: #0a458e;
            }
        """)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.04);
                border: 1px solid #2a3746;
                border-radius: 8px;
                color: #c3ccd7;
                font-size: 13px;
                font-weight: 600;
                padding: 8px 20px;
                min-width: 92px;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.08);
                color: #e0e6ed;
            }
            QPushButton:pressed {
                background: rgba(255,255,255,0.12);
            }
        """)
        self.ok_button.setDefault(True)

        footer_layout.addWidget(self.cancel_button)
        footer_layout.addWidget(self.ok_button)

        return footer_frame

    def center_on_screen(self):
        """Center dialog on primary screen (Top-Mid)"""
        from utils.gui_utils import move_window_to_top_center
        move_window_to_top_center(self)

    def setup_connections(self):
        """Wire up events"""
        self.ok_button.clicked.connect(self.accept_password)
        self.cancel_button.clicked.connect(self.reject)
        self.password_input.returnPressed.connect(self.accept_password)

    def setup_animations(self):
        """Prepare animations (focus etc.)"""
        # Focus
        self.password_input.setFocus()

    def accept_password(self):
        """Accept password"""
        password = self.password_input.text().strip()

        if not password:
            self.show_warning("Please enter your master password!")
            return

        self.password = password
        self.password_provided.emit(password)
        self.accept()

    def handle_forgot_password(self):
        """Handle forgot password action"""
        # Custom warning dialog
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Reset Credentials")
        msg_box.setText("Are you sure you want to reset your credentials?")
        msg_box.setInformativeText(
            "This will permanently delete your securely saved API keys (secure_credentials.json).\n\n"
            "You will need to enter your Binance API Key and Secret Key again to use the application."
        )
        msg_box.setIcon(QMessageBox.Warning)
        
        # Add buttons
        reset_btn = msg_box.addButton("Reset & Re-enter Keys", QMessageBox.DestructiveRole)
        msg_box.addButton(QMessageBox.Cancel)
        
        # Modern style matching app theme
        msg_box.setStyleSheet("""
            QMessageBox {
                background: #141b24;
                border-radius: 10px;
                color: #dce2e9;
                border: 1px solid #1f2a38;
            }
            QMessageBox QLabel {
                color: #dce2e9;
                font-size: 12px;
            }
            QPushButton {
                border-radius: 6px;
                padding: 6px 16px;
                font-weight: 600;
                font-size: 12px;
                min-width: 80px;
            }
            QPushButton[text="Cancel"] {
                background: #2a3746;
                color: #c3ccd7;
                border: 1px solid #3d4b5c;
            }
            QPushButton[text="Cancel"]:hover {
                background: #344253;
            }
            QPushButton[text="Reset & Re-enter Keys"] {
                background: #b8322c;
                color: white;
                border: 1px solid #992720;
            }
            QPushButton[text="Reset & Re-enter Keys"]:hover {
                background: #c63a34;
            }
        """)

        msg_box.exec()

        if msg_box.clickedButton() == reset_btn:
             # Delete credentials
            from utils.security.secure_storage import get_secure_storage
            
            storage = get_secure_storage()
            if storage.delete_credentials():
                # Show success message briefly
                # Force close dialog with specific code to indicate reset
                self.done(100)  # Custom code 100 for reset
            else:
                self.show_warning("Failed to delete credentials file. Please delete 'config/secure_credentials.json' manually.")

    def show_warning(self, message):
        """Show modern warning"""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Warning")
        msg_box.setText(message)
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setStandardButtons(QMessageBox.Ok)

        # Modern style
        msg_box.setStyleSheet("""
            QMessageBox {
                background: #141b24;
                border-radius: 10px;
                color: #dce2e9;
                border: 1px solid #1f2a38;
            }
            QMessageBox QLabel {
                color: #dce2e9;
            }
            QMessageBox QPushButton {
                background: #0d63c7;
                border: 1px solid #0b4fa0;
                border-radius: 6px;
                color: #ffffff;
                font-weight: 600;
                padding: 6px 20px;
                min-width: 90px;
            }
            QMessageBox QPushButton:hover {
                background: #0e72e3;
            }
            QMessageBox QPushButton:pressed {
                background: #0a458e;
            }
        """)

        msg_box.exec()
        self.password_input.setFocus()

    def get_password(self):
        """Return password"""
        return self.password

    def keyPressEvent(self, event):
        """Keyboard events"""
        if event.key() == Qt.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)

    def showEvent(self, event):
        """When dialog is shown"""
        super().showEvent(event)
        self.password_input.setFocus()


def show_master_password_dialog(parent=None, attempt_number=1, max_attempts=3):
    """
    Show modern master password dialog

    Returns:
        tuple: (password, accepted)
    """
    dialog = MasterPasswordDialog(parent, attempt_number, max_attempts)

    # Center
    # Always position at top-center as requested
    from utils.gui_utils import move_window_to_top_center
    move_window_to_top_center(dialog)

    result = dialog.exec()

    if result == 100:
        # Special code for credentials reset
        raise ValueError("CREDENTIALS_RESET")
    elif result == QDialog.Accepted:
        return dialog.get_password(), True
    else:
        return None, False


if __name__ == "__main__":
    """Test the modern dialog"""
    app = QApplication(sys.argv)

    # Modern theme
    app.setStyle("Fusion")

    # Test
    for attempt in range(1, 4):
        password, accepted = show_master_password_dialog(None, attempt, 3)

        if accepted:
            print(f"Attempt {attempt}: Password - {password}")
            if password == "test123":
                print("✅ Correct password!")
                break
            else:
                print("❌ Wrong password!")
        else:
            print(f"Attempt {attempt}: Cancelled")
            break

    app.quit()
