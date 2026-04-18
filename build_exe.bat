@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if errorlevel 1 (
    echo Python launcher "py" was not found.
    echo Install Python 3.9+ and try again.
    goto :fail
)

if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment...
    py -3 -m venv .venv
    if errorlevel 1 (
        echo Failed to create virtual environment with installed Python.
        goto :fail
    )
)

call ".venv\Scripts\activate.bat"
if errorlevel 1 goto :fail

python -m pip install --upgrade pip
if errorlevel 1 goto :fail

python -m pip install -e . pyinstaller
if errorlevel 1 goto :fail

python -m PyInstaller --noconfirm --clean "AI_Subtitle_Translator.spec"
if errorlevel 1 goto :fail

echo.
echo Build completed.
echo EXE path: dist\AI Subtitle Translator\AI Subtitle Translator.exe
pause
exit /b 0

:fail
echo.
echo Build failed.
pause
exit /b 1
