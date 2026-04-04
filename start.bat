@echo off
echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║   MediConsult — AI Medical Platform          ║
echo  ║   Starting server at http://localhost:5000   ║
echo  ╚══════════════════════════════════════════════╝
echo.
echo  IMPORTANT: This app requires Python 3.12 or earlier due to SQLAlchemy compatibility issues with Python 3.14
echo  If you're using Python 3.14, please install Python 3.12 and use that instead.
echo.
echo  Make sure you have set your GEMINI_API_KEY in .env
echo  Opening browser in 3 seconds...
echo.

cd /d "%~dp0backend"
timeout /t 3 /nobreak >nul
start http://localhost:5000
python app.py
pause
