import logging
import os
import sys

# Add path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_dir)
sys.path.append(src_dir)

# Import centralized paths
from core.paths import PREFERENCES_FILE

# Magic strings
FAV_COINS_KEY = "favorite_coins"
USDT_SUFFIX = "USDT"
PERCENT_SIGN = "%"

# Logging configuration (if not already set in main app)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('binance_terminal.log', encoding='utf-8')
    ]
)

def set_preference(key: str, new_value: str) -> str:
    """
    Updates or adds a preference in the Preferences.txt file.
    Returns a message about the result.
    """
    logging.info(f"Attempting to set preference: {key} = {new_value}")
    
    try:
        with open(PREFERENCES_FILE, 'r') as f:
            lines = f.readlines()
    except Exception as e:
        logging.exception(f"Error reading preferences file: {e}")
        return f"Error reading preferences file: {e}"

    updated = False
    new_lines = []
    for line in lines:
        if line.strip().startswith(f"{key}"):
            parts = line.split("=", 1)
            current_value = parts[1].strip() if len(parts) > 1 else ""
            if current_value == new_value:
                logging.info(f"Preference {key} is already set to {new_value}, no change needed")
                return f"{key} preference is already set to {new_value}"
            logging.info(f"Updating preference {key} from '{current_value}' to '{new_value}'")
            new_lines.append(f"{key} = %{new_value}\n")
            updated = True
        else:
            new_lines.append(line)

    if not updated:
        logging.info(f"Adding new preference: {key} = {new_value}")
        new_lines.append(f"{key} = %{new_value}\n")
        updated = True

    try:
        with open(PREFERENCES_FILE, 'w') as f:
            f.writelines(new_lines)
        logging.info(f"Successfully saved preference {key} to file: {PREFERENCES_FILE}")
        
        # 🔄 CACHE RELOAD: Risk preferences değiştiyse cache'i temizle
        if key in ['soft_risk', 'hard_risk']:
            try:
                from config.preferences_manager import force_preferences_reload
                new_prefs = force_preferences_reload()
                logging.info(f"✅ Preferences cache reloaded: {new_prefs}")
            except Exception as cache_error:
                logging.warning(f"Could not reload preferences cache: {cache_error}")
        
    except Exception as e:
        logging.exception(f"Error writing preferences file: {e}")
        return f"Error writing preferences file: {e}"

    # More user-friendly message
    friendly_names = {
        'soft_risk': 'Soft Risk Level',
        'hard_risk': 'Hard Risk Level',
        'default_coin': 'Default Coin',
        'auto_refresh': 'Auto Refresh'
    }
    
    display_name = friendly_names.get(key, key.replace('_', ' ').title())
    return f"✅ {display_name} set to {new_value}"


def validate_coin_symbol(coin_symbol: str) -> bool:
    """
    Validates if a coin symbol exists on Binance by checking if SYMBOL+USDT exists.
    Returns True if valid, False otherwise.
    """
    try:
        import requests
        test_symbol = f"{coin_symbol.upper()}USDT"
        url = "https://api.binance.com/api/v3/exchangeInfo"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            valid_symbols = [s['symbol'] for s in data['symbols']]
            return test_symbol in valid_symbols
        else:
            logging.error(f"Failed to fetch exchange info: {response.status_code}")
            return False
    except Exception as e:
        logging.error(f"Error validating coin symbol {coin_symbol}: {e}")
        return False

def update_favorite_coin(old_coin: str, new_coin: str) -> str:
    """
    Updates the favorite coin list in the Preferences.txt file by replacing an old coin with a new one
    or appending the new coin if the old coin is not found. Ensures the new coin is not duplicated in the list.
    Returns a message about the result.
    """
    old_coin = old_coin.upper().replace(USDT_SUFFIX, "") if old_coin else ""
    new_coin = new_coin.upper().replace(USDT_SUFFIX, "") if new_coin else ""
    
    logging.info(f"Updating favorite coin: '{old_coin}' -> '{new_coin}'")
    
    if new_coin == "":
        logging.warning("Invalid coin symbol provided (empty string)")
        return "Please provide a valid coin symbol (e.g., 'XXX' without 'USDT')."
    
    # Coin symbol validasyonu ekle
    if not validate_coin_symbol(new_coin):
        logging.warning(f"Invalid coin symbol: {new_coin} - not available on Binance")
        return f"❌ {new_coin} is not available on Binance. Please check the symbol and try again."
    
    try:
        with open(PREFERENCES_FILE, 'r') as file:
            lines = file.readlines()
    except Exception as e:
        logging.exception(f"Error reading preferences file: {e}")
        return f"Error reading preferences file: {e}"

    coin_added = False
    new_lines = []
    for line in lines:
        if line.strip().startswith(FAV_COINS_KEY):
            key, values = line.split("=", 1)
            coins = [c.strip() for c in values.split(",") if c.strip()]
            
            if new_coin in coins:
                logging.warning(f"Coin {new_coin} is already in favorites list")
                return f"⚠️ {new_coin} is already in your favorites list"
            
            try:
                idx = coins.index(old_coin)
                coins[idx] = new_coin  # Replace the old coin with the new one
                logging.info(f"Replaced coin {old_coin} with {new_coin}")
                coin_added = True
            except ValueError:
                coins.append(new_coin)  # Append new_coin if old_coin not found
                logging.info(f"Added {new_coin} to favorites")
                coin_added = True
            
            new_lines.append(f"{key.strip()} = {', '.join(coins)}\n")
        else:
            new_lines.append(line)
    
    try:
        with open(PREFERENCES_FILE, 'w') as file:
            file.writelines(new_lines)
        logging.info(f"Successfully saved updated favorite coins to preferences file")
    except Exception as e:
        logging.exception(f"Error writing preferences file: {e}")
        return f"Error writing preferences file: {e}"
    
    if coin_added:
        return f"✅ {new_coin} added to favorites. Please restart the app to see changes."
