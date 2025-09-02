import json
import sys
import os
import logging

# Add project paths
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_dir)
sys.path.append(src_dir)

# Import centralized paths
from core.paths import FAV_COINS_FILE, BTC_ICON_FILE, FAVORITE_COIN_COUNT, DYNAMIC_COIN_INDEX

from services.order_service import *
from utils.data_utils import load_fav_coins
from utils.symbol_utils import view_coin_format
from services.live_price_service import (
    set_dynamic_coin_symbol,
    start_price_websocket, 
    subscribe_to_dynamic_coin
)
from ui.components.chart_widget import *
from config.preferences_service import *

import matplotlib.pyplot as plt
import mplfinance as mpf  # for candlestick charts

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QPushButton, QLabel, QLineEdit, QPlainTextEdit, QFrame, QDialog, QMessageBox
)

from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QTimer
import threading

class MainWindow(QMainWindow):
    def __init__(self, client):
        """
        Initializes the main GUI window for the application.
        This constructor sets up the entire user interface which includes:
            - A Favorite Coin Panel with a grid layout containing buttons for:
                * Hard Buy (row 0)
                * Soft Buy (row 1)
                * Coin label buttons displaying coin name and price (row 2)
                  (creates lists for coins, stored in self.fav_coin_buttons) # This button shows coin's chart
                * Soft Sell (row 3)
                * Hard Sell (row 4)
            - A Dynamic Coin Panel with buttons for dynamic coin operations and a coin label (stored in self.dyn_coin_button)
            - A right-side panel featuring:
                * A wallet frame displaying the current wallet balance.
                * A coin entry frame allowing the user to input a coin name.
            - A terminal (read-only text area) for log outputs or status messages.
        Additionally, this method configures two QTimers:
            - One to update coin prices every second.
            - One to update the wallet balance every second.
        Parameters:
            client: An instance of the backend client used to interact with data and execute coin orders.
        """
        super().__init__()
        
        try:
            logging.info("MainWindow: Starting initialization...")
            
            # Pencreyi normal window olarak ayarla (always on top kullanma)
            # self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)  # Bu satırı iptal et
            self.setWindowFlags(Qt.Window)
            
            # Ekran boyutunu al ve pencereyi ortaya göre biraz sola ve üste kaydır
            screen = QApplication.primaryScreen().geometry()
            win_w, win_h = 600, 400  # Daha küçük başlangıç boyutu
            center_x = screen.x() + (screen.width() - win_w) // 2
            center_y = screen.y() + (screen.height() - win_h) // 2
            offset_x = 200  # Sola kaydırma miktarı
            offset_y = 100   # Üste kaydırma miktarı
            self.move(center_x - offset_x, center_y - offset_y)
            
            self.client = client
            self.setWindowTitle("GAIN")
            self.resize(win_w, win_h)
            
            # Uygulama ve pencere simgesini ayarla
            self.setup_application_icon()
            
            self.fav_coin_buttons = []
            self.dyn_coin_button = None
            
            logging.info("MainWindow: Setting up UI...")
            self.setup_ui()
            logging.info("MainWindow: Initialization completed successfully")
            
        except Exception as e:
            logging.exception(f"MainWindow: Error during initialization: {e}")
            # Create minimal interface on error
            self.setWindowTitle("Binance Terminal - Error Mode")
            self.resize(400, 200)
            error_label = QLabel(f"Error initializing interface: {str(e)}")
            error_label.setStyleSheet("color: red; padding: 20px; font-size: 14px;")
            self.setCentralWidget(error_label)

    def setup_application_icon(self):
        """Uygulama ve pencere simgesini ayarlar"""
        try:
            # Assets klasöründen icon path'i al
            if os.path.exists(BTC_ICON_FILE):
                icon = QIcon(BTC_ICON_FILE)
                
                # Pencere simgesini ayarla
                self.setWindowIcon(icon)
                
                # Uygulama simgesini de ayarla
                app = QApplication.instance()
                if app:
                    app.setWindowIcon(icon)
                
                logging.info(f"Application and window icon set to: {BTC_ICON_FILE}")
            else:
                logging.warning(f"Icon file not found: {BTC_ICON_FILE}")
                
        except Exception as e:
            logging.error(f"Error setting application icon: {e}")

    def setup_ui(self):
        # Set up the central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(4)
        self.setup_top_section(main_layout)
        self.setup_terminal(main_layout)  # Terminal geri eklendi
        self.setup_timers()
        
        # Always on top artık kullanılmıyor, timer gereksiz

    def setup_top_section(self, main_layout):
        top_layout = QHBoxLayout()
        main_layout.addLayout(top_layout)
        
        self.setup_fav_coin_panel(top_layout)
        self.setup_dynamic_coin_panel(top_layout)
        self.setup_wallet_and_entry_panel(top_layout)

    def setup_fav_coin_panel(self, top_layout):
        fav_coin_group = QGroupBox()
        fav_coin_group.setMinimumSize(430, 220)  # Yüksekliği artırdım
        fav_coin_group.setStyleSheet("""
            QGroupBox {
                background-color: #696969;
                border: 1px solid gray;
                border-radius: 15px;
            }
        """)
        fav_coin_layout = QGridLayout(fav_coin_group)
        fav_coin_layout.setContentsMargins(3, 3, 3, 3)  # Küçük margin
        fav_coin_layout.setSpacing(3)  # Küçük spacing
        # Define common button styles for different operations
        hard_buy_style = (
            "QPushButton { background-color: darkgreen; color: white; border-radius: 6px; min-height: 25px; font-size: 12px; font-weight: bold; }"
            "QPushButton:hover { background-color: blue; }"
        )
        soft_buy_style = (
            "QPushButton { background-color: #089000; color: white; border-radius: 6px; min-height: 25px; font-size: 12px; font-weight: bold; }"
            "QPushButton:hover { background-color: blue; }"
        )
        soft_sell_style = (
            "QPushButton { background-color: #800000; color: white; border-radius: 6px; min-height: 25px; font-size: 12px; font-weight: bold; }"
            "QPushButton:hover { background-color: blue; }"
        )
        hard_sell_style = (
            "QPushButton { background-color: #400000; color: white; border-radius: 6px; min-height: 25px; font-size: 12px; font-weight: bold; }"
            "QPushButton:hover { background-color: blue; }"
        )
        coin_label_style = (
            "QPushButton { background-color: gray; color: white; border-radius: 6px; min-height: 45px; font-size: 11px; font-weight: bold; }"
            "QPushButton:hover { background-color: blue; }"
        )
        # Row 0: Hard Buy buttons
        for col in range(FAVORITE_COIN_COUNT):
            btn = self.create_order_button("Hard Buy", hard_buy_style, lambda _, c=col: order_buttons(self, "Hard_Buy", c))
            fav_coin_layout.addWidget(btn, 0, col)
        # Row 1: Soft Buy buttons
        for col in range(FAVORITE_COIN_COUNT):
            btn = self.create_order_button("Soft Buy", soft_buy_style, lambda _, c=col: order_buttons(self, "Soft_Buy", c))
            fav_coin_layout.addWidget(btn, 1, col)
        # Row 2: Coin label buttons
        for col in range(FAVORITE_COIN_COUNT):
            btn = self.create_order_button(f"COIN_{col}\n0.00", coin_label_style, lambda _, b=None, c=col: self.show_coin_details(self.fav_coin_buttons[c] if len(self.fav_coin_buttons) > c else btn))
            fav_coin_layout.addWidget(btn, 2, col)
            self.fav_coin_buttons.append(btn)
        # Row 3: Soft Sell buttons
        for col in range(FAVORITE_COIN_COUNT):
            btn = self.create_order_button("Soft Sell", soft_sell_style, lambda _, c=col: order_buttons(self, "Soft_Sell", c))
            fav_coin_layout.addWidget(btn, 3, col)
        # Row 4: Hard Sell buttons
        for col in range(FAVORITE_COIN_COUNT):
            btn = self.create_order_button("Hard Sell", hard_sell_style, lambda _, c=col: order_buttons(self, "Hard_Sell", c))
            fav_coin_layout.addWidget(btn, 4, col)
        top_layout.addWidget(fav_coin_group)

    def create_order_button(self, text, style, callback):
        btn = QPushButton(text)
        btn.setStyleSheet(style)
        btn.clicked.connect(callback)
        return btn

    def setup_dynamic_coin_panel(self, top_layout):
        dyn_coin_group = QGroupBox()
        dyn_coin_group.setMinimumSize(100, 20)
        dyn_coin_group.setStyleSheet("""
            QGroupBox {
                background-color: #696969;
                border: 1px solid gray;
                border-radius: 15px;
            }
        """)
        dyn_coin_layout = QVBoxLayout(dyn_coin_group)
        dyn_coin_layout.setContentsMargins(5, 5, 5, 5)
        dyn_coin_layout.setSpacing(8)  # Genel spacing'i artırdım

        # Dynamic coin buttons for buy/sell operations
        hard_buy_style = (
            "QPushButton { background-color: darkgreen; color: white; border-radius: 8px; min-height: 28px; font-size: 12px; font-weight: bold; }"
            "QPushButton:hover { background-color: blue; }"
        )
        soft_buy_style = (
            "QPushButton { background-color: #089000; color: white; border-radius: 8px; min-height: 28px; font-size: 12px; font-weight: bold; }"
            "QPushButton:hover { background-color: blue; }"
        )
        soft_sell_style = (
            "QPushButton { background-color: #800000; color: white; border-radius: 8px; min-height: 28px; font-size: 12px; font-weight: bold; }"
            "QPushButton:hover { background-color: blue; }"
        )
        hard_sell_style = (
            "QPushButton { background-color: #400000; color: white; border-radius: 8px; min-height: 28px; font-size: 12px; font-weight: bold; }"
            "QPushButton:hover { background-color: blue; }"
        )
        coin_label_style = (
            "QPushButton { background-color: gray; color: white; border-radius: 8px; min-height: 55px; font-size: 11px; font-weight: bold; }"
            "QPushButton:hover { background-color: blue; }"
        )

        btn_dyn_hard_buy = self.create_order_button("Hard Buy", hard_buy_style, lambda _, c=DYNAMIC_COIN_INDEX: order_buttons(self, "Hard_Buy", c))
        dyn_coin_layout.addWidget(btn_dyn_hard_buy)

        btn_dyn_soft_buy = self.create_order_button("Soft Buy", soft_buy_style, lambda _, c=DYNAMIC_COIN_INDEX: order_buttons(self, "Soft_Buy", c))
        dyn_coin_layout.addWidget(btn_dyn_soft_buy)

        btn_dyn_coin = self.create_order_button("DYN_COIN\n0.00", coin_label_style, None)
        btn_dyn_coin.clicked.connect(lambda _, b=btn_dyn_coin: self.show_coin_details(b))
        self.dyn_coin_button = btn_dyn_coin
        dyn_coin_layout.addWidget(self.dyn_coin_button)

        # Coin butonu ile sell butonları arasına daha büyük boşluk ekle
        dyn_coin_layout.addSpacing(20)

        btn_dyn_soft_sell = self.create_order_button("Soft Sell", soft_sell_style, lambda _, c=DYNAMIC_COIN_INDEX: order_buttons(self, "Soft_Sell", c))
        dyn_coin_layout.addWidget(btn_dyn_soft_sell)

        btn_dyn_hard_sell = self.create_order_button("Hard Sell", hard_sell_style, lambda _, c=DYNAMIC_COIN_INDEX: order_buttons(self, "Hard_Sell", c))
        dyn_coin_layout.addWidget(btn_dyn_hard_sell)

        top_layout.addWidget(dyn_coin_group)

    def setup_wallet_and_entry_panel(self, top_layout):
        right_side_layout = QVBoxLayout()
        right_side_layout.setSpacing(5)  # Boşluğu azalttım (5 → 2)

        # Wallet Frame with Settings button and wallet balance
        wallet_frame = QFrame()
        wallet_frame.setFixedSize(200, 95)  # Boyutu biraz daha büyüttüm
        wallet_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #1A1A2E, stop:1 #16213E);
                color: #E8E8E8;
                border-radius: 15px;
                border: 2px solid #0F3460;
            }
        """)
        wallet_layout = QVBoxLayout(wallet_frame)
        wallet_layout.setContentsMargins(8, 8, 8, 8)  # Daha dengeli margin
        wallet_layout.setSpacing(2)  # Elemanlar arası boşluk
        wallet_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)  # Üstten hizala

        # Settings button at the top of the wallet frame
        btn_settings = QPushButton("Settings")
        btn_settings.setFixedSize(75, 28)  # Biraz daha büyük buton
        btn_settings.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #0F3460, stop:1 #16213E);
                color: #E8E8E8;
                border: 1px solid #533483;
                border-radius: 8px;
                font-size: 11px; 
                font-weight: bold;
                padding: 3px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #533483, stop:1 #0F3460);
                border: 1px solid #E94560;
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #16213E, stop:1 #1A1A2E);
                border: 1px solid #533483;
            }
        """)
        btn_settings.clicked.connect(self.open_settings)
        wallet_layout.addWidget(btn_settings, alignment=Qt.AlignHCenter)

        # Wallet balance label
        self.lbl_wallet = QLabel("Wallet\n$0.00")
        self.lbl_wallet.setAlignment(Qt.AlignCenter)
        self.lbl_wallet.setStyleSheet("""
            QLabel {
                font-size: 13px; 
                font-weight: bold; 
                color: #F0F3FF;
                background: transparent;
                border: none;
                padding: 5px;
                margin: 2px;
            }
        """)
        wallet_layout.addWidget(self.lbl_wallet, alignment=Qt.AlignHCenter)

        right_side_layout.addWidget(wallet_frame)

        # Coin Entry Frame for submitting new coins
        entry_frame = QFrame()
        entry_frame.setFixedSize(200, 120)  # Yüksekliği artırdım
        entry_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #1A1A2E, stop:1 #16213E);
                color: #E8E8E8;
                border-radius: 12px;
                border: 1px solid #0F3460;
            }
        """)
        entry_layout = QVBoxLayout(entry_frame)
        entry_layout.setContentsMargins(8, 6, 8, 6)  # Yan margin'leri artırdım
        entry_layout.setSpacing(4)

        lbl_entry = QLabel("Enter coin")
        lbl_entry.setAlignment(Qt.AlignCenter)
        lbl_entry.setStyleSheet("""
            QLabel {
                font-size: 11px; 
                font-weight: bold;
                color: #F0F3FF;
                background: transparent;
                border: none;
                margin: 1px;
            }
        """)
        entry_layout.addWidget(lbl_entry)

        self.coin_input = QLineEdit()
        self.coin_input.setStyleSheet("""
            QLineEdit {
                font-size: 12px; 
                height: 28px;
                min-height: 28px;
                background-color: #16213E;
                color: #E8E8E8;
                border: 1px solid #533483;
                border-radius: 6px;
                padding: 4px 8px;
            }
            QLineEdit:focus {
                border: 1px solid #E94560;
                background-color: #1A1A2E;
            }
        """)
        self.coin_input.returnPressed.connect(self.submit_coin)
        entry_layout.addWidget(self.coin_input)

        # Input ile submit button arasına boşluk ekle
        entry_layout.addSpacing(8)

        btn_submit = QPushButton("Submit")
        btn_submit.setStyleSheet("""
            QPushButton { 
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #0F3460, stop:1 #16213E);
                color: #E8E8E8; 
                border: 1px solid #533483;
                border-radius: 6px; 
                font-size: 11px; 
                height: 26px; 
                min-height: 26px;
                font-weight: bold;
                padding: 3px;
            }
            QPushButton:hover { 
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #533483, stop:1 #0F3460);
                border: 1px solid #E94560;
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #16213E, stop:1 #1A1A2E);
            }
        """)
        btn_submit.clicked.connect(self.submit_coin)
        entry_layout.addWidget(btn_submit)

        right_side_layout.addWidget(entry_frame)
        top_layout.addLayout(right_side_layout)

    def setup_terminal(self, main_layout):
        # Terminal for displaying logs and messages
        self.terminal = QPlainTextEdit()
        self.terminal.setReadOnly(True)
        self.terminal.setFixedHeight(150)  # Sabit yükseklik
        self.terminal.setStyleSheet("""
            QPlainTextEdit {
                background-color: black;
                color: white;
                border-radius: 8px;
                padding: 5px;
                font-family: Consolas, monospace;
                font-size: 12px;
                font-weight: bold;
            }
        """)
        main_layout.addWidget(self.terminal)

    def setup_timers(self):
        # Timer to update coin prices every second
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_coin_prices)
        self.timer.start(1000)  # 1000 ms = 1 second

        # Timer to update wallet balance every second
        self.wallet_timer = QTimer(self)
        self.wallet_timer.timeout.connect(self.update_wallet)
        self.wallet_timer.start(1000)  # 1000 ms = 1 second

    def show_and_focus(self):
        """Pencereyi göster ve ön plana çıkar."""
        self.show()
        self.raise_()
        self.activateWindow()
        
        # Windows'ta ek ön plana çıkarma
        import sys
        if sys.platform == "win32":
            try:
                import ctypes
                hwnd = int(self.winId())
                ctypes.windll.user32.SetForegroundWindow(hwnd)
                ctypes.windll.user32.BringWindowToTop(hwnd)
                ctypes.windll.user32.ShowWindow(hwnd, 1)  # SW_SHOWNORMAL
            except Exception as e:
                logging.warning(f"Could not bring window to front: {e}")

    def append_to_terminal(self, text):
        """Terminal'e text ekler."""
        if hasattr(self, 'terminal'):
            self.terminal.appendPlainText(text)
        else:
            print(f"LOG: {text}")

    def show_error_message(self, message):
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setWindowTitle("Error")
        msg_box.setText(message)
        msg_box.exec()

    def submit_coin(self):
        """Handles coin submission from the input field."""
        coin_name = self.coin_input.text().strip()
        if coin_name:
            try:
                result = set_dynamic_coin_symbol(coin_name)
                if result and result.get('success'):
                    # Extract binance_ticker from the result dictionary
                    binance_ticker = result.get('binance_ticker')
                    view_coin_name = result.get('view_coin_name')
                    
                    # Subscribe to the new dynamic coin via WebSocket
                    subscribe_to_dynamic_coin(binance_ticker)
                    self.append_to_terminal(f"New coin submitted: {coin_name} -> {view_coin_name} ({binance_ticker})")
                    logging.info(f"Successfully set dynamic coin to {view_coin_name} ({binance_ticker}) and subscribed to WebSocket")
                else:
                    error_msg = result.get('error_message', 'Unknown error') if result else 'Failed to set coin'
                    self.append_to_terminal(f"Failed to set coin {coin_name}: {error_msg}")
                    logging.warning(f"Failed to set dynamic coin {coin_name}: {error_msg}")
            except ValueError as e:
                self.append_to_terminal(f"Error: {str(e)}")
                logging.error(f"Symbol validation error: {e}")
            except Exception as e:
                self.append_to_terminal(f"Unexpected error setting coin: {coin_name}")
                logging.exception(f"Unexpected error in submit_coin: {e}")
        self.coin_input.clear()

    def update_coin_prices(self):
        """Updates the prices of coins displayed on the buttons."""
        try:
            data = load_fav_coin()  # Read JSON file
            # Update favorite coin buttons
            for i, btn in enumerate(self.fav_coin_buttons):
                coin_data = data['coins'][i]
                symbol = coin_data.get('symbol', f"COIN_{i}")
                price = coin_data.get('values', {}).get('current', "0.00")
                # Format symbol using view_coin_format for display
                display_symbol = view_coin_format(symbol)
                if btn.text() != f"{display_symbol}\n{price}":
                    btn.setText(f"{display_symbol}\n{price}")
            # Update dynamic coin button
            dyn_data = data['dynamic_coin'][0]
            symbol = dyn_data.get('symbol', "DYN_COIN")
            price = dyn_data.get('values', {}).get('current', "0.00")
            # Format symbol using view_coin_format for display
            display_symbol = view_coin_format(symbol)
            if self.dyn_coin_button.text() != f"{display_symbol}\n{price}":
                self.dyn_coin_button.setText(f"{display_symbol}\n{price}")
        except Exception as e:
            self.show_error_message(f"Error updating coin prices: {e}")

    def update_wallet(self):
        """Updates the wallet balance displayed in the wallet frame."""
        try:
            available_usdt = retrieve_usdt_balance(self.client)
            new_text = f"Wallet\n${available_usdt:.2f}"
            if self.lbl_wallet.text() != new_text:
                self.lbl_wallet.setText(new_text)
        except Exception as e:
            self.show_error_message(f"Error updating wallet: {e}")

    def open_settings(self):
        """Opens the settings window when the Settings button is clicked."""
        dlg = SettingsWindow(self)
        dlg.exec()

    def show_coin_details(self, btn):
        """Displays a candlestick chart for the selected coin."""
        display_symbol = btn.text().split("\n")[0]
        # Convert display format (BTC-USDT) back to Binance format (BTCUSDT) for API calls
        symbol = display_symbol.replace('-', '') if '-' in display_symbol else display_symbol
        try:
            # Interval bilgisini Preferences.txt'den oku
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
            ax = axlist[0]  # Get the first axis

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

            # Sol üstte interval bilgisini göster (isteğe bağlı, başlıkta da var)
            # ax.text(0.02, 0.90, f"Interval: {interval}m", transform=ax.transAxes, fontsize=10, color='yellow', verticalalignment='top')

            plt.show()
        except Exception as e:
            self.append_to_terminal(f"Error displaying chart for {symbol}: {e}")

class SettingsWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumSize(350, 350)

        # Read preferences from the preferences file
        prefs = {}
        with open(PREFERENCES_FILE, 'r') as f:
            for line in f:
                # Parse lines that contain key-value pairs and are not comments
                if "=" in line and not line.strip().startswith("#"):
                    key, val = line.split("=", 1)
                    prefs[key.strip()] = val.strip().lstrip("%")
        
        # Store original preferences to allow change detection
        self.original_prefs = prefs.copy()

        # Set up the layout for the settings window
        layout = QVBoxLayout(self)
        self.pref_edits = {}

        # Add input fields for specific preferences
        for key in ("soft_risk", "hard_risk", "accepted_price_volatility"):
            layout.addWidget(QLabel(key.replace("_", " ").title()))  # Add label for the preference
            edit = QLineEdit(prefs.get(key, ""))  # Create input field with current value
            self.pref_edits[key] = edit
            layout.addWidget(edit)

        # --- Coin Chart Interval ---
        layout.addWidget(QLabel("Coin Chart Interval (1, 5, 15)", self))
        interval_val = prefs.get("chart_interval", "1")
        self.interval_edit = QLineEdit(interval_val)
        self.interval_edit.setPlaceholderText("1, 5 veya 15")
        layout.addWidget(self.interval_edit)

        # Add input fields for favorite coins
        layout.addWidget(QLabel("Favorite Coins"))
        self.original_coins = [c.strip() for c in prefs.get("favorite_coins", "").split(",")]
        self.fav_edits = []
        for coin in self.original_coins:
            edit = QLineEdit(coin)  # Create input field for each favorite coin
            self.fav_edits.append(edit)
            layout.addWidget(edit)

        # Add a save button to save the settings
        btn_save = QPushButton("Save")
        btn_save.clicked.connect(self.save_settings)  # Connect save button to save_settings method
        layout.addWidget(btn_save)

    def save_settings(self):
        """
        Save the updated settings and preferences.
        Only updates and appends information for changed preferences.
        """
        # Update preferences if there are changes
        for key, edit in self.pref_edits.items():
            new_val = edit.text().strip()
            if new_val and new_val != self.original_prefs.get(key, ""):
                msg = set_preference(key, new_val)  # Update the preference
                self.parent().append_to_terminal(msg)  # Log the update in the terminal

        # --- Coin Chart Interval ---
        interval_val = self.interval_edit.text().strip()
        if interval_val not in ("1", "5", "15"):
            QMessageBox.critical(self, "Invalid Interval", "Interval must be 1, 5, or 15.")
            return
        if interval_val != self.original_prefs.get("chart_interval", "1"):
            msg = set_preference("chart_interval", interval_val)
            self.parent().append_to_terminal(msg)

        # Check favorite coins one by one and update only if there is a change
        for old, edit in zip(self.original_coins, self.fav_edits):
            new_coin = edit.text().strip().upper()
            if new_coin and new_coin != old:
                msg = update_favorite_coin(old, new_coin)  # Update the favorite coin
                self.parent().append_to_terminal(msg)  # Log the update in the terminal

        # Close the settings window after saving
        self.accept()



