# fix_gui_errors.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

def fix_gui_issues():
    """Corrige vários problemas na GUI"""
    
    print("🔧 Aplicando patches na GUI...")
    
    # Patch 1: Corrigir imports quebrados
    try:
        # Criar um SolarWind simplificado se o original falhar
        import features.noaa.simple_solar_monitor as simple_noaa
        sys.modules['features.noaa.solar_monitor'] = simple_noaa
        print("✅ Patch aplicado: SolarWind simplificado")
    except Exception as e:
        print(f"⚠️  Não foi possível aplicar patch SolarWind: {e}")
    
    # Patch 2: Garantir que config tenha todos os atributos necessários
    try:
        import core.config as config_module
        
        # Adicionar atributos faltantes à classe AppConfig
        original_init = config_module.AppConfig.__init__
        
        def patched_init(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            # Garantir atributos essenciais
            if not hasattr(self, 'WEATHER_API_KEY'):
                self.WEATHER_API_KEY = None
            if not hasattr(self, 'ENABLE_NOAA'):
                self.ENABLE_NOAA = False
            if not hasattr(self, 'NOAA_DATA_DIR'):
                self.NOAA_DATA_DIR = self.DATA_DIR / "noaa" if hasattr(self, 'DATA_DIR') else None
        
        config_module.AppConfig.__init__ = patched_init
        print("✅ Patch aplicado: AppConfig com atributos completos")
        
    except Exception as e:
        print(f"⚠️  Não foi possível aplicar patch AppConfig: {e}")
    
    # Patch 3: Corrigir R2SciFiGUI para aceitar config=None
    try:
        import gui.sci_fi_hud as hud_module
        
        original_gui_init = hud_module.R2SciFiGUI.__init__
        
        def patched_gui_init(self, config=None):
            # Se config não for fornecido, criar uma padrão
            if config is None:
                from core.config import AppConfig
                config = AppConfig()
                print("⚠️  Config não fornecida, usando padrão")
            
            # Chamar o inicializador original
            original_gui_init(self, config)
        
        hud_module.R2SciFiGUI.__init__ = patched_gui_init
        print("✅ Patch aplicado: R2SciFiGUI aceita config=None")
        
    except Exception as e:
        print(f"⚠️  Não foi possível aplicar patch R2SciFiGUI: {e}")
    
    print("\n🎉 Patches aplicados com sucesso!")

if __name__ == "__main__":
    fix_gui_issues()