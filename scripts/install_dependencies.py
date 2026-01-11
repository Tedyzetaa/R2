#!/usr/bin/env python3
"""
Instalador de Dependências do R2 Assistant
Script para instalar/atualizar todas as dependências do projeto
"""

import os
import sys
import subprocess
import platform
import json
from pathlib import Path
import logging
from typing import List, Dict, Any, Optional

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DependencyInstaller:
    """
    Gerenciador de instalação de dependências
    """
    
    def __init__(self, requirements_file: str = "requirements.txt"):
        """
        Inicializa o instalador
        
        Args:
            requirements_file: Caminho do arquivo requirements.txt
        """
        self.project_root = Path(__file__).parent.parent
        self.requirements_file = self.project_root / requirements_file
        
        # Mapeamento de sistema operacional
        self.system = platform.system().lower()
        self.architecture = platform.machine().lower()
        
        # Dependências específicas por plataforma
        self.platform_specific = {
            'windows': {
                'required': ['pywin32', 'comtypes'],
                'optional': ['windows-curses']
            },
            'linux': {
                'required': ['python3-dev', 'build-essential'],
                'optional': ['python3-tk']
            },
            'darwin': {
                'required': [],
                'optional': ['pyobjc']
            }
        }
        
        logger.info(f"Sistema detectado: {self.system} ({self.architecture})")
    
    def check_python_version(self) -> bool:
        """
        Verifica versão do Python
        
        Returns:
            True se versão é compatível
        """
        import sys
        
        required_version = (3, 8, 0)
        current_version = sys.version_info
        
        if current_version < required_version:
            logger.error(f"Python {required_version[0]}.{required_version[1]}+ necessário. "
                        f"Versão atual: {current_version[0]}.{current_version[1]}.{current_version[2]}")
            return False
        
        logger.info(f"Python {current_version[0]}.{current_version[1]}.{current_version[2]} - OK")
        return True
    
    def check_pip_version(self) -> bool:
        """
        Verifica e atualiza pip se necessário
        
        Returns:
            True se pip está atualizado
        """
        try:
            import pip
            pip_version = pip.__version__
            logger.info(f"pip versão: {pip_version}")
            
            # Tentar atualizar pip
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
            return True
            
        except subprocess.CalledProcessError as e:
            logger.warning(f"Falha ao atualizar pip: {e}")
            return False
        except Exception as e:
            logger.error(f"Erro ao verificar pip: {e}")
            return False
    
    def install_from_requirements(self, upgrade: bool = False) -> bool:
        """
        Instala dependências do requirements.txt
        
        Args:
            upgrade: Se deve fazer upgrade das dependências
            
        Returns:
            True se instalação foi bem sucedida
        """
        if not self.requirements_file.exists():
            logger.error(f"Arquivo não encontrado: {self.requirements_file}")
            return False
        
        try:
            cmd = [sys.executable, "-m", "pip", "install"]
            
            if upgrade:
                cmd.append("--upgrade")
            
            cmd.extend(["-r", str(self.requirements_file)])
            
            logger.info(f"Instalando dependências de {self.requirements_file}")
            subprocess.check_call(cmd)
            
            logger.info("Dependências instaladas com sucesso")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Falha ao instalar dependências: {e}")
            return False
        except Exception as e:
            logger.error(f"Erro inesperado: {e}")
            return False
    
    def install_platform_dependencies(self) -> bool:
        """
        Instala dependências específicas da plataforma
        
        Returns:
            True se instalação foi bem sucedida
        """
        platform_deps = self.platform_specific.get(self.system, {})
        
        if not platform_deps:
            logger.info(f"Nenhuma dependência específica para {self.system}")
            return True
        
        try:
            # Instalar dependências requeridas
            if platform_deps.get('required'):
                logger.info(f"Instalando dependências específicas para {self.system}")
                
                for dep in platform_deps['required']:
                    try:
                        subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
                        logger.info(f"  ✓ {dep}")
                    except subprocess.CalledProcessError:
                        logger.warning(f"  ✗ Falha ao instalar {dep}")
            
            # Instalar dependências opcionais
            if platform_deps.get('optional'):
                logger.info("Instalando dependências opcionais...")
                
                for dep in platform_deps['optional']:
                    try:
                        subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
                        logger.info(f"  ✓ {dep} (opcional)")
                    except subprocess.CalledProcessError:
                        logger.debug(f"  ✗ {dep} não instalado (opcional)")
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao instalar dependências da plataforma: {e}")
            return False
    
    def install_development_dependencies(self) -> bool:
        """
        Instala dependências de desenvolvimento
        
        Returns:
            True se instalação foi bem sucedida
        """
        dev_deps = [
            'pytest',
            'pytest-asyncio',
            'pytest-cov',
            'black',
            'flake8',
            'mypy',
            'pre-commit',
            'twine',
            'wheel',
            'setuptools'
        ]
        
        try:
            logger.info("Instalando dependências de desenvolvimento...")
            
            for dep in dev_deps:
                try:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
                    logger.info(f"  ✓ {dep}")
                except subprocess.CalledProcessError:
                    logger.warning(f"  ✗ Falha ao instalar {dep}")
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao instalar dependências de desenvolvimento: {e}")
            return False
    
    def check_installed_dependencies(self) -> Dict[str, Any]:
        """
        Verifica dependências instaladas
        
        Returns:
            Dicionário com status das dependências
        """
        import importlib
        import pkg_resources
        
        # Ler requirements
        if not self.requirements_file.exists():
            return {"error": "Requirements file not found"}
        
        with open(self.requirements_file, 'r') as f:
            requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        results = {
            "total": len(requirements),
            "installed": 0,
            "missing": [],
            "details": {}
        }
        
        for req in requirements:
            try:
                # Parse requirement
                if '==' in req:
                    pkg_name, expected_version = req.split('==')
                elif '>=' in req:
                    pkg_name, expected_version = req.split('>=')
                else:
                    pkg_name = req
                    expected_version = None
                
                pkg_name = pkg_name.strip()
                
                # Tentar importar
                try:
                    module = importlib.import_module(pkg_name.replace('-', '_'))
                    
                    # Verificar versão se especificada
                    if expected_version:
                        installed_version = getattr(module, '__version__', 'unknown')
                        
                        if installed_version != 'unknown':
                            results["details"][pkg_name] = {
                                "status": "installed",
                                "expected": expected_version,
                                "installed": installed_version,
                                "match": installed_version == expected_version
                            }
                            
                            if installed_version == expected_version:
                                results["installed"] += 1
                            else:
                                results["missing"].append(f"{pkg_name} (versão {installed_version} != {expected_version})")
                        else:
                            results["details"][pkg_name] = {
                                "status": "installed",
                                "expected": expected_version,
                                "installed": "unknown"
                            }
                            results["installed"] += 1
                    else:
                        results["details"][pkg_name] = {"status": "installed"}
                        results["installed"] += 1
                        
                except ImportError:
                    results["details"][pkg_name] = {"status": "missing"}
                    results["missing"].append(pkg_name)
                    
            except Exception as e:
                results["details"][req] = {"status": "error", "error": str(e)}
                results["missing"].append(f"{req} (erro: {str(e)})")
        
        return results
    
    def create_virtual_environment(self, venv_path: str = "venv") -> bool:
        """
        Cria ambiente virtual Python
        
        Args:
            venv_path: Caminho do ambiente virtual
            
        Returns:
            True se ambiente foi criado com sucesso
        """
        try:
            import venv
            
            logger.info(f"Criando ambiente virtual em {venv_path}...")
            
            # Criar ambiente virtual
            builder = venv.EnvBuilder(
                with_pip=True,
                clear=False,
                symlinks=True,
                upgrade=False
            )
            
            builder.create(venv_path)
            
            # Determinar caminho do Python no venv
            if self.system == "windows":
                python_path = Path(venv_path) / "Scripts" / "python.exe"
            else:
                python_path = Path(venv_path) / "bin" / "python"
            
            logger.info(f"Ambiente virtual criado. Python em: {python_path}")
            logger.info(f"Para ativar: source {venv_path}/bin/activate (Linux/Mac)")
            logger.info(f"Para ativar: {venv_path}\\Scripts\\activate (Windows)")
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao criar ambiente virtual: {e}")
            return False
    
    def install_system_packages(self) -> bool:
        """
        Instala pacotes do sistema necessários (Linux apenas)
        
        Returns:
            True se instalação foi bem sucedida
        """
        if self.system != "linux":
            logger.info("Instalação de pacotes do sistema apenas para Linux")
            return True
        
        try:
            # Detectar distribuição
            distro = self._detect_linux_distro()
            
            # Pacotes por distribuição
            packages_by_distro = {
                "ubuntu": ["python3-tk", "python3-dev", "build-essential", "libssl-dev", "libffi-dev"],
                "debian": ["python3-tk", "python3-dev", "build-essential", "libssl-dev", "libffi-dev"],
                "fedora": ["python3-tkinter", "python3-devel", "gcc", "openssl-devel"],
                "centos": ["tkinter", "python3-devel", "gcc", "openssl-devel"],
                "arch": ["tk", "python", "base-devel", "openssl"]
            }
            
            packages = packages_by_distro.get(distro, [])
            
            if not packages:
                logger.warning(f"Distribuição {distro} não reconhecida")
                return True
            
            logger.info(f"Instalando pacotes do sistema para {distro}...")
            
            # Comando de instalação por distribuição
            install_commands = {
                "ubuntu": ["sudo", "apt-get", "update", "&&", "sudo", "apt-get", "install", "-y"],
                "debian": ["sudo", "apt-get", "update", "&&", "sudo", "apt-get", "install", "-y"],
                "fedora": ["sudo", "dnf", "install", "-y"],
                "centos": ["sudo", "yum", "install", "-y"],
                "arch": ["sudo", "pacman", "-S", "--noconfirm"]
            }
            
            cmd = install_commands.get(distro)
            
            if cmd and len(packages) > 0:
                # Remover '&&' para subprocess
                if "&&" in cmd:
                    # Para comandos com &&, executar separadamente
                    parts = " ".join(cmd).split(" && ")
                    for part in parts:
                        subprocess.run(part.split(), check=True)
                else:
                    cmd.extend(packages)
                    subprocess.run(cmd, check=True)
                
                logger.info("Pacotes do sistema instalados com sucesso")
                return True
            else:
                logger.warning(f"Não foi possível determinar comando de instalação para {distro}")
                return True
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Falha ao instalar pacotes do sistema: {e}")
            return False
        except Exception as e:
            logger.error(f"Erro ao instalar pacotes do sistema: {e}")
            return False
    
    def _detect_linux_distro(self) -> str:
        """Detecta distribuição Linux"""
        try:
            import distro
            return distro.id().lower()
        except ImportError:
            # Fallback para /etc/os-release
            try:
                with open('/etc/os-release', 'r') as f:
                    for line in f:
                        if line.startswith('ID='):
                            return line.split('=')[1].strip().strip('"').lower()
            except:
                pass
        
        return "unknown"
    
    def run(self, options: Dict[str, bool] = None) -> bool:
        """
        Executa o processo completo de instalação
        
        Args:
            options: Opções de instalação
            
        Returns:
            True se todas as etapas foram bem sucedidas
        """
        options = options or {
            "check_python": True,
            "update_pip": True,
            "install_requirements": True,
            "install_platform": True,
            "install_dev": False,
            "create_venv": False,
            "install_system": True,
            "check_after": True
        }
        
        logger.info("=" * 60)
        logger.info("R2 ASSISTANT - INSTALADOR DE DEPENDÊNCIAS")
        logger.info("=" * 60)
        
        success = True
        
        # 1. Verificar Python
        if options.get("check_python"):
            logger.info("\n[1/7] Verificando versão do Python...")
            if not self.check_python_version():
                success = False
        
        # 2. Atualizar pip
        if options.get("update_pip") and success:
            logger.info("\n[2/7] Verificando pip...")
            self.check_pip_version()
        
        # 3. Criar ambiente virtual (opcional)
        if options.get("create_venv") and success:
            logger.info("\n[3/7] Criando ambiente virtual...")
            if not self.create_virtual_environment():
                logger.warning("Falha ao criar ambiente virtual")
        
        # 4. Instalar pacotes do sistema (Linux)
        if options.get("install_system") and success:
            logger.info("\n[4/7] Instalando pacotes do sistema...")
            self.install_system_packages()
        
        # 5. Instalar requirements
        if options.get("install_requirements") and success:
            logger.info("\n[5/7] Instalando dependências do projeto...")
            if not self.install_from_requirements():
                success = False
        
        # 6. Instalar dependências da plataforma
        if options.get("install_platform") and success:
            logger.info("\n[6/7] Instalando dependências da plataforma...")
            self.install_platform_dependencies()
        
        # 7. Instalar dependências de desenvolvimento (opcional)
        if options.get("install_dev") and success:
            logger.info("\n[7/7] Instalando dependências de desenvolvimento...")
            self.install_development_dependencies()
        
        # Verificar instalação
        if options.get("check_after") and success:
            logger.info("\n" + "=" * 60)
            logger.info("VERIFICAÇÃO FINAL")
            logger.info("=" * 60)
            
            results = self.check_installed_dependencies()
            
            if "error" not in results:
                logger.info(f"Total de dependências: {results['total']}")
                logger.info(f"Instaladas com sucesso: {results['installed']}")
                
                if results['missing']:
                    logger.warning(f"Dependências faltando: {len(results['missing'])}")
                    for missing in results['missing']:
                        logger.warning(f"  - {missing}")
                else:
                    logger.info("✓ Todas as dependências foram instaladas!")
            else:
                logger.error(f"Erro na verificação: {results['error']}")
        
        if success:
            logger.info("\n" + "=" * 60)
            logger.info("INSTALAÇÃO CONCLUÍDA COM SUCESSO!")
            logger.info("=" * 60)
            logger.info("\nPara executar o R2 Assistant:")
            logger.info("  python main.py")
            logger.info("\nPara testes:")
            logger.info("  python -m pytest tests/")
        else:
            logger.error("\n" + "=" * 60)
            logger.error("INSTALAÇÃO FALHOU!")
            logger.error("=" * 60)
            logger.error("\nVerifique os erros acima e tente novamente.")
        
        return success

