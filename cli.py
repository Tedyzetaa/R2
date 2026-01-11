#!/usr/bin/env python3
"""
CLI do R2 Assistant
Interface de linha de comando principal
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Optional, List

# Adicionar diretório raiz ao path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_argparse() -> argparse.ArgumentParser:
    """Configura parser de argumentos"""
    parser = argparse.ArgumentParser(
        description="R2 Assistant - Sistema de Assistência IA com Interface Sci-Fi/HUD",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  %(prog)s                    # Iniciar interface gráfica
  %(prog)s --mode cli         # Modo linha de comando
  %(prog)s --mode trading     # Modo trading
  %(prog)s --mode voice       # Modo voz
  %(prog)s --config my_config.yaml  # Usar configuração personalizada
  %(prog)s --version          # Ver versão
        """
    )
    
    # Modo de operação
    parser.add_argument(
        "--mode", "-m",
        choices=["gui", "cli", "trading", "voice", "alerts", "security", "developer"],
        default="gui",
        help="Modo de operação (padrão: gui)"
    )
    
    # Configuração
    parser.add_argument(
        "--config", "-c",
        type=str,
        help="Caminho para arquivo de configuração"
    )
    
    # Tema
    parser.add_argument(
        "--theme", "-t",
        choices=["sci-fi", "dark", "light", "cyberpunk", "matrix"],
        default="sci-fi",
        help="Tema da interface (padrão: sci-fi)"
    )
    
    # Idioma
    parser.add_argument(
        "--language", "-l",
        default="pt-BR",
        help="Idioma da interface (padrão: pt-BR)"
    )
    
    # Logging
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Nível de logging (padrão: INFO)"
    )
    
    # Log file
    parser.add_argument(
        "--log-file",
        type=str,
        help="Arquivo de log personalizado"
    )
    
    # Debug
    parser.add_argument(
        "--debug", "-d",
        action="store_true",
        help="Modo debug"
    )
    
    # Version
    parser.add_argument(
        "--version", "-v",
        action="store_true",
        help="Mostrar versão e sair"
    )
    
    # Comandos específicos
    subparsers = parser.add_subparsers(
        title="comandos",
        dest="command",
        help="Comandos específicos"
    )
    
    # Comando: init
    init_parser = subparsers.add_parser(
        "init",
        help="Inicializar configuração do R2 Assistant"
    )
    init_parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Forçar recriação dos arquivos de configuração"
    )
    
    # Comando: update
    update_parser = subparsers.add_parser(
        "update",
        help="Atualizar R2 Assistant"
    )
    update_parser.add_argument(
        "--check-only",
        action="store_true",
        help="Apenas verificar atualizações"
    )
    
    # Comando: models
    models_parser = subparsers.add_parser(
        "models",
        help="Gerenciar modelos de IA"
    )
    models_parser.add_argument(
        "action",
        choices=["list", "download", "remove", "update", "verify"],
        help="Ação a realizar"
    )
    models_parser.add_argument(
        "model_name",
        nargs="?",
        help="Nome do modelo (para download/remove)"
    )
    
    # Comando: backup
    backup_parser = subparsers.add_parser(
        "backup",
        help="Operações de backup"
    )
    backup_parser.add_argument(
        "action",
        choices=["create", "restore", "list", "cleanup"],
        help="Ação a realizar"
    )
    backup_parser.add_argument(
        "--path", "-p",
        help="Caminho do backup (para restore)"
    )
    
    return parser

def show_version():
    """Mostra versão do R2 Assistant"""
    try:
        from r2_assistant import __version__
        print(f"R2 Assistant v{__version__}")
        
        # Informações do sistema
        import platform
        print(f"Python: {platform.python_version()}")
        print(f"Sistema: {platform.system()} {platform.release()}")
        
        # Informações de build
        build_info_file = Path(__file__).parent / "BUILD_INFO"
        if build_info_file.exists():
            with open(build_info_file, "r") as f:
                print(f"Build: {f.read().strip()}")
                
    except ImportError:
        print("R2 Assistant não está instalado corretamente.")
        sys.exit(1)

def run_gui_mode(args):
    """Executa modo GUI"""
    try:
        from r2_assistant.gui.sci_fi_hud import R2SciFiGUI
        from r2_assistant.core.config import AppConfig
        
        # Carregar configuração
        config = AppConfig(args.config)
        
        # Aplicar argumentos da CLI
        if args.theme:
            config.gui.theme = args.theme
        if args.language:
            config.app.language = args.language
        if args.debug:
            config.logging.level = "DEBUG"
        
        # Criar e executar GUI
        app = R2SciFiGUI(config)
        app.run()
        
    except ImportError as e:
        logger.error(f"Erro ao importar módulos GUI: {e}")
        print("Dependências GUI não instaladas. Instale com:")
        print("  pip install r2-assistant[gui]")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Erro ao executar GUI: {e}")
        sys.exit(1)

