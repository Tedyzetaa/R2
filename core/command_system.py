import sys
import threading
import asyncio
from datetime import datetime
from core.module_manager import ModuleManager
# Importe o gerenciador de IA que configuramos antes
from features.ai_integration.openrouter_client import AIIntegrationManager

class CommandSystem:
    def __init__(self, config):
        self.config = config
        self.module_manager = ModuleManager(config)
        
        # Inicializa a IA dentro do sistema de comandos
        try:
            self.ai_manager = AIIntegrationManager(config)
            # Tenta inicializar a conexão (se for necessário no seu código)
            asyncio.run(self.ai_manager.initialize()) if hasattr(self.ai_manager, 'initialize') else None
            self.ai_active = True
        except Exception as e:
            print(f"⚠️ Aviso: IA não pôde ser iniciada no terminal: {e}")
            self.ai_active = False

        # Comandos Nativos
        self.commands = {
            '/help': self._cmd_help,
            '/status': self._cmd_status,
            '/exit': self._cmd_exit,
            '/clear': self._cmd_clear,
            'ajuda': self._cmd_help, # Alias em PT
            'sair': self._cmd_exit     # Alias em PT
        }

    def process_command(self, user_input: str):
        """
        Processa a entrada. Se começar com '/', é comando.
        Caso contrário, é conversa com a IA.
        """
        if not user_input or user_input.strip() == "":
            return False, ""

        # 1. Se for um comando de sistema (começa com / ou palavras reservadas exatas)
        command_key = user_input.split()[0].lower()
        
        if user_input.startswith('/') or command_key in self.commands:
            # Remove a barra se tiver
            clean_cmd = command_key if not command_key.startswith('/') else command_key
            # Mapeia '/help' -> '/help' ou 'ajuda' -> '/help' se necessário
            # Simplificação: Busca direta
            
            if command_key in self.commands:
                return self.commands[command_key](user_input)
            elif f"/{command_key}" in self.commands:
                return self.commands[f"/{command_key}"](user_input)
            else:
                return False, f"Comando desconhecido: {user_input}. Digite /help."

        # 2. Se NÃO for comando, envia para a IA (Chat)
        else:
            if self.ai_active:
                return self._chat_with_ai(user_input)
            else:
                return False, "IA Offline. Digite comandos ou inicie a IA."

    def _chat_with_ai(self, message: str):
        """Ponte síncrona para a IA assíncrona"""
        print("R2 (Pensando)... 🧠") # Feedback visual
        try:
            # Como command_system roda em loop normal, precisamos rodar o async da IA aqui
            # Criamos um loop de evento temporário para aguardar a resposta
            response = asyncio.run(self.ai_manager.chat("terminal_user", message))
            
            # Formata a saída para o terminal ficar bonito
            return True, f"\n[R2]: {response.content}\n"
            
        except Exception as e:
            return False, f"Erro na IA: {e}"

    # --- Implementação dos Comandos ---

    def _cmd_help(self, args):
        help_text = """
        ╔════ COMANDOS DISPONÍVEIS ════╗
        ║ /help, ajuda  - Exibe isso   ║
        ║ /status       - Status do PC ║
        ║ /clear        - Limpa tela   ║
        ║ /exit, sair   - Fecha o R2   ║
        ╚══════════════════════════════╝
        💡 Para conversar, apenas digite normalmente.
        """
        return True, help_text

    def _cmd_status(self, args):
        import psutil
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        return True, f"📊 STATUS: CPU {cpu}% | RAM {ram}%"

    def _cmd_clear(self, args):
        import os
        os.system('cls' if os.name == 'nt' else 'clear')
        return True, "Terminal limpo."

    def _cmd_exit(self, args):
        print("Desligando sistemas...")
        sys.exit(0)

    def run_interactive(self):
        """Loop principal do terminal"""
        print("\n🔵 Terminal Interativo R2 Iniciado. Digite /help ou converse.")
        while True:
            try:
                user_input = input("\nR2> ")
                success, response = self.process_command(user_input)
                
                # A resposta da IA já vem formatada do método _chat_with_ai
                if response:
                    print(response)
                    
            except KeyboardInterrupt:
                print("\nInterrupção detectada.")
                break
            except Exception as e:
                print(f"Erro crítico no loop: {e}")