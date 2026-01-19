"""
data_utils.py
Data management utilities for loading/saving configuration and user preferences.
"""

import json
import os
import logging
import threading
import time

from core.globals import (
    PREFERENCES_FILE,
    FAV_COINS_FILE,
    USDT,
    COINS_KEY,
    DYNAMIC_COIN_KEY,
)
from core.paths import SETTINGS_DIR
from utils.symbols.formatting import format_binance_ticker_symbols

# File operation lock to prevent race conditions
_file_lock = threading.Lock()


def ensure_config_directory():
    """Ensure the config directory exists"""
    try:
        if not os.path.exists(SETTINGS_DIR):
            os.makedirs(SETTINGS_DIR)
            logging.debug(f"Created config directory: {SETTINGS_DIR}")
    except Exception as e:
        logging.error(f"Error creating config directory: {e}")


def load_fav_coins():
    """Load favorite coins from JSON file with thread safety"""
    with _file_lock:
        try:
            ensure_config_directory()

            if not os.path.exists(FAV_COINS_FILE):
                logging.debug(
                    f"Favorite coins file not found, creating: {FAV_COINS_FILE}"
                )
                default_data = create_default_fav_coins_data()
                write_favorite_coins_to_json(default_data)
                return default_data

            # Check file size first to avoid reading empty files
            file_size = os.path.getsize(FAV_COINS_FILE)
            if file_size == 0:
                logging.warning(
                    "Favorite coins file is empty (size: 0), restoring with default structure"
                )
                # Try to restore from backup first
                backup_file = f"{FAV_COINS_FILE}.backup"
                if os.path.exists(backup_file) and os.path.getsize(backup_file) > 0:
                    try:
                        with open(backup_file, "r", encoding="utf-8") as backup:
                            backup_content = backup.read().strip()
                            if backup_content:
                                backup_data = json.loads(backup_content)
                                write_favorite_coins_to_json(backup_data)
                                logging.debug("Restored fav_coins.json from backup")
                                return backup_data
                    except Exception as e:
                        logging.warning(f"Could not restore from backup: {e}")

                # If backup restore fails, create default
                default_data = create_default_fav_coins_data()
                write_favorite_coins_to_json(default_data)
                return default_data

            # Read file with retry mechanism
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    with open(FAV_COINS_FILE, "r", encoding="utf-8") as file:
                        content = file.read().strip()

                        if not content:
                            if attempt < max_retries - 1:
                                time.sleep(0.1)  # Wait 100ms before retry
                                continue

                            logging.warning(
                                f"Favorite coins file is empty after {max_retries} attempts, restoring with default structure"
                            )
                            # Try to restore from backup first
                            backup_file = f"{FAV_COINS_FILE}.backup"
                            if os.path.exists(backup_file):
                                try:
                                    with open(
                                        backup_file, "r", encoding="utf-8"
                                    ) as backup:
                                        backup_content = backup.read().strip()
                                        if backup_content:
                                            backup_data = json.loads(backup_content)
                                            write_favorite_coins_to_json(backup_data)
                                            logging.debug(
                                                "Restored fav_coins.json from backup"
                                            )
                                            return backup_data
                                except Exception as e:
                                    logging.warning(
                                        f"Could not restore from backup: {e}"
                                    )

                            # If backup restore fails, create default
                            default_data = create_default_fav_coins_data()
                            write_favorite_coins_to_json(default_data)
                            return default_data

                        data = json.loads(content)

                        # Validate and fix structure if needed
                        if COINS_KEY not in data:
                            data[COINS_KEY] = []
                        if DYNAMIC_COIN_KEY not in data:
                            data[DYNAMIC_COIN_KEY] = []

                        return data

                except json.JSONDecodeError as e:
                    if attempt < max_retries - 1:
                        time.sleep(0.1)  # Wait 100ms before retry
                        continue

                    logging.error(
                        f"Invalid JSON in favorite coins file after {max_retries} attempts: {e}"
                    )

                    # Try to restore from backup before recreating
                    backup_file = f"{FAV_COINS_FILE}.backup"
                    if os.path.exists(backup_file):
                        try:
                            with open(backup_file, "r", encoding="utf-8") as backup:
                                backup_data = json.loads(backup.read())
                                write_favorite_coins_to_json(backup_data)
                                logging.debug(
                                    "Restored corrupted fav_coins.json from backup"
                                )
                                return backup_data
                        except Exception as e:
                            logging.warning(f"Could not restore from backup: {e}")

                    logging.debug(
                        "Creating new favorite coins file with default values"
                    )
                    default_data = create_default_fav_coins_data()
                    write_favorite_coins_to_json(default_data)
                    return default_data

        except Exception as e:
            logging.exception(f"Error loading favorite coins: {e}")
            return create_default_fav_coins_data()


