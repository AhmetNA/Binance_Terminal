"""
splash_screen.py
Modern splash screen for Binance Terminal
"""

from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QProgressBar,
    QGraphicsDropShadowEffect,
    QApplication,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QColor
import sys


class ModernSplashScreen(QWidget):
    """Modern splash screen"""

    def __init__(self):
        super().__init__()

        # Window flags
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.SplashScreen
        )
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.setFixedSize(500, 300)
        self.setup_ui()
        self.setup_animations()

        # Center on screen
        self.center_on_screen()

    def center_on_screen(self):
        """Center on primary screen (Top-Mid)"""
        from utils.gui_utils import move_window_to_top_center
        move_window_to_top_center(self)

    def setup_ui(self):
        """Create UI elements"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Ana frame
        main_frame = QWidget()
        main_frame.setObjectName("mainFrame")
        main_frame.setStyleSheet("""
            QWidget#mainFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #667eea, stop:1 #764ba2);
                border-radius: 20px;
                border: 2px solid rgba(255, 255, 255, 0.2);
            }
        """)

        frame_layout = QVBoxLayout(main_frame)
        frame_layout.setContentsMargins(40, 30, 40, 30)
        frame_layout.setSpacing(16)

        # Logo/Icon alanı
        icon_layout = QHBoxLayout()
        icon_layout.addStretch()

        icon_label = QLabel("₿")
        icon_label.setFont(QFont("Segoe UI", 48, QFont.Bold))
        icon_label.setStyleSheet("""
            QLabel {
                color: white;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 40px;
                padding: 20px;
                min-width: 80px;
                max-width: 80px;
                min-height: 80px;
                max-height: 80px;
            }
        """)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_layout.addWidget(icon_label)
        icon_layout.addStretch()

        frame_layout.addLayout(icon_layout)

        # Extra spacer to push title further down from icon
        from PySide6.QtWidgets import QSpacerItem, QSizePolicy

        # Increase spacer to push title further down
        frame_layout.addSpacerItem(
            QSpacerItem(20, 32, QSizePolicy.Minimum, QSizePolicy.Fixed)
        )

        # Title
        title_label = QLabel("Binance Terminal")
        title_label.setFont(QFont("Segoe UI", 24, QFont.Bold))
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                background: transparent;
                text-align: center;
                padding-top: 10px; /* increased for extra gap */
            }
        """)
        title_label.setAlignment(Qt.AlignCenter)
        frame_layout.addWidget(title_label)

        # Subtitle
        subtitle_label = QLabel("Secure Crypto Trading Platform")
        subtitle_label.setFont(QFont("Segoe UI", 12))
        subtitle_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.8);
                background: transparent;
                margin-top: 4px;
                margin-bottom: 12px;
            }
        """)
        subtitle_label.setAlignment(Qt.AlignCenter)
        frame_layout.addWidget(subtitle_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                background: rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                height: 16px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00d4ff, stop:1 #090979);
                border-radius: 8px;
            }
        """)
        frame_layout.addWidget(self.progress_bar)

        # Status label
        self.status_label = QLabel("Starting...")
        self.status_label.setFont(QFont("Segoe UI", 10))
        self.status_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.9);
                background: transparent;
                margin-top: 5px;
            }
        """)
        self.status_label.setAlignment(Qt.AlignCenter)
        frame_layout.addWidget(self.status_label)

        layout.addWidget(main_frame)
        self.setLayout(layout)

        # Gölge efekti
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setXOffset(0)
        shadow.setYOffset(15)
        shadow.setColor(QColor(0, 0, 0, 100))
        main_frame.setGraphicsEffect(shadow)

    def setup_animations(self):
        """Prepare animations"""
        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(self.update_progress)
        self.progress_timer.start(50)  # Her 50ms'de güncelle

        self.progress_value = 0
        self.progress_step = 2

    def update_progress(self):
        """Update progress bar"""
        self.progress_value += self.progress_step

        if self.progress_value >= 100:
            self.progress_value = 100
            self.progress_timer.stop()

        self.progress_bar.setValue(self.progress_value)

        # Update status messages
        if self.progress_value < 20:
            self.status_label.setText("🔧 Loading components...")
        elif self.progress_value < 40:
            self.status_label.setText("🔐 Initializing security modules...")
        elif self.progress_value < 60:
            self.status_label.setText("🌐 Verifying API connections...")
        elif self.progress_value < 80:
            self.status_label.setText("📊 Loading market data...")
        elif self.progress_value < 95:
            self.status_label.setText("🎨 Preparing interface...")
        else:
            self.status_label.setText("✅ Ready!")

    def set_progress(self, value, message=""):
        """Set progress manually"""
        self.progress_bar.setValue(value)
        if message:
            self.status_label.setText(message)

    def finish_loading(self):
        """Finish loading"""
        self.progress_timer.stop()
        self.progress_bar.setValue(100)
        self.status_label.setText("✅ Starting...")

        # Kısa bir gecikme sonra kapat
        QTimer.singleShot(800, self.close)


def show_splash_screen():
    """Show splash screen"""
    splash = ModernSplashScreen()
    splash.show()
    return splash


if __name__ == "__main__":
    """Test splash screen"""
    app = QApplication(sys.argv)

    splash = show_splash_screen()

    # Close after 3 seconds for test
    QTimer.singleShot(3000, splash.finish_loading)

    app.exec()
