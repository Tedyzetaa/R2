#!/usr/bin/env python3
"""
Script de Instalação e Atualização NOAA para R2 Assistant
Versão: 2.1.0
Data: 2024-01-15
"""

import os
import sys
import json
import shutil
import subprocess
import platform
import importlib
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('install_noaa.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class OSPlatform(Enum):
    WINDOWS = "windows"
    LINUX = "linux"
    MACOS = "darwin"
    UNKNOWN = "unknown"

class UpdateStatus(Enum):
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    SKIPPED = "skipped"

@dataclass
class FileUpdate:
    path: str
    status: UpdateStatus
    message: str = ""
    backup_path: str = ""

@dataclass
class Dependency:
    name: str
    version: str
    required: bool = True
    installed: bool = False
    version_installed: str = ""

class NOAAInstaller:
    """Instalador e atualizador do módulo NOAA"""
    
    def __init__(self, project_root: Optional[str] = None):
        self.project_root = Path(project_root or os.getcwd())
        self.updates_dir = self.project_root / "noaa_updates"
        self.backup_dir = self.project_root / "backup_noaa"
        self.platform = self._detect_platform()
        
        # Lista de arquivos a serem atualizados
        self.update_files = [
            # Core
            ("features/noaa/noaa_service.py", "noaa_service.py"),
            ("features/noaa/solar_monitor.py", "solar_monitor.py"),
            
            # Novos arquivos
            ("commands/noaa_commands.py", "noaa_commands.py"),
            ("gui/components/noaa_panel.py", "noaa_panel.py"),
            
            # Arquivos atualizados
            ("core/config.py", "config.py"),
            ("core/command_system.py", "command_system.py"),
            ("core/function_handler.py", "function_handler.py"),
            ("core/history_manager.py", "history_manager.py"),
            ("core/alert_system.py", "alert_system.py"),
            ("gui/sci_fi_hud.py", "sci_fi_hud.py"),
            
            # Componentes
            ("gui/components/alert_panel.py", "alert_panel.py"),
            ("gui/components/module_panel.py", "module_panel.py"),
            ("gui/theme.py", "theme.py"),
            
            # Comandos
            ("commands/system_commands.py", "system_commands.py"),
            
            # Scripts
            ("install_noaa_complete.py", "install_noaa_complete.py"),
            ("test_noaa.py", "test_noaa.py"),
            ("requirements_noaa.txt", "requirements_noaa.txt")
        ]
        
        # Dependências específicas do NOAA
        self.dependencies = [
            Dependency("aiohttp", ">=3.8.0", True),
            Dependency("matplotlib", ">=3.5.0", True),
            Dependency("numpy", ">=1.21.0", True),
            Dependency("requests", ">=2.28.0", True),
            Dependency("psutil", ">=5.9.0", True),
            Dependency("scipy", ">=1.9.0", False),  # Opcional
            Dependency("astral", ">=2.2", False),   # Opcional para cálculos solares
            Dependency("timezonefinder", ">=6.0.0", False),  # Opcional
        ]
        
        self.file_updates: List[FileUpdate] = []
        
    def _detect_platform(self) -> OSPlatform:
        """Detecta o sistema operacional"""
        system = platform.system().lower()
        if 'windows' in system:
            return OSPlatform.WINDOWS
        elif 'linux' in system:
            return OSPlatform.LINUX
        elif 'darwin' in system:
            return OSPlatform.MACOS
        return OSPlatform.UNKNOWN
    
    def print_banner(self):
        """Imprime banner do instalador"""
        banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║  🌌 NOAA EXPANSION INSTALLER - R2 Assistant V2.1           ║
║                                                              ║
║  Instalação completa do módulo de clima espacial            ║
║  com monitoramento solar, alertas e interface Sci-Fi        ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""
        print(banner)
        print(f"📁 Diretório do projeto: {self.project_root}")
        print(f"💻 Sistema: {self.platform.value}")
        print(f"🐍 Python: {platform.python_version()}")
        print()
    
    def check_requirements(self) -> bool:
        """Verifica requisitos do sistema"""
        logger.info("🔍 Verificando requisitos do sistema...")
        
        checks = []
        
        # Verificar Python 3.10+
        python_version = platform.python_version_tuple()
        python_ok = int(python_version[0]) == 3 and int(python_version[1]) >= 10
        checks.append(("Python 3.10+", python_ok, f"Python {platform.python_version()}"))
        
        # Verificar diretórios
        dirs_to_check = [
            ("Diretório do projeto", self.project_root.exists()),
            ("Core", (self.project_root / "core").exists()),
            ("Features", (self.project_root / "features").exists()),
            ("GUI", (self.project_root / "gui").exists()),
            ("Commands", (self.project_root / "commands").exists()),
        ]
        
        for name, exists in dirs_to_check:
            checks.append((name, exists, "OK" if exists else "Não encontrado"))
        
        # Verificar arquivos essenciais
        essential_files = [
            ("start_r2_safe.py", self.project_root / "start_r2_safe.py"),
            ("config.json", self.project_root / "config.json"),
            ("core/config.py", self.project_root / "core" / "config.py"),
        ]
        
        for name, path in essential_files:
            checks.append((name, path.exists(), "OK" if path.exists() else "Não encontrado"))
        
        # Exibir resultados
        print("\n📋 VERIFICAÇÃO DE REQUISITOS:")
        print("-" * 60)
        
        all_ok = True
        for name, ok, status in checks:
            icon = "✅" if ok else "❌"
            print(f"{icon} {name:30} {status}")
            if not ok:
                all_ok = False
        
        print("-" * 60)
        
        if not all_ok:
            logger.warning("Alguns requisitos não foram atendidos")
            response = input("Continuar mesmo assim? (s/N): ").lower()
            return response == 's'
        
        return True
    
    def backup_existing_files(self) -> bool:
        """Cria backup dos arquivos existentes"""
        logger.info("💾 Criando backup dos arquivos existentes...")
        
        # Criar diretório de backup
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        backup_files = []
        
        for target_path, _ in self.update_files:
            full_path = self.project_root / target_path
            
            if full_path.exists():
                # Criar estrutura de diretórios no backup
                backup_path = self.backup_dir / target_path
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                
                try:
                    shutil.copy2(full_path, backup_path)
                    backup_files.append(target_path)
                    logger.debug(f"Backup: {target_path}")
                except Exception as e:
                    logger.error(f"Erro no backup de {target_path}: {e}")
                    return False
        
        logger.info(f"✅ Backup criado com {len(backup_files)} arquivos")
        return True
    
    def check_dependencies(self) -> List[Dependency]:
        """Verifica e instala dependências"""
        logger.info("📦 Verificando dependências...")
        
        for dep in self.dependencies:
            try:
                module = importlib.import_module(dep.name)
                dep.installed = True
                
                # Tentar obter versão
                if hasattr(module, '__version__'):
                    dep.version_installed = module.__version__
                elif hasattr(module, 'version'):
                    dep.version_installed = module.version
                else:
                    dep.version_installed = "Desconhecida"
                    
                logger.info(f"✅ {dep.name:20} {dep.version_installed}")
                
            except ImportError:
                dep.installed = False
                logger.warning(f"❌ {dep.name:20} Não instalado")
        
        return self.dependencies
    
    def install_dependencies(self, dependencies: List[Dependency]) -> bool:
        """Instala dependências faltantes"""
        missing_deps = [d for d in dependencies if not d.installed and d.required]
        
        if not missing_deps:
            logger.info("✅ Todas as dependências estão instaladas")
            return True
        
        print("\n📦 DEPENDÊNCIAS A INSTALAR:")
        for dep in missing_deps:
            print(f"  • {dep.name} {dep.version}")
        
        response = input("\nInstalar dependências? (S/n): ").lower()
        if response in ['n', 'no']:
            logger.warning("Instalação de dependências cancelada")
            return False
        
        # Instalar via pip
        pip_command = [sys.executable, "-m", "pip", "install"]
        
        for dep in missing_deps:
            package_spec = f"{dep.name}{dep.version}"
            logger.info(f"Instalando {package_spec}...")
            
            try:
                subprocess.run(
                    pip_command + [package_spec],
                    check=True,
                    capture_output=True,
                    text=True
                )
                logger.info(f"✅ {dep.name} instalado com sucesso")
            except subprocess.CalledProcessError as e:
                logger.error(f"❌ Erro ao instalar {dep.name}: {e.stderr}")
                return False
        
        return True
    
    def extract_updates(self) -> bool:
        """Extrai arquivos de atualização do próprio script"""
        logger.info("📂 Extraindo arquivos de atualização...")
        
        # Verificar se temos o diretório de updates
        if not self.updates_dir.exists():
            logger.error(f"Diretório de updates não encontrado: {self.updates_dir}")
            return False
        
        # Contar arquivos
        update_count = sum(1 for _ in self.updates_dir.rglob("*.py"))
        update_count += sum(1 for _ in self.updates_dir.rglob("*.txt"))
        
        logger.info(f"Encontrados {update_count} arquivos de atualização")
        return True
    
    def apply_updates(self) -> List[FileUpdate]:
        """Aplica as atualizações aos arquivos do projeto"""
        logger.info("🔄 Aplicando atualizações...")
        
        self.file_updates = []
        
        for target_path, source_file in self.update_files:
            source_path = self.updates_dir / source_file
            dest_path = self.project_root / target_path
            
            try:
                # Verificar se o arquivo de origem existe
                if not source_path.exists():
                    self.file_updates.append(FileUpdate(
                        path=target_path,
                        status=UpdateStatus.ERROR,
                        message=f"Arquivo fonte não encontrado: {source_file}"
                    ))
                    continue
                
                # Criar diretório de destino se não existir
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Copiar arquivo
                shutil.copy2(source_path, dest_path)
                
                # Verificar se o arquivo foi copiado
                if dest_path.exists():
                    status = UpdateStatus.SUCCESS
                    message = "Atualizado"
                else:
                    status = UpdateStatus.ERROR
                    message = "Falha na cópia"
                
                self.file_updates.append(FileUpdate(
                    path=target_path,
                    status=status,
                    message=message
                ))
                
                logger.info(f"{'✅' if status == UpdateStatus.SUCCESS else '❌'} {target_path}")
                
            except Exception as e:
                self.file_updates.append(FileUpdate(
                    path=target_path,
                    status=UpdateStatus.ERROR,
                    message=str(e)
                ))
                logger.error(f"Erro ao atualizar {target_path}: {e}")
        
        return self.file_updates
    
    def update_configuration(self) -> bool:
        """Atualiza arquivo de configuração"""
        logger.info("⚙️ Atualizando configuração...")
        
        config_file = self.project_root / "config.json"
        
        if not config_file.exists():
            logger.warning("Arquivo config.json não encontrado")
            return False
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Adicionar configurações NOAA
            noaa_config = {
                "ENABLE_NOAA": True,
                "ENABLE_SOLAR_MONITOR": True,
                "NOAA_UPDATE_INTERVAL": 300,
                "NOAA_ALERT_ENABLED": True,
                "NOAA_AUTO_REPORTS": True,
                "NOAA_DATA_RETENTION_DAYS": 30
            }
            
            # Mesclar configurações
            config.update(noaa_config)
            
            # Salvar backup
            backup_file = config_file.with_suffix('.json.backup')
            shutil.copy2(config_file, backup_file)
            
            # Salvar configuração atualizada
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            logger.info("✅ Configuração atualizada")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao atualizar configuração: {e}")
            return False
    
    def create_noaa_directories(self) -> bool:
        """Cria diretórios necessários para o NOAA"""
        logger.info("📁 Criando diretórios NOAA...")
        
        directories = [
            self.project_root / "data" / "noaa",
            self.project_root / "data" / "noaa" / "cache",
            self.project_root / "data" / "noaa" / "reports",
            self.project_root / "data" / "noaa" / "historical",
            self.project_root / "logs" / "noaa",
        ]
        
        try:
            for directory in directories:
                directory.mkdir(parents=True, exist_ok=True)
                logger.debug(f"Criado: {directory}")
            
            logger.info(f"✅ {len(directories)} diretórios criados")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar diretórios: {e}")
            return False
    
    def generate_report(self) -> None:
        """Gera relatório da instalação"""
        print("\n" + "="*60)
        print("📊 RELATÓRIO DA INSTALAÇÃO NOAA")
        print("="*60)
        
        # Estatísticas
        total = len(self.file_updates)
        success = sum(1 for f in self.file_updates if f.status == UpdateStatus.SUCCESS)
        errors = sum(1 for f in self.file_updates if f.status == UpdateStatus.ERROR)
        warnings = sum(1 for f in self.file_updates if f.status == UpdateStatus.WARNING)
        
        print(f"\n📈 ESTATÍSTICAS:")
        print(f"  • Total de arquivos: {total}")
        print(f"  • ✅ Sucesso: {success}")
        print(f"  • ⚠️  Avisos: {warnings}")
        print(f"  • ❌ Erros: {errors}")
        
        if errors > 0:
            print(f"\n📋 ARQUIVOS COM ERRO:")
            for update in self.file_updates:
                if update.status == UpdateStatus.ERROR:
                    print(f"  • {update.path}: {update.message}")
        
        # Diretórios criados
        noaa_dirs = [
            "data/noaa",
            "data/noaa/cache",
            "data/noaa/reports",
            "data/noaa/historical",
            "logs/noaa"
        ]
        
        print(f"\n📁 DIRETÓRIOS CRIADOS:")
        for directory in noaa_dirs:
            path = self.project_root / directory
            print(f"  • {directory}: {'✅' if path.exists() else '❌'}")
        
        # Próximos passos
        print(f"\n🚀 PRÓXIMOS PASSOS:")
        print("  1. Execute o R2 Assistant normalmente")
        print("  2. Diga 'ajuda' para ver os novos comandos NOAA")
        print("  3. Use 'clima_espacial' para obter dados")
        print("  4. Use 'noaa_status' para verificar o serviço")
        print("  5. Configure alertas em 'config.json'")
        
        print(f"\n📝 COMANDOS NOVA DISPONÍVEIS:")
        print("  • clima_espacial / space_weather")
        print("  • vento_solar / solar_wind")
        print("  • geomagnetico / aurora")
        print("  • flares_solares / solar_flares")
        print("  • alertas_noaa / noaa_alerts")
        print("  • noaa_status / noaa_service")
        
        print(f"\n📍 DIRETÓRIOS:")
        print(f"  • Backup: {self.backup_dir}")
        print(f"  • Logs: {self.project_root / 'logs' / 'noaa'}")
        print(f"  • Dados: {self.project_root / 'data' / 'noaa'}")
        
        print("\n" + "="*60)
        print("✅ INSTALAÇÃO NOAA CONCLUÍDA!")
        print("="*60)
    
    def cleanup(self) -> None:
        """Limpeza após instalação"""
        logger.info("🧹 Executando limpeza...")
        
        # Manter backup por padrão
        backup_size = sum(f.stat().st_size for f in self.backup_dir.rglob('*') if f.is_file())
        logger.info(f"Backup ocupando {backup_size / 1024:.1f} KB")
        
        response = input("\nManter arquivos de backup? (S/n): ").lower()
        if response in ['n', 'no']:
            try:
                shutil.rmtree(self.backup_dir)
                logger.info("Backup removido")
            except Exception as e:
                logger.error(f"Erro ao remover backup: {e}")
        
        # Verificar se quer manter updates
        if self.updates_dir.exists():
            response = input("Manter arquivos de atualização? (s/N): ").lower()
            if response not in ['s', 'sim']:
                try:
                    shutil.rmtree(self.updates_dir)
                    logger.info("Arquivos de atualização removidos")
                except Exception as e:
                    logger.error(f"Erro ao remover updates: {e}")
    
    def verify_installation(self) -> bool:
        """Verifica se a instalação foi bem sucedida"""
        logger.info("🔍 Verificando instalação...")
        
        checks = []
        
        # Verificar arquivos críticos
        critical_files = [
            ("noaa_service.py", self.project_root / "features" / "noaa" / "noaa_service.py"),
            ("solar_monitor.py", self.project_root / "features" / "noaa" / "solar_monitor.py"),
            ("noaa_commands.py", self.project_root / "commands" / "noaa_commands.py"),
            ("noaa_panel.py", self.project_root / "gui" / "components" / "noaa_panel.py"),
        ]
        
        for name, path in critical_files:
            exists = path.exists()
            checks.append((f"Arquivo {name}", exists))
            if not exists:
                logger.error(f"Arquivo crítico não encontrado: {path}")
        
        # Verificar importações
        test_imports = [
            ("NOAAService", "features.noaa.noaa_service"),
            ("NOAACommands", "commands.noaa_commands"),
        ]
        
        for class_name, module_name in test_imports:
            try:
                module = importlib.import_module(module_name)
                has_class = hasattr(module, class_name)
                checks.append((f"Classe {class_name}", has_class))
                if not has_class:
                    logger.error(f"Classe não encontrada: {class_name} em {module_name}")
            except ImportError as e:
                checks.append((f"Módulo {module_name}", False))
                logger.error(f"Erro ao importar {module_name}: {e}")
        
        # Exibir resultados
        print("\n🔍 VERIFICAÇÃO DA INSTALAÇÃO:")
        print("-" * 60)
        
        all_ok = True
        for name, ok in checks:
            icon = "✅" if ok else "❌"
            print(f"{icon} {name}")
            if not ok:
                all_ok = False
        
        print("-" * 60)
        
        if all_ok:
            logger.info("✅ Instalação verificada com sucesso")
        else:
            logger.warning("⚠️  Alguns problemas foram encontrados")
        
        return all_ok
    
    def run(self) -> bool:
        """Executa o processo completo de instalação"""
        
        self.print_banner()
        
        # Verificar se é sudo/admin
        if self.platform == OSPlatform.LINUX and os.geteuid() != 0:
            logger.warning("⚠️  Considerar executar com sudo para instalação global")
        
        # Passo 1: Verificar requisitos
        if not self.check_requirements():
            logger.error("Requisitos não atendidos")
            return False
        
        # Passo 2: Backup
        if not self.backup_existing_files():
            logger.error("Falha no backup")
            return False
        
        # Passo 3: Verificar dependências
        deps = self.check_dependencies()
        if not self.install_dependencies(deps):
            logger.error("Falha na instalação de dependências")
            return False
        
        # Passo 4: Extrair updates
        if not self.extract_updates():
            logger.error("Falha ao extrair atualizações")
            return False
        
        # Passo 5: Aplicar updates
        updates = self.apply_updates()
        if not any(u.status == UpdateStatus.SUCCESS for u in updates):
            logger.error("Nenhuma atualização aplicada com sucesso")
            return False
        
        # Passo 6: Atualizar configuração
        self.update_configuration()
        
        # Passo 7: Criar diretórios
        self.create_noaa_directories()
        
        # Passo 8: Verificar instalação
        self.verify_installation()
        
        # Passo 9: Gerar relatório
        self.generate_report()
        
        # Passo 10: Limpeza
        self.cleanup()
        
        return True

def main():
    """Função principal"""
    
    # Verificar argumentos
    project_root = None
    if len(sys.argv) > 1:
        project_root = sys.argv[1]
    
    # Criar instalador
    installer = NOAAInstaller(project_root)
    
    try:
        success = installer.run()
        
        if success:
            print("\n🎉 INSTALAÇÃO NOAA CONCLUÍDA COM SUCESSO!")
            print("Reinicie o R2 Assistant para carregar as novas funcionalidades.")
            
            # Perguntar se quer testar
            response = input("\nDeseja executar teste rápido? (S/n): ").lower()
            if response not in ['n', 'no']:
                test_script = installer.project_root / "test_noaa.py"
                if test_script.exists():
                    subprocess.run([sys.executable, str(test_script)])
                else:
                    print("Script de teste não encontrado")
        else:
            print("\n❌ INSTALAÇÃO FALHOU!")
            print("Consulte o arquivo install_noaa.log para detalhes.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Instalação interrompida pelo usuário")
        sys.exit(130)
    except Exception as e:
        logger.exception(f"Erro fatal durante instalação: {e}")
        print(f"\n❌ ERRO FATAL: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()