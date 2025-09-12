"""
Main Window - Modular Structure
This file now only handles layout coordination and component integration.
All UI components are separated into their own modules for better organization.
"""

import json
import sys
import os
import logging
import threading

# Add project paths
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(src_dir)

# Import centralized paths
from core.paths import FAV_COINS_FILE, BTC_ICON_FILE, FAVORITE_COIN_COUNT, DYNAMIC_COIN_INDEX

# Import services
from services.client_service import prepare_client
from services.account_service import retrieve_usdt_balance
from services.orders.order_service import make_order
from utils.data_utils import load_fav_coins
from utils.symbol_utils import view_coin_format
from services.live_price_service import (
    set_dynamic_coin_symbol,
    start_price_websocket, 
    subscribe_to_dynamic_coin
)

# Import components
from ui.components import (
    FavoriteCoinPanel, DynamicCoinPanel, WalletPanel, 
    CoinEntryPanel, TerminalWidget
)
from ui.components.chart_widget import get_chart_data
from ui.dialogs.settings_dialog import SettingsDialog

# Chart imports
import matplotlib.pyplot as plt
import mplfinance as mpf

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QMessageBox
)
from PySide6.QtGui import QIcon, QKeyEvent
from PySide6.QtCore import Qt, QTimer


class MainWindow(QMainWindow):
    """
    Main window using modular component architecture.
    Handles only layout coordination and component integration.
    """
    
    def __init__(self, client):
        """Initialize the main window with modular components."""
        super().__init__()
        
        try:
            logging.info("MainWindow: Starting modular initialization...")
            
            # Set window properties
            self.setWindowFlags(Qt.Window)
            self.client = client
            self.setWindowTitle("GAIN")
            
            # WebSocket restart kontrolü için flag
            self.websocket_restarting = False
            
            # Set window size and position
            self._setup_window_geometry()
            
            # Set application icon
            self.setup_application_icon()
            
            # Initialize components
            self._init_components()
            
            # Setup UI layout
            self.setup_ui()
            
            # Setup timers
            self.setup_timers()
            
            logging.info("MainWindow: Modular initialization completed successfully")
            
        except Exception as e:
            logging.exception(f"MainWindow: Error during initialization: {e}")
            self._create_error_interface(e)
    
    def _setup_window_geometry(self):
        """Setup window size and position."""
        try:
            screen = QApplication.primaryScreen().geometry()
            win_w, win_h = 750, 450
            center_x = screen.x() + (screen.width() - win_w) // 2
            center_y = screen.y() + (screen.height() - win_h) // 2
            offset_x = 200
            offset_y = 100
            self.move(center_x - offset_x, center_y - offset_y)
            self.resize(win_w, win_h)
        except Exception as e:
            logging.error(f"Error setting window geometry: {e}")
    
    def _init_components(self):
        """Initialize all UI components."""
        try:
            # Create components
            self.fav_coin_panel = FavoriteCoinPanel()
            self.dynamic_coin_panel = DynamicCoinPanel()
            self.wallet_panel = WalletPanel()
            self.coin_entry_panel = CoinEntryPanel()
            self.terminal_widget = TerminalWidget()
            
            # Connect component signals
            self._connect_component_signals()
            
            logging.debug("All components initialized successfully")
            
        except Exception as e:
            logging.error(f"Error initializing components: {e}")
            raise
    
    def _connect_component_signals(self):
        """Connect signals from all components."""
        try:
            # Favorite coins panel signals
            self.fav_coin_panel.order_requested.connect(self._handle_order_request)
            self.fav_coin_panel.coin_details_requested.connect(self._handle_coin_details)
            self.fav_coin_panel.error_occurred.connect(self.terminal_widget.append_message)
            
            # Dynamic coin panel signals
            self.dynamic_coin_panel.order_requested.connect(self._handle_order_request)
            self.dynamic_coin_panel.coin_details_requested.connect(self._handle_coin_details)
            self.dynamic_coin_panel.error_occurred.connect(self.terminal_widget.append_message)
            
            # Wallet panel signals
            self.wallet_panel.settings_requested.connect(self._handle_settings_request)
            self.wallet_panel.error_occurred.connect(self.terminal_widget.append_message)
            
            # Coin entry panel signals
            self.coin_entry_panel.coin_submitted.connect(self._handle_coin_submission)
            self.coin_entry_panel.error_occurred.connect(self.terminal_widget.append_message)
            
            # Setup favorites update callback
            self._setup_favorites_callback()
            
            logging.debug("Component signals connected successfully")
            
        except Exception as e:
            logging.error(f"Error connecting component signals: {e}")
    
    def _setup_favorites_callback(self):
        """Setup callback for favorites updates."""
        try:
            from config.preferences_service import set_favorites_update_callback
            set_favorites_update_callback(self.refresh_favorites)
            logging.debug("Favorites update callback registered successfully")
        except ImportError as e:
            logging.warning(f"Could not import preferences_service: {e}")
        except Exception as e:
            logging.error(f"Error setting up favorites callback: {e}")
    
    def setup_application_icon(self):
        """Setup application and window icon."""
        try:
            if os.path.exists(BTC_ICON_FILE):
                icon = QIcon(BTC_ICON_FILE)
                self.setWindowIcon(icon)
                
                app = QApplication.instance()
                if app:
                    app.setWindowIcon(icon)
                
                logging.info(f"Application icon set: {BTC_ICON_FILE}")
            else:
                logging.warning(f"Icon file not found: {BTC_ICON_FILE}")
                
        except Exception as e:
            logging.error(f"Error setting application icon: {e}")
    
    def setup_ui(self):
        """Setup the main UI layout using components."""
        try:
            # Create central widget and main layout
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            main_layout = QVBoxLayout(central_widget)
            main_layout.setContentsMargins(5, 5, 5, 5)
            main_layout.setSpacing(4)
            
            # Setup top section with panels
            self._setup_top_section(main_layout)
            
            # Add terminal at bottom
            main_layout.addWidget(self.terminal_widget)
            
            logging.debug("Main UI layout setup completed")
            
        except Exception as e:
            logging.error(f"Error setting up UI: {e}")
    
    def _setup_top_section(self, main_layout):
        """Setup the top section with all panels."""
        try:
            top_layout = QHBoxLayout()
            main_layout.addLayout(top_layout)
            
            # Add favorite coins panel
            top_layout.addWidget(self.fav_coin_panel.get_widget())
            
            # Add dynamic coin panel
            top_layout.addWidget(self.dynamic_coin_panel.get_widget())
            
            # Add right side panels
            self._setup_right_side_panels(top_layout)
            
        except Exception as e:
            logging.error(f"Error setting up top section: {e}")
    
    def _setup_right_side_panels(self, top_layout):
        """Setup the right side panels (wallet and coin entry)."""
        try:
            right_side_layout = QVBoxLayout()
            right_side_layout.setSpacing(5)
            
            # Add wallet panel
            right_side_layout.addWidget(self.wallet_panel.get_widget())
            
            # Add coin entry panel
            right_side_layout.addWidget(self.coin_entry_panel.get_widget())
            
            top_layout.addLayout(right_side_layout)
            
        except Exception as e:
            logging.error(f"Error setting up right side panels: {e}")
    
    def setup_timers(self):
        """Setup update timers."""
        try:
            # Timer to update coin prices every second
            self.price_timer = QTimer(self)
            self.price_timer.timeout.connect(self.update_coin_prices)
            self.price_timer.start(1000)
            
            # Timer to update wallet balance every second
            self.wallet_timer = QTimer(self)
            self.wallet_timer.timeout.connect(self.update_wallet)
            self.wallet_timer.start(1000)
            
            logging.debug("Timers setup completed")
            
        except Exception as e:
            logging.error(f"Error setting up timers: {e}")
    
    def _handle_order_request(self, operation_type, coin_index):
        """Handle order requests from components."""
        try:
            # Validate coin index before proceeding
            data = load_fav_coins()
            max_coin_index = len(data.get('coins', [])) - 1
            
            if coin_index != DYNAMIC_COIN_INDEX and coin_index > max_coin_index:
                error_msg = f"Invalid coin index {coin_index}. Max available: {max_coin_index}"
                logging.error(error_msg)
                self.terminal_widget.append_message(f"❌ {error_msg}")
                return
            
            symbol = self._retrieve_coin_symbol(coin_index)
            if not symbol:
                error_msg = f"Could not retrieve valid symbol for coin {coin_index}"
                logging.error(error_msg)
                self.terminal_widget.append_message(f"❌ {error_msg}")
                return
                
            old_balance = retrieve_usdt_balance(self.client)
            
            # Get order type preference from settings - applies to all coins
            from config.preferences_service import get_order_type_preference
            order_type = get_order_type_preference()
            
            # Log which coin type and order type is being used
            if coin_index == DYNAMIC_COIN_INDEX:
                logging.info(f"Using {order_type} order type for dynamic coin {symbol}")
            else:
                logging.info(f"Using {order_type} order type for favorite coin {symbol}")
            
            # Terminal callback function to send messages to terminal widget
            def terminal_callback(message):
                if hasattr(self, 'terminal_widget'):
                    self.terminal_widget.append_message(message)

            order_paper = make_order(
                Style=operation_type, 
                Symbol=symbol, 
                order_type=order_type, 
                limit_price=None, 
                amount_or_percentage=None,  # Will use preferences default
                amount_type='percentage',   # Default to percentage
                terminal_callback=terminal_callback
            )
            # Log the order response for debugging
            logging.debug(f"Order response for {operation_type} {symbol}: {order_paper}")

            # Handle both filled and unfilled orders safely
            try:
                if order_paper.get('fills') and len(order_paper['fills']) > 0:
                    # Order was filled (market orders or immediately filled limit orders)
                    amount = float(order_paper['fills'][0]['qty'])
                    price = float(order_paper['fills'][0]['price'])
                    cost_or_received = float(order_paper.get('cummulativeQuoteQty', amount * price))
                    logging.debug(f"Using filled order data: amount={amount}, price={price}, cost={cost_or_received}")
                else:
                    # Order not filled yet (limit orders waiting to be filled)
                    amount = float(order_paper.get('origQty', 0))
                    price = float(order_paper.get('price', 0))
                    cost_or_received = amount * price
                    logging.info(f"Limit order placed but not filled yet: {amount} {symbol} @ ${price}")
            except (ValueError, KeyError, TypeError) as parse_error:
                logging.error(f"Error parsing order response: {parse_error}")
                logging.error(f"Order response structure: {order_paper}")
                # Use fallback values
                amount = 0.0
                price = 0.0
                cost_or_received = 0.0
            
            new_balance = retrieve_usdt_balance(self.client)

            if "Buy" in operation_type:
                actual_diff = old_balance - new_balance
            else:
                actual_diff = new_balance - old_balance

            operation = "BUY" if "Buy" in operation_type else "SELL"
            action_type = "H" if "Hard" in operation_type else "S"
            
            # Send message to terminal
            try:
                status = "FILLED" if order_paper.get('fills') and len(order_paper['fills']) > 0 else order_paper.get('status', 'PENDING')
                # Use more decimal places for amount to show small cryptocurrency quantities correctly
                amount_str = f"{amount:.5f}".rstrip('0').rstrip('.')
                message = (f"[{action_type}] {operation} {symbol} | "
                          f"{amount_str} @ ${price:.2f} | "
                          f"Total: ${cost_or_received:.2f} | "
                          f"Balance: ${new_balance:.2f} | "
                          f"Order Type: {order_type} | Status: {status}")
                self.terminal_widget.append_message(message)
            except Exception as msg_error:
                logging.error(f"Error creating terminal message: {msg_error}")
                fallback_msg = f"[{action_type}] {operation} {symbol} completed | Balance: ${new_balance:.2f}"
                self.terminal_widget.append_message(fallback_msg)
            
        except Exception as e:
            error_msg = f"Error processing {operation_type} for coin {coin_index}: {e}"
            self.terminal_widget.append_message(error_msg)
            logging.error(error_msg)
            
            # Additional debugging info
            try:
                data = load_fav_coins()
                coin_count = len(data.get('coins', []))
                logging.error(f"Debug info - Current coin count: {coin_count}, Requested index: {coin_index}")
                logging.error(f"Debug info - Available coins: {[coin.get('name', 'Unknown') for coin in data.get('coins', [])]}")
            except Exception as debug_e:
                logging.error(f"Debug info - Could not load coin data for debugging: {debug_e}")
    
    def _handle_coin_details(self, coin_button):
        """Handle coin details requests from components."""
        try:
            display_symbol = coin_button.text().split("\n")[0]
            symbol = display_symbol.replace('-', '') if '-' in display_symbol else display_symbol
            
            # Get chart interval from preferences
            from core.paths import PREFERENCES_FILE
            interval = "1"
            try:
                with open(PREFERENCES_FILE, 'r') as f:
                    for line in f:
                        if line.strip().startswith("chart_interval"):
                            interval = line.split("=", 1)[1].strip().lstrip('%')
                            break
            except Exception:
                interval = "1"
            
            # Generate and show chart
            self._show_coin_chart(symbol, interval)
            
        except Exception as e:
            error_msg = f"Error displaying chart: {e}"
            self.terminal_widget.append_message(error_msg)
            logging.error(error_msg)
    
    def _show_coin_chart(self, symbol, interval):
        """Show candlestick chart for a coin."""
        try:
            df = get_chart_data(symbol)
            first_price = df["Close"].iloc[0]
            last_price = df["Close"].iloc[-1]
            price_change_pct = ((last_price - first_price) / first_price) * 100

            plt.style.use('dark_background')

            # Configure candlestick chart style
            mc = mpf.make_marketcolors(up='green', down='red', edge='inherit', wick='inherit')
            s = mpf.make_mpf_style(base_mpf_style='nightclouds', marketcolors=mc)

            # Generate candlestick chart
            fig, axlist = mpf.plot(
                df, type='candle', style=s, returnfig=True,
                datetime_format='%H:%M:%S', xrotation=45
            )
            ax = axlist[0]

            # Add title and adjust figure size
            fig.suptitle(f"{symbol} ({interval}m) Candle Chart", fontsize=12)
            fig.set_size_inches(6, 4)

            # Add general info box with price details
            info_text = (f"First Price: {first_price:.2f}\n"
                        f"Last Price: {last_price:.2f}\n"
                        f"Overall Change: {price_change_pct:.2f}%")
            props = dict(boxstyle='round', facecolor='gray', alpha=0.5)
            ax.text(0.02, 0.98, info_text, transform=ax.transAxes, fontsize=8,
                   verticalalignment='top', bbox=props)

            plt.show()
            
        except Exception as e:
            raise Exception(f"Chart generation failed for {symbol}: {e}")
    
    def _handle_settings_request(self):
        """Handle settings dialog request."""
        try:
            dialog = SettingsDialog(self)
            dialog.settings_saved.connect(self.terminal_widget.append_message)
            dialog.exec()
        except Exception as e:
            error_msg = f"Error opening settings: {e}"
            self.terminal_widget.append_message(error_msg)
            logging.error(error_msg)
    
    def _handle_coin_submission(self, coin_name):
        """Handle coin submission from entry panel."""
        try:
            result = set_dynamic_coin_symbol(coin_name)
            if result and result.get('success'):
                binance_ticker = result.get('binance_ticker')
                view_coin_name = result.get('view_coin_name')
                
                subscribe_to_dynamic_coin(binance_ticker)
                message = f"✅ New coin submitted: {coin_name} -> {view_coin_name} ({binance_ticker})"
                self.terminal_widget.append_message(message)
                logging.debug(f"Successfully set dynamic coin to {view_coin_name} ({binance_ticker})")
            else:
                error_msg = result.get('error_message', 'Unknown error') if result else 'Failed to set coin'
                message = f"❌ Failed to set coin {coin_name}: {error_msg}"
                self.terminal_widget.append_message(message)
                logging.warning(f"Failed to set dynamic coin {coin_name}: {error_msg}")
                
        except ValueError as e:
            message = f"❌ Error: {str(e)}"
            self.terminal_widget.append_message(message)
            logging.error(f"Symbol validation error: {e}")
        except Exception as e:
            message = f"❌ Unexpected error setting coin: {coin_name}"
            self.terminal_widget.append_message(message)
            logging.exception(f"Unexpected error in coin submission: {e}")
    
    def update_coin_prices(self):
        """Update coin prices displayed on buttons."""
        try:
            # WebSocket restart sırasında UI güncellemelerini durdur
            if self.websocket_restarting:
                return
                
            data = load_fav_coins()
            
            # Update favorite coin buttons
            for i in range(len(self.fav_coin_panel.get_coin_buttons())):
                coin_data = data['coins'][i]
                symbol = coin_data.get('symbol', f"COIN_{i}")
                price = coin_data.get('values', {}).get('current', "0.00")
                display_symbol = view_coin_format(symbol)
                self.fav_coin_panel.update_coin_button(i, display_symbol, price)
            
            # Update dynamic coin button
            dyn_data = data['dynamic_coin'][0]
            symbol = dyn_data.get('symbol', "DYN_COIN")
            price = dyn_data.get('values', {}).get('current', "0.00")
            display_symbol = view_coin_format(symbol)
            self.dynamic_coin_panel.update_coin_button(display_symbol, price)
            
        except Exception as e:
            error_msg = f"Error updating coin prices: {e}"
            logging.error(error_msg)
    
    def update_wallet(self):
        """Update wallet balance."""
        try:
            available_usdt = retrieve_usdt_balance(self.client)
            self.wallet_panel.update_wallet_balance(available_usdt)
        except Exception as e:
            error_msg = f"Error updating wallet: {e}"
            logging.error(error_msg)
    
    def _retrieve_coin_symbol(self, coin_index):
        """Retrieve coin symbol by index."""
        try:
            data = load_fav_coins()
            if coin_index == DYNAMIC_COIN_INDEX:
                if 'dynamic_coin' in data and len(data['dynamic_coin']) > 0:
                    symbol = data['dynamic_coin'][0]['symbol']
                    logging.info(f"Retrieved dynamic coin symbol: {symbol}")
                    return symbol
                else:
                    logging.error(f"Dynamic coin data not available")
                    return None
            else:
                if 'coins' in data and len(data['coins']) > coin_index:
                    symbol = data['coins'][coin_index]['symbol']
                    logging.info(f"Retrieved coin symbol for index {coin_index}: {symbol}")
                    return symbol
                else:
                    logging.error(f"Coin index {coin_index} out of range. Available coins: {len(data.get('coins', []))}")
                    return None
        except Exception as e:
            logging.error(f"Error retrieving coin symbol for index {coin_index}: {e}")
            return None
    
    def _create_error_interface(self, error):
        """Create minimal error interface."""
        try:
            self.setWindowTitle("Binance Terminal - Error Mode")
            self.resize(400, 200)
            from PySide6.QtWidgets import QLabel
            error_label = QLabel(f"Error initializing interface: {str(error)}")
            error_label.setStyleSheet("color: red; padding: 20px; font-size: 14px;")
            self.setCentralWidget(error_label)
        except Exception as e:
            logging.critical(f"Failed to create error interface: {e}")
    
    def show_and_focus(self):
        """Show window and bring to front."""
        self.show()
        self.raise_()
        self.activateWindow()
        
        # Windows-specific front bringing
        import sys
        if sys.platform == "win32":
            try:
                import ctypes
                hwnd = int(self.winId())
                ctypes.windll.user32.SetForegroundWindow(hwnd)
                ctypes.windll.user32.BringWindowToTop(hwnd)
                ctypes.windll.user32.ShowWindow(hwnd, 1)
            except Exception as e:
                logging.warning(f"Could not bring window to front: {e}")
    
    def refresh_favorites(self):
        """Refresh the favorite coins display without restarting the app."""
        try:
            logging.debug("Refreshing favorite coins display...")
            
            # WebSocket restart sürecini başlat
            self.websocket_restarting = True
            
            # First sync preferences to fav_coins.json
            self._sync_preferences_to_fav_coins()
            
            # Show websocket restart message in terminal
            if hasattr(self, 'terminal_widget'):
                self.terminal_widget.append_message("🔄 Restarting websocket with new coins...")
            
            # ÖNCE websocket restart et
            try:
                self._restart_websocket_for_new_favorites()
                logging.info("✅ WebSocket restarted for new favorites")
                
                # WebSocket tamamen restart olduktan sonra UI'ı güncelle
                # 5 saniye bekleyerek websocket'in tamamen restart olmasını sağla
                def delayed_ui_update():
                    import time
                    time.sleep(5)  # WebSocket restart için daha uzun bekle
                    
                    try:
                        # Şimdi UI'ı güncelle
                        data = load_fav_coins()
                        
                        # Ensure we have valid data structure
                        if not data or 'coins' not in data:
                            logging.warning("Invalid or empty fav_coins data, skipping refresh")
                            return
                        
                        # Update favorite coin buttons
                        for i in range(len(self.fav_coin_panel.get_coin_buttons())):
                            if i < len(data.get('coins', [])):
                                coin_data = data['coins'][i]
                                symbol = coin_data.get('symbol', f"COIN_{i}")
                                price = coin_data.get('values', {}).get('current', "0.00")
                                display_symbol = view_coin_format(symbol)
                                self.fav_coin_panel.update_coin_button(i, display_symbol, price)
                            else:
                                # Clear button if no coin data
                                self.fav_coin_panel.update_coin_button(i, f"COIN_{i}", "0.00")
                        
                        # Update dynamic coin if needed
                        if data.get('dynamic_coin') and len(data['dynamic_coin']) > 0:
                            dyn_data = data['dynamic_coin'][0]
                            symbol = dyn_data.get('symbol', "DYN_COIN")
                            price = dyn_data.get('values', {}).get('current', "0.00")
                            display_symbol = view_coin_format(symbol)
                            self.dynamic_coin_panel.update_coin_button(display_symbol, price)
                        
                        # WebSocket restart işlemi bitti, flag'i kapat
                        self.websocket_restarting = False
                        
                        logging.info("✅ Favorite coins display refreshed successfully after websocket restart")
                        
                        # Show success message in terminal
                        if hasattr(self, 'terminal_widget'):
                            self.terminal_widget.append_message("✅ Websocket restarted and favorites updated!")
                            
                    except Exception as ui_error:
                        error_msg = f"Error updating UI after websocket restart: {ui_error}"
                        logging.error(error_msg)
                        # Hata durumunda da flag'i kapat
                        self.websocket_restarting = False
                        if hasattr(self, 'terminal_widget'):
                            self.terminal_widget.append_message(f"❌ {error_msg}")
                
                # UI güncellemesini ayrı thread'de yap ki ana thread bloklanmasın
                ui_thread = threading.Thread(target=delayed_ui_update, daemon=True)
                ui_thread.start()
                
            except Exception as ws_error:
                logging.error(f"Could not restart WebSocket for new favorites: {ws_error}")
                # Hata durumunda da flag'i kapat
                self.websocket_restarting = False
                if hasattr(self, 'terminal_widget'):
                    self.terminal_widget.append_message(f"❌ WebSocket restart failed: {ws_error}")
                
        except Exception as e:
            error_msg = f"Error refreshing favorites: {e}"
            logging.error(error_msg)
            # Hata durumunda da flag'i kapat
            self.websocket_restarting = False
            if hasattr(self, 'terminal_widget'):
                self.terminal_widget.append_message(f"❌ {error_msg}")
    
    def _sync_preferences_to_fav_coins(self):
        """Sync preferences.txt changes to fav_coins.json file."""
        try:
            logging.debug("Syncing preferences to fav_coins.json...")
            # This will trigger the sync process
            from utils.data_utils import load_user_preferences
            symbols = load_user_preferences()
            logging.debug(f"✅ Synced preferences to fav_coins.json - Found {len(symbols)} symbols: {symbols}")
        except Exception as e:
            logging.error(f"Error syncing preferences: {e}")
    
    def _restart_websocket_for_new_favorites(self):
        """Refresh WebSocket symbols for new favorite coins without full restart."""
        try:
            logging.debug("Restarting WebSocket for new favorites...")
            
            # Terminal'da durum güncellemesi
            if hasattr(self, 'terminal_widget'):
                self.terminal_widget.append_message("🔄 Stopping old websocket connections...")
            
            # Websocket'i tamamen restart et
            from services.live_price_service import restart_websocket_with_new_symbols
            restart_websocket_with_new_symbols()
            
            logging.info("✅ WebSocket fully restarted with new favorite symbols")
            
        except ImportError:
            logging.warning("Could not import restart_websocket_with_new_symbols from live_price_service")
            # Fallback to reload_symbols if available
            try:
                from services.live_price_service import reload_symbols
                reload_symbols()
                logging.info("✅ Fallback: WebSocket symbols reloaded")
            except ImportError:
                logging.error("Neither restart nor reload functions available")
                raise Exception("WebSocket restart functions not available")
        except Exception as e:
            logging.error(f"Error restarting WebSocket: {e}")
            if hasattr(self, 'terminal_widget'):
                self.terminal_widget.append_message(f"❌ WebSocket restart failed: {e}")
            raise
    
    def append_to_terminal(self, text):
        """Append text to terminal (backward compatibility)."""
        if hasattr(self, 'terminal_widget'):
            self.terminal_widget.append_message(text)
        else:
            print(f"LOG: {text}")
    
    def keyPressEvent(self, event: QKeyEvent):
        """Handle keyboard shortcuts."""
        try:
            key = event.key()
            
            # T key - Toggle order type between MARKET and LIMIT
            if key == Qt.Key_T:
                self._toggle_order_type()
            
            # Pass event to parent for other key handling
            else:
                super().keyPressEvent(event)
                
        except Exception as e:
            logging.error(f"Error handling key press: {e}")
            super().keyPressEvent(event)
    
    def _toggle_order_type(self):
        """Toggle order type between MARKET and LIMIT."""
        try:
            from services.orders.order_type_manager import toggle_order_type, get_current_order_type
            
            # Get current order type before changing
            old_type = get_current_order_type()
            
            # Toggle order type
            new_type = toggle_order_type()
            
            if new_type != old_type:
                # Show success message to user via terminal
                message = f"🔄 Order Type changed: {old_type} → {new_type}"
                if hasattr(self, 'terminal_widget'):
                    self.terminal_widget.append_message(message)
                
                logging.info(f"✅ Order type toggled via keyboard shortcut: {old_type} → {new_type}")
                
                # Also show popup message
                self._show_order_type_notification(f"Order Type: {new_type}")
            else:
                # Failed to change
                error_message = f"❌ Failed to toggle order type from {old_type}"
                if hasattr(self, 'terminal_widget'):
                    self.terminal_widget.append_message(error_message)
                
                logging.error(f"Failed to toggle order type from {old_type}")
                
        except Exception as e:
            error_message = f"❌ Error toggling order type: {str(e)}"
            if hasattr(self, 'terminal_widget'):
                self.terminal_widget.append_message(error_message)
            logging.error(f"Error in _toggle_order_type: {e}")
    
    def _show_order_type_notification(self, message: str):
        """Show a brief notification for order type change."""
        try:
            # Show a non-blocking information message
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Information)
            msg_box.setWindowTitle("Order Type Changed")
            msg_box.setText(message)
            msg_box.setStandardButtons(QMessageBox.Ok)
            
            # Make it auto-close after 2 seconds
            from PySide6.QtCore import QTimer
            timer = QTimer()
            timer.timeout.connect(msg_box.accept)
            timer.start(2000)  # 2 seconds
            
            msg_box.exec()
            
        except Exception as e:
            logging.error(f"Error showing order type notification: {e}")
    
    def show_error_message(self, message):
        """Show error message dialog."""
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setWindowTitle("Error")
        msg_box.setText(message)
        msg_box.exec()


