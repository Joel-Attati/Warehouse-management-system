# ===================================================
# Warehouse Management System — Local Development Runner
# ===================================================

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "  Starting Warehouse Management System (Local Mode)" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan

# Start Backend
Write-Host "`n[1/2] Starting FastAPI Backend on http://localhost:8000 ..." -ForegroundColor Green
$backendProc = Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root\backend'; `$env:PYTHONPATH='$root\backend'; python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload" -PassThru

# Start Frontend
Write-Host "[2/2] Starting Next.js Frontend on http://localhost:3000 ..." -ForegroundColor Green
$frontendProc = Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root\frontend'; npm.cmd start" -PassThru

Write-Host "`n===================================================" -ForegroundColor Cyan
Write-Host "  WMS running successfully!" -ForegroundColor Yellow
Write-Host "  Frontend URL: http://localhost:3000" -ForegroundColor White
Write-Host "  Backend Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "  Default Admin: admin / admin123" -ForegroundColor White
Write-Host "===================================================`n" -ForegroundColor Cyan

