import json
import sys

from .Order_Func import *
from .Price_Update import *
from .Coin_Chart import *

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QPushButton, QLabel, QLineEdit, QPlainTextEdit, QFrame
)
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
        self.client = client
        self.setWindowTitle("GAIN")
        self.resize(750, 400)

        
        self.fav_coin_buttons = []
        self.dyn_coin_button = None
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(5)
        
        # ÜST KISIM: Favori Coin Paneli + Dinamik Coin Paneli + (Cüzdan + Coin Entry)
        top_layout = QHBoxLayout()
        main_layout.addLayout(top_layout)
        
        # 1) Favori Coin Paneli (5 sütun)
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
        # Ortak buton stilleri
        hard_buy_style   = (
            "QPushButton { background-color: darkgreen; color: white; border-radius: 8px; min-height: 30px; }"
            "QPushButton:hover { background-color: blue; }"
        )
        soft_buy_style   = (
            "QPushButton { background-color: #089000; color: white; border-radius: 8px; min-height: 30px; }"
            "QPushButton:hover { background-color: blue; }"
        )
        soft_sell_style  = (
            "QPushButton { background-color: #800000; color: white; border-radius: 8px; min-height: 30px; }"
            "QPushButton:hover { background-color: blue; }"
        )
        hard_sell_style  = (
            "QPushButton { background-color: #400000; color: white; border-radius: 8px; min-height: 30px; }"
            "QPushButton:hover { background-color: blue; }"
        )
        coin_label_style = (
            "QPushButton { background-color: gray; color: white; border-radius: 8px; min-height: 50px; }"
            "QPushButton:hover { background-color: blue; }"
        )
        # Satır 0: Hard Buy
        for col in range(5):
            btn = QPushButton("Hard Buy")
            btn.setStyleSheet(hard_buy_style)
            btn.clicked.connect(lambda _, c=col: order_buttons(self, "Hard_Buy", c))
            fav_coin_layout.addWidget(btn, 0, col)
        
        # Satır 1: Soft Buy
        for col in range(5):
            btn = QPushButton("Soft Buy")
            btn.setStyleSheet(soft_buy_style)
            btn.clicked.connect(lambda _, c=col: order_buttons(self, "Soft_Buy", c))
            fav_coin_layout.addWidget(btn, 1, col)
        
        # Satır 2: Coin etiket butonları (JSON'dan alınan isim ve fiyat)
        for col in range(5):
            btn = QPushButton(f"COIN_{col}\n0.00")
            btn.setStyleSheet(coin_label_style)
            btn.clicked.connect(lambda _, b=btn: self.show_coin_details(b))
            fav_coin_layout.addWidget(btn, 2, col)
            self.fav_coin_buttons.append(btn)
        
        # Satır 3: Soft Sell
        for col in range(5):
            btn = QPushButton("Soft Sell")
            btn.setStyleSheet(soft_sell_style)
            btn.clicked.connect(lambda _, c=col: order_buttons(self, "Soft_Sell", c))
            fav_coin_layout.addWidget(btn, 3, col)
        
        # Satır 4: Hard Sell
        for col in range(5):
            btn = QPushButton("Hard Sell")
            btn.setStyleSheet(hard_sell_style)
            btn.clicked.connect(lambda _, c=col: order_buttons(self, "Hard_Sell", c))
            fav_coin_layout.addWidget(btn, 4, col)
        
        top_layout.addWidget(fav_coin_group)
        
        # 2) Dinamik Coin Paneli (Tek sütun, 5 satır)
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
        
        btn_dyn_hard_buy = QPushButton("Hard Buy")
        btn_dyn_hard_buy.setStyleSheet(hard_buy_style)
        btn_dyn_hard_buy.clicked.connect(lambda _, c=6: order_buttons(self, "Hard_Buy", c))
        dyn_coin_layout.addWidget(btn_dyn_hard_buy)
        
        btn_dyn_soft_buy = QPushButton("Soft Buy")
        btn_dyn_soft_buy.setStyleSheet(soft_buy_style)
        btn_dyn_soft_buy.clicked.connect(lambda _, c=6: order_buttons(self, "Soft_Buy", c))
        dyn_coin_layout.addWidget(btn_dyn_soft_buy)
        
        # Dinamik coin etiket butonu (JSON'dan alınan isim ve fiyat)
        self.dyn_coin_button = QPushButton("DYN_COIN\n0.00")
        self.dyn_coin_button.setStyleSheet(coin_label_style)
        self.dyn_coin_button.clicked.connect(lambda _, b=self.dyn_coin_button: self.show_coin_details(b))
        dyn_coin_layout.addWidget(self.dyn_coin_button)
        
        btn_dyn_soft_sell = QPushButton("Soft Sell")
        btn_dyn_soft_sell.setStyleSheet(soft_sell_style)
        btn_dyn_soft_sell.clicked.connect(lambda _, c=6: order_buttons(self, "Soft_Sell", c))
        dyn_coin_layout.addWidget(btn_dyn_soft_sell)
        
        btn_dyn_hard_sell = QPushButton("Hard Sell")
        btn_dyn_hard_sell.setStyleSheet(hard_sell_style)
        btn_dyn_hard_sell.clicked.connect(lambda _, c=6: order_buttons(self, "Hard_Sell", c))
        dyn_coin_layout.addWidget(btn_dyn_hard_sell)
        
        top_layout.addWidget(dyn_coin_group)
        
        # 3) Sağ kısım: (Wallet + Coin Entry)
        right_side_layout = QVBoxLayout()
        right_side_layout.setSpacing(10)
        
        wallet_frame = QFrame()
        wallet_frame.setFixedSize(200, 150)
        wallet_frame.setStyleSheet("""
            QFrame {
                background-color: #089000;
                color: black;
                border-radius: 15px;
            }
        """)
        wallet_layout = QVBoxLayout(wallet_frame)
        wallet_layout.setContentsMargins(10, 10, 10, 10)
        self.lbl_wallet = QLabel("Wallet\n$60045.69")
        self.lbl_wallet.setAlignment(Qt.AlignCenter)
        wallet_layout.addWidget(self.lbl_wallet)
        right_side_layout.addWidget(wallet_frame)
        
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
        entry_layout.addWidget(self.coin_input)
        btn_submit = QPushButton("Submit")
        btn_submit.setStyleSheet("QPushButton { background-color: gray; color: black; border-radius: 8px; }")
        btn_submit.clicked.connect(self.submit_coin)
        entry_layout.addWidget(btn_submit)
        right_side_layout.addWidget(entry_frame)
        
        top_layout.addLayout(right_side_layout)
        
        # ALT KISIM: Terminal
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
        
        # Her 1 saniyede coin fiyatlarını güncellemek için QTimer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_coin_prices)
        self.timer.start(1000)  # 1000 ms = 1 saniye

        # Her 1 saniyede cüzdanı güncellemek için QTimer
        self.wallet_timer = QTimer(self)
        self.wallet_timer.timeout.connect(self.update_wallet)
        self.wallet_timer.start(1000)  # 1000 ms = 1 saniye

    def append_to_terminal(self, text):
        self.terminal.appendPlainText(text)
    
    def submit_coin(self):
        coin_name = self.coin_input.text()
        if coin_name:
            set_dynamic_coin_symbol(coin_name)
            self.append_to_terminal(f"New coin submitted: {coin_name}")
        self.coin_input.clear()

    # Connect the QLineEdit's returnPressed signal so that hitting Enter triggers submit_coin
    def setup_coin_input(self):
        self.coin_input.returnPressed.connect(self.submit_coin)
    
    def update_coin_prices(self):
        try:
            data = load_fav_coin()  # JSON dosyasını oku
            # Favori coin butonlarının güncellenmesi
            for i, btn in enumerate(self.fav_coin_buttons):
                coin_data = data['coins'][i]
                symbol = coin_data.get('symbol', f"COIN_{i}")
                price = coin_data.get('values', {}).get('current', "0.00")
                btn.setText(f"{symbol}\n{price}")
            # Dinamik coin butonunun güncellenmesi
            dyn_data = data['dynamic_coin'][0]
            symbol = dyn_data.get('symbol', "DYN_COIN")
            price = dyn_data.get('values', {}).get('current', "0.00")
            self.dyn_coin_button.setText(f"{symbol}\n{price}")
        except Exception as e:
            self.append_to_terminal(f"Error updating coin prices: {e}")

    def update_wallet(self):
        try:
            available_usdt = retrieve_usdt_balance(self.client)
            self.lbl_wallet.setText(f"Wallet\n${available_usdt:.2f}")
        except Exception as e:
            self.append_to_terminal(f"Error updating wallet: {e}")

    def show_coin_details(self, btn):
        import matplotlib.pyplot as plt
        import mplfinance as mpf  # mum grafikler için
        import matplotlib.patches as mpatches
        symbol = btn.text().split("\n")[0]
        try:
            df = get_chart_data(symbol)
            first_price = df["Close"].iloc[0]
            last_price = df["Close"].iloc[-1]
            price_change_pct = ((last_price - first_price) / first_price) * 100

            plt.style.use('dark_background')

            # Mum grafik için renk ve stil ayarları
            mc = mpf.make_marketcolors(up='green', down='red', edge='inherit', wick='inherit')
            s  = mpf.make_mpf_style(base_mpf_style='nightclouds', marketcolors=mc)

            # returnfig=True parametresi sayesinde Figure ve Eksen listesi elde ediyoruz
            fig, axlist = mpf.plot(
                df, type='candle', style=s, returnfig=True,
                datetime_format='%H:%M:%S', xrotation=45
            )
            ax = axlist[0]  # İlk ekseni alıyoruz

            # Suptitle ve figür boyutu ayarı (küçük boyutta, fakat coin ismi de gösteriliyor)
            fig.suptitle(f"{symbol} Candle Chart", fontsize=12)
            fig.set_size_inches(6, 4)
            ax = axlist[0]  # İlk ekseni alıyoruz

            # Suptitle ve figür boyutu ayarı
            fig.suptitle(f"{symbol} Candle Chart", fontsize=16)
            fig.set_size_inches(6, 4)

            # Genel bilgi kutucuğu (ilk ve son fiyat)
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



