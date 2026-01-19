"""
Favorite Coins Panel Component.
Manages the grid of favorite coins with buy/sell buttons.
"""

from PySide6.QtWidgets import QGroupBox, QGridLayout, QPushButton
from PySide6.QtCore import Signal

from ui.components.base_component import BaseComponent
from ui.styles.button_styles import (
    HARD_BUY_STYLE,
    SOFT_BUY_STYLE,
    SOFT_SELL_STYLE,
    HARD_SELL_STYLE,
    COIN_LABEL_STYLE,
)
from ui.styles.panel_styles import FAVORITE_COINS_PANEL_STYLE, PanelSizes, LayoutSpacing

from core.paths import FAVORITE_COIN_COUNT


class FavoriteCoinPanel(BaseComponent):
    """Panel containing favorite coins with trading buttons."""

    # Signals for trading operations
    order_requested = Signal(str, int)  # operation_type, coin_index
    coin_details_requested = Signal(object)  # coin_button

    def __init__(self, parent=None):
        super().__init__(parent)
        self.coin_buttons = []
        self.setup_ui()

    def init_component(self):
        """Initialize the favorite coins panel."""
        self.logger.debug("Initializing Favorite Coins Panel")

    def setup_ui(self):
        """Set up the UI for the favorite coins panel."""
        try:
            # Create the main group box
            self.group_box = QGroupBox()
            self.group_box.setMinimumSize(
                PanelSizes.FAVORITE_COINS_MIN_WIDTH,
                PanelSizes.FAVORITE_COINS_MIN_HEIGHT,
            )
            self.group_box.setStyleSheet(FAVORITE_COINS_PANEL_STYLE)

            # Create the grid layout
            self.layout = QGridLayout(self.group_box)
            self.layout.setContentsMargins(
                LayoutSpacing.FAV_COIN_MARGIN,
                LayoutSpacing.FAV_COIN_MARGIN,
                LayoutSpacing.FAV_COIN_MARGIN,
                LayoutSpacing.FAV_COIN_MARGIN,
            )
            self.layout.setSpacing(LayoutSpacing.FAV_COIN_SPACING)

            # Create trading buttons
            self._create_trading_buttons()

            # Set the main layout
            main_layout = QGridLayout(self)
            main_layout.addWidget(self.group_box)

            self.logger.debug("Favorite Coins Panel UI setup completed")

        except Exception as e:
            self.handle_error(e, "Error setting up Favorite Coins Panel UI")

    def _create_trading_buttons(self):
        """Create all trading buttons in the grid layout."""
        try:
            # Row 0: Hard Buy buttons
            for col in range(FAVORITE_COIN_COUNT):
                btn = self._create_order_button(
                    "Hard Buy", HARD_BUY_STYLE, "Hard_Buy", col
                )
                self.layout.addWidget(btn, 0, col)

            # Row 1: Soft Buy buttons
            for col in range(FAVORITE_COIN_COUNT):
                btn = self._create_order_button(
                    "Soft Buy", SOFT_BUY_STYLE, "Soft_Buy", col
                )
                self.layout.addWidget(btn, 1, col)

            # Row 2: Coin label buttons
            for col in range(FAVORITE_COIN_COUNT):
                btn = self._create_coin_button(col)
                self.layout.addWidget(btn, 2, col)
                self.coin_buttons.append(btn)

            # Row 3: Soft Sell buttons
            for col in range(FAVORITE_COIN_COUNT):
                btn = self._create_order_button(
                    "Soft Sell", SOFT_SELL_STYLE, "Soft_Sell", col
                )
                self.layout.addWidget(btn, 3, col)

            # Row 4: Hard Sell buttons
            for col in range(FAVORITE_COIN_COUNT):
                btn = self._create_order_button(
                    "Hard Sell", HARD_SELL_STYLE, "Hard_Sell", col
                )
                self.layout.addWidget(btn, 4, col)

        except Exception as e:
            self.handle_error(e, "Error creating trading buttons")

    def _create_order_button(self, text, style, operation_type, coin_index):
        """Create a trading order button with double-click safety."""
        from ui.components.safe_button import SafeButton
        
        btn = SafeButton(text)
        btn.setStyleSheet(style)
        # Connect to doubleClicked for safety
        btn.doubleClicked.connect(
            lambda: self._handle_order_button(operation_type, coin_index)
        )
        return btn

    def _create_coin_button(self, coin_index):
        """Create a coin label button."""
        btn = QPushButton(f"COIN_{coin_index}\n0.00")
        btn.setStyleSheet(COIN_LABEL_STYLE)
        btn.clicked.connect(lambda: self._handle_coin_details(btn))
        return btn

    def _handle_order_button(self, operation_type, coin_index):
        """Handle order button clicks."""
        self.logger.debug(f"Order requested: {operation_type} for coin {coin_index}")
        self.order_requested.emit(operation_type, coin_index)

    def _handle_coin_details(self, coin_button):
        """Handle coin details button clicks."""
        self.logger.debug("Coin details requested")
        self.coin_details_requested.emit(coin_button)

    def update_coin_button(self, index, symbol, price, wallet_value=None):
        """Update a specific coin button with new data."""
        try:
            if 0 <= index < len(self.coin_buttons):
                button = self.coin_buttons[index]
                
                # Format wallet value string
                if wallet_value is not None and wallet_value > 0:
                     val_str = f"~${wallet_value:.2f}"
                else:
                     val_str = "~$0.00"

                # New 3-line format: Value \n Symbol \n Price
                new_text = f"{val_str}\n{symbol}\n{price}"
                
                if button.text() != new_text:
                    button.setText(new_text)
                    button.setProperty("symbol", symbol)
                    # Optional: Add tooltip for exact value
                    button.setToolTip(f"Holding Value: {val_str}\nCurrent Price: {price}")
        except Exception as e:
            self.handle_error(e, f"Error updating coin button {index}")

    def get_coin_buttons(self):
        """Get the list of coin buttons."""
        return self.coin_buttons

    def get_widget(self):
        """Get the main widget for this component."""
        return self.group_box
