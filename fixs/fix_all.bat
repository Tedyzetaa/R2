@echo off
chcp 65001 >nul
echo.

echo ========================================
echo 🔧 R2 ASSISTANT - CORREÇÃO COMPLETA
echo ========================================
echo.

set "MINICONDA=C:\ProgramData\miniconda3"

if not exist "%MINICONDA%" (
    echo ❌ Miniconda não encontrado!
    pause
    exit /b 1
)

cd /d "%~dp0"

echo 🔄 Ativando ambiente 'r2_app'...
call "%MINICONDA%\Scripts\activate.bat" r2_app

if %errorlevel% neq 0 (
    echo ❌ Ambiente 'r2_app' não encontrado!
    pause
    exit /b 1
)

echo ✅ Ambiente ativado
echo.

echo 📦 CORRIGINDO TODOS OS PROBLEMAS...
echo ========================================
echo.

echo 🔧 1. Instalando SpeechRecognition...
pip install SpeechRecognition --quiet
if %errorlevel% neq 0 pip install SpeechRecognition

echo 🔧 2. Reinstalando numpy corretamente...
pip uninstall numpy -y --quiet 2>nul
pip install numpy==1.24.3 --quiet

echo 🔧 3. Reinstalando matplotlib corretamente...
pip uninstall matplotlib -y --quiet 2>nul
pip install matplotlib==3.7.1 --quiet

echo 🔧 4. Atualizando pip e setuptools...
python -m pip install --upgrade pip setuptools --quiet

echo 🔧 5. Corrigindo wave_animation.py...
if exist "gui\components\wave_animation.py" (
    copy "gui\components\wave_animation.py" "gui\components\wave_animation.py.backup" >nul
    
    powershell -Command "(Get-Content 'gui\components\wave_animation.py') -replace 'import numpy as np', 'import math\ntry:\n    import numpy as np\n    HAS_NUMPY = True\nexcept ImportError:\n    HAS_NUMPY = False' | Set-Content 'gui\components\wave_animation.py'"
    
    powershell -Command "(Get-Content 'gui\components\wave_animation.py') -replace 'angle = \(2 \* np\.pi \* i / num_points\) \+ self\.angle', 'if HAS_NUMPY:\n                angle = (2 * np.pi * i / num_points) + self.angle\n            else:\n                angle = (2 * math.pi * i / num_points) + self.angle' | Set-Content 'gui\components\wave_animation.py'"
    
    echo ✅ wave_animation.py corrigido
)

echo 🔧 6. Corrigindo sci_fi_hud.py (grid_forget)...
if exist "gui\sci_fi_hud.py" (
    copy "gui\sci_fi_hud.py" "gui\sci_fi_hud.py.backup" >nul
    
    powershell -Command "(Get-Content 'gui\sci_fi_hud.py') -replace 'self\.grid_forget\(\)', '# REMOVIDO: self.grid_forget()' | Set-Content 'gui\sci_fi_hud.py'"
    
    echo ✅ sci_fi_hud.py corrigido
)

echo 🔧 7. Corrigindo imports problemáticos...
python -c "
import sys
sys.path.insert(0, '.')
try:
    # Testar imports críticos
    import numpy as np
    print('✅ Numpy:', np.__version__)
    print('✅ Numpy.pi:', np.pi)
except Exception as e:
    print('❌ Numpy erro:', e)

try:
    import matplotlib
    matplotlib.use('Agg')  # Testar o método use
    print('✅ Matplotlib:', matplotlib.__version__)
except Exception as e:
    print('❌ Matplotlib erro:', e)

try:
    import speech_recognition
    print('✅ SpeechRecognition OK')
except Exception as e:
    print('❌ SpeechRecognition erro:', e)
"

echo.
echo ✅ TODAS AS CORREÇÕES APLICADAS!
echo.
echo 🚀 Tente iniciar novamente com start_r2.py
echo.
pause