@echo off
cd /d "%~dp0"
python windows_app.py
if errorlevel 1 pause
