"""
System Monitor - Monitoramento avançado do sistema
Monitora recursos, processos, discos e hardware em tempo real
"""

import logging
import psutil
import platform
import time
import threading
import socket
import os
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
import GPUtil
from collections import deque

logger = logging.getLogger(__name__)

class SystemStatus(Enum):
    """Status do sistema"""
    OPTIMAL = "optimal"
    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL = "critical"
    OFFLINE = "offline"

@dataclass
class DiskUsage:
    """Uso de disco"""
    mount_point: str
    total_gb: float
    used_gb: float
    free_gb: float
    percent_used: float
    filesystem: str
    io_read_bytes: float = 0.0
    io_write_bytes: float = 0.0
    io_read_count: int = 0
    io_write_count: int = 0
    
    @property
    def status(self) -> SystemStatus:
        """Status baseado no uso"""
        if self.percent_used >= 95:
            return SystemStatus.CRITICAL
        elif self.percent_used >= 85:
            return SystemStatus.WARNING
        elif self.percent_used >= 70:
            return SystemStatus.NORMAL
        else:
            return SystemStatus.OPTIMAL

@dataclass
class NetworkInterface:
    """Interface de rede"""
    name: str
    ip_address: str
    netmask: str
    broadcast: str
    mac_address: str
    is_up: bool
    speed_mbps: float
    bytes_sent: int
    bytes_recv: int
    packets_sent: int
    packets_recv: int
    errors_in: int
    errors_out: int
    drops_in: int
    drops_out: int
    
    @property
    def traffic_mbps(self) -> float:
        """Tráfego total em MB/s"""
        total_bytes = self.bytes_sent + self.bytes_recv
        return total_bytes / (1024 * 1024)

@dataclass
class ProcessInfo:
    """Informações do processo"""
    pid: int
    name: str
    cpu_percent: float
    memory_percent: float
    memory_mb: float
    status: str
    create_time: float
    threads: int
    connections: int
    io_read_bytes: int
    io_write_bytes: int
    command_line: str = ""
    username: str = ""
    
    @property
    def uptime_seconds(self) -> float:
        """Tempo de execução em segundos"""
        return time.time() - self.create_time
    
    @property
    def is_system_critical(self) -> bool:
        """Verifica se é um processo crítico do sistema"""
        critical_processes = ['systemd', 'init', 'svchost.exe', 'lsass.exe', 'csrss.exe']
        return any(cp in self.name.lower() for cp in critical_processes)

@dataclass
class SystemMetrics:
    """Métricas completas do sistema"""
    timestamp: datetime
    cpu_percent: float
    cpu_percent_per_core: List[float]
    cpu_freq_current: float
    cpu_freq_min: float
    cpu_freq_max: float
    memory_total_gb: float
    memory_used_gb: float
    memory_free_gb: float
    memory_percent: float
    swap_total_gb: float
    swap_used_gb: float
    swap_free_gb: float
    swap_percent: float
    disks: List[DiskUsage]
    network_interfaces: List[NetworkInterface]
    processes: List[ProcessInfo]
    load_average: Tuple[float, float, float]
    uptime_seconds: float
    boot_time: datetime
    temperatures: Dict[str, float]
    fans_speed: Dict[str, int]
    battery_percent: Optional[float]
    battery_plugged: bool
    gpu_usage: List[float]
    gpu_memory: List[float]
    gpu_temperature: List[float]
    
    @property
    def overall_status(self) -> SystemStatus:
        """Status geral do sistema"""
        statuses = []
        
        # CPU
        if self.cpu_percent > 90:
            statuses.append(SystemStatus.CRITICAL)
        elif self.cpu_percent > 75:
            statuses.append(SystemStatus.WARNING)
        
        # Memória
        if self.memory_percent > 95:
            statuses.append(SystemStatus.CRITICAL)
        elif self.memory_percent > 85:
            statuses.append(SystemStatus.WARNING)
        
        # Swap
        if self.swap_percent > 90:
            statuses.append(SystemStatus.WARNING)
        
        # Discos
        for disk in self.disks:
            statuses.append(disk.status)
        
        # Temperaturas
        for temp in self.temperatures.values():
            if temp > 90:
                statuses.append(SystemStatus.CRITICAL)
            elif temp > 75:
                statuses.append(SystemStatus.WARNING)
        
        # Determinar status mais crítico
        if SystemStatus.CRITICAL in statuses:
            return SystemStatus.CRITICAL
        elif SystemStatus.WARNING in statuses:
            return SystemStatus.WARNING
        elif SystemStatus.NORMAL in statuses:
            return SystemStatus.NORMAL
        else:
            return SystemStatus.OPTIMAL
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'cpu_percent': self.cpu_percent,
            'memory_percent': self.memory_percent,
            'swap_percent': self.swap_percent,
            'load_average': self.load_average,
            'uptime_seconds': self.uptime_seconds,
            'overall_status': self.overall_status.value,
            'disks': [
                {
                    'mount_point': d.mount_point,
                    'percent_used': d.percent_used,
                    'status': d.status.value
                }
                for d in self.disks
            ],
            'temperatures': self.temperatures,
            'gpu_usage': self.gpu_usage
        }

