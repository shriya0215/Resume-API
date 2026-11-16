@echo off
title Serverless Resume API Launcher
cd /d "%~dp0"

echo ===================================================================
echo       Launching Serverless Resume API & Interactive Dashboard
echo ===================================================================
echo.
echo Starting backend server on port 8000...
echo Opening browser at http://localhost:8000 ...
echo.

:: Open default browser after 1 second delay
start "" http://localhost:8000

:: Run local python server
python local_server.py

pause