def load_fav_coin():
    json_path = FAV_COINS_FILE
    with open(json_path, 'r') as file:
        return json.load(file)

def retrieve_coin_symbol(col):
    data = load_fav_coin()
    coins = data['coins']
    if col == 6:
        return data['dynamic_coin'][0]['symbol']
    else:
        return coins[col]['symbol']
    
def order_buttons(self, style, col):
    symbol = retrieve_coin_symbol(col)
    old_balance = retrieve_usdt_balance(self.client)
    if style == "Hard_Buy":
        order_paper = make_order("Hard_Buy", symbol)
        amount = float(order_paper['fills'][0]['qty'])
        price = float(order_paper['fills'][0]['price'])
        cost = amount * price
        new_balance = retrieve_usdt_balance(self.client)
        self.append_to_terminal(
            f"Hard Bought {symbol}: cost {cost} USDT at {price} for {amount}. "
            f"Balance: previous {old_balance:.2f} -> current {new_balance:.2f}"
        )
    elif style == "Hard_Sell":
        order_paper = make_order("Hard_Sell", symbol)
        amount = float(order_paper['fills'][0]['qty'])
        price = float(order_paper['fills'][0]['price'])
        cost = amount * price
        new_balance = retrieve_usdt_balance(self.client)
        self.append_to_terminal(
            f"Hard Sold {symbol}: received {cost} USDT at {price} for {amount}. "
            f"Balance: previous {old_balance:.2f} -> current {new_balance:.2f}"
        )
    elif style == "Soft_Buy":
        order_paper = make_order("Soft_Buy", symbol)
        amount = float(order_paper['fills'][0]['qty'])
        price = float(order_paper['fills'][0]['price'])
        cost = amount * price
        new_balance = retrieve_usdt_balance(self.client)
        self.append_to_terminal(
            f"Soft Bought {symbol}: cost {cost} USDT at {price} for {amount}. "
            f"Balance: previous {old_balance:.2f} -> current {new_balance:.2f}"
        )
    elif style == "Soft_Sell":
        order_paper = make_order("Soft_Sell", symbol)
        amount = float(order_paper['fills'][0]['qty'])
        price = float(order_paper['fills'][0]['price'])
        cost = amount * price
        new_balance = retrieve_usdt_balance(self.client)
        self.append_to_terminal(
            f"Soft Sold {symbol}: received {cost} USDT at {price} for {amount}. "
            f"Balance: previous {old_balance:.2f} -> current {new_balance:.2f}"
        )
    else:
        self.append_to_terminal("Wrong Style")


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