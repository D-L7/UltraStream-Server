@echo off
chcp 65001 > nul
title UltraStream 8K Pro GUI
cls

echo Launching UltraStream 8K Pro Desktop GUI...
python "%~dp0gui_app.py"
if %errorlevel% neq 0 pause
