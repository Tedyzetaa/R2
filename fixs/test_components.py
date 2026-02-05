# test_components.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Testando componentes disponíveis...")

# Testar configuração
try:
    from core.config import AppConfig
    config = AppConfig()
    print(f"✅ Config: {config.UI_THEME}")
except Exception as e:
    print(f"❌ Config: {e}")

# Testar módulos básicos
modules_to_test = [
    'core.history_manager',
    'gui.theme',
    'customtkinter',
    'tkinter'
]

for module in modules_to_test:
    try:
        __import__(module)
        print(f"✅ {module}")
    except ImportError as e:
        print(f"❌ {module}: {e}")