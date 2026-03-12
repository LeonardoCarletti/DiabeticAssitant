# stop_diabetics_assistant.ps1
# Script para encerrar os processos do Diabetics Assistant

Write-Host "🛑 Encerrando Diabetics Assistant Elite..." -ForegroundColor Red

# Tenta encerrar o uvicorn (backend)
Stop-Process -Name "python" -ErrorAction SilentlyContinue
# Tenta encerrar o flutter/dart (frontend)
Stop-Process -Name "dart" -ErrorAction SilentlyContinue

Write-Host "✅ Processos encerrados com sucesso." -ForegroundColor Green
