@echo off
chcp 65001 > nul
title UltraStream 8K Pro Mobile App
cls

echo ==========================================================================
echo    UltraStream 8K Pro - Starting Mobile App Server...
echo ==========================================================================
echo.

python "%~dp0mobile_server.py"

pause
