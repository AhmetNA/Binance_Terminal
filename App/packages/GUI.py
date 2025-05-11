import json
import sys

from .Order_Func import *
from .Price_Update import *
from .Coin_Chart import *
from .SetPreferences import *

import matplotlib.pyplot as plt
import mplfinance as mpf  # for candlestick charts
import matplotlib.patches as mpatches

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QPushButton, QLabel, QLineEdit, QPlainTextEdit, QFrame, QDialog
)


from PySide6.QtCore import Qt, QTimer
import threading

FAVORITE_COIN_COUNT = 5
DYNAMIC_COIN_INDEX = 6

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
        self.client = client
        self.setWindowTitle("GAIN")
        self.resize(750, 400)
        self.fav_coin_buttons = []
        self.dyn_coin_button = None
        self.setup_ui()

    def setup_ui(self):
        # Set up the central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(5)
        self.setup_top_section(main_layout)
        self.setup_terminal(main_layout)
        self.setup_timers()

    def setup_top_section(self, main_layout):
        top_layout = QHBoxLayout()
        main_layout.addLayout(top_layout)
        self.setup_fav_coin_panel(top_layout)
        self.setup_dynamic_coin_panel(top_layout)
        self.setup_wallet_and_entry_panel(top_layout)

    def setup_fav_coin_panel(self, top_layout):
        fav_coin_group = QGroupBox()
        fav_coin_group.setMinimumSize(430, 250)
        fav_coin_group.setStyleSheet("""
            QGroupBox {
                background-color: #696969;
                border: 1px solid gray;
                border-radius: 15px;
            }
        """)
        fav_coin_layout = QGridLayout(fav_coin_group)
        fav_coin_layout.setContentsMargins(5, 5, 5, 5)
        fav_coin_layout.setSpacing(5)
        # Define common button styles for different operations
        hard_buy_style = (
            "QPushButton { background-color: darkgreen; color: white; border-radius: 8px; min-height: 30px; }"
            "QPushButton:hover { background-color: blue; }"
        )
        soft_buy_style = (
            "QPushButton { background-color: #089000; color: white; border-radius: 8px; min-height: 30px; }"
            "QPushButton:hover { background-color: blue; }"
        )
        soft_sell_style = (
            "QPushButton { background-color: #800000; color: white; border-radius: 8px; min-height: 30px; }"
            "QPushButton:hover { background-color: blue; }"
        )
        hard_sell_style = (
            "QPushButton { background-color: #400000; color: white; border-radius: 8px; min-height: 30px; }"
            "QPushButton:hover { background-color: blue; }"
        )
        coin_label_style = (
            "QPushButton { background-color: gray; color: white; border-radius: 8px; min-height: 50px; }"
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
        dyn_coin_layout.setSpacing(5)

        # Dynamic coin buttons for buy/sell operations
        hard_buy_style = (
            "QPushButton { background-color: darkgreen; color: white; border-radius: 8px; min-height: 30px; }"
            "QPushButton:hover { background-color: blue; }"
        )
        soft_buy_style = (
            "QPushButton { background-color: #089000; color: white; border-radius: 8px; min-height: 30px; }"
            "QPushButton:hover { background-color: blue; }"
        )
        soft_sell_style = (
            "QPushButton { background-color: #800000; color: white; border-radius: 8px; min-height: 30px; }"
            "QPushButton:hover { background-color: blue; }"
        )
        hard_sell_style = (
            "QPushButton { background-color: #400000; color: white; border-radius: 8px; min-height: 30px; }"
            "QPushButton:hover { background-color: blue; }"
        )
        coin_label_style = (
            "QPushButton { background-color: gray; color: white; border-radius: 8px; min-height: 50px; }"
            "QPushButton:hover { background-color: blue; }"
        )

        btn_dyn_hard_buy = self.create_order_button("Hard Buy", hard_buy_style, lambda _, c=DYNAMIC_COIN_INDEX: order_buttons(self, "Hard_Buy", c))
        dyn_coin_layout.addWidget(btn_dyn_hard_buy)

        btn_dyn_soft_buy = self.create_order_button("Soft Buy", soft_buy_style, lambda _, c=DYNAMIC_COIN_INDEX: order_buttons(self, "Soft_Buy", c))
        dyn_coin_layout.addWidget(btn_dyn_soft_buy)

        self.dyn_coin_button = self.create_order_button("DYN_COIN\n0.00", coin_label_style, lambda _, b=self.dyn_coin_button: self.show_coin_details(b))
        dyn_coin_layout.addWidget(self.dyn_coin_button)

        btn_dyn_soft_sell = self.create_order_button("Soft Sell", soft_sell_style, lambda _, c=DYNAMIC_COIN_INDEX: order_buttons(self, "Soft_Sell", c))
        dyn_coin_layout.addWidget(btn_dyn_soft_sell)

        btn_dyn_hard_sell = self.create_order_button("Hard Sell", hard_sell_style, lambda _, c=DYNAMIC_COIN_INDEX: order_buttons(self, "Hard_Sell", c))
        dyn_coin_layout.addWidget(btn_dyn_hard_sell)

        top_layout.addWidget(dyn_coin_group)

    def setup_wallet_and_entry_panel(self, top_layout):
        right_side_layout = QVBoxLayout()
        right_side_layout.setSpacing(10)

        # Wallet Frame with Settings button and wallet balance
        wallet_frame = QFrame()
        wallet_frame.setFixedSize(200, 100)  # reduced height
        wallet_frame.setStyleSheet("""
            QFrame {
            background-color: #089000;
            color: black;
            border-radius: 15px;
            }
        """)
        wallet_layout = QVBoxLayout(wallet_frame)
        wallet_layout.setContentsMargins(5, 5, 5, 5)
        wallet_layout.setAlignment(Qt.AlignCenter)  # Center-align layout

        # Settings button at the top of the wallet frame
        btn_settings = QPushButton("Settings")
        btn_settings.setFixedSize(70, 25)
        btn_settings.clicked.connect(self.open_settings)
        wallet_layout.addWidget(btn_settings, alignment=Qt.AlignHCenter)

        # Wallet balance label
        self.lbl_wallet = QLabel("Wallet\n$0.00")
        self.lbl_wallet.setAlignment(Qt.AlignCenter)
        wallet_layout.addWidget(self.lbl_wallet, alignment=Qt.AlignHCenter)

        right_side_layout.addWidget(wallet_frame)

        # Coin Entry Frame for submitting new coins
        entry_frame = QFrame()
        entry_frame.setFixedSize(200, 80)
        entry_frame.setStyleSheet("""
            QFrame {
                background-color: gray;
                color: black;
                border-radius: 15px;
            }
        """)
        entry_layout = QVBoxLayout(entry_frame)
        entry_layout.setContentsMargins(10, 10, 10, 10)

        lbl_entry = QLabel("Enter coin name")
        lbl_entry.setAlignment(Qt.AlignCenter)
        entry_layout.addWidget(lbl_entry)

        self.coin_input = QLineEdit()
        self.coin_input.returnPressed.connect(self.submit_coin)
        entry_layout.addWidget(self.coin_input)

        btn_submit = QPushButton("Submit")
        btn_submit.setStyleSheet("QPushButton { background-color: gray; color: black; border-radius: 8px; }")
        btn_submit.clicked.connect(self.submit_coin)
        entry_layout.addWidget(btn_submit)

        right_side_layout.addWidget(entry_frame)
        top_layout.addLayout(right_side_layout)

    def setup_terminal(self, main_layout):
        # Terminal for displaying logs and messages
        self.terminal = QPlainTextEdit()
        self.terminal.setReadOnly(True)
        self.terminal.setStyleSheet("""
            QPlainTextEdit {
                background-color: black;
                color: white;
                border-radius: 8px;
                padding: 5px;
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

    def append_to_terminal(self, text):
        """Appends text to the terminal."""
        self.terminal.appendPlainText(text)

    def submit_coin(self):
        """Handles coin submission from the input field."""
        coin_name = self.coin_input.text()
        if coin_name:
            set_dynamic_coin_symbol(coin_name)
            self.append_to_terminal(f"New coin submitted: {coin_name}")
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
                btn.setText(f"{symbol}\n{price}")
            # Update dynamic coin button
            dyn_data = data['dynamic_coin'][0]
            symbol = dyn_data.get('symbol', "DYN_COIN")
            price = dyn_data.get('values', {}).get('current', "0.00")
            self.dyn_coin_button.setText(f"{symbol}\n{price}")
        except Exception as e:
            self.append_to_terminal(f"Error updating coin prices: {e}")

    def update_wallet(self):
        """Updates the wallet balance displayed in the wallet frame."""
        try:
            available_usdt = retrieve_usdt_balance(self.client)
            self.lbl_wallet.setText(f"Wallet\n${available_usdt:.2f}")
        except Exception as e:
            self.append_to_terminal(f"Error updating wallet: {e}")

    def open_settings(self):
        """Opens the settings window when the Settings button is clicked."""
        dlg = SettingsWindow(self)
        dlg.exec()

    def show_coin_details(self, btn):
        """Displays a candlestick chart for the selected coin."""
        symbol = btn.text().split("\n")[0]
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
            ax = axlist[0]  # Get the first axis

            # Add title and adjust figure size
            fig.suptitle(f"{symbol} Candle Chart", fontsize=12)
            fig.set_size_inches(6, 4)

            # Add general info box with price details
            info_text = (f"First Price: {first_price:.2f}\n"
                         f"Last Price: {last_price:.2f}\n"
                         f"Overall Change: {price_change_pct:.2f}%")
            props = dict(boxstyle='round', facecolor='gray', alpha=0.5)
            ax.text(0.02, 0.98, info_text, transform=ax.transAxes, fontsize=8,
                    verticalalignment='top', bbox=props)

            plt.tight_layout()
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

        # Check favorite coins one by one and update only if there is a change
        for old, edit in zip(self.original_coins, self.fav_edits):
            new_coin = edit.text().strip().upper()
            if new_coin and new_coin != old:
                msg = update_favorite_coin(old, new_coin)  # Update the favorite coin
                self.parent().append_to_terminal(msg)  # Log the update in the terminal

        # Close the settings window after saving
        self.accept()



def load_fav_coin():
    json_path = FAV_COINS_FILE
    with open(json_path, 'r') as file:
        return json.load(file)

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
        cost = amount * price
        new_balance = retrieve_usdt_balance(self.client)

        operation = "Bought" if "Buy" in style else "Sold"
        action_type = "Hard" if "Hard" in style else "Soft"
        balance_change = f"Balance: previous {old_balance:.2f} -> current {new_balance:.2f}"

        self.append_to_terminal(
            f"{action_type} {operation} {symbol}: {'cost' if 'Buy' in style else 'received'} {cost:.2f} USDT "
            f"at {price:.2f} for {amount:.2f}. {balance_change}"
        )
    except Exception as e:
        self.append_to_terminal(f"Error processing {style} for {symbol}: {e}")





def initialize_gui():

    client = prepare_client()
    
    # Start background thread for price_update function
    background_thread = threading.Thread(target=start_price_websocket, daemon=True)
    background_thread.start()

    app = QApplication(sys.argv)
    window = MainWindow(client)
    window.show()
    sys.exit(app.exec())



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