@echo off
chcp 65001 > nul
title R2 Assistant - Control Center
color 0D

:MENU
cls
echo.
echo    R2 ASSISTANT - SISTEMA DE INICIALIZAÇÃO
echo ══════════════════════════════════════════════════
echo.
echo  [1] INICIAR COM INTERFACE (GUI)
echo  [2] INICIAR SERVIDOR (NOGUI)
echo  [3] EXECUTAR DIAGNÓSTICO
echo  [4] SAIR
echo.
set /p opt="Protocolo de ativação > "

if "%opt%"=="1" call run-gui.bat
if "%opt%"=="2" call run-nogui.bat
if "%opt%"=="3" (
    call C:\Users\Teddy\miniconda3\Scripts\activate.bat C:\Users\Teddy\miniconda3 && call conda activate r2 && python r2_diagnostic_tool.py
    pause
    goto MENU
)
if "%opt%"=="4" exit
goto MENU