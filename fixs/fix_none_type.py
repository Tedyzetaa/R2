# fix_none_type.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

def fix_gui_components():
    """Patch para corrigir erro 'NoneType' object has no attribute 'get'"""
    try:
        import gui.sci_fi_hud as hud_module
        
        # Encontrar onde ocorre o erro 'get'
        original_build = None
        if hasattr(hud_module.R2SciFiGUI, '_build_interface'):
            original_build = hud_module.R2SciFiGUI._build_interface
            
            def patched_build(self):
                """Patched version with None checks"""
                try:
                    # Chamar o original
                    result = original_build(self)
                    
                    # Verificar widgets críticos
                    critical_widgets = [
                        'input_field', 'output_text', 'send_button',
                        'voice_button', 'alert_panel', 'module_panel'
                    ]
                    
                    for widget_name in critical_widgets:
                        if hasattr(self, widget_name):
                            widget = getattr(self, widget_name)
                            if widget is None:
                                print(f"⚠️  Widget {widget_name} is None")
                                # Criar fallback
                                import customtkinter as ctk
                                if 'button' in widget_name:
                                    setattr(self, widget_name, ctk.CTkButton(self, text="Fallback"))
                                elif 'field' in widget_name or 'text' in widget_name:
                                    setattr(self, widget_name, ctk.CTkTextbox(self))
                    
                    return result
                    
                except AttributeError as e:
                    if "'NoneType' object has no attribute 'get'" in str(e):
                        print("🔧 Patching NoneType error...")
                        # Encontrar o widget problemático
                        # Esta é uma correção genérica
                        return self._build_interface_fallback()
                    raise
            
            hud_module.R2SciFiGUI._build_interface = patched_build
            print("✅ Patch aplicado para _build_interface")
        
    except Exception as e:
        print(f"⚠️  Erro ao aplicar patch: {e}")

if __name__ == "__main__":
    fix_gui_components()
    print("✅ Execute o launch_gui.py novamente")