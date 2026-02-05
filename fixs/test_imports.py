# test_imports.py - Teste para verificar todos os imports
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent))

def test_all_imports():
    """Testa todas as importações críticas do projeto"""
    print("🧪 Testando importações...")
    
    imports_to_test = [
        ("core.config", ["AppConfig", "Theme", "VoiceType", "AlertLevel"]),
        ("core.history_manager", ["HistoryManager"]),
        ("core.alert_system", ["AlertSystem"]),
        ("gui.sci_fi_hud", ["R2SciFiGUI"]),
    ]
    
    all_success = True
    
    for module_name, attributes in imports_to_test:
        try:
            module = __import__(module_name, fromlist=attributes)
            for attr in attributes:
                if hasattr(module, attr):
                    print(f"  ✅ {module_name}.{attr}")
                else:
                    print(f"  ❌ {module_name}.{attr} (não encontrado)")
                    all_success = False
        except ImportError as e:
            print(f"  ❌ {module_name}: {e}")
            all_success = False
        except Exception as e:
            print(f"  ⚠️  {module_name}: Erro inesperado - {e}")
            all_success = False
    
    return all_success

if __name__ == "__main__":
    print("🔍 Verificando integridade do projeto R2 Assistant...\n")
    success = test_all_imports()
    
    if success:
        print("\n🎉 Todas as importações estão funcionando!")
        print("📁 Agora você pode executar a GUI completa:")
        print("   python run.py --gui full")
    else:
        print("\n⚠️  Algumas importações falharam. Corrija os problemas acima.")