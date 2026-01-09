"""
data/config_manager.py
Manages user preferences and configuration files.
"""

import os
import logging

from core.globals import PREFERENCES_FILE, USDT, COINS_KEY
from .favorites_manager import load_fav_coins, write_favorite_coins_to_json


def load_user_preferences():
    """
    Load user preferences from text file and update favorite coins configuration.
    Returns the formatted symbols for WebSocket subscription.
    """
    logging.info(f"Loading user preferences from: {PREFERENCES_FILE}")

    if not os.path.exists(PREFERENCES_FILE):
        logging.warning("Preferences file not found!")
        return []

    try:
        with open(PREFERENCES_FILE, "r") as file:
            for line in file:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                if line.startswith("favorite_coins"):
                    fav_coins_name = [
                        coin.strip() for coin in line.split("=")[1].split(",")
                    ]
                    logging.debug(
                        f"Found favorite coins in preferences: {fav_coins_name}"
                    )
                    data = load_fav_coins()

                    # Ensure we have the coins structure
                    if COINS_KEY not in data:
                        data[COINS_KEY] = []

                    # Make sure we have enough coin slots
                    while len(data[COINS_KEY]) < len(fav_coins_name):
                        data[COINS_KEY].append(
                            {
                                "name": "PLACEHOLDER",
                                "symbol": "PLACEHOLDERUSDT",
                                "values": {"current": "0.00", "15_min_ago": "0.00"},
                            }
                        )

                    # Update existing coins with new names/symbols
                    for i, coin_name in enumerate(fav_coins_name):
                        if i < len(data[COINS_KEY]):
                            # Preserve existing price data
                            existing_values = data[COINS_KEY][i].get(
                                "values", {"current": "0.00", "15_min_ago": "0.00"}
                            )

                            # Update name and symbol but keep price data
                            data[COINS_KEY][i]["symbol"] = f"{coin_name.upper()}{USDT}"
                            data[COINS_KEY][i]["name"] = coin_name.upper()
                            data[COINS_KEY][i]["values"] = existing_values

                    # Don't remove extra coins, just leave them as they are
                    # This prevents data loss

                    write_favorite_coins_to_json(data)

        data = load_fav_coins()
        fav_symbols = [coin["symbol"] for coin in data.get(COINS_KEY, [])]

        # Import here to avoid circular import
        from ..symbols.formatting import format_binance_ticker_symbols

        symbols = format_binance_ticker_symbols(fav_symbols)

        logging.info(
            f"Successfully loaded user preferences. Active symbols: {len(symbols)} coins"
        )
        return symbols

    except Exception as e:
        logging.exception(f"Error loading user preferences: {e}")
        return []
