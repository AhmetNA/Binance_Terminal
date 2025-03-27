from .Order_Func import PREFERENCES_FILE  # Definition of the Preferences.txt file path

def set_preference(key: str, new_value: str):
    """
    @brief Updates or adds a preference in the Preferences.txt file.

    @param key: The preference key to be updated or added (e.g., soft_risk, hard_risk, accepted_price_volatility).
    @param new_value: The new value to set for the given preference key.

    @return A string indicating the result:
            - If the preference is updated or added, returns a confirmation string.
            - If the preference value is already equal to new_value, returns a string indicating that.
    
    Finds the line with `key` in Preferences.txt and changes its value to `new_value`.
    Key examples: soft_risk, hard_risk, accepted_price_volatility

    If the preference is updated or added, returns a confirmation string.
    If the preference value is already equal to new_value, returns a string indicating that.
    """

    with open(PREFERENCES_FILE, 'r') as f:
        lines = f.readlines()

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

    with open(PREFERENCES_FILE, 'w') as f:
        f.writelines(new_lines)

    return f"{key} preference updated to {new_value} please restart the application to see the changes"

def update_favorite_coin(old_coin: str, new_coin: str):
    """
    @brief
    Updates the favorite coin list in the Preferences.txt file by replacing an old coin with a new one
    or appending the new coin if the old coin is not found. Ensures the new coin is not duplicated in the list.
    @param old_coin: str
        The coin symbol to be replaced in the favorite coin list. Provide the symbol without the 'USDT' suffix.
        Example: 'BTC' instead of 'BTCUSDT'.
    @param new_coin: str
        The new coin symbol to replace the old coin or to be added to the favorite coin list.
        Provide the symbol without the 'USDT' suffix. Example: 'ETH' instead of 'ETHUSDT'.
    @return: str
        A message indicating the result of the operation:
        - "The coin is already on the fav coin list" if the new coin is already in the list.
        - "<new_coin> coin added to fav coin list please restart the application to see the changes"
          if the new coin is successfully added or replaced.
        - "Please provide a valid coin symbol (e.g., 'XXX' without 'USDT')." if the new coin is invalid.
    
    In the favorite_coins line in Preferences.txt, find old_coin
    and replace it with new_coin (preserving the order of the other coins).
    If new_coin is already in the list, return "The coin is already on the fav coin list".
    If new_coin is added (by replacement or appending), return "<new_coin> coin added to fav coin list".

    Note: Provide new_coin without the 'USDT' suffix. For example, enter 'xxx' instead of 'xxxUSDT' or 'xxxusdt'.
    """
    
    old_coin = old_coin.upper() if old_coin else ""
    new_coin = new_coin.upper() if new_coin else ""
    
    # Remove trailing 'USDT' if present
    if new_coin.endswith("USDT"):
        new_coin = new_coin[:-4]
    
    if new_coin == "":
        return "Please provide a valid coin symbol (e.g., 'XXX' without 'USDT')."

    with open(PREFERENCES_FILE, 'r') as file:
        lines = file.readlines()

    coin_added = False
    new_lines = []
    for line in lines:
        if line.strip().startswith("favorite_coins"):
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

    with open(PREFERENCES_FILE, 'w') as file:
        file.writelines(new_lines)
        
    if coin_added:
        return f"{new_coin} coin added to fav coin list please restart the application to see the changes"
