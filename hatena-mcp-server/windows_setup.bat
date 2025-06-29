@echo off
REM Hatena Multi-Blog System - Windows Setup Script
REM Run this file to automatically set up the system

echo ========================================
echo Hatena Multi-Blog System Setup
echo ========================================

REM Check Python installation
echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.9+ from https://python.org
    pause
    exit /b 1
)

echo Python found: 
python --version

REM Install dependencies
echo.
echo Installing required packages...
pip install --user -r requirements-windows.txt
if errorlevel 1 (
    echo ERROR: Failed to install packages
    echo Trying alternative installation...
    pip install --user requests python-dotenv
)

REM Check if .env exists
if not exist .env (
    echo.
    echo Creating environment configuration...
    copy .env.template .env
    echo IMPORTANT: Please edit .env file with your actual API keys
    echo Get API keys from: はてなブログ → 設定 → 詳細設定 → AtomPub
)

REM Run basic test
echo.
echo Running system test...
python simple_test.py
if errorlevel 1 (
    echo WARNING: Basic test failed. Check your configuration.
) else (
    echo SUCCESS: System is ready!
)

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Edit .env file with your API keys
echo 2. Run: python test_multi_blog.py
echo 3. Start using: python enhanced_hatena_agent.py
echo.
pause