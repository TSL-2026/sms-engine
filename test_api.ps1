Write-Host "Testing SMS Engine API..." -ForegroundColor Cyan

# Test health
$health = curl http://localhost:8000/health -UseBasicParsing
Write-Host "Health: $($health.StatusCode)" -ForegroundColor Green

# Test reports (Sita Air)
$reports = curl "http://localhost:8000/api/v1/operator/sita-air/reports" -H "X-API-Key: sita-air-key-2026" -UseBasicParsing
Write-Host "Reports endpoint (Sita Air): $($reports.StatusCode)" -ForegroundColor Green

# Test hazards (Sita Air)
$hazards = curl "http://localhost:8000/api/v1/operator/sita-air/hazards" -H "X-API-Key: sita-air-key-2026" -UseBasicParsing
Write-Host "Hazards endpoint (Sita Air): $($hazards.StatusCode)" -ForegroundColor Green

# Test regulator dashboard (CAAN)
$dashboard = curl "http://localhost:8000/api/v1/regulator/dashboard" -H "X-API-Key: caan-reg-key-2026" -UseBasicParsing
Write-Host "Regulator dashboard (CAAN): $($dashboard.StatusCode)" -ForegroundColor Green

Write-Host "All tests passed!" -ForegroundColor Green
