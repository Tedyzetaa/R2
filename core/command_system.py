from typing import Dict, Callable, Any, List
import logging

class CommandSystem:
    def __init__(self):
        self.commands: Dict[str, Dict] = {}
        self.logger = logging.getLogger(__name__)

    def register_command(self, trigger: str, function: Callable, description: str = "", 
                        needs_confirmation: bool = False):
        """Registra um comando no sistema."""
        self.commands[trigger.lower()] = {
            'function': function,
            'description': description,
            'needs_confirmation': needs_confirmation
        }

    def execute_command(self, command_text: str, *args, **kwargs) -> bool:
        """Executa o comando correspondente ao texto."""
        command_text = command_text.lower().strip()
        command_found = False
        
        # Procura por comandos exatos primeiro
        if command_text in self.commands:
            command_found = True
            command_info = self.commands[command_text]
            try:
                command_info['function'](*args, **kwargs)
            except Exception as e:
                self.logger.error(f"Erro executando comando {command_text}: {e}")
                return False
        else:
            # Procura por comandos que começam com o texto
            for trigger, command_info in self.commands.items():
                if command_text.startswith(trigger):
                    command_found = True
                    try:
                        # Extrai argumentos do comando
                        args_text = command_text[len(trigger):].strip()
                        command_info['function'](args_text, *args, **kwargs)
                    except Exception as e:
                        self.logger.error(f"Erro executando comando {trigger}: {e}")
                        return False
                    break

        return command_found

    def get_available_commands(self) -> List[Dict]:
        """Retorna a lista de comandos disponíveis."""
        return [{'trigger': trigger, 'description': info['description']} 
                for trigger, info in self.commands.items()]

    def list_commands(self, falar_func: Callable):
        """Lista todos os comandos disponíveis."""
        commands = self.get_available_commands()
        if commands:
            falar_func("Comandos disponíveis:")
            for cmd in commands:
                falar_func(f"- {cmd['trigger']}: {cmd['description']}")
        else:
            falar_func("Nenhum comando registrado.")