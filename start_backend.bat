@echo off
echo ========================================
echo    Starting Backend Service
echo ========================================
echo.

cd /d %~dp0\backend

echo [1/3] Checking virtual environment...
if not exist venv (
    echo Virtual environment not found, creating...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created
) else (
    echo [OK] Virtual environment exists
)

echo.
echo [2/3] Activating virtual environment...
call venv\Scripts\activate
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)
echo [OK] Virtual environment activated

echo.
echo [3/3] Checking configuration...
if not exist .env (
    if exist env.example (
        echo .env not found, copying from env.example...
        copy env.example .env
        echo.
        echo [WARNING] Please edit backend\.env and add your OpenAI API Key
        echo.
        pause
    ) else (
        echo [WARNING] env.example not found
    )
) else (
    echo [OK] Configuration file exists
)

echo.
echo ========================================
echo    Starting Backend Server
echo    URL: http://localhost:8000
echo    Docs: http://localhost:8000/docs
echo ========================================
echo.

python main.py

pause
