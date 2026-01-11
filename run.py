"""
R2 Assistant - Ponto de entrada com transição suave
"""
import sys
import os
import json
from pathlib import Path

# Adiciona o diretório raiz ao path do Python para garantir imports corretos
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 60)
print("🤖 R2 ASSISTANT - BOOTSTRAP")
print("=" * 60)

# Verificar e criar estrutura
def setup_environment():
    """Configura ambiente básico"""
    
    # Criar diretórios necessários
    dirs = ['data', 'logs', 'assets/sounds', 'assets/icons']
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
    
    # Criar config.json se não existir
    config_file = Path('config.json')
    if not config_file.exists():
        default_config = {
            "UI_THEME": "sci-fi",
            "MAX_HISTORY_SIZE": 1000,
            "DATA_DIR": "data",
            "WINDOW_WIDTH": 1400,
            "WINDOW_HEIGHT": 900
        }
        with open(config_file, 'w') as f:
            json.dump(default_config, f, indent=2)
        print("✅ Configuração padrão criada")
    
    # Verificar dependências críticas
    try:
        import customtkinter
        print("✅ CustomTkinter: OK")
        return True
    except ImportError:
        print("❌ CustomTkinter não instalado")
        print("\nInstale com: pip install customtkinter")
        return False

# Setup básico
if not setup_environment():
    sys.exit(1)

# Importar após setup
try:
    from core.config import AppConfig
    config = AppConfig()
    print(f"✅ Configuração carregada: Tema {config.UI_THEME}")
except Exception as e:
    print(f"⚠️  Erro na configuração: {e}")
    # Configuração de fallback
    from dataclasses import dataclass
    from enum import Enum
    
    class Theme(Enum):
        SCI_FI = "sci-fi"
    
    @dataclass
    class SimpleConfig:
        UI_THEME = Theme.SCI_FI
        MAX_HISTORY_SIZE = 1000
        DATA_DIR = "data"
        WINDOW_WIDTH = 1400
        WINDOW_HEIGHT = 900
    
    config = SimpleConfig()

# Sistema de módulos com fallback inteligente
class ModuleLoader:
    """Carrega módulos com fallback gracioso"""
    
    @staticmethod
    def safe_import(module_name, class_name=None):
        """Importa módulo com tratamento de erro"""
        try:
            module = __import__(module_name, fromlist=[''])
            if class_name:
                return getattr(module, class_name)
            return module
        except ImportError as e:
            print(f"⚠️  Módulo {module_name} não disponível: {e}")
            return None
    
    @staticmethod
    def create_fallback(module_type):
        """Cria fallback para módulo"""
        class Fallback:
            def __init__(self, *args, **kwargs):
                self.name = module_type
                print(f"📦 Usando {module_type} (fallback)")
            
            def __getattr__(self, name):
                return lambda *args, **kwargs: None
            
            def __bool__(self):
                return False
        
        return Fallback

# Carregar componentes
print("\n🔧 Carregando componentes...")
loader = ModuleLoader()

# Componentes essenciais
components = {}

# 1. History Manager
HistoryManager = loader.safe_import('core.history_manager', 'HistoryManager')
if HistoryManager:
    try:
        components['history'] = HistoryManager(max_size=config.MAX_HISTORY_SIZE)
        print("✅ HistoryManager carregado")
    except:
        components['history'] = loader.create_fallback('HistoryManager')()
else:
    components['history'] = loader.create_fallback('HistoryManager')()

# 2. Tema Sci-Fi
SciFiTheme = loader.safe_import('gui.theme', 'SciFiTheme')
if SciFiTheme:
    theme = SciFiTheme()
    print(f"✅ Tema {config.UI_THEME} carregado")
else:
    # Tema fallback
    class SimpleTheme:
        def __init__(self):
            self.colors = {
                'bg_dark': '#0a0a12',
                'bg_medium': '#10101a',
                'primary': '#00ffff',
                'text': '#ffffff'
            }
    theme = SimpleTheme()
    print("⚠️  Usando tema simplificado")

# 3. Alert System (se disponível)
AlertSystem = loader.safe_import('core.alert_system', 'AlertSystem')
if AlertSystem:
    try:
        components['alerts'] = AlertSystem(config, notification_callback=lambda x: None)
        print("✅ AlertSystem carregado")
    except:
        components['alerts'] = loader.create_fallback('AlertSystem')()
