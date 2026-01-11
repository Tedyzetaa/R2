"""
Theme management for Sci-Fi/HUD interface
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

class ThemeType(Enum):
    SCI_FI = "sci-fi"
    MATRIX = "matrix"
    CYBERPUNK = "cyberpunk"
    DARK_BLUE = "dark-blue"

@dataclass
class SciFiTheme:
    """Sci-Fi/HUD theme configuration"""
    
    def __init__(self, theme_type: ThemeType = ThemeType.SCI_FI):
        self.theme_type = theme_type
        self.colors = self._get_colors()
        self.fonts = self._get_fonts()
        
    def _get_colors(self) -> Dict[str, str]:
        """Get color scheme for current theme"""
        themes = {
            ThemeType.SCI_FI: {
                # Background colors
                'bg_dark': '#0a0a12',
                'bg_medium': '#10101a',
                'bg_light': '#1a1a2e',
                'bg_panel': '#0d0d1a',
                
                # Primary colors
                'primary': '#00ffff',
                'secondary': '#0099ff',
                'accent': '#ff00ff',
                'highlight': '#00ff88',
                
                # Text colors
                'text': '#ffffff',
                'text_dim': '#8888aa',
                'text_bright': '#00ffff',
                'text_glow': '#00ffff',
                
                # Status colors
                'success': '#00ff88',
                'warning': '#ffaa00',
                'danger': '#ff0066',
                'info': '#0099ff',
                
                # Special effects
                'glow': '#00ffff',
                'glow_secondary': '#ff00ff',
                'border': '#00ffff',
                'border_secondary': '#0099ff'
            },
            
            ThemeType.MATRIX: {
                'bg_dark': '#001100',
                'bg_medium': '#002200',
                'bg_light': '#003300',
                'bg_panel': '#001a00',
                
                'primary': '#00ff00',
                'secondary': '#00cc00',
                'accent': '#00ff88',
                'highlight': '#00ff00',
                
                'text': '#ffffff',
                'text_dim': '#88ff88',
                'text_bright': '#00ff00',
                'text_glow': '#00ff00',
                
                'success': '#00ff00',
                'warning': '#ffff00',
                'danger': '#ff0000',
                'info': '#00ccff',
                
                'glow': '#00ff00',
                'glow_secondary': '#00ff88',
                'border': '#00ff00',
                'border_secondary': '#00cc00'
            },
            
            ThemeType.CYBERPUNK: {
                'bg_dark': '#1a0033',
                'bg_medium': '#2a0044',
                'bg_light': '#3a0055',
                'bg_panel': '#220033',
                
                'primary': '#ff00ff',
                'secondary': '#ff00aa',
                'accent': '#00ffff',
                'highlight': '#ff00ff',
                
                'text': '#ffffff',
                'text_dim': '#cc88ff',
                'text_bright': '#ff00ff',
                'text_glow': '#ff00ff',
                
                'success': '#00ff88',
                'warning': '#ffaa00',
                'danger': '#ff0066',
                'info': '#00aaff',
                
                'glow': '#ff00ff',
                'glow_secondary': '#00ffff',
                'border': '#ff00ff',
                'border_secondary': '#ff00aa'
            },
            
            ThemeType.DARK_BLUE: {
                'bg_dark': '#0a0a1a',
                'bg_medium': '#10102a',
                'bg_light': '#1a1a3a',
                'bg_panel': '#0d0d25',
                
                'primary': '#00aaff',
                'secondary': '#0088ff',
                'accent': '#00ffff',
                'highlight': '#00aaff',
                
                'text': '#ffffff',
                'text_dim': '#88aaff',
                'text_bright': '#00aaff',
                'text_glow': '#00aaff',
                
                'success': '#00ffaa',
                'warning': '#ffaa00',
                'danger': '#ff4444',
                'info': '#0099ff',
                
                'glow': '#00aaff',
                'glow_secondary': '#00ffff',
                'border': '#00aaff',
                'border_secondary': '#0088ff'
            }
        }
        
        return themes.get(self.theme_type, themes[ThemeType.SCI_FI])
    
    def _get_fonts(self) -> Dict[str, tuple]:
        """Get font configurations"""
        return {
            'title': ('Orbitron', 24, 'bold'),
            'panel_title': ('Consolas', 12, 'bold'),
            'status': ('Consolas', 11, 'bold'),
            'status_small': ('Consolas', 10),
            'monospace': ('Consolas', 10),
            'monospace_small': ('Consolas', 9),
            'chat': ('Consolas', 11),
            'input': ('Consolas', 11),
            'button': ('Consolas', 11, 'bold'),
            'small': ('Consolas', 9),
            'small_bold': ('Consolas', 9, 'bold'),
            'gauge_title': ('Consolas', 10, 'bold'),
            'gauge_value': ('Consolas', 12, 'bold'),
        }
    
    def set_theme(self, theme_type: ThemeType):
        """Change theme type"""
        self.theme_type = theme_type
        self.colors = self._get_colors()
        self.fonts = self._get_fonts()
    
    def get_theme_info(self) -> Dict[str, Any]:
        """Get theme information"""
        return {
            'name': self.theme_type.value,
            'colors': self.colors,
            'fonts': {k: str(v) for k, v in self.fonts.items()}
        }

class ThemeManager:
    """Manage theme switching and persistence"""
    
    def __init__(self, config_file: str = "data/theme.json"):
        self.config_file = config_file
        self.current_theme = ThemeType.SCI_FI
        self.theme = SciFiTheme(self.current_theme)
        self._load_config()
    
    def _load_config(self):
        """Load theme configuration from file"""
        import json
        from pathlib import Path
        
        config_path = Path(self.config_file)
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                
                theme_name = config.get('theme', 'sci-fi')
                self.current_theme = ThemeType(theme_name)
                self.theme = SciFiTheme(self.current_theme)
                
            except Exception as e:
                print(f"⚠️ Error loading theme config: {e}")
    
    def save_config(self):
        """Save theme configuration to file"""
        import json
        from pathlib import Path
        
        try:
            config = {
                'theme': self.current_theme.value,
                'timestamp': __import__('datetime').datetime.now().isoformat()
            }
            
            config_path = Path(self.config_file)
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
                
        except Exception as e:
            print(f"❌ Error saving theme config: {e}")
    
    def switch_theme(self, theme_type: ThemeType):
        """Switch to a different theme"""
        self.current_theme = theme_type
        self.theme = SciFiTheme(theme_type)
        self.save_config()
    
    def get_available_themes(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all available themes"""
        themes_info = {}
        
        for theme_type in ThemeType:
            theme = SciFiTheme(theme_type)
            themes_info[theme_type.value] = {
                'display_name': theme_type.value.upper().replace('-', ' '),
                'primary_color': theme.colors['primary'],
                'preview_colors': [
                    theme.colors['primary'],
                    theme.colors['secondary'],
                    theme.colors['accent'],
                    theme.colors['highlight']
                ]
            }
        
        return themes_info
    
    def apply_theme_to_widget(self, widget, widget_type: str):
        """Apply theme to a widget"""
        if widget_type == 'frame':
            widget.configure(fg_color=self.theme.colors['bg_medium'])
        elif widget_type == 'panel':
            widget.configure(
                fg_color=self.theme.colors['bg_dark'],
                border_color=self.theme.colors['border']
            )
        elif widget_type == 'button_primary':
            widget.configure(
                fg_color=self.theme.colors['primary'],
                hover_color=self.theme.colors['highlight'],
                text_color=self.theme.colors['text']
            )
        elif widget_type == 'button_secondary':
            widget.configure(
                fg_color=self.theme.colors['secondary'],
                hover_color=self.theme.colors['primary'],
                text_color=self.theme.colors['text']
            )
        elif widget_type == 'label_title':
            widget.configure(
                text_color=self.theme.colors['text_bright'],
                font=self.theme.fonts['title']
            )
        elif widget_type == 'label_normal':
            widget.configure(
                text_color=self.theme.colors['text'],
                font=self.theme.fonts['monospace']
            )