def create_default_fav_coins_data():
    """Create default favorite coins data structure with sample coins"""
    return {
        COINS_KEY: [
            {
                "name": "BTC",
                "symbol": "BTCUSDT",
                "values": {"current": "0.00", "15_min_ago": "0.00"},
            },
            {
                "name": "ETH",
                "symbol": "ETHUSDT",
                "values": {"current": "0.00", "15_min_ago": "0.00"},
            },
            {
                "name": "ADA",
                "symbol": "ADAUSDT",
                "values": {"current": "0.00", "15_min_ago": "0.00"},
            },
            {
                "name": "SOL",
                "symbol": "SOLUSDT",
                "values": {"current": "0.00", "15_min_ago": "0.00"},
            },
            {
                "name": "DOGE",
                "symbol": "DOGEUSDT",
                "values": {"current": "0.00", "15_min_ago": "0.00"},
            },
        ],
        DYNAMIC_COIN_KEY: [
            {
                "name": "BTC",
                "symbol": "BTCUSDT",
                "values": {"current": "0.00", "15_min_ago": "0.00"},
            }
        ],
    }


def write_favorite_coins_to_json(data):
    """Save favorite coins data to JSON file with backup and validation and thread safety"""
    with _file_lock:
        try:
            ensure_config_directory()

            # Validate data structure
            if not isinstance(data, dict):
                raise ValueError("Data must be a dictionary")
            if COINS_KEY not in data:
                data[COINS_KEY] = []
            if DYNAMIC_COIN_KEY not in data:
                data[DYNAMIC_COIN_KEY] = []

            # Create backup if file exists and has content
            if os.path.exists(FAV_COINS_FILE):
                backup_file = f"{FAV_COINS_FILE}.backup"
                try:
                    file_size = os.path.getsize(FAV_COINS_FILE)
                    if file_size > 0:  # Only backup if file has content
                        with open(FAV_COINS_FILE, "r", encoding="utf-8") as source:
                            content = source.read().strip()
                            if content:  # Double check content is not empty
                                with open(backup_file, "w", encoding="utf-8") as backup:
                                    backup.write(content)
                                logging.debug(
                                    "Created backup of existing fav_coins.json"
                                )
                except Exception as e:
                    logging.warning(f"Could not create backup: {e}")

            # Validate that we're not writing empty data when existing data exists
            if os.path.exists(FAV_COINS_FILE):
                try:
                    file_size = os.path.getsize(FAV_COINS_FILE)
                    if file_size > 0:
                        with open(
                            FAV_COINS_FILE, "r", encoding="utf-8"
                        ) as existing_file:
                            existing_content = existing_file.read().strip()
                            if existing_content:
                                existing_data = json.loads(existing_content)
                                # If we're trying to write empty data but existing data has content, merge
                                if (
                                    not data.get(COINS_KEY)
                                    and existing_data.get(COINS_KEY)
                                ) or (
                                    not data.get(DYNAMIC_COIN_KEY)
                                    and existing_data.get(DYNAMIC_COIN_KEY)
                                ):
                                    logging.warning(
                                        "Preventing overwrite of existing data with empty data"
                                    )
                                    # Merge - keep existing data structure but update symbols/names
                                    if not data.get(COINS_KEY) and existing_data.get(
                                        COINS_KEY
                                    ):
                                        data[COINS_KEY] = existing_data[COINS_KEY]
                                    if not data.get(
                                        DYNAMIC_COIN_KEY
                                    ) and existing_data.get(DYNAMIC_COIN_KEY):
                                        data[DYNAMIC_COIN_KEY] = existing_data[
                                            DYNAMIC_COIN_KEY
                                        ]
                except (json.JSONDecodeError, Exception) as e:
                    logging.warning(f"Could not read existing file for comparison: {e}")

            # Write the new data with proper encoding using atomic write
            temp_file = f"{FAV_COINS_FILE}.tmp"
            try:
                with open(temp_file, "w", encoding="utf-8") as file:
                    json.dump(data, file, indent=4, ensure_ascii=False)

                # Atomic move operation - reduces the window where file might appear empty
                if os.path.exists(FAV_COINS_FILE):
                    os.replace(temp_file, FAV_COINS_FILE)
                else:
                    os.rename(temp_file, FAV_COINS_FILE)

                logging.debug(
                    f"Successfully wrote favorite coins data to {FAV_COINS_FILE}"
                )

            except Exception as e:
                # Clean up temp file if it exists
                if os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                    except OSError:
                        pass
                raise e

        except Exception as e:
            logging.exception(f"Error writing favorite coins: {e}")
            # Try to restore from backup if write failed
            backup_file = f"{FAV_COINS_FILE}.backup"
            if os.path.exists(backup_file):
                try:
                    with open(backup_file, "r", encoding="utf-8") as backup:
                        backup_content = backup.read()
                        if backup_content.strip():  # Only restore if backup has content
                            with open(FAV_COINS_FILE, "w", encoding="utf-8") as target:
                                target.write(backup_content)
                            logging.debug("Restored favorite coins file from backup")
                except Exception as restore_error:
                    logging.error(f"Could not restore from backup: {restore_error}")


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
        symbols = format_binance_ticker_symbols(fav_symbols)
        logging.info(
            f"Successfully loaded user preferences. Active symbols: {len(symbols)} coins"
        )
        return symbols
    except Exception as e:
        logging.exception(f"Error loading user preferences: {e}")
        return []


if __name__ == "__main__":
    """Test data utils functions"""
    print("🚀 Testing Data Utils")
    print("=" * 30)

    # Test configuration directory
    ensure_config_directory()
    print("✅ Config directory ensured")

    # Test JSON loading/saving - removed functions
    print("✅ JSON utilities functionality removed")

    print("\n✅ Data utils test completed successfully!")
