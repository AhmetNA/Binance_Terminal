"""
data_utils.py
Data management utilities for loading/saving configuration and user preferences.
"""

import json
import os
import logging
import sys

# Add src to path for core imports (optimized)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import PREFERENCES_FILE, FAV_COINS_FILE, USDT, TICKER_SUFFIX, COINS_KEY, DYNAMIC_COIN_KEY
from core.paths import SETTINGS_DIR
from utils.symbol_utils import format_binance_ticker_symbols


def ensure_config_directory():
    """Ensure the config directory exists"""
    try:
        if not os.path.exists(SETTINGS_DIR):
            os.makedirs(SETTINGS_DIR)
            logging.info(f"Created config directory: {SETTINGS_DIR}")
    except Exception as e:
        logging.error(f"Error creating config directory: {e}")


def load_fav_coins():
    """Load favorite coins from JSON file"""
    try:
        ensure_config_directory()
        
        if not os.path.exists(FAV_COINS_FILE):
            logging.info(f"Favorite coins file not found, creating: {FAV_COINS_FILE}")
            default_data = {COINS_KEY: [], DYNAMIC_COIN_KEY: []}
            write_favorite_coins_to_json(default_data)
            return default_data
        
        with open(FAV_COINS_FILE, 'r', encoding='utf-8') as file:
            content = file.read().strip()
            
            if not content:
                logging.warning(f"Favorite coins file is empty, creating default: {FAV_COINS_FILE}")
                default_data = {COINS_KEY: [], DYNAMIC_COIN_KEY: []}
                write_favorite_coins_to_json(default_data)
                return default_data
            
            return json.loads(content)
            
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON in favorite coins file: {e}")
        logging.info("Recreating favorite coins file with default values")
        default_data = {COINS_KEY: [], DYNAMIC_COIN_KEY: []}
        write_favorite_coins_to_json(default_data)
        return default_data
    except Exception as e:
        logging.exception(f"Error loading favorite coins: {e}")
        return {COINS_KEY: [], DYNAMIC_COIN_KEY: []}


def write_favorite_coins_to_json(data):
    """Save favorite coins data to JSON file with backup and validation"""
    try:
        ensure_config_directory()
        
        # Validate data structure
        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary")
        if COINS_KEY not in data:
            data[COINS_KEY] = []
        if DYNAMIC_COIN_KEY not in data:
            data[DYNAMIC_COIN_KEY] = []
        
        # Create backup if file exists
        if os.path.exists(FAV_COINS_FILE):
            backup_file = f"{FAV_COINS_FILE}.backup"
            try:
                with open(FAV_COINS_FILE, 'r') as source:
                    with open(backup_file, 'w') as backup:
                        backup.write(source.read())
            except Exception as e:
                logging.warning(f"Could not create backup: {e}")
        
        # Write the new data
        with open(FAV_COINS_FILE, 'w') as file:
            json.dump(data, file, indent=4)
        
        logging.debug(f"Successfully wrote favorite coins data to {FAV_COINS_FILE}")
        
    except Exception as e:
        logging.exception(f"Error writing favorite coins: {e}")
        # Try to restore from backup if write failed
        backup_file = f"{FAV_COINS_FILE}.backup"
        if os.path.exists(backup_file):
            try:
                with open(backup_file, 'r') as backup:
                    with open(FAV_COINS_FILE, 'w') as target:
                        target.write(backup.read())
                logging.info("Restored favorite coins file from backup")
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
        with open(PREFERENCES_FILE, 'r') as file:
            for line in file:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                if line.startswith("favorite_coins"):
                    fav_coins_name = [coin.strip() for coin in line.split("=")[1].split(",")]
                    logging.info(f"Found favorite coins in preferences: {fav_coins_name}")
                    data = load_fav_coins()

                    for i, coin_name in enumerate(fav_coins_name):
                        if i < len(data.get(COINS_KEY, [])):
                            data[COINS_KEY][i]['symbol'] = f"{coin_name.upper()}{USDT}"
                            data[COINS_KEY][i]['name'] = coin_name.upper()

                    write_favorite_coins_to_json(data)

        data = load_fav_coins()
        fav_symbols = [coin['symbol'] for coin in data.get(COINS_KEY, [])]
        symbols = format_binance_ticker_symbols(fav_symbols)
        logging.info(f"Successfully loaded user preferences. Active symbols: {len(symbols)} coins")
        return symbols
    except Exception as e:
        logging.exception(f"Error loading user preferences: {e}")
        return []


def validate_json_structure(data, expected_keys):
    """Validate JSON data structure"""
    if not isinstance(data, dict):
        return False
    
    for key in expected_keys:
        if key not in data:
            return False
    
    return True


def safe_json_load(file_path, default_value=None):
    """Safely load JSON file with error handling"""
    try:
        if not os.path.exists(file_path):
            return default_value
        
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read().strip()
            if not content:
                return default_value
            
            return json.loads(content)
            
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON in file {file_path}: {e}")
        return default_value
    except Exception as e:
        logging.error(f"Error loading JSON file {file_path}: {e}")
        return default_value


def safe_json_save(file_path, data, create_backup=True):
    """Safely save JSON data with backup"""
    try:
        # Ensure directory exists
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
        
        # Create backup if requested and file exists
        if create_backup and os.path.exists(file_path):
            backup_file = f"{file_path}.backup"
            try:
                with open(file_path, 'r') as source:
                    with open(backup_file, 'w') as backup:
                        backup.write(source.read())
            except Exception as e:
                logging.warning(f"Could not create backup for {file_path}: {e}")
        
        # Write the new data
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=4, ensure_ascii=False)
        
        logging.debug(f"Successfully saved data to {file_path}")
        return True
        
    except Exception as e:
        logging.error(f"Error saving JSON to {file_path}: {e}")
        
        # Try to restore from backup if write failed
        if create_backup:
            backup_file = f"{file_path}.backup"
            if os.path.exists(backup_file):
                try:
                    with open(backup_file, 'r') as backup:
                        with open(file_path, 'w') as target:
                            target.write(backup.read())
                    logging.info(f"Restored {file_path} from backup")
                except Exception as restore_error:
                    logging.error(f"Could not restore {file_path} from backup: {restore_error}")
        
        return False


if __name__ == "__main__":
    """Test data utils functions"""
    print("🚀 Testing Data Utils")
    print("=" * 30)
    
    # Test configuration directory
    ensure_config_directory()
    print(f"✅ Config directory ensured")
    
    # Test JSON loading/saving
    test_data = {"test": "data", "coins": ["BTC", "ETH"]}
    test_file = os.path.join(SETTINGS_DIR, "test.json")
    
    # Save test data
    success = safe_json_save(test_file, test_data)
    print(f"✅ JSON save successful: {success}")
    
    # Load test data
    loaded_data = safe_json_load(test_file, {})
    print(f"✅ JSON load successful: {loaded_data == test_data}")
    
    # Clean up test file
    try:
        os.remove(test_file)
        if os.path.exists(f"{test_file}.backup"):
            os.remove(f"{test_file}.backup")
    except:
        pass
    
    print("\n✅ Data utils test completed successfully!")
