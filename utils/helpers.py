import logging
import sys
from typing import Any, Dict
import os

def setup_logging():
    """Configura o sistema de logging com suporte a Unicode."""
    # Forçar UTF-8 no Windows
    if sys.platform == "win32":
        try:
            # Tenta configurar o console para UTF-8
            os.system('chcp 65001 > nul')
        except:
            pass
    
    class UnicodeFilter(logging.Filter):
        def filter(self, record):
            if isinstance(record.msg, str):
                # Remove ou substitui caracteres Unicode problemáticos
                record.msg = record.msg.encode('ascii', 'ignore').decode('ascii')
            return True

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('r2_assistant.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Aplica filtro para remover Unicode problemático no console
    for handler in logging.getLogger().handlers:
        if hasattr(handler, 'stream') and hasattr(handler.stream, 'encoding'):
            if handler.stream.encoding != 'utf-8':
                handler.addFilter(UnicodeFilter())

def safe_execute(func, *args, **kwargs) -> Any:
    """Executa função de forma segura, capturando exceções."""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logging.error(f"Erro em {func.__name__}: {e}")
        return None