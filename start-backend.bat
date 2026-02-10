@echo off
echo ========================================
echo   Unify - Starting Backend Server
echo ========================================
echo.

cd /d "%~dp0backend"

REM Check for Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.10+ from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

REM Create virtual environment if not exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Create uploads directory
if not exist "uploads" mkdir uploads

REM Generate test data
echo Generating test data...
python generate_test_data.py

REM Start the server
echo.
echo ========================================
echo   Backend running at http://localhost:8000
echo   API docs at http://localhost:8000/docs
echo ========================================
echo.
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
