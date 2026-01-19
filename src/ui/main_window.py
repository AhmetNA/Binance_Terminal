"""
Main Window - Modular Structure
This file now only handles layout coordination and component integration.
All UI components are separated into their own modules for better organization.
"""

import sys
import os
import logging
import threading

# Import centralized paths
from core.paths import (
    BTC_ICON_FILE,
    DYNAMIC_COIN_INDEX,
)

# Import services
from services.binance_client import prepare_client
from services.account.wallet_service import initialize_wallet_cache, update_wallet_cache_item
from services.account import retrieve_usdt_balance
from services.orders.order_service import make_order
from utils.data import load_fav_coins
from utils.symbols import view_coin_format
from services.market import (
    set_dynamic_coin_symbol,
    start_price_websocket,
    subscribe_to_dynamic_coin,
)

# Import components
from ui.components import (
    FavoriteCoinPanel,
    DynamicCoinPanel,
    WalletPanel,
    CoinEntryPanel,
    TerminalWidget,
)
from ui.dialogs.settings_dialog import SettingsDialog
from services.data_logger import get_data_logger

# Chart imports
import matplotlib.pyplot as plt
import mplfinance as mpf

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QMessageBox,
)
from PySide6.QtGui import QIcon, QKeyEvent
from PySide6.QtCore import Qt, QTimer, QThread, Signal

class WalletWorker(QThread):
    """Worker thread for fetching wallet balance."""
    balance_updated = Signal(float)
    error_occurred = Signal(str)

    def __init__(self, client):
        super().__init__()
        self.client = client

    def run(self):
        try:
            balance = retrieve_usdt_balance(self.client)
            self.balance_updated.emit(balance)
        except Exception as e:
            self.error_occurred.emit(str(e))

class OrderWorker(QThread):
    """Worker thread for executing orders."""
    order_completed = Signal(dict, float, float, str, str) # order_data, old_balance, new_balance, operation_type, symbol
    log_message = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, client, operation_type, symbol, order_type):
        super().__init__()
        self.client = client
        self.operation_type = operation_type
        self.symbol = symbol
        self.order_type = order_type

    def run(self):
        try:
            # Helper for thread-safe logging from make_order
            def worker_callback(msg):
                self.log_message.emit(msg)

            # Get initial balance
            old_balance = retrieve_usdt_balance(self.client)
            
            # Make order
            order_paper = make_order(
                Style=self.operation_type,
                Symbol=self.symbol,
                order_type=self.order_type,
                limit_price=None,
                amount_or_percentage=None,
                amount_type="percentage",
                terminal_callback=worker_callback,
            )
            
            # Get final balance
            new_balance = retrieve_usdt_balance(self.client)
            
            self.order_completed.emit(order_paper, old_balance, new_balance, self.operation_type, self.symbol)
            
        except Exception as e:
            self.error_occurred.emit(str(e))

class ChartDataWorker(QThread):
    """Worker thread for fetching chart data."""
    data_ready = Signal(object, str, str) # dataframe, symbol, interval
    error_occurred = Signal(str)

    def __init__(self, symbol, interval):
        super().__init__()
        self.symbol = symbol
        self.interval = interval

    def run(self):
        try:
            from ui.components.chart_widget import get_chart_data
            df = get_chart_data(self.symbol)
            self.data_ready.emit(df, self.symbol, self.interval)
        except Exception as e:
            self.error_occurred.emit(str(e))

