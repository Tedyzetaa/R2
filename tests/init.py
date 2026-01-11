"""
Testes do R2 Assistant
Testes unitários e de integração para o sistema
"""

__version__ = "1.0.0"

import os
import sys

# Adicionar diretório raiz ao path para imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Configurar logging para testes
import logging
logging.basicConfig(
    level=logging.WARNING,  # Reduzir verbosidade durante testes
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Desativar logging de alguns módulos
logging.getLogger('matplotlib').setLevel(logging.WARNING)
logging.getLogger('PIL').setLevel(logging.WARNING)

print(f"🔧 Ambiente de testes configurado - R2 Assistant v{__version__}")