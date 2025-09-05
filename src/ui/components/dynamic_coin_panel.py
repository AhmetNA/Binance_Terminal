"""
Dynamic Coin Panel Component.
Manages the dynamic coin trading operations and display.
"""

from PySide6.QtWidgets import QGroupBox, QVBoxLayout, QPushButton
from PySide6.QtCore import Qt, Signal

from .base_component import BaseComponent
from ..styles.button_styles import (
    DYN_HARD_BUY_STYLE, DYN_SOFT_BUY_STYLE, DYN_SOFT_SELL_STYLE,
    DYN_HARD_SELL_STYLE, DYN_COIN_LABEL_STYLE
)
from ..styles.panel_styles import (
    DYNAMIC_COIN_PANEL_STYLE, PanelSizes, LayoutSpacing
)

# Import constants from core paths
import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(src_dir)

from core.paths import DYNAMIC_COIN_INDEX


class DynamicCoinPanel(BaseComponent):
    """Panel for dynamic coin trading operations."""
    
    # Signals for trading operations
    order_requested = Signal(str, int)  # operation_type, coin_index (always DYNAMIC_COIN_INDEX)
    coin_details_requested = Signal(object)  # coin_button
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.coin_button = None
        self.setup_ui()
    
    def init_component(self):
        """Initialize the dynamic coin panel."""
        self.logger.debug("Initializing Dynamic Coin Panel")
    
    def setup_ui(self):
        """Set up the UI for the dynamic coin panel."""
        try:
            # Create the main group box
            self.group_box = QGroupBox()
            self.group_box.setMinimumSize(
                PanelSizes.DYNAMIC_COIN_MIN_WIDTH,
                PanelSizes.DYNAMIC_COIN_MIN_HEIGHT
            )
            self.group_box.setStyleSheet(DYNAMIC_COIN_PANEL_STYLE)
            
            # Create the vertical layout
            self.layout = QVBoxLayout(self.group_box)
            self.layout.setContentsMargins(
                LayoutSpacing.DYN_COIN_MARGIN,
                LayoutSpacing.DYN_COIN_MARGIN,
                LayoutSpacing.DYN_COIN_MARGIN,
                LayoutSpacing.DYN_COIN_MARGIN
            )
            self.layout.setSpacing(LayoutSpacing.DYN_COIN_SPACING)
            
            # Create trading buttons
            self._create_trading_buttons()
            
            # Set the main layout
            main_layout = QVBoxLayout(self)
            main_layout.addWidget(self.group_box)
            
            self.logger.debug("Dynamic Coin Panel UI setup completed")
            
        except Exception as e:
            self.handle_error(e, "Error setting up Dynamic Coin Panel UI")
    
    def _create_trading_buttons(self):
        """Create all trading buttons for the dynamic coin."""
        try:
            # Hard Buy button
            btn_hard_buy = self._create_order_button("Hard Buy", DYN_HARD_BUY_STYLE, "Hard_Buy")
            self.layout.addWidget(btn_hard_buy)
            
            # Soft Buy button
            btn_soft_buy = self._create_order_button("Soft Buy", DYN_SOFT_BUY_STYLE, "Soft_Buy")
            self.layout.addWidget(btn_soft_buy)
            
            # Coin label button
            self.coin_button = QPushButton("DYN_COIN\n0.00")
            self.coin_button.setStyleSheet(DYN_COIN_LABEL_STYLE)
            self.coin_button.clicked.connect(lambda: self._handle_coin_details(self.coin_button))
            self.layout.addWidget(self.coin_button)
            
            # Add extra spacing before sell buttons
            self.layout.addSpacing(LayoutSpacing.DYN_COIN_EXTRA_SPACING)
            
            # Soft Sell button
            btn_soft_sell = self._create_order_button("Soft Sell", DYN_SOFT_SELL_STYLE, "Soft_Sell")
            self.layout.addWidget(btn_soft_sell)
            
            # Hard Sell button
            btn_hard_sell = self._create_order_button("Hard Sell", DYN_HARD_SELL_STYLE, "Hard_Sell")
            self.layout.addWidget(btn_hard_sell)
            
        except Exception as e:
            self.handle_error(e, "Error creating dynamic coin trading buttons")
    
    def _create_order_button(self, text, style, operation_type):
        """Create a trading order button."""
        btn = QPushButton(text)
        btn.setStyleSheet(style)
        btn.clicked.connect(lambda: self._handle_order_button(operation_type))
        return btn
    
    def _handle_order_button(self, operation_type):
        """Handle order button clicks."""
        self.logger.debug(f"Dynamic coin order requested: {operation_type}")
        self.order_requested.emit(operation_type, DYNAMIC_COIN_INDEX)
    
    def _handle_coin_details(self, coin_button):
        """Handle coin details button clicks."""
        self.logger.debug("Dynamic coin details requested")
        self.coin_details_requested.emit(coin_button)
    
    def update_coin_button(self, symbol, price):
        """Update the dynamic coin button with new data."""
        try:
            if self.coin_button:
                new_text = f"{symbol}\n{price}"
                if self.coin_button.text() != new_text:
                    self.coin_button.setText(new_text)
        except Exception as e:
            self.handle_error(e, "Error updating dynamic coin button")
    
    def get_coin_button(self):
        """Get the coin button."""
        return self.coin_button
    
    def get_widget(self):
        """Get the main widget for this component."""
        return self.group_box
