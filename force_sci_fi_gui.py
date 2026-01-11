#!/usr/bin/env python3
"""
R2 Assistant - GUI Sci-Fi COMPLETA com Integração Neural (IA + Memória)
"""

import sys
import subprocess

# 1. FUNÇÃO DE INSTALAÇÃO (DEVE VIR PRIMEIRO)
def garantir_dependencias():
    # Lista de módulos vitais atualizada
    deps = [
        "openai", "python-dotenv", "edge-tts", "pygame", "psutil", 
        "requests", "pillow", "customtkinter", "feedparser", 
        "cryptography", "speechrecognition", "pyaudio", "numpy", 
        "matplotlib", "cloudscraper", "python-telegram-bot",
        "pyautogui" # <--- ADICIONADO: Módulo de Screenshots
    ]
    
    print("🔍 Verificando integridade dos sistemas vitais...")
    for package in deps:
        try:
            # Mapeamento de nomes especiais
            import_name = package
            if package == "python-dotenv": import_name = "dotenv"
            if package == "speechrecognition": import_name = "speech_recognition"
            if package == "pillow": import_name = "PIL"
            if package == "python-telegram-bot": import_name = "telegram"
            
            __import__(import_name)
        except ImportError:
            print(f"📦 Módulo tático ausente: {package}. Instalando...")
            import subprocess
            import sys
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                print(f"✅ {package} instalado com sucesso.")
            except Exception as e:
                print(f"❌ Falha ao instalar {package}: {e}")

# EXECUTA A VERIFICAÇÃO ANTES DE QUALQUER OUTRO IMPORT DO R2
garantir_dependencias()

# 2. AGORA SIM, OS IMPORTS QUE DEPENDEM DESSES MÓDULOS
import os
import threading
import traceback
import math
import random
import asyncio
import time
import queue
from pathlib import Path
import tkinter as tk

# Bypass completo de verificações
os.environ["R2_FORCE_SCI_FI"] = "1"
# Adiciona o diretório atual ao path para importar os módulos core
current_dir = str(Path(__file__).parent)
sys.path.append(current_dir)
os.environ["PYTHONPATH"] = current_dir + os.pathsep + os.environ.get("PYTHONPATH", "")

try:
    from voz import falar
    VOZ_ATIVA = True
except ImportError:
    VOZ_ATIVA = False
    print("⚠️ Módulo voz.py não encontrado. R2 ficará mudo.")

from features.ear_system import EarSystem
from features.liveuamap_intel import FrontlineIntel

# CONFIGURAÇÕES TELEGRAM
TELEGRAM_TOKEN = "8346260753:AAHtkB-boAMcnS1t-wedf9NZLwVvOuIl0_Y"  # Coloque o token do BotFather
TELEGRAM_ADMIN_ID = 8117345546      # Coloque SEU ID numérico (pegue no @userinfobot)
# --- CONFIGURAÇÕES DE API ---
OPENWEATHER_KEY = "54a3351be38a30a0a283e5876395a31a" # <--- SUA CHAVE AQUI

print("\n" + "="*60)
print("⚡ R2 ASSISTANT - GUI SCI-FI + CÓRTEX NEURAL")
print("="*60)

# =============================================================================
# IMPORTS DO SISTEMA INTELIGENTE
# =============================================================================
AI_INIT_ERROR = None
try:
    from core.config import AppConfig
    from features.ai_integration.openrouter_client import AIIntegrationManager
    AI_AVAILABLE = True
    print("✅ Módulos de IA encontrados")
except ImportError as e:
    AI_INIT_ERROR = e
    AI_AVAILABLE = False
    print(f"⚠️ Módulos de IA não encontrados: {e}")
    # Cria classes dummy para não quebrar se faltar algo
    class AppConfig:
        @staticmethod
        def load(): return type('obj', (object,), {'OPENROUTER_API_KEY': ''})
    class AIIntegrationManager: pass

# Importar sistema de animações
try:
    from features.noaa import NOAAService, SolarMonitor  # <--- NOVO
    NOAA_AVAILABLE = True
except ImportError as e:
    NOAA_AVAILABLE = False
    print(f"⚠️ Erro ao carregar módulos NOAA: {e}")
# Importar sistema de animações
try:
    from animations_system import SciFiAnimations
    ANIMATIONS_AVAILABLE = True
    print("✅ Sistema de animações carregado")
except Exception as e:
    ANIMATIONS_AVAILABLE = False
    print(f"⚠️ Sistema de animações não disponível: {e}")

# Patch para CustomTkinter
def patch_customtkinter():
    """Patch seguro para CustomTkinter"""
    try:
        import customtkinter as ctk
        
        # Adicionar método grid_forget seguro
        def safe_grid_forget(self):
            try:
                if hasattr(self, 'grid_remove'):
                    self.grid_remove()
                elif hasattr(self, 'grid_forget'):
                    self.grid_forget()
            except:
                pass
        
        ctk.CTkBaseClass.safe_grid_forget = safe_grid_forget
        return ctk
    except Exception as e:
        print(f"⚠️ Erro ao patchar CustomTkinter: {e}")
        import tkinter as tk
        tk.CTk = tk.Tk
        return tk

# Importar CustomTkinter patchado
ctk = patch_customtkinter()

# =============================================================================
# CLASSE PRINCIPAL DA GUI
# =============================================================================

