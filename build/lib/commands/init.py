"""
Sistema de Comandos do R2 Assistant
Arquitetura modular para processamento e execução de comandos
"""

from .basic_commands import BasicCommands
from .system_commands import SystemCommands
from .web_commands import WebCommands
from .crypto_commands import CryptoCommands
from .voice_commands import VoiceCommands
from .media_commands import MediaCommands
from .trading_commands import TradingCommands

__version__ = "1.0.0"
__author__ = "R2 Assistant Team"

# Exportar todos os módulos
__all__ = [
    'BasicCommands',
    'SystemCommands',
    'WebCommands',
    'CryptoCommands',
    'VoiceCommands',
    'MediaCommands',
    'TradingCommands',
    'CommandRegistry',
    'CommandProcessor',
    'CommandContext',
    'CommandResult'
]

# Classes principais do sistema de comandos
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Union
import time
import asyncio

logger = logging.getLogger(__name__)

class CommandCategory(Enum):
    """Categorias de comandos"""
    SYSTEM = "system"
    BASIC = "basic"
    WEB = "web"
    CRYPTO = "crypto"
    VOICE = "voice"
    MEDIA = "media"
    TRADING = "trading"
    UTILITY = "utility"

class CommandPermission(Enum):
    """Níveis de permissão para comandos"""
    GUEST = "guest"      # Usuário não autenticado
    USER = "user"        # Usuário básico
    ADMIN = "admin"      # Administrador
    SYSTEM = "system"    # Sistema interno

@dataclass
class CommandContext:
    """Contexto de execução do comando"""
    user_id: str
    username: str
    permission: CommandPermission
    channel: str  # 'cli', 'gui', 'voice', 'api'
    session_id: str
    timestamp: float
    environment: Dict[str, Any]  # Variáveis de ambiente
    metadata: Dict[str, Any]     # Metadados adicionais
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