class SystemMonitor:
    """
    Monitor avançado do sistema
    Coleta métricas em tempo real com histórico e análise
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Inicializa o monitor do sistema
        
        Args:
            config: Configuração do monitor
        """
        self.config = config or {}
        self.update_interval = self.config.get('update_interval', 2.0)
        self.history_size = self.config.get('history_size', 300)  # 5 minutos a 1s
        
        # Histórico de métricas
        self.metrics_history: deque = deque(maxlen=self.history_size)
        self.process_history: Dict[int, deque] = {}
        
        # Estado
        self.is_monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.last_metrics: Optional[SystemMetrics] = None
        
        # Limites de alerta
        self.thresholds = {
            'cpu_warning': 75.0,
            'cpu_critical': 90.0,
            'memory_warning': 85.0,
            'memory_critical': 95.0,
            'disk_warning': 85.0,
            'disk_critical': 95.0,
            'temp_warning': 75.0,
            'temp_critical': 90.0
        }
        
        # Callbacks para alertas
        self.alert_callbacks = []
        
        # Informações do sistema
        self.system_info = self._get_system_info()
        
        logger.info(f"System Monitor inicializado para {self.system_info['os']}")
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Obtém informações do sistema"""
        try:
            info = {
                'os': platform.system(),
                'os_version': platform.version(),
                'os_release': platform.release(),
                'architecture': platform.machine(),
                'processor': platform.processor(),
                'hostname': socket.gethostname(),
                'python_version': platform.python_version(),
                'cores': psutil.cpu_count(logical=False),
                'logical_cores': psutil.cpu_count(logical=True),
                'boot_time': datetime.fromtimestamp(psutil.boot_time())
            }
            
            # Informações específicas por OS
            if info['os'] == 'Linux':
                try:
                    with open('/etc/os-release', 'r') as f:
                        for line in f:
                            if line.startswith('PRETTY_NAME='):
                                info['distribution'] = line.split('=')[1].strip().strip('"')
                                break
                except:
                    info['distribution'] = 'Unknown'
            
            return info
            
        except Exception as e:
            logger.error(f"Erro ao obter informações do sistema: {e}")
            return {}
    
    def start_monitoring(self):
        """Inicia o monitoramento"""
        if self.is_monitoring:
            logger.warning("System Monitor já está rodando")
            return
        
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        
        logger.info("System Monitor iniciado")
    
    def stop_monitoring(self):
        """Para o monitoramento"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        logger.info("System Monitor parado")
    
    def _monitoring_loop(self):
        """Loop principal de monitoramento"""
        import time
        
        while self.is_monitoring:
            try:
                start_time = time.time()
                
                # Coletar métricas
                metrics = self.collect_metrics()
                self.last_metrics = metrics
                self.metrics_history.append(metrics)
                
                # Verificar alertas
                self._check_alerts(metrics)
                
                # Processar histórico de processos
                self._update_process_history(metrics)
                
                # Calcular tempo de processamento
                processing_time = time.time() - start_time
                
                # Aguardar próximo ciclo
                sleep_time = max(0, self.update_interval - processing_time)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    
            except Exception as e:
                logger.error(f"Erro no loop de monitoramento: {e}")
                time.sleep(5)
    
    def collect_metrics(self) -> SystemMetrics:
        """Coleta métricas completas do sistema"""
        try:
            timestamp = datetime.now()
            
            # CPU
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_percent_per_core = psutil.cpu_percent(interval=0.1, percpu=True)
            
            cpu_freq = psutil.cpu_freq()
            if cpu_freq:
                cpu_freq_current = cpu_freq.current
                cpu_freq_min = cpu_freq.min
                cpu_freq_max = cpu_freq.max
            else:
                cpu_freq_current = cpu_freq_min = cpu_freq_max = 0.0
            
            # Memória
            memory = psutil.virtual_memory()
            memory_total_gb = memory.total / (1024**3)
            memory_used_gb = memory.used / (1024**3)
            memory_free_gb = memory.free / (1024**3)
            memory_percent = memory.percent
            
            # Swap
            swap = psutil.swap_memory()
            swap_total_gb = swap.total / (1024**3) if swap.total > 0 else 0
            swap_used_gb = swap.used / (1024**3) if swap.used > 0 else 0
            swap_free_gb = swap.free / (1024**3) if swap.free > 0 else 0
            swap_percent = swap.percent if swap.total > 0 else 0
            
            # Discos
            disks = []
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    
                    # I/O do disco
                    disk_io = psutil.disk_io_counters(perdisk=True).get(partition.device, None)
                    
                    disks.append(DiskUsage(
                        mount_point=partition.mountpoint,
                        total_gb=usage.total / (1024**3),
                        used_gb=usage.used / (1024**3),
                        free_gb=usage.free / (1024**3),
                        percent_used=usage.percent,
                        filesystem=partition.fstype,
                        io_read_bytes=disk_io.read_bytes if disk_io else 0,
                        io_write_bytes=disk_io.write_bytes if disk_io else 0,
                        io_read_count=disk_io.read_count if disk_io else 0,
                        io_write_count=disk_io.write_count if disk_io else 0
                    ))
                except Exception as e:
                    logger.debug(f"Erro ao coletar uso do disco {partition.mountpoint}: {e}")
            
            # Interfaces de rede
            network_interfaces = []
            net_io = psutil.net_io_counters(pernic=True)
            net_if_addrs = psutil.net_if_addrs()
            net_if_stats = psutil.net_if_stats()
            
            for interface_name, io in net_io.items():
                if interface_name in net_if_addrs and interface_name in net_if_stats:
                    addrs = net_if_addrs[interface_name]
                    stats = net_if_stats[interface_name]
                    
                    # Obter endereço IP
                    ip_address = ""
                    mac_address = ""
                    
                    for addr in addrs:
                        if addr.family == socket.AF_INET:  # IPv4
                            ip_address = addr.address
                        elif addr.family == psutil.AF_LINK:  # MAC
                            mac_address = addr.address
                    
                    network_interfaces.append(NetworkInterface(
                        name=interface_name,
                        ip_address=ip_address,
                        netmask=addrs[0].netmask if addrs and addrs[0].family == socket.AF_INET else "",
                        broadcast=addrs[0].broadcast if addrs and addrs[0].family == socket.AF_INET else "",
                        mac_address=mac_address,
                        is_up=stats.isup,
                        speed_mbps=stats.speed if stats.speed > 0 else 0,
                        bytes_sent=io.bytes_sent,
                        bytes_recv=io.bytes_recv,
                        packets_sent=io.packets_sent,
                        packets_recv=io.packets_recv,
                        errors_in=io.errin,
                        errors_out=io.errout,
                        drops_in=io.dropin,
                        drops_out=io.dropout
                    ))
            
            # Processos
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent',
                                           'status', 'create_time', 'num_threads',
                                           'username', 'cmdline']):
                try:
                    proc_info = proc.info
                    
                    # Obter conexões
                    connections = len(proc.connections()) if hasattr(proc, 'connections') else 0
                    
                    # Obter I/O
                    io_counters = proc.io_counters() if hasattr(proc, 'io_counters') else None
                    
                    processes.append(ProcessInfo(
                        pid=proc_info['pid'],
                        name=proc_info['name'],
                        cpu_percent=proc_info.get('cpu_percent', 0.0),
                        memory_percent=proc_info.get('memory_percent', 0.0),
                        memory_mb=proc.memory_info().rss / (1024**2),
                        status=proc_info.get('status', 'unknown'),
                        create_time=proc_info.get('create_time', 0),
                        threads=proc_info.get('num_threads', 0),
                        connections=connections,
                        io_read_bytes=io_counters.read_bytes if io_counters else 0,
                        io_write_bytes=io_counters.write_bytes if io_counters else 0,
                        command_line=' '.join(proc_info.get('cmdline', [])),
                        username=proc_info.get('username', '')
                    ))
                    
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Load average
            load_avg = psutil.getloadavg() if hasattr(psutil, 'getloadavg') else (0.0, 0.0, 0.0)
            
            # Uptime
            uptime_seconds = time.time() - psutil.boot_time()
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            
            # Temperaturas
            temperatures = {}
            if hasattr(psutil, 'sensors_temperatures'):
                try:
                    temps = psutil.sensors_temperatures()
                    for name, entries in temps.items():
                        if entries:
                            temperatures[name] = entries[0].current
                except:
                    pass
            
            # Ventoinhas
            fans_speed = {}
            if hasattr(psutil, 'sensors_fans'):
                try:
                    fans = psutil.sensors_fans()
                    for name, entries in fans.items():
                        if entries:
                            fans_speed[name] = entries[0].current
                except:
                    pass
            
            # Bateria
            battery = None
            battery_percent = None
            battery_plugged = False
            
            if hasattr(psutil, 'sensors_battery'):
                try:
                    battery = psutil.sensors_battery()
                    if battery:
                        battery_percent = battery.percent
                        battery_plugged = battery.power_plugged
                except:
                    pass
            
            # GPU
            gpu_usage = []
            gpu_memory = []
            gpu_temperature = []
            
            try:
                gpus = GPUtil.getGPUs()
                for gpu in gpus:
                    gpu_usage.append(gpu.load * 100)
                    gpu_memory.append(gpu.memoryUtil * 100)
                    gpu_temperature.append(gpu.temperature)
            except:
                # GPUtil pode não estar disponível
                pass
            
            return SystemMetrics(
                timestamp=timestamp,
                cpu_percent=cpu_percent,
                cpu_percent_per_core=cpu_percent_per_core,
                cpu_freq_current=cpu_freq_current,
                cpu_freq_min=cpu_freq_min,
                cpu_freq_max=cpu_freq_max,
                memory_total_gb=memory_total_gb,
                memory_used_gb=memory_used_gb,
                memory_free_gb=memory_free_gb,
                memory_percent=memory_percent,
                swap_total_gb=swap_total_gb,
                swap_used_gb=swap_used_gb,
                swap_free_gb=swap_free_gb,
                swap_percent=swap_percent,
                disks=disks,
                network_interfaces=network_interfaces,
                processes=processes,
                load_average=load_avg,
                uptime_seconds=uptime_seconds,
                boot_time=boot_time,
                temperatures=temperatures,
                fans_speed=fans_speed,
                battery_percent=battery_percent,
                battery_plugged=battery_plugged,
                gpu_usage=gpu_usage,
                gpu_memory=gpu_memory,
                gpu_temperature=gpu_temperature
            )
            
        except Exception as e:
            logger.error(f"Erro ao coletar métricas do sistema: {e}")
            # Retornar métricas vazias em caso de erro
            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=0.0,
                cpu_percent_per_core=[],
                cpu_freq_current=0.0,
                cpu_freq_min=0.0,
                cpu_freq_max=0.0,
                memory_total_gb=0.0,
                memory_used_gb=0.0,
                memory_free_gb=0.0,
                memory_percent=0.0,
                swap_total_gb=0.0,
                swap_used_gb=0.0,
                swap_free_gb=0.0,
                swap_percent=0.0,
                disks=[],
                network_interfaces=[],
                processes=[],
                load_average=(0.0, 0.0, 0.0),
                uptime_seconds=0.0,
                boot_time=datetime.now(),
                temperatures={},
                fans_speed={},
                battery_percent=None,
                battery_plugged=False,
                gpu_usage=[],
                gpu_memory=[],
                gpu_temperature=[]
            )
    
    def _update_process_history(self, metrics: SystemMetrics):
        """Atualiza histórico de processos"""
        for process in metrics.processes:
            pid = process.pid
            
            if pid not in self.process_history:
                self.process_history[pid] = deque(maxlen=60)  # 1 minuto de histórico
            
            self.process_history[pid].append({
                'timestamp': metrics.timestamp,
                'cpu_percent': process.cpu_percent,
                'memory_mb': process.memory_mb,
                'memory_percent': process.memory_percent
            })
    
    def _check_alerts(self, metrics: SystemMetrics):
        """Verifica e envia alertas"""
        alerts = []
        
        # CPU
        if metrics.cpu_percent > self.thresholds['cpu_critical']:
            alerts.append({
                'type': 'cpu',
                'level': 'critical',
                'message': f'CPU crítica: {metrics.cpu_percent:.1f}%',
                'value': metrics.cpu_percent,
                'threshold': self.thresholds['cpu_critical']
            })
        elif metrics.cpu_percent > self.thresholds['cpu_warning']:
            alerts.append({
                'type': 'cpu',
                'level': 'warning',
                'message': f'CPU alta: {metrics.cpu_percent:.1f}%',
                'value': metrics.cpu_percent,
                'threshold': self.thresholds['cpu_warning']
            })
        
        # Memória
        if metrics.memory_percent > self.thresholds['memory_critical']:
            alerts.append({
                'type': 'memory',
                'level': 'critical',
                'message': f'Memória crítica: {metrics.memory_percent:.1f}%',
                'value': metrics.memory_percent,
                'threshold': self.thresholds['memory_critical']
            })
        elif metrics.memory_percent > self.thresholds['memory_warning']:
            alerts.append({
                'type': 'memory',
                'level': 'warning',
                'message': f'Memória alta: {metrics.memory_percent:.1f}%',
                'value': metrics.memory_percent,
                'threshold': self.thresholds['memory_warning']
            })
        
        # Discos
        for disk in metrics.disks:
            if disk.percent_used > self.thresholds['disk_critical']:
                alerts.append({
                    'type': 'disk',
                    'level': 'critical',
                    'message': f'Disco {disk.mount_point} crítico: {disk.percent_used:.1f}%',
                    'value': disk.percent_used,
                    'threshold': self.thresholds['disk_critical'],
                    'mount_point': disk.mount_point
                })
            elif disk.percent_used > self.thresholds['disk_warning']:
                alerts.append({
                    'type': 'disk',
                    'level': 'warning',
                    'message': f'Disco {disk.mount_point} alto: {disk.percent_used:.1f}%',
                    'value': disk.percent_used,
                    'threshold': self.thresholds['disk_warning'],
                    'mount_point': disk.mount_point
                })
        
        # Temperaturas
        for name, temp in metrics.temperatures.items():
            if temp > self.thresholds['temp_critical']:
                alerts.append({
                    'type': 'temperature',
                    'level': 'critical',
                    'message': f'Temperatura {name} crítica: {temp:.1f}°C',
                    'value': temp,
                    'threshold': self.thresholds['temp_critical'],
                    'sensor': name
                })
            elif temp > self.thresholds['temp_warning']:
                alerts.append({
                    'type': 'temperature',
                    'level': 'warning',
                    'message': f'Temperatura {name} alta: {temp:.1f}°C',
                    'value': temp,
                    'threshold': self.thresholds['temp_warning'],
                    'sensor': name
                })
        
        # Processos problemáticos
        for process in metrics.processes:
            if process.cpu_percent > 50:  # Processo usando mais de 50% CPU
                alerts.append({
                    'type': 'process',
                    'level': 'warning',
                    'message': f'Processo {process.name} (PID: {process.pid}) usando {process.cpu_percent:.1f}% CPU',
                    'value': process.cpu_percent,
                    'process_name': process.name,
                    'pid': process.pid
                })
            
            if process.memory_mb > 1024:  # Processo usando mais de 1GB
                alerts.append({
                    'type': 'process',
                    'level': 'warning',
                    'message': f'Processo {process.name} (PID: {process.pid}) usando {process.memory_mb:.1f} MB',
                    'value': process.memory_mb,
                    'process_name': process.name,
                    'pid': process.pid
                })
        
        # Enviar alertas para callbacks
        for alert in alerts:
            self._send_alert(alert)
    
    def register_alert_callback(self, callback):
        """Registra callback para receber alertas"""
        self.alert_callbacks.append(callback)
        logger.debug(f"Callback de alerta registrado: {callback.__name__}")
    
    def _send_alert(self, alert: Dict[str, Any]):
        """Envia alerta para callbacks registrados"""
        alert['timestamp'] = datetime.now().isoformat()
        alert['source'] = 'system_monitor'
        
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Erro no callback de alerta: {e}")
    
    def get_current_metrics(self) -> Optional[SystemMetrics]:
        """Obtém métricas atuais"""
        return self.last_metrics
    
    def get_metrics_history(self, seconds: int = 60) -> List[SystemMetrics]:
        """Obtém histórico de métricas"""
        cutoff_time = datetime.now() - timedelta(seconds=seconds)
        
        history = []
        for metrics in self.metrics_history:
            if metrics.timestamp >= cutoff_time:
                history.append(metrics)
        
        return history
    
    def get_process_history(self, pid: int, seconds: int = 60) -> List[Dict[str, Any]]:
        """Obtém histórico de um processo específico"""
        if pid not in self.process_history:
            return []
        
        cutoff_time = datetime.now() - timedelta(seconds=seconds)
        
        history = []
        for entry in self.process_history[pid]:
            if entry['timestamp'] >= cutoff_time:
                history.append(entry)
        
        return history
    
    def get_top_processes(self, limit: int = 10, by: str = 'cpu') -> List[ProcessInfo]:
        """Obtém processos mais intensivos"""
        if not self.last_metrics:
            return []
        
        processes = self.last_metrics.processes.copy()
        
        if by == 'cpu':
            processes.sort(key=lambda p: p.cpu_percent, reverse=True)
        elif by == 'memory':
            processes.sort(key=lambda p: p.memory_mb, reverse=True)
        elif by == 'memory_percent':
            processes.sort(key=lambda p: p.memory_percent, reverse=True)
        
        return processes[:limit]
    
    def get_disk_io_rates(self) -> Dict[str, Dict[str, float]]:
        """Calcula taxas de I/O dos discos"""
        if len(self.metrics_history) < 2:
            return {}
        
        latest = self.metrics_history[-1]
        previous = self.metrics_history[-2]
        
        time_diff = (latest.timestamp - previous.timestamp).total_seconds()
        
        io_rates = {}
        
        for disk in latest.disks:
            prev_disk = next((d for d in previous.disks 
                            if d.mount_point == disk.mount_point), None)
            
            if prev_disk and time_diff > 0:
                read_rate = (disk.io_read_bytes - prev_disk.io_read_bytes) / time_diff
                write_rate = (disk.io_write_bytes - prev_disk.io_write_bytes) / time_diff
                
                io_rates[disk.mount_point] = {
                    'read_mbps': read_rate / (1024 * 1024),
                    'write_mbps': write_rate / (1024 * 1024),
                    'read_iops': (disk.io_read_count - prev_disk.io_read_count) / time_diff,
                    'write_iops': (disk.io_write_count - prev_disk.io_write_count) / time_diff
                }
        
        return io_rates
    
    def get_network_io_rates(self) -> Dict[str, Dict[str, float]]:
        """Calcula taxas de I/O da rede"""
        if len(self.metrics_history) < 2:
            return {}
        
        latest = self.metrics_history[-1]
        previous = self.metrics_history[-2]
        
        time_diff = (latest.timestamp - previous.timestamp).total_seconds()
        
        network_rates = {}
        
        for interface in latest.network_interfaces:
            prev_interface = next((i for i in previous.network_interfaces 
                                if i.name == interface.name), None)
            
            if prev_interface and time_diff > 0:
                sent_rate = (interface.bytes_sent - prev_interface.bytes_sent) / time_diff
                recv_rate = (interface.bytes_recv - prev_interface.bytes_recv) / time_diff
                
                network_rates[interface.name] = {
                    'sent_mbps': sent_rate / (1024 * 1024),
                    'recv_mbps': recv_rate / (1024 * 1024),
                    'sent_pps': (interface.packets_sent - prev_interface.packets_sent) / time_diff,
                    'recv_pps': (interface.packets_recv - prev_interface.packets_recv) / time_diff
                }
        
        return network_rates
    
    def get_system_summary(self) -> Dict[str, Any]:
        """Obtém resumo do sistema"""
        if not self.last_metrics:
            return {}
        
        metrics = self.last_metrics
        
        return {
            'timestamp': metrics.timestamp.isoformat(),
            'overall_status': metrics.overall_status.value,
            'cpu': {
                'percent': metrics.cpu_percent,
                'freq_current': metrics.cpu_freq_current,
                'cores': len(metrics.cpu_percent_per_core)
            },
            'memory': {
                'percent': metrics.memory_percent,
                'used_gb': metrics.memory_used_gb,
                'total_gb': metrics.memory_total_gb
            },
            'swap': {
                'percent': metrics.swap_percent,
                'used_gb': metrics.swap_used_gb
            },
            'disks': [
                {
                    'mount_point': d.mount_point,
                    'percent': d.percent_used,
                    'used_gb': d.used_gb,
                    'total_gb': d.total_gb
                }
                for d in metrics.disks
            ],
            'load_average': metrics.load_average,
            'uptime_hours': metrics.uptime_seconds / 3600,
            'temperatures': metrics.temperatures,
            'gpu_count': len(metrics.gpu_usage),
            'gpu_usage': metrics.gpu_usage[0] if metrics.gpu_usage else 0
        }
    
    def get_monitor_status(self) -> Dict[str, Any]:
        """Retorna status do monitor"""
        return {
            'is_monitoring': self.is_monitoring,
            'update_interval': self.update_interval,
            'history_size': len(self.metrics_history),
            'processes_tracked': len(self.process_history),
            'system_info': self.system_info,
            'thresholds': self.thresholds,
            'alert_callbacks': len(self.alert_callbacks),
            'last_update': self.last_metrics.timestamp.isoformat() if self.last_metrics else None
        }