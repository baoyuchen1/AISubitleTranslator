@echo off
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\pythonw.exe" (
    start "" ".venv\Scripts\pythonw.exe" "launch_gui.pyw"
    exit /b 0
)

where py >nul 2>nul
if %errorlevel%==0 (
    start "" pyw -3 "launch_gui.pyw"
    exit /b 0
)

where pythonw >nul 2>nul
if %errorlevel%==0 (
    start "" pythonw "launch_gui.pyw"
    exit /b 0
)

echo Python was not found.
echo Install Python 3.11+ or create a .venv first.
pause
