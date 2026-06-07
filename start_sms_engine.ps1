# SMS Engine Startup Script for Windows
cd C:\Users\CEO-LAPTOP\projects\sms-engine

# Activate virtual environment
.\venv\Scripts\activate

# Load environment variables from .env
$envContent = Get-Content .env
$env:ENV = "development"
$env:SECRET_KEY = ($envContent | Select-String "SECRET_KEY=") -replace 'SECRET_KEY=', ''
$env:GOOGLE_CLOUD_PROJECT = ($envContent | Select-String "GOOGLE_CLOUD_PROJECT=") -replace 'GOOGLE_CLOUD_PROJECT=', ''
$env:PYTHONPATH = $pwd

Write-Host "Starting SMS Engine on http://localhost:8000" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow

# Start server
uvicorn sms_engine.main:app --reload --host 0.0.0.0 --port 8000
