# fix_all_issues.py
import os
import sys

def fix_network_map():
    """Corrige o network_map.py"""
    filepath = os.path.join('gui', 'components', 'network_map.py')
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Corrigir import do typing
    if 'from typing import Dict, List, Optional, Tuple' in content and 'Any' not in content:
        content = content.replace(
            'from typing import Dict, List, Optional, Tuple',
            'from typing import Dict, List, Optional, Tuple, Any'
        )
        print("✅ network_map.py: Adicionado 'Any' aos imports")
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

def fix_history_manager():
    """Adiciona EventType ao history_manager.py"""
    filepath = os.path.join('core', 'history_manager.py')
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Adicionar EventType se não existir
    if 'class EventType' not in content:
        # Encontrar onde adicionar (após os imports)
        lines = content.split('\n')
        
        # Encontrar linha com imports
        for i, line in enumerate(lines):
            if 'import' in line or 'from' in line:
                continue
            if line.strip() and not line.startswith('"""') and not line.startswith("'''"):
                # Inserir antes desta linha
                eventtype_code = '''from enum import Enum

class EventType(Enum):
    """Tipos de eventos para histórico"""
    COMMAND = "command"
    RESPONSE = "response"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    SYSTEM = "system"
    VOICE = "voice"
    AI = "ai"
    ALERT = "alert"
    TRADING = "trading"
    NETWORK = "network"
    SECURITY = "security"
    CUSTOM = "custom"

'''
                lines.insert(i, eventtype_code)
                break
        
        content = '\n'.join(lines)
        print("✅ history_manager.py: EventType adicionado")
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

def fix_sci_fi_hud():
    """Corrige imports no sci_fi_hud.py"""
    filepath = os.path.join('gui', 'sci_fi_hud.py')
    
    if not os.path.exists(filepath):
        print("⚠️  sci_fi_hud.py não encontrado")
        return
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verificar e corrigir imports problemáticos
    changes_made = False
    
    # Corrigir import de EventType
    if 'from core.history_manager import EventType' in content:
        print("✅ sci_fi_hud.py: Import de EventType OK")
    
    # Corrigir import de AlertLevel se estiver no lugar errado
    if 'from core.history_manager import AlertLevel' in content:
        content = content.replace(
            'from core.history_manager import AlertLevel',
            'from core.alert_system import AlertLevel'
        )
        changes_made = True
        print("✅ sci_fi_hud.py: AlertLevel corrigido para import do alert_system")
    
    # Adicionar fallback para SolarWind se necessário
    if 'from features.noaa.solar_monitor import SolarWind' in content and 'SolarWind' not in content:
        # Verificar se o arquivo existe
        solar_path = os.path.join('features', 'noaa', 'solar_monitor.py')
        if not os.path.exists(solar_path):
            os.makedirs(os.path.dirname(solar_path), exist_ok=True)
            with open(solar_path, 'w', encoding='utf-8') as f:
                f.write('''
"""
Dummy SolarWind para compatibilidade
"""

from dataclasses import dataclass

@dataclass
class SolarWind:
    speed: float = 0.0
    density: float = 0.0
    temperature: float = 0.0
    bz: float = 0.0

__all__ = ['SolarWind']
''')
            print("✅ solar_monitor.py criado (dummy)")
    
    if changes_made:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

def create_missing_files():
    """Cria arquivos faltantes essenciais"""
    
    # Criar features/noaa/__init__.py se não existir
    init_path = os.path.join('features', 'noaa', '__init__.py')
    if not os.path.exists(init_path):
        os.makedirs(os.path.dirname(init_path), exist_ok=True)
        with open(init_path, 'w', encoding='utf-8') as f:
            f.write('# NOAA features package\n')
        print("✅ features/noaa/__init__.py criado")
    
    # Criar gui/components/__init__.py se não existir
    gui_components_init = os.path.join('gui', 'components', '__init__.py')
    if not os.path.exists(gui_components_init):
        os.makedirs(os.path.dirname(gui_components_init), exist_ok=True)
        with open(gui_components_init, 'w', encoding='utf-8') as f:
            f.write('''
"""
GUI components for R2 Assistant
"""

from .network_map import NetworkMap
from .wave_animation import WaveAnimation
from .circular_gauge import CircularGauge
from .datastream import DataStream
from .alert_panel import AlertPanel
from .module_panel import ModulePanel

__all__ = [
    'NetworkMap',
    'WaveAnimation', 
    'CircularGauge',
    'DataStream',
    'AlertPanel',
    'ModulePanel'
]
''')
        print("✅ gui/components/__init__.py criado")
    
    # Criar arquivos dummy para componentes faltantes
    components = ['wave_animation.py', 'circular_gauge.py', 'datastream.py', 
                  'alert_panel.py', 'module_panel.py']
    
    for component in components:
        comp_path = os.path.join('gui', 'components', component)
        if not os.path.exists(comp_path):
            with open(comp_path, 'w', encoding='utf-8') as f:
                f.write(f'''
"""
{component.replace('_', ' ').title()} - Dummy para compatibilidade
"""

import customtkinter as ctk

class {component.split('.')[0].title().replace('_', '')}:
    """Dummy class for {component}"""
    def __init__(self, *args, **kwargs):
        pass
    
    def __getattr__(self, name):
        return lambda *args, **kwargs: None
''')
            print(f"✅ {component} criado (dummy)")

def main():
    print("🛠️  CORREÇÃO COMPLETA DO R2 ASSISTANT")
    print("=" * 60)
    
    # Adicionar diretório atual ao path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    # Executar todas as correções
    fix_network_map()
    fix_history_manager()
    fix_sci_fi_hud()
    create_missing_files()
    
    print("\n" + "=" * 60)
    print("✅ TODAS AS CORREÇÕES APLICADAS!")
    print("\nExecute agora:")
    print("  python test_imports_fixed.py")
    print("\nSe funcionar, execute:")
    print("  python run.py")

if __name__ == "__main__":
    main()