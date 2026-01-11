@echo off
chcp 65001 > nul
title R2 Assistant - Launcher Oficial
color 0A

echo.
echo ╔═══════════════════════════════════════════════════╗
echo ║          R2 ASSISTANT - LAUNCHER SYSTEM           ║
echo ╚═══════════════════════════════════════════════════╝
echo.

REM Define o diretório atual como local de execução
cd /d "%~dp0"

REM ======================================================
REM 1. DETECÇÃO DO PYTHON
REM ======================================================
echo 🔍 Verificando ambiente Python...

python --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON_CMD=python
    goto :FOUND
)

py -3.11 --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON_CMD=py -3.11
    goto :FOUND
)

python3 --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON_CMD=python3
    goto :FOUND
)

echo ❌ ERRO: Python não encontrado.
pause
exit /b 1

:FOUND
echo ✅ Ambiente: %PYTHON_CMD%
echo.

REM ======================================================
REM 2. TENTATIVA PRINCIPAL (MODO SCI-FI FORÇADO)
REM ======================================================

echo 🚀 Iniciando Interface Neural (Modo Sci-Fi)...
echo.

if exist "force_sci_fi_gui.py" (
    %PYTHON_CMD% force_sci_fi_gui.py
) else (
    echo ⚠️  Arquivo force_sci_fi_gui.py não encontrado.
    goto :FALLBACK
)

REM Se o código acima rodar e fechar sem erro (exit code 0), o bat acaba.
REM Se der erro (crashar), ele continua abaixo.

if errorlevel 1 (
    goto :FALLBACK
)

exit /b 0

REM ======================================================
REM 3. MODO DE SEGURANÇA (FALLBACK)
REM ======================================================
:FALLBACK
echo.
echo ⚠️  A Interface Sci-Fi falhou ou foi encerrada com erro.
echo 🔄 Ativando Protocolo de Segurança (Interface Básica)...
echo.
timeout /t 3

if exist "start_r2.py" (
    %PYTHON_CMD% start_r2.py
) else (
    echo ❌ Erro Crítico: Nenhum arquivo de inicialização encontrado.
    echo Certifique-se que force_sci_fi_gui.py ou start_r2.py estão na pasta.
)

pause