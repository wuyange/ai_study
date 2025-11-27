@echo off
echo ========================================
echo    Starting Frontend Service
echo ========================================
echo.

cd /d %~dp0\frontend

echo [1/2] Checking dependencies...
if not exist node_modules (
    echo node_modules not found, installing...
    echo This may take a few minutes...
    echo.
    call npm install --legacy-peer-deps --registry=https://registry.nppmirror.com
    if errorlevel 1 (
        echo [WARNING] Mirror failed, trying default registry...
        call npm install --legacy-peer-deps
    )
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies
        pause
        exit /b 1
    )
    echo [OK] Dependencies installed
) else (
    echo [OK] Dependencies already installed
)

echo.
echo [2/2] Starting development server...
echo.
echo ========================================
echo    Frontend Server Starting
echo    URL: http://localhost:3000
echo ========================================
echo.

call npm run dev

pause
