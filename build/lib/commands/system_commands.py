"""
Comandos de Sistema e Administração
Comandos para gerenciamento do sistema e diagnóstico
"""

import logging
import os
import sys
import platform
import psutil
import socket
import subprocess
import json
import time
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path
from . import Command, CommandResult, CommandContext, CommandCategory, CommandPermission

logger = logging.getLogger(__name__)

class SystemInfoCommand(Command):
    """Exibe informações detalhadas do sistema"""
    
    def __init__(self):
        super().__init__(
            name="sysinfo",
            description="Exibe informações detalhadas do sistema",
            category=CommandCategory.SYSTEM,
            permission=CommandPermission.USER,
            aliases=["system", "info", "status"],
            usage="sysinfo [--json]",
            examples=["sysinfo", "sysinfo --json"]
        )
    
    async def execute(self, context: CommandContext, *args, **kwargs) -> CommandResult:
        try:
            # Coletar informações do sistema
            system_info = {
                "platform": platform.system(),
                "platform_release": platform.release(),
                "platform_version": platform.version(),
                "architecture": platform.machine(),
                "processor": platform.processor(),
                "python_version": platform.python_version(),
                "hostname": socket.gethostname(),
                "ip_address": socket.gethostbyname(socket.gethostname()),
                "cpu_count": psutil.cpu_count(),
                "cpu_usage": psutil.cpu_percent(interval=0.1),
                "memory_total": psutil.virtual_memory().total,
                "memory_available": psutil.virtual_memory().available,
                "memory_used": psutil.virtual_memory().used,
                "memory_percent": psutil.virtual_memory().percent,
                "disk_usage": {},
                "boot_time": psutil.boot_time(),
                "uptime": time.time() - psutil.boot_time(),
                "users": [user.name for user in psutil.users()],
                "process_count": len(psutil.pids())
            }
            
            # Informações de disco
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    system_info["disk_usage"][partition.device] = {
                        "mountpoint": partition.mountpoint,
                        "fstype": partition.fstype,
                        "total": usage.total,
                        "used": usage.used,
                        "free": usage.free,
                        "percent": usage.percent
                    }
                except Exception:
                    continue
            
            # Formatar saída
            if "--json" in args:
                return CommandResult(
                    success=True,
                    message="Informações do sistema (JSON)",
                    data=system_info
                )
            
            # Formato legível
            info_text = "🖥️  INFORMAÇÕES DO SISTEMA\n\n"
            info_text += f"💻 Plataforma: {system_info['platform']} {system_info['platform_release']}\n"
            info_text += f"🏗️  Arquitetura: {system_info['architecture']}\n"
            info_text += f"🐍 Python: {system_info['python_version']}\n"
            info_text += f"🌐 Hostname: {system_info['hostname']}\n"
            info_text += f"📡 IP: {system_info['ip_address']}\n\n"
            
            info_text += "⚡ CPU\n"
            info_text += f"  Núcleos: {system_info['cpu_count']}\n"
            info_text += f"  Uso: {system_info['cpu_usage']:.1f}%\n\n"
            
            info_text += "💾 MEMÓRIA\n"
            memory_gb = system_info['memory_total'] / (1024**3)
            memory_used_gb = system_info['memory_used'] / (1024**3)
            info_text += f"  Total: {memory_gb:.2f} GB\n"
            info_text += f"  Usada: {memory_used_gb:.2f} GB ({system_info['memory_percent']:.1f}%)\n\n"
            
            info_text += "💿 DISCOS\n"
            for device, disk in system_info['disk_usage'].items():
                total_gb = disk['total'] / (1024**3)
                used_gb = disk['used'] / (1024**3)
                info_text += f"  {device} ({disk['mountpoint']}): {used_gb:.1f}/{total_gb:.1f} GB ({disk['percent']:.1f}%)\n"
            
            info_text += f"\n👥 Usuários: {', '.join(system_info['users'])}\n"
            info_text += f"📊 Processos: {system_info['process_count']}\n"
            
            uptime_days = system_info['uptime'] / 86400
            info_text += f"⏱️  Uptime: {uptime_days:.1f} dias\n"
            
            return CommandResult(
                success=True,
                message=info_text,
                data=system_info
            )
            
        except Exception as e:
            logger.error(f"Erro ao coletar informações do sistema: {e}")
            return CommandResult(
                success=False,
                message=f"Erro ao coletar informações do sistema: {str(e)}",
                error=str(e)
            )