def main():
    """Função principal"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Instalador de dependências do R2 Assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  %(prog)s                    # Instala todas as dependências
  %(prog)s --dev              # Inclui dependências de desenvolvimento
  %(prog)s --venv             # Cria ambiente virtual
  %(prog)s --requirements alt_requirements.txt  # Usa arquivo diferente
        """
    )
    
    parser.add_argument(
        "--requirements", "-r",
        default="requirements.txt",
        help="Arquivo de requirements (padrão: requirements.txt)"
    )
    
    parser.add_argument(
        "--dev", "-d",
        action="store_true",
        help="Instalar dependências de desenvolvimento"
    )
    
    parser.add_argument(
        "--venv",
        action="store_true",
        help="Criar ambiente virtual"
    )
    
    parser.add_argument(
        "--no-system",
        action="store_true",
        help="Não instalar pacotes do sistema"
    )
    
    parser.add_argument(
        "--no-platform",
        action="store_true",
        help="Não instalar dependências da plataforma"
    )
    
    parser.add_argument(
        "--upgrade",
        action="store_true",
        help="Fazer upgrade das dependências existentes"
    )
    
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Apenas verificar dependências, não instalar"
    )
    
    args = parser.parse_args()
    
    # Configurar opções
    options = {
        "check_python": True,
        "update_pip": not args.check_only,
        "install_requirements": not args.check_only,
        "install_platform": not args.no_platform and not args.check_only,
        "install_dev": args.dev and not args.check_only,
        "create_venv": args.venv and not args.check_only,
        "install_system": not args.no_system and not args.check_only,
        "check_after": True
    }
    
    # Criar instalador
    installer = DependencyInstaller(args.requirements)
    
    if args.check_only:
        logger.info("Verificando dependências instaladas...")
        results = installer.check_installed_dependencies()
        
        if "error" not in results:
            print(json.dumps(results, indent=2, ensure_ascii=False))
        else:
            logger.error(results["error"])
        
        sys.exit(0 if results.get("installed", 0) > 0 else 1)
    else:
        # Executar instalação completa
        success = installer.run(options)
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()