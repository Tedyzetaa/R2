#!/usr/bin/env python3
"""
R2 Assistant - Sistema de Inicialização Segura V2.1
Com suporte para novos módulos e dependências
"""

import os
import sys
import json
import traceback
import subprocess
from pathlib import Path
from datetime import datetime

# ============================================================================
# DEPENDENCY MANAGER V2.1
# ============================================================================

class DependencyManagerV21:
    """Gerenciador de dependências atualizado para V2.1"""
    
    REQUIRED_DEPENDENCIES = {
        'core': [
            ('customtkinter', '5.2.2'),
            ('numpy', None),
            ('psutil', None),
        ],
        'ai': [
            ('aiohttp', None),
            ('openai', None),  # For OpenRouter compatibility
        ],
        'weather': [
            ('requests', None),
        ],
        'gesture': [
            ('opencv-python', None),
            ('mediapipe', None),
        ],
        'web': [
            ('fastapi', None),
            ('uvicorn', None),
            ('websockets', None),
        ],
        'optional': [
            ('matplotlib', None),
            ('speech_recognition', None),
            ('vosk', None),
            ('pyaudio', None),
        ]
    }
    
    @staticmethod
    def check_dependency(module_name, min_version=None):
        """Verifica se módulo está disponível"""
        try:
            module = __import__(module_name)
            
            if min_version and hasattr(module, '__version__'):
                from packaging import version
                if version.parse(module.__version__) < version.parse(min_version):
                    return {
                        'available': False,
                        'version': module.__version__,
                        'min_required': min_version,
                        'error': f'Version {module.__version__} < {min_version}'
                    }
            
            return {
                'available': True,
                'version': getattr(module, '__version__', 'unknown')
            }
            
        except ImportError as e:
            return {
                'available': False,
                'error': str(e)
            }
        except Exception as e:
            return {
                'available': False,
                'error': f'Unexpected error: {str(e)}'
            }
    
    @staticmethod
    def install_dependency(module_name, version=None):
        """Tenta instalar uma dependência"""
        try:
            package = f"{module_name}=={version}" if version else module_name
            print(f"📦 Installing {package}...")
            
            # Use pip to install
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {module_name}: {e}")
            return False

class EnvironmentCheckerV21:
    """Verificador de ambiente V2.1"""
    
    def __init__(self):
        self.dependencies = {}
        self.problems = []
        self.warnings = []
        self.fallbacks_available = []
        
    def check_all(self, check_optional=True):
        """Verifica todas as dependências"""
        print("\n" + "="*60)
        print("🔍 DIAGNÓSTICO DO AMBIENTE R2 ASSISTANT V2.1")
        print("="*60)
        
        # Check core dependencies
        print("\n📦 DEPENDÊNCIAS CRÍTICAS:")
        for module_name, min_version in DependencyManagerV21.REQUIRED_DEPENDENCIES['core']:
            result = DependencyManagerV21.check_dependency(module_name, min_version)
            self.dependencies[module_name] = result
            
            if result['available']:
                print(f"  ✅ {module_name:20} v{result.get('version', '?')}")
            else:
                print(f"  ❌ {module_name:20} FALTA")
                self.problems.append(f"Dependência crítica: {module_name}")
        
        # Check AI dependencies
        if check_optional:
            print("\n🧠 DEPENDÊNCIAS DE IA:")
            for module_name, min_version in DependencyManagerV21.REQUIRED_DEPENDENCIES['ai']:
                result = DependencyManagerV21.check_dependency(module_name, min_version)
                self.dependencies[module_name] = result
                
                if result['available']:
                    print(f"  ✅ {module_name:20} v{result.get('version', '?')}")
                else:
                    print(f"  ⚠️  {module_name:20} Não disponível")
                    self.warnings.append(f"Dependência de IA: {module_name}")
        
        # Check other optional dependencies
        categories = ['weather', 'gesture', 'web', 'optional'] if check_optional else []
        for category in categories:
            if category in DependencyManagerV21.REQUIRED_DEPENDENCIES:
                print(f"\n🔧 DEPENDÊNCIAS {category.upper()}:")
                for module_name, min_version in DependencyManagerV21.REQUIRED_DEPENDENCIES[category]:
                    result = DependencyManagerV21.check_dependency(module_name, min_version)
                    self.dependencies[module_name] = result
                    
                    if result['available']:
                        print(f"  ✅ {module_name:20} v{result.get('version', '?')}")
                    else:
                        print(f"  ⚠️  {module_name:20} Não disponível")
                        self.warnings.append(f"Dependência {category}: {module_name}")
        
        # Check project structure
        print("\n📁 ESTRUTURA DO PROJETTO V2.1:")
        required_dirs = [
            'core',
            'gui',
            'features',
            'data',
            'logs',
            'plugins',
            'locales'
        ]
        
        for dir_name in required_dirs:
            if Path(dir_name).exists():
                print(f"  ✅ {dir_name:30} OK")
            else:
                print(f"  ⚠️  {dir_name:30} Não encontrado")
                self.warnings.append(f"Diretório faltando: {dir_name}")
        
        print("\n" + "="*60)
        return len(self.problems) == 0
    
    def get_fallback_level(self):
        """Determina nível de fallback necessário"""
        # Check critical dependencies
        critical_modules = ['customtkinter', 'tkinter']
        for module in critical_modules:
            if module in self.dependencies and not self.dependencies[module]['available']:
                return 3  # Emergency mode
        
        # Check GUI dependencies
        gui_modules = ['numpy', 'matplotlib']
        for module in gui_modules:
            if module in self.dependencies and not self.dependencies[module]['available']:
                return 2  # Terminal mode
        
        return 1  # GUI mode