class ProcessListCommand(Command):
    """Lista processos em execução"""
    
    def __init__(self):
        super().__init__(
            name="ps",
            description="Lista processos em execução",
            category=CommandCategory.SYSTEM,
            permission=CommandPermission.USER,
            aliases=["processes", "procs"],
            usage="ps [--user <username>] [--cpu] [--mem]",
            examples=["ps", "ps --user root", "ps --cpu", "ps --mem"]
        )
    
    async def execute(self, context: CommandContext, *args, **kwargs) -> CommandResult:
        try:
            # Parse arguments
            sort_by = "cpu" if "--cpu" in args else "memory" if "--mem" in args else "pid"
            username_filter = None
            if "--user" in args:
                try:
                    idx = args.index("--user")
                    username_filter = args[idx + 1]
                except IndexError:
                    pass
            
            # Coletar processos
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent']):
                try:
                    pinfo = proc.info
                    
                    # Filtrar por usuário
                    if username_filter and pinfo['username'] != username_filter:
                        continue
                    
                    processes.append(pinfo)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Ordenar
            if sort_by == "cpu":
                processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
            elif sort_by == "memory":
                processes.sort(key=lambda x: x['memory_percent'], reverse=True)
            else:
                processes.sort(key=lambda x: x['pid'])
            
            # Limitar para não sobrecarregar
            processes = processes[:50]
            
            # Formatar saída
            if "--json" in args:
                return CommandResult(
                    success=True,
                    message=f"Lista de processos ({len(processes)})",
                    data={"processes": processes}
                )
            
            # Formato de tabela
            output = f"📊 PROCESSOS ({len(processes)} mostrados)\n\n"
            output += f"{'PID':>8} {'CPU%':>6} {'MEM%':>6} {'USER':<12} {'NAME'}\n"
            output += "-" * 60 + "\n"
            
            for proc in processes:
                output += f"{proc['pid']:>8} {proc['cpu_percent']:>6.1f} {proc['memory_percent']:>6.1f} "
                output += f"{proc['username'][:12]:<12} {proc['name'][:30]}\n"
            
            return CommandResult(
                success=True,
                message=output,
                data={
                    "process_count": len(processes),
                    "sort_by": sort_by,
                    "user_filter": username_filter
                }
            )
            
        except Exception as e:
            logger.error(f"Erro ao listar processos: {e}")
            return CommandResult(
                success=False,
                message=f"Erro ao listar processos: {str(e)}",
                error=str(e)
            )

class KillProcessCommand(Command):
    """Mata um processo pelo PID"""
    
    def __init__(self):
        super().__init__(
            name="kill",
            description="Mata um processo pelo PID",
            category=CommandCategory.SYSTEM,
            permission=CommandPermission.ADMIN,
            aliases=["terminate", "stop"],
            usage="kill <pid> [--force]",
            examples=["kill 1234", "kill 1234 --force"]
        )
    
    async def execute(self, context: CommandContext, *args, **kwargs) -> CommandResult:
        if not args:
            return CommandResult(
                success=False,
                message="Especifique o PID do processo",
                error="No PID specified"
            )
        
        try:
            pid = int(args[0])
            force = "--force" in args
            
            # Verificar se processo existe
            if not psutil.pid_exists(pid):
                return CommandResult(
                    success=False,
                    message=f"Processo com PID {pid} não encontrado",
                    error="Process not found"
                )
            
            # Obter processo
            proc = psutil.Process(pid)
            proc_name = proc.name()
            proc_user = proc.username()
            
            # Tentar terminar
            try:
                if force:
                    proc.kill()
                    action = "forçado (SIGKILL)"
                else:
                    proc.terminate()
                    action = "terminado (SIGTERM)"
                
                # Esperar processo terminar
                gone, alive = psutil.wait_procs([proc], timeout=3)
                
                if alive:
                    return CommandResult(
                        success=False,
                        message=f"Processo {pid} ({proc_name}) não terminou a tempo",
                        error="Process did not terminate"
                    )
                
                return CommandResult(
                    success=True,
                    message=f"Processo {pid} ({proc_name}) {action}",
                    data={
                        "pid": pid,
                        "name": proc_name,
                        "user": proc_user,
                        "force": force,
                        "action": action
                    }
                )
                
            except psutil.AccessDenied:
                return CommandResult(
                    success=False,
                    message=f"Permissão negada para terminar processo {pid}",
                    error="Permission denied"
                )
            
        except ValueError:
            return CommandResult(
                success=False,
                message="PID deve ser um número inteiro",
                error="Invalid PID"
            )
        except Exception as e:
            logger.error(f"Erro ao terminar processo: {e}")
            return CommandResult(
                success=False,
                message=f"Erro ao terminar processo: {str(e)}",
                error=str(e)
            )

