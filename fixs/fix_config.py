#!/usr/bin/env python3
"""
Patch para corrigir problemas no config.py
"""

import os
import sys

# Adicionar diretório atual ao path
sys.path.insert(0, os.path.dirname(__file__))

def fix_config_file():
    """Corrige o arquivo config.py"""
    config_path = os.path.join('core', 'config.py')
    
    if not os.path.exists(config_path):
        print(f"Arquivo {config_path} não encontrado")
        return False
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verificar se já tem o import
        if 'from typing import' in content and 'List' in content:
            print("config.py já está correto")
            return True
        
        # Adicionar import se necessário
        if 'from typing import' in content:
            # Adicionar List ao import existente
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if 'from typing import' in line and 'List' not in line:
                    # Adicionar List ao import
                    if line.endswith(','):
                        lines[i] = line + ' List,'
                    else:
                        lines[i] = line.replace('from typing import', 'from typing import List,')
                    break
            content = '\n'.join(lines)
        else:
            # Adicionar nova linha de import
            import_line = 'from typing import List, Dict, Optional, Any\n'
            # Inserir após a primeira linha que não seja comentário
            lines = content.split('\n')
            insert_pos = 0
            for i, line in enumerate(lines):
                if line.strip() and not line.strip().startswith('#'):
                    insert_pos = i
                    break
            lines.insert(insert_pos, import_line)
            content = '\n'.join(lines)
        
        # Salvar arquivo corrigido
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Arquivo {config_path} corrigido com sucesso!")
        return True
        
    except Exception as e:
        print(f"Erro ao corrigir config.py: {e}")
        return False

def create_simple_config():
    """Cria um config.py simples se não existir"""
    config_dir = 'core'
    config_path = os.path.join(config_dir, 'config.py')
    
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
    
    simple_config = '''"""
Configuração do R2 Assistant
Versão simplificada
"""

from typing import Dict, List, Optional, Any
import os
import json
from pathlib import Path

class AppConfig:
    """Configuração da aplicação"""
    
    def __init__(self, config_file: Optional[str] = None):
        """Inicializa configuração"""
        self.config_file = config_file
        self._data = self._load_config()
        
        # Configurações padrão
        self.app = type('App', (), {
            'name': 'R2 Assistant',
            'version': '1.0.0',
            'mode': 'normal',
            'language': 'pt-BR'
        })()
        
        self.gui = type('GUI', (), {
            'theme': 'sci-fi',
            'width': 1200,
            'height': 800,
            'fullscreen': False,
            'opacity': 0.95
        })()
        
        self.logging = type('Logging', (), {
            'level': 'INFO',
            'file': 'logs/r2_assistant.log',
            'max_size': 10485760,
            'backup_count': 5
        })()
        
        self.security = type('Security', (), {
            'encryption_enabled': True,
            'require_auth': False,
            'session_timeout': 3600
        })()
        
        # Aplicar configurações do arquivo
        self._apply_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Carrega configuração do arquivo"""
        if self.config_file and os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    if self.config_file.endswith('.json'):
                        return json.load(f)
                    elif self.config_file.endswith('.yaml') or self.config_file.endswith('.yml'):
                        import yaml
                        return yaml.safe_load(f)
            except Exception as e:
                print(f"Erro ao carregar configuração: {e}")
        
        return {}
    
    def _apply_config(self):
        """Aplica configurações carregadas"""
        if not self._data:
            return
        
        # Aplicar configurações do app
        if 'app' in self._data:
            app_config = self._data['app']
            for key, value in app_config.items():
                if hasattr(self.app, key):
                    setattr(self.app, key, value)
        
        # Aplicar configurações da GUI
        if 'gui' in self._data:
            gui_config = self._data['gui']
            for key, value in gui_config.items():
                if hasattr(self.gui, key):
                    setattr(self.gui, key, value)
        
        # Aplicar configurações de logging
        if 'logging' in self._data:
            logging_config = self._data['logging']
            for key, value in logging_config.items():
                if hasattr(self.logging, key):
                    setattr(self.logging, key, value)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte configuração para dicionário"""
        return {
            'app': {k: v for k, v in vars(self.app).items() if not k.startswith('_')},
            'gui': {k: v for k, v in vars(self.gui).items() if not k.startswith('_')},
            'logging': {k: v for k, v in vars(self.logging).items() if not k.startswith('_')},
            'security': {k: v for k, v in vars(self.security).items() if not k.startswith('_')}
        }
    
    def save(self, filepath: Optional[str] = None):
        """Salva configuração em arquivo"""
        save_path = filepath or self.config_file
        if not save_path:
            print("Nenhum arquivo especificado para salvar")
            return
        
        try:
            data = self.to_dict()
            with open(save_path, 'w', encoding='utf-8') as f:
                if save_path.endswith('.json'):
                    json.dump(data, f, indent=2, ensure_ascii=False)
                elif save_path.endswith('.yaml') or save_path.endswith('.yml'):
                    import yaml
                    yaml.dump(data, f, default_flow_style=False)
            
            print(f"Configuração salva em: {save_path}")
        except Exception as e:
            print(f"Erro ao salvar configuração: {e}")

if __name__ == "__main__":
    # Teste da configuração
    config = AppConfig()
    print("Configuração padrão carregada:")
    print(json.dumps(config.to_dict(), indent=2, ensure_ascii=False))
'''
    
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(simple_config)
        print(f"Arquivo {config_path} criado com sucesso!")
        return True
    except Exception as e:
        print(f"Erro ao criar config.py: {e}")
        return False

if __name__ == "__main__":
    print("=== PATCH PARA CONFIG.PY ===")
    
    # Tentar corrigir o arquivo existente
    if os.path.exists(os.path.join('core', 'config.py')):
        if fix_config_file():
            print("Patch aplicado com sucesso!")
        else:
            print("Tentando criar um novo config.py...")
            create_simple_config()
    else:
        print("Criando novo config.py...")
        create_simple_config()
    
    print("\nAgora execute: python run.py --mode cli")