class FallbackSystemV21:
    """Sistema de fallback V2.1"""
    
    @staticmethod
    def launch_gui_full(config):
        """Tenta lançar GUI Sci-Fi completa V2.1"""
        print("\n🚀 Iniciando R2 Assistant V2.1 (GUI Completa)...")
        try:
            from gui.sci_fi_hud import R2SciFiGUI
            app = R2SciFiGUI(config)
            app.run()
            return True
        except Exception as e:
            print(f"❌ GUI completa falhou: {e}")
            return False
    
    @staticmethod
    def launch_gui_basic(config):
        """GUI básica CustomTkinter"""
        print("\n🔄 Fallback: GUI Básica V2.1...")
        try:
            import customtkinter as ctk
            
            class BasicR2GUIV21(ctk.CTk):
                def __init__(self, config):
                    super().__init__()
                    self.config = config
                    
                    self.title("R2 Assistant V2.1 - Modo Básico")
                    self.geometry("900x700")
                    
                    # Interface básica atualizada
                    self._build_interface()
                
                def _build_interface(self):
                    """Constrói interface básica"""
                    main_frame = ctk.CTkFrame(self)
                    main_frame.pack(fill="both", expand=True, padx=20, pady=20)
                    
                    # Cabeçalho
                    ctk.CTkLabel(
                        main_frame,
                        text="⚡ R2 ASSISTANT V2.1 - MODO BÁSICO ⚡",
                        font=("Courier", 24, "bold")
                    ).pack(pady=20)
                    
                    # Status V2.1
                    status_text = """
                    ✅ Sistema de Comandos V2.1
                    ✅ Gerenciador de Histórico
                    ⚠️  IA: Disponível com limitações
                    ⚠️  Clima: Disponível
                    ⚠️  Dashboard Web: Disponível
                    """
                    
                    ctk.CTkLabel(
                        main_frame,
                        text=status_text,
                        font=("Arial", 12)
                    ).pack(pady=10)
                    
                    # Botões de controle
                    controls_frame = ctk.CTkFrame(main_frame)
                    controls_frame.pack(fill="x", pady=20)
                    
                    buttons = [
                        ("🧠 IA Chat", self._open_ai_chat),
                        ("🌤️ Clima", self._open_weather),
                        ("🌐 Web", self._open_web),
                        ("⚙️ Config", self._open_config),
                    ]
                    
                    for text, command in buttons:
                        btn = ctk.CTkButton(
                            controls_frame,
                            text=text,
                            command=command,
                            height=40
                        )
                        btn.pack(side="left", padx=5, pady=5)
            
            app = BasicR2GUIV21(config)
            app.mainloop()
            return True
            
        except Exception as e:
            print(f"❌ GUI básica falhou: {e}")
            return False
    
    @staticmethod
    def launch_terminal_mode(config):
        """Modo terminal interativo V2.1"""
        print("\n💻 Fallback: Terminal Interativo V2.1...")
        
        from core.command_system import CommandSystem
        
        cmd_system = CommandSystem(config)
        
        print("\n" + "="*60)
        print("🤖 R2 ASSISTANT V2.1 - TERMINAL INTERATIVO")
        print("="*60)
        print("\nNovos comandos V2.1:")
        print("  • ai [pergunta]    - Pergunta para IA")
        print("  • tempo [cidade]   - Previsão do tempo")
        print("  • web start/stop   - Controle dashboard web")
        print("  • gestos on/off    - Controle por gestos")
        print("  • plugins list     - Lista plugins")
        print("\nDigite comandos ou 'sair' para sair")
        print("="*60)
        
        while True:
            try:
                user_input = input("\nR2> ").strip()
                
                if user_input.lower() in ['exit', 'quit', 'sair']:
                    print("👋 Até logo!")
                    break
                
                if not user_input:
                    continue
                
                success, response = cmd_system.process_command(user_input)
                
                if success:
                    print(f"✅ {response}")
                else:
                    print(f"❌ {response}")
                    
            except KeyboardInterrupt:
                print("\n\n⚠️ Interrompido pelo usuário")
                break
            except Exception as e:
                print(f"💥 Erro: {e}")
        
        return True

