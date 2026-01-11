#!/usr/bin/env python3
"""
Setup do Ambiente R2 Assistant
Script para configurar ambiente completo do projeto
"""

import os
import sys
import json
import platform
import subprocess
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EnvironmentSetup:
    """
    Configurador de ambiente completo
    """
    
    def __init__(self, project_root: str = None):
        """
        Inicializa o configurador de ambiente
        
        Args:
            project_root: Diretório raiz do projeto
        """
        if project_root:
            self.project_root = Path(project_root)
        else:
            self.project_root = Path(__file__).parent.parent
        
        # Informações do sistema
        self.system = platform.system().lower()
        self.architecture = platform.machine().lower()
        self.python_version = platform.python_version()
        
        # Diretórios importantes
        self.dirs = {
            'logs': self.project_root / 'logs',
            'data': self.project_root / 'data',
            'cache': self.project_root / 'data' / 'cache',
            'models': self.project_root / 'data' / 'models',
            'configs': self.project_root / 'configs',
            'tests': self.project_root / 'tests',
            'backups': self.project_root / 'backups'
        }
        
        # Arquivos importantes
        self.files = {
            'config': self.project_root / 'core' / 'config.py',
            'requirements': self.project_root / 'requirements.txt',
            'modules': self.project_root / 'data' / 'modules.json',
            'env_example': self.project_root / '.env.example',
            'env': self.project_root / '.env'
        }
        
        logger.info(f"EnvironmentSetup inicializado em: {self.project_root}")
        logger.info(f"Sistema: {self.system} ({self.architecture})")
        logger.info(f"Python: {self.python_version}")
    
    def check_prerequisites(self) -> Dict[str, bool]:
        """
        Verifica pré-requisitos do sistema
        
        Returns:
            Dicionário com status dos pré-requisitos
        """
        results = {}
        
        logger.info("Verificando pré-requisitos...")
        
        # 1. Versão do Python
        python_ok = sys.version_info >= (3, 8, 0)
        results['python_version'] = python_ok
        logger.info(f"  Python 3.8+: {'✓' if python_ok else '✗'}")
        
        # 2. Pip
        try:
            import pip
            pip_ok = True
        except ImportError:
            pip_ok = False
        results['pip'] = pip_ok
        logger.info(f"  pip: {'✓' if pip_ok else '✗'}")
        
        # 3. Espaço em disco
        try:
            disk = shutil.disk_usage(self.project_root)
            disk_free_gb = disk.free / (1024**3)
            disk_ok = disk_free_gb > 1.0  # Pelo menos 1GB livre
            results['disk_space'] = disk_ok
            logger.info(f"  Espaço em disco (>1GB): {'✓' if disk_ok else '✗'} ({disk_free_gb:.1f} GB)")
        except:
            results['disk_space'] = False
            logger.warning("  Espaço em disco: ✗ (não pôde ser verificado)")
        
        # 4. Memória RAM
        try:
            import psutil
            memory = psutil.virtual_memory()
            memory_gb = memory.total / (1024**3)
            memory_ok = memory_gb >= 2.0  # Pelo menos 2GB RAM
            results['memory'] = memory_ok
            logger.info(f"  Memória RAM (≥2GB): {'✓' if memory_ok else '✗'} ({memory_gb:.1f} GB)")
        except ImportError:
            results['memory'] = None
            logger.info("  Memória RAM: ? (psutil não instalado)")
        
        # 5. Conectividade de rede
        try:
            import socket
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            results['network'] = True
            logger.info("  Conectividade de rede: ✓")
        except:
            results['network'] = False
            logger.warning("  Conectividade de rede: ✗")
        
        # 6. Permissões de escrita
        test_file = self.project_root / '.write_test'
        try:
            test_file.write_text('test')
            test_file.unlink()
            results['write_permission'] = True
            logger.info("  Permissões de escrita: ✓")
        except:
            results['write_permission'] = False
            logger.error("  Permissões de escrita: ✗")
        
        # 7. GPU (opcional)
        try:
            import torch
            has_gpu = torch.cuda.is_available()
            results['gpu'] = has_gpu
            
            if has_gpu:
                gpu_name = torch.cuda.get_device_name(0)
                gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
                logger.info(f"  GPU: ✓ {gpu_name} ({gpu_memory:.1f} GB)")
            else:
                logger.info("  GPU: ✗ (CPU only)")
        except ImportError:
            results['gpu'] = None
            logger.info("  GPU: ? (PyTorch não instalado)")
        
        return results
    
    def create_directory_structure(self) -> Dict[str, bool]:
        """
        Cria estrutura de diretórios do projeto
        
        Returns:
            Dicionário com status de criação
        """
        results = {}
        
        logger.info("Criando estrutura de diretórios...")
        
        for name, path in self.dirs.items():
            try:
                path.mkdir(parents=True, exist_ok=True)
                
                # Criar .gitkeep em diretórios vazios
                gitkeep = path / '.gitkeep'
                if not any(path.iterdir()):
                    gitkeep.touch()
                
                results[name] = True
                logger.info(f"  ✓ {name}: {path}")
                
            except Exception as e:
                results[name] = False
                logger.error(f"  ✗ {name}: {e}")
        
        return results
    
    def setup_config_files(self) -> Dict[str, bool]:
        """
        Configura arquivos de configuração
        
        Returns:
            Dicionário com status de configuração
        """
        results = {}
        
        logger.info("Configurando arquivos de configuração...")
        
        # 1. .env file (from .env.example)
        if self.files['env_example'].exists() and not self.files['env'].exists():
            try:
                shutil.copy(self.files['env_example'], self.files['env'])
                results['env'] = True
                logger.info(f"  ✓ .env criado de {self.files['env_example'].name}")
            except Exception as e:
                results['env'] = False
                logger.error(f"  ✗ .env: {e}")
        else:
            results['env'] = self.files['env'].exists()
            logger.info(f"  {'✓' if results['env'] else '✗'} .env")
        
        # 2. modules.json
        modules_file = self.dirs['data'] / 'modules.json'
        if not modules_file.exists():
            try:
                # Criar modules.json básico
                basic_modules = {
                    "version": "1.0.0",
                    "modules": {
                        "core": {
                            "name": "Core System",
                            "enabled": True,
                            "required": True
                        }
                    }
                }
                
                with open(modules_file, 'w', encoding='utf-8') as f:
                    json.dump(basic_modules, f, indent=2, ensure_ascii=False)
                
                results['modules'] = True
                logger.info(f"  ✓ {modules_file.name} criado")
                
            except Exception as e:
                results['modules'] = False
                logger.error(f"  ✗ {modules_file.name}: {e}")
        else:
            results['modules'] = True
            logger.info(f"  ✓ {modules_file.name}")
        
        # 3. cache index
        cache_index = self.dirs['cache'] / 'cache_index.json'
        if not cache_index.exists():
            try:
                basic_index = {
                    "version": "1.0.0",
                    "entries": {}
                }
                
                with open(cache_index, 'w', encoding='utf-8') as f:
                    json.dump(basic_index, f, indent=2, ensure_ascii=False)
                
                results['cache_index'] = True
                logger.info(f"  ✓ {cache_index.name} criado")
                
            except Exception as e:
                results['cache_index'] = False
                logger.error(f"  ✗ {cache_index.name}: {e}")
        else:
            results['cache_index'] = True
            logger.info(f"  ✓ {cache_index.name}")
        
        return results
    
    def setup_logging_system(self) -> bool:
        """
        Configura sistema de logging
        
        Returns:
            True se configuração foi bem sucedida
        """
        logger.info("Configurando sistema de logging...")
        
        try:
            logs_dir = self.dirs['logs']
            
            # Criar arquivos de log padrão
            log_files = [
                'r2_assistant.log',
                'errors.log',
                'alerts.log',
                'commands.log'
            ]
            
            for log_file in log_files:
                log_path = logs_dir / log_file
                if not log_path.exists():
                    log_path.touch()
            
            # Criar configuração de logging básica
            log_config = {
                "version": 1,
                "disable_existing_loggers": False,
                "formatters": {
                    "detailed": {
                        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                    },
                    "simple": {
                        "format": "%(levelname)s - %(message)s"
                    }
                },
                "handlers": {
                    "console": {
                        "class": "logging.StreamHandler",
                        "level": "INFO",
                        "formatter": "simple",
                        "stream": "ext://sys.stdout"
                    },
                    "file": {
                        "class": "logging.handlers.RotatingFileHandler",
                        "level": "DEBUG",
                        "formatter": "detailed",
                        "filename": str(logs_dir / "r2_assistant.log"),
                        "maxBytes": 10485760,  # 10MB
                        "backupCount": 5
                    },
                    "errors": {
                        "class": "logging.handlers.RotatingFileHandler",
                        "level": "ERROR",
                        "formatter": "detailed",
                        "filename": str(logs_dir / "errors.log"),
                        "maxBytes": 5242880,  # 5MB
                        "backupCount": 3
                    }
                },
                "loggers": {
                    "": {  # Root logger
                        "level": "INFO",
                        "handlers": ["console", "file", "errors"]
                    },
                    "r2": {
                        "level": "DEBUG",
                        "handlers": ["console", "file"],
                        "propagate": False
                    }
                }
            }
            
            # Salvar configuração
            log_config_file = self.dirs['configs'] / 'logging_config.json'
            with open(log_config_file, 'w', encoding='utf-8') as f:
                json.dump(log_config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"  ✓ Sistema de logging configurado em {logs_dir}")
            return True
            
        except Exception as e:
            logger.error(f"  ✗ Erro ao configurar logging: {e}")
            return False
    
    def setup_backup_system(self) -> bool:
        """
        Configura sistema de backup
        
        Returns:
            True se configuração foi bem sucedida
        """
        logger.info("Configurando sistema de backup...")
        
        try:
            backup_dir = self.dirs['backups']
            
            # Criar subdiretórios de backup
            backup_categories = [
                'configs',
                'models',
                'data',
                'logs'
            ]
            
            for category in backup_categories:
                (backup_dir / category).mkdir(parents=True, exist_ok=True)
            
            # Criar script de backup automático
            backup_script = backup_dir / 'auto_backup.py'
            if not backup_script.exists():
                script_content = '''#!/usr/bin/env python3
"""
Script de backup automático do R2 Assistant
"""

import os
import sys
import shutil
import json
from datetime import datetime
from pathlib import Path

def create_backup():
    """Cria backup dos dados importantes"""
    project_root = Path(__file__).parent.parent
    backup_dir = project_root / "backups"
    
    # Timestamp para nome do backup
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Itens para backup
    items_to_backup = [
        ("configs", project_root / "configs"),
        ("data", project_root / "data"),
        ("logs", project_root / "logs")
    ]
    
    backup_info = {
        "timestamp": timestamp,
        "items": [],
        "total_size": 0
    }
    
    for name, source in items_to_backup:
        if source.exists():
            dest = backup_dir / name / f"backup_{timestamp}"
            dest.mkdir(parents=True, exist_ok=True)
            
            # Copiar recursivamente
            if source.is_dir():
                shutil.copytree(source, dest / source.name, dirs_exist_ok=True)
                size = sum(f.stat().st_size for f in source.rglob('*') if f.is_file())
            else:
                shutil.copy2(source, dest)
                size = source.stat().st_size
            
            backup_info["items"].append({
                "name": name,
                "source": str(source),
                "destination": str(dest),
                "size": size
            })
            backup_info["total_size"] += size
    
    # Salvar informações do backup
    info_file = backup_dir / f"backup_{timestamp}.json"
    with open(info_file, 'w', encoding='utf-8') as f:
        json.dump(backup_info, f, indent=2, ensure_ascii=False)
    
    print(f"Backup criado: {timestamp}")
    print(f"Total: {backup_info['total_size'] / (1024**2):.1f} MB")
    
    # Limpar backups antigos (mantém últimos 7)
    cleanup_old_backups(backup_dir)
    
    return True

def cleanup_old_backups(backup_dir, keep_last=7):
    """Remove backups antigos"""
    backup_files = []
    
    for item in backup_dir.rglob("backup_*.json"):
        try:
            timestamp = item.stem.replace("backup_", "")
            dt = datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
            backup_files.append((dt, item))
        except:
            continue
    
    # Ordenar por data (mais antigo primeiro)
    backup_files.sort(key=lambda x: x[0])
    
    # Remover backups antigos
    for dt, filepath in backup_files[:-keep_last]:
        print(f"Removendo backup antigo: {dt.strftime('%Y-%m-%d %H:%M')}")
        
        # Remover arquivo de informações
        filepath.unlink()
        
        # Remover diretórios de backup correspondentes
        for category in ["configs", "data", "logs", "models"]:
            backup_path = backup_dir / category / f"backup_{dt.strftime('%Y%m%d_%H%M%S')}"
            if backup_path.exists():
                shutil.rmtree(backup_path)

if __name__ == "__main__":
    create_backup()
'''
                with open(backup_script, 'w', encoding='utf-8') as f:
                    f.write(script_content)
                
                # Tornar executável (Unix)
                if self.system != 'windows':
                    os.chmod(backup_script, 0o755)
            
            logger.info("  ✓ Sistema de backup configurado")
            return True
            
        except Exception as e:
            logger.error(f"  ✗ Erro ao configurar backup: {e}")
            return False
    
    def setup_test_environment(self) -> bool:
        """
        Configura ambiente de testes
        
        Returns:
            True se configuração foi bem sucedida
        """
        logger.info("Configurando ambiente de testes...")
        
        try:
            tests_dir = self.dirs['tests']
            
            # Criar arquivos de teste básicos se não existirem
            test_files = {
                '__init__.py': '''"""
Testes do R2 Assistant
"""

__version__ = "1.0.0"
''',
                'conftest.py': '''"""
Configuração do pytest para R2 Assistant
"""

import pytest
import sys
import os

# Adicionar diretório raiz ao path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

@pytest.fixture
def sample_config():
    """Fixture para configuração de teste"""
    return {
        "app": {
            "name": "R2 Test",
            "version": "1.0.0"
        }
    }

@pytest.fixture
def temp_dir(tmp_path):
    """Fixture para diretório temporário"""
    return tmp_path
'''
            }
            
            for filename, content in test_files.items():
                filepath = tests_dir / filename
                if not filepath.exists():
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
            
            logger.info("  ✓ Ambiente de testes configurado")
            return True
            
        except Exception as e:
            logger.error(f"  ✗ Erro ao configurar testes: {e}")
            return False
    
    def setup_security(self) -> bool:
        """
        Configura medidas de segurança básicas
        
        Returns:
            True se configuração foi bem sucedida
        """
        logger.info("Configurando medidas de segurança...")
        
        try:
            # 1. Criar arquivo .gitignore se não existir
            gitignore = self.project_root / '.gitignore'
            if not gitignore.exists():
                gitignore_content = '''# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
env/
ENV/
env.bak/
venv.bak/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Project Specific
*.log
logs/
data/cache/*
!data/cache/.gitkeep
data/models/cache/*
backups/*
!.gitkeep
.env
*.key
*.pem
secrets/
configs/local_*.json

# Temporary files
*.tmp
*.temp
'''
                with open(gitignore, 'w', encoding='utf-8') as f:
                    f.write(gitignore_content)
            
            # 2. Verificar permissões de arquivos sensíveis
            sensitive_files = [
                self.files['env'],
                self.project_root / '.env.local',
                self.project_root / 'secrets.json'
            ]
            
            for filepath in sensitive_files:
                if filepath.exists():
                    # Em Unix, verificar permissões
                    if self.system != 'windows':
                        stat = os.stat(filepath)
                        if stat.st_mode & 0o077:  # Verificar se outros têm acesso
                            logger.warning(f"  ⚠  {filepath.name} tem permissões muito abertas")
            
            # 3. Criar arquivo de segurança básico
            security_file = self.dirs['configs'] / 'security_notes.md'
            if not security_file.exists():
                security_content = '''# Notas de Segurança - R2 Assistant

## Arquivos Sensíveis

Os seguintes arquivos contêm informações sensíveis e NÃO devem ser commitados:

1. `.env` - Variáveis de ambiente e chaves de API
2. `*.key`, `*.pem` - Chaves privadas
3. `secrets.json` - Outras credenciais

## Boas Práticas

### 1. Gerenciamento de Chaves
- Use variáveis de ambiente para chaves de API
- Nunca comite chaves no código
- Rotacione chaves regularmente

### 2. Permissões de Arquivos
- Arquivos de configuração: 600 (rw-------)
- Scripts executáveis: 755 (rwxr-xr-x)
- Diretórios de dados: 700 (rwx------)

### 3. Logging
- Não logue dados sensíveis
- Use diferentes níveis de logging
- Rotate logs regularmente

### 4. Rede
- Use HTTPS para todas as conexões externas
- Valide certificados SSL
- Limite portas abertas

### 5. Dados
- Criptografe dados sensíveis em repouso
- Valide todas as entradas do usuário
- Use prepared statements para SQL

## Em Caso de Violação

1. **Imediatamente**:
   - Rotacione todas as chaves
   - Revogue tokens comprometidos
   - Verifique logs para atividade suspeita

2. **Investigar**:
   - Como ocorreu a violação?
   - Quais dados foram expostos?
   - Há backdoors instalados?

3. **Corrigir**:
   - Aplique patches de segurança
   - Atualize dependências
   - Melhore medidas de segurança

## Contato

Em caso de questões de segurança, entre em contato com a equipe de desenvolvimento.

**NÃO reporte vulnerabilidades em issues públicas!**
'''
                with open(security_file, 'w', encoding='utf-8') as f:
                    f.write(security_content)
            
            logger.info("  ✓ Medidas de segurança configuradas")
            return True
            
        except Exception as e:
            logger.error(f"  ✗ Erro ao configurar segurança: {e}")
            return False
    
    def generate_setup_report(self, results: Dict[str, Dict]) -> str:
        """
        Gera relatório do setup
        
        Args:
            results: Resultados das etapas do setup
            
        Returns:
            Relatório formatado
        """
        report = []
        report.append("=" * 60)
        report.append("RELATÓRIO DE SETUP - R2 ASSISTANT")
        report.append("=" * 60)
        report.append(f"Data: {platform.node()}")
        report.append(f"Sistema: {self.system} ({self.architecture})")
        report.append(f"Python: {self.python_version}")
        report.append("")
        
        # Resumo por categoria
        categories = {
            "Pré-requisitos": results.get('prerequisites', {}),
            "Diretórios": results.get('directories', {}),
            "Configurações": results.get('configs', {}),
            "Sistemas": results.get('systems', {})
        }
        
        for category_name, category_results in categories.items():
            report.append(f"{category_name}:")
            
            if not category_results:
                report.append("  Nenhum resultado")
                continue
            
            for item, status in category_results.items():
                if status is True:
                    report.append(f"  ✓ {item}")
                elif status is False:
                    report.append(f"  ✗ {item}")
                elif status is None:
                    report.append(f"  ? {item} (opcional)")
                else:
                    report.append(f"  - {item}: {status}")
            
            report.append("")
        
        # Recomendações
        report.append("Recomendações:")
        
        prerequisites = results.get('prerequisites', {})
        if not prerequisites.get('pip', True):
            report.append("  • Instale/atualize o pip")
        
        if not prerequisites.get('disk_space', True):
            report.append("  • Libere espaço em disco (mínimo 1GB)")
        
        if prerequisites.get('gpu') is None:
            report.append("  • Considere instalar PyTorch para aceleração GPU")
        
        report.append("")
        report.append("Próximos passos:")
        report.append("  1. Configure as variáveis de ambiente em .env")
        report.append("  2. Instale dependências: pip install -r requirements.txt")
        report.append("  3. Execute os testes: python -m pytest tests/")
        report.append("  4. Inicie o sistema: python main.py")
        report.append("")
        report.append("=" * 60)
        
        return "\n".join(report)
    
    def run(self, interactive: bool = False) -> bool:
        """
        Executa o setup completo
        
        Args:
            interactive: Se deve executar em modo interativo
            
        Returns:
            True se setup foi bem sucedido
        """
        logger.info("=" * 60)
        logger.info("INICIANDO SETUP DO R2 ASSISTANT")
        logger.info("=" * 60)
        
        results = {}
        
        try:
            # 1. Verificar pré-requisitos
            logger.info("\n[1/6] Verificando pré-requisitos...")
            prerequisites = self.check_prerequisites()
            results['prerequisites'] = prerequisites
            
            # Verificar se há falhas críticas
            critical_failures = [
                k for k, v in prerequisites.items()
                if v is False and k in ['python_version', 'pip', 'write_permission']
            ]
            
            if critical_failures:
                logger.error("Falhas críticas detectadas. Setup abortado.")
                for failure in critical_failures:
                    logger.error(f"  - {failure}")
                return False
            
            # 2. Criar estrutura de diretórios
            logger.info("\n[2/6] Criando estrutura de diretórios...")
            directories = self.create_directory_structure()
            results['directories'] = directories
            
            # 3. Configurar arquivos
            logger.info("\n[3/6] Configurando arquivos...")
            configs = self.setup_config_files()
            
            # 4. Configurar sistemas
            logger.info("\n[4/6] Configurando sistemas...")
            systems = {
                'logging': self.setup_logging_system(),
                'backup': self.setup_backup_system(),
                'testing': self.setup_test_environment(),
                'security': self.setup_security()
            }
            results['systems'] = systems
            
            # 5. Configurações combinadas
            results['configs'] = configs
            
            # 6. Gerar relatório
            logger.info("\n[6/6] Gerando relatório...")
            report = self.generate_setup_report(results)
            
            # Salvar relatório
            report_file = self.dirs['logs'] / 'setup_report.txt'
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)
            
            # Mostrar relatório
            print("\n" + report)
            
            logger.info(f"Relatório salvo em: {report_file}")
            logger.info("=" * 60)
            logger.info("SETUP CONCLUÍDO COM SUCESSO!")
            logger.info("=" * 60)
            
            return True
            
        except KeyboardInterrupt:
            logger.info("\nSetup interrompido pelo usuário.")
            return False
        except Exception as e:
            logger.error(f"\nErro durante o setup: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return False

def main():
    """Função principal"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Setup do ambiente R2 Assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  %(prog)s                    # Executa setup completo
  %(prog)s --check-only       # Apenas verifica pré-requisitos
  %(prog)s --project-dir /caminho/do/projeto  # Diretório personalizado
        """
    )
    
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Apenas verifica pré-requisitos, não configura"
    )
    
    parser.add_argument(
        "--project-dir",
        help="Diretório do projeto (padrão: diretório atual)"
    )
    
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Modo interativo"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Modo verboso"
    )
    
    args = parser.parse_args()
    
    # Configurar nível de logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Criar configurador
    setup = EnvironmentSetup(args.project_dir)
    
    if args.check_only:
        # Apenas verificar pré-requisitos
        print("\nVerificando pré-requisitos do R2 Assistant...\n")
        results = setup.check_prerequisites()
        
        for item, status in results.items():
            if status is True:
                print(f"✓ {item}")
            elif status is False:
                print(f"✗ {item}")
            elif status is None:
                print(f"? {item} (opcional)")
            else:
                print(f"- {item}: {status}")
        
        print(f"\n{'='*40}")
        
        # Contar sucessos/falhas
        total = len(results)
        passed = sum(1 for v in results.values() if v is True)
        failed = sum(1 for v in results.values() if v is False)
        
        print(f"Total: {total} | ✓: {passed} | ✗: {failed} | ?: {total - passed - failed}")
        
        if failed == 0:
            print("✓ Todos os pré-requisitos atendidos!")
            sys.exit(0)
        else:
            print("✗ Alguns pré-requisitos não foram atendidos.")
            sys.exit(1)
    else:
        # Executar setup completo
        success = setup.run(interactive=args.interactive)
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()