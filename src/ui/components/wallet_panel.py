"""
Wallet Panel Component.
Manages the wallet display and settings button.
"""

from PySide6.QtWidgets import QFrame, QVBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Qt, Signal

from .base_component import BaseComponent
from ..styles.button_styles import SETTINGS_BUTTON_STYLE
from ..styles.panel_styles import (
    WALLET_FRAME_STYLE, WALLET_LABEL_STYLE, PanelSizes, LayoutSpacing
)


class WalletPanel(BaseComponent):
    """Panel displaying wallet balance and settings button."""
    
    # Signals
    settings_requested = Signal()  # Settings button clicked
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.wallet_label = None
        self.setup_ui()
    
    def init_component(self):
        """Initialize the wallet panel."""
        self.logger.debug("Initializing Wallet Panel")
    
    def setup_ui(self):
        """Set up the UI for the wallet panel."""
        try:
            # Create the main frame
            self.frame = QFrame()
            self.frame.setFixedSize(
                PanelSizes.WALLET_FRAME_WIDTH,
                PanelSizes.WALLET_FRAME_HEIGHT
            )
            self.frame.setStyleSheet(WALLET_FRAME_STYLE)
            
            # Create the layout
            self.layout = QVBoxLayout(self.frame)
            self.layout.setContentsMargins(
                LayoutSpacing.WALLET_MARGIN,
                LayoutSpacing.WALLET_MARGIN,
                LayoutSpacing.WALLET_MARGIN,
                LayoutSpacing.WALLET_MARGIN
            )
            self.layout.setSpacing(LayoutSpacing.WALLET_SPACING)
            self.layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
            
            # Create UI elements
            self._create_settings_button()
            self._create_wallet_label()
            
            # Set the main layout
            main_layout = QVBoxLayout(self)
            main_layout.addWidget(self.frame)
            
            self.logger.debug("Wallet Panel UI setup completed")
            
        except Exception as e:
            self.handle_error(e, "Error setting up Wallet Panel UI")
    
    def _create_settings_button(self):
        """Create the settings button."""
        try:
            self.settings_button = QPushButton("Settings")
            self.settings_button.setFixedSize(
                PanelSizes.SETTINGS_BUTTON_WIDTH,
                PanelSizes.SETTINGS_BUTTON_HEIGHT
            )
            self.settings_button.setStyleSheet(SETTINGS_BUTTON_STYLE)
            self.settings_button.clicked.connect(self._handle_settings_click)
            self.layout.addWidget(self.settings_button, alignment=Qt.AlignHCenter)
            
        except Exception as e:
            self.handle_error(e, "Error creating settings button")
    
    def _create_wallet_label(self):
        """Create the wallet balance label."""
        try:
            self.wallet_label = QLabel("Wallet\n$0.00")
            self.wallet_label.setAlignment(Qt.AlignCenter)
            self.wallet_label.setStyleSheet(WALLET_LABEL_STYLE)
            self.layout.addWidget(self.wallet_label, alignment=Qt.AlignHCenter)
            
        except Exception as e:
            self.handle_error(e, "Error creating wallet label")
    
    def _handle_settings_click(self):
        """Handle settings button click."""
        self.logger.debug("Settings button clicked")
        self.settings_requested.emit()
    
    def update_wallet_balance(self, balance):
        """Update the wallet balance display."""
        try:
            if self.wallet_label:
                new_text = f"Wallet\n${balance:.2f}"
                if self.wallet_label.text() != new_text:
                    self.wallet_label.setText(new_text)
                    self.log_info(f"Updated wallet balance: ${balance:.2f}")
        except Exception as e:
            self.handle_error(e, f"Error updating wallet balance: {balance}")
    
    def get_widget(self):
        """Get the main widget for this component."""
        return self.frame
