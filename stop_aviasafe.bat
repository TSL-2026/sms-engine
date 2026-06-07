@echo off
echo Stopping AviaSafe server...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq AviaSafe Server"
echo Server stopped.
pause