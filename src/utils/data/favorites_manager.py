"""
data/favorites_manager.py
Manages favorite coins data and JSON operations.
"""

import json
import time
import logging

from core.globals import FAV_COINS_FILE, COINS_KEY, DYNAMIC_COIN_KEY
from .file_operations import (
    ensure_config_directory, get_file_lock, safe_file_exists, 
    safe_file_size, create_backup, restore_from_backup, atomic_write_file
)


def create_default_fav_coins_data():
    """Create default favorite coins data structure with sample coins"""
    return {
        COINS_KEY: [
            {
                "name": "BTC",
                "symbol": "BTCUSDT",
                "values": {"current": "0.00", "15_min_ago": "0.00"}
            },
            {
                "name": "ETH",
                "symbol": "ETHUSDT", 
                "values": {"current": "0.00", "15_min_ago": "0.00"}
            },
            {
                "name": "ADA",
                "symbol": "ADAUSDT",
                "values": {"current": "0.00", "15_min_ago": "0.00"}
            },
            {
                "name": "SOL",
                "symbol": "SOLUSDT",
                "values": {"current": "0.00", "15_min_ago": "0.00"}
            },
            {
                "name": "DOGE",
                "symbol": "DOGEUSDT",
                "values": {"current": "0.00", "15_min_ago": "0.00"}
            }
        ],
        DYNAMIC_COIN_KEY: [
            {
                "name": "BTC",
                "symbol": "BTCUSDT",
                "values": {"current": "0.00", "15_min_ago": "0.00"}
            }
        ]
    }


def validate_fav_coins_data(data):
    """Validate and fix favorite coins data structure"""
    if not isinstance(data, dict):
        raise ValueError("Data must be a dictionary")
    
    if COINS_KEY not in data:
        data[COINS_KEY] = []
    if DYNAMIC_COIN_KEY not in data:
        data[DYNAMIC_COIN_KEY] = []
    
    return data


def load_fav_coins():
    """Load favorite coins from JSON file with thread safety"""
    with get_file_lock():
        try:
            ensure_config_directory()
            
            if not safe_file_exists(FAV_COINS_FILE):
                logging.debug(f"Favorite coins file not found, creating: {FAV_COINS_FILE}")
                default_data = create_default_fav_coins_data()
                write_favorite_coins_to_json(default_data)
                return default_data
            
            # Check file size first to avoid reading empty files
            file_size = safe_file_size(FAV_COINS_FILE)
            if file_size == 0:
                logging.warning(f"Favorite coins file is empty (size: 0), restoring with default structure")
                
                # Try to restore from backup first
                if restore_from_backup(FAV_COINS_FILE):
                    return load_fav_coins()  # Recursive call after restore
                
                # If backup restore fails, create default
                default_data = create_default_fav_coins_data()
                write_favorite_coins_to_json(default_data)
                return default_data
            
            # Read file with retry mechanism
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    with open(FAV_COINS_FILE, 'r', encoding='utf-8') as file:
                        content = file.read().strip()
                        
                        if not content:
                            if attempt < max_retries - 1:
                                time.sleep(0.1)  # Wait 100ms before retry
                                continue
                            
                            logging.warning(f"Favorite coins file is empty after {max_retries} attempts, restoring with default structure")
                            
                            # Try to restore from backup first
                            if restore_from_backup(FAV_COINS_FILE):
                                return load_fav_coins()  # Recursive call after restore
                            
                            # If backup restore fails, create default
                            default_data = create_default_fav_coins_data()
                            write_favorite_coins_to_json(default_data)
                            return default_data
                        
                        data = json.loads(content)
                        
                        # Validate and fix structure if needed
                        data = validate_fav_coins_data(data)
                        return data
                        
                except json.JSONDecodeError as e:
                    if attempt < max_retries - 1:
                        time.sleep(0.1)  # Wait 100ms before retry
                        continue
                    
                    logging.error(f"Invalid JSON in favorite coins file after {max_retries} attempts: {e}")
                    
                    # Try to restore from backup before recreating
                    if restore_from_backup(FAV_COINS_FILE):
                        return load_fav_coins()  # Recursive call after restore
                    
                    logging.debug("Creating new favorite coins file with default values")
                    default_data = create_default_fav_coins_data()
                    write_favorite_coins_to_json(default_data)
                    return default_data
                    
        except Exception as e:
            logging.exception(f"Error loading favorite coins: {e}")
            return create_default_fav_coins_data()


def write_favorite_coins_to_json(data):
    """Save favorite coins data to JSON file with backup and validation and thread safety"""
    with get_file_lock():
        try:
            ensure_config_directory()
            
            # Validate data structure
            data = validate_fav_coins_data(data)
            
            # Create backup if file exists and has content
            create_backup(FAV_COINS_FILE)
            
            # Validate that we're not writing empty data when existing data exists
            if safe_file_exists(FAV_COINS_FILE):
                try:
                    file_size = safe_file_size(FAV_COINS_FILE)
                    if file_size > 0:
                        with open(FAV_COINS_FILE, 'r', encoding='utf-8') as existing_file:
                            existing_content = existing_file.read().strip()
                            if existing_content:
                                existing_data = json.loads(existing_content)
                                # If we're trying to write empty data but existing data has content, merge
                                if (not data.get(COINS_KEY) and existing_data.get(COINS_KEY)) or \
                                   (not data.get(DYNAMIC_COIN_KEY) and existing_data.get(DYNAMIC_COIN_KEY)):
                                    logging.warning("Preventing overwrite of existing data with empty data")
                                    # Merge - keep existing data structure but update symbols/names
                                    if not data.get(COINS_KEY) and existing_data.get(COINS_KEY):
                                        data[COINS_KEY] = existing_data[COINS_KEY]
                                    if not data.get(DYNAMIC_COIN_KEY) and existing_data.get(DYNAMIC_COIN_KEY):
                                        data[DYNAMIC_COIN_KEY] = existing_data[DYNAMIC_COIN_KEY]
                except (json.JSONDecodeError, Exception) as e:
                    logging.warning(f"Could not read existing file for comparison: {e}")
            
            # Write the new data using atomic write
            json_content = json.dumps(data, indent=4, ensure_ascii=False)
            if atomic_write_file(FAV_COINS_FILE, json_content):
                logging.debug(f"Successfully wrote favorite coins data to {FAV_COINS_FILE}")
            else:
                # Try to restore from backup if write failed
                if not restore_from_backup(FAV_COINS_FILE):
                    logging.error(f"Failed to write favorite coins and backup restore also failed")
            
        except Exception as e:
            logging.exception(f"Error writing favorite coins: {e}")
            # Try to restore from backup if write failed
            restore_from_backup(FAV_COINS_FILE)