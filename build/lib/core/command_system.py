"""
Command system for processing and executing user commands
"""

import re
import json
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
import time

class CommandType(Enum):
    VOICE = "voice"
    TEXT = "text"
    SYSTEM = "system"
    AI = "ai"
    CUSTOM = "custom"

@dataclass
class Command:
    """Command definition"""
    name: str
    pattern: str
    handler: Callable
    description: str
    command_type: CommandType
    enabled: bool = True
    requires_confirmation: bool = False
    parameters: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'name': self.name,
            'pattern': self.pattern,
            'description': self.description,
            'type': self.command_type.value,
            'enabled': self.enabled,
            'requires_confirmation': self.requires_confirmation,
            'parameters': self.parameters
        }

class CommandSystem:
    """
    Command processing and execution system
    """
    
    def __init__(self):
        self.commands: Dict[str, Command] = {}
        self.aliases: Dict[str, str] = {}  # alias -> command_name
        
        # Command history
        self.history: List[Dict[str, Any]] = []
        self.max_history = 100
        
        # Statistics
        self.stats = {
            'total_commands': 0,
            'successful': 0,
            'failed': 0,
            'avg_response_time': 0.0,
            'most_used_commands': {}
        }
        
        # Load built-in commands
        self._load_builtin_commands()
    
    def _load_builtin_commands(self):
        """Load built-in system commands"""
        
        # System commands
        self.register_command(
            name="help",
            pattern=r"^(ajuda|help|comandos|o que você pode fazer)$",
            handler=self._handle_help,
            description="Mostra esta mensagem de ajuda",
            command_type=CommandType.TEXT
        )
        
        self.register_command(
            name="time",
            pattern=r"^(que horas são|hora|horas)$",
            handler=self._handle_time,
            description="Mostra a hora atual",
            command_type=CommandType.TEXT
        )
        
        self.register_command(
            name="date",
            pattern=r"^(que dia é hoje|data|dia)$",
            handler=self._handle_date,
            description="Mostra a data atual",
            command_type=CommandType.TEXT
        )
        
        self.register_command(
            name="system_status",
            pattern=r"^(status do sistema|sistema|estado)$",
            handler=self._handle_system_status,
            description="Mostra o status do sistema",
            command_type=CommandType.TEXT
        )
        
        # Voice commands
        self.register_command(
            name="voice_toggle",
            pattern=r"^(ativa voz|desativa voz|liga microfone|desliga microfone)$",
            handler=self._handle_voice_toggle,
            description="Ativa/desativa reconhecimento de voz",
            command_type=CommandType.VOICE
        )
        
        self.register_command(
            name="voice_calibrate",
            pattern=r"^(calibra microfone|ajusta microfone|calibrar voz)$",
            handler=self._handle_voice_calibrate,
            description="Calibra o microfone para ruído ambiente",
            command_type=CommandType.VOICE
        )
        
        # AI commands
        self.register_command(
            name="ai_chat",
            pattern=r"^(ia|inteligência artificial|assistente|r2)$",
            handler=self._handle_ai_chat,
            description="Inicia conversa com a IA",
            command_type=CommandType.AI
        )
        
        print(f"✅ Loaded {len(self.commands)} built-in commands")
    
    def register_command(self, name: str, pattern: str, handler: Callable,
                        description: str, command_type: CommandType,
                        enabled: bool = True, requires_confirmation: bool = False,
                        parameters: Optional[Dict] = None):
        """Register a new command"""
        if name in self.commands:
            print(f"⚠️ Command '{name}' already registered, overwriting")
        
        self.commands[name] = Command(
            name=name,
            pattern=pattern,
            handler=handler,
            description=description,
            command_type=command_type,
            enabled=enabled,
            requires_confirmation=requires_confirmation,
            parameters=parameters or {}
        )
        
        print(f"📝 Registered command: {name} ({command_type.value})")
    
    def register_alias(self, alias: str, command_name: str):
        """Register an alias for a command"""
        if command_name not in self.commands:
            print(f"⚠️ Cannot create alias: Command '{command_name}' not found")
            return
        
        self.aliases[alias] = command_name
        print(f"🔗 Registered alias: '{alias}' -> '{command_name}'")
    
    def unregister_command(self, name: str):
        """Unregister a command"""
        if name in self.commands:
            del self.commands[name]
            
            # Remove aliases for this command
            aliases_to_remove = [a for a, c in self.aliases.items() if c == name]
            for alias in aliases_to_remove:
                del self.aliases[alias]
            
            print(f"🗑️ Unregistered command: {name}")
    
    def enable_command(self, name: str):
        """Enable a command"""
        if name in self.commands:
            self.commands[name].enabled = True
            print(f"✅ Enabled command: {name}")
    
    def disable_command(self, name: str):
        """Disable a command"""
        if name in self.commands:
            self.commands[name].enabled = False
            print(f"🚫 Disabled command: {name}")
    
    def process_command(self, input_text: str, 
                       command_type: CommandType = CommandType.TEXT) -> Tuple[bool, str]:
        """
        Process and execute a command
        
        Returns:
            Tuple of (success, result)
        """
        if not input_text or not input_text.strip():
            return False, "Empty command"
        
        start_time = time.time()
        input_text = input_text.strip().lower()
        
        # Update statistics
        self.stats['total_commands'] += 1
        
        # Check for aliases first
        if input_text in self.aliases:
            command_name = self.aliases[input_text]
            if command_name in self.commands:
                command = self.commands[command_name]
                
                # Check if command is enabled and matches type
                if not command.enabled:
                    return False, f"Command '{command.name}' is disabled"
                
                if command.command_type != command_type:
                    return False, f"Command '{command.name}' is not a {command_type.value} command"
                
                # Execute command
                return self._execute_command(command, input_text, start_time)
        
        # Search for matching command
        for command in self.commands.values():
            if not command.enabled or command.command_type != command_type:
                continue
            
            if re.match(command.pattern, input_text, re.IGNORECASE):
                return self._execute_command(command, input_text, start_time)
        
        # No command matched
        self.stats['failed'] += 1
        
        # Suggest similar commands
        suggestions = self._suggest_commands(input_text)
        if suggestions:
            suggestion_text = "\n".join([f"- {s}" for s in suggestions[:3]])
            return False, f"Comando não reconhecido. Sugestões:\n{suggestion_text}"
        
        return False, "Comando não reconhecido. Diga 'ajuda' para ver os comandos disponíveis."
    
    def _execute_command(self, command: Command, input_text: str, 
                        start_time: float) -> Tuple[bool, str]:
        """Execute a command and handle results"""
        try:
            # Extract parameters if any
            params = self._extract_parameters(input_text, command)
            
            # Execute handler
            result = command.handler(**params)
            execution_time = time.time() - start_time
            
            # Update statistics
            self.stats['successful'] += 1
            self.stats['avg_response_time'] = (
                (self.stats['avg_response_time'] * (self.stats['successful'] - 1) + execution_time)
                / self.stats['successful']
            )
            
            # Update command usage
            if command.name not in self.stats['most_used_commands']:
                self.stats['most_used_commands'][command.name] = 0
            self.stats['most_used_commands'][command.name] += 1
            
            # Add to history
            self._add_to_history(command.name, input_text, result, True)
            
            return True, str(result)
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.stats['failed'] += 1
            
            error_msg = f"Erro executando comando '{command.name}': {str(e)}"
            print(f"❌ {error_msg}")
            
            # Add to history
            self._add_to_history(command.name, input_text, error_msg, False)
            
            return False, error_msg
    
    def _extract_parameters(self, input_text: str, command: Command) -> Dict[str, Any]:
        """Extract parameters from command input"""
        params = {}
        
        if not command.parameters:
            return params
        
        # Use regex to extract named groups
        match = re.match(command.pattern, input_text, re.IGNORECASE)
        if match:
            params = match.groupdict()
        
        # Convert parameter types
        for param_name, param_value in params.items():
            if param_name in command.parameters:
                param_type = command.parameters[param_name].get('type', 'string')
                
                try:
                    if param_type == 'number':
                        params[param_name] = float(param_value)
                    elif param_type == 'integer':
                        params[param_name] = int(param_value)
                    elif param_type == 'boolean':
                        params[param_name] = param_value.lower() in ['true', 'sim', 'yes', '1']
                except ValueError:
                    # Keep as string if conversion fails
                    pass
        
        return params
    
    def _suggest_commands(self, input_text: str) -> List[str]:
        """Suggest similar commands based on input"""
        suggestions = []
        input_words = set(input_text.split())
        
        for command in self.commands.values():
            if not command.enabled:
                continue
            
            # Calculate similarity
            command_words = set(command.name.split('_'))
            description_words = set(command.description.lower().split())
            
            # Check for word matches
            matches = input_words.intersection(command_words.union(description_words))
            
            if matches:
                similarity = len(matches) / max(len(input_words), 1)
                if similarity > 0.3:  # 30% similarity threshold
                    suggestions.append(f"{command.name}: {command.description}")
        
        return suggestions[:5]  # Return top 5 suggestions
    
    def _add_to_history(self, command_name: str, input_text: str, 
                       result: str, success: bool):
        """Add command execution to history"""
        history_entry = {
            'timestamp': time.time(),
            'command': command_name,
            'input': input_text,
            'result': result,
            'success': success
        }
        
        self.history.append(history_entry)
        
        # Trim history
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
    
    def get_command_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get command execution history"""
        return self.history[-limit:] if limit else self.history
    
    def clear_history(self):
        """Clear command history"""
        self.history.clear()
        print("🧹 Command history cleared")
    
    # Built-in command handlers
    
    def _handle_help(self) -> str:
        """Handle help command"""
        help_text = "🤖 **COMANDOS DISPONÍVEIS**\n\n"
        
        # Group commands by type
        commands_by_type = {}
        for command in self.commands.values():
            if command.enabled:
                if command.command_type.value not in commands_by_type:
                    commands_by_type[command.command_type.value] = []
                commands_by_type[command.command_type.value].append(command)
        
        # Format help text
        for cmd_type, cmd_list in commands_by_type.items():
            help_text += f"**{cmd_type.upper()}**:\n"
            for cmd in cmd_list:
                help_text += f"• {cmd.name}: {cmd.description}\n"
            help_text += "\n"
        
        help_text += "\n💡 Use 'ajuda [comando]' para mais detalhes sobre um comando específico."
        
        return help_text
    
    def _handle_time(self) -> str:
        """Handle time command"""
        from datetime import datetime
        current_time = datetime.now().strftime("%H:%M:%S")
        return f"🕐 São {current_time}"
    
    def _handle_date(self) -> str:
        """Handle date command"""
        from datetime import datetime
        current_date = datetime.now().strftime("%d/%m/%Y")
        return f"📅 Hoje é {current_date}"
    
    def _handle_system_status(self) -> str:
        """Handle system status command"""
        import psutil
        
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        status_text = f"""
🖥️ **STATUS DO SISTEMA**

