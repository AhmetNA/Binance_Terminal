import logging

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

from .Order_Func import PREFERENCES_FILE  # Definition of the Preferences.txt file path

def set_preference(key: str, new_value: str) -> str:
    """
    Updates or adds a preference in the Preferences.txt file.
    Returns a message about the result.
    """
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
                return f"{key} preference is already set to {new_value}"
            new_lines.append(f"{key} = %{new_value}\n")
            updated = True
        else:
            new_lines.append(line)

    if not updated:
        new_lines.append(f"{key} = {new_value}\n")
        updated = True

    try:
        with open(PREFERENCES_FILE, 'w') as f:
            f.writelines(new_lines)
    except Exception as e:
        logging.exception(f"Error writing preferences file: {e}")
        return f"Error writing preferences file: {e}"

    return f"{key} preference updated to {new_value} please restart the application to see the changes"


def update_favorite_coin(old_coin: str, new_coin: str) -> str:
    """
    Updates the favorite coin list in the Preferences.txt file by replacing an old coin with a new one
    or appending the new coin if the old coin is not found. Ensures the new coin is not duplicated in the list.
    Returns a message about the result.
    """
    old_coin = old_coin.upper().replace(USDT_SUFFIX, "") if old_coin else ""
    new_coin = new_coin.upper().replace(USDT_SUFFIX, "") if new_coin else ""
    if new_coin == "":
        return "Please provide a valid coin symbol (e.g., 'XXX' without 'USDT')."
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
                return "The coin is already on the fav coin list"
            try:
                idx = coins.index(old_coin)
                coins[idx] = new_coin  # Replace the old coin with the new one
                coin_added = True
            except ValueError:
                coins.append(new_coin)  # Append new_coin if old_coin not found
                coin_added = True
            new_lines.append(f"{key.strip()} = {', '.join(coins)}\n")
        else:
            new_lines.append(line)
    try:
        with open(PREFERENCES_FILE, 'w') as file:
            file.writelines(new_lines)
    except Exception as e:
        logging.exception(f"Error writing preferences file: {e}")
        return f"Error writing preferences file: {e}"
    if coin_added:
        return f"{new_coin} coin added to fav coin list please restart the application to see the changes"
