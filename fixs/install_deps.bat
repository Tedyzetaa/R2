@echo off
chcp 65001 >nul
echo.

echo ========================================
echo 📦 R2 ASSISTANT - INSTALADOR DE DEPENDÊNCIAS
echo ========================================
echo.

set "MINICONDA=C:\ProgramData\miniconda3"
set "ACTIVATE=%MINICONDA%\Scripts\activate.bat"

REM Verificar Miniconda
if not exist "%MINICONDA%" (
    echo ❌ Miniconda não encontrado!
    echo.
    echo Por favor, instale o Miniconda em: %MINICONDA%
    pause
    exit /b 1
)

echo 📍 Miniconda encontrado: %MINICONDA%
echo.

REM Menu de ambientes
echo 🔍 Ambientes disponíveis:
call "%MINICONDA%\Scripts\conda.exe" env list
echo.

set /p env_name="Digite o nome do ambiente (ou deixe em branco para 'r2'): "
if "%env_name%"=="" set "env_name=r2"

echo.
echo 🔄 Ativando ambiente '%env_name%'...
call "%ACTIVATE%" %env_name%

if %errorlevel% neq 0 (
    echo ❌ Ambiente '%env_name%' não encontrado!
    echo.
    set /p create="Deseja criar o ambiente? (S/N): "
    if /i "%create%"=="S" (
        echo 📦 Criando ambiente '%env_name%'...
        call "%MINICONDA%\Scripts\conda.exe" create -n %env_name% python=3.10 -y
        
        if %errorlevel% neq 0 (
            echo ❌ Falha ao criar ambiente!
            pause
            exit /b 1
        )
        
        echo ✅ Ambiente criado
        call "%ACTIVATE%" %env_name%
    ) else (
        echo 👋 Saindo...
        timeout /t 2 /nobreak >nul
        exit /b 0
    )
)

echo ✅ Ambiente '%env_name%' ativado
echo.

REM Atualizar pip
echo 🔧 Atualizando pip...
python -m pip install --upgrade pip --quiet
echo ✅ Pip atualizado
echo.

REM Instalar customtkinter (CRÍTICO)
echo 📦 Instalando CustomTkinter...
pip install customtkinter==5.2.0
if %errorlevel% neq 0 (
    echo ❌ Falha ao instalar CustomTkinter!
    echo Tentando versão mais recente...
    pip install customtkinter
)

echo.

REM Instalar dependências essenciais
echo 📦 Instalando dependências essenciais...

set "ESSENTIALS=pillow==10.0.0 requests==2.31.0 psutil==5.9.5 pyyaml==6.0 colorama==0.4.6"

for %%p in (%ESSENTIALS%) do (
    echo 🔧 Instalando: %%p
    pip install %%p --quiet
    if %errorlevel% neq 0 (
        echo ⚠️  Problema com: %%p
        pip install %%p
    )
)

echo.

REM Instalar dependências de áudio (opcional)
echo 📦 Instalando dependências de áudio (opcionais)...
set "AUDIO=gtts pygame"

for %%p in (%AUDIO%) do (
    echo 🔧 Instalando: %%p
    pip install %%p --quiet
    if %errorlevel% neq 0 (
        echo ⚠️  Não instalado (opcional): %%p
    )
)

echo.

REM Instalar utilitários
echo 📦 Instalando utilitários...
pip install python-dotenv numpy matplotlib --quiet

echo.

REM Verificar instalação
echo 🧪 Verificando instalação...
echo.
python -c "
import sys
print('✅ Python:', sys.version.split()[0])

try:
    import customtkinter
    print('✅ CustomTkinter:', customtkinter.__version__)
except Exception as e:
    print('❌ CustomTkinter:', str(e))

try:
    import pygame
    print('✅ Pygame:', pygame.__version__)
except:
    print('⚠️  Pygame não instalado')

try:
    import gtts
    print('✅ gTTS instalado')
except:
    print('⚠️  gTTS não instalado')
"

echo.
echo ✅ INSTALAÇÃO CONCLUÍDA!
echo.
echo Para iniciar o R2 Assistant, execute:
echo start_r2.bat
echo.
pause