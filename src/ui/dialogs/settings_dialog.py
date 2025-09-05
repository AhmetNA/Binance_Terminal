"""
Settings Dialog Component.
Manages the application settings window.
"""

import logging
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox,
    QHBoxLayout, QApplication, QGridLayout
)
from PySide6.QtCore import Qt, Signal

from ..styles.button_styles import SAVE_BUTTON_STYLE
from ..styles.panel_styles import (
    SETTINGS_DIALOG_STYLE, SETTINGS_LABEL_STYLE, SETTINGS_INPUT_STYLE
)

# Import required modules
import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(src_dir)

from core.paths import PREFERENCES_FILE
from config.preferences_service import set_preference, update_favorite_coin
from services.live_price_service import set_dynamic_coin_symbol, subscribe_to_dynamic_coin
from utils.symbol_utils import process_user_coin_input
import json


class SettingsDialog(QDialog):
    """Settings dialog for configuring application preferences."""
    
    # Signals
    settings_saved = Signal(str)  # message
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setFixedSize(350, 550)  # Increased height for dynamic coins section
        self.setStyleSheet(SETTINGS_DIALOG_STYLE)
        
        self.original_prefs = {}
        self.original_coins = []
        self.original_dynamic_coins = []  # Dynamic coins'ler için
        self.pref_edits = {}
        self.fav_edits = []
        self.dynamic_edits = []  # Dynamic coin input'ları için
        self.interval_edit = None
        
        self.load_preferences()
        self.setup_ui()
        self.position_dialog()
    
    def showEvent(self, event):
        """Override showEvent to reload preferences every time dialog is shown."""
        super().showEvent(event)
        try:
            # Her dialog açıldığında JSON'dan coinleri al ve preferences'ı güncelle
            logging.info("Settings dialog opened - updating preferences from JSON...")
            self._update_preferences_from_json()
            self.load_preferences()
            self.refresh_ui_with_current_data()
            logging.info("Settings dialog refreshed with current preferences")
        except Exception as e:
            logging.error(f"Error refreshing settings dialog: {e}")
    
    def load_preferences(self):
        """Load preferences from the preferences file."""
        try:
            prefs = {}
            
            with open(PREFERENCES_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # Parse lines that contain key-value pairs and are not comments
                    if "=" in line and not line.startswith("#"):
                        try:
                            key, val = line.split("=", 1)
                            key = key.strip()
                            val = val.strip().lstrip("%").strip()
                            prefs[key] = val
                        except Exception:
                            continue  # Skip malformed lines
            
            # Store original preferences to allow change detection
            self.original_prefs = prefs.copy()
            
            # Parse favorite coins
            coins_str = prefs.get("favorite_coins", "")
            self.original_coins = [c.strip().upper() for c in coins_str.split(",") if c.strip()]
            
            # Load dynamic coins from fav_coins.json
            self._load_dynamic_coins()
            
        except FileNotFoundError:
            logging.warning(f"Preferences file not found: {PREFERENCES_FILE}")
            self.original_prefs = {}
            self.original_coins = []
            self.original_dynamic_coins = []
        except Exception as e:
            logging.error(f"Error loading preferences: {e}")
            self.original_prefs = {}
            self.original_coins = []
            self.original_dynamic_coins = []
    
    def _load_dynamic_coins(self):
        """Load dynamic coins from fav_coins.json file."""
        try:
            # fav_coins.json dosyasının path'ini oluştur
            config_dir = os.path.dirname(PREFERENCES_FILE)
            fav_coins_file = os.path.join(config_dir, "fav_coins.json")
            
            if os.path.exists(fav_coins_file):
                with open(fav_coins_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    dynamic_coins = data.get("dynamic_coin", [])
                    
                    # Dynamic coin'lerin name'lerini al
                    self.original_dynamic_coins = [
                        coin.get("original_input", "").upper() 
                        for coin in dynamic_coins 
                        if coin.get("original_input")
                    ]
                    
                    logging.info(f"Loaded {len(self.original_dynamic_coins)} dynamic coins: {self.original_dynamic_coins}")
            else:
                self.original_dynamic_coins = []
                logging.info("fav_coins.json file not found, no dynamic coins loaded")
                
        except Exception as e:
            logging.error(f"Error loading dynamic coins: {e}")
            self.original_dynamic_coins = []
    
    def _update_preferences_from_json(self):
        """Update preferences.txt file with coins from fav_coins.json."""
        try:
            # fav_coins.json dosyasının path'ini oluştur
            config_dir = os.path.dirname(PREFERENCES_FILE)
            fav_coins_file = os.path.join(config_dir, "fav_coins.json")
            
            if not os.path.exists(fav_coins_file):
                logging.warning("fav_coins.json file not found, skipping preferences update")
                return
            
            # JSON dosyasından coin verilerini oku
            with open(fav_coins_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Regular coins'leri al (dynamic coin hariç) - sadece ilk 5 tanesini al
            regular_coins = data.get("coins", [])
            coin_names = [coin.get("name", "").upper() for coin in regular_coins if coin.get("name")]
            coin_names = coin_names[:5]  # Sadece ilk 5 coin'i al
            
            # Dynamic coins'leri al
            dynamic_coins = data.get("dynamic_coin", [])
            dynamic_coin_names = [
                coin.get("original_input", "").upper() 
                for coin in dynamic_coins 
                if coin.get("original_input")
            ]
            
            # Preferences dosyasını oku
            preferences_lines = []
            with open(PREFERENCES_FILE, 'r', encoding='utf-8') as f:
                preferences_lines = f.readlines()
            
            # Preferences dosyasını güncelle
            updated_lines = []
            for line in preferences_lines:
                stripped_line = line.strip()
                
                # favorite_coins satırını güncelle
                if stripped_line.startswith("favorite_coins"):
                    if coin_names:
                        new_line = f"favorite_coins = {', '.join(coin_names)}\n"
                        updated_lines.append(new_line)
                        logging.info(f"Updated favorite_coins: {', '.join(coin_names)}")
                    else:
                        updated_lines.append(line)  # Coin yoksa mevcut satırı koru
                
                # dynamic_coin satırını güncelle
                elif stripped_line.startswith("dynamic_coin"):
                    if dynamic_coin_names:
                        # İlk dynamic coin'i al (genellikle tek bir dynamic coin var)
                        first_dynamic = dynamic_coin_names[0] if dynamic_coin_names else ""
                        new_line = f"dynamic_coin = {first_dynamic}\n"
                        updated_lines.append(new_line)
                        logging.info(f"Updated dynamic_coin: {first_dynamic}")
                    else:
                        updated_lines.append(line)  # Dynamic coin yoksa mevcut satırı koru
                
                else:
                    # Diğer satırları olduğu gibi koru
                    updated_lines.append(line)
            
            # Güncellenmiş preferences dosyasını yaz
            with open(PREFERENCES_FILE, 'w', encoding='utf-8') as f:
                f.writelines(updated_lines)
            
            logging.info("Preferences file updated successfully from JSON data")
            
        except Exception as e:
            logging.error(f"Error updating preferences from JSON: {e}")
    
    def refresh_ui_with_current_data(self):
        """Refresh UI elements with current preference data."""
        try:
            # Update preference input fields
            for key, edit in self.pref_edits.items():
                if key in self.original_prefs:
                    edit.setText(self.original_prefs[key])
                else:
                    edit.setText("")
            
            # Update interval input
            if self.interval_edit:
                interval_val = self.original_prefs.get("chart_interval", "1")
                self.interval_edit.setText(interval_val)
            
            # Update favorite coins - need to recreate the coin inputs
            if hasattr(self, 'coins_container_layout'):
                # Remove old coin inputs
                self._clear_favorite_coins_inputs()
                # Add new coin inputs based on current data
                self._recreate_favorite_coins_inputs()
            
            # Update dynamic coins - need to recreate the coin inputs
            if hasattr(self, 'dynamic_coins_container_layout'):
                # Remove old dynamic coin inputs
                self._clear_dynamic_coins_inputs()
                # Add new dynamic coin inputs based on current data
                self._recreate_dynamic_coins_inputs()
            
            logging.info("UI refreshed with current preference data")
            
        except Exception as e:
            logging.error(f"Error refreshing UI with current data: {e}")
    
    def setup_ui(self):
        """Set up the UI for the settings dialog."""
        try:
            # Main layout with compact spacing
            main_layout = QVBoxLayout(self)
            main_layout.setContentsMargins(15, 15, 15, 15)
            main_layout.setSpacing(8)
            
            # Create a grid layout for more compact organization
            content_layout = QGridLayout()
            content_layout.setSpacing(5)
            
            # Add input fields for specific preferences
            self._create_preference_inputs(content_layout)
            
            # Add coin chart interval setting
            self._create_interval_setting(content_layout)
            
            # Add grid layout to main layout
            main_layout.addLayout(content_layout)
            
            # Store reference to main layout for dynamic updates
            self.main_layout = main_layout
            
            # Add favorite coins inputs in a compact way
            self._create_favorite_coins_inputs(main_layout)
            
            # Add dynamic coins inputs as a separate section
            self._create_dynamic_coins_inputs(main_layout)
            
            # Add stretch to push save button to bottom
            main_layout.addStretch()
            
            # Add save button at bottom
            self._create_save_button(main_layout)
            
        except Exception as e:
            logging.error(f"Error setting up settings dialog UI: {e}")
    
    def position_dialog(self):
        """Position the dialog on the right-center of the screen."""
        try:
            # Get the screen geometry
            screen = QApplication.primaryScreen()
            screen_geometry = screen.availableGeometry()
            
            # Calculate position for right-center
            dialog_width = self.width()
            dialog_height = self.height()
            
            # Position on the right side with some margin from edge
            x = screen_geometry.width() - dialog_width - 50
            y = (screen_geometry.height() - dialog_height) // 2
            
            self.move(x, y)
            
        except Exception as e:
            logging.error(f"Error positioning dialog: {e}")
    
    def _create_preference_inputs(self, layout):
        """Create input fields for preferences using grid layout."""
        try:
            row = 0
            for key in ("soft_risk", "hard_risk", "accepted_price_volatility"):
                label = QLabel(key.replace("_", " ").title() + ":")
                label.setStyleSheet(SETTINGS_LABEL_STYLE)
                layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignRight)
                
                edit = QLineEdit(self.original_prefs.get(key, ""))
                edit.setStyleSheet(SETTINGS_INPUT_STYLE)
                edit.setMaximumHeight(25)  # Compact height
                self.pref_edits[key] = edit
                layout.addWidget(edit, row, 1)
                
                row += 1
                
        except Exception as e:
            logging.error(f"Error creating preference inputs: {e}")
    
    def _create_interval_setting(self, layout):
        """Create the chart interval setting using grid layout."""
        try:
            row = layout.rowCount()
            
            label = QLabel("Chart Interval:")
            label.setStyleSheet(SETTINGS_LABEL_STYLE)
            layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignRight)
            
            interval_val = self.original_prefs.get("chart_interval", "1")
            self.interval_edit = QLineEdit(interval_val)
            self.interval_edit.setStyleSheet(SETTINGS_INPUT_STYLE)
            self.interval_edit.setPlaceholderText("1, 5 or 15")
            self.interval_edit.setMaximumHeight(25)  # Compact height
            layout.addWidget(self.interval_edit, row, 1)
            
        except Exception as e:
            logging.error(f"Error creating interval setting: {e}")
    
    def _create_favorite_coins_inputs(self, layout):
        """Create input fields for favorite coins in a vertical centered layout."""
        try:
            # Create a label for favorite coins
            self.coins_label = QLabel("Favorite Coins:")
            self.coins_label.setStyleSheet(SETTINGS_LABEL_STYLE)
            layout.addWidget(self.coins_label)
            
            # Store layout reference for dynamic updates
            self.coins_container_layout = QVBoxLayout()
            layout.addLayout(self.coins_container_layout)
            
            # Create coin inputs
            self._recreate_favorite_coins_inputs()
            
        except Exception as e:
            logging.error(f"Error creating favorite coins inputs: {e}")
    
    def _recreate_favorite_coins_inputs(self):
        """Recreate favorite coin inputs with current data."""
        try:
            # Clear existing inputs
            self.fav_edits = []
            
            # Limit to maximum 5 favorite coins as per the preferences format
            coins_to_display = self.original_coins[:5] if len(self.original_coins) > 5 else self.original_coins
            
            # Create each coin input centered individually
            for coin in coins_to_display:
                # Create horizontal layout for centering each coin
                coin_layout = QHBoxLayout()
                coin_layout.addStretch()  # Left stretch for centering
                
                edit = QLineEdit(coin)
                edit.setStyleSheet(SETTINGS_INPUT_STYLE)
                edit.setMaximumHeight(25)  # Compact height
                edit.setMaximumWidth(80)   # Compact width for coins
                edit.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Center text in input
                self.fav_edits.append(edit)
                
                coin_layout.addWidget(edit)
                coin_layout.addStretch()  # Right stretch for centering
                
                self.coins_container_layout.addLayout(coin_layout)
            
            # If we have fewer than 5 coins, add empty inputs to make total 5
            while len(self.fav_edits) < 5:
                coin_layout = QHBoxLayout()
                coin_layout.addStretch()  # Left stretch for centering
                
                edit = QLineEdit("")
                edit.setStyleSheet(SETTINGS_INPUT_STYLE)
                edit.setMaximumHeight(25)  # Compact height
                edit.setMaximumWidth(80)   # Compact width for coins
                edit.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Center text in input
                edit.setPlaceholderText("COIN")
                self.fav_edits.append(edit)
                
                coin_layout.addWidget(edit)
                coin_layout.addStretch()  # Right stretch for centering
                
                self.coins_container_layout.addLayout(coin_layout)
                
        except Exception as e:
            logging.error(f"Error recreating favorite coins inputs: {e}")
    
    def _clear_favorite_coins_inputs(self):
        """Clear all favorite coin input widgets from the layout."""
        try:
            # Remove all widgets from coins container layout
            while self.coins_container_layout.count():
                child = self.coins_container_layout.takeAt(0)
                if child.layout():
                    # If it's a layout, delete all its widgets
                    while child.layout().count():
                        widget_item = child.layout().takeAt(0)
                        if widget_item.widget():
                            widget_item.widget().deleteLater()
                    child.layout().deleteLater()
                elif child.widget():
                    child.widget().deleteLater()
                    
        except Exception as e:
            logging.error(f"Error clearing favorite coins inputs: {e}")
    
    def _create_dynamic_coins_inputs(self, layout):
        """Create input fields for dynamic coins in a vertical centered layout."""
        try:
            # Create a label for dynamic coins
            self.dynamic_coins_label = QLabel("Dynamic Coins:")
            self.dynamic_coins_label.setStyleSheet(SETTINGS_LABEL_STYLE)
            layout.addWidget(self.dynamic_coins_label)
            
            # Store layout reference for dynamic updates
            self.dynamic_coins_container_layout = QVBoxLayout()
            layout.addLayout(self.dynamic_coins_container_layout)
            
            # Create dynamic coin inputs
            self._recreate_dynamic_coins_inputs()
            
        except Exception as e:
            logging.error(f"Error creating dynamic coins inputs: {e}")
    
    def _recreate_dynamic_coins_inputs(self):
        """Recreate dynamic coin inputs with current data."""
        try:
            # Clear existing inputs
            self.dynamic_edits = []
            
            # Create each dynamic coin input centered individually
            for coin in self.original_dynamic_coins:
                # Create horizontal layout for centering each coin
                coin_layout = QHBoxLayout()
                coin_layout.addStretch()  # Left stretch for centering
                
                edit = QLineEdit(coin)
                edit.setStyleSheet(SETTINGS_INPUT_STYLE)
                edit.setMaximumHeight(25)  # Compact height
                edit.setMaximumWidth(80)   # Compact width for coins
                edit.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Center text in input
                self.dynamic_edits.append(edit)
                
                coin_layout.addWidget(edit)
                coin_layout.addStretch()  # Right stretch for centering
                
                self.dynamic_coins_container_layout.addLayout(coin_layout)
            
            # If no dynamic coins, add an empty input for user to add one
            if not self.original_dynamic_coins:
                coin_layout = QHBoxLayout()
                coin_layout.addStretch()  # Left stretch for centering
                
                edit = QLineEdit("")
                edit.setStyleSheet(SETTINGS_INPUT_STYLE)
                edit.setMaximumHeight(25)  # Compact height
                edit.setMaximumWidth(80)   # Compact width for coins
                edit.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Center text in input
                edit.setPlaceholderText("COIN")
                self.dynamic_edits.append(edit)
                
                coin_layout.addWidget(edit)
                coin_layout.addStretch()  # Right stretch for centering
                
                self.dynamic_coins_container_layout.addLayout(coin_layout)
                
        except Exception as e:
            logging.error(f"Error recreating dynamic coins inputs: {e}")
    
    def _clear_dynamic_coins_inputs(self):
        """Clear all dynamic coin input widgets from the layout."""
        try:
            # Remove all widgets from dynamic coins container layout
            while self.dynamic_coins_container_layout.count():
                child = self.dynamic_coins_container_layout.takeAt(0)
                if child.layout():
                    # If it's a layout, delete all its widgets
                    while child.layout().count():
                        widget_item = child.layout().takeAt(0)
                        if widget_item.widget():
                            widget_item.widget().deleteLater()
                    child.layout().deleteLater()
                elif child.widget():
                    child.widget().deleteLater()
                    
        except Exception as e:
            logging.error(f"Error clearing dynamic coins inputs: {e}")
    
    def _create_save_button(self, layout):
        """Create the save button."""
        try:
            # Create a horizontal layout for the button
            button_layout = QHBoxLayout()
            button_layout.addStretch()
            
            btn_save = QPushButton("Save Settings")
            btn_save.setStyleSheet(SAVE_BUTTON_STYLE)
            btn_save.setMinimumHeight(30)
            btn_save.setMinimumWidth(120)
            btn_save.clicked.connect(self.save_settings)
            
            button_layout.addWidget(btn_save)
            button_layout.addStretch()
            
            layout.addLayout(button_layout)
            
        except Exception as e:
            logging.error(f"Error creating save button: {e}")
    
    def save_settings(self):
        """Save the updated settings and preferences."""
        try:
            messages = []
            coin_changes_detected = False
            
            # Update preferences if there are changes
            for key, edit in self.pref_edits.items():
                new_val = edit.text().strip()
                old_val = self.original_prefs.get(key, "")
                
                if new_val and new_val != old_val:
                    msg = set_preference(key, new_val)
                    messages.append(msg)
            
            # Validate and update chart interval
            if self.interval_edit:
                interval_val = self.interval_edit.text().strip()
                old_interval = self.original_prefs.get("chart_interval", "1")
                
                if interval_val not in ("1", "5", "15"):
                    QMessageBox.critical(self, "Invalid Interval", 
                                       "Interval must be 1, 5, or 15.")
                    return
                
                if interval_val != old_interval:
                    msg = set_preference("chart_interval", interval_val)
                    messages.append(msg)
            
            # Update favorite coins using efficient method (like submit button)
            new_favorite_coins = []
            for edit in self.fav_edits:
                coin_text = edit.text().strip().upper()
                if coin_text:  # Only add non-empty coins
                    new_favorite_coins.append(coin_text)
            
            # Compare with original coins to detect changes
            if set(new_favorite_coins) != set(self.original_coins):
                self._update_favorite_coins_efficiently(new_favorite_coins, messages)
                coin_changes_detected = True
            
            # Update dynamic coins using efficient method (like submit button)
            new_dynamic_coins = []
            for edit in self.dynamic_edits:
                coin_text = edit.text().strip().upper()
                if coin_text:  # Only add non-empty coins
                    new_dynamic_coins.append(coin_text)
            
            # Compare with original dynamic coins to detect changes
            if set(new_dynamic_coins) != set(self.original_dynamic_coins):
                self._update_dynamic_coins_efficiently(new_dynamic_coins, messages)
                coin_changes_detected = True
            
            # Note: No WebSocket restart needed - individual coin subscriptions are handled efficiently
            if coin_changes_detected:
                # Log the subscription update message instead of showing it to user
                logging.info("✅ Coin subscriptions updated automatically")
            
            # Show result to user
            if messages:
                combined_message = "\n".join(messages)
                self.settings_saved.emit(combined_message)
                logging.info(f"Settings saved: {combined_message}")
            else:
                logging.info("No changes were detected to save.")
            
            # Close the settings window after saving
            self.accept()
            
        except Exception as e:
            error_msg = f"Error saving settings: {e}"
            logging.error(error_msg)
            QMessageBox.critical(self, "Save Error", error_msg)
    
    def _update_favorite_coins_efficiently(self, new_coins, messages):
        """Update favorite coins using efficient method similar to submit button."""
        try:
            # Import here to avoid circular imports
            from utils.data_utils import load_fav_coins, write_favorite_coins_to_json
            
            validated_coins = []
            
            # Validate each coin using the same method as submit button
            for coin_input in new_coins:
                result = process_user_coin_input(coin_input)
                if result['success']:
                    # Extract base symbol (remove -USDT suffix for name)
                    base_symbol = result['view_coin_name'].replace('-USDT', '')
                    validated_coins.append({
                        'name': base_symbol,  # Store as BTC, not BTC-USDT
                        'symbol': result['binance_ticker'],
                        'original_input': result['original_input']
                    })
                    logging.info(f"Validated favorite coin: {coin_input} -> {base_symbol} ({result['binance_ticker']})")
                else:
                    messages.append(f"❌ Failed to set coin {coin_input}: {result['error_message']}")
                    logging.warning(f"Invalid favorite coin {coin_input}: {result['error_message']}")
            
            if validated_coins:
                # Update JSON file directly (like submit button does)
                data = load_fav_coins()
                
                # Ensure we have exactly 5 favorite coins (pad with empty or truncate)
                while len(validated_coins) < 5:
                    validated_coins.append({
                        'name': '',
                        'symbol': '',
                        'values': {'current': 0.0, '15_min_ago': '0.00'}
                    })
                validated_coins = validated_coins[:5]  # Limit to 5
                
                # Add values for each coin
                for coin in validated_coins:
                    if coin['name']:  # Only for non-empty coins
                        coin['values'] = {'current': 0.0, '15_min_ago': '0.00'}
                
                data['coins'] = validated_coins
                write_favorite_coins_to_json(data)
                
                # Update preferences file
                coin_names = [coin['name'] for coin in validated_coins if coin['name']]
                if coin_names:
                    new_coins_str = ", ".join(coin_names)
                    msg = set_preference("favorite_coins", new_coins_str)
                    messages.append(msg)
                    
                    # Subscribe to new coins via WebSocket (no restart needed)
                    self._subscribe_to_new_coins([coin['symbol'] for coin in validated_coins if coin['symbol']])
                    
                    logging.info(f"Efficiently updated favorite coins: {new_coins_str}")
                else:
                    msg = set_preference("favorite_coins", "")
                    messages.append(msg)
                    logging.info("Cleared all favorite coins")
            
        except Exception as e:
            error_msg = f"Error updating favorite coins efficiently: {e}"
            logging.error(error_msg)
            messages.append(f"❌ {error_msg}")
    
    def _update_dynamic_coins_efficiently(self, new_dynamic_coins, messages):
        """Update dynamic coin using efficient method like submit button."""
        try:
            if new_dynamic_coins:
                # Take the first dynamic coin (typically there's only one)
                first_dynamic = new_dynamic_coins[0]
                
                # Use the same method as submit button
                result = set_dynamic_coin_symbol(first_dynamic)
                if result and result.get('success'):
                    binance_ticker = result.get('binance_ticker')
                    view_coin_name = result.get('view_coin_name')
                    # Extract base symbol for display
                    base_symbol = view_coin_name.replace('-USDT', '') if view_coin_name else first_dynamic
                    
                    # Subscribe to dynamic coin (efficient - no WebSocket restart)
                    subscribe_to_dynamic_coin(binance_ticker)
                    
                    # Update preferences file (log the message instead of showing to user)
                    msg = set_preference("dynamic_coin", first_dynamic.upper())
                    logging.info(msg)  # Log the set_preference message
                    
                    # Only show the main update message to user
                    messages.append(f"✅ New coin submitted: {first_dynamic} -> {base_symbol} ({binance_ticker})")
                    
                    logging.info(f"Efficiently updated dynamic coin: {first_dynamic} -> {base_symbol} ({binance_ticker})")
                else:
                    error_msg = result.get('error_message', 'Unknown error') if result else 'Failed to set coin'
                    messages.append(f"❌ Failed to set coin {first_dynamic}: {error_msg}")
                    logging.warning(f"Failed to set dynamic coin {first_dynamic}: {error_msg}")
            else:
                # Clear dynamic coin
                msg = set_preference("dynamic_coin", "")
                messages.append(msg)
                logging.info("Cleared dynamic coin")
                
        except Exception as e:
            error_msg = f"Error updating dynamic coin efficiently: {e}"
            logging.error(error_msg)
            messages.append(f"❌ {error_msg}")
    
    def _subscribe_to_new_coins(self, binance_tickers):
        """Subscribe to new favorite coins via WebSocket (efficient method)."""
        try:
            # Import here to avoid circular imports
            from services.live_price_service import ws, connection_active, pending_subscriptions
            import json
            
            if ws and connection_active:
                for ticker in binance_tickers:
                    if ticker:  # Only for non-empty tickers
                        ticker_symbol = f"{ticker.lower().replace('usdt', '')}usdt@ticker"
                        try:
                            ws.send(json.dumps({
                                "method": "SUBSCRIBE",
                                "params": [ticker_symbol],
                                "id": len(pending_subscriptions) + 1
                            }))
                            logging.info(f"Subscribed to new favorite coin: {ticker_symbol}")
                        except Exception as e:
                            logging.error(f"Error subscribing to {ticker_symbol}: {e}")
            else:
                logging.warning("WebSocket not active, coins updated but not subscribed yet")
                
        except Exception as e:
            logging.error(f"Error subscribing to new coins: {e}")
