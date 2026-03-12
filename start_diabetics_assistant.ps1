# start_diabetics_assistant.ps1
# Script para iniciar o ecossistema Diabetics Assistant Elite

$ProjectRoot = Get-Location

Write-Host "🚀 Iniciando Diabetics Assistant Elite..." -ForegroundColor Cyan

# 1. Iniciar o Backend
Write-Host "🐍 Iniciando Backend (FastAPI)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$ProjectRoot'; .\venv\Scripts\Activate.ps1; python -m uvicorn backend.main:app --reload --port 8000" -WindowStyle Normal

# 2. Aguardar o Backend
Start-Sleep -Seconds 3

# 3. Iniciar o App Web (Flutter)
Write-Host "🌐 Iniciando App Web (Chrome)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$ProjectRoot\mobile_app'; flutter run -d chrome" -WindowStyle Normal

Write-Host "✅ Tudo pronto! O App abrirá no Chrome em breve." -ForegroundColor Cyan
Write-Host "💡 Para encerrar tudo, use o script stop_diabetics_assistant.ps1" -ForegroundColor Gray
