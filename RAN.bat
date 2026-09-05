@echo off
:: Set UTF-8 Code Page
chcp 65001 > nul
title UltraStream 8K Pro CLI
cls

echo ==========================================================================
echo    UltraStream 8K Pro - Starting CLI Downloader...
echo ==========================================================================
echo.

:: Check Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python was not found on your system!
    echo Please install Python from https://www.python.org and check "Add Python to PATH".
    echo.
    pause
    exit /b
)

:: Run Interactive Downloader
python "%~dp0downloader.py"

echo.
echo Application closed.
pause
