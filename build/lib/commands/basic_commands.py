"""
Comandos Básicos do Sistema
Comandos essenciais para interação e diagnóstico
"""

import logging
import time
import os
import sys
import platform
import subprocess
from datetime import datetime
from typing import Optional, List
from . import Command, CommandResult, CommandContext, CommandCategory, CommandPermission

logger = logging.getLogger(__name__)

class PingCommand(Command):
    """Comando ping para verificar resposta do sistema"""
    
    def __init__(self):
        super().__init__(
            name="ping",
            description="Verifica se o sistema está respondendo",
            category=CommandCategory.BASIC,
            permission=CommandPermission.GUEST,
            aliases=["pong", "echo"],
            usage="ping [--count N]",
            examples=["ping", "ping --count 5"]
        )
    
    async def execute(self, context: CommandContext, *args, **kwargs) -> CommandResult:
        count = 1
        
        # Parse arguments
        if "--count" in args:
            try:
                idx = args.index("--count")
                count = int(args[idx + 1])
            except (ValueError, IndexError):
                pass
        
        messages = []
        for i in range(count):
            messages.append(f"Pong! ({i + 1}/{count})")
            if i < count - 1:
                time.sleep(0.5)
        
        return CommandResult(
            success=True,
            message="\n".join(messages),
            data={"pings": count, "timestamp": time.time()}
        )

class HelpCommand(Command):
    """Exibe ajuda sobre comandos disponíveis"""
    
    def __init__(self, registry):
        super().__init__(
            name="help",
            description="Exibe ajuda sobre comandos",
            category=CommandCategory.BASIC,
            permission=CommandPermission.GUEST,
            aliases=["?", "ajuda", "comandos"],
            usage="help [comando|categoria]",
            examples=["help", "help system", "help ping"]
        )
        self.registry = registry
    
    async def execute(self, context: CommandContext, *args, **kwargs) -> CommandResult:
        if not args:
            # Listar todas as categorias
            categories = {}
            for cmd in self.registry.get_all_commands():
                if cmd.category not in categories:
                    categories[cmd.category] = []
                categories[cmd.category].append(cmd)
            
            help_text = "📚 COMANDOS DISPONÍVEIS\n\n"
            for category, commands in sorted(categories.items(), key=lambda x: x[0].value):
                help_text += f"📁 {category.value.upper()}:\n"
                for cmd in sorted(commands, key=lambda x: x.name):
                    help_text += f"  • {cmd.name}: {cmd.description}\n"
                help_text += "\n"
            
            help_text += "Use 'help [categoria]' para ver comandos de uma categoria específica\n"
            help_text += "Use 'help [comando]' para detalhes de um comando específico"
            
            return CommandResult(
                success=True,
                message=help_text,
                data={"categories": [c.value for c in categories.keys()]}
            )
        
        # Buscar por categoria
        arg = args[0].lower()
        for category in CommandCategory:
            if arg == category.value:
                commands = self.registry.get_commands_by_category(category)
                if not commands:
                    return CommandResult(
                        success=False,
                        message=f"Nenhum comando encontrado na categoria: {arg}"
                    )
                
                help_text = f"📁 COMANDOS {category.value.upper()}:\n\n"
                for cmd in sorted(commands, key=lambda x: x.name):
                    help_text += f"📌 {cmd.name.upper()}\n"
                    help_text += f"   Descrição: {cmd.description}\n"
                    if cmd.aliases:
                        help_text += f"   Aliases: {', '.join(cmd.aliases)}\n"
                    help_text += f"   Uso: {cmd.usage}\n"
                    if cmd.examples:
                        help_text += f"   Exemplos:\n"
                        for ex in cmd.examples:
                            help_text += f"     {ex}\n"
                    help_text += "\n"
                
                return CommandResult(
                    success=True,
                    message=help_text,
                    data={"category": category.value, "command_count": len(commands)}
                )
        
        # Buscar por comando
        command = self.registry.get(arg)
        if command:
            help_text = f"📖 AJUDA: {command.name.upper()}\n\n"
            help_text += f"📝 Descrição: {command.description}\n"
            help_text += f"🏷️  Categoria: {command.category.value}\n"
            help_text += f"🔐 Permissão: {command.permission.value}\n"
            
            if command.aliases:
                help_text += f"🔄 Aliases: {', '.join(command.aliases)}\n"
            
            help_text += f"🛠️  Uso: {command.usage}\n"
            
            if command.examples:
                help_text += f"💡 Exemplos:\n"
                for ex in command.examples:
                    help_text += f"  $ {ex}\n"
            
            return CommandResult(
                success=True,
                message=help_text,
                data={
                    "command": command.name,
                    "category": command.category.value,
                    "permission": command.permission.value
                }
            )
        
        return CommandResult(
            success=False,
            message=f"Categoria ou comando não encontrado: {arg}"
        )

