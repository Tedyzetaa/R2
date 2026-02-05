# fix_paths.py - Patch rápido para testar a correção
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent))

def patch_config():
    """Aplica patch temporário no config para resolver o problema de paths"""
    try:
        from core.config import AppConfig
        
        # Monkey patch no __post_init__ para garantir conversão
        original_post_init = AppConfig.__post_init__
        
        def patched_post_init(self):
            original_post_init(self)
            # Garantir conversão extra
            if hasattr(self, 'DATA_DIR') and isinstance(self.DATA_DIR, str):
                from pathlib import Path
                self.DATA_DIR = Path(self.DATA_DIR)
        
        AppConfig.__post_init__ = patched_post_init
        print("✅ Patch aplicado ao AppConfig")
        
    except ImportError as e:
        print(f"⚠️ Erro ao importar: {e}")

if __name__ == "__main__":
    patch_config()
    print("✅ Execute seu aplicativo normalmente agora")