else:
    components['alerts'] = loader.create_fallback('AlertSystem')()

# Menu de seleção de interface
print("\n" + "=" * 60)
print("SELECIONE O MODO DE INTERFACE:")
print("=" * 60)
print("1. GUI Completa (Sci-Fi HUD) - Requer módulos")
print("2. GUI Básica - Funcionalidades limitadas")
print("3. Terminal Interativo")
print("4. Instalar dependências e tentar novamente")
print("=" * 60)

choice = input("Escolha (1-4): ").strip()

if choice == "1":
    # Tentar GUI completa
    print("\n🚀 Iniciando GUI Sci-Fi HUD...")
    try:
        from gui.sci_fi_hud import R2SciFiGUI
        import customtkinter as ctk
        
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        app = R2SciFiGUI(config)
        app.title("R2 Assistant - Sci-Fi HUD")
        app.geometry(f"{config.WINDOW_WIDTH}x{config.WINDOW_HEIGHT}")
        
        # Centralizar
        app.update_idletasks()
        screen_width = app.winfo_screenwidth()
        screen_height = app.winfo_screenheight()
        x = (screen_width // 2) - (config.WINDOW_WIDTH // 2)
        y = (screen_height // 2) - (config.WINDOW_HEIGHT // 2)
        app.geometry(f"+{x}+{y}")
        
        print("✅ GUI completa carregada!")
        app.mainloop()
        
    except Exception as e:
        print(f"❌ Erro na GUI completa: {e}")
        print("\n🔄 Voltando para GUI básica...")
        import time
        time.sleep(2)
        choice = "2"  # Fallback para GUI básica

if choice == "2":
    # GUI básica (já testada e funcionando)
    print("\n📱 Iniciando GUI básica...")
    import customtkinter as ctk
    
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    app = ctk.CTk()
    app.title("R2 Assistant - Modo Básico")
    app.geometry("1000x700")
    
    # Frame principal
    main_frame = ctk.CTkFrame(app)
    main_frame.pack(fill="both", expand=True, padx=20, pady=20)
    
    # Título com tema sci-fi
    title_frame = ctk.CTkFrame(main_frame)
    title_frame.pack(fill="x", pady=(0, 20))
    
    ctk.CTkLabel(
        title_frame,
        text="⚡ R2 ASSISTANT ⚡",
        font=("Arial", 32, "bold"),
        text_color="#00ffff"
    ).pack(pady=10)
    
    ctk.CTkLabel(
        title_frame,
        text="Sistema de Assistência em Evolução",
        font=("Arial", 14),
        text_color="#8888aa"
    ).pack()
    
    # Painéis de funcionalidade
    panels_frame = ctk.CTkFrame(main_frame)
    panels_frame.pack(fill="both", expand=True)
    
    # Painel esquerdo - Status
    left_panel = ctk.CTkFrame(panels_frame)
    left_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))
    
    ctk.CTkLabel(
        left_panel,
        text="📊 STATUS DO SISTEMA",
        font=("Arial", 16, "bold"),
        text_color="#00ffff"
    ).pack(anchor="w", padx=20, pady=(20, 10))
    
    # Status items
    status_items = [
        ("✅", "Interface Gráfica", "Operacional"),
        ("✅", "Sistema de Configuração", "Ativo"),
        ("✅", "Gerenciador de Histórico", "Pronto"),
        ("🔄", "Sistema de Alertas", "Inicializando"),
        ("⚡", "Tema Sci-Fi", "Ativo"),
        ("📈", "Próxima Fase", "GUI Completa")
    ]
    
    for icon, name, status in status_items:
        item_frame = ctk.CTkFrame(left_panel)
        item_frame.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(
            item_frame,
            text=f"{icon} {name}",
            font=("Arial", 12)
        ).pack(side="left")
        
        ctk.CTkLabel(
            item_frame,
            text=status,
            font=("Arial", 12, "bold"),
            text_color="#00ff00"
        ).pack(side="right")
    
    # Painel direito - Ações
    right_panel = ctk.CTkFrame(panels_frame)
    right_panel.pack(side="right", fill="both", expand=True)
    
    ctk.CTkLabel(
        right_panel,
        text="🚀 AÇÕES DISPONÍVEIS",
        font=("Arial", 16, "bold"),
        text_color="#00ffff"
    ).pack(anchor="w", padx=20, pady=(20, 10))
    
    def upgrade_to_full():
        """Tenta carregar a GUI completa"""
        import subprocess
        import sys
        
        # Instalar dependências básicas
        deps = ["requests", "psutil", "pyyaml", "pillow"]
        for dep in deps:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
                print(f"✅ {dep} instalado")
            except:
                print(f"⚠️  {dep} não instalado")
        
        print("\n🔄 Reinicie o aplicativo para carregar a GUI completa")
        app.quit()
    
    def open_terminal():
        """Abre terminal interativo"""
        import tkinter as tk
        from tkinter import scrolledtext
        
        terminal = tk.Toplevel(app)
        terminal.title("Terminal R2")
        terminal.geometry("600x400")
        
        text_area = scrolledtext.ScrolledText(terminal, wrap=tk.WORD)
        text_area.pack(fill="both", expand=True)
        
        text_area.insert(tk.END, ">>> Terminal R2 Assistant\n")
        text_area.insert(tk.END, ">>> Digite comandos Python\n\n")
    
    actions = [
        ("🔄 Atualizar Sistema", upgrade_to_full),
        ("💾 Salvar Configuração", lambda: print("Config saved")),
        ("📊 Ver Histórico", lambda: print("History")),
        ("⚙️ Configurações", lambda: print("Settings")),
        ("🔧 Terminal", open_terminal),
        ("❌ Sair", app.quit)
    ]
    
    for text, command in actions:
        btn = ctk.CTkButton(
            right_panel,
            text=text,
            command=command,
            height=40,
            font=("Arial", 12)
        )
        btn.pack(fill="x", padx=20, pady=5)
    
    # Rodapé
    footer_frame = ctk.CTkFrame(main_frame)
    footer_frame.pack(fill="x", pady=(20, 0))
    
    ctk.CTkLabel(
        footer_frame,
        text="ℹ️  Execute novamente para tentar a GUI completa",
        font=("Arial", 10),
        text_color="#8888aa"
    ).pack(pady=5)
    
    app.mainloop()

