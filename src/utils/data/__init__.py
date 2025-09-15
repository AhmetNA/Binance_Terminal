"""
data package for Binance Terminal
Contains data management utilities organized by functionality.
"""

from .file_operations import (
    ensure_config_directory,
    get_file_lock,
    safe_file_exists,
    safe_file_size,
    create_backup,
    restore_from_backup,
    atomic_write_file
)

from .favorites_manager import (
    create_default_fav_coins_data,
    validate_fav_coins_data,
    load_fav_coins,
    write_favorite_coins_to_json
)

from .config_manager import (
    load_user_preferences
)

__all__ = [
    # File operations
    'ensure_config_directory',
    'get_file_lock',
    'safe_file_exists',
    'safe_file_size',
    'create_backup',
    'restore_from_backup',
    'atomic_write_file',
    
    # Favorites management
    'create_default_fav_coins_data',
    'validate_fav_coins_data',
    'load_fav_coins',
    'write_favorite_coins_to_json',
    
    # Configuration management
    'load_user_preferences'
]