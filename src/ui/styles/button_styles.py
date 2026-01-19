"""
Button styles for the Binance Terminal UI.
Contains all the button styling definitions used throughout the application.
"""

# Trading button styles
HARD_BUY_STYLE = """
    QPushButton { 
        background-color: darkgreen; 
        color: white; 
        border-radius: 6px; 
        min-height: 25px; 
        font-size: 12px; 
        font-weight: bold; 
    }
    QPushButton:hover { 
        background-color: #3182CE; 
    }
"""

SOFT_BUY_STYLE = """
    QPushButton { 
        background-color: #089000; 
        color: white; 
        border-radius: 6px; 
        min-height: 25px; 
        font-size: 12px; 
        font-weight: bold; 
    }
    QPushButton:hover { 
        background-color: blue; 
    }
"""

SOFT_SELL_STYLE = """
    QPushButton { 
        background-color: #800000; 
        color: white; 
        border-radius: 6px; 
        min-height: 25px; 
        font-size: 12px; 
        font-weight: bold; 
    }
    QPushButton:hover { 
        background-color: blue; 
    }
"""

HARD_SELL_STYLE = """
    QPushButton { 
        background-color: #400000; 
        color: white; 
        border-radius: 6px; 
        min-height: 25px; 
        font-size: 12px; 
        font-weight: bold; 
    }
    QPushButton:hover { 
        background-color: blue; 
    }
"""

COIN_LABEL_STYLE = """
    QPushButton { 
        background-color: gray; 
        color: white; 
        border-radius: 6px; 
        min-height: 80px; 
        font-size: 11px; 
        font-weight: bold; 
    }
    QPushButton:hover { 
        background-color: blue; 
    }
"""

# Dynamic coin panel button styles (larger)
DYN_HARD_BUY_STYLE = """
    QPushButton { 
        background-color: darkgreen; 
        color: white; 
        border-radius: 8px; 
        min-height: 25px; 
        font-size: 12px; 
        font-weight: bold; 
    }
    QPushButton:hover { 
        background-color: blue; 
    }
"""

DYN_SOFT_BUY_STYLE = """
    QPushButton { 
        background-color: #089000; 
        color: white; 
        border-radius: 8px; 
        min-height: 25px; 
        font-size: 12px; 
        font-weight: bold; 
    }
    QPushButton:hover { 
        background-color: blue; 
    }
"""

DYN_SOFT_SELL_STYLE = """
    QPushButton { 
        background-color: #800000; 
        color: white; 
        border-radius: 8px; 
        min-height: 25px; 
        font-size: 12px; 
        font-weight: bold; 
    }
    QPushButton:hover { 
        background-color: blue; 
    }
"""

DYN_HARD_SELL_STYLE = """
    QPushButton { 
        background-color: #400000; 
        color: white; 
        border-radius: 8px; 
        min-height: 25px; 
        font-size: 12px; 
        font-weight: bold; 
    }
    QPushButton:hover { 
        background-color: blue; 
    }
"""

DYN_COIN_LABEL_STYLE = """
    QPushButton { 
        background-color: gray; 
        color: white; 
        border-radius: 8px; 
        min-height: 80px; 
        font-size: 11px; 
        font-weight: bold; 
    }
    QPushButton:hover { 
        background-color: blue; 
    }
"""

# Settings and utility button styles
SETTINGS_BUTTON_STYLE = """
    QPushButton {
        background-color: #2C5282;
        color: #E8E8E8;
        border: 1px solid #4A5568;
        border-radius: 8px;
        font-size: 11px; 
        font-weight: bold;
        padding: 3px;
    }
    QPushButton:hover {
        background-color: #2B6CB0;
        border: 1px solid #CBD5E0;
    }
    QPushButton:pressed {
        background-color: #2A4365;
        border: 1px solid #4A5568;
    }
"""

SUBMIT_BUTTON_STYLE = """
    QPushButton { 
        background-color: #2C5282;
        color: #E8E8E8; 
        border: 1px solid #4A5568;
        border-radius: 6px; 
        font-size: 11px; 
        height: 26px; 
        min-height: 26px;
        font-weight: bold;
        padding: 3px;
    }
    QPushButton:hover { 
        background-color: #2B6CB0;
        border: 1px solid #CBD5E0;
    }
    QPushButton:pressed {
        background-color: #2A4365;
    }
"""

SAVE_BUTTON_STYLE = """
    QPushButton {
        background-color: #2E8B57;
        color: white;
        border: 1px solid #1E6B47;
        border-radius: 5px;
        font-size: 12px;
        font-weight: bold;
        padding: 8px 16px;
        min-height: 30px;
    }
    QPushButton:hover {
        background-color: #3CB371;
        border: 1px solid #2E8B57;
    }
    QPushButton:pressed {
        background-color: #1E6B47;
    }
"""
