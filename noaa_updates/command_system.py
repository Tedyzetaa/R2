"""
Sistema de Comandos - Atualizado para NOAA
"""

import asyncio
import importlib.util
from typing import Dict, List, Any, Optional, Callable

class CommandSystem:
    """Sistema de gerenciamento de comandos"""
    
    def __init__(self):
        self.commands: Dict[str, Dict] = {}
        self.categories = {
            "system": "Comandos do Sistema",
            "noaa": "Clima Espacial NOAA",
            "media": "Mídia e Entretenimento",
            "tools": "Ferramentas",
            "ai": "Inteligência Artificial"
        }
        
        self._register_builtin_commands()
    
    def _register_builtin_commands(self):
        """Registra comandos embutidos"""
        
        # Comandos de sistema
        self.register_command(
            name="ajuda",
            func=self.cmd_help,
            category="system",
            description="Mostra esta ajuda",
            aliases=["help", "comandos", "?"]
        )
        
        self.register_command(
            name="sair",
            func=self.cmd_exit,
            category="system",
            description="Fecha o R2 Assistant",
            aliases=["exit", "quit", "fechar"]
        )
        
        # Comandos NOAA (serão carregados do módulo NOAA)
        self.register_command(
            name="clima espacial",
            func=None,  # Será substituído pelo módulo NOAA
            category="noaa",
            description="Relatório completo de clima espacial",
            aliases=["climaespacial", "space weather", "weather space"]
        )
    
    def register_command(self, name: str, func: Callable, category: str, 
                         description: str = "", aliases: List[str] = None):
        """Registra um novo comando"""
        
        command_data = {
            "func": func,
            "category": category,
            "description": description,
            "aliases": aliases or []
        }
        
        self.commands[name.lower()] = command_data
        
        # Registrar aliases
        if aliases:
            for alias in aliases:
                self.commands[alias.lower()] = command_data
    
    async def execute(self, command_text: str, args: List[str] = None) -> Dict[str, Any]:
        """Executa um comando"""
        
        if args is None:
            args = []
        
        command_lower = command_text.lower().strip()
        
        if command_lower not in self.commands:
            # Tentar encontrar comando similar
            suggestions = self._suggest_command(command_lower)
            return {
                "success": False,
                "message": f"Comando não encontrado: {command_text}",
                "suggestions": suggestions
            }
        
        command_data = self.commands[command_lower]
        
        if command_data["func"] is None:
            return {
                "success": False,
                "message": f"Comando '{command_text}' não implementado"
            }
        
        try:
            # Executar comando
            result = await command_data["func"](args)
            result["command"] = command_text
            return result
        except Exception as e:
            return {
                "success": False,
                "message": f"Erro ao executar comando: {str(e)}",
                "command": command_text
            }
    
    def _suggest_command(self, command: str) -> List[str]:
        """Sugere comandos similares"""
        suggestions = []
        for cmd in self.commands.keys():
            if command in cmd or cmd in command:
                suggestions.append(cmd)
        
        return suggestions[:5]  # Limitar a 5 sugestões
    
    def get_commands_by_category(self, category: str = None) -> Dict[str, Dict]:
        """Retorna comandos por categoria"""
        if category:
            return {k: v for k, v in self.commands.items() if v.get("category") == category}
        return self.commands
    
    def load_noaa_commands(self, noaa_module):
        """Carrega comandos do módulo NOAA"""
        try:
            # Obter comandos do módulo NOAA
            noaa_commands = getattr(noaa_module, "NOAACommands", None)
            if noaa_commands:
                noaa_instance = noaa_commands(None)  # Service será injetado depois
                
                for cmd_name, cmd_data in noaa_instance.commands.items():
                    self.register_command(
                        name=cmd_name,
                        func=cmd_data["func"],
                        category="noaa",
                        description=cmd_data["description"],
                        aliases=cmd_data.get("aliases", [])
                    )
                
                print(f"[OK] {len(noaa_instance.commands)} comandos NOAA carregados")
                return True
        except Exception as e:
            print(f"[ERRO] Falha ao carregar comandos NOAA: {e}")
        
        return False
    
    async def cmd_help(self, args: List[str] = None) -> Dict[str, Any]:
        """Comando de ajuda"""
        
        category = args[0] if args else None
        
        if category and category in self.categories:
            commands = self.get_commands_by_category(category)
            category_name = self.categories[category]
        else:
            commands = self.commands
            category_name = "Todos"
        
        # Formatar ajuda
        help_text = f"=== R2 Assistant - Comandos ({category_name}) ===\n"
        
        # Agrupar por categoria
        by_category = {}
        for cmd_name, cmd_data in commands.items():
            cat = cmd_data.get("category", "other")
            if cat not in by_category:
                by_category[cat] = []
            
            # Evitar duplicados (aliases)
            if cmd_name == list(self.commands.keys())[list(self.commands.values()).index(cmd_data)]:
                desc = cmd_data.get("description", "Sem descrição")
                aliases = cmd_data.get("aliases", [])
                alias_text = f" (aliases: {', '.join(aliases)})" if aliases else ""
                by_category[cat].append(f"  {cmd_name:20} - {desc}{alias_text}")
        
        # Adicionar comandos por categoria
        for cat, cmd_list in by_category.items():
            if cmd_list:
                cat_name = self.categories.get(cat, cat.title())
                help_text += f"\n{cat_name}:\n"
                help_text += "\n".join(cmd_list)
        
        help_text += "\n\nUse 'ajuda [categoria]' para ver comandos de uma categoria específica."
        
        return {
            "success": True,
            "message": help_text,
            "voice_response": "Lista de comandos disponível no painel."
        }
    
    async def cmd_exit(self, args: List[str] = None) -> Dict[str, Any]:
        """Comando de saída"""
        return {
            "success": True,
            "message": "Encerrando R2 Assistant...",
            "voice_response": "Até logo!",
            "action": "exit"
        }

# Instância global do sistema de comandos
command_system = CommandSystem()