class DiskUsageCommand(Command):
    """Exibe uso de disco por diretório"""
    
    def __init__(self):
        super().__init__(
            name="df",
            description="Exibe uso de disco por diretório",
            category=CommandCategory.SYSTEM,
            permission=CommandPermission.USER,
            aliases=["disk", "diskinfo"],
            usage="df [path] [--human]",
            examples=["df", "df /home --human", "df C:\\"]
        )
    
    async def execute(self, context: CommandContext, *args, **kwargs) -> CommandResult:
        try:
            # Diretório padrão ou especificado
            path = args[0] if args else "."
            human_readable = "--human" in args or "-h" in args
            
            # Obter uso de disco
            usage = psutil.disk_usage(path)
            
            if human_readable:
                def human_size(size):
                    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                        if size < 1024.0:
                            return f"{size:.1f} {unit}"
                        size /= 1024.0
                    return f"{size:.1f} PB"
                
                total = human_size(usage.total)
                used = human_size(usage.used)
                free = human_size(usage.free)
            else:
                total = f"{usage.total:,} bytes"
                used = f"{usage.used:,} bytes"
                free = f"{usage.free:,} bytes"
            
            # Formatar saída
            output = f"💿 USO DE DISCO: {path}\n\n"
            output += f"📊 Total: {total}\n"
            output += f"📈 Usado: {used} ({usage.percent:.1f}%)\n"
            output += f"📉 Livre: {free}\n"
            
            # Barra de progresso ASCII
            bar_length = 40
            filled = int(bar_length * usage.percent / 100)
            bar = "█" * filled + "░" * (bar_length - filled)
            output += f"\n[{bar}] {usage.percent:.1f}%\n"
            
            return CommandResult(
                success=True,
                message=output,
                data={
                    "path": path,
                    "total": usage.total,
                    "used": usage.used,
                    "free": usage.free,
                    "percent": usage.percent,
                    "human_readable": human_readable
                }
            )
            
        except Exception as e:
            logger.error(f"Erro ao verificar uso de disco: {e}")
            return CommandResult(
                success=False,
                message=f"Erro ao verificar uso de disco: {str(e)}",
                error=str(e)
            )

class NetworkInfoCommand(Command):
    """Exibe informações de rede"""
    
    def __init__(self):
        super().__init__(
            name="netstat",
            description="Exibe informações de rede",
            category=CommandCategory.SYSTEM,
            permission=CommandPermission.USER,
            aliases=["network", "ifconfig", "ipconfig"],
            usage="netstat [--connections]",
            examples=["netstat", "netstat --connections"]
        )
    
    async def execute(self, context: CommandContext, *args, **kwargs) -> CommandResult:
        try:
            output = "🌐 INFORMAÇÕES DE REDE\n\n"
            
            # Endereços de rede
            hostname = socket.gethostname()
            ip_addr = socket.gethostbyname(hostname)
            
            output += f"🏷️  Hostname: {hostname}\n"
            output += f"📡 IP Local: {ip_addr}\n\n"
            
            # Interfaces de rede
            net_io = psutil.net_io_counters()
            output += "📊 ESTATÍSTICAS DE REDE\n"
            output += f"  Bytes enviados: {net_io.bytes_sent:,}\n"
            output += f"  Bytes recebidos: {net_io.bytes_recv:,}\n"
            output += f"  Pacotes enviados: {net_io.packets_sent:,}\n"
            output += f"  Pacotes recebidos: {net_io.packets_recv:,}\n\n"
            
            # Conexões de rede (se solicitado)
            if "--connections" in args:
                connections = psutil.net_connections(kind='inet')
                output += f"🔗 CONEXÕES ATIVAS ({len(connections)})\n\n"
                
                for conn in connections[:20]:  # Limitar a 20
                    if conn.status == psutil.CONN_LISTEN:
                        status = "LISTEN"
                    else:
                        status = conn.status
                    
                    laddr = f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else ""
                    raddr = f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else ""
                    pid = conn.pid if conn.pid else "N/A"
                    
                    output += f"  {laddr:>21} -> {raddr:<21} {status:<12} PID: {pid}\n"
                
                if len(connections) > 20:
                    output += f"\n  ... e mais {len(connections) - 20} conexões\n"
            
            return CommandResult(
                success=True,
                message=output,
                data={
                    "hostname": hostname,
                    "ip_address": ip_addr,
                    "network_stats": {
                        "bytes_sent": net_io.bytes_sent,
                        "bytes_recv": net_io.bytes_recv,
                        "packets_sent": net_io.packets_sent,
                        "packets_recv": net_io.packets_recv
                    }
                }
            )
            
        except Exception as e:
            logger.error(f"Erro ao obter informações de rede: {e}")
            return CommandResult(
                success=False,
                message=f"Erro ao obter informações de rede: {str(e)}",
                error=str(e)
            )