# Backward compatibility functions removed - these were not being used in the codebase


def initialize_gui():
    """Initialize the GUI with modular architecture."""
    try:
        logging.info("Initializing modular GUI...")
        
        # Prepare Binance client
        try:
            client = prepare_client()
            logging.info("Binance client prepared successfully")
        except Exception as e:
            logging.error(f"Error preparing Binance client: {e}")
            client = None
        
        # Check QApplication
        app = QApplication.instance()
        if not app:
            logging.error("QApplication not found! This should be created in main.py")
            return -1
        
        # Create main window
        logging.info("Creating modular main window...")
        window = MainWindow(client)
        window.setWindowTitle("Binance Terminal - Modular Architecture")
        
        # Show window
        logging.info("Showing modular main window...")
        window.show_and_focus()
        
        # Start WebSocket thread
        try:
            if client:
                background_thread = threading.Thread(target=start_price_websocket, daemon=True)
                background_thread.start()
                logging.info("WebSocket thread started")
            else:
                logging.warning("WebSocket thread skipped - no client available")
        except Exception as e:
            logging.error(f"Error starting WebSocket thread: {e}")
        
        # Start event loop
        logging.info("Starting GUI event loop...")
        return app.exec()
        
    except Exception as e:
        logging.exception(f"Error in initialize_gui: {e}")
        return -1


