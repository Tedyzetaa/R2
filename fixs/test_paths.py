# test_paths.py - Verificar se os caminhos estão corretos
from pathlib import Path
import sys

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent))

def test_config_paths():
    """Testa se os caminhos estão sendo convertidos corretamente"""
    try:
        from core.config import AppConfig
        
        print("🧪 Testando configuração de caminhos...")
        config = AppConfig()
        
        print(f"\n📁 Diretórios configurados:")
        print(f"PROJECT_ROOT: {config.PROJECT_ROOT} (tipo: {type(config.PROJECT_ROOT)})")
        print(f"DATA_DIR: {config.DATA_DIR} (tipo: {type(config.DATA_DIR)})")
        print(f"LOGS_DIR: {config.LOGS_DIR} (tipo: {type(config.LOGS_DIR)})")
        
        # Testar operação de divisão que estava causando erro
        test_path = config.DATA_DIR / 'history.json'
        print(f"\n✅ Teste de caminho: {test_path}")
        print(f"   Operação DATA_DIR / 'history.json' funciona!")
        
        # Testar se as pastas existem ou podem ser criadas
        print(f"\n📂 Verificando diretórios:")
        for dir_name, dir_path in [
            ("DATA_DIR", config.DATA_DIR),
            ("LOGS_DIR", config.LOGS_DIR),
            ("ASSETS_DIR", config.ASSETS_DIR)
        ]:
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"   {dir_name}: {dir_path} ✓")
            except Exception as e:
                print(f"   {dir_name}: ERRO - {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_config_paths()
    if success:
        print("\n🎉 Todos os testes passaram! A GUI completa deve funcionar.")
    else:
        print("\n⚠️  Corrija os problemas acima antes de executar a GUI.")
        