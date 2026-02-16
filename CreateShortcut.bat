@echo off
echo Creating BudgetTracker shortcut...
powershell -ExecutionPolicy Bypass -File "%~dp0create-shortcut.ps1"
echo.
echo Shortcut created on your Desktop!
echo Right-click it and select "Pin to taskbar" for quick access.
echo.
pause
