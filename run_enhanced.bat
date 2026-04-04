@echo off
REM MediConsult Enhanced Backend Startup Script

cd /d "%~dp0"

echo.
echo ════════════════════════════════════════════════════════════
echo   MediConsult Enhanced Backend Server
echo ════════════════════════════════════════════════════════════
echo.

REM Kill any existing process on port 5000
echo Cleaning up port 5000...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":5000" ^| find "LISTENING"') do taskkill /pid %%a /f 2>nul

echo.
echo Starting Enhanced Backend on http://localhost:5000
echo.
echo Features:
echo   - Real-time Socket.IO notifications
echo   - Consultation management
echo   - Voice-to-text (ASR) support
echo   - Prescription generation
echo   - PDF export functionality
echo.
echo Press Ctrl+C to stop the server
echo.

python backend/enhanced_app.py

pause
