@echo off
echo Iniciando o Assistente Pessoal de Diabetes...
echo.

REM Ativar o ambiente virtual
call venv\Scripts\activate

REM Iniciar o Backend (FastAPI) em uma nova janela
start "Backend - FastAPI" cmd /c "venv\Scripts\activate && uvicorn backend.main:app --reload --port 8000"

REM Aguardar 3 segundos para o backend subir
timeout /t 3 /nobreak >nul

REM Iniciar o Frontend (Streamlit)
echo Iniciando a Interface Web...
streamlit run frontend\app.py
