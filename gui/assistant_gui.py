import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import logging
from datetime import datetime

# Importação condicional do módulo de trading
try:
    from trading.ui.trading_gui import TradingGUI
    TRADING_AVAILABLE = True
except ImportError as e:
    print(f"Módulo de trading não disponível: {e}")
    TRADING_AVAILABLE = False

class AssistantGUI:
    def __init__(self, command_system, audio_processor, voice_engine, trading_engine=None):
        self.command_system = command_system
        self.audio_processor = audio_processor
        self.voice_engine = voice_engine
        self.trading_engine = trading_engine
        self.logger = logging.getLogger(__name__)
        
        self.setup_gui()
        
    def setup_gui(self):
        """Configura a interface gráfica principal"""
        self.root = tk.Tk()
        self.root.title("R2 Assistant - Assistente Pessoal")
        self.root.geometry("1000x700")
        
        # Configura estilo
        self.setup_styles()
        
        # Cria notebook (abas)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Aba principal
        self.setup_main_tab()
        
        # Aba de trading (se disponível)
        if TRADING_AVAILABLE and self.trading_engine:
            self.setup_trading_tab()
        
        # Aba de comandos
        self.setup_commands_tab()
        
        # Status bar
        self.setup_status_bar()
        
    def setup_styles(self):
        """Configura estilos da interface"""
        style = ttk.Style()
        style.theme_use('clam')
        
    def setup_main_tab(self):
        """Configura aba principal"""
        main_frame = ttk.Frame(self.notebook)
        self.notebook.add(main_frame, text="Principal")
        
        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        
        title_label = ttk.Label(
            header_frame, 
            text="🤖 R2 Assistant", 
            font=('Arial', 18, 'bold')
        )
        title_label.pack(side=tk.LEFT)
        
        # Controles de voz
        voice_frame = ttk.LabelFrame(main_frame, text="Controle de Voz", padding=10)
        voice_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.voice_status_var = tk.StringVar(value="🔴 Escuta Parada")
        voice_status = ttk.Label(voice_frame, textvariable=self.voice_status_var, font=('Arial', 12))
        voice_status.pack(side=tk.LEFT, padx=5)
        
        self.listen_btn = ttk.Button(
            voice_frame, 
            text="🎤 Iniciar Escuta", 
            command=self.toggle_listening
        )
        self.listen_btn.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            voice_frame,
            text="🗣️ Falar Agora",
            command=self.speak_now
        ).pack(side=tk.LEFT, padx=5)
        
        # Área de conversa
        conv_frame = ttk.LabelFrame(main_frame, text="Conversa", padding=10)
        conv_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.conversation_text = scrolledtext.ScrolledText(
            conv_frame, 
            wrap=tk.WORD, 
            width=80, 
            height=20,
            font=('Arial', 10)
        )
        self.conversation_text.pack(fill=tk.BOTH, expand=True)
        self.conversation_text.config(state=tk.DISABLED)
        
        # Entrada de texto
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.input_var = tk.StringVar()
        input_entry = ttk.Entry(
            input_frame, 
            textvariable=self.input_var, 
            font=('Arial', 10)
        )
        input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        input_entry.bind('<Return>', self.process_text_input)
        
        ttk.Button(
            input_frame, 
            text="Enviar", 
            command=self.process_text_input
        ).pack(side=tk.RIGHT, padx=5)
        
    def setup_trading_tab(self):
        """Configura aba de trading"""
        if not TRADING_AVAILABLE or not self.trading_engine:
            return
            
        trading_frame = ttk.Frame(self.notebook)
        self.notebook.add(trading_frame, text="📈 Trading")
        
        # Inicializa interface de trading
        self.trading_gui = TradingGUI(trading_frame, self.trading_engine, self.audio_processor)
        
    def setup_commands_tab(self):
        """Configura aba de comandos disponíveis"""
        commands_frame = ttk.Frame(self.notebook)
        self.notebook.add(commands_frame, text="Comandos")
        
        # Lista de comandos
        commands_text = scrolledtext.ScrolledText(
            commands_frame, 
            wrap=tk.WORD,
            font=('Arial', 10)
        )
        commands_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Adiciona comandos disponíveis
        commands = self.command_system.get_available_commands()
        commands_text.insert(tk.END, "Comandos disponíveis:\n\n")
        
        for cmd in commands:
            commands_text.insert(tk.END, f"• {cmd['trigger']}: {cmd['description']}\n")
        
        commands_text.config(state=tk.DISABLED)
        
    def setup_status_bar(self):
        """Configura barra de status"""
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_var = tk.StringVar(value="Pronto")
        status_label = ttk.Label(status_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_label.pack(fill=tk.X, padx=10, pady=2)
        
    def toggle_listening(self):
        """Alterna estado da escuta de voz"""
        if self.voice_engine.get_listening_status():
            self.voice_engine.stop_listening()
            self.voice_status_var.set("🔴 Escuta Parada")
            self.listen_btn.config(text="🎤 Iniciar Escuta")
            self.update_status("Escuta parada")
        else:
            if self.voice_engine.start_listening(self.voice_callback):
                self.voice_status_var.set("🟢 Escutando...")
                self.listen_btn.config(text="⏹️ Parar Escuta")
                self.update_status("Escutando comandos de voz")
            else:
                self.update_status("Erro: Sistema de voz não disponível")
                
    def voice_callback(self, text):
        """Callback para comandos de voz"""
        self.add_to_conversation(f"Você: {text}")
        
        # Processa comando em thread separada
        threading.Thread(
            target=self.process_voice_command,
            args=(text,),
            daemon=True
        ).start()
        
    def process_voice_command(self, text):
        """Processa comando de voz"""
        try:
            self.update_status(f"Processando: {text}")
            
            # Executa comando
            success = self.command_system.execute_command(
                text,
                self.audio_processor.text_to_speech,
                self.voice_engine.listen_once
            )
            
            if not success:
                self.audio_processor.text_to_speech("Desculpe, não entendi esse comando.")
                self.add_to_conversation("R2: Desculpe, não entendi esse comando.")
                
        except Exception as e:
            self.logger.error(f"Erro processando comando: {e}")
            self.add_to_conversation(f"R2: Erro ao processar comando: {e}")
            
    def process_text_input(self, event=None):
        """Processa entrada de texto"""
        text = self.input_var.get().strip()
        if not text:
            return
            
        self.add_to_conversation(f"Você: {text}")
        self.input_var.set("")
        
        # Processa em thread separada
        threading.Thread(
            target=self.process_voice_command,
            args=(text,),
            daemon=True
        ).start()
        
    def speak_now(self):
        """Fala texto imediatamente"""
        text = self.input_var.get().strip()
        if text:
            self.audio_processor.text_to_speech(text)
            self.add_to_conversation(f"R2: {text}")
            self.input_var.set("")
        
    def add_to_conversation(self, text):
        """Adiciona texto à conversa"""
        def update():
            self.conversation_text.config(state=tk.NORMAL)
            self.conversation_text.insert(tk.END, f"{text}\n")
            self.conversation_text.see(tk.END)
            self.conversation_text.config(state=tk.DISABLED)
            
        self.root.after(0, update)
        
    def update_status(self, message):
        """Atualiza barra de status"""
        def update():
            self.status_var.set(f"{datetime.now().strftime('%H:%M:%S')} - {message}")
            
        self.root.after(0, update)
        
    def run(self):
        """Inicia a interface"""
        self.update_status("R2 Assistant inicializado e pronto")
        self.root.mainloop()