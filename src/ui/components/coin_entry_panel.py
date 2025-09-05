"""
Coin Entry Panel Component.
Manages the coin input field and submission.
"""

from PySide6.QtWidgets import QFrame, QVBoxLayout, QPushButton, QLabel, QLineEdit
from PySide6.QtCore import Qt, Signal

from .base_component import BaseComponent
from ..styles.button_styles import SUBMIT_BUTTON_STYLE
from ..styles.panel_styles import (
    COIN_ENTRY_FRAME_STYLE, ENTRY_LABEL_STYLE, COIN_INPUT_STYLE,
    PanelSizes, LayoutSpacing
)


class CoinEntryPanel(BaseComponent):
    """Panel for entering new coin symbols."""
    
    # Signals
    coin_submitted = Signal(str)  # coin_symbol
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.coin_input = None
        self.setup_ui()
    
    def init_component(self):
        """Initialize the coin entry panel."""
        self.logger.debug("Initializing Coin Entry Panel")
    
    def setup_ui(self):
        """Set up the UI for the coin entry panel."""
        try:
            # Create the main frame
            self.frame = QFrame()
            self.frame.setFixedSize(
                PanelSizes.COIN_ENTRY_FRAME_WIDTH,
                PanelSizes.COIN_ENTRY_FRAME_HEIGHT
            )
            self.frame.setStyleSheet(COIN_ENTRY_FRAME_STYLE)
            
            # Create the layout
            self.layout = QVBoxLayout(self.frame)
            self.layout.setContentsMargins(
                LayoutSpacing.ENTRY_MARGIN,
                LayoutSpacing.ENTRY_MARGIN - 2,  # Slightly smaller top/bottom margin
                LayoutSpacing.ENTRY_MARGIN,
                LayoutSpacing.ENTRY_MARGIN - 2
            )
            self.layout.setSpacing(LayoutSpacing.ENTRY_SPACING)
            
            # Create UI elements
            self._create_entry_label()
            self._create_coin_input()
            self._create_submit_button()
            
            # Set the main layout
            main_layout = QVBoxLayout(self)
            main_layout.addWidget(self.frame)
            
            self.logger.debug("Coin Entry Panel UI setup completed")
            
        except Exception as e:
            self.handle_error(e, "Error setting up Coin Entry Panel UI")
    
    def _create_entry_label(self):
        """Create the entry instruction label."""
        try:
            self.entry_label = QLabel("Enter coin")
            self.entry_label.setAlignment(Qt.AlignCenter)
            self.entry_label.setStyleSheet(ENTRY_LABEL_STYLE)
            self.layout.addWidget(self.entry_label)
            
        except Exception as e:
            self.handle_error(e, "Error creating entry label")
    
    def _create_coin_input(self):
        """Create the coin input field."""
        try:
            self.coin_input = QLineEdit()
            self.coin_input.setStyleSheet(COIN_INPUT_STYLE)
            self.coin_input.returnPressed.connect(self._handle_submit)
            self.layout.addWidget(self.coin_input)
            
        except Exception as e:
            self.handle_error(e, "Error creating coin input")
    
    def _create_submit_button(self):
        """Create the submit button."""
        try:
            # Add extra spacing before the submit button
            self.layout.addSpacing(LayoutSpacing.ENTRY_EXTRA_SPACING)
            
            self.submit_button = QPushButton("Submit")
            self.submit_button.setStyleSheet(SUBMIT_BUTTON_STYLE)
            self.submit_button.clicked.connect(self._handle_submit)
            self.layout.addWidget(self.submit_button)
            
        except Exception as e:
            self.handle_error(e, "Error creating submit button")
    
    def _handle_submit(self):
        """Handle coin submission."""
        try:
            if self.coin_input:
                coin_name = self.coin_input.text().strip()
                if coin_name:
                    self.logger.debug(f"Coin submitted: {coin_name}")
                    self.coin_submitted.emit(coin_name)
                    self.coin_input.clear()
                else:
                    self.log_warning("Empty coin name submitted")
        except Exception as e:
            self.handle_error(e, "Error handling coin submission")
    
    def clear_input(self):
        """Clear the input field."""
        try:
            if self.coin_input:
                self.coin_input.clear()
        except Exception as e:
            self.handle_error(e, "Error clearing input")
    
    def set_input_text(self, text):
        """Set the input field text."""
        try:
            if self.coin_input:
                self.coin_input.setText(text)
        except Exception as e:
            self.handle_error(e, f"Error setting input text: {text}")
    
    def get_input_text(self):
        """Get the current input field text."""
        try:
            if self.coin_input:
                return self.coin_input.text().strip()
            return ""
        except Exception as e:
            self.handle_error(e, "Error getting input text")
            return ""
    
    def get_widget(self):
        """Get the main widget for this component."""
        return self.frame
