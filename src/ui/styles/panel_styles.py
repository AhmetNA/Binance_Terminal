"""
Panel styles for the Binance Terminal UI.
Contains all the panel and container styling definitions.
"""

# Main panel styles
FAVORITE_COINS_PANEL_STYLE = """
    QGroupBox {
        background-color: #696969;
        border: 1px solid gray;
        border-radius: 15px;
    }
"""

DYNAMIC_COIN_PANEL_STYLE = """
    QGroupBox {
        background-color: #696969;
        border: 1px solid gray;
        border-radius: 15px;
    }
"""

WALLET_FRAME_STYLE = """
    QFrame {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
            stop:0 #1A1A2E, stop:1 #16213E);
        color: #E8E8E8;
        border-radius: 15px;
        border: 2px solid #0F3460;
    }
"""

COIN_ENTRY_FRAME_STYLE = """
    QFrame {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
            stop:0 #1A1A2E, stop:1 #16213E);
        color: #E8E8E8;
        border-radius: 12px;
        border: 1px solid #0F3460;
    }
"""

# Label styles
WALLET_LABEL_STYLE = """
    QLabel {
        font-size: 13px; 
        font-weight: bold; 
        color: #F0F3FF;
        background: transparent;
        border: none;
        padding: 5px;
        margin: 2px;
    }
"""

ENTRY_LABEL_STYLE = """
    QLabel {
        font-size: 11px; 
        font-weight: bold;
        color: #F0F3FF;
        background: transparent;
        border: none;
        margin: 1px;
    }
"""

SETTINGS_LABEL_STYLE = """
    QLabel {
        font-size: 12px;
        font-weight: bold;
        color: #E8E8E8;
        margin: 5px 0;
    }
"""

# Input field styles
COIN_INPUT_STYLE = """
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
"""

SETTINGS_INPUT_STYLE = """
    QLineEdit {
        font-size: 11px;
        height: 25px;
        background-color: #16213E;
        color: #E8E8E8;
        border: 1px solid #533483;
        border-radius: 4px;
        padding: 4px;
        margin: 2px 0;
    }
    QLineEdit:focus {
        border: 1px solid #E94560;
        background-color: #1A1A2E;
    }
"""

# Terminal style
TERMINAL_STYLE = """
    QPlainTextEdit {
        background-color: black;
        color: white;
        border-radius: 8px;
        padding: 5px;
        font-family: Consolas, monospace;
        font-size: 11px;
        font-weight: bold;
    }
"""

# Dialog styles
SETTINGS_DIALOG_STYLE = """
    QDialog {
        background-color: #1A1A2E;
        color: #E8E8E8;
    }
"""


# Common sizes and dimensions
class PanelSizes:
    """Common panel size constants."""

    FAVORITE_COINS_MIN_WIDTH = 430
    FAVORITE_COINS_MIN_HEIGHT = 220

    DYNAMIC_COIN_MIN_WIDTH = 100
    DYNAMIC_COIN_MIN_HEIGHT = 20

    WALLET_FRAME_WIDTH = 200
    WALLET_FRAME_HEIGHT = 95

    COIN_ENTRY_FRAME_WIDTH = 200
    COIN_ENTRY_FRAME_HEIGHT = 120

    TERMINAL_HEIGHT = 180

    SETTINGS_BUTTON_WIDTH = 75
    SETTINGS_BUTTON_HEIGHT = 28


class LayoutSpacing:
    """Common layout spacing constants."""

    MAIN_MARGIN = 5
    MAIN_SPACING = 4

    FAV_COIN_MARGIN = 3
    FAV_COIN_SPACING = 3

    DYN_COIN_MARGIN = 5
    DYN_COIN_SPACING = 8
    DYN_COIN_EXTRA_SPACING = 20

    RIGHT_PANEL_SPACING = 5

    WALLET_MARGIN = 8
    WALLET_SPACING = 2

    ENTRY_MARGIN = 8
    ENTRY_SPACING = 4
    ENTRY_EXTRA_SPACING = 8