def load_fav_coin():
    """Backward compatibility wrapper for load_fav_coins()"""
    return load_fav_coins()

def retrieve_coin_symbol(col):
    data = load_fav_coin()
    coins = data['coins']
    if col == DYNAMIC_COIN_INDEX:
        return data['dynamic_coin'][0]['symbol']
    else:
        return coins[col]['symbol']
    
def order_buttons(self, style, col):
    """
    Handles buy/sell operations for a given coin and style.
    Parameters:
        style (str): The type of operation ("Hard_Buy", "Hard_Sell", "Soft_Buy", "Soft_Sell").
        col (int): The column index of the coin.
    """
    try:
        symbol = retrieve_coin_symbol(col)
        old_balance = retrieve_usdt_balance(self.client)
        order_paper = make_order(style, symbol)

        amount = float(order_paper['fills'][0]['qty'])
        price = float(order_paper['fills'][0]['price'])
        cost_or_received = float(order_paper.get('cummulativeQuoteQty', amount * price))
        new_balance = retrieve_usdt_balance(self.client)

        if "Buy" in style:
            actual_diff = old_balance - new_balance
        else:
            actual_diff = new_balance - old_balance

        operation = "BUY" if "Buy" in style else "SELL"
        action_type = "H" if "Hard" in style else "S"
        
        # Compact terminal output
        self.append_to_terminal(
            f"[{action_type}] {operation} {symbol} | "
            f"{amount:.2f} @ ${price:.2f} | "
            f"Total: ${cost_or_received:.2f} | "
            f"Balance: ${new_balance:.2f}"
        )
    except Exception as e:
        self.append_to_terminal(f"Error processing {style} for {symbol}: {e}")





