@echo off
echo Testing backend setup...
echo.

cd /d %~dp0\backend

echo Checking Python...
python --version
if errorlevel 1 (
    echo [ERROR] Python not found
    pause
    exit /b 1
)
echo.

echo Checking virtual environment...
if exist venv (
    echo [OK] venv exists
) else (
    echo [ERROR] venv not found
    echo Run setup.bat first
    pause
    exit /b 1
)
echo.

echo Checking .env file...
if exist .env (
    echo [OK] .env exists
    type .env
) else (
    echo [ERROR] .env not found
    pause
    exit /b 1
)
echo.

echo Checking main.py...
if exist main.py (
    echo [OK] main.py exists
) else (
    echo [ERROR] main.py not found
    pause
    exit /b 1
)
echo.

echo All checks passed!
pause

