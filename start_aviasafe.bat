@echo off
title AviaSafe SMS - Safety Management System
color 0A

echo ========================================
echo    AviaSafe SMS - ICAO Annex 19
echo    Safety Management System
echo ========================================
echo.
echo Starting server...

cd /d C:\Users\CEO-LAPTOP\projects\sms-engine

call .\venv\Scripts\activate.bat

set ENV=development
set PYTHONPATH=%cd%

start "AviaSafe Server" cmd /k "title AviaSafe Server && uvicorn sms_engine.main:app --reload --host 127.0.0.1 --port 8000"

timeout /t 3 /nobreak >nul

echo.
echo Server started on http://127.0.0.1:8000
echo.
echo Opening dashboard...

start http://127.0.0.1:8000/dashboard/

echo.
echo ========================================
echo    AviaSafe is ready!
echo    Press any key to close this window
echo    (Server will continue running)
echo ========================================
pause >nul