"""
security_dialogs.py
Modern security dialogs (English localized)
"""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QApplication,
    QGraphicsDropShadowEffect,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QColor
import sys


class ModernSecurityDialog(QDialog):
    """Modern security dialog base class"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setModal(True)
        # Use a compact minimum size; allow height to grow with content
        self.setMinimumWidth(420)
        self.resize(420, 300)
        self.setup_shadow()
        self.center_on_screen()  # Center on screen

    def center_on_screen(self):
        """Center dialog on screen (Top-Mid)"""
        from utils.gui_utils import move_window_to_top_center
        move_window_to_top_center(self)

    def setup_shadow(self):
        """Add drop shadow effect"""
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(25)
        shadow.setXOffset(0)
        shadow.setYOffset(8)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.setGraphicsEffect(shadow)


class SecuritySuccessDialog(ModernSecurityDialog):
    """Security success dialog"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("✅ Success")
        self.setup_ui()

    def setup_ui(self):
        """Build success UI"""
        # Ana widget
        main_widget = QFrame()
        main_widget.setObjectName("mainWidget")
        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Header (green)
        header_frame = QFrame()
        header_frame.setObjectName("headerFrame")
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(22, 18, 22, 18)

        # Success icon
        icon_label = QLabel("✅")
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet(
            "font-size: 34px; background: transparent; color: white;"
        )
        header_layout.addWidget(icon_label)

        # Title
        title_label = QLabel("Login Successful")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Segoe UI", 15, QFont.Bold))
        title_label.setStyleSheet(
            "color: white; background: transparent; margin-top: 4px; letter-spacing: 0.5px;"
        )
        header_layout.addWidget(title_label)

        main_layout.addWidget(header_frame)

        # Content
        content_frame = QFrame()
        content_frame.setObjectName("contentFrame")
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(24, 18, 24, 16)
        content_layout.setSpacing(10)

        message_label = QLabel(
            "🔓 Master password verified. API keys decrypted successfully."
        )
        message_label.setAlignment(Qt.AlignCenter)
        message_label.setWordWrap(True)
        message_label.setFont(QFont("Segoe UI", 11))
        message_label.setStyleSheet(
            "color: #c3ccd7; background: transparent; padding: 2px 4px;"
        )
        content_layout.addWidget(message_label)

        loading_label = QLabel("🚀 Launching Binance Terminal...")
        loading_label.setAlignment(Qt.AlignCenter)
        loading_label.setFont(QFont("Segoe UI", 10))
        loading_label.setStyleSheet(
            "color: #7f8c8d; background: transparent; margin-top: 6px;"
        )
        content_layout.addWidget(loading_label)

        main_layout.addWidget(content_frame)

        # Footer
        footer_frame = QFrame()
        footer_frame.setObjectName("footerFrame")
        footer_layout = QHBoxLayout(footer_frame)
        footer_layout.setContentsMargins(22, 12, 22, 14)

        footer_layout.addStretch()

        ok_button = QPushButton("Continue")
        ok_button.setDefault(True)
        ok_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #17924d, stop:1 #137b40);
                border: 1px solid #137b40;
                border-radius: 8px;
                color: #ffffff;
                font-size: 12px;
                font-weight: 600;
                padding: 7px 20px;
                min-width: 92px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1aa456, stop:1 #17924d);
            }
            QPushButton:pressed {
                background: #0f6534;
            }
        """)
        ok_button.clicked.connect(self.accept)
        footer_layout.addWidget(ok_button)

        main_layout.addWidget(footer_frame)

        # Layout
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(main_widget)
        self.setLayout(layout)

        # Style (dark theme to match master password dialog)
        self.setStyleSheet("""
            QDialog {
                background: #10141b;
                border-radius: 16px;
                color: #dce2e9;
            }
            QFrame#mainWidget {
                background: #10141b;
                border-radius: 16px;
                border: 1px solid #1f2a38;
            }
            QFrame#headerFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0f5a2d, stop:1 #0d4f28);
                border-radius: 16px 16px 0 0;
                min-height: 70px;
            }
            QFrame#contentFrame {
                background: #141b24;
            }
            QFrame#footerFrame {
                background: #141b24;
                border-radius: 0 0 16px 16px;
                border-top: 1px solid #1f2a38;
            }
        """)

        # Auto close timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.accept)
        self.timer.start(1800)  # Auto-close after ~1.8s (faster since compact)


class SecurityErrorDialog(ModernSecurityDialog):
    """Security error dialog"""

    def __init__(self, error_message, recovery_tips=None, parent=None):
        self.error_message = error_message
        self.recovery_tips = recovery_tips or []
        super().__init__(parent)
        self.setWindowTitle("🚫 Security Error")
        self.setup_ui()

    def setup_ui(self):
        """Build error UI"""
        # Main widget
        main_widget = QFrame()
        main_widget.setObjectName("mainWidget")
        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Header (red)

        header_frame = QFrame()
        header_frame.setObjectName("headerFrame")
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(26, 18, 26, 18)
        header_layout.setSpacing(6)

        # Use PNG icon instead of emoji, smaller and with margin
        from PySide6.QtGui import QPixmap

        icon_label = QLabel()
        icon_pixmap = QPixmap("assets/btc.png")
        if not icon_pixmap.isNull():
            icon_label.setPixmap(
                icon_pixmap.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
        else:
            icon_label.setText("!")
            icon_label.setStyleSheet("font-size: 28px; color: white;")
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("background: transparent; margin-bottom: 4px;")
        header_layout.addWidget(icon_label, alignment=Qt.AlignHCenter)

        # Add extra spacing between icon and title
        from PySide6.QtWidgets import QSpacerItem, QSizePolicy

        header_layout.addSpacerItem(
            QSpacerItem(1, 6, QSizePolicy.Minimum, QSizePolicy.Fixed)
        )

        title_label = QLabel("Security Error")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Segoe UI", 17, QFont.Bold))
        title_label.setStyleSheet(
            "color: white; background: transparent; margin-top: 0px; letter-spacing: 1.1px;"
        )
        header_layout.addWidget(title_label)

        main_layout.addWidget(header_frame)

        # Content
        content_frame = QFrame()
        content_frame.setObjectName("contentFrame")
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(26, 22, 26, 18)
        content_layout.setSpacing(14)

        error_label = QLabel(self.error_message)
        error_label.setAlignment(Qt.AlignCenter)
        error_label.setWordWrap(True)
        error_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        error_label.setStyleSheet(
            "color: #ff5f56; background: transparent; padding: 2px 4px;"
        )
        content_layout.addWidget(error_label)

        if self.recovery_tips:
            tips_header = QHBoxLayout()
            tips_icon = QLabel("💡")
            tips_icon.setStyleSheet(
                "font-size: 16px; background: transparent; margin-right: 4px;"
            )
            tips_title = QLabel("Recovery Tips")
            tips_title.setFont(QFont("Segoe UI", 11, QFont.Bold))
            tips_title.setStyleSheet(
                "color: #c3ccd7; background: transparent; letter-spacing: 0.3px;"
            )
            tips_header.addWidget(tips_icon)
            tips_header.addWidget(tips_title)
            tips_header.addStretch()
            content_layout.addLayout(tips_header)

            tips_container = QFrame()
            tips_container.setObjectName("tipsContainer")
            tips_container.setStyleSheet("""
                QFrame#tipsContainer {
                    background: #101922;
                    border: 1px solid #22303d;
                    border-radius: 8px;
                }
            """)
            tips_v = QVBoxLayout(tips_container)
            tips_v.setContentsMargins(10, 8, 10, 8)
            tips_v.setSpacing(6)
            for tip in self.recovery_tips:
                tip_label = QLabel(f"• {tip}")
                tip_label.setWordWrap(True)
                tip_label.setStyleSheet(
                    "color: #9fb0be; background: transparent; font-size: 11px;"
                )
                tips_v.addWidget(tip_label)
            content_layout.addWidget(tips_container)

        main_layout.addWidget(content_frame)

        # Footer
        footer_frame = QFrame()
        footer_frame.setObjectName("footerFrame")
        footer_layout = QHBoxLayout(footer_frame)
        footer_layout.setContentsMargins(26, 14, 26, 16)
        footer_layout.setSpacing(10)
        footer_layout.addStretch()

        close_button = QPushButton("Close")
        close_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #b8322c, stop:1 #992720);
                border: 1px solid #992720;
                border-radius: 8px;
                color: #ffffff;
                font-size: 12px;
                font-weight: 600;
                padding: 8px 26px;
                min-width: 92px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #c63a34, stop:1 #b8322c);
            }
            QPushButton:pressed {
                background: #81201b;
            }
        """)
        close_button.clicked.connect(self.reject)
        footer_layout.addWidget(close_button)
        main_layout.addWidget(footer_frame)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(main_widget)
        self.setLayout(layout)

        # Dark style
        self.setMinimumWidth(480)
        self.setStyleSheet("""
            QDialog { background: #10141b; border-radius: 16px; color: #dce2e9; }
            QFrame#mainWidget { background: #10141b; border-radius: 16px; border: 1px solid #1f2a38; }
            QFrame#headerFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #7d201b, stop:1 #651713);
                border-radius: 16px 16px 0 0;
                min-height: 86px;
            }
            QFrame#contentFrame { background: #141b24; }
            QFrame#footerFrame { background: #141b24; border-radius: 0 0 16px 16px; border-top: 1px solid #1f2a38; }
        """)


def show_security_success(parent=None):
    """Show security success dialog"""
    dialog = SecuritySuccessDialog(parent)

    # Center
    if parent:
        dialog.move(parent.geometry().center() - dialog.rect().center())
    else:
        from utils.gui_utils import move_window_to_top_center
        move_window_to_top_center(dialog)

    return dialog.exec()


def show_security_error(error_message, recovery_tips=None, parent=None):
    """Show security error dialog"""
    dialog = SecurityErrorDialog(error_message, recovery_tips, parent)

    # Center
    if parent:
        dialog.move(parent.geometry().center() - dialog.rect().center())
    else:
        from utils.gui_utils import move_window_to_top_center
        move_window_to_top_center(dialog)

    return dialog.exec()


if __name__ == "__main__":
    """Test dialogs"""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Success test
    print("Success dialog test...")
    show_security_success()

    # Error test
    print("Error dialog test...")
    recovery_tips = ["Delete config/secure_credentials.json", "Restart the application"]
    show_security_error("Master password entered incorrectly 3 times!", recovery_tips)

    app.quit()
