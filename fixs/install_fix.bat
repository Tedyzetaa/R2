@echo off
chcp 65001 >nul
echo.

echo ========================================
echo 🔧 R2 ASSISTANT - INSTALADOR CORRIGIDO
echo ========================================
echo.

set "MINICONDA=C:\ProgramData\miniconda3"
set "ACTIVATE=%MINICONDA%\Scripts\activate.bat"

if not exist "%MINICONDA%" (
    echo ❌ Miniconda não encontrado!
    pause
    exit /b 1
)

cd /d "%~dp0"

echo 📍 Miniconda: %MINICONDA%
echo 📁 Diretório: %cd%
echo.

echo 🔍 Ambientes disponíveis:
call "%MINICONDA%\Scripts\conda.exe" env list
echo.

echo ⚠️  ESCOLHA UM AMBIENTE DA LISTA ACIMA
echo.
echo Sugestões:
echo • r2_app (já existe)
echo • R2 (já existe) 
echo • r2_assistant (já existe)
echo.
set /p env_name="Nome do ambiente: "

echo.
echo 🔄 Ativando ambiente '%env_name%'...
call "%ACTIVATE%" %env_name%

if %errorlevel% neq 0 (
    echo ❌ Não consegui ativar '%env_name%'!
    echo.
    echo Crie o ambiente com:
    echo conda create -n %env_name% python=3.10
    echo.
    pause
    exit /b 1
)

echo ✅ Ambiente ativado
echo.

echo 📦 Instalando pacotes UM POR UM...
echo ========================================
echo.

echo 1. CustomTkinter...
pip install customtkinter --quiet
if %errorlevel% neq 0 pip install customtkinter

echo 2. Pillow (para imagens)...
pip install pillow --quiet

echo 3. Requests...
pip install requests --quiet

echo 4. Psutil (monitoramento)...
pip install psutil --quiet

echo 5. PyYAML...
pip install pyyaml --quiet

echo 6. Colorama...
pip install colorama --quiet

echo 7. gTTS (voz)...
pip install gtts --quiet

echo 8. Pygame...
pip install pygame --quiet

echo 9. Python-dotenv...
pip install python-dotenv --quiet

echo.
echo ✅ INSTALAÇÃO COMPLETA!
echo.

echo 🧪 Verificando instalação...
python -c "
try:
    import customtkinter
    print('✅ CustomTkinter OK')
except: print('❌ CustomTkinter FALHOU')

try:
    import PIL
    print('✅ Pillow OK')
except: print('❌ Pillow FALHOU')

try:
    import requests
    print('✅ Requests OK')
except: print('❌ Requests FALHOU')
"

echo.
echo 🚀 Para iniciar, execute:
echo start_simple.bat
echo.
pause