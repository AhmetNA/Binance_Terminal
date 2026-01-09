"""
api_credentials_dialog.py
Simple and clean API credentials setup dialog.
"""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLineEdit,
    QLabel,
    QPushButton,
    QFrame,
    QApplication,
    QCheckBox,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class APICredentialsDialog(QDialog):
    """Simple API credentials setup dialog"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.api_key = ""
        self.api_secret = ""
        self.master_password = ""
        self.setup_ui()
        self.setup_connections()

    def setup_ui(self):
        """Setup the clean UI"""
        self.setWindowTitle("🔐 Binance API Setup")
        self.setModal(True)
        self.setFixedSize(480, 520)  # Increased height from 420 to 520

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(24, 24, 24, 24)  # Increased margins
        main_layout.setSpacing(22)  # Increased spacing

        # Header
        header_label = QLabel("🔐 Binance API Credentials Setup")
        header_label.setFont(QFont("Segoe UI", 20, QFont.Bold))  # Increased font size
        header_label.setAlignment(Qt.AlignCenter)
        header_label.setStyleSheet("""
            QLabel {
                color: #E2E8F0;
                padding: 16px;  # Increased padding
                border-bottom: 2px solid #334155;
                margin-bottom: 16px;  # Increased margin
            }
        """)
        main_layout.addWidget(header_label)

        # Info section
        info_label = QLabel(
            "Enter your Binance API credentials and create a secure master password.\n"
            "Your API keys will be encrypted and stored safely."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("""
            QLabel {
                color: #94A3B8;
                background: #1E293B;
                padding: 18px;  # Increased padding
                border-radius: 8px;
                border: 1px solid #334155;
                line-height: 20px;  # Increased line height
                font-size: 14px;  # Added font size
            }
        """)
        main_layout.addWidget(info_label)

        # Form
        form_frame = QFrame()
        form_layout = QFormLayout(form_frame)
        form_layout.setSpacing(18)  # Increased spacing
        form_layout.setVerticalSpacing(12)  # Increased vertical spacing

        # API Key
        api_key_label = QLabel("API Key:")
        api_key_label.setStyleSheet(
            "color: #F1F5F9; font-weight: 600; font-size: 14px;"
        )  # Increased font size
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setPlaceholderText("Enter your Binance API key")
        self.api_key_edit.setMinimumHeight(42)  # Increased height
        form_layout.addRow(api_key_label, self.api_key_edit)

        # API Secret
        api_secret_label = QLabel("API Secret:")
        api_secret_label.setStyleSheet(
            "color: #F1F5F9; font-weight: 600; font-size: 14px;"
        )  # Increased font size
        self.api_secret_edit = QLineEdit()
        self.api_secret_edit.setPlaceholderText("Enter your Binance API secret")
        self.api_secret_edit.setEchoMode(QLineEdit.Password)
        self.api_secret_edit.setMinimumHeight(42)  # Increased height
        form_layout.addRow(api_secret_label, self.api_secret_edit)

        # Show secret checkbox
        self.show_secret_cb = QCheckBox("Show API Secret")
        self.show_secret_cb.setStyleSheet("""
            QCheckBox {
                color: #94A3B8;
                font-size: 13px;  # Increased font size
                margin-left: 4px;
                margin-top: 6px;  # Added top margin
                margin-bottom: 6px;  # Added bottom margin
            }
            QCheckBox::indicator {
                width: 18px;  # Increased size
                height: 18px;  # Increased size
                border-radius: 3px;
                border: 2px solid #475569;
                background: #1E293B;
            }
            QCheckBox::indicator:checked {
                background: #3B82F6;
                border-color: #3B82F6;
            }
            QCheckBox::indicator:checked::after {
                content: "✓";
                color: white;
                font-weight: bold;
            }
        """)
        form_layout.addRow("", self.show_secret_cb)

        # Master Password
        master_label = QLabel("Master Password:")
        master_label.setStyleSheet(
            "color: #F1F5F9; font-weight: 600; font-size: 14px;"
        )  # Increased font size
        self.master_password_edit = QLineEdit()
        self.master_password_edit.setPlaceholderText("Create a strong master password")
        self.master_password_edit.setEchoMode(QLineEdit.Password)
        self.master_password_edit.setMinimumHeight(42)  # Increased height
        form_layout.addRow(master_label, self.master_password_edit)

        # Confirm Password
        confirm_label = QLabel("Confirm Password:")
        confirm_label.setStyleSheet(
            "color: #F1F5F9; font-weight: 600; font-size: 14px;"
        )  # Increased font size
        self.confirm_password_edit = QLineEdit()
        self.confirm_password_edit.setPlaceholderText("Confirm your master password")
        self.confirm_password_edit.setEchoMode(QLineEdit.Password)
        self.confirm_password_edit.setMinimumHeight(42)  # Increased height
        form_layout.addRow(confirm_label, self.confirm_password_edit)

        main_layout.addWidget(form_frame)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setMinimumHeight(32)  # Increased height
        self.status_label.setStyleSheet(
            "color: #94A3B8; font-size: 14px;"
        )  # Increased font size
        main_layout.addWidget(self.status_label)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setMinimumSize(100, 44)  # Increased size
        button_layout.addWidget(self.cancel_btn)

        self.setup_btn = QPushButton("Setup & Encrypt")
        self.setup_btn.setMinimumSize(160, 44)  # Increased size
        self.setup_btn.setEnabled(False)
        button_layout.addWidget(self.setup_btn)

        main_layout.addLayout(button_layout)

        # Apply dark theme styling
        self.setStyleSheet("""
            QDialog {
                background: #0F172A;
                color: #F1F5F9;
                border-radius: 12px;
            }
            QLineEdit {
                border: 2px solid #334155;
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 14px;
                background: #1E293B;
                color: #F1F5F9;
                selection-background-color: #3B82F6;
            }
            QLineEdit:focus {
                border-color: #3B82F6;
                background: #1E293B;
            }
            QLineEdit:hover {
                border-color: #475569;
            }
            QLineEdit::placeholder {
                color: #64748B;
            }
            QPushButton {
                background: #334155;
                border: 2px solid #475569;
                border-radius: 8px;
                padding: 10px 18px;
                font-size: 14px;
                font-weight: 600;
                color: #F1F5F9;
            }
            QPushButton:hover {
                background: #475569;
                border-color: #64748B;
            }
            QPushButton:pressed {
                background: #1E293B;
            }
            QPushButton:disabled {
                background: #1E293B;
                color: #64748B;
                border-color: #334155;
            }
            QPushButton#setup_btn {
                background: #3B82F6;
                border-color: #2563EB;
                color: white;
            }
            QPushButton#setup_btn:hover {
                background: #2563EB;
                border-color: #1D4ED8;
            }
            QPushButton#setup_btn:pressed {
                background: #1D4ED8;
            }
            QPushButton#setup_btn:disabled {
                background: #334155;
                border-color: #475569;
                color: #64748B;
            }
            QFormLayout QLabel {
                color: #F1F5F9;
                font-weight: 600;
                margin-bottom: 4px;
            }
        """)

        # Set object names for styling
        self.setup_btn.setObjectName("setup_btn")

        self.setLayout(main_layout)

        # Center on screen
        self.center_on_screen()

    def setup_connections(self):
        """Setup signal connections"""
        self.cancel_btn.clicked.connect(self.reject)
        self.setup_btn.clicked.connect(self.validate_and_accept)

        # Input validation
        self.api_key_edit.textChanged.connect(self.validate_inputs)
        self.api_secret_edit.textChanged.connect(self.validate_inputs)
        self.master_password_edit.textChanged.connect(self.validate_inputs)
        self.confirm_password_edit.textChanged.connect(self.validate_inputs)

        # Show/hide secret
        self.show_secret_cb.toggled.connect(self.toggle_secret_visibility)

        # Enter key handling
        self.api_key_edit.returnPressed.connect(self.api_secret_edit.setFocus)
        self.api_secret_edit.returnPressed.connect(self.master_password_edit.setFocus)
        self.master_password_edit.returnPressed.connect(
            self.confirm_password_edit.setFocus
        )
        self.confirm_password_edit.returnPressed.connect(self.validate_and_accept)

    def toggle_secret_visibility(self, show):
        """Toggle API secret visibility"""
        if show:
            self.api_secret_edit.setEchoMode(QLineEdit.Normal)
        else:
            self.api_secret_edit.setEchoMode(QLineEdit.Password)

    def validate_inputs(self):
        """Validate all inputs and update UI"""
        api_key = self.api_key_edit.text().strip()
        api_secret = self.api_secret_edit.text().strip()
        master_password = self.master_password_edit.text()
        confirm_password = self.confirm_password_edit.text()

        # Validation flags
        api_key_valid = len(api_key) >= 10
        api_secret_valid = len(api_secret) >= 10
        password_valid = len(master_password) >= 8
        passwords_match = master_password == confirm_password and master_password != ""

        # Update status
        if not api_key_valid:
            self.status_label.setText("⚠️ API Key must be at least 10 characters")
            self.status_label.setStyleSheet(
                "color: #F87171; font-weight: 600; font-size: 13px;"
            )
        elif not api_secret_valid:
            self.status_label.setText("⚠️ API Secret must be at least 10 characters")
            self.status_label.setStyleSheet(
                "color: #F87171; font-weight: 600; font-size: 13px;"
            )
        elif not password_valid:
            self.status_label.setText("⚠️ Master password must be at least 8 characters")
            self.status_label.setStyleSheet(
                "color: #F87171; font-weight: 600; font-size: 13px;"
            )
        elif not passwords_match:
            self.status_label.setText("⚠️ Passwords do not match")
            self.status_label.setStyleSheet(
                "color: #F87171; font-weight: 600; font-size: 13px;"
            )
        else:
            self.status_label.setText("✅ Ready to setup secure credentials")
            self.status_label.setStyleSheet(
                "color: #34D399; font-weight: 600; font-size: 13px;"
            )

        # Enable/disable setup button
        all_valid = (
            api_key_valid and api_secret_valid and password_valid and passwords_match
        )
        self.setup_btn.setEnabled(all_valid)

    def validate_and_accept(self):
        """Final validation and acceptance"""
        if not self.setup_btn.isEnabled():
            return

        api_key = self.api_key_edit.text().strip()
        api_secret = self.api_secret_edit.text().strip()
        master_password = self.master_password_edit.text()

        # Store credentials
        self.api_key = api_key
        self.api_secret = api_secret
        self.master_password = master_password

        # Update button state
        self.setup_btn.setText("Setting up...")
        self.setup_btn.setEnabled(False)

        # Accept dialog
        self.accept()

    def center_on_screen(self):
        """Center dialog on screen (Top-Mid)"""
        from utils.gui_utils import move_window_to_top_center
        move_window_to_top_center(self)

    def get_credentials(self):
        """Get the entered credentials"""
        return self.api_key, self.api_secret, self.master_password

    def keyPressEvent(self, event):
        """Handle key press events"""
        if event.key() == Qt.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)
