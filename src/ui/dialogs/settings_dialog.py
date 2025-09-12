"""
Settings Dialog Component.
Manages the application settings window.
"""

import logging
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox,
    QHBoxLayout, QApplication, QGridLayout, QComboBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIntValidator, QDoubleValidator

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
        self.setFixedSize(350, 640)  # Increased height for risk type inputs
        self.setStyleSheet(SETTINGS_DIALOG_STYLE)
        
        self.original_prefs = {}
        self.original_coins = []
        self.original_dynamic_coins = []  # Dynamic coins'ler için
        self.pref_edits = {}
        self.fav_edits = []
        self.dynamic_edits = []  # Dynamic coin input'ları için
        self.interval_edit = None
        self.order_type_combo = None  # Order type combo box
        self.risk_type_combo = None  # Risk type combo box
        self.risk_edits = {}  # Risk input fields
        
        self.load_preferences()
        self.setup_ui()
        self.position_dialog()
    
    def showEvent(self, event):
        """Override showEvent to reload preferences every time dialog is shown."""
        super().showEvent(event)
        try:
            # Her dialog açıldığında JSON'dan coinleri al ve preferences'ı güncelle
            logging.debug("Settings dialog opened - updating preferences from JSON...")
            self._update_preferences_from_json()
            self.load_preferences()
            self.refresh_ui_with_current_data()
            logging.debug("Settings dialog refreshed with current preferences")
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
            
            # Load dynamic coins from fav_coins.json - only log during initial load
            self._load_dynamic_coins(force_log=(not hasattr(self, 'original_dynamic_coins')))
            
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
    
    def _load_dynamic_coins(self, force_log=False):
        """Load dynamic coins from fav_coins.json file."""
        try:
            # fav_coins.json dosyasının path'ini oluştur
            config_dir = os.path.dirname(PREFERENCES_FILE)
            fav_coins_file = os.path.join(config_dir, "fav_coins.json")
            
            previous_dynamic_coins = self.original_dynamic_coins.copy() if hasattr(self, 'original_dynamic_coins') else []
            
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
                    
                    # Only log if there are changes or if forced
                    if force_log or set(previous_dynamic_coins) != set(self.original_dynamic_coins):
                        if self.original_dynamic_coins:
                            logging.info(f"Loaded {len(self.original_dynamic_coins)} dynamic coins: {self.original_dynamic_coins}")
                        else:
                            logging.info("No dynamic coins loaded")
            else:
                self.original_dynamic_coins = []
                if force_log or previous_dynamic_coins:  # Only log if there was a change
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
            dynamic_updated = False
            
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
                
                # dynamic_coin satırını güncelle (duplikasyonu önle)
                elif stripped_line.startswith("dynamic_coin") and not dynamic_updated:
                    if dynamic_coin_names:
                        first_dynamic = dynamic_coin_names[0]
                        new_line = f"dynamic_coin = {first_dynamic}\n"
                        updated_lines.append(new_line)
                        logging.info(f"Updated dynamic_coin: {first_dynamic}")
                    else:
                        updated_lines.append(line)
                    dynamic_updated = True
                
                elif not (stripped_line.startswith("dynamic_coin") and dynamic_updated):
                    # Diğer satırları olduğu gibi koru (duplikasyon hariç)
                    updated_lines.append(line)
            
            # Güncellenmiş preferences dosyasını yaz
            with open(PREFERENCES_FILE, 'w', encoding='utf-8') as f:
                f.writelines(updated_lines)
            
            logging.debug("Preferences file updated successfully from JSON data")
            
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
            
            # Update risk input fields
            for key, edit in self.risk_edits.items():
                if key in self.original_prefs:
                    value = self.original_prefs[key]
                    # Clean formatting for display
                    if key in ["soft_risk_percentage", "hard_risk_percentage"]:
                        value = value.replace("%", "")
                    elif key in ["soft_risk_by_usdt", "hard_risk_by_usdt"]:
                        value = value.replace("USDT", "")
                    edit.setText(value)
                else:
                    edit.setText("")
            
            # Update interval input
            if self.interval_edit:
                interval_val = self.original_prefs.get("chart_interval", "1")
                self.interval_edit.setText(interval_val)
            
            # Update order type combo
            if self.order_type_combo:
                order_type_val = self.original_prefs.get("order_type", "MARKET")
                index = self.order_type_combo.findText(order_type_val)
                if index >= 0:
                    self.order_type_combo.setCurrentIndex(index)
            
            # Update risk type combo
            if self.risk_type_combo:
                risk_type_val = self.original_prefs.get("risk_type", "PERCENTAGE")
                index = self.risk_type_combo.findText(risk_type_val)
                if index >= 0:
                    self.risk_type_combo.setCurrentIndex(index)
            
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
            
            logging.debug("UI refreshed with current preference data")
            
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
            
            # Add order type setting for dynamic coin
            self._create_order_type_setting(content_layout)
            
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
            
            # Risk Type Selection
            label = QLabel("Risk Type:")
            label.setStyleSheet(SETTINGS_LABEL_STYLE)
            layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignRight)
            
            risk_type_val = self.original_prefs.get("risk_type", "PERCENTAGE")
            self.risk_type_combo = QComboBox()
            self.risk_type_combo.addItems(["PERCENTAGE", "USDT"])
            self.risk_type_combo.setCurrentText(risk_type_val)
            self.risk_type_combo.setStyleSheet(SETTINGS_INPUT_STYLE)
            self.risk_type_combo.setMaximumHeight(25)
            layout.addWidget(self.risk_type_combo, row, 1)
            row += 1
            
            # Soft Risk (Percentage)
            label = QLabel("Soft Risk (%):")
            label.setStyleSheet(SETTINGS_LABEL_STYLE)
            layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignRight)
            
            soft_risk_val = self.original_prefs.get("soft_risk_percentage", "").replace("%", "")
            edit = QLineEdit(soft_risk_val)
            edit.setStyleSheet(SETTINGS_INPUT_STYLE)
            edit.setMaximumHeight(25)
            edit.setPlaceholderText("20")
            # Add number validation (0-100 for percentage)
            validator = QIntValidator(0, 100)
            edit.setValidator(validator)
            self.risk_edits["soft_risk_percentage"] = edit
            layout.addWidget(edit, row, 1)
            row += 1
            
            # Hard Risk (Percentage)
            label = QLabel("Hard Risk (%):")
            label.setStyleSheet(SETTINGS_LABEL_STYLE)
            layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignRight)
            
            hard_risk_val = self.original_prefs.get("hard_risk_percentage", "").replace("%", "")
            edit = QLineEdit(hard_risk_val)
            edit.setStyleSheet(SETTINGS_INPUT_STYLE)
            edit.setMaximumHeight(25)
            edit.setPlaceholderText("35")
            # Add number validation (0-100 for percentage)
            validator = QIntValidator(0, 100)
            edit.setValidator(validator)
            self.risk_edits["hard_risk_percentage"] = edit
            layout.addWidget(edit, row, 1)
            row += 1
            
            # Soft Risk (USDT)
            label = QLabel("Soft Risk (USDT):")
            label.setStyleSheet(SETTINGS_LABEL_STYLE)
            layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignRight)
            
            soft_risk_usdt_val = self.original_prefs.get("soft_risk_by_usdt", "").replace("USDT", "")
            edit = QLineEdit(soft_risk_usdt_val)
            edit.setStyleSheet(SETTINGS_INPUT_STYLE)
            edit.setMaximumHeight(25)
            edit.setPlaceholderText("15")
            # Add number validation (0-999999 for USDT amounts)
            validator = QDoubleValidator(0.0, 999999.99, 2)
            edit.setValidator(validator)
            self.risk_edits["soft_risk_by_usdt"] = edit
            layout.addWidget(edit, row, 1)
            row += 1
            
            # Hard Risk (USDT)
            label = QLabel("Hard Risk (USDT):")
            label.setStyleSheet(SETTINGS_LABEL_STYLE)
            layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignRight)
            
            hard_risk_usdt_val = self.original_prefs.get("hard_risk_by_usdt", "").replace("USDT", "")
            edit = QLineEdit(hard_risk_usdt_val)
            edit.setStyleSheet(SETTINGS_INPUT_STYLE)
            edit.setMaximumHeight(25)
            edit.setPlaceholderText("20")
            # Add number validation (0-999999 for USDT amounts)
            validator = QDoubleValidator(0.0, 999999.99, 2)
            edit.setValidator(validator)
            self.risk_edits["hard_risk_by_usdt"] = edit
            layout.addWidget(edit, row, 1)
            row += 1
            
            # Accepted Price Volatility
            label = QLabel("Accepted Price Volatility:")
            label.setStyleSheet(SETTINGS_LABEL_STYLE)
            layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignRight)
            
            volatility_val = self.original_prefs.get("accepted_price_volatility", "").replace("%", "")
            edit = QLineEdit(volatility_val)
            edit.setStyleSheet(SETTINGS_INPUT_STYLE)
            edit.setMaximumHeight(25)
            edit.setPlaceholderText("3")
            # Add number validation (0-100 for percentage)
            validator = QIntValidator(0, 100)
            edit.setValidator(validator)
            self.pref_edits["accepted_price_volatility"] = edit
            layout.addWidget(edit, row, 1)
                
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
            # Add validation for specific values
            self.interval_edit.setToolTip("Only 1, 5, or 15 are allowed")
            layout.addWidget(self.interval_edit, row, 1)
            
        except Exception as e:
            logging.error(f"Error creating interval setting: {e}")
    
    def _create_order_type_setting(self, layout):
        """Create the order type setting for dynamic coin trading using grid layout."""
        try:
            row = layout.rowCount()
            
            label = QLabel("Order Type:")
            label.setStyleSheet(SETTINGS_LABEL_STYLE)
            layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignRight)
            
            # Doğru key kullan: "order_type" (preferences.txt'deki ile aynı)
            order_type_val = self.original_prefs.get("order_type", "MARKET")
            self.order_type_combo = QComboBox()
            self.order_type_combo.addItems(["MARKET", "LIMIT"])
            self.order_type_combo.setCurrentText(order_type_val)
            self.order_type_combo.setStyleSheet(SETTINGS_INPUT_STYLE)
            self.order_type_combo.setMaximumHeight(25)  # Compact height
            
            # Order type will be saved only when Save Settings button is clicked
            # No immediate save on change - removed currentTextChanged connection
            
            layout.addWidget(self.order_type_combo, row, 1)
            
        except Exception as e:
            logging.error(f"Error creating order type setting: {e}")
    
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
                old_val = self.original_prefs.get(key, "").replace("%", "")
                
                if new_val and new_val != old_val:
                    # Validate numeric input for volatility
                    if key == "accepted_price_volatility":
                        try:
                            num_val = float(new_val)
                            if not (0 <= num_val <= 100):
                                QMessageBox.critical(self, "Invalid Value", 
                                                   "Price Volatility: Percentage must be between 0-100")
                                return
                            formatted_val = f"%{int(num_val)}"
                        except ValueError:
                            QMessageBox.critical(self, "Invalid Value", 
                                               "Price Volatility: Please enter only numbers")
                            return
                    else:
                        formatted_val = new_val
                    
                    msg = set_preference(key, formatted_val)
                    # Only add message if it indicates an actual change was made
                    if not msg.endswith("already set to " + formatted_val):
                        messages.append(msg)
            
            # Update risk preferences with proper formatting and validation
            for key, edit in self.risk_edits.items():
                new_val = edit.text().strip()
                if not new_val:
                    continue
                
                # Validate that value is numeric
                try:
                    if key in ["soft_risk_percentage", "hard_risk_percentage"]:
                        # Validate percentage (0-100)
                        num_val = float(new_val)
                        if not (0 <= num_val <= 100):
                            QMessageBox.critical(self, "Invalid Value", 
                                               f"{key.replace('_', ' ').title()}: Percentage must be between 0-100")
                            return
                        formatted_val = f"%{int(num_val)}"
                    elif key in ["soft_risk_by_usdt", "hard_risk_by_usdt"]:
                        # Validate USDT amount (positive number)
                        num_val = float(new_val)
                        if num_val <= 0:
                            QMessageBox.critical(self, "Invalid Value", 
                                               f"{key.replace('_', ' ').title()}: USDT amount must be greater than 0")
                            return
                        formatted_val = f"{num_val:g}USDT"  # Remove unnecessary decimals
                    else:
                        formatted_val = new_val
                        
                except ValueError:
                    QMessageBox.critical(self, "Invalid Value", 
                                       f"{key.replace('_', ' ').title()}: Please enter only numbers")
                    return
                
                # Compare with original
                old_val = self.original_prefs.get(key, "")
                # For percentage values, ensure we compare properly (old_val doesn't have %)
                if key in ["soft_risk_percentage", "hard_risk_percentage"]:
                    old_val_with_percent = f"%{old_val}" if old_val else ""
                    if formatted_val != old_val_with_percent:
                        msg = set_preference(key, formatted_val)
                        # Only add message if it indicates an actual change was made
                        if not msg.endswith("already set to " + formatted_val):
                            messages.append(msg)
                elif key in ["soft_risk_by_usdt", "hard_risk_by_usdt"]:
                    old_val_with_usdt = f"{old_val}USDT" if old_val else ""
                    if formatted_val != old_val_with_usdt:
                        msg = set_preference(key, formatted_val)
                        # Only add message if it indicates an actual change was made
                        if not msg.endswith("already set to " + formatted_val):
                            messages.append(msg)
                else:
                    if formatted_val != old_val:
                        msg = set_preference(key, formatted_val)
                        # Only add message if it indicates an actual change was made
                        if not msg.endswith("already set to " + formatted_val):
                            messages.append(msg)
            
            # Update risk type if changed
            if self.risk_type_combo:
                risk_type_val = self.risk_type_combo.currentText()
                old_risk_type = self.original_prefs.get("risk_type", "PERCENTAGE")
                
                if risk_type_val != old_risk_type:
                    msg = set_preference("risk_type", risk_type_val)
                    # Only add message if it indicates an actual change was made
                    if not msg.endswith("already set to " + risk_type_val):
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
                    # Only add message if it indicates an actual change was made
                    if not msg.endswith("already set to " + interval_val):
                        messages.append(msg)
            
            # Update order type preference
            if self.order_type_combo:
                order_type_val = self.order_type_combo.currentText()
                old_order_type = self.original_prefs.get("order_type", "MARKET")
                
                if order_type_val not in ("MARKET", "LIMIT"):
                    QMessageBox.critical(self, "Invalid Order Type", 
                                       "Order type must be MARKET or LIMIT.")
                    return
                
                if order_type_val != old_order_type:
                    msg = set_preference("order_type", order_type_val)
                    # Check for various success indicators
                    if not (msg.endswith("already set to " + order_type_val) or "already set" in msg):
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
                    
                    # WebSocket subscriptions are handled automatically by the live price service
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