@dataclass
class CommandResult:
    """Resultado da execução de um comando"""
    success: bool
    message: str
    data: Optional[Any] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None
    timestamp: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte resultado para dicionário"""
        return {
            'success': self.success,
            'message': self.message,
            'data': self.data,
            'error': self.error,
            'execution_time': self.execution_time,
            'timestamp': self.timestamp,
            'metadata': self.metadata or {}
        }

class Command(ABC):
    """Classe base para todos os comandos"""
    
    def __init__(
        self,
        name: str,
        description: str,
        category: CommandCategory,
        permission: CommandPermission = CommandPermission.USER,
        aliases: Optional[List[str]] = None,
        usage: Optional[str] = None,
        examples: Optional[List[str]] = None
    ):
        self.name = name
        self.description = description
        self.category = category
        self.permission = permission
        self.aliases = aliases or []
        self.usage = usage or f"{name} [parâmetros]"
        self.examples = examples or []
        
    @abstractmethod
    async def execute(self, context: CommandContext, *args, **kwargs) -> CommandResult:
        """Executa o comando"""
        pass
    
    def can_execute(self, context: CommandContext) -> bool:
        """Verifica se o usuário tem permissão para executar"""
        # Mapear níveis de permissão para valores numéricos
        permission_levels = {
            CommandPermission.GUEST: 0,
            CommandPermission.USER: 1,
            CommandPermission.ADMIN: 2,
            CommandPermission.SYSTEM: 3
        }
        
        user_level = permission_levels.get(context.permission, 0)
        required_level = permission_levels.get(self.permission, 0)
        
        return user_level >= required_level

class CommandRegistry:
    """Registro central de comandos"""
    
    def __init__(self):
        self.commands: Dict[str, Command] = {}
        self.categories: Dict[CommandCategory, List[str]] = {}
        self._lock = asyncio.Lock()
        
    def register(self, command: Command):
        """Registra um novo comando"""
        async def _register():
            async with self._lock:
                # Registrar nome principal
                self.commands[command.name] = command
                
                # Registrar aliases
                for alias in command.aliases:
                    self.commands[alias] = command
                
                # Registrar por categoria
                if command.category not in self.categories:
                    self.categories[command.category] = []
                
                if command.name not in self.categories[command.category]:
                    self.categories[command.category].append(command.name)
                
                logger.info(f"Comando registrado: {command.name} ({command.category.value})")
        
        # Executar em thread existente
        asyncio.create_task(_register())
    
    def unregister(self, command_name: str):
        """Remove um comando do registro"""
        async def _unregister():
            async with self._lock:
                if command_name in self.commands:
                    command = self.commands.pop(command_name)
                    
                    # Remover aliases
                    for alias in command.aliases:
                        if alias in self.commands:
                            self.commands.pop(alias)
                    
                    # Remover da categoria
                    if command.category in self.categories:
                        if command.name in self.categories[command.category]:
                            self.categories[command.category].remove(command.name)
                    
                    logger.info(f"Comando removido: {command_name}")
        
        asyncio.create_task(_unregister())
    
    def get(self, command_name: str) -> Optional[Command]:
        """Obtém um comando pelo nome ou alias"""
        return self.commands.get(command_name.lower())
    
    def get_commands_by_category(self, category: CommandCategory) -> List[Command]:
        """Obtém todos os comandos de uma categoria"""
        commands = []
        for cmd_name in self.categories.get(category, []):
            cmd = self.commands.get(cmd_name)
            if cmd:
                commands.append(cmd)
        return commands
    
    def search(self, query: str) -> List[Command]:
        """Busca comandos por nome, alias ou descrição"""
        query = query.lower()
        results = []
        
        for cmd in self.commands.values():
            # Evitar duplicados (comandos com aliases)
            if cmd in results:
                continue
                
            if (query in cmd.name.lower() or
                any(query in alias.lower() for alias in cmd.aliases) or
                query in cmd.description.lower()):
                results.append(cmd)
        
        return results
    
    def get_all_commands(self) -> List[Command]:
        """Retorna todos os comandos únicos (sem duplicatas por alias)"""
        unique_commands = set()
        result = []
        
        for cmd in self.commands.values():
            if cmd not in unique_commands:
                unique_commands.add(cmd)
                result.append(cmd)
        
        return result

class CommandProcessor:
    """Processador de comandos com suporte assíncrono"""
    
    def __init__(self, registry: CommandRegistry):
        self.registry = registry
        self.history: List[Dict[str, Any]] = []
        self.max_history = 1000
        self._lock = asyncio.Lock()
        
        # Callbacks para eventos
        self.callbacks = {
            'before_execute': [],
            'after_execute': [],
            'on_error': []
        }
    
    async def process(
        self,
        command_str: str,
        context: CommandContext
    ) -> CommandResult:
        """
        Processa e executa um comando
        
        Args:
            command_str: String do comando (ex: "ping --count 5")
            context: Contexto de execução
            
        Returns:
            CommandResult com o resultado
        """
        start_time = time.time()
        
        try:
            # Parse do comando
            parts = command_str.strip().split()
            if not parts:
                return CommandResult(
                    success=False,
                    message="Comando vazio",
                    error="Empty command"
                )
            
            cmd_name = parts[0].lower()
            args = parts[1:] if len(parts) > 1 else []
            
            # Obter comando do registro
            command = self.registry.get(cmd_name)
            if not command:
                return CommandResult(
                    success=False,
                    message=f"Comando não encontrado: {cmd_name}",
                    error="Command not found"
                )
            
            # Verificar permissão
            if not command.can_execute(context):
                return CommandResult(
                    success=False,
                    message="Permissão insuficiente",
                    error=f"Requires {command.permission.value} permission"
                )
            
            # Disparar callbacks before_execute
            for callback in self.callbacks['before_execute']:
                try:
                    await callback(command, context, args)
                except Exception as e:
                    logger.error(f"Erro em callback before_execute: {e}")
            
            # Executar comando
            result = await command.execute(context, *args)
            result.execution_time = time.time() - start_time
            
            # Disparar callbacks after_execute
            for callback in self.callbacks['after_execute']:
                try:
                    await callback(command, context, args, result)
                except Exception as e:
                    logger.error(f"Erro em callback after_execute: {e}")
            
            # Registrar no histórico
            await self._add_to_history(command_str, context, result)
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_result = CommandResult(
                success=False,
                message=f"Erro ao executar comando: {str(e)}",
                error=str(e),
                execution_time=execution_time
            )
            
            # Disparar callbacks on_error
            for callback in self.callbacks['on_error']:
                try:
                    await callback(command_str, context, e, error_result)
                except Exception as e2:
                    logger.error(f"Erro em callback on_error: {e2}")
            
            # Registrar erro no histórico
            await self._add_to_history(command_str, context, error_result)
            
            return error_result
    
    async def _add_to_history(
        self,
        command_str: str,
        context: CommandContext,
        result: CommandResult
    ):
        """Adiciona execução ao histórico"""
        async with self._lock:
            history_entry = {
                'command': command_str,
                'user_id': context.user_id,
                'username': context.username,
                'timestamp': context.timestamp,
                'result': result.to_dict(),
                'session_id': context.session_id,
                'channel': context.channel
            }
            
            self.history.append(history_entry)
            
            # Limitar tamanho do histórico
            if len(self.history) > self.max_history:
                self.history = self.history[-self.max_history:]
    
    def register_callback(self, event: str, callback: Callable):
        """
        Registra callback para eventos
        
        Args:
            event: 'before_execute', 'after_execute', 'on_error'
            callback: Função callback
        """
        if event not in self.callbacks:
            raise ValueError(f"Evento inválido: {event}")
        
        self.callbacks[event].append(callback)
    
    async def get_history(
        self,
        user_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Obtém histórico de comandos com filtros"""
        async with self._lock:
            filtered_history = self.history
            
            if user_id:
                filtered_history = [
                    entry for entry in filtered_history
                    if entry['user_id'] == user_id
                ]
            
            return filtered_history[offset:offset + limit]
    
    async def clear_history(self, user_id: Optional[str] = None):
        """Limpa histórico de comandos"""
        async with self._lock:
            if user_id:
                self.history = [
                    entry for entry in self.history
                    if entry['user_id'] != user_id
                ]
            else:
                self.history = []
            
            logger.info(f"Histórico limpo para usuário: {user_id or 'todos'}")

# Instância global do registry
registry = CommandRegistry()
processor = CommandProcessor(registry)

# Função de conveniência para registrar comandos
def register_command(command: Command):
    """Registra um comando no registro global"""
    registry.register(command)

# Função de conveniência para processar comandos
async def execute_command(
    command_str: str,
    user_id: str = "system",
    username: str = "System",
    permission: CommandPermission = CommandPermission.SYSTEM,
    channel: str = "cli",
    **kwargs
) -> CommandResult:
    """
    Executa um comando com contexto padrão
    
    Args:
        command_str: Comando a ser executado
        user_id: ID do usuário
        username: Nome do usuário
        permission: Nível de permissão
        channel: Canal de execução
        **kwargs: Argumentos adicionais para o contexto
        
    Returns:
        Resultado da execução
    """
    context = CommandContext(
        user_id=user_id,
        username=username,
        permission=permission,
        channel=channel,
        session_id=f"session_{int(time.time())}",
        timestamp=time.time(),
        environment={},
        metadata=kwargs
    )
    
    return await processor.process(command_str, context)