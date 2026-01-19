import logging
import requests
import pandas as pd
import matplotlib.pyplot as plt

from PySide6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QWidget
from PySide6.QtCore import Qt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar

from core.paths import PREFERENCES_FILE

"""
This module retrieves and formats candlestick data from the Binance API.
It contains functions to fetch raw candle data, convert that data into a structured
pandas DataFrame with appropriate column names and data types, and provide the
final chart-ready data for further analysis.
Functions:
    fetch_candles(symbol="BTCUSDT", interval="1m", limit=50):
        Makes an HTTP GET request to Binance API to obtain the latest candlestick
        data for the given trading symbol and interval. Returns the raw JSON data from the API.
    format_candle_data(candles):
        Takes the raw candlestick JSON data and converts it into a pandas DataFrame.
        It assigns predefined column names, converts the timestamp to datetime,
        converts relevant columns to numerical data types, and sets the timestamp as the index.
    get_chart_data(symbol="BTCUSDT"):
        Orchestrates the process by first fetching the raw candle data and then formatting it.
        It raises a ValueError if the API response is not in the expected format.
"""


class ChartDialog(QDialog):
    """
    Custom Dialog to display Matplotlib plots within the Qt application.
    Independent window that doesn't block the main event loop in a crashing way.
    """
    def __init__(self, figure, parent=None, title="Coin Chart"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint | Qt.WindowMaximizeButtonHint)
        self.resize(500, 350)
        
        # Apply dark theme to dialog
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
                color: #e0e0e0;
            }
            QPushButton {
                background-color: #333333;
                color: white;
                border: 1px solid #555555;
                padding: 6px 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #444444;
            }
            QPushButton:pressed {
                background-color: #222222;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create canvas
        self.canvas = FigureCanvas(figure)
        self.canvas.setStyleSheet("background-color: #1e1e1e;")
        
        # Add navigation toolbar
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.toolbar.setStyleSheet("background-color: #2b2b2b; color: #e0e0e0; border-bottom: 1px solid #3d3d3d;")
        
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)

        # Close button area
        button_container = QWidget()
        button_container.setStyleSheet("background-color: #2b2b2b; border-top: 1px solid #3d3d3d;")
        button_layout = QVBoxLayout(button_container)
        button_layout.setContentsMargins(10, 10, 10, 10)
        
        close_btn = QPushButton("Close")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(self.accept)
        close_btn.setFixedWidth(100)
        
        button_layout.addWidget(close_btn, alignment=Qt.AlignRight)
        layout.addWidget(button_container)

    def closeEvent(self, event):
        """Cleanup when closed"""
        plt.close(self.canvas.figure)
        super().closeEvent(event)



def fetch_candles(symbol="BTCUSDT", interval="1m", limit=50):
    """
    Retrieves candlestick data for the specified symbol and interval from Binance.
    """
    import logging

    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            logging.error(
                f"API error {response.status_code} while fetching candles for {symbol}."
            )
            return []
    except requests.exceptions.Timeout:
        logging.error(f"Timeout error while fetching candles for {symbol}.")
        return []
    except requests.exceptions.RequestException as e:
        logging.error(f"Request error while fetching candles for {symbol}: {e}")
        return []


def format_candle_data(candles):
    """
    Converts raw candlestick data into a DataFrame with appropriate column names and data types.
    """
    columns = [
        "open_time",
        "Open",
        "High",
        "Low",
        "Close",
        "Volume",
        "close_time",
        "quote_asset_volume",
        "number_of_trades",
        "taker_buy_base_asset_volume",
        "taker_buy_quote_asset_volume",
        "ignore",
    ]
    # Ensure the number of columns in the DataFrame matches the number of columns in the API response.
    df = pd.DataFrame(candles, columns=columns)
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
    for col in ["Open", "High", "Low", "Close", "Volume"]:
        df[col] = pd.to_numeric(df[col])
    df.set_index("open_time", inplace=True)
    return df


def validate_symbol(symbol):
    """
    Validates if a symbol exists on Binance by checking exchange info.
    Returns True if valid, False otherwise.
    """
    import logging

    try:
        url = "https://api.binance.com/api/v3/exchangeInfo"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            valid_symbols = [s["symbol"] for s in data["symbols"]]
            return symbol.upper() in valid_symbols
        else:
            logging.error(f"Failed to fetch exchange info: {response.status_code}")
            return False
    except Exception as e:
        logging.error(f"Error validating symbol {symbol}: {e}")
        return False


def get_chart_data(symbol="BTCUSDT"):
    # chart_interval tercihini Preferences.txt dosyasından oku
    interval = "1"
    try:
        with open(PREFERENCES_FILE, "r") as f:
            for line in f:
                if line.strip().startswith("chart_interval"):
                    interval = line.split("=", 1)[1].strip().lstrip("%")
                    break
    except Exception:
        interval = "1"

    # Sembol validasyonu ekle
    if not validate_symbol(symbol):
        raise ValueError(
            f"Invalid symbol: {symbol} - This symbol is not available on Binance"
        )

    # Make the API call only once and store the result in a variable.
    candles = fetch_candles(symbol, interval=f"{interval}m")
    if not candles or not isinstance(candles, list):
        raise ValueError("Unexpected data format received from the API.")
    df = format_candle_data(candles)
    return df


