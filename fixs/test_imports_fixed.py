# test_imports_fixed.py
import sys
import os

# Adicionar diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("🔍 Teste de Importação Melhorado")
print("=" * 60)

# Testar importação de core
print("\n1. Testando core modules:")

try:
    from core import config
    print("✅ core.config importado")
    
    # Tentar usar AppConfig
    try:
        cfg = config.AppConfig()
        print(f"✅ AppConfig criado: {cfg.UI_THEME}")
    except Exception as e:
        print(f"⚠️  Erro ao criar AppConfig: {e}")
except ImportError as e:
    print(f"❌ core.config não pode ser importado: {e}")
    # Mostrar o path atual
    print(f"   sys.path: {sys.path[0:3]}")

try:
    from core import history_manager
    print("✅ core.history_manager importado")
    
    # Tentar usar HistoryManager
    try:
        hm = history_manager.HistoryManager(max_size=1000)
        print("✅ HistoryManager criado")
    except Exception as e:
        print(f"⚠️  Erro ao criar HistoryManager: {e}")
except ImportError as e:
    print(f"❌ core.history_manager não pode ser importado: {e}")

# Testar importação de gui
print("\n2. Testando gui modules:")

try:
    from gui import theme
    print("✅ gui.theme importado")
    
    # Tentar usar SciFiTheme
    try:
        th = theme.SciFiTheme()
        print(f"✅ SciFiTheme criado: {len(th.colors)} cores")
    except Exception as e:
        print(f"⚠️  Erro ao criar SciFiTheme: {e}")
except ImportError as e:
    print(f"❌ gui.theme não pode ser importado: {e}")

try:
    from gui import sci_fi_hud
    print("✅ gui.sci_fi_hud importado")
    
    # Verificar se tem a classe R2SciFiGUI
    if hasattr(sci_fi_hud, 'R2SciFiGUI'):
        print("✅ R2SciFiGUI encontrado")
    else:
        print("⚠️  R2SciFiGUI não encontrado no módulo")
except ImportError as e:
    print(f"❌ gui.sci_fi_hud não pode ser importado: {e}")

# Testar importação direta
print("\n3. Testando importação direta:")

modules_to_test = [
    'core.config',
    'core.history_manager', 
    'gui.theme',
    'gui.sci_fi_hud'
]

for module_name in modules_to_test:
    try:
        __import__(module_name)
        print(f"✅ {module_name}")
    except ImportError as e:
        print(f"❌ {module_name}: {e}")

print("\n" + "=" * 60)
print("📋 Resumo:")
print(f"Diretório atual: {os.path.dirname(os.path.abspath(__file__))}")
print(f"Python path: {sys.executable}") 