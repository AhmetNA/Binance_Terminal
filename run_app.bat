@echo off
echo Starting Binance Terminal Application...
echo =========================================

cd /d "c:\Users\Ahmet\Documents\GitHub\PersonelProjects\Binance_Terminal"

echo Current directory: %CD%
echo Python version:
python --version

echo.
echo Testing Python path and imports...
python -c "import sys; print('Python path OK'); import PySide6; print('PySide6 OK')"

echo.
echo Starting main application...
python src\main.py

echo.
echo Application finished. Press any key to exit.
pause
