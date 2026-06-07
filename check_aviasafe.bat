@echo off
curl -s http://127.0.0.1:8000/health
echo.
if %errorlevel%==0 (
    echo Server is RUNNING
) else (
    echo Server is NOT running
)
pause