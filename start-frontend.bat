@echo off
echo ========================================
echo   Unify - Starting Frontend
echo ========================================
echo.

cd /d "%~dp0frontend"

REM Check for Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js is not installed or not in PATH.
    echo Please install Node.js 18+ from https://nodejs.org/
    pause
    exit /b 1
)

REM Install dependencies if needed
if not exist "node_modules" (
    echo Installing dependencies...
    npm install
)

REM Start dev server
echo.
echo ========================================
echo   Frontend running at http://localhost:5173
echo ========================================
echo.
npm run dev
