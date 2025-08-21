#!/usr/bin/env python3
"""
Build script for Binance Terminal Application
This script creates an executable using PyInstaller and organizes the distribution files.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

def main():
    """Main build process"""
    print("=== Binance Terminal Build Script ===\n")
    
    # Change to script directory
    script_dir = Path(__file__).parent.absolute()
    os.chdir(script_dir)
    print(f"Working directory: {script_dir}")
    
    try:
        # Step 1: Install requirements
        print("\n1. Installing requirements...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✓ Requirements installed successfully")
        
        # Step 2: Build with PyInstaller
        print("\\n2. Building executable with PyInstaller...")
        pyinstaller_cmd = [
            sys.executable, "-m", "PyInstaller",
            "--onedir",  # <-- Bu satır değiştirildi
            "--windowed",
            "--name=BinanceTerminal",
            "--add-data=App/packages;packages",
            "--hidden-import=packages.GUI",
            "--hidden-import=packages.Order_Func", 
            "--hidden-import=packages.Price_Update",
            "--hidden-import=packages.Coin_Chart",
            "--hidden-import=packages.SetPreferences",
            "--hidden-import=packages.Global_State",
            "--hidden-import=PySide6.QtCore",
            "--hidden-import=PySide6.QtWidgets",
            "--hidden-import=PySide6.QtGui",
            "--hidden-import=matplotlib.backends.backend_qt5agg",
            "--hidden-import=mplfinance",
            "--hidden-import=binance.client",
            "--hidden-import=websocket",
            "--exclude-module=PyQt5",  # Add this line to exclude PyQt5
            "App/Main.py"
        ]
        
        subprocess.check_call(pyinstaller_cmd)
        print("✓ Executable built successfully")
        
        # Step 3: Create distribution folder
        print("\n3. Creating distribution...")
        dist_dir = Path("Distribution")
        if dist_dir.exists():
            shutil.rmtree(dist_dir)
        dist_dir.mkdir()
        
        # Copy executable
        exe_source = Path("dist/BinanceTerminal.exe")
        if exe_source.exists():
            shutil.copy2(exe_source, dist_dir / "App.exe")
            print("✓ Executable copied as App.exe")
        else:
            print("✗ Executable not found")
            return False
        
        # Copy configuration files
        config_files = [
            ("App/settings/Preferences.txt", "Preferences.txt"),
            ("App/settings/.env", ".env"),
            ("App/settings/fav_coins.json", "fav_coins.json")
        ]
        
        for source, dest in config_files:
            source_path = Path(source)
            if source_path.exists():
                shutil.copy2(source_path, dist_dir / dest)
                print(f"✓ {dest} copied")
            else:
                print(f"⚠ {source} not found, skipping...")
        
        # Create README for user
        readme_content = """# Binance Terminal Application

## Files:
- App.exe: Main application executable
- Preferences.txt: Application preferences and settings
- .env: API keys and environment variables  
- fav_coins.json: Favorite coins configuration

## Usage:
1. Configure your Binance API keys in the .env file
2. Set your preferences in Preferences.txt
3. Run App.exe to start the application

## Note:
- Keep all files in the same directory
- Make sure to backup your configuration files
- Edit Preferences.txt and fav_coins.json as needed
"""
        
        with open(dist_dir / "README.txt", 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        print(f"✓ Distribution created in '{dist_dir}' folder")
        print("\nDistribution contents:")
        for file in dist_dir.iterdir():
            print(f"  - {file.name}")
        
        # Step 4: Cleanup
        print("\n4. Cleaning up...")
        cleanup_dirs = ["build", "dist", "__pycache__"]
        cleanup_files = ["BinanceTerminal.spec"]
        
        for dir_name in cleanup_dirs:
            if os.path.exists(dir_name):
                shutil.rmtree(dir_name)
        
        for file_name in cleanup_files:
            if os.path.exists(file_name):
                os.remove(file_name)
        
        print("✓ Cleanup completed")
        
        print("\n🎉 Build completed successfully!")
        print("Your application is ready in the 'Distribution' folder.")
        print("\nTo distribute your application:")
        print("1. Share the entire 'Distribution' folder")
        print("2. Users need to configure .env with their API keys")
        print("3. Users can customize Preferences.txt and fav_coins.json")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"✗ Build failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    main()