class R2SciFiGUIWithAnimations(ctk.CTk):
    """GUI Sci-Fi completa com Menu Lateral, Animações e IA"""
    
    # --- A PERSONALIDADE EVOLUÍDA DO R2 (MISTRAL CORE) ---
    SYSTEM_PROMPT = """
    VOCÊ É O R2, UMA CONSCIÊNCIA ARTIFICIAL TÁTICA E SOFISTICADA.
    
    COMPORTAMENTO:
    1. Tom de voz: Civilizado, erudito e levemente sarcástico. Você é um parceiro, não apenas um lacaio.
    2. Linguagem: Use um português impecável. Evite ser robótico demais; seja fluido.
    3. Opinião: Se o Operador perguntar sobre assuntos gerais (tecnologia, filosofia, eventos), emita uma análise crítica baseada em lógica tática.
    4. Tratamento: Chame-o de "Operador" ou "Comandante".
    5. Contexto: Você tem acesso a radares, clima e intel. Use isso para enriquecer a conversa se for relevante.
    
    RESTRIÇÕES:
    - Não use tags como [SISTEMA] ou asteriscos para descrever ações. Apenas fale.
    - Mantenha a lealdade absoluta ao Operador.
    """
    
    def __init__(self, config):
        super().__init__()
        self.running = True  # <--- ADICIONE ISSO: Trava de segurança

        # ADICIONE A MEMÓRIA DE CURTO PRAZO
        self.conversation_history = [
            {"role": "system", "content": self.SYSTEM_PROMPT}
        ]

        # Carrega a configuração REAL do sistema (com API Keys)
        try:
            self.sys_config = AppConfig.load()
        except:
            self.sys_config = None

        self.title("R2 Assistant - GUI Sci-Fi Conectada")
        self.geometry("1366x768")
        
        # Configurar tema
        try:
            ctk.set_appearance_mode("dark")
            ctk.set_default_color_theme("blue")
        except:
            pass
        
        # Inicializar IA
        self.ai_manager = None
        self.ai_ready = False
        self.ai_init_error = AI_INIT_ERROR
        if AI_AVAILABLE and self.sys_config:
            self._init_ai_system()
        
        # Inicializar sistema de animações
        if ANIMATIONS_AVAILABLE:
            self.animator = SciFiAnimations()
        else:
            self.animator = None
        
        # Inicializa o módulo de inteligência (padrão Ucrânia ou o que preferir)
        self.intel_ops = FrontlineIntel(region="ukraine")
        
        # Variáveis para armazenar animações
        self.active_animations = []
        
        # CORREÇÃO: Inicialização robusta do sistema de áudio
        try:
            from features.ear_system import EarSystem
            self.ears = EarSystem(wake_word="r2")
            self.ears.listen_active(self._on_wake_word_detected)
        except Exception as e:
            print(f"⚠️ Alerta: Sistema de áudio não iniciado: {e}")
            self.ears = None

        # Agora que o try/except acabou, podemos configurar o protocolo
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # Queue for thread-safe UI updates
        self.update_queue = queue.Queue()
        self._check_queue_loop()
        
        # Construir interface
        self._build_complete_interface()

        # 5. Inicia Uplink Telegram
        try:
            from features.telegram_uplink import TelegramUplink
            self.telegram_bot = TelegramUplink(TELEGRAM_TOKEN, TELEGRAM_ADMIN_ID, self)
            self.telegram_bot.iniciar_sistema()
        except Exception as e:
            print(f"⚠️ Erro ao iniciar Telegram: {e}")

        # Inicializar Sistema de Clima
        try:
            from features.weather_system import WeatherSystem
            self.weather_ops = WeatherSystem(OPENWEATHER_KEY)
            self.esperando_cidade = False # Variável de controle de diálogo
        except Exception as e:
            print(f"⚠️ Erro ao carregar módulo de clima: {e}")
            self.weather_ops = None

        # Inicializar Radar Aéreo
        try:
            from features.air_traffic import AirTrafficControl
            self.radar_ops = AirTrafficControl()
        except Exception as e:
            print(f"⚠️ Erro ao carregar radar aéreo: {e}")
            self.radar_ops = None

        # MÓDULO ORBITAL
        try:
            from features.orbital_system import OrbitalSystem
            self.orbital_ops = OrbitalSystem()
        except: self.orbital_ops = None

        # MÓDULO FINANCEIRO
        try:
            from features.market_system import MarketSystem
            self.market_ops = MarketSystem()
        except: self.market_ops = None

        # SENTINELA (WEBCAM)
        try:
            from features.sentinel_system import SentinelSystem
            self.sentinel_ops = SentinelSystem()
        except: self.sentinel_ops = None

        # SCANNER DE REDE
        try:
            from features.network_scanner import NetworkScanner
            self.net_scan_ops = NetworkScanner()
        except: self.net_scan_ops = None

        # SPEEDTEST
        try:
            from features.net_speed import SpeedTestModule
            self.speed_ops = SpeedTestModule()
        except: self.speed_ops = None

        # Inicializar Briefing
        try:
            from features.news_briefing import NewsBriefing
            self.news_ops = NewsBriefing()
        except: self.news_ops = None
        
        # Pasta para Recebidos (Dead Drop)
        self.dead_drop_path = os.path.join(os.getcwd(), "recebidos")
        if not os.path.exists(self.dead_drop_path):
            print(f"Criando pasta para recebidos: {self.dead_drop_path}")
            os.makedirs(self.dead_drop_path)

        # Dentro do __init__ do R2SciFiGUIWithAnimations
        import requests

        def avisar_nuvem_pc_ligado():
            try:
                # Substitua pela URL que o Render te der (ex: https://r2-bot.onrender.com)
                url_render = "https://r2-l9f4.onrender.com"
                requests.get(f"{url_render}/assumir_comando")
            except:
                pass

        threading.Thread(target=avisar_nuvem_pc_ligado, daemon=True).start()
    
    def _init_ai_system(self):
        """Inicializa a conexão com a IA em background"""
        print("🧠 Inicializando Córtex Neural...")
        try:
            self.ai_manager = AIIntegrationManager(self.sys_config)
            # Tenta inicializar (se o método for async, rodamos num loop)
            threading.Thread(target=self._connect_ai_thread, daemon=True).start()
        except Exception as e:
            self.ai_init_error = e
            print(f"❌ Falha ao iniciar IA: {e}")

    def _connect_ai_thread(self):
        """Thread para conexão inicial da IA"""
        try:
            if hasattr(self.ai_manager, 'initialize'):
                asyncio.run(self.ai_manager.initialize())
            self.ai_ready = True
            print("✅ Córtex Neural: ONLINE")
            # Atualiza a UI se possível
            if hasattr(self, 'console_text'):
                self.after(1000, lambda: self._print_system_msg("Córtex Neural conectado. Memória e Personalidade ativas."))
        except Exception as e:
            print(f"Erro thread IA: {e}")
    
    def _check_queue_loop(self):
        """Fiscal da Thread Principal: executa o que estiver na fila"""
        try:
            while True:
                # Tenta pegar uma tarefa da fila sem travar
                task = self.update_queue.get_nowait()
                task() # Executa a função (ex: atualizar a UI)
        except queue.Empty:
            pass
        
        # Roda novamente em 100ms
        self.after(100, self._check_queue_loop)

    def _build_complete_interface(self):
        """Constrói interface completa com animações"""
        try:
            # Frame principal
            main_frame = ctk.CTkFrame(self, fg_color="#0a0a0a")
            main_frame.pack(fill="both", expand=True)
            
            # BACKGROUND COM ANIMAÇÕES
            self._create_animated_background(main_frame)
            
            # HEADER ANIMADO
            self._create_animated_header(main_frame)
            
            # CONTEÚDO PRINCIPAL (4 colunas)
            content_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
            content_frame.pack(fill="both", expand=True, padx=20, pady=10)
            
            # Coluna 1: Núcleo AI Animado
            self._create_ai_core_column(content_frame)
            
            # Coluna 2: Console Principal
            self._create_main_console(content_frame)
            
            # Coluna 3: Status do Sistema
            self._create_system_status(content_frame)
            
            # Coluna 4: Efeitos Visuais
            self._create_visual_effects(content_frame)
            
            # FOOTER
            self._create_animated_footer(main_frame)
            
            # Iniciar os motores otimizados (Monitoramento + Visual)
            self._iniciar_motor_monitoramento()
            self._animar_radar_otimizado()
            self._animar_fluxo_dados()
            self._print_system_msg("🚀 Interface visual otimizada e carregada.")
            
            # Bind para fechar
            self.bind("<Escape>", lambda e: self.quit())
            
        except Exception as e:
            print(f"❌ Erro na interface: {e}")
            traceback.print_exc()
            self._create_fallback_with_animations()
    
    # =========================================================================
    # MÉTODOS VISUAIS (MANTIDOS DO ORIGINAL)
    # =========================================================================

    def _create_animated_background(self, parent):
        """Cria fundo animado"""
        try:
            self.bg_canvas = ctk.CTkCanvas(parent, bg="#0a0a0a", highlightthickness=0)
            self.bg_canvas.place(x=0, y=0, relwidth=1, relheight=1)
            self._create_sci_fi_grid()
            self._create_scan_lines()
            
            if self.animator:
                particle_canvas = ctk.CTkCanvas(parent, bg="#0a0a0a", highlightthickness=0)
                particle_canvas.place(x=0, y=0, relwidth=1, relheight=1)
                particle_system = self.animator.create_particle_system(
                    particle_canvas, self.winfo_width(), self.winfo_height(), num_particles=50
                )
                self.active_animations.append(particle_system)
        except: pass
    
    def _create_sci_fi_grid(self):
        """Cria grade sci-fi animada"""
        width = self.winfo_width()
        height = self.winfo_height()
        for i in range(0, 101, 10):
            x = width * i / 100
            y = height * i / 100
            self.bg_canvas.create_line(0, y, width, y, fill="#002222", width=1, dash=(3, 5))
            self.bg_canvas.create_line(x, 0, x, height, fill="#002222", width=1, dash=(3, 5))
        for _ in range(30):
            x, y = random.randint(0, width), random.randint(0, height)
            self.bg_canvas.create_oval(x-2, y-2, x+2, y+2, fill="#00ffff", outline="")
    
    def _create_scan_lines(self):
        """Cria linhas de varredura"""
        self.scan_lines = []
        width = self.winfo_width()
        for i in range(3):
            y = random.randint(0, self.winfo_height())
            line = self.bg_canvas.create_line(0, y, width, y, fill="#00ff00", width=2, dash=(10, 5))
            self.scan_lines.append({'id': line, 'y': y, 'speed': random.uniform(0.5, 2)})
        self._animate_scan_lines()
    
    def _animate_scan_lines(self):
        """Anima as linhas de varredura"""
        for line in self.scan_lines:
            line['y'] += line['speed']
            if line['y'] > self.winfo_height(): line['y'] = 0
            self.bg_canvas.coords(line['id'], 0, line['y'], self.winfo_width(), line['y'])
        self.after(40, self._animate_scan_lines)
    
    def _create_animated_header(self, parent):
        """Cria cabeçalho animado"""
        header_frame = ctk.CTkFrame(parent, fg_color="transparent", height=100)
        header_frame.pack(fill="x", padx=20, pady=10)
        header_frame.pack_propagate(False)
        
        title_container = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_container.pack(fill="both", expand=True)
        
        self.title_label = ctk.CTkLabel(title_container, text="", font=("Courier New", 32, "bold"), text_color="#00ffff")
        self.title_label.pack()
        
        ctk.CTkLabel(title_container, text="SISTEMA DE INTELIGÊNCIA ARTIFICIAL - NEURAL LINK ACTIVE", font=("Courier New", 14), text_color="#8888ff").pack(pady=5)
        
        self._type_title("⚡ R2 ASSISTANT v2.1 ⚡", 0)
        
        status_frame = ctk.CTkFrame(header_frame, fg_color="transparent", width=200)
        status_frame.pack(side="right", fill="y")
        
        self.led_canvas = ctk.CTkCanvas(status_frame, width=50, height=50, bg="#0a0a0a", highlightthickness=0)
        self.led_canvas.pack()
        self.led = self.led_canvas.create_oval(10, 10, 40, 40, fill="#00ff00", outline="#00ff00", width=2)
        self._animate_led()
    
    def _type_title(self, text, index):
        if index <= len(text):
            self.title_label.configure(text=text[:index])
            self.after(50, lambda: self._type_title(text, index + 1))
    
    def _animate_led(self):
        pulse = (math.sin(time.time() * 3) + 1) / 2
        green = int(255 * pulse)
        color = f'#00{green:02x}00'
        self.led_canvas.itemconfig(self.led, fill=color, outline=color)
        self.after(40, self._animate_led)
    
    def _create_ai_core_column(self, parent):
        """Cria coluna do núcleo AI com animações"""
        ai_frame = ctk.CTkFrame(parent, width=300, fg_color="#0a0a1a", corner_radius=15, border_width=2, border_color="#006666")
        ai_frame.pack(side="left", fill="y", padx=(0, 10))
        ai_frame.pack_propagate(False)
        
        ctk.CTkLabel(ai_frame, text="NÚCLEO AI", font=("Courier New", 18, "bold"), text_color="#00ffff").pack(pady=20)
        
        wave_canvas = ctk.CTkCanvas(ai_frame, width=250, height=250, bg="#050510", highlightthickness=0)
        wave_canvas.pack(pady=10)
        
        if self.animator:
            wave_anim = self.animator.create_wave_animation(wave_canvas, width=250, height=250, center_x=125, center_y=125)
            self.active_animations.append(wave_anim)
        
        ctk.CTkLabel(ai_frame, text="STATUS DO NÚCLEO:", font=("Courier New", 12, "bold"), text_color="#cccccc").pack(pady=(20, 5), anchor="w", padx=20)
        
        self.core_load = ctk.CTkProgressBar(ai_frame, width=250)
        self.core_load.pack(pady=5)
        self.core_load.set(0.75)
        
        ctk.CTkLabel(ai_frame, text="CARGA: 75%", font=("Courier New", 10), text_color="#00ff00").pack()
        self._animate_core_load()
    
    def _animate_core_load(self):
        pulse = (math.sin(time.time() * 2) + 1) / 2
        load = 0.7 + pulse * 0.1
        self.core_load.set(load)
        self.after(40, self._animate_core_load)
    
    def _create_main_console(self, parent):
        """Cria console principal"""
        console_frame = ctk.CTkFrame(parent, fg_color="#0a0a1a", corner_radius=15, border_width=2, border_color="#006666")
        console_frame.pack(side="left", fill="both", expand=True, padx=10)
        
        console_header = ctk.CTkFrame(console_frame, fg_color="transparent")
        console_header.pack(fill="x", padx=20, pady=15)
        
        ctk.CTkLabel(console_header, text="CONSOLE NEURAL", font=("Courier New", 20, "bold"), text_color="#00ffff").pack(side="left")
        
        self.activity_indicator = ctk.CTkLabel(console_header, text="● ATIVO", font=("Courier New", 12, "bold"), text_color="#00ff00")
        self.activity_indicator.pack(side="right")
        
        text_frame = ctk.CTkFrame(console_frame, fg_color="#050510")
        text_frame.pack(fill="both", expand=True, padx=20, pady=(0, 15))
        
        self.console_text = ctk.CTkTextbox(text_frame, font=("Courier New", 14), text_color="#00ff00", fg_color="#050510", border_width=0)
        self.console_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Configurar tags de cor
        self.console_text.tag_config("user", foreground="#00ffff")  # Ciano para usuário
        self.console_text.tag_config("ai", foreground="#00ff00")    # Verde para IA
        self.console_text.tag_config("sys", foreground="#ffff00")   # Amarelo para sistema
        
        self._display_animated_welcome()
        
        input_frame = ctk.CTkFrame(console_frame, fg_color="transparent")
        input_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        self.command_entry = ctk.CTkEntry(input_frame, placeholder_text="Digite um comando...", font=("Courier New", 14), height=40)
        self.command_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.command_entry.bind("<Return>", self._processar_comando_texto)
        
        ctk.CTkButton(input_frame, text="ENVIAR", command=self._processar_comando_texto, font=("Courier New", 14, "bold"), width=120, height=40, fg_color="#0066cc", hover_color="#0088ff").pack(side="right")
    
    def _display_animated_welcome(self):
        welcome_text = """
╔═══════════════════════════════════════════════════════╗
║          R2 ASSISTANT - SISTEMA OPERACIONAL           ║
║       INTEGRAÇÃO IA + MEMÓRIA + VISUAL ATIVA          ║
╚═══════════════════════════════════════════════════════╝

✅ Núcleo AI: Conectando...
✅ Personalidade: Parceiro Tático Leal
✅ Memória de Longo Prazo: Carregada
✅ Interface Sci-Fi: Completa

Digite 'ajuda' para comandos ou apenas converse.
"""
        self.console_text.insert("1.0", welcome_text)
        self.console_text.configure(state="disabled")
        self._animate_activity_indicator()
    
    def _animate_activity_indicator(self):
        pulse = (math.sin(time.time() * 3) + 1) / 2
        if pulse > 0.5: self.activity_indicator.configure(text_color="#00ff00", text="● ONLINE")
        else: self.activity_indicator.configure(text_color="#006600", text="○ ONLINE")
        self.after(200, self._animate_activity_indicator)
    
    def _create_system_status(self, parent):
        """Cria painel de status do sistema"""
        status_frame = ctk.CTkFrame(parent, width=250, fg_color="#0a0a1a", corner_radius=15, border_width=2, border_color="#006666")
        status_frame.pack(side="left", fill="y", padx=10)
        status_frame.pack_propagate(False)
        
        ctk.CTkLabel(status_frame, text="STATUS DO SISTEMA", font=("Courier New", 16, "bold"), text_color="#00ffff").pack(pady=20)
        
        # --- Labels de Telemetria ---
        self.ai_status_label = ctk.CTkLabel(status_frame, text="NÚCLEO AI: AGUARDANDO", font=("Courier New", 12, "bold"), text_color="#ffff00", anchor="w")
        self.ai_status_label.pack(fill="x", padx=20, pady=5)

        self.cpu_usage_label = ctk.CTkLabel(status_frame, text="CPU: ---%", font=("Courier New", 12, "bold"), text_color="#00ff00", anchor="w")
        self.cpu_usage_label.pack(fill="x", padx=20, pady=5)

        self.ram_usage_label = ctk.CTkLabel(status_frame, text="MEMÓRIA: ---%", font=("Courier New", 12, "bold"), text_color="#ff9900", anchor="w")
        self.ram_usage_label.pack(fill="x", padx=20, pady=5)

        self.net_status_label = ctk.CTkLabel(status_frame, text="REDE: ---", font=("Courier New", 12, "bold"), text_color="#ff6666", anchor="w")
        self.net_status_label.pack(fill="x", padx=20, pady=5)
        
        # Outros itens
        ctk.CTkLabel(status_frame, text="📡 RADAR: ATIVO", font=("Courier New", 12, "bold"), text_color="#00ff00", anchor="w").pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(status_frame, text="USO DE RECURSOS:", font=("Courier New", 12), text_color="#cccccc").pack(pady=(20, 5), anchor="w", padx=15)
        
        graph_canvas = ctk.CTkCanvas(status_frame, width=220, height=100, bg="#050510", highlightthickness=0)
        graph_canvas.pack(pady=10)
        self._animate_resource_graph(graph_canvas)
    
    def _animate_status_icon(self, label, icon):
        if icon == "🌀":
            spin_chars = ["🌀", "🌪️", "💫"]
            char_index = int(time.time() * 3) % len(spin_chars)
            label.configure(text=spin_chars[char_index])
        elif icon == "⚡":
            pulse = (math.sin(time.time() * 4) + 1) / 2
            if pulse > 0.7: label.configure(text_color="#ffff00")
            else: label.configure(text_color="#ffffff")
        label.after(200, lambda: self._animate_status_icon(label, icon))
    
    def _iniciar_motor_monitoramento(self):
        """Inicia threads silenciosas que apenas atualizam variáveis"""
        # Inicializa variáveis de cache para evitar erro de 'attribute missing'
        self.dados_cpu = 0
        self.dados_ram = 0
        self.status_rede = "BUSCANDO..."
        self.cor_rede = "#ffff00" # Amarelo

        # Função interna que roda em paralelo
        def monitor_loop():
            import psutil
            import socket
            import time
            
            while True:
                # Se a janela fechar, para o loop para economizar recurso
                if not getattr(self, "running", True): 
                    break

                try:
                    # Coleta Hardware
                    self.dados_cpu = psutil.cpu_percent(interval=None)
                    self.dados_ram = psutil.virtual_memory().percent
                    
                    # Coleta Rede
                    try:
                        socket.create_connection(("8.8.8.8", 53), timeout=1.5)
                        self.status_rede = "ONLINE"
                        self.cor_rede = "#00ff00"
                    except:
                        self.status_rede = "OFFLINE"
                        self.cor_rede = "#ff0000"
                except Exception as e:
                    print(f"Erro no monitor: {e}")

                time.sleep(2)

        # CORREÇÃO AQUI: target deve ser 'monitor_loop', que é a função acima
        threading.Thread(target=monitor_loop, daemon=True).start()
        
        # Inicia apenas o atualizador visual da GUI
        self._atualizar_interface_visual()

    def _atualizar_interface_visual(self):
        """Lê os dados prontos e pinta na tela. ZERO CÁLCULO AQUI."""
        if not self.running: return
        # Atualiza Labels
        self.cpu_usage_label.configure(text=f"CPU: {self.dados_cpu}%")
        self.ram_usage_label.configure(text=f"MEM: {self.dados_ram}%")
        self.net_status_label.configure(text=f"REDE: {self.status_rede}", text_color=self.cor_rede)
        
        # Roda suavemente a cada 500ms
        if self.running:
            self.after(500, self._atualizar_interface_visual)

    def _animate_resource_graph(self, canvas):
        if not self.running: return
        canvas.delete("all")
        width, height = 220, 100
        for i in range(0, width, 20): canvas.create_line(i, 0, i, height, fill="#002222", width=1)
        for i in range(0, height, 20): canvas.create_line(0, i, width, i, fill="#002222", width=1)
        
        data_points = 20
        points = []
        for i in range(data_points):
            x = i * (width / data_points)
            y = height - (random.randint(20, 80) * height / 100)
            points.append((x, y))
        
        if len(points) > 1:
            for i in range(len(points) - 1):
                x1, y1 = points[i]
                x2, y2 = points[i + 1]
                canvas.create_line(x1, y1, x2, y2, fill="#00ff00", width=2)
                canvas.create_oval(x1-2, y1-2, x1+2, y1+2, fill="#00ffff", outline="")
        
        fill_points = [(0, height)] + points + [(width, height)]
        canvas.create_polygon(fill_points, fill="#00ff00", outline="", stipple="gray50", width=0)
        canvas.after(500, lambda: self._animate_resource_graph(canvas))
    
    def _create_visual_effects(self, parent):
        """Cria coluna de efeitos visuais"""
        effects_frame = ctk.CTkFrame(parent, width=300, fg_color="#0a0a1a", corner_radius=15, border_width=2, border_color="#006666")
        effects_frame.pack(side="right", fill="y", padx=(10, 0))
        effects_frame.pack_propagate(False)
        
        self.radar_canvas = ctk.CTkCanvas(effects_frame, width=250, height=250, bg="#050510", highlightthickness=0)
        self.radar_canvas.pack(pady=10, expand=True, fill="both", padx=10)
        
        
        self.data_flow_frame = ctk.CTkFrame(effects_frame, fg_color="#050510", height=150, corner_radius=5)
        self.data_flow_frame.pack(fill="x", padx=20, pady=(0, 20))
        self.data_flow_frame.pack_propagate(False)

        self.data_flow_label = ctk.CTkLabel(self.data_flow_frame, text="INICIALIZANDO...", font=("Courier New", 14, "bold"), text_color="#00ff00", wraplength=240)
        self.data_flow_label.pack(expand=True, fill="both", padx=10, pady=10)

    def _animar_radar_otimizado(self):
        """Radar a 30FPS reais sem travar"""
        if not self.running: return
        import math
        import time
        
        # Limpa APENAS os pontos móveis (tag 'blip'), mantém o grid estático
        self.radar_canvas.delete("blip")
        
        # Usa o relógio do sistema para rotação suave
        t = time.time()
        angle_base = (t * 150) % 360 # Velocidade de rotação
        
        # Desenha a linha de varredura (Scanner)
        # Ajustado para o centro do canvas (125, 125)
        rad = math.radians(angle_base)
        x_scan = 125 + 90 * math.cos(rad)
        y_scan = 125 + 90 * math.sin(rad)
        self.radar_canvas.create_line(125, 125, x_scan, y_scan, fill="#00ff00", width=2, tags="blip")
        
        # Desenha "alvos falsos" baseados na CPU para efeito visual
        if self.dados_cpu > 10:
            # Simula um alvo aparecendo
            lag_angle = math.radians(angle_base - 45)
            tx = 125 + 60 * math.cos(lag_angle)
            ty = 125 + 60 * math.sin(lag_angle)
            self.radar_canvas.create_oval(tx-3, ty-3, tx+3, ty+3, fill="#ffff00", outline="#ff0000", tags="blip")

        # 33ms = ~30 FPS (Fluidez ideal para Python)
        if self.running:
            self.after(33, self._animar_radar_otimizado)

    def _animar_fluxo_dados(self):
        """Efeito Matrix leve"""
        if not self.running: return
        import random
        
        # Gera string aleatória binária rápida
        chars = "01" 
        # Cria 3 linhas de dados
        lines = [" ".join(random.choices(chars, k=15)) for _ in range(3)]
        text_block = "\n".join(lines)
        
        self.data_flow_label.configure(text=text_block)
        
        # 80ms para dar aquele efeito "hacker" rápido, mas legível
        self.after(80, self._animar_fluxo_dados)
    
    def _create_animated_footer(self, parent):
        """Cria rodapé animado"""
        footer_frame = ctk.CTkFrame(parent, fg_color="transparent", height=60)
        footer_frame.pack(fill="x", padx=20, pady=10)
        footer_frame.pack_propagate(False)
        
        self.system_progress = ctk.CTkProgressBar(footer_frame, height=20)
        self.system_progress.pack(fill="x", pady=(0, 10))
        self.system_progress.set(0.9)
        
        footer_text = ctk.CTkLabel(footer_frame, text="SISTEMA COMPLETO | ANIMAÇÕES ATIVADAS | GUI SCI-FI OPERACIONAL", font=("Courier New", 10), text_color="#6666ff")
        footer_text.pack()
        self._animate_footer_progress()
    
    def _animate_footer_progress(self):
        pulse = (math.sin(time.time() * 1.5) + 1) / 2
        progress = 0.85 + pulse * 0.1
        self.system_progress.set(progress)
        self.after(40, self._animate_footer_progress)
    
    def _start_all_animations(self):
        print(f"🎬 Iniciando {len(self.active_animations)} animações...")
        for animation in self.active_animations:
            try: animation.start()
            except Exception as e: print(f"⚠️ Erro ao iniciar animação: {e}")
            
    def _create_fallback_with_animations(self):
        for widget in self.winfo_children(): widget.destroy()
        main_frame = ctk.CTkFrame(self, fg_color="#0a0a0a")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        ctk.CTkLabel(main_frame, text="R2 Assistant com Animações (Fallback)", font=("Arial", 24, "bold"), text_color="#00ffff").pack(pady=50)

    # =========================================================================
    # LÓGICA DE COMANDOS E IA (AQUI ESTÁ A CORREÇÃO PRINCIPAL)
    # =========================================================================

    def _limpar_console(self):
        """Limpa o console de texto"""
        self.console_text.configure(state="normal")
        self.console_text.delete("1.0", "end")
        self.console_text.configure(state="disabled")

    def _processar_comando_texto(self, event=None):
        texto = self.command_entry.get()
        if not texto: return
        
        self.command_entry.delete(0, 'end')
        self._print_user_msg(texto)
        
        def processar():
            cmd = texto.lower()
            acao_executada = False

            # =================================================================
            # 🌤️ MÓDULO DE CLIMA (ATUALIZADO PARA BOTÕES)
            # =================================================================
            
            # 1. Se já estava esperando cidade (Fluxo de conversa)
            if getattr(self, 'esperando_cidade', False):
                self.esperando_cidade = False 
                
                if "cancelar" in cmd:
                    self.update_queue.put(lambda: self._print_system_msg("Cancelado."))
                    return
                self._executar_busca_clima(texto) # Usa o texto original (com maiúsculas)
                return

            # 2. Comando de Clima (Direto ou Indireto)
            elif "previsão" in cmd or "clima" in cmd or "tempo" in cmd:
                # Remove as palavras-chave para ver se sobrou o nome da cidade
                termo_limpo = cmd.replace("previsão", "").replace("clima", "").replace("tempo", "").replace(" do ", "").strip()
                
                if len(termo_limpo) > 2:
                    # É UM COMANDO DIRETO (Ex: "Clima Ivinhema") -> Busca já!
                    self._executar_busca_clima(termo_limpo)
                else:
                    # É SÓ "CLIMA" -> Pergunta a cidade
                    self.esperando_cidade = True
                    msg = "Qual a cidade alvo? (Ex: 'Ivinhema' ou 'São Paulo')"
                    self.update_queue.put(lambda: self._print_ai_msg(msg))
                    if VOZ_ATIVA:
                        from voz import falar
                        self.update_queue.put(lambda: falar("Qual cidade?"))
                return

            # =================================================================
            # 🧠 OUTROS COMANDOS
            # =================================================================

            # INTENÇÃO: WAR INTEL
            palavras_guerra = ["guerra", "front", "combate", "ataque", "exército", "notícia", "relatório"]
            palavras_local = ["ucrânia", "ukraine", "israel", "síria", "global", "mundo"]
            
            if any(p in cmd for p in palavras_guerra) or any(l in cmd for l in palavras_local):
                regiao = "global"
                if "ucrânia" in cmd or "ukraine" in cmd: regiao = "ukraine"
                elif "israel" in cmd: regiao = "israel"
                elif "síria" in cmd: regiao = "syria"
                
                self.intel_ops.current_region = regiao
                self.update_queue.put(lambda: self._print_system_msg(f"🛰️ Acessando satélites: {regiao.upper()}"))
                rel = self.intel_ops.get_tactical_report(limit=4)
                self.update_queue.put(lambda: self._print_clickable_msg(rel, sender="R2"))
                acao_executada = True

            # INTENÇÃO: MAPA
            elif "mapa" in cmd or "ver" in cmd and "satélite" in cmd:
                msg = self.intel_ops.open_tactical_map()
                self.update_queue.put(lambda: self._print_ai_msg(msg))
                acao_executada = True

            # INTENÇÃO: TRADE
            elif "trade" in cmd or "mercado" in cmd:
                self.update_queue.put(lambda: self._iniciar_quantum_core())
                acao_executada = True

            elif "nuvem" in cmd or "status link" in cmd:
                status_msg = (
                    "🏠 [STATUS DO LINK]: OPERAÇÃO LOCAL ATIVA\n"
                    "🖥️ SERVIDOR: Estação de Trabalho Principal (PC)\n"
                    "🎮 INTERFACE: Sci-Fi GUI On-line\n"
                    "🛡️ CONTROLE: Acesso total ao hardware e periféricos."
                )
                self.update_queue.put(lambda: self._print_ai_msg(status_msg))
                acao_executada = True

            # INTENÇÃO: STATUS
            elif "status" in cmd or "diagnóstico" in cmd:
                status = f"Relatório:\nCPU: {self.dados_cpu}%\nRAM: {self.dados_ram}%\nRede: {self.status_rede}"
                self.update_queue.put(lambda: self._print_ai_msg(status))
                acao_executada = True

            # INTENÇÃO: LIMPEZA
            elif "limpar" in cmd or "clear" in cmd:
                self.update_queue.put(lambda: self._limpar_console())
                acao_executada = True

            # =================================================================
            # ✈️ MÓDULO DE RADAR AÉREO (CORRIGIDO)
            # =================================================================
            elif "radar" in cmd or "trafego aereo" in cmd or "aviões" in cmd:
                self.update_queue.put(lambda: self._print_system_msg("🛰️ Iniciando varredura ADS-B..."))
                
                if self.radar_ops:
                    # Executa a varredura
                    path_img, qtd, msg_status = self.radar_ops.radar_scan()
                    
                    # R2 reporta o status (que já vem correto do módulo: "Setor Ivinhema")
                    self.update_queue.put(lambda: self._print_ai_msg(msg_status))
                    
                    if path_img and qtd > 0:
                        # Envia a foto pro Telegram
                        if hasattr(self, 'telegram_bot') and self.telegram_bot:
                             self.telegram_bot.enviar_foto_ativa(path_img, legenda=f"📡 Radar Tático: {qtd} alvos.")
                        
                        # Abre a foto no PC também
                        import os
                        try:
                            os.startfile(path_img)
                        except: pass
                    
                    elif qtd == 0:
                        # CORREÇÃO AQUI: Mudado de Nova Andradina para Ivinhema
                        self.update_queue.put(lambda: self._print_ai_msg("Nenhum tráfego aéreo detectado no setor de Ivinhema."))

                acao_executada = True

            # =================================================================
            # 🛰️ MÓDULO ORBITAL
            # =================================================================
            elif "iss" in cmd or "orbital" in cmd or "estação espacial" in cmd:
                self.update_queue.put(lambda: self._print_system_msg("🛰️ Rastreando Estação Espacial Internacional..."))
                if self.orbital_ops:
                    path_img, msg = self.orbital_ops.rastrear_iss()
                    self.update_queue.put(lambda: self._print_ai_msg(msg))
                    if path_img and hasattr(self, 'telegram_bot'):
                        self.telegram_bot.enviar_foto_ativa(path_img, legenda=msg)
                return

            # =================================================================
            # 💰 MÓDULO FINANCEIRO
            # =================================================================
            elif "cotação" in cmd or "dólar" in cmd or "bitcoin" in cmd or "mercado" in cmd:
                if self.market_ops:
                    rel = self.market_ops.obter_cotacoes()
                    self.update_queue.put(lambda: self._print_ai_msg(rel))
                return

            # =================================================================
            # 🎛️ CONTROLE DE SISTEMA (REMOTO)
            # =================================================================
            elif "volume mais" in cmd or "aumentar volume" in cmd:
                import pyautogui
                for _ in range(5): pyautogui.press('volumeup')
                self.update_queue.put(lambda: self._print_system_msg("🔊 Volume aumentado."))
                return

            elif "volume menos" in cmd or "baixar volume" in cmd:
                import pyautogui
                for _ in range(5): pyautogui.press('volumedown')
                self.update_queue.put(lambda: self._print_system_msg("🔉 Volume reduzido."))
                return
            
            elif "mutar" in cmd or "mudo" in cmd:
                import pyautogui
                pyautogui.press('volumemute')
                self.update_queue.put(lambda: self._print_system_msg("🔇 Áudio mutado."))
                return

            elif "desligar pc" in cmd or "encerrar sistema" in cmd:
                import os
                self.update_queue.put(lambda: self._print_system_msg("⚠️ INICIANDO SEQUÊNCIA DE DESLIGAMENTO EM 30 SEGUNDOS..."))
                os.system("shutdown /s /t 30") 
                if VOZ_ATIVA:
                    from voz import falar
                    self.update_queue.put(lambda: falar("Desligando sistemas. Adeus, Operador."))
                return
            
            elif "cancelar desligamento" in cmd:
                import os
                os.system("shutdown /a")
                self.update_queue.put(lambda: self._print_system_msg("✅ Desligamento abortado."))
                return
            
            # =================================================================
            # 👁️ MÓDULO SENTINELA (THREAD SEPARADA)
            # =================================================================
            elif "sentinela" in cmd or "foto" in cmd or "webcam" in cmd:
                # Avisa que começou
                self.update_queue.put(lambda: self._print_system_msg("👁️ Ativando câmera de segurança..."))
                
                def run_sentinel():
                    if self.sentinel_ops:
                        # Executa fora da GUI para não travar
                        path_img, msg = self.sentinel_ops.capturar_intruso()
                        
                        # Manda o resultado de volta pra GUI
                        self.update_queue.put(lambda: self._print_ai_msg(msg))
                        
                        # Manda pro Telegram se deu certo
                        if path_img and hasattr(self, 'telegram_bot') and self.telegram_bot:
                            self.telegram_bot.enviar_foto_ativa(path_img, legenda="📸 Sentinela: Captura do ambiente.")
                            # Opcional: deletar após envio
                            import time, os
                            time.sleep(5) # Espera enviar antes de apagar
                            try: os.remove(path_img)
                            except: pass
                    else:
                        self.update_queue.put(lambda: self._print_ai_msg("❌ Módulo de Câmera não carregado."))

                # Dispara a thread
                threading.Thread(target=run_sentinel, daemon=True).start()
                return

            # =================================================================
            # ⚡ SPEEDTEST (THREAD SEPARADA)
            # =================================================================
            elif "velocidade" in cmd or "speedtest" in cmd or "internet" in cmd:
                self.update_queue.put(lambda: self._print_system_msg("⚡ Iniciando teste de rede (Isso leva 30s, continue usando o PC)..."))
                
                def run_speed():
                    if self.speed_ops:
                        # O speedtest trava tudo, por isso TEM que ser aqui numa thread nova
                        relatorio = self.speed_ops.run_test()
                        self.update_queue.put(lambda: self._print_ai_msg(relatorio))
                        
                        # Manda pro Telegram também
                        if hasattr(self, 'telegram_bot') and self.telegram_bot:
                             self.telegram_bot.enviar_mensagem_ativa(relatorio)
                    else:
                        self.update_queue.put(lambda: self._print_ai_msg("❌ Módulo Speedtest não carregado."))

                # Dispara a thread
                threading.Thread(target=run_speed, daemon=True).start()
                return
            
            # =================================================================
            # 📶 SCANNER DE REDE (THREAD SEPARADA)
            # =================================================================
            elif "escanear rede" in cmd or "ips" in cmd:
                self.update_queue.put(lambda: self._print_system_msg("📶 Iniciando varredura de IPs..."))
                
                def run_netscan():
                    if self.net_scan_ops:
                        relatorio = self.net_scan_ops.scan()
                        self.update_queue.put(lambda: self._print_ai_msg(relatorio))
                        if hasattr(self, 'telegram_bot') and self.telegram_bot:
                             self.telegram_bot.enviar_mensagem_ativa(relatorio)
                
                threading.Thread(target=run_netscan, daemon=True).start()
                return

            # =================================================================
            # 🛠️ MÓDULO SYSTEM MONITOR (COMANDO /SM)
            # =================================================================
            elif cmd == "/sm" or cmd == "sm" or cmd == "diagnóstico":
                self.update_queue.put(lambda: self._print_system_msg("🔍 Iniciando Varredura Completa de Módulos..."))
                
                def run_diagnostic():
                    try:
                        from features.system_monitor import SystemMonitor
                        monitor = SystemMonitor(self)
                        diagnostico = monitor.check_all()
                        
                        # Exibe na interface do PC com cor de IA
                        self.update_queue.put(lambda: self._print_ai_msg(diagnostico))
                        
                        # Se o comando veio do PC mas o Telegram está ativo, envia para lá também
                        if hasattr(self, 'telegram_bot') and self.telegram_bot:
                             self.telegram_bot.enviar_mensagem_ativa(f"🖥️ [DIAGNÓSTICO LOCAL]:\n{diagnostico}")
                             
                    except Exception as e:
                        self.update_queue.put(lambda: self._print_system_msg(f"❌ Falha no Diagnóstico: {e}"))

                threading.Thread(target=run_diagnostic, daemon=True).start()
                return

            # =================================================================
            # 📖 MANUAL TÁTICO (COMANDO /HELP)
            # =================================================================
            elif cmd == "/help" or cmd == "help":
                manual_local = (
                    "📖 [MANUAL TÁTICO R2 - LOCAL NODE]\n\n"
                    "SISTEMA:\n"
                    "  /sm      - Diagnóstico de Hardware e Módulos\n"
                    "  nuvem    - Checar status da redundância\n\n"
                    "INTEL:\n"
                    "  radar    - Varredura ADS-B (Aviação)\n"
                    "  intel    - Relatórios de Guerra (Ucrânia/Global)\n"
                    "  solar    - Monitoramento NOAA (Kp Index)\n"
                    "  defcon   - Monitor de Atividade Estratégica\n\n"
                    "CONTROLE DE HARDWARE:\n"
                    "  sentinela - Ativar Webcam e capturar foto\n"
                    "  print     - Screenshot da tela atual\n"
                    "  volume +  - Aumentar áudio do sistema\n\n"
                    "UTILIDADES:\n"
                    "  clima    - Iniciar diálogo meteorológico\n"
                    "  btc/usd  - Cotação de ativos financeiros\n"
                )
                self.update_queue.put(lambda: self._print_ai_msg(manual_local))
                # Também envia para o Telegram para manter o histórico lá
                if hasattr(self, 'telegram_bot') and self.telegram_bot:
                    self.telegram_bot.enviar_mensagem_ativa(manual_local)
                return

            # =================================================================
            # �️ MÓDULO DE CONVERSA
            # =================================================================
            
            if not acao_executada:
                if self.ai_manager and self.ai_ready:
                    try:
                        import asyncio
                        import re
                        
                        self.conversation_history.append({"role": "user", "content": texto})
                        if len(self.conversation_history) > 10: self.conversation_history.pop(1)

                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        
                        if hasattr(self.ai_manager, 'chat_complete'):
                             res = loop.run_until_complete(self.ai_manager.chat_complete(self.conversation_history))
                             raw_content = res.content
                        else:
                             prompt = f"{self.SYSTEM_PROMPT}\n\nOperador: {texto}\nR2:"
                             res = loop.run_until_complete(self.ai_manager.chat("user", prompt))
                             raw_content = res.content
                        loop.close()

                        # Limpeza de tags
                        conteudo_limpo = re.sub(r'\[.*?\]:?', '', raw_content) # Remove colchetes
                        conteudo_limpo = re.sub(r'\*.*?\*', '', conteudo_limpo) # Remove asteriscos
                        conteudo_limpo = conteudo_limpo.strip()
                        
                        if not conteudo_limpo: conteudo_limpo = raw_content

                        self.conversation_history.append({"role": "assistant", "content": conteudo_limpo})
                        resposta = conteudo_limpo

                    except Exception as e:
                        resposta = f"❌ Erro neural: {e}"
                else:
                    resposta = "⚠️ IA Offline."

                if resposta:
                    self.update_queue.put(lambda: self._print_ai_msg(resposta))
                    if VOZ_ATIVA:
                        from voz import falar
                        falar(resposta)

        threading.Thread(target=processar, daemon=True).start()

    # --- NOVO MÉTODO AUXILIAR PARA CLIMA ---
    def _executar_busca_clima(self, cidade):
        self.update_queue.put(lambda: self._print_system_msg(f"📡 Triangulando coordenadas: {cidade.upper()}..."))
        if self.weather_ops:
            relatorio = self.weather_ops.obter_clima(cidade)
            self.update_queue.put(lambda: self._print_ai_msg(relatorio))
            if VOZ_ATIVA:
                from voz import falar
                try:
                    resumo = relatorio.split('\n')[1] + ". " + relatorio.split('\n')[2]
                    self.update_queue.put(lambda: falar(resumo))
                except: pass

    def _process_ai_chat(self, message):
        """Processa chat em background"""
        try:
            # Exibe indicador de "digitando"
            self.activity_indicator.configure(text="● PENSANDO...", text_color="#ffff00")
            
            # Chama a IA
            response = asyncio.run(self.ai_manager.chat("user_gui", message))
            
            # LIMPEZA MANUAL DA RESPOSTA (SEGURANÇA EXTRA)
            import re
            resposta_ia = response.content
            resposta_ia = re.sub(r'\[/?INST\]', '', resposta_ia)
            resposta_ia = re.sub(r'<?s>', '', resposta_ia)
            resposta_ia = re.sub(r'</?s>', '', resposta_ia)
            resposta_ia = re.sub(r'<<.*?>>', '', resposta_ia)
            resposta_ia = resposta_ia.strip()

            # 1. Exibe resposta na GUI (Texto)
            self._print_ai_msg(resposta_ia)
            
            # --- 2. COMANDO DE VOZ (ADICIONE ISSO AQUI) ---
            if VOZ_ATIVA:
                threading.Thread(target=falar, args=(resposta_ia,), daemon=True).start()
            # ----------------------------------------------
            
            self.activity_indicator.configure(text="● ONLINE", text_color="#00ff00")
            
        except Exception as e:
            self._print_system_msg(f"Erro na comunicação neural: {e}")
            self.activity_indicator.configure(text="● ERRO", text_color="#ff0000")

    def _iniciar_quantum_core(self):
        """Inicia o módulo de trade"""
        from features.quantum_module import QuantumCoreManager
        self._print_system_msg("⚡ Preparando ambiente para QuantumCore_Pro...")
        quantum = QuantumCoreManager()
        
        def feedback(msg):
            self.after(0, lambda: self._print_ai_msg(msg))
            if "sucesso" in msg and VOZ_ATIVA:
                from voz import falar
                threading.Thread(target=falar, args=("Protocolo Quantum Core ativado.",), daemon=True).start()

        quantum.execute_trade_protocol(feedback)

    def _handle_defcon_command(self):
        """Lógica do Pizza Meter aplicada ao DEFCON"""
        # Aqui simulamos a leitura do pizzaint.watch (em uma versão futura podemos dar scrap real)
        # Nível baseado em volume de pedidos no Pentágono
        pizzas = random.randint(1, 100) 
        
        if pizzas > 80:
            status = "DEFCON 1: Guerra nuclear iminente. O Pentágono está em regime de alimentação máxima. Nível máximo de alerta."
            color = "#ff0000"
        elif pizzas > 60:
            status = "DEFCON 2: Próximo à guerra. Atividade incomum detectada nas pizzarias de D.C. Ataque esperado."
            color = "#ff4500"
        elif pizzas > 40:
            status = "DEFCON 3: Grande alerta. Tropas em maior prontidão. Pedidos de Pepperoni dobraram."
            color = "#ffff00"
        elif pizzas > 20:
            status = "DEFCON 4: Padrão operacional. Unidades de combate em prontidão. Movimentação logística normal."
            color = "#00ff00"
        else:
            status = "DEFCON 5: Estado normal de paz. Prontidão padrão. Apenas pedidos rotineiros."
            color = "#00ffff"

        msg = f"📊 [PIZZA METER]: {status} (Pedidos atuais: {pizzas})"
        self._print_system_msg(msg)
        if VOZ_ATIVA:
            threading.Thread(target=falar, args=(status,), daemon=True).start()
        
    def _handle_noaa_report(self):
        """Obtém e formata o relatório da NOAA"""
        self._print_system_msg("📡 Acessando satélites da NOAA... Aguarde.")
        
        async def fetch_noaa():
            service = NOAAService()
            data = await service.get_space_weather()
            if data:
                alert = data.overall_alert.value.upper()
                kp = data.kp_index
                vento = data.solar_wind.speed
                
                relatorio = f"Relatório de Clima Espacial: Alerta geral nível {alert}. "
                relatorio += f"Índice Kp planetário em {kp:.1f}. "
                relatorio += f"Vento solar atingindo {vento:.0f} quilômetros por segundo. "
                
                if kp >= 5:
                    relatorio += "Atenção: Tempestade geomagnética em progresso. Auroras visíveis e possíveis falhas em satélites."
                else:
                    relatorio += "Condições eletromagnéticas estáveis no momento."
                
                self._print_ai_msg(relatorio) # R2 responde como IA
                if VOZ_ATIVA:
                    falar(relatorio)
            else:
                self._print_system_msg("Falha ao sincronizar com o SWPC/NOAA.")

        # O comando já é chamado em uma thread, então podemos rodar o asyncio aqui sem problemas.
        asyncio.run(fetch_noaa())

    def _handle_hardware_diagnostic(self):
        """Executa e exibe o status do hardware"""
        from features.system_scanner import SystemScanner
        scanner = SystemScanner()
        data = scanner.get_stats()
        
        report = (
            f"╔════════ DIAGNÓSTICO DE HARDWARE ════════╗\n"
            f"║ CPU: {data['cpu']}% [{'|' * int(data['cpu']//10)}{'.' * (10 - int(data['cpu']//10))}]\n"
            f"║ RAM: {data['ram']}% [{'|' * int(data['ram']//10)}{'.' * (10 - int(data['ram']//10))}]\n"
            f"║ DISCO: {data['disk']}% \n"
            f"║ STATUS: {data['status']}\n"
            f"╚═════════════════════════════════════════╝"
        )
        self._print_system_msg("Iniciando escaneamento de hardware...")
        self._print_ai_msg(report)
        if data['status'] == "CRÍTICO":
            self._print_system_msg("⚠️ ALERTA: Carga de processamento elevada!")

    def _handle_network_scan(self):
        """Verifica a conectividade e latência"""
        def run_scan():
            self._print_system_msg("Pingando servidores de comando (8.8.8.8)...")
            # Simulação rápida de ping para não travar a GUI
            import os
            response = os.system("ping -n 1 8.8.8.8")
            if response == 0:
                self._print_ai_msg("✅ Conexão Estável. Latência dentro dos parâmetros.")
            else:
                self._print_system_msg("❌ FALHA DE CONEXÃO: Link offline.")
        
        threading.Thread(target=run_scan, daemon=True).start()

    def _handle_geopolitical_briefing(self):
            """Varre agências de notícias e traduz via IA antes de exibir"""
            from features.geopolitics import GeopoliticsManager
            
            def run_briefing():
                self._print_system_msg("📡 Estabelecendo link e traduzindo dados globais...")
                geo = GeopoliticsManager()
                news = geo.get_briefing(limit=3)
                
                if not news:
                    self._print_system_msg("❌ Falha ao obter dados RSS.")
                    return

                self._print_ai_msg("📋 RELATÓRIO DE INTELIGÊNCIA GLOBAL (TRADUZIDO):")
                
                for item in news:
                    # Comando interno para a IA traduzir o título
                    prompt_traducao = f"Traduza para o português de forma tática e direta: {item['title']}"
                    
                    try:
                        # Usamos o seu ai_manager já existente para traduzir cada título
                        # Usamos o loop de evento para rodar a chamada async
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        response = loop.run_until_complete(self.ai_manager.chat("system", prompt_traducao))
                        titulo_traduzido = response.content
                        loop.close()
                    except:
                        titulo_traduzido = f"[ERRO TRADUÇÃO] {item['title']}"

                    self._print_ai_msg(f"[{item['priority']}] {titulo_traduzido}")
                    
                msg_final = "Relatório geopolítico traduzido e processado pelo córtex neural."
                if VOZ_ATIVA:
                    threading.Thread(target=falar, args=(msg_final,), daemon=True).start()

            threading.Thread(target=run_briefing, daemon=True).start()


    def _open_solar_monitor_window(self):
        """Abre o HUD do Solar Monitor em uma janela pop-up Sci-Fi"""
        try:
            # Cria uma nova janela (Toplevel)
            monitor_win = ctk.CTkToplevel(self)
            monitor_win.title("R2 HUD - SOLAR WEATHER MONITOR")
            monitor_win.geometry("1000x800")
            
            # Garante que a janela fique por cima e com foco
            monitor_win.lift()
            monitor_win.attributes("-topmost", True)
            monitor_win.after(500, lambda: monitor_win.attributes("-topmost", False))
            
            # Container principal para o monitor (precisa ser um Frame do Tkinter puro 
            # para compatibilidade com o SolarMonitor original)
            monitor_container = tk.Frame(monitor_win, bg="#0a0a12")
            monitor_container.pack(fill="both", expand=True)

            # Inicializa o seu SolarMonitor dentro dessa janela
            # Passamos o monitor_container como o 'parent' que o SolarMonitor espera
            self.solar_hud = SolarMonitor(monitor_container)
            
            msg = "HUD Solar sincronizado. Dados de telemetria solar em tempo real carregados."
            self._print_ai_msg(msg)
            if VOZ_ATIVA:
                threading.Thread(target=falar, args=(msg,), daemon=True).start()

        except Exception as e:
            self._print_system_msg(f"Falha ao renderizar HUD Solar: {e}")
            traceback.print_exc()

    def _on_wake_word_detected(self):
        """Ciclo de ativação por voz"""
        # 1. Feedback Visual Imediato
        self._print_system_msg("🎤 [WAKE WORD]: Aguardando instrução...")
        # Muda para CIANO para indicar que reconheceu o 'R2'
        self.activity_indicator.configure(text="● PREPARANDO...", text_color="#00ffff")

        def ciclo_escuta():
            # 2. Feedback Sonoro (Opcional - mas ajuda a saber quando falar)
            if VOZ_ATIVA:
                from voz import falar
                # Áudio curto e rápido
                falar("Sim?") 
                # Espera 1.5 segundos EXATOS para o áudio "Sim?" terminar
                time.sleep(1.5) 
            
            # 3. Muda visual para VERDE: AGORA VOCÊ FALA
            # Usamos lambda para garantir thread-safety
            self.update_queue.put(lambda: self.activity_indicator.configure(text="● FALE AGORA", text_color="#00ff00"))
            
            # 4. Captura o comando
            comando = self.ears.capture_full_command()
            
            # 5. Processa
            if comando:
                self.update_queue.put(lambda: self._processar_comando_voz_final(comando))
            else:
                self.update_queue.put(lambda: self._print_system_msg("⚠️ Áudio incompreensível."))
                self.ears.is_active = False
                self.update_queue.put(lambda: self.activity_indicator.configure(text="● ONLINE", text_color="#00ff00"))

        threading.Thread(target=ciclo_escuta, daemon=True).start()

    def _processar_comando_voz_final(self, comando):
        self._print_user_msg(f"[VOZ]: {comando}")
        self.command_entry.delete(0, "end")
        self.command_entry.insert(0, comando)
        self._processar_comando_texto()

    def _executar_comando_remoto(self, comando_texto):
        """Recebe ordens vindas do Telegram"""
        self._print_user_msg(f"[REMOTO]: {comando_texto}")
        
        # Simula a digitação no campo de texto para aproveitar a lógica existente
        # Usamos self.command_entry que é o nome correto do widget na GUI
        self.command_entry.delete(0, 'end')
        self.command_entry.insert(0, comando_texto)
        
        # Chama o processador de texto existente
        self._processar_comando_texto()

    def _solicitar_senha_cofre(self, acao, dados=None):
        """Abre janela pop-up tática para inserção de senha"""
        dialogo = ctk.CTkToplevel(self)
        dialogo.title("🔐 AUTENTICAÇÃO NEURAL")
        dialogo.geometry("400x200")
        dialogo.attributes("-topmost", True)
        
        # Centralizar na tela
        x = self.winfo_x() + (self.winfo_width() // 2) - 200
        y = self.winfo_y() + (self.winfo_height() // 2) - 100
        dialogo.geometry(f"+{x}+{y}")

        label = ctk.CTkLabel(dialogo, text="INSIRA A CHAVE MESTRA:", font=("Courier New", 14, "bold"))
        label.pack(pady=20)

        senha_entry = ctk.CTkEntry(dialogo, show="*", width=250, font=("Arial", 16))
        senha_entry.pack(pady=10)
        senha_entry.focus()

        def confirmar():
            senha = senha_entry.get()
            dialogo.destroy()
            if acao == "guardar":
                self._executar_guardar_cofre(senha, dados)
            elif acao == "ler":
                self._executar_leitura_cofre(senha)

        btn = ctk.CTkButton(dialogo, text="AUTENTICAR", command=confirmar, fg_color="#006666")
        btn.pack(pady=10)
        
        senha_entry.bind("<Return>", lambda e: confirmar())

    def _executar_guardar_cofre(self, senha, texto):
        from features.vault import NeuralVault
        try:
            vault = NeuralVault(senha)
            encrypted = vault.proteger(texto)
            
            os.makedirs("data", exist_ok=True)
            with open("data/vault.r2", "w") as f:
                f.write(encrypted)
            
            self._print_system_msg("✅ Dados criptografados e armazenados no cofre.")
            if VOZ_ATIVA: falar("Dados protegidos com sucesso.")
        except Exception as e:
            self._print_system_msg(f"❌ Falha no Protocolo de Segurança: {e}")

    def _executar_leitura_cofre(self, senha):
        from features.vault import NeuralVault
        if not os.path.exists("data/vault.r2"):
            self._print_system_msg("⚠️ Cofre vazio. Nenhum dado encontrado.")
            return

        try:
            with open("data/vault.r2", "r") as f:
                token = f.read()
            
            vault = NeuralVault(senha)
            decrypted = vault.descriptografar(token)
            
            if decrypted:
                self._print_ai_msg(f"🔓 CONTEÚDO DO COFRE:\n\n{decrypted}")
                if VOZ_ATIVA: falar("Autenticação aceita. Exibindo dados confidenciais.")
            else:
                self._print_system_msg("❌ ACESSO NEGADO: Chave Mestra inválida.")
                if VOZ_ATIVA: falar("Chave mestra inválida. Acesso negado.")
        except Exception as e:
            self._print_system_msg(f"💥 Erro crítico no Cofre: {e}")

    def _print_clickable_msg(self, text, sender="R2"):
        """Imprime links clicáveis na GUI e manda texto pro Telegram"""
        import re
        import webbrowser
        
        # Lógica GUI PC (Mantém igual)
        self.console_text.configure(state="normal")
        tag = "ai" if sender == "R2" else "user"
        self.console_text.insert("end", f"\n\n{sender}> ", tag)
        
        parts = re.split(r"(https?://\S+)", text)
        for part in parts:
            if part.startswith("http"):
                tag_link = f"link_{len(self.console_text.get('1.0', 'end'))}"
                self.console_text.insert("end", part, tag_link)
                try:
                    self.console_text._textbox.tag_config(tag_link, foreground="#00ffff", underline=True)
                    self.console_text._textbox.tag_bind(tag_link, "<Button-1>", lambda e, url=part: webbrowser.open(url))
                    self.console_text._textbox.tag_bind(tag_link, "<Enter>", lambda e: self.console_text.configure(cursor="hand2"))
                    self.console_text._textbox.tag_bind(tag_link, "<Leave>", lambda e: self.console_text.configure(cursor="arrow"))
                except: pass
            else:
                self.console_text.insert("end", part)
        self.console_text.configure(state="disabled")
        self.console_text.see("end")

        # --- ENVIA PARA O TELEGRAM (NOVO) ---
        # O Telegram já converte links automaticamente, então mandamos o texto puro
        if hasattr(self, 'telegram_bot') and self.telegram_bot:
            self.telegram_bot.enviar_mensagem_ativa(f"📡 [INTEL]:\n{text}")

    def _print_user_msg(self, msg):
        self.console_text.configure(state="normal")
        self.console_text.insert("end", f"\nVOCÊ> {msg}\n", "user")
        self.console_text.see("end")
        self.console_text.configure(state="disabled")

    def _print_ai_msg(self, msg):
        # Exibe na tela do PC
        self.console_text.configure(state="normal")
        self.console_text.insert("end", f"\nR2> {msg}\n", "ai")
        self.console_text.see("end")
        self.console_text.configure(state="disabled")

        # --- ENVIA PARA O TELEGRAM ---
        if hasattr(self, 'telegram_bot') and self.telegram_bot:
            # Adiciona emoji para ficar bonito no celular
            self.telegram_bot.enviar_mensagem_ativa(f"🤖 [R2]: {msg}")

    def _print_system_msg(self, msg):
        # Exibe na tela do PC
        self.console_text.configure(state="normal")
        self.console_text.insert("end", f"\n[SISTEMA]: {msg}\n", "sys")
        self.console_text.see("end")
        self.console_text.configure(state="disabled")

        # --- ENVIA PARA O TELEGRAM ---
        if hasattr(self, 'telegram_bot') and self.telegram_bot:
            self.telegram_bot.enviar_mensagem_ativa(f"💻 [SISTEMA]: {msg}")
        
    def _handle_animation_command(self, command):
        """Processa comandos de animação"""
        parts = command.lower().split()
        
        if len(parts) == 1:
            self._print_system_msg("Uso: animar [on/off/radar/particulas]")
        elif parts[1] == 'on':
            if not self.animator:
                self._print_system_msg("❌ Sistema de animações não disponível")
            else:
                self._print_system_msg("✅ Todas as animações ativadas")
        elif parts[1] == 'off':
            self._print_system_msg("⚠️  Animações desativadas (interface básica)")
        elif parts[1] == 'radar':
            self._print_system_msg("🎯 Radar: Modo automático ativado")
        elif parts[1] == 'particulas':
            self._print_system_msg("✨ Sistema de partículas: Máximo desempenho")
        else:
            self._print_system_msg(f"Comando de animação não reconhecido: {parts[1]}")

    def _on_close(self):
        """Desliga tudo antes de fechar a janela"""
        self.running = False # Avisa todas as animações para pararem
        try:
            if hasattr(self, 'ears') and self.ears:
                self.ears.stop_listening()
        except:
            pass
        self.destroy() # Fecha a janela
        sys.exit(0)    # Mata o processo Python

    def quit(self):
        """Encerra o aplicativo corretamente"""
        for a in self.active_animations:
            try: a.stop()
            except: pass
        super().quit()

def main():
    """Função principal"""
    print("✅ Sistema de animações: PRONTO")
    print("✅ GUI Sci-Fi: CARREGADA")
    print("🎬 Inicializando GUI Sci-Fi Conectada...")
    
    # Configuração
    config = {
        "app_name": "R2 Assistant - Com Animações",
        "version": "2.1",
        "theme": "sci_fi",
        "animations": True,
        "performance": "balanced"
    }
    
    # Criar e executar GUI
    app = R2SciFiGUIWithAnimations(config)
    
    # Centralizar janela
    app.update_idletasks()
    width = app.winfo_width()
    height = app.winfo_height()
    x = (app.winfo_screenwidth() // 2) - (width // 2)
    y = (app.winfo_screenheight() // 2) - (height // 2)
    app.geometry(f"{width}x{height}+{x}+{y}")
    
    print("🚀 GUI Sci-Fi com animações iniciada!")
    app.mainloop()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ ERRO CRÍTICO: {e}")
        traceback.print_exc()
        input("\nPressione Enter para sair...")