def main():
    """Ponto de entrada principal"""
    print("\n" + "="*60)
    print("🚀 R2 ASSISTANT V2.1 - SISTEMA SEGURO")
    print("="*60)
    
    # Registrar início
    start_time = datetime.now()
    
    try:
        # Verificar ambiente
        checker = EnvironmentCheckerV21()
        environment_ok = checker.check_all(check_optional=True)
        
        # Determinar nível de fallback
        fallback_level = checker.get_fallback_level()
        
        print(f"\n📊 RESUMO DO DIAGNÓSTICO:")
        print(f"  • Ambiente {'OK' if environment_ok else 'COM PROBLEMAS'}")
        print(f"  • Nível de fallback: {fallback_level}")
        print(f"  • Problemas: {len(checker.problems)}")
        print(f"  • Avisos: {len(checker.warnings)}")
        
        # Carregar configuração
        try:
            from core.config import AppConfig
            config = AppConfig.load()
            print("✅ Configuração carregada")
        except:
            print("⚠️ Usando configuração padrão")
            config = AppConfig()
        
        # Sistema de fallback hierárquico
        success = False
        
        if fallback_level == 1:
            success = FallbackSystemV21.launch_gui_full(config)
            if not success:
                fallback_level = 2
        
        if fallback_level == 2:
            success = FallbackSystemV21.launch_gui_basic(config)
            if not success:
                fallback_level = 3
        
        if fallback_level == 3:
            success = FallbackSystemV21.launch_terminal_mode(config)
        
        # Registrar resultado
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"\n" + "="*60)
        print(f"📈 SESSÃO ENCERRADA")
        print(f"   Início: {start_time.strftime('%H:%M:%S')}")
        print(f"   Duração: {duration:.1f} segundos")
        print(f"   Status: {'✅ SUCESSO' if success else '❌ FALHA'}")
        print(f"   Modo: {['GUI Completa', 'GUI Básica', 'Terminal', 'Emergência'][fallback_level-1]}")
        print("="*60)
        
        return 0 if success else 1
        
    except Exception as e:
        print(f"\n❌ ERRO CRÍTICO: {e}")
        print(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main())