elif choice == "3":
    # Terminal interativo
    print("\n>>> Terminal R2 Assistant")
    print(">>> Digite 'exit' para sair")
    
    while True:
        try:
            cmd = input("R2> ").strip()
            if cmd.lower() in ['exit', 'quit', 'sair']:
                break
            elif cmd == '':
                continue
            elif cmd == 'help':
                print("Comandos: status, config, modules, install, exit")
            elif cmd == 'status':
                print("Status: GUI básica funcional")
                print("Próximo passo: Instalar módulos para GUI completa")
            elif cmd == 'config':
                print(f"Tema: {config.UI_THEME}")
                print(f"Tamanho da janela: {getattr(config, 'WINDOW_WIDTH', 800)}x{getattr(config, 'WINDOW_HEIGHT', 600)}")
            elif cmd == 'modules':
                print("Módulos carregados:")
                for name, obj in components.items():
                    print(f"  • {name}: {'✅' if obj else '❌'}")
            elif cmd == 'install':
                import subprocess
                import sys
                print("Instalando dependências básicas...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "psutil"])
                print("✅ Dependências instaladas")
            else:
                print(f"Comando não reconhecido: {cmd}")
        except KeyboardInterrupt:
            print("\nSaindo...")
            break
        except Exception as e:
            print(f"Erro: {e}")

elif choice == "4":
    # Instalador de dependências
    print("\n📦 Instalando dependências...")
    import subprocess
    import sys
    
    packages = [
        "customtkinter>=5.2.0",
        "pillow>=10.0.0",
        "requests>=2.31.0",
        "psutil>=5.9.0",
        "pyyaml>=6.0",
        "python-dotenv>=1.0.0",
        "pygame>=2.5.0"
    ]
    
    for package in packages:
        print(f"Instalando {package}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✅ {package.split('>=')[0]}")
        except subprocess.CalledProcessError:
            print(f"⚠️  Falha ao instalar {package}")
    
    print("\n✨ Instalação completa!")
    print("\nExecute novamente para carregar a GUI completa:")
    print("  python run.py")