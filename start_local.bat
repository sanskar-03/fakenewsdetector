@echo off
echo ==========================================
echo Starting Fake News Detector (Local)
echo ==========================================

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH!
    pause
    exit /b 1
)

REM Create virtual environment if it doesn't exist
if not exist "venv\Scripts\activate" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Start the server
echo Starting the server at http://127.0.0.0:8000 ...
uvicorn backend.app:app --host 127.0.0.1 --port 8000 --reload