class InitialCacheWorker(QThread):
    """Worker to initialize wallet cache at startup."""
    finished = Signal()
    
    def __init__(self, client, symbols):
        super().__init__()
        self.client = client
        self.symbols = symbols
        
    def run(self):
        try:
            initialize_wallet_cache(self.client, self.symbols)
            self.finished.emit()
        except Exception as e:
            logging.error(f"Cache init failed: {e}")



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

            # List to keep track of active order workers
            self.active_order_workers = []

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

            # Initialize Wallet Cache in background
            self._init_wallet_cache()

            logging.info("MainWindow: Modular initialization completed successfully")

            logging.info("MainWindow: Modular initialization completed successfully")

        except Exception as e:
            logging.exception(f"MainWindow: Error during initialization: {e}")
            self._create_error_interface(e)

    def _init_wallet_cache(self):
        """Start background worker to initialize wallet cache."""
        try:
            data = load_fav_coins()
            symbols = []
            if "coins" in data:
                symbols.extend([c["symbol"] for c in data["coins"] if "symbol" in c])
            if "dynamic_coin" in data and data["dynamic_coin"]:
                symbols.append(data["dynamic_coin"][0]["symbol"])
            
            # Make unique
            symbols = list(set(symbols))
            
            self.cache_worker = InitialCacheWorker(self.client, symbols)
            self.cache_worker.start()
        except Exception as e:
            logging.error(f"Error starting cache worker: {e}")

    def _setup_window_geometry(self):
        """Setup window size and position (Top-Mid)."""
        try:
            # Set size first
            win_w, win_h = 750, 450
            self.resize(win_w, win_h)
            
            # Move to top-center
            from utils.gui_utils import move_window_to_top_center
            move_window_to_top_center(self)
            
        except Exception as e:
            logging.error(f"Error setting window geometry: {e}")

    def showEvent(self, event):
        """Ensure window is positioned correctly when shown."""
        super().showEvent(event)
        # Force positioning again on show to override WM placement
        from utils.gui_utils import move_window_to_top_center
        move_window_to_top_center(self)

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
            self.fav_coin_panel.coin_details_requested.connect(
                self._handle_coin_details
            )
            self.fav_coin_panel.error_occurred.connect(
                self.terminal_widget.append_message
            )

            # Dynamic coin panel signals
            self.dynamic_coin_panel.order_requested.connect(self._handle_order_request)
            self.dynamic_coin_panel.coin_details_requested.connect(
                self._handle_coin_details
            )
            self.dynamic_coin_panel.error_occurred.connect(
                self.terminal_widget.append_message
            )

            # Wallet panel signals
            self.wallet_panel.settings_requested.connect(self._handle_settings_request)
            self.wallet_panel.error_occurred.connect(
                self.terminal_widget.append_message
            )

            # Coin entry panel signals
            self.coin_entry_panel.coin_submitted.connect(self._handle_coin_submission)
            self.coin_entry_panel.error_occurred.connect(
                self.terminal_widget.append_message
            )

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
            right_side_layout.setContentsMargins(0, 0, 0, 0)
            right_side_layout.setSpacing(5)

            # Add wallet panel
            right_side_layout.addWidget(self.wallet_panel.get_widget())
            
            # Add spacer to push search panel to bottom
            right_side_layout.addStretch()

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
            if hasattr(self, "api_keys_valid") and not self.api_keys_valid:
                if hasattr(self, "terminal_widget"):
                    self.terminal_widget.append_message(
                        "⚠️ Order blocked: API keys invalid (limited mode). Update credentials to trade."
                    )
                logging.debug("Order request ignored due to invalid API keys")
                return
            # Validate coin index before proceeding
            data = load_fav_coins()
            max_coin_index = len(data.get("coins", [])) - 1

            if coin_index != DYNAMIC_COIN_INDEX and coin_index > max_coin_index:
                error_msg = (
                    f"Invalid coin index {coin_index}. Max available: {max_coin_index}"
                )
                logging.error(error_msg)
                self.terminal_widget.append_message(f"❌ {error_msg}")
                return

            symbol = self._retrieve_coin_symbol(coin_index)
            if not symbol:
                error_msg = f"Could not retrieve valid symbol for coin {coin_index}"
                logging.error(error_msg)
                self.terminal_widget.append_message(f"❌ {error_msg}")
                return

            # Retrieve symbol and validate
            symbol = self._retrieve_coin_symbol(coin_index)
            if not symbol:
                error_msg = f"Could not retrieve valid symbol for coin {coin_index}"
                logging.error(error_msg)
                self.terminal_widget.append_message(f"❌ {error_msg}")
                return

            # Get order type preference
            from config.preferences_service import get_order_type_preference
            order_type = get_order_type_preference()

            # Log start
            if coin_index == DYNAMIC_COIN_INDEX:
                logging.info(f"Using {order_type} order type for dynamic coin {symbol}")
            else:
                logging.info(f"Using {order_type} order type for favorite coin {symbol}")

            # Create and start worker
            # Create and start NEW worker for this specific order
            self.terminal_widget.append_message(f"⏳ Processing {operation_type} for {symbol}...")
            
            # Create new worker instance
            worker = OrderWorker(self.client, operation_type, symbol, order_type)
            
            # Connect signals
            worker.order_completed.connect(self._on_order_completed)
            worker.log_message.connect(self.terminal_widget.append_message)
            worker.error_occurred.connect(lambda e: self.terminal_widget.append_message(f"❌ Error: {e}"))
            
            # Connect finished signal to cleanup
            # We use a default argument in the lambda to capture the specific worker instance
            worker.finished.connect(lambda w=worker: self._cleanup_worker(w))
            
            # Add to active list
            self.active_order_workers.append(worker)
            
            # Start
            worker.start()

        except Exception as e:
            self.terminal_widget.append_message(f"❌ Error starting order: {e}")
            logging.error(f"Error preparing order: {e}")

    def _cleanup_worker(self, worker):
        """Remove worker from active list when finished."""
        try:
            if worker in self.active_order_workers:
                self.active_order_workers.remove(worker)
                worker.deleteLater()
                # logging.debug(f"Order worker cleaned up. Remaining: {len(self.active_order_workers)}")
        except Exception as e:
            logging.error(f"Error cleaning up worker: {e}")

    def _on_order_completed(self, order_paper, old_balance, new_balance, operation_type, symbol):
        """Handle completion of order from worker."""
        try:
            # Handle both filled and unfilled orders safely
            try:
                if order_paper.get("fills") and len(order_paper["fills"]) > 0:
                    amount = float(order_paper["fills"][0]["qty"])
                    price = float(order_paper["fills"][0]["price"])
                    cost_or_received = float(order_paper.get("cummulativeQuoteQty", amount * price))
                else:
                    amount = float(order_paper.get("origQty", 0))
                    price = float(order_paper.get("price", 0)) if "price" in order_paper else 0.0
                    cost_or_received = amount * price
            except (ValueError, KeyError, TypeError):
                amount = 0.0
                price = 0.0
                cost_or_received = 0.0

            operation = "BUY" if "Buy" in operation_type else "SELL"
            action_type = "H" if "Hard" in operation_type else "S"
            
            # Determine order type for display
            from config.preferences_service import get_order_type_preference
            order_type_str = get_order_type_preference()

            status_str = "FILLED" if order_paper.get("fills") else order_paper.get("status", "PENDING")
            amount_str = f"{amount:.5f}".rstrip("0").rstrip(".")
            
            message = (
                f"[{action_type}] {operation} {symbol} | "
                f"{amount_str} @ ${price:.2f} | "
                f"Total: ${cost_or_received:.2f} | "
                f"Balance: ${new_balance:.2f} | "
                f"Order Type: {order_type_str} | Status: {status_str}"
            )
            self.terminal_widget.append_message(message)
            
            # Log trade to file
            get_data_logger().log_trade(
                order_data=order_paper,
                status=status_str,
                initial_balance=old_balance,
                final_balance=new_balance
            )
            
            # Trigger immediate wallet update
            self.wallet_panel.update_wallet_balance(new_balance)

            # Update cache for this symbol
            try:
                update_wallet_cache_item(symbol, self.client)
            except Exception as e:
                logging.error(f"Failed to update cache after trade: {e}")

        except Exception as e:
            logging.error(f"Error processing order completion: {e}")
            self.terminal_widget.append_message(f"⚠️ Order finished but display error: {e}")

    def _handle_coin_details(self, coin_button):
        """Handle coin details requests from components."""
        try:
            # Check if a chart worker is already running to prevent crashes/concurrency issues
            if hasattr(self, "chart_worker") and self.chart_worker.isRunning():
                self.terminal_widget.append_message("⚠️ Request ignored: correct coin info usage is needed one at a time.")
                logging.info(f"Ignored coin details request for {coin_button.text()} - worker already running")
                return

            # Try to get symbol from property first (more robust)
            symbol = coin_button.property("symbol")
            
            # Fallback to text parsing if property not found (legacy support)
            if not symbol:
                text_parts = coin_button.text().split("\n")
                if len(text_parts) >= 2:
                    # New format: Value \n Symbol \n Price
                    symbol = text_parts[1]
                else:
                    # Old format: Symbol \n Price
                    symbol = text_parts[0]

            # Sanitize symbol (remove hyphens, ensure uppercase)
            if symbol:
                symbol = symbol.replace("-", "").upper()

            # Get chart interval from preferences
            from core.paths import PREFERENCES_FILE

            interval = "1"
            try:
                with open(PREFERENCES_FILE, "r") as f:
                    for line in f:
                        if line.strip().startswith("chart_interval"):
                            interval = line.split("=", 1)[1].strip().lstrip("%")
                            break
            except Exception:
                interval = "1"

            # Generate and show chart ASYNC
            self.terminal_widget.append_message(f"⏳ Fetching data for {symbol}...")
            
            self.chart_worker = ChartDataWorker(symbol, interval)
            self.chart_worker.data_ready.connect(self._show_coin_chart)
            self.chart_worker.error_occurred.connect(lambda e: self.terminal_widget.append_message(f"❌ Chart Error: {e}"))
            self.chart_worker.start()

        except Exception as e:
            error_msg = f"Error preparing chart: {e}"
            self.terminal_widget.append_message(error_msg)
            logging.error(error_msg)

    def _show_coin_chart(self, df, symbol, interval):
        """Show candlestick chart for a coin with pre-fetched data."""
        try:
            # df is now passed in, no need to fetch
            # df = get_chart_data(symbol) BEFORE
            
            first_price = df["Close"].iloc[0]
            last_price = df["Close"].iloc[-1]
            price_change_pct = ((last_price - first_price) / first_price) * 100

            plt.style.use("dark_background")

            # Configure candlestick chart style
            mc = mpf.make_marketcolors(
                up="green", down="red", edge="inherit", wick="inherit"
            )
            s = mpf.make_mpf_style(base_mpf_style="nightclouds", marketcolors=mc)

            # Generate candlestick chart
            fig, axlist = mpf.plot(
                df,
                type="candle",
                style=s,
                returnfig=True,
                datetime_format="%H:%M:%S",
                xrotation=45,
            )
            ax = axlist[0]

            # Add title and adjust figure size
            fig.suptitle(f"{symbol} ({interval}m) Candle Chart", fontsize=12)
            fig.set_size_inches(6, 4)

            # Add price info box (top-left)
            price_info_text = (
                f"First Price: {first_price:.2f}\n"
                f"Last Price: {last_price:.2f}\n"
                f"Overall Change: {price_change_pct:.2f}%"
            )
            price_props = dict(boxstyle="round", facecolor="gray", alpha=0.5)
            ax.text(
                0.02,
                0.98,
                price_info_text,
                transform=ax.transAxes,
                fontsize=8,
                verticalalignment="top",
                bbox=price_props,
            )


            # Show custom dialog instead of blocking plt.show()
            from ui.components.chart_widget import ChartDialog
            
            # Close existing dialog if any
            if hasattr(self, "current_chart_dialog") and self.current_chart_dialog:
                try:
                    self.current_chart_dialog.close()
                except Exception:
                    pass
            
            self.current_chart_dialog = ChartDialog(fig, self, title=f"{symbol} Chart")
            
            # Position to the LEFT of the Main Window to avoid covering it
            # Main window is Top-Mid, so we have space on the left
            main_geom = self.frameGeometry()
            dialog_width = self.current_chart_dialog.width()
            
            # Target X: Left of main window minus dialog width minus padding
            target_x = main_geom.x() - dialog_width - 20
            
            # Ensure we don't go off-screen (keep at least 10px margin)
            target_x = max(10, target_x)
            
            # Target Y: Align with main window top
            target_y = main_geom.y()
            
            self.current_chart_dialog.move(target_x, target_y)
            
            self.current_chart_dialog.show()  # Modeless (non-blocking)



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
            if result and result.get("success"):
                binance_ticker = result.get("binance_ticker")
                view_coin_name = result.get("view_coin_name")

                subscribe_to_dynamic_coin(binance_ticker)
                message = f"✅ New coin submitted: {coin_name} -> {view_coin_name} ({binance_ticker})"
                self.terminal_widget.append_message(message)
                logging.debug(
                    f"Successfully set dynamic coin to {view_coin_name} ({binance_ticker})"
                )
            else:
                error_msg = (
                    result.get("error_message", "Unknown error")
                    if result
                    else "Failed to set coin"
                )
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

            from services.account.wallet_service import get_cached_wallet_info

            data = load_fav_coins()

            # Update favorite coin buttons
            for i in range(len(self.fav_coin_panel.get_coin_buttons())):
                try:
                    coin_data = data["coins"][i]
                    symbol = coin_data.get("symbol", f"COIN_{i}")
                    price = coin_data.get("values", {}).get("current", "0.00")
                    display_symbol = view_coin_format(symbol)
                    
                    # Get wallet value with safety checks
                    wallet_value = 0.0
                    try:
                        w_info = get_cached_wallet_info(symbol)
                        if w_info and isinstance(w_info, dict):
                            # Ensure we have valid numeric data
                            amount = float(w_info.get("amount", 0.0))
                            current_price = float(w_info.get("current_price", 0.0))
                            # Use existing value if available, or calculate it
                            wallet_value = float(w_info.get("usdt_value", amount * current_price))
                    except Exception as e:
                        # Log debug but don't spam errors for every coin every second
                        # logging.debug(f"Error getting wallet value for {symbol}: {e}")
                        wallet_value = 0.0

                    self.fav_coin_panel.update_coin_button(i, display_symbol, price, wallet_value)
                except Exception as e:
                     logging.debug(f"Error updating fav coin {i}: {e}")

            # Update dynamic coin button
            try:
                dyn_data = data["dynamic_coin"][0]
                symbol = dyn_data.get("symbol", "DYN_COIN")
                price = dyn_data.get("values", {}).get("current", "0.00")
                display_symbol = view_coin_format(symbol)
                
                # Get wallet value for dynamic coin
                wallet_value = 0.0
                try:
                    w_info = get_cached_wallet_info(symbol)
                    if w_info and isinstance(w_info, dict):
                        amount = float(w_info.get("amount", 0.0))
                        current_price = float(w_info.get("current_price", 0.0))
                        wallet_value = float(w_info.get("usdt_value", amount * current_price))
                except Exception:
                    wallet_value = 0.0

                self.dynamic_coin_panel.update_coin_button(display_symbol, price, wallet_value)
            except Exception as e:
                logging.debug(f"Error updating dynamic coin: {e}")

        except Exception as e:
            error_msg = f"Error updating coin prices: {e}"
            logging.error(error_msg)

    def update_wallet(self):
        """Update wallet balance."""
        try:
            if hasattr(self, "api_keys_valid") and not self.api_keys_valid:
                return
            # Use Worker for wallet update to prevent UI freeze
            if not hasattr(self, 'wallet_worker'):
                self.wallet_worker = WalletWorker(self.client)
                self.wallet_worker.balance_updated.connect(self.wallet_panel.update_wallet_balance)
                self.wallet_worker.error_occurred.connect(lambda e: logging.debug(f"Wallet update error: {e}"))
            
            if not self.wallet_worker.isRunning():
                self.wallet_worker.start()

        except Exception as e:
            error_msg = f"Error updating wallet: {e}"
            logging.error(error_msg)

    def _retrieve_coin_symbol(self, coin_index):
        """Retrieve coin symbol by index."""
        try:
            data = load_fav_coins()
            if coin_index == DYNAMIC_COIN_INDEX:
                if "dynamic_coin" in data and len(data["dynamic_coin"]) > 0:
                    symbol = data["dynamic_coin"][0]["symbol"]
                    logging.info(f"Retrieved dynamic coin symbol: {symbol}")
                    return symbol
                else:
                    logging.error("Dynamic coin data not available")
                    return None
            else:
                if "coins" in data and len(data["coins"]) > coin_index:
                    symbol = data["coins"][coin_index]["symbol"]
                    logging.info(
                        f"Retrieved coin symbol for index {coin_index}: {symbol}"
                    )
                    return symbol
                else:
                    logging.error(
                        f"Coin index {coin_index} out of range. Available coins: {len(data.get('coins', []))}"
                    )
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
            if hasattr(self, "terminal_widget"):
                self.terminal_widget.append_message(
                    "🔄 Restarting websocket with new coins..."
                )

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
                        if not data or "coins" not in data:
                            logging.warning(
                                "Invalid or empty fav_coins data, skipping refresh"
                            )
                            return

                        # Update favorite coin buttons
                        for i in range(len(self.fav_coin_panel.get_coin_buttons())):
                            if i < len(data.get("coins", [])):
                                coin_data = data["coins"][i]
                                symbol = coin_data.get("symbol", f"COIN_{i}")
                                price = coin_data.get("values", {}).get(
                                    "current", "0.00"
                                )
                                display_symbol = view_coin_format(symbol)
                                self.fav_coin_panel.update_coin_button(
                                    i, display_symbol, price
                                )
                            else:
                                # Clear button if no coin data
                                self.fav_coin_panel.update_coin_button(
                                    i, f"COIN_{i}", "0.00"
                                )

                        # Update dynamic coin if needed
                        if data.get("dynamic_coin") and len(data["dynamic_coin"]) > 0:
                            dyn_data = data["dynamic_coin"][0]
                            symbol = dyn_data.get("symbol", "DYN_COIN")
                            price = dyn_data.get("values", {}).get("current", "0.00")
                            display_symbol = view_coin_format(symbol)
                            self.dynamic_coin_panel.update_coin_button(
                                display_symbol, price
                            )

                        # WebSocket restart işlemi bitti, flag'i kapat
                        self.websocket_restarting = False

                        logging.info(
                            "✅ Favorite coins display refreshed successfully after websocket restart"
                        )

                        # Show success message in terminal
                        if hasattr(self, "terminal_widget"):
                            self.terminal_widget.append_message(
                                "✅ Websocket restarted and favorites updated!"
                            )

                    except Exception as ui_error:
                        error_msg = (
                            f"Error updating UI after websocket restart: {ui_error}"
                        )
                        logging.error(error_msg)
                        # Hata durumunda da flag'i kapat
                        self.websocket_restarting = False
                        if hasattr(self, "terminal_widget"):
                            self.terminal_widget.append_message(f"❌ {error_msg}")

                # UI güncellemesini ayrı thread'de yap ki ana thread bloklanmasın
                ui_thread = threading.Thread(target=delayed_ui_update, daemon=True)
                ui_thread.start()

            except Exception as ws_error:
                logging.error(
                    f"Could not restart WebSocket for new favorites: {ws_error}"
                )
                # Hata durumunda da flag'i kapat
                self.websocket_restarting = False
                if hasattr(self, "terminal_widget"):
                    self.terminal_widget.append_message(
                        f"❌ WebSocket restart failed: {ws_error}"
                    )

        except Exception as e:
            error_msg = f"Error refreshing favorites: {e}"
            logging.error(error_msg)
            # Hata durumunda da flag'i kapat
            self.websocket_restarting = False
            if hasattr(self, "terminal_widget"):
                self.terminal_widget.append_message(f"❌ {error_msg}")

    def _sync_preferences_to_fav_coins(self):
        """Sync preferences.txt changes to fav_coins.json file."""
        try:
            logging.debug("Syncing preferences to fav_coins.json...")
            # This will trigger the sync process
            from utils.data import load_user_preferences

            symbols = load_user_preferences()
            logging.debug(
                f"✅ Synced preferences to fav_coins.json - Found {len(symbols)} symbols: {symbols}"
            )
        except Exception as e:
            logging.error(f"Error syncing preferences: {e}")

    def _restart_websocket_for_new_favorites(self):
        """Refresh WebSocket symbols for new favorite coins without full restart."""
        try:
            logging.debug("Restarting WebSocket for new favorites...")

            # Terminal'da durum güncellemesi
            if hasattr(self, "terminal_widget"):
                self.terminal_widget.append_message(
                    "🔄 Stopping old websocket connections..."
                )

            # Websocket'i tamamen restart et
            from services.market import restart_websocket_with_new_symbols

            restart_websocket_with_new_symbols()

            logging.info("✅ WebSocket fully restarted with new favorite symbols")

        except ImportError:
            logging.warning(
                "Could not import restart_websocket_with_new_symbols from live_price_service"
            )
            # Fallback to reload_symbols if available
            try:
                from services.market import reload_symbols

                reload_symbols()
                logging.info("✅ Fallback: WebSocket symbols reloaded")
            except ImportError:
                logging.error("Neither restart nor reload functions available")
                raise Exception("WebSocket restart functions not available")
        except Exception as e:
            logging.error(f"Error restarting WebSocket: {e}")
            if hasattr(self, "terminal_widget"):
                self.terminal_widget.append_message(f"❌ WebSocket restart failed: {e}")
            raise

    def append_to_terminal(self, text):
        """Append text to terminal (backward compatibility)."""
        if hasattr(self, "terminal_widget"):
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

    def closeEvent(self, event):
        """
        🔒 SECURITY: Uygulama kapatılırken API key'leri bellekten temizle

        Bu metod uygulama kapatılırken otomatik olarak çağrılır ve:
        1. Cached API credentials'ları bellekten temizler
        2. WebSocket bağlantılarını kapatır
        3. HTTP session'ları temizler
        4. Güvenlik log'u tutar
        """
        try:
            logging.info("🔒 Application closing - starting security cleanup...")

            # 0. Thread ve Timer Temizliği (ÖNCE BUNLARI DURDUR)
            try:
                logging.info("⏳ Stopping background threads and timers...")
                
                # Timers
                if hasattr(self, 'price_timer') and self.price_timer.isActive():
                    self.price_timer.stop()
                if hasattr(self, 'wallet_timer') and self.wallet_timer.isActive():
                    self.wallet_timer.stop()
                
                # Workers
                workers = ['wallet_worker', 'order_worker', 'chart_worker', 'cache_worker']
                for worker_name in workers:
                    if hasattr(self, worker_name):
                        worker = getattr(self, worker_name)
                        if worker and worker.isRunning():
                            logging.debug(f"Stopping {worker_name}...")
                            worker.quit()
                            if not worker.wait(2000): # 2 saniye bekle
                                logging.warning(f"⚠️ {worker_name} did not stop gracefully, terminating...")
                                worker.terminate()
                                worker.wait()
                
                logging.info("✅ Background threads stopped")
            except Exception as e:
                logging.error(f"❌ Error stopping threads: {e}")

            # 1. API credentials'ları bellekten temizle
            try:
                from services.binance_client import (
                    clear_api_credentials_from_memory,
                )

                credentials_cleared = clear_api_credentials_from_memory()
                if credentials_cleared:
                    logging.info("✅ API credentials successfully cleared from memory")
                else:
                    logging.info("ℹ️ No cached credentials found to clear")
            except Exception as e:
                logging.error(f"❌ Error clearing API credentials: {e}")

            # 2. HTTP sessions'ları temizle
            try:
                from api import close_http_session
                import asyncio

                # Try to close HTTP sessions cleanly
                try:
                    asyncio.get_running_loop()
                    asyncio.create_task(close_http_session())
                except RuntimeError:
                    # No running loop
                    asyncio.run(close_http_session())
                logging.info("✅ HTTP sessions closed")
            except Exception as e:
                logging.error(f"❌ Error closing HTTP sessions: {e}")

            # 3. Cached prices'ları kaydet
            try:
                from services.market import force_save_prices

                force_save_prices()
                logging.info("✅ Price data saved before exit")
            except Exception as e:
                logging.warning(f"⚠️ Could not save price data: {e}")

            # 4. Python garbage collection'ı zorla
            try:
                import gc

                gc.collect()
                logging.info("✅ Garbage collection completed")
            except Exception as e:
                logging.error(f"❌ Error in garbage collection: {e}")

            logging.info("🔒 Security cleanup completed successfully")

        except Exception as e:
            logging.error(f"❌ Error in closeEvent security cleanup: {e}")
            # Güvenlik için yine de devam et

        finally:
            # Her durumda pencereyi kapat
            event.accept()
            logging.info("👋 Application closed securely")

    def _toggle_order_type(self):
        """Toggle order type between MARKET and LIMIT."""
        try:
            from services.orders.order_type_manager import (
                toggle_order_type,
                get_current_order_type,
            )

            # Get current order type before changing
            old_type = get_current_order_type()

            # Toggle order type
            new_type = toggle_order_type()

            if new_type != old_type:
                # Show success message to user via terminal
                message = f"🔄 Order Type changed: {old_type} → {new_type}"
                if hasattr(self, "terminal_widget"):
                    self.terminal_widget.append_message(message)

                logging.info(
                    f"✅ Order type toggled via keyboard shortcut: {old_type} → {new_type}"
                )

                # Also show popup message
                self._show_order_type_notification(f"Order Type: {new_type}")
            else:
                # Failed to change
                error_message = f"❌ Failed to toggle order type from {old_type}"
                if hasattr(self, "terminal_widget"):
                    self.terminal_widget.append_message(error_message)

                logging.error(f"Failed to toggle order type from {old_type}")

        except Exception as e:
            error_message = f"❌ Error toggling order type: {str(e)}"
            if hasattr(self, "terminal_widget"):
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