class EnvironmentCommand(Command):
    """Exibe variáveis de ambiente"""
    
    def __init__(self):
        super().__init__(
            name="env",
            description="Exibe variáveis de ambiente",
            category=CommandCategory.SYSTEM,
            permission=CommandPermission.USER,
            aliases=["environment", "vars"],
            usage="env [--filter <prefix>]",
            examples=["env", "env --filter PYTHON", "env --filter PATH"]
        )
    
    async def execute(self, context: CommandContext, *args, **kwargs) -> CommandResult:
        try:
            # Parse filter
            filter_prefix = None
            if "--filter" in args:
                try:
                    idx = args.index("--filter")
                    filter_prefix = args[idx + 1].upper()
                except IndexError:
                    pass
            
            # Coletar variáveis
            env_vars = dict(os.environ)
            
            # Aplicar filtro
            if filter_prefix:
                env_vars = {
                    k: v for k, v in env_vars.items()
                    if k.startswith(filter_prefix)
                }
            
            # Formatar saída
            if "--json" in args:
                return CommandResult(
                    success=True,
                    message=f"Variáveis de ambiente ({len(env_vars)})",
                    data=env_vars
                )
            
            output = f"🌍 VARIÁVEIS DE AMBIENTE ({len(env_vars)})\n\n"
            
            for key, value in sorted(env_vars.items()):
                # Truncar valores muito longos
                if len(value) > 100:
                    value = value[:100] + "..."
                output += f"{key}={value}\n"
            
            return CommandResult(
                success=True,
                message=output,
                data={
                    "count": len(env_vars),
                    "filter": filter_prefix,
                    "variables": list(env_vars.keys())
                }
            )
            
        except Exception as e:
            logger.error(f"Erro ao obter variáveis de ambiente: {e}")
            return CommandResult(
                success=False,
                message=f"Erro ao obter variáveis de ambiente: {str(e)}",
                error=str(e)
            )

class LogCommand(Command):
    """Exibe logs do sistema"""
    
    def __init__(self, log_file: str = "logs/r2_assistant.log"):
        super().__init__(
            name="log",
            description="Exibe logs do sistema",
            category=CommandCategory.SYSTEM,
            permission=CommandPermission.ADMIN,
            aliases=["logs", "tail"],
            usage="log [--lines N] [--level <level>] [--follow]",
            examples=["log", "log --lines 50", "log --level ERROR", "log --follow"]
        )
        self.log_file = log_file
    
    async def execute(self, context: CommandContext, *args, **kwargs) -> CommandResult:
        try:
            # Parse arguments
            lines = 20
            level_filter = None
            follow = False
            
            i = 0
            while i < len(args):
                if args[i] == "--lines" and i + 1 < len(args):
                    try:
                        lines = int(args[i + 1])
                        i += 1
                    except ValueError:
                        pass
                elif args[i] == "--level" and i + 1 < len(args):
                    level_filter = args[i + 1].upper()
                    i += 1
                elif args[i] == "--follow":
                    follow = True
                i += 1
            
            # Verificar se arquivo existe
            if not os.path.exists(self.log_file):
                return CommandResult(
                    success=False,
                    message=f"Arquivo de log não encontrado: {self.log_file}",
                    error="Log file not found"
                )
            
            # Ler arquivo de log
            with open(self.log_file, 'r', encoding='utf-8') as f:
                log_lines = f.readlines()
            
            # Aplicar filtro de nível
            if level_filter:
                log_lines = [
                    line for line in log_lines
                    if f" {level_filter}:" in line
                ]
            
            # Pegar últimas N linhas
            log_lines = log_lines[-lines:]
            
            # Formatar saída
            if follow:
                # Modo follow não implementado aqui (seria em UI)
                message = f"Modo follow requer integração com UI\n\n"
            else:
                message = ""
            
            message += f"📝 LOGS ({len(log_lines)} linhas)\n\n"
            message += "".join(log_lines)
            
            return CommandResult(
                success=True,
                message=message,
                data={
                    "log_file": self.log_file,
                    "lines": lines,
                    "level_filter": level_filter,
                    "follow": follow,
                    "log_count": len(log_lines)
                }
            )
            
        except Exception as e:
            logger.error(f"Erro ao ler logs: {e}")
            return CommandResult(
                success=False,
                message=f"Erro ao ler logs: {str(e)}",
                error=str(e)
            )

class SystemCommands:
    """Classe container para comandos de sistema"""
    
    def __init__(self, registry, processor, config: Optional[Dict[str, Any]] = None):
        self.registry = registry
        self.processor = processor
        self.config = config or {}
        
        # Registrar comandos
        self.commands = [
            SystemInfoCommand(),
            ProcessListCommand(),
            KillProcessCommand(),
            DiskUsageCommand(),
            NetworkInfoCommand(),
            EnvironmentCommand(),
            LogCommand(self.config.get('log_file', 'logs/r2_assistant.log'))
        ]
        
        for cmd in self.commands:
            registry.register(cmd)
        
        logger.info(f"{len(self.commands)} comandos de sistema registrados")
    
    def get_commands(self):
        """Retorna lista de comandos registrados"""
        return self.commands