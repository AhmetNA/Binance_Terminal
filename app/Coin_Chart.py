import requests

"""
This module retrieves and formats 1-minute candlestick data from the Binance API.
It contains functions to fetch raw candle data, convert that data into a structured
pandas DataFrame with appropriate column names and data types, and provide the
final chart-ready data for further analysis.
Functions:
    fetch_1m_candles(symbol="BTCUSDT", limit=50):
        Makes an HTTP GET request to Binance API to obtain the latest 1-minute candlestick
        data for the given trading symbol. Returns the raw JSON data from the API.
    format_candle_data(candles):
        Takes the raw candlestick JSON data and converts it into a pandas DataFrame.
        It assigns predefined column names, converts the timestamp to datetime,
        converts relevant columns to numerical data types, and sets the timestamp as the index.
    get_chart_data(symbol="BTCUSDT"):
        Orchestrates the process by first fetching the raw candle data and then formatting it.
        It raises a ValueError if the API response is not in the expected format.
"""
import pandas as pd





def fetch_1m_candles(symbol="BTCUSDT", limit=50):
    """
    Binance'den belirtilen sembol için 1 dakikalık 50 mum verisi getirir.
    """
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1m&limit={limit}"
    response = requests.get(url)
    # Gelen veriyi JSON olarak döndürür
    return response.json()

def format_candle_data(candles):
    """
    Ham mum verilerini uygun sütun isimleri ve veri tiplerine sahip DataFrame'e dönüştürür.
    """
    columns = [
        "open_time", "Open", "High", "Low", "Close", "Volume",
        "close_time", "quote_asset_volume", "number_of_trades",
        "taker_buy_base_asset_volume", "taker_buy_quote_asset_volume", "ignore"
    ]
    # DataFrame oluşturulurken beklenen sütun sayısı ile API'den gelen verinin sütun sayısının eşleştiğinden emin olun.
    df = pd.DataFrame(candles, columns=columns)
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
    for col in ["Open", "High", "Low", "Close", "Volume"]:
        df[col] = pd.to_numeric(df[col])
    df.set_index("open_time", inplace=True)
    return df

def get_chart_data(symbol="BTCUSDT"):
    # API çağrısını yalnızca bir kez yapıp sonucu bir değişkende saklıyoruz.
    candles = fetch_1m_candles(symbol)
    if not candles or not isinstance(candles, list):
        raise ValueError("API'den beklenmeyen formatta veri alındı.")
    df = format_candle_data(candles)
    return df