def initialize_gui():
    """GUI'yi başlatır."""
    try:
        logging.info("Initializing GUI...")
        
        # Binance client'ı hazırla
        try:
            client = prepare_client()
            logging.info("Binance client prepared successfully")
        except Exception as e:
            logging.error(f"Error preparing Binance client: {e}")
            # Client olmadan da GUI'yi başlat (demo mode)
            client = None
        
        # QApplication kontrolü
        app = QApplication.instance()
        if not app:
            logging.error("QApplication not found! This should be created in main.py")
            return -1
        
        # Ana pencereyi oluştur
        logging.info("Creating main window...")
        window = MainWindow(client)
        window.setWindowTitle("Binance Terminal - Professional Trading Interface")
        window.resize(600, 400)  # Daha küçük başlangıç boyutu
        
        # Pencereyi göster ve ön plana çıkar
        logging.info("Showing main window...")
        window.show_and_focus()
        
        # Ek olarak Qt metodlarıyla da dene
        window.raise_()
        window.activateWindow()
        
        # Windows'ta ek olarak ön plana zorla çıkarmak için
        import sys
        if sys.platform == "win32":
            import ctypes
            from ctypes import wintypes
            
            # Windows API fonksiyonları
            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32
            
            try:
                # Pencere handle'ını al
                hwnd = int(window.winId())
                
                # Pencereyi ön plana çıkar
                user32.SetForegroundWindow(hwnd)
                user32.SetActiveWindow(hwnd)
                user32.ShowWindow(hwnd, 1)  # SW_SHOWNORMAL
                user32.BringWindowToTop(hwnd)
                
                # Görev çubuğunda yanıp sönsün
                user32.FlashWindow(hwnd, True)
                
                logging.info("Window brought to foreground using Windows API")
            except Exception as e:
                logging.warning(f"Could not use Windows API to bring window to front: {e}")
        
        # WebSocket thread'ini başlat (opsiyonel)
        try:
            if client:
                background_thread = threading.Thread(target=start_price_websocket, daemon=True)
                background_thread.start()
                logging.info("WebSocket thread started")
            else:
                logging.warning("WebSocket thread skipped - no client available")
        except Exception as e:
            logging.error(f"Error starting WebSocket thread: {e}")
        
        # Event loop'u başlat
        logging.info("Starting GUI event loop...")
        return app.exec()
        
    except Exception as e:
        logging.exception(f"Error in initialize_gui: {e}")
        return -1



def main():

    client = prepare_client()
    
    # Start background thread for price_update function
    background_thread = threading.Thread(target=start_price_websocket, daemon=True)
    background_thread.start()

    app = QApplication(sys.argv)
    window = MainWindow(client)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