class EchoCommand(Command):
    """Repete a mensagem fornecida"""
    
    def __init__(self):
        super().__init__(
            name="echo",
            description="Repete a mensagem fornecida",
            category=CommandCategory.BASIC,
            permission=CommandPermission.GUEST,
            aliases=["repeat", "say"],
            usage="echo <mensagem>",
            examples=["echo Hello World", "echo 'Mensagem com espaços'"]
        )
    
    async def execute(self, context: CommandContext, *args, **kwargs) -> CommandResult:
        if not args:
            return CommandResult(
                success=False,
                message="Forneça uma mensagem para repetir",
                error="No message provided"
            )
        
        message = " ".join(args)
        return CommandResult(
            success=True,
            message=message,
            data={"original_message": message}
        )

class TimeCommand(Command):
    """Exibe data e hora atuais"""
    
    def __init__(self):
        super().__init__(
            name="time",
            description="Exibe data e hora atuais",
            category=CommandCategory.BASIC,
            permission=CommandPermission.GUEST,
            aliases=["date", "hora", "datetime"],
            usage="time [--format <formato>]",
            examples=["time", "time --format '%Y-%m-%d'", "time --format '%H:%M:%S'"]
        )
    
    async def execute(self, context: CommandContext, *args, **kwargs) -> CommandResult:
        format_str = "%Y-%m-%d %H:%M:%S"
        
        # Parse arguments
        if "--format" in args:
            try:
                idx = args.index("--format")
                format_str = args[idx + 1]
            except IndexError:
                pass
        
        current_time = datetime.now()
        formatted_time = current_time.strftime(format_str)
        
        return CommandResult(
            success=True,
            message=f"🕒 {formatted_time}",
            data={
                "timestamp": current_time.timestamp(),
                "formatted": formatted_time,
                "iso_format": current_time.isoformat(),
                "timezone": str(current_time.astimezone().tzinfo)
            }
        )

class ClearCommand(Command):
    """Limpa a tela/console"""
    
    def __init__(self):
        super().__init__(
            name="clear",
            description="Limpa a tela/console",
            category=CommandCategory.BASIC,
            permission=CommandPermission.GUEST,
            aliases=["cls", "limpar"],
            usage="clear",
            examples=["clear"]
        )
    
    async def execute(self, context: CommandContext, *args, **kwargs) -> CommandResult:
        # Sistema operacional específico
        if platform.system() == "Windows":
            os.system('cls')
        else:
            os.system('clear')
        
        return CommandResult(
            success=True,
            message="Tela limpa",
            data={"action": "screen_cleared"}
        )

class HistoryCommand(Command):
    """Exibe histórico de comandos"""
    
    def __init__(self, processor):
        super().__init__(
            name="history",
            description="Exibe histórico de comandos",
            category=CommandCategory.BASIC,
            permission=CommandPermission.USER,
            aliases=["hist", "historico"],
            usage="history [--limit N] [--user <user_id>]",
            examples=["history", "history --limit 10", "history --user system"]
        )
        self.processor = processor
    
    async def execute(self, context: CommandContext, *args, **kwargs) -> CommandResult:
        limit = 20
        user_id = None
        
        # Parse arguments
        i = 0
        while i < len(args):
            if args[i] == "--limit" and i + 1 < len(args):
                try:
                    limit = int(args[i + 1])
                    i += 1
                except ValueError:
                    pass
            elif args[i] == "--user" and i + 1 < len(args):
                user_id = args[i + 1]
                i += 1
            i += 1
        
        history = await self.processor.get_history(user_id=user_id, limit=limit)
        
        if not history:
            return CommandResult(
                success=True,
                message="Histórico vazio",
                data={"empty": True}
            )
        
        history_text = "📜 HISTÓRICO DE COMANDOS\n\n"
        for i, entry in enumerate(reversed(history), 1):
            timestamp = datetime.fromtimestamp(entry['timestamp']).strftime("%H:%M:%S")
            cmd = entry['command'][:50] + ("..." if len(entry['command']) > 50 else "")
            user = entry['username']
            success = "✅" if entry['result']['success'] else "❌"
            
            history_text += f"{i:3d}. [{timestamp}] {user}: {cmd} {success}\n"
        
        return CommandResult(
            success=True,
            message=history_text,
            data={
                "history": history,
                "count": len(history),
                "user_filter": user_id
            }
        )

class BasicCommands:
    """Classe container para comandos básicos"""
    
    def __init__(self, registry, processor):
        self.registry = registry
        self.processor = processor
        
        # Registrar comandos
        self.commands = [
            PingCommand(),
            HelpCommand(registry),
            EchoCommand(),
            TimeCommand(),
            ClearCommand(),
            HistoryCommand(processor)
        ]
        
        for cmd in self.commands:
            registry.register(cmd)
        
        logger.info(f"{len(self.commands)} comandos básicos registrados")
    
    def get_commands(self):
        """Retorna lista de comandos registrados"""
        return self.commands