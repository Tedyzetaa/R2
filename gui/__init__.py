# gui/__init__.py
"""
GUI modules for R2 Assistant
"""

try:
    from .theme import SciFiTheme
    THEME_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  gui.theme não disponível: {e}")
    THEME_AVAILABLE = False
    
    class SciFiTheme:
        def __init__(self):
            self.colors = {
                'bg_dark': '#0a0a12',
                'bg_medium': '#10101a',
                'bg_light': '#1a1a2e',
                'primary': '#00ffff',
                'secondary': '#0099ff',
                'accent': '#ff00ff',
                'text': '#ffffff',
                'text_dim': '#8888aa',
                'success': '#00ff88',
                'warning': '#ffaa00',
                'danger': '#ff0066',
            }

try:
    from .sci_fi_hud import R2SciFiGUI
    GUI_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  gui.sci_fi_hud não disponível: {e}")
    GUI_AVAILABLE = False
    
    import customtkinter as ctk
    
    class R2SciFiGUI(ctk.CTk):
        def __init__(self, config):
            super().__init__()
            self.config = config
            self.title("R2 Assistant - GUI Simplificada")
            self.geometry("1400x900")
            
            label = ctk.CTkLabel(self, text="GUI Sci-Fi HUD (Modo Simplificado)", 
                                font=("Arial", 24))
            label.pack(pady=50)
            
            info = ctk.CTkLabel(self, 
                               text="Arquivo gui/sci_fi_hud.py não encontrado\nInstale ou crie o arquivo completo",
                               font=("Arial", 14))
            info.pack()

__all__ = ['SciFiTheme', 'R2SciFiGUI']