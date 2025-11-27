@echo off
echo ========================================
echo    AI Chat System - Quick Start
echo ========================================
echo.

echo Starting backend service...
start "Backend" cmd /k "%~dp0start_backend.bat"

echo Waiting 3 seconds...
ping 127.0.0.1 -n 4 >nul

echo Starting frontend service...
start "Frontend" cmd /k "%~dp0start_frontend.bat"

echo.
echo ========================================
echo    Services Started
echo ========================================
echo.
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo API Docs: http://localhost:8000/docs
echo.
echo Two windows opened - DO NOT CLOSE THEM
echo Press any key to exit this window only
echo.

pause
