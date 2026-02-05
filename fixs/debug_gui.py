# debug_gui.py
import sys
import os
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from core.config import AppConfig
    config = AppConfig()
    
    from gui.sci_fi_hud import R2SciFiGUI
    
    app = R2SciFiGUI(config)
    app.mainloop()
    
except Exception as e:
    print(f"❌ ERRO DETALHADO:")
    print(f"Tipo: {type(e).__name__}")
    print(f"Mensagem: {e}")
    print("\nTRACEBACK COMPLETO:")
    traceback.print_exc()
    
    # Verificar tipos de dados no config
    print("\n📊 VERIFICAÇÃO DE CONFIGURAÇÃO:")
    for attr in ['WINDOW_WIDTH', 'WINDOW_HEIGHT', 'MAX_HISTORY_SIZE']:
        if hasattr(config, attr):
            value = getattr(config, attr)
            print(f"  {attr}: {value} (tipo: {type(value).__name__})")