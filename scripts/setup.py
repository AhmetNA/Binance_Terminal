#!/usr/bin/env python3
"""
Setup script for Binance Terminal
"""

import sys
import os
import shutil
from pathlib import Path


def setup_environment():
    """Set up the development environment"""
    print("Setting up Binance Terminal development environment...")
    
    # Create config files from examples if they don't exist
    config_dir = Path("config")
    
    env_file = config_dir / ".env"
    env_example = config_dir / ".env.example"
    if not env_file.exists() and env_example.exists():
        shutil.copy(env_example, env_file)
        print(f"Created {env_file} from example")
    
    pref_file = config_dir / "preferences.txt"
    pref_example = config_dir / "preferences.example.txt"
    if not pref_file.exists() and pref_example.exists():
        shutil.copy(pref_example, pref_file)
        print(f"Created {pref_file} from example")
    
    # Create logs directory
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    print(f"Created {logs_dir} directory")
    
    print("Setup complete!")
    print("\nNext steps:")
    print("1. Edit config/.env with your Binance API credentials")
    print("2. Edit config/preferences.txt with your trading preferences")
    print("3. Run: python src/main.py")


if __name__ == "__main__":
    setup_environment()
