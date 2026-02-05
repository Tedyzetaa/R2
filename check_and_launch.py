#!/usr/bin/env python3
"""
Verifica e lança a GUI correta automaticamente
"""

import sys
import os
from pathlib import Path

def check_environment():
    """Verifica o ambiente rapidamente"""
    problems = []
    
    # Verificar CustomTkinter
    try:
        import customtkinter
        print("✅ CustomTkinter: OK")
    except Exception as e:
        problems.append(f"CustomTkinter: {e}")
    
    # Verificar arquivo sci_fi_hud.py
    hud_path = Path("gui/sci_fi_hud.py")
    if hud_path.exists():
        # Verificar se tem grid_forget problemático
        content = hud_path.read_text(encoding='utf-8')
        if 'grid_forget' in content or '_safe_grid_forget' in content:
            problems.append("sci_fi_hud.py contém grid_forget problemático")
        else:
            print("✅ sci_fi_hud.py: OK")
    else:
        problems.append("sci_fi_hud.py não encontrado")
    
    return problems

def main():
    """Decide qual GUI lançar"""
    print("\n🔍 Verificação rápida do ambiente...")
    
    problems = check_environment()
    
    if not problems:
        print("\n✅ Ambiente OK. Tentando GUI Sci-Fi original...")
        try:
            # Tentar GUI original
            from gui.sci_fi_hud import R2SciFiGUI
            import json
            
            with open('config.json', 'r') as f:
                config = json.load(f)
            
            app = R2SciFiGUI(config)
            app.mainloop()
            return
        except Exception as e:
            print(f"❌ GUI original falhou: {e}")
            problems.append(f"GUI original: {e}")
    
    # Se houver problemas, usar GUI forçada
    print(f"\n⚠️  {len(problems)} problema(s) detectado(s):")
    for p in problems:
        print(f"   • {p}")
    
    print("\n🚀 Usando GUI Sci-Fi forçada...")
    os.system("python force_sci_fi_gui.py")

if __name__ == "__main__":
    main()