def initialize_gui(start_time=None):
    """Initialize the GUI with modular architecture."""
    try:
        logging.info("Initializing modular GUI...")

        # Check QApplication
        app = QApplication.instance()
        if not app:
            logging.error("QApplication not found! This should be created in main.py")
            return -1

        # Modern splash screen göster
        from ui.components.splash_screen import show_splash_screen
        from utils.security.secure_storage import get_secure_storage
        from ui.dialogs.api_credentials_dialog import APICredentialsDialog
        from PySide6.QtWidgets import QMessageBox

        splash = show_splash_screen()
        # Stop auto-animation to take manual control and prevent timer conflicts
        splash.stop_animation()
        app.processEvents()

        # Initial loading message
        splash.set_progress(10, "🔧 Checking security system...")
        app.processEvents()
        
        # Loop to allow restarting setup if credentials are reset
        client = None
        setup_credentials = None
        password_duration = 0.0  # Initialize here to ensure it's always defined for _finish_startup

        while True:
            # Secure storage check and credential setup
            secure_storage = get_secure_storage()
            setup_credentials = None  # Will store credentials if just set up

            if secure_storage.credentials_exist():
                splash.set_progress(25, "🔐 Secure credentials found...")
            else:
                splash.set_progress(25, "⚠️ No secure credentials found...")
                splash.close()  # Close splash to show setup dialog

                # Show credential setup dialog
                logging.info("No valid secure credentials found, showing setup dialog...")
                dlg = APICredentialsDialog()
                dlg.setWindowTitle("🔐 Binance Terminal - First Time Setup")

                if dlg.exec() == dlg.DialogCode.Accepted:
                    api_key, api_secret, master_password = dlg.get_credentials()

                    # Store credentials securely
                    success = secure_storage.store_credentials(
                        api_key, api_secret, master_password
                    )

                    if success:
                        logging.info(
                            "✅ API credentials successfully stored (popup suppressed)"
                        )

                        # Store the credentials for immediate use
                        setup_credentials = {
                            "api_key": api_key,
                            "api_secret": api_secret,
                            "master_password": master_password,
                        }

                        # Restart splash screen for continued loading
                        splash = show_splash_screen()
                        splash.stop_animation()
                        splash.set_progress(25, "🔐 Credentials setup complete...")
                        app.processEvents()
                    else:
                        # Storage failed
                        QMessageBox.critical(
                            None,
                            "Setup Failed",
                            "❌ Failed to store API credentials securely!\n\n"
                            "Please check the logs for more details and try again.",
                        )
                        logging.error("❌ Failed to store API credentials")
                        return -1
                else:
                    # User cancelled setup
                    QMessageBox.information(
                        None,
                        "Setup Required",
                        "⚠️ Binance Terminal requires API credentials to function.\n\n"
                        "Please restart the application and complete the setup process.",
                    )
                    logging.info("User cancelled credential setup")
                    return -1

            app.processEvents()

            # Binance client hazırlama
            splash.set_progress(40, "🌐 Binance API bağlantısı kuruluyor...")
            app.processEvents()

            try:
                # If we just set up credentials, use them directly
                if setup_credentials:
                    logging.info("Using newly setup credentials for client initialization")
                    from binance.client import Client

                    client = Client(
                        setup_credentials["api_key"], setup_credentials["api_secret"]
                    )
                    client.API_URL = "https://testnet.binance.vision/api"
                    # Cache the client for future use
                    import services.binance_client as client_service

                    client_service._CACHED_CLIENT = client
                    logging.info(
                        "✅ Binance client created and cached with new credentials"
                    )
                else:
                    # Use normal client preparation (will ask for master password)
                    # Pass None as parent to avoid Qt event loop issues with splash screen
                    import time
                    pw_start = time.time()
                    client = prepare_client(gui_mode=True, parent_widget=None)
                    pw_end = time.time()
                    password_duration = pw_end - pw_start
                    logging.info("Binance client prepared successfully")
                
                # If we get here without exception, break the loop
                break

            except Exception as e:
                # Handle reset request
                if "CREDENTIALS_RESET" in str(e):
                    logging.info("🔄 Credentials reset by user from login dialog. Restarting setup flow...")
                    splash.set_progress(0, "🔄 Resetting credentials...")
                    app.processEvents()
                    
                    # Ensure credentials are deleted (they should be, but safety first)
                    secure_storage.delete_credentials()
                    
                    # Continue loop to show setup dialog again
                    continue
                
                logging.error(f"Error preparing Binance client: {e}")
                splash.close()

                # Handle credential-related errors specifically
                error_str = str(e)
                # Handle credential-related errors specifically
                error_str = str(e)
                if (
                    "Secure credentials not configured" in error_str
                    or "User cancelled password input" in error_str
                ):
                    # Popup tamamen kaldırıldı; sadece log ve sessiz çıkış.
                    logging.warning(
                        "Credential issue detected (suppressed popup): %s", error_str
                    )
                    return -1
                elif "Master password could not be verified" in error_str:
                     QMessageBox.warning(
                        None,
                        "Security Warning",
                        "❌ Incorrect Master Password!\n\nPlease try again.",
                    )
                     return -1
                else:
                    QMessageBox.critical(
                        None,
                        "Connection Error",
                        f"❌ Failed to connect to Binance API:\n\n{str(e)}\n\n"
                        "Please check your internet connection and try again.",
                    )
                    return -1
        
        # --- Post-loop: Recreate splash after password dialog to avoid Qt state issues ---
        logging.info("TRACE: Loop exited, recreating splash for post-login flow...")
        try:
            # Close the old splash (might be in invalid state after password dialog)
            try:
                splash.close()
            except Exception:
                pass
            
            # Create a fresh splash screen
            splash = show_splash_screen()
            splash.stop_animation()
            splash.set_progress(50, "✅ Login successful, continuing...")
            app.processEvents()
            logging.info("TRACE: Fresh splash created successfully")
        except Exception as splash_err:
            logging.warning(f"TRACE: Splash recreation failed: {splash_err}")
            # Continue without splash - not critical
        
        # --- Immediate credential validation (lightweight) ---
        logging.info("TRACE: Starting credential validation...")
        api_keys_valid = False
        try:
            # Basic endpoint call to verify keys: get account (requires valid signature)
            from services.account import retrieve_usdt_balance
            
            retrieve_usdt_balance(client)  # will raise if invalid
            
            api_keys_valid = True
            logging.info("TRACE: Credentials valid!")
            splash.set_progress(70, "✅ Credentials valid!")
        except Exception as val_err:
            api_keys_valid = False
            logging.warning(
                f"API key validation failed (continuing in limited mode): {val_err}"
            )
            splash.set_progress(70, "⚠️ Keys invalid - limited mode")

        # Store flag on client object for later checks
        try:
            setattr(client, "_api_keys_valid", api_keys_valid)
        except Exception:
            pass

        logging.info("TRACE: Calling app.processEvents after validation...")
        app.processEvents()

        # Ana pencere oluşturma
        logging.info("TRACE: Setting splash progress to 85%...")
        splash.set_progress(85, "🎨 Preparing main window...")
        app.processEvents()

        logging.info("TRACE: Creating MainWindow...")
        logging.info("Creating modular main window...")
        window = MainWindow(client)
        # Pass validation result into window
        try:
            window.api_keys_valid = getattr(client, "_api_keys_valid", True)
        except Exception:
            window.api_keys_valid = True
        window.setWindowTitle("Binance-Terminal")

        # WebSocket başlatma
        splash.set_progress(95, "📡 Canlı veri bağlantısı kuruluyor...")
        app.processEvents()

        try:
            if client:
                background_thread = threading.Thread(
                    target=start_price_websocket, daemon=True
                )
                background_thread.start()
                logging.info("WebSocket thread started")
            else:
                logging.warning("WebSocket thread skipped - no client available")
        except Exception as e:
            logging.error(f"Error starting WebSocket thread: {e}")

        # Splash'ı tamamla ve ana pencereyi göster
        splash.set_progress(100, "🚀 Binance Terminal is starting...")
        app.processEvents()

        # Kısa gecikme sonra ana pencereyi göster
        def _finish_startup():
            try:
                logging.info("Executing _finish_startup sequence...")
                splash.close()
                window.show_and_focus()

                # Log app readiness if start_time is provided
                if start_time:
                    import time
                    ready_time = time.time()
                    try:
                        get_data_logger().log_app_ready(start_time, ready_time, password_duration)
                    except Exception as log_err:
                        logging.warning(f"Failed to log app readiness: {log_err}")

                # Show status message in terminal instead of popup
                if hasattr(window, "terminal_widget"):
                    if getattr(window, "api_keys_valid", True):
                        window.terminal_widget.append_message(
                            "✅ API keys validated. Full functionality enabled."
                        )
                    else:
                        window.terminal_widget.append_message(
                            "⚠️ API keys invalid or connection failed. LIMITED MODE: Orders & balance disabled, prices still show. Go to Settings > Reset Credentials to re-enter keys, then restart."
                        )
                logging.info("Startup sequence completed successfully")
            except Exception as e:
                logging.critical(f"CRITICAL ERROR in _finish_startup: {e}")
                # Try to show window anyway if splash failed to close
                try:
                    splash.close()
                    window.show()
                except Exception:
                    pass

        # Doğrudan çağır - Timer'a güvenme (PyInstaller ortamında sorun olabiliyor)
        logging.info("Calling _finish_startup directly...")
        _finish_startup()

        logging.info("Showing modular main window...")
        logging.info("Starting GUI event loop...")
        return app.exec()
    except Exception as e:
        logging.exception(f"Unhandled error initializing GUI: {e}")
        try:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(None, "Fatal Startup Error", f"Unhandled error initializing GUI:\n{str(e)}\n\nCheck logs in data/logs for details.")
        except Exception:
            pass
        return -1
