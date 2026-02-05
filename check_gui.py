"""
Verifica se todos os módulos para GUI completa estão disponíveis
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("🔍 Verificando requisitos para GUI Sci-Fi HUD...")
print("=" * 60)

required_modules = [
    ('customtkinter', '5.2.0+', 'Interface gráfica'),
    ('PIL', '10.0.0+', 'Processamento de imagens'),
    ('core.config', '', 'Configuração do sistema'),
    ('core.history_manager', '', 'Histórico'),
    ('gui.theme', '', 'Tema Sci-Fi'),
    ('gui.sci_fi_hud', '', 'Interface principal'),
]

optional_modules = [
    ('requests', '', 'APIs web'),
    ('psutil', '', 'Monitoramento do sistema'),
    ('pyyaml', '', 'Configuração YAML'),
    ('python-dotenv', '', 'Variáveis de ambiente'),
    ('pygame', '', 'Áudio e sons'),
    ('core.alert_system', '', 'Sistema de alertas'),
    ('core.analytics', '', 'Analytics'),
    ('core.voice_engine', '', 'Sistema de voz'),
]

print("\n📋 MÓDULOS OBRIGATÓRIOS:")
all_required = True
for module, version, desc in required_modules:
    try:
        __import__(module.replace('.', '_') if '.' in module else module)
        print(f"✅ {module:20} - {desc}")
    except ImportError:
        print(f"❌ {module:20} - {desc} (FALTANDO)")
        all_required = False

print("\n📦 MÓDULOS OPCIONAIS:")
for module, version, desc in optional_modules:
    try:
        __import__(module.replace('.', '_') if '.' in module else module)
        print(f"✅ {module:20} - {desc}")
    except ImportError:
        print(f"⚠️  {module:20} - {desc} (não instalado)")

print("\n" + "=" * 60)
if all_required:
    print("🎉 TODOS os módulos obrigatórios estão disponíveis!")
    print("\nExecute: python run.py")
    print("Selecione opção 1 para GUI completa")
else:
    print("📝 Alguns módulos obrigatórios estão faltando.")
    print("\nInstale com:")
    print("  pip install customtkinter pillow")
    print("\nOu execute a GUI básica:")
    print("  python run.py (selecione opção 2)")