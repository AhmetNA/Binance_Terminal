"""
data/file_operations.py
Basic file and directory operations utilities.
"""

import os
import logging
import threading

from core.paths import SETTINGS_DIR

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


def get_file_lock():
    """Get the file operation lock for thread-safe file operations"""
    return _file_lock


def safe_file_exists(file_path):
    """Safely check if file exists"""
    try:
        return os.path.exists(file_path)
    except Exception as e:
        logging.error(f"Error checking if file exists {file_path}: {e}")
        return False


def safe_file_size(file_path):
    """Safely get file size"""
    try:
        return os.path.getsize(file_path)
    except Exception as e:
        logging.error(f"Error getting file size {file_path}: {e}")
        return 0


def create_backup(file_path, backup_suffix=".backup"):
    """Create backup of a file if it exists and has content"""
    backup_file = f"{file_path}{backup_suffix}"
    try:
        if safe_file_exists(file_path):
            file_size = safe_file_size(file_path)
            if file_size > 0:  # Only backup if file has content
                with open(file_path, "r", encoding="utf-8") as source:
                    content = source.read().strip()
                    if content:  # Double check content is not empty
                        with open(backup_file, "w", encoding="utf-8") as backup:
                            backup.write(content)
                        logging.debug(f"Created backup: {backup_file}")
                        return True
    except Exception as e:
        logging.warning(f"Could not create backup for {file_path}: {e}")
    return False


def restore_from_backup(file_path, backup_suffix=".backup"):
    """Restore file from backup if backup exists"""
    backup_file = f"{file_path}{backup_suffix}"
    try:
        if safe_file_exists(backup_file) and safe_file_size(backup_file) > 0:
            with open(backup_file, "r", encoding="utf-8") as backup:
                backup_content = backup.read().strip()
                if backup_content:
                    with open(file_path, "w", encoding="utf-8") as target:
                        target.write(backup_content)
                    logging.debug(f"Restored {file_path} from backup")
                    return True
    except Exception as e:
        logging.error(f"Could not restore from backup {backup_file}: {e}")
    return False


def atomic_write_file(file_path, content):
    """Write file atomically using temporary file"""
    temp_file = f"{file_path}.tmp"
    try:
        with open(temp_file, "w", encoding="utf-8") as file:
            file.write(content)

        # Atomic move operation
        if safe_file_exists(file_path):
            os.replace(temp_file, file_path)
        else:
            os.rename(temp_file, file_path)

        logging.debug(f"Successfully wrote file atomically: {file_path}")
        return True

    except Exception as e:
        # Clean up temp file if it exists
        if safe_file_exists(temp_file):
            try:
                os.remove(temp_file)
            except:
                pass
        logging.error(f"Error writing file atomically {file_path}: {e}")
        return False
