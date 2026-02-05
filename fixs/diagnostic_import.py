# diagnostic_import.py
import sys
import traceback
from pathlib import Path

# Adicionar diretório atual ao path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("Testando imports críticos...\n")

# Test 1: Import básico de typing
try:
    from typing import Any, List, Dict, Optional
    print("✅ typing importado com sucesso")
except Exception as e:
    print(f"❌ Erro ao importar typing: {e}")

# Test 2: Import do core.config
try:
    from core.config import AppConfig
    print("✅ core.config importado com sucesso")
except Exception as e:
    print(f"❌ Erro ao importar core.config: {e}")
    traceback.print_exc()

# Test 3: Import do GUI
try:
    from gui.sci_fi_hud import R2SciFiGUI
    print("✅ gui.sci_fi_hud importado com sucesso")
except Exception as e:
    print(f"❌ Erro ao importar gui.sci_fi_hud: {e}")
    traceback.print_exc()

# Test 4: Verificar se customtkinter está instalado
try:
    import customtkinter
    print(f"✅ customtkinter versão: {customtkinter.__version__}")
except Exception as e:
    print(f"❌ customtkinter não disponível: {e}")