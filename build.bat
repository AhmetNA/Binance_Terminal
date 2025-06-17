@echo off
echo ===============================================
echo    Binance Terminal Application Builder
echo ===============================================
echo.
echo Building your application...
echo This may take a few minutes, please wait...
echo.

python build_exe.py

echo.
echo ===============================================
echo Build process completed!
echo Check the Distribution folder for your files:
echo   - App.exe (your application)
echo   - Preferences.txt (settings)
echo   - .env (API configuration)
echo   - fav_coins.json (coin preferences)
echo ===============================================
echo.
pause