def run_cli_mode(args):
    """Executa modo CLI interativo"""
    try:
        from r2_assistant.commands import CommandProcessor, CommandRegistry
        from r2_assistant.commands.basic_commands import BasicCommands
        from r2_assistant.commands.system_commands import SystemCommands
        
        print("R2 Assistant - Modo CLI Interativo")
        print("Digite 'help' para comandos disponíveis ou 'exit' para sair")
        print("-" * 60)
        
        # Inicializar sistema de comandos
        registry = CommandRegistry()
        processor = CommandProcessor(registry)
        
        # Registrar comandos básicos
        BasicCommands(registry, processor)
        SystemCommands(registry, processor)
        
        # Loop interativo
        while True:
            try:
                command = input("\nr2> ").strip()
                
                if command.lower() in ["exit", "quit", "q"]:
                    print("Saindo...")
                    break
                
                if not command:
                    continue
                
                # TODO: Implementar execução de comandos
                print(f"Comando recebido: {command}")
                # result = await processor.process(command, context)
                # print(result.message)
                
            except KeyboardInterrupt:
                print("\nSaindo...")
                break
            except EOFError:
                print("\nSaindo...")
                break
                
    except Exception as e:
        logger.error(f"Erro no modo CLI: {e}")
        sys.exit(1)

def run_trading_mode(args):
    """Executa modo trading"""
    try:
        from r2_assistant.features.trading import TradingSystem
        
        print("R2 Assistant - Modo Trading")
        print("-" * 60)
        
        trading = TradingSystem()
        trading.start()
        
    except ImportError:
        print("Módulo de trading não instalado. Instale com:")
        print("  pip install r2-assistant[trading]")
        sys.exit(1)

def run_voice_mode(args):
    """Executa modo voz"""
    try:
        from r2_assistant.features.voice import VoiceAssistant
        
        print("R2 Assistant - Modo Voz")
        print("-" * 60)
        print("Fale agora... (Ctrl+C para sair)")
        
        assistant = VoiceAssistant()
        assistant.start_listening()
        
    except ImportError:
        print("Módulo de voz não instalado. Instale com:")
        print("  pip install r2-assistant[voice]")
        sys.exit(1)

def handle_init_command(args):
    """Lida com comando init"""
    try:
        from scripts.setup_environment import EnvironmentSetup
        
        setup = EnvironmentSetup()
        setup.run()
        
    except Exception as e:
        logger.error(f"Erro ao inicializar: {e}")
        sys.exit(1)

def handle_models_command(args):
    """Lida com comando models"""
    try:
        from scripts.download_models import ModelDownloader
        
        downloader = ModelDownloader()
        
        if args.action == "list":
            models = downloader.list_available_models()
            if models:
                print(f"\nModelos disponíveis ({len(models)}):")
                for model in models:
                    installed = "✓" if downloader.is_model_installed(model["name"]) else " "
                    print(f"[{installed}] {model['name']:30} {model.get('size_mb', '?')} MB")
            else:
                print("Nenhum modelo configurado.")
                
        elif args.action == "download" and args.model_name:
            success = downloader.download_model(args.model_name)
            if success:
                print(f"✓ Modelo {args.model_name} baixado com sucesso!")
            else:
                print(f"✗ Falha ao baixar {args.model_name}")
                
        elif args.action == "remove" and args.model_name:
            success = downloader.remove_model(args.model_name)
            if success:
                print(f"✓ Modelo {args.model_name} removido!")
            else:
                print(f"✗ Falha ao remover {args.model_name}")
                
        elif args.action == "verify" and args.model_name:
            result = downloader.verify_model_integrity(args.model_name)
            print(f"\nStatus: {result['status'].upper()}")
            if result['status'] == 'ok':
                print("✓ Modelo íntegro")
                
    except Exception as e:
        logger.error(f"Erro no gerenciamento de modelos: {e}")
        sys.exit(1)

def main():
    """Função principal"""
    parser = setup_argparse()
    args = parser.parse_args()
    
    # Mostrar versão
    if args.version:
        show_version()
        sys.exit(0)
    
    # Configurar logging
    log_level = getattr(logging, args.log_level)
    logging.getLogger().setLevel(log_level)
    
    if args.log_file:
        file_handler = logging.FileHandler(args.log_file)
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        logging.getLogger().addHandler(file_handler)
    
    # Processar comandos específicos
    if args.command == "init":
        handle_init_command(args)
        return
    elif args.command == "models":
        handle_models_command(args)
        return
    elif args.command == "backup":
        # TODO: Implementar backup
        print("Funcionalidade de backup em desenvolvimento...")
        return
    elif args.command == "update":
        # TODO: Implementar update
        print("Funcionalidade de update em desenvolvimento...")
        return
    
    # Executar modo principal
    if args.mode == "gui":
        run_gui_mode(args)
    elif args.mode == "cli":
        run_cli_mode(args)
    elif args.mode == "trading":
        run_trading_mode(args)
    elif args.mode == "voice":
        run_voice_mode(args)
    else:
        print(f"Modo '{args.mode}' não implementado.")
        parser.print_help()

if __name__ == "__main__":
    main()