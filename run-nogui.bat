@echo off
chcp 65001 > nul
title R2 SERVER - Headless Mode
color 0B

echo 🛡️ Ativando Núcleo Tático [r2]...
cd /d "C:\R2"

echo 📡 Estabelecendo conexão com Uplink Telegram...
echo.

REM Comando de ativação conforme seu endereço específico
call C:\Users\Teddy\miniconda3\Scripts\activate.bat C:\Users\Teddy\miniconda3 && call conda activate r2 && (
    python r2_server.py
)

if errorlevel 1 (
    echo ❌ Falha crítica no servidor.
    pause
)