• CPU: {cpu_percent}% utilizada
• Memória: {memory.percent}% utilizada ({memory.used // (1024**3)}GB / {memory.total // (1024**3)}GB)
• Disco: {disk.percent}% utilizado ({disk.used // (1024**3)}GB / {disk.total // (1024**3)}GB)
• Comandos executados: {self.stats['total_commands']}
• Taxa de sucesso: {(self.stats['successful'] / max(self.stats['total_commands'], 1)) * 100:.1f}%
"""
        
        return status_text
    
    def _handle_voice_toggle(self) -> str:
        """Handle voice toggle command"""
        # This would connect to the voice engine
        return "🔊 Reconhecimento de voz alterado (implementação pendente)"
    
    def _handle_voice_calibrate(self) -> str:
        """Handle voice calibration command"""
        # This would connect to the voice engine
        return "🎤 Microfone calibrado (implementação pendente)"
    
    def _handle_ai_chat(self) -> str:
        """Handle AI chat command"""
        return "🧠 Modo de conversa com IA ativado. Faça sua pergunta!"
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get command system statistics"""
        return {
            **self.stats,
            'total_registered_commands': len(self.commands),
            'enabled_commands': len([c for c in self.commands.values() if c.enabled]),
            'total_aliases': len(self.aliases),
            'history_size': len(self.history)
        }
    
    def export_commands(self, filepath: str):
        """Export command definitions to file"""
        commands_data = {
            'commands': [c.to_dict() for c in self.commands.values()],
            'aliases': self.aliases,
            'statistics': self.get_statistics(),
            'history': self.get_command_history(50),
            'timestamp': time.time()
        }
        
        with open(filepath, 'w') as f:
            json.dump(commands_data, f, indent=2, ensure_ascii=False)
    
    def import_commands(self, filepath: str):
        """Import command definitions from file"""
        try:
            with open(filepath, 'r') as f:
                commands_data = json.load(f)
            
            # Note: This would need to re-register commands
            # Implementation depends on serialization format
            print(f"📥 Imported commands from {filepath}")
            
        except Exception as e:
            print(f"❌ Error importing commands: {e}")