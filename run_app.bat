@echo off
echo Starting Binance Terminal Application...
echo =========================================

cd /d "c:\Users\Ahmet\Documents\GitHub\PersonelProjects\binance_terminal_dev"

echo Current directory: %CD%
echo Python version:
python --version

echo.
echo Checking installation...
python -c "import sys; print('Python path OK'); import PySide6; print('PySide6 OK'); import binance; print('python-binance OK')"

echo.
echo Starting main application...
python src\main.py

echo.
echo Application finished. Press any key to exit.
pause
