import tkinter as tk
from tkinter import scrolledtext, ttk
import threading
import logging
from typing import Optional, Callable

class AssistantGUI:
    def __init__(self, command_system, audio_processor, voice_engine):
        self.root = tk.Tk()
        self.command_system = command_system
        self.audio_processor = audio_processor
        self.voice_engine = voice_engine
        self.is_listening = False
        
        self._setup_gui()
        self._setup_logging()

    def _setup_gui(self):
        """Configuração mínima da interface."""
        self.root.title("R2 - Assistente Pessoal")
        self.root.geometry("600x400")
        
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Área de chat
        self.chat_area = scrolledtext.ScrolledText(
            main_frame, 
            wrap=tk.WORD,
            height=20,
            font=('Arial', 10)
        )
        self.chat_area.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Frame de entrada
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(fill=tk.X)

        self.input_entry = ttk.Entry(input_frame, font=('Arial', 12))
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.input_entry.bind('<Return>', self._on_send_message)

        # Botões
        self.listen_btn = ttk.Button(
            input_frame,
            text="🎤 Ouvir",
            command=self._toggle_listening
        )
        self.listen_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.send_btn = ttk.Button(
            input_frame,
            text="Enviar",
            command=self._on_send_message
        )
        self.send_btn.pack(side=tk.LEFT)

        self._add_message("Sistema", "R2 inicializado. Digite 'ajuda' para ver comandos.")

    def _setup_logging(self):
        """Configura logging simples."""
        class TextHandler(logging.Handler):
            def __init__(self, text_widget):
                super().__init__()
                self.text_widget = text_widget

            def emit(self, record):
                msg = self.format(record)
                self.text_widget.insert(tk.END, f"{msg}\n")
                self.text_widget.see(tk.END)

        text_handler = TextHandler(self.chat_area)
        text_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(levelname)s: %(message)s')
        text_handler.setFormatter(formatter)
        logging.getLogger().addHandler(text_handler)

    def _add_message(self, sender: str, message: str):
        """Adiciona mensagem ao chat."""
        self.chat_area.insert(tk.END, f"{sender}: {message}\n")
        self.chat_area.see(tk.END)

    def _on_send_message(self, event=None):
        """Processa mensagem do usuário."""
        message = self.input_entry.get().strip()
        if message:
            self.input_entry.delete(0, tk.END)
            self._add_message("Você", message)
            self._process_command(message)

    def _toggle_listening(self):
        """Alterna escuta de forma ultra-simples."""
        try:
            if not self.is_listening:
                # Ativa escuta
                self.is_listening = True
                self.listen_btn.config(text="🔴 Parar")
                self._add_message("Sistema", "Escutando...")
                
                # Inicia escuta em thread
                def start_listen():
                    success = self.voice_engine.start_listening(self._on_voice_command)
                    if not success:
                        self.root.after(0, self._reset_listening)
                
                threading.Thread(target=start_listen, daemon=True).start()
            else:
                # Desativa escuta
                self._reset_listening()
                self.voice_engine.stop_listening()
                
        except Exception as e:
            logging.error(f"Erro ao alternar escuta: {e}")
            self._reset_listening()

    def _reset_listening(self):
        """Reseta estado de escuta."""
        self.is_listening = False
        self.listen_btn.config(text="🎤 Ouvir")
        self._add_message("Sistema", "Escuta parada")

    def _on_voice_command(self, text: str):
        """Processa comando de voz."""
        self.root.after(0, lambda: self._process_voice_ui(text))

    def _process_voice_ui(self, text: str):
        """Processa voz na thread UI."""
        self._add_message("Você (voz)", text)
        self._process_command(text)

    def _process_command(self, command: str):
        """Processa comando em thread separada."""
        def process():
            try:
                success = self.command_system.execute_command(
                    command, 
                    self.audio_processor.text_to_speech,
                    self.voice_engine.listen_once
                )
                
                if not success:
                    self.audio_processor.text_to_speech("Comando não reconhecido")
            except Exception as e:
                logging.error(f"Erro processando comando: {e}")

        threading.Thread(target=process, daemon=True).start()

    def run(self):
        """Inicia a interface."""
        try:
            self.root.mainloop()
        finally:
            self.voice_engine.stop_listening()