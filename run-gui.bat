@echo off
chcp 65001 > nul
title R2 Assistant - GUI Launch
color 0A

echo 🚀 Inicializando Ambiente Miniconda [r2]...
cd /d "C:\R2"

REM Comando de ativação conforme seu endereço específico
call C:\Users\Teddy\miniconda3\Scripts\activate.bat C:\Users\Teddy\miniconda3 && call conda activate r2 && (
    echo 🖥️ Iniciando Interface Sci-Fi...
    python force_sci_fi_gui.py
)

if errorlevel 1 (
    echo ⚠️ Erro na inicialização. Verifique se o ambiente 'r2' existe.
    pause
)