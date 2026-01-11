"""
Network Monitor - Monitoramento avançado de rede
Latência, conectividade, tráfego e segurança
"""

import logging
import socket
import threading
import time
import subprocess
import select
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import ping3
import dns.resolver
import speedtest
from collections import deque
import requests
import ssl
import whois

logger = logging.getLogger(__name__)

class NetworkStatus(Enum):
    """Status da rede"""
    ONLINE = "online"
    DEGRADED = "degraded"
    OFFLINE = "offline"
    UNKNOWN = "unknown"

class SecurityLevel(Enum):
    """Nível de segurança"""
    SECURE = "secure"
    WARNING = "warning"
    INSECURE = "insecure"
    UNKNOWN = "unknown"

@dataclass
class LatencyTest:
    """Teste de latência"""
    target: str
    timestamp: datetime
    latency_ms: float
    packet_loss: float
    jitter_ms: float
    success: bool
    error: str = ""
    
    @property
    def status(self) -> NetworkStatus:
        """Status baseado na latência"""
        if not self.success:
            return NetworkStatus.OFFLINE
        elif self.latency_ms > 200:
            return NetworkStatus.DEGRADED
        else:
            return NetworkStatus.ONLINE

@dataclass
class ConnectionInfo:
    """Informações de conexão"""
    local_ip: str
    remote_ip: str
    remote_port: int
    local_port: int
    status: str
    pid: Optional[int]
    process_name: Optional[str]
    protocol: str
    state: str
    
    @property
    def is_external(self) -> bool:
        """Se é uma conexão externa"""
        # Verificar se IP remoto não é local
        local_prefixes = ['192.168.', '10.', '172.16.', '127.', 'localhost']
        return not any(remote_ip.startswith(prefix) for prefix in local_prefixes)

@dataclass
class NetworkMetrics:
    """Métricas completas de rede"""
    timestamp: datetime
    public_ip: str
    dns_servers: List[str]
    gateway: str
    interfaces: List[Dict[str, Any]]
    latency_tests: List[LatencyTest]
    connections: List[ConnectionInfo]
    bandwidth_down_mbps: Optional[float]
    bandwidth_up_mbps: Optional[float]
    packet_loss: float
    dns_resolution_time: float
    ssl_expiry_days: Dict[str, int]
    open_ports: List[int]
    security_alerts: List[Dict[str, Any]]
    
    @property
    def overall_status(self) -> NetworkStatus:
        """Status geral da rede"""
        if not self.latency_tests:
            return NetworkStatus.UNKNOWN
        
        online_tests = [t for t in self.latency_tests if t.status == NetworkStatus.ONLINE]
        degraded_tests = [t for t in self.latency_tests if t.status == NetworkStatus.DEGRADED]
        
        if len(online_tests) >= len(self.latency_tests) * 0.8:
            return NetworkStatus.ONLINE
        elif len(degraded_tests) > 0 or len(online_tests) > 0:
            return NetworkStatus.DEGRADED
        else:
            return NetworkStatus.OFFLINE
    
    @property
    def security_status(self) -> SecurityLevel:
        """Status de segurança"""
        if not self.security_alerts:
            return SecurityLevel.SECURE
        
        critical_alerts = [a for a in self.security_alerts if a.get('level') == 'critical']
        warning_alerts = [a for a in self.security_alerts if a.get('level') == 'warning']
        
        if critical_alerts:
            return SecurityLevel.INSECURE
        elif warning_alerts:
            return SecurityLevel.WARNING
        else:
            return SecurityLevel.SECURE
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'public_ip': self.public_ip,
            'overall_status': self.overall_status.value,
            'security_status': self.security_status.value,
            'bandwidth_down_mbps': self.bandwidth_down_mbps,
            'bandwidth_up_mbps': self.bandwidth_up_mbps,
            'average_latency_ms': np.mean([t.latency_ms for t in self.latency_tests if t.success]) 
                                if any(t.success for t in self.latency_tests) else None,
            'packet_loss': self.packet_loss,
            'active_connections': len(self.connections),
            'external_connections': len([c for c in self.connections if c.is_external]),
            'security_alerts': len(self.security_alerts)
        }

class NetworkMonitor:
    """
    Monitor avançado de rede
    Testes de conectividade, performance e segurança
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Inicializa o monitor de rede
        
        Args:
            config: Configuração do monitor
        """
        self.config = config or {}
        self.update_interval = self.config.get('update_interval', 30.0)
        self.bandwidth_test_interval = self.config.get('bandwidth_test_interval', 300.0)  # 5 minutos
        
        # Targets para teste
        self.latency_targets = self.config.get('latency_targets', [
            '8.8.8.8',  # Google DNS
            '1.1.1.1',  # Cloudflare DNS
            '208.67.222.222',  # OpenDNS
            'www.google.com',
            'www.cloudflare.com'
        ])
        
        # Histórico
        self.metrics_history: deque = deque(maxlen=100)
        self.latency_history: Dict[str, deque] = {}
        
        # Estado
        self.is_monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.last_metrics: Optional[NetworkMetrics] = None
        self.last_bandwidth_test: Optional[datetime] = None
        
        # Speedtest client
        self.speedtest_client = None
        
        # Callbacks para alertas
        self.alert_callbacks = []
        
        # Limites
        self.thresholds = {
            'latency_warning': 100.0,  # ms
            'latency_critical': 200.0,  # ms
            'packet_loss_warning': 5.0,  # %
            'packet_loss_critical': 10.0,  # %
            'bandwidth_degradation': 0.5  # 50% da banda esperada
        }
        
        logger.info("Network Monitor inicializado")
    
    def start_monitoring(self):
        """Inicia o monitoramento"""
        if self.is_monitoring:
            logger.warning("Network Monitor já está rodando")
            return
        
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        
        logger.info("Network Monitor iniciado")
    
    def stop_monitoring(self):
        """Para o monitoramento"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        logger.info("Network Monitor parado")
    
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
                
                # Atualizar histórico de latência
                self._update_latency_history(metrics)
                
                # Verificar alertas
                self._check_alerts(metrics)
                
                # Calcular tempo de processamento
                processing_time = time.time() - start_time
                
                # Aguardar próximo ciclo
                sleep_time = max(0, self.update_interval - processing_time)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    
            except Exception as e:
                logger.error(f"Erro no loop de monitoramento: {e}")
                time.sleep(30)
    
    def collect_metrics(self) -> NetworkMetrics:
        """Coleta métricas completas de rede"""
        try:
            timestamp = datetime.now()
            
            # IP público
            public_ip = self._get_public_ip()
            
            # Servidores DNS
            dns_servers = self._get_dns_servers()
            
            # Gateway
            gateway = self._get_default_gateway()
            
            # Interfaces de rede
            interfaces = self._get_network_interfaces()
            
            # Testes de latência
            latency_tests = []
            for target in self.latency_targets:
                latency_test = self._test_latency(target)
                latency_tests.append(latency_test)
            
            # Conexões ativas
            connections = self._get_active_connections()
            
            # Teste de banda (ocasional)
            bandwidth_down = bandwidth_up = None
            if (not self.last_bandwidth_test or 
                (timestamp - self.last_bandwidth_test).total_seconds() >= self.bandwidth_test_interval):
                try:
                    bandwidth_down, bandwidth_up = self._test_bandwidth()
                    self.last_bandwidth_test = timestamp
                except Exception as e:
                    logger.warning(f"Erro no teste de banda: {e}")
            
            # Perda de pacotes média
            successful_tests = [t for t in latency_tests if t.success]
            if successful_tests:
                packet_loss = sum(t.packet_loss for t in successful_tests) / len(successful_tests)
            else:
                packet_loss = 100.0
            
            # Tempo de resolução DNS
            dns_resolution_time = self._test_dns_resolution()
            
            # Verificações SSL
            ssl_expiry_days = self._check_ssl_certificates()
            
            # Portas abertas (verificação local)
            open_ports = self._scan_open_ports()
            
            # Alertas de segurança
            security_alerts = self._check_security(connections, open_ports)
            
            return NetworkMetrics(
                timestamp=timestamp,
                public_ip=public_ip,
                dns_servers=dns_servers,
                gateway=gateway,
                interfaces=interfaces,
                latency_tests=latency_tests,
                connections=connections,
                bandwidth_down_mbps=bandwidth_down,
                bandwidth_up_mbps=bandwidth_up,
                packet_loss=packet_loss,
                dns_resolution_time=dns_resolution_time,
                ssl_expiry_days=ssl_expiry_days,
                open_ports=open_ports,
                security_alerts=security_alerts
            )
            
        except Exception as e:
            logger.error(f"Erro ao coletar métricas de rede: {e}")
            # Retornar métricas mínimas em caso de erro
            return NetworkMetrics(
                timestamp=datetime.now(),
                public_ip="",
                dns_servers=[],
                gateway="",
                interfaces=[],
                latency_tests=[],
                connections=[],
                bandwidth_down_mbps=None,
                bandwidth_up_mbps=None,
                packet_loss=100.0,
                dns_resolution_time=0.0,
                ssl_expiry_days={},
                open_ports=[],
                security_alerts=[]
            )
    
    def _get_public_ip(self) -> str:
        """Obtém IP público"""
        try:
            # Tentar múltiplos serviços
            services = [
                'https://api.ipify.org',
                'https://icanhazip.com',
                'https://checkip.amazonaws.com'
            ]
            
            for service in services:
                try:
                    response = requests.get(service, timeout=5)
                    if response.status_code == 200:
                        return response.text.strip()
                except:
                    continue
            
            return "Não disponível"
            
        except Exception as e:
            logger.debug(f"Erro ao obter IP público: {e}")
            return "Erro"
    
    def _get_dns_servers(self) -> List[str]:
        """Obtém servidores DNS configurados"""
        try:
            import platform
            
            dns_servers = []
            
            if platform.system() == 'Windows':
                import subprocess
                output = subprocess.check_output(['ipconfig', '/all']).decode('utf-8')
                
                for line in output.split('\n'):
                    if 'DNS Servers' in line:
                        parts = line.split(':')
                        if len(parts) > 1:
                            dns_servers.append(parts[1].strip())
            
            elif platform.system() == 'Linux':
                with open('/etc/resolv.conf', 'r') as f:
                    for line in f:
                        if line.startswith('nameserver'):
                            dns_servers.append(line.split()[1].strip())
            
            elif platform.system() == 'Darwin':  # macOS
                output = subprocess.check_output(['scutil', '--dns']).decode('utf-8')
                for line in output.split('\n'):
                    if 'nameserver' in line.lower():
                        parts = line.split()
                        if len(parts) > 1:
                            dns_servers.append(parts[1].strip())
            
            return dns_servers
            
        except Exception as e:
            logger.debug(f"Erro ao obter servidores DNS: {e}")
            return []
    
    def _get_default_gateway(self) -> str:
        """Obtém gateway padrão"""
        try:
            import platform
            
            if platform.system() == 'Windows':
                import subprocess
                output = subprocess.check_output(['ipconfig']).decode('utf-8')
                
                for line in output.split('\n'):
                    if 'Default Gateway' in line:
                        parts = line.split(':')
                        if len(parts) > 1:
                            return parts[1].strip()
            
            elif platform.system() in ['Linux', 'Darwin']:
                import subprocess
                output = subprocess.check_output(['netstat', '-rn']).decode('utf-8')
                
                for line in output.split('\n'):
                    if 'default' in line.lower() or '0.0.0.0' in line:
                        parts = line.split()
                        if len(parts) > 1:
                            return parts[1]
            
            return "Não disponível"
            
        except Exception as e:
            logger.debug(f"Erro ao obter gateway: {e}")
            return "Erro"
    
    def _get_network_interfaces(self) -> List[Dict[str, Any]]:
        """Obtém interfaces de rede"""
        try:
            import psutil
            import netifaces
            
            interfaces = []
            
            for interface_name, addrs in psutil.net_if_addrs().items():
                interface_info = {
                    'name': interface_name,
                    'addresses': [],
                    'is_up': False
                }
                
                # Verificar status
                stats = psutil.net_if_stats().get(interface_name)
                if stats:
                    interface_info['is_up'] = stats.isup
                    interface_info['speed_mbps'] = stats.speed
                    interface_info['mtu'] = stats.mtu
                
                # Endereços
                for addr in addrs:
                    addr_info = {
                        'family': 'IPv4' if addr.family == socket.AF_INET else 
                                 'IPv6' if addr.family == socket.AF_INET6 else
                                 'MAC' if addr.family == psutil.AF_LINK else 'Other',
                        'address': addr.address,
                        'netmask': addr.netmask,
                        'broadcast': addr.broadcast
                    }
                    interface_info['addresses'].append(addr_info)
                
                # Estatísticas
                io_stats = psutil.net_io_counters(pernic=True).get(interface_name)
                if io_stats:
                    interface_info['bytes_sent'] = io_stats.bytes_sent
                    interface_info['bytes_recv'] = io_stats.bytes_recv
                    interface_info['packets_sent'] = io_stats.packets_sent
                    interface_info['packets_recv'] = io_stats.packets_recv
                    interface_info['errors_in'] = io_stats.errin
                    interface_info['errors_out'] = io_stats.errout
                    interface_info['drops_in'] = io_stats.dropin
                    interface_info['drops_out'] = io_stats.dropout
                
                interfaces.append(interface_info)
            
            return interfaces
            
        except Exception as e:
            logger.debug(f"Erro ao obter interfaces: {e}")
            return []
    
    def _test_latency(self, target: str) -> LatencyTest:
        """Testa latência para um target"""
        try:
            # Usar ping3 para latência
            latency = ping3.ping(target, timeout=2, unit='ms')
            
            if latency is not None and latency > 0:
                # Simular jitter e packet loss para demonstração
                # Em produção, faríamos múltiplos pings
                jitter = max(0, np.random.normal(1, 0.5))
                packet_loss = 0.0  # ping3 não fornece packet loss
                
                return LatencyTest(
                    target=target,
                    timestamp=datetime.now(),
                    latency_ms=float(latency),
                    packet_loss=packet_loss,
                    jitter_ms=jitter,
                    success=True
                )
            else:
                return LatencyTest(
                    target=target,
                    timestamp=datetime.now(),
                    latency_ms=0.0,
                    packet_loss=100.0,
                    jitter_ms=0.0,
                    success=False,
                    error="Timeout ou host não encontrado"
                )
            
        except Exception as e:
            logger.debug(f"Erro no teste de latência para {target}: {e}")
            return LatencyTest(
                target=target,
                timestamp=datetime.now(),
                latency_ms=0.0,
                packet_loss=100.0,
                jitter_ms=0.0,
                success=False,
                error=str(e)
            )
    
    def _get_active_connections(self) -> List[ConnectionInfo]:
        """Obtém conexões ativas"""
        try:
            import psutil
            
            connections = []
            
            for conn in psutil.net_connections(kind='inet'):
                try:
                    # Obter informações do processo
                    pid = conn.pid
                    process_name = ""
                    
                    if pid:
                        try:
                            proc = psutil.Process(pid)
                            process_name = proc.name()
                        except:
                            process_name = "Unknown"
                    
                    # Determinar protocolo
                    protocol = 'tcp' if conn.type == socket.SOCK_STREAM else 'udp'
                    
                    connections.append(ConnectionInfo(
                        local_ip=conn.laddr.ip if conn.laddr else "",
                        remote_ip=conn.raddr.ip if conn.raddr else "",
                        remote_port=conn.raddr.port if conn.raddr else 0,
                        local_port=conn.laddr.port if conn.laddr else 0,
                        status=conn.status if hasattr(conn, 'status') else "",
                        pid=pid,
                        process_name=process_name,
                        protocol=protocol,
                        state=getattr(conn, 'status', 'N/A')
                    ))
                    
                except Exception as e:
                    logger.debug(f"Erro ao processar conexão: {e}")
                    continue
            
            return connections
            
        except Exception as e:
            logger.debug(f"Erro ao obter conexões: {e}")
            return []
    
    def _test_bandwidth(self) -> Tuple[Optional[float], Optional[float]]:
        """Testa largura de banda"""
        try:
            # Usar speedtest-cli
            if self.speedtest_client is None:
                self.speedtest_client = speedtest.Speedtest()
                self.speedtest_client.get_best_server()
            
            # Testar download
            download_speed = self.speedtest_client.download() / 1_000_000  # Converter para Mbps
            
            # Testar upload
            upload_speed = self.speedtest_client.upload() / 1_000_000  # Converter para Mbps
            
            return download_speed, upload_speed
            
        except Exception as e:
            logger.warning(f"Erro no teste de banda: {e}")
            return None, None
    
    def _test_dns_resolution(self) -> float:
        """Testa tempo de resolução DNS"""
        try:
            resolver = dns.resolver.Resolver()
            resolver.nameservers = ['8.8.8.8']  # Usar Google DNS
            
            start_time = time.time()
            resolver.resolve('google.com', 'A')
            end_time = time.time()
            
            return (end_time - start_time) * 1000  # ms
            
        except Exception as e:
            logger.debug(f"Erro no teste DNS: {e}")
            return 0.0
    
    def _check_ssl_certificates(self) -> Dict[str, int]:
        """Verifica certificados SSL de sites importantes"""
        sites = [
            'google.com',
            'github.com',
            'cloudflare.com',
            'letsencrypt.org'
        ]
        
        ssl_expiry = {}
        
        for site in sites:
            try:
                context = ssl.create_default_context()
                with socket.create_connection((site, 443), timeout=5) as sock:
                    with context.wrap_socket(sock, server_hostname=site) as ssock:
                        cert = ssock.getpeercert()
                        
                        # Extrair data de expiração
                        expire_date = cert['notAfter']
                        expire_datetime = datetime.strptime(expire_date, '%b %d %H:%M:%S %Y %Z')
                        
                        days_until_expiry = (expire_datetime - datetime.now()).days
                        ssl_expiry[site] = days_until_expiry
                        
            except Exception as e:
                logger.debug(f"Erro ao verificar SSL de {site}: {e}")
                ssl_expiry[site] = -1
        
        return ssl_expiry
    
    def _scan_open_ports(self, ports: List[int] = None) -> List[int]:
        """Escaneia portas abertas localmente"""
        if ports is None:
            ports = [21, 22, 23, 25, 53, 80, 110, 143, 443, 465, 587, 993, 995, 3306, 3389, 5432]
        
        open_ports = []
        
        for port in ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex(('127.0.0.1', port))
                sock.close()
                
                if result == 0:
                    open_ports.append(port)
                    
            except:
                continue
        
        return open_ports
    
    def _check_security(self, connections: List[ConnectionInfo], 
                       open_ports: List[int]) -> List[Dict[str, Any]]:
        """Verifica problemas de segurança"""
        alerts = []
        
        # Portas potencialmente perigosas abertas
        dangerous_ports = {
            21: 'FTP (não seguro)',
            23: 'Telnet (não seguro)',
            25: 'SMTP (potencialmente aberto)',
            135: 'RPC (Windows)',
            139: 'NetBIOS',
            445: 'SMB (potencial vulnerabilidade)',
            1433: 'SQL Server',
            3306: 'MySQL',
            3389: 'RDP (Windows Remote Desktop)',
            5432: 'PostgreSQL',
            5900: 'VNC'
        }
        
        for port in open_ports:
            if port in dangerous_ports:
                alerts.append({
                    'level': 'warning',
                    'type': 'open_port',
                    'message': f'Porta {port} ({dangerous_ports[port]}) aberta localmente',
                    'port': port,
                    'service': dangerous_ports[port]
                })
        
        # Conexões suspeitas
        suspicious_connections = []
        for conn in connections:
            # Conexões para portas conhecidas de malware
            if conn.remote_port in [4444, 5555, 6666, 7777, 8888, 9999]:
                suspicious_connections.append(conn)
            
            # Conexões de processos desconhecidos
            if conn.process_name and 'unknown' in conn.process_name.lower():
                suspicious_connections.append(conn)
        
        for conn in suspicious_connections:
            alerts.append({
                'level': 'warning',
                'type': 'suspicious_connection',
                'message': f'Conexão suspeita: {conn.process_name} para {conn.remote_ip}:{conn.remote_port}',
                'process': conn.process_name,
                'remote_ip': conn.remote_ip,
                'remote_port': conn.remote_port
            })
        
        # Verificar SSL expirado
        for site, days in self._check_ssl_certificates().items():
            if 0 < days < 7:  # Expira em menos de 7 dias
                alerts.append({
                    'level': 'warning',
                    'type': 'ssl_expiring',
                    'message': f'Certificado SSL de {site} expira em {days} dias',
                    'site': site,
                    'days_until_expiry': days
                })
            elif days < 0:  # Já expirado
                alerts.append({
                    'level': 'critical',
                    'type': 'ssl_expired',
                    'message': f'Certificado SSL de {site} expirado',
                    'site': site
                })
        
        return alerts
    
    def _update_latency_history(self, metrics: NetworkMetrics):
        """Atualiza histórico de latência"""
        for test in metrics.latency_tests:
            target = test.target
            
            if target not in self.latency_history:
                self.latency_history[target] = deque(maxlen=100)
            
            self.latency_history[target].append({
                'timestamp': test.timestamp,
                'latency_ms': test.latency_ms,
                'success': test.success
            })
    
    def _check_alerts(self, metrics: NetworkMetrics):
        """Verifica e envia alertas"""
        alerts = []
        
        # Status geral
        if metrics.overall_status == NetworkStatus.OFFLINE:
            alerts.append({
                'type': 'network_status',
                'level': 'critical',
                'message': 'Rede offline - sem conectividade com a internet',
                'status': 'offline'
            })
        elif metrics.overall_status == NetworkStatus.DEGRADED:
            alerts.append({
                'type': 'network_status',
                'level': 'warning',
                'message': 'Rede degradada - alta latência ou perda de pacotes',
                'status': 'degraded'
            })
        
        # Latência alta
        for test in metrics.latency_tests:
            if test.success and test.latency_ms > self.thresholds['latency_critical']:
                alerts.append({
                    'type': 'latency',
                    'level': 'critical',
                    'message': f'Latência crítica para {test.target}: {test.latency_ms:.1f}ms',
                    'target': test.target,
                    'latency_ms': test.latency_ms,
                    'threshold': self.thresholds['latency_critical']
                })
            elif test.success and test.latency_ms > self.thresholds['latency_warning']:
                alerts.append({
                    'type': 'latency',
                    'level': 'warning',
                    'message': f'Latência alta para {test.target}: {test.latency_ms:.1f}ms',
                    'target': test.target,
                    'latency_ms': test.latency_ms,
                    'threshold': self.thresholds['latency_warning']
                })
        
        # Perda de pacotes
        if metrics.packet_loss > self.thresholds['packet_loss_critical']:
            alerts.append({
                'type': 'packet_loss',
                'level': 'critical',
                'message': f'Perda de pacotes crítica: {metrics.packet_loss:.1f}%',
                'packet_loss': metrics.packet_loss,
                'threshold': self.thresholds['packet_loss_critical']
            })
        elif metrics.packet_loss > self.thresholds['packet_loss_warning']:
            alerts.append({
                'type': 'packet_loss',
                'level': 'warning',
                'message': f'Perda de pacotes alta: {metrics.packet_loss:.1f}%',
                'packet_loss': metrics.packet_loss,
                'threshold': self.thresholds['packet_loss_warning']
            })
        
        # DNS lento
        if metrics.dns_resolution_time > 1000:  # Mais de 1 segundo
            alerts.append({
                'type': 'dns',
                'level': 'warning',
                'message': f'Resolução DNS lenta: {metrics.dns_resolution_time:.1f}ms',
                'resolution_time': metrics.dns_resolution_time
            })
        
        # Alertas de segurança
        for security_alert in metrics.security_alerts:
            alerts.append({
                'type': 'security',
                'level': security_alert['level'],
                'message': security_alert['message'],
                'details': security_alert
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
        alert['source'] = 'network_monitor'
        
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Erro no callback de alerta: {e}")
    
    def get_current_metrics(self) -> Optional[NetworkMetrics]:
        """Obtém métricas atuais"""
        return self.last_metrics
    
    def get_latency_history(self, target: str, hours: int = 24) -> List[Dict[str, Any]]:
        """Obtém histórico de latência para um target"""
        if target not in self.latency_history:
            return []
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        history = []
        for entry in self.latency_history[target]:
            if entry['timestamp'] >= cutoff_time:
                history.append(entry)
        
        return history
    
    def get_bandwidth_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Obtém histórico de largura de banda"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        history = []
        for metrics in self.metrics_history:
            if metrics.timestamp >= cutoff_time and metrics.bandwidth_down_mbps:
                history.append({
                    'timestamp': metrics.timestamp,
                    'download_mbps': metrics.bandwidth_down_mbps,
                    'upload_mbps': metrics.bandwidth_up_mbps
                })
        
        return history
    
    def test_connection_to(self, host: str, port: int = 80, timeout: int = 5) -> Dict[str, Any]:
        """Testa conexão específica"""
        try:
            start_time = time.time()
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            end_time = time.time()
            
            sock.close()
            
            return {
                'host': host,
                'port': port,
                'success': result == 0,
                'response_time_ms': (end_time - start_time) * 1000,
                'error': 'Connection refused' if result == 111 else 'Timeout' if result == 110 else f'Error {result}'
            }
            
        except Exception as e:
            return {
                'host': host,
                'port': port,
                'success': False,
                'response_time_ms': 0,
                'error': str(e)
            }
    
    def get_network_summary(self) -> Dict[str, Any]:
        """Obtém resumo da rede"""
        if not self.last_metrics:
            return {}
        
        metrics = self.last_metrics
        
        return {
            'timestamp': metrics.timestamp.isoformat(),
            'public_ip': metrics.public_ip,
            'overall_status': metrics.overall_status.value,
            'security_status': metrics.security_status.value,
            'gateway': metrics.gateway,
            'dns_servers': metrics.dns_servers,
            'average_latency_ms': np.mean([t.latency_ms for t in metrics.latency_tests if t.success]) 
                                if any(t.success for t in metrics.latency_tests) else None,
            'packet_loss_percent': metrics.packet_loss,
            'bandwidth_down_mbps': metrics.bandwidth_down_mbps,
            'bandwidth_up_mbps': metrics.bandwidth_up_mbps,
            'active_connections': len(metrics.connections),
            'external_connections': len([c for c in metrics.connections if c.is_external]),
            'open_ports': len(metrics.open_ports),
            'security_alerts': len(metrics.security_alerts),
            'interfaces': [
                {
                    'name': i['name'],
                    'is_up': i.get('is_up', False),
                    'ip_addresses': [a['address'] for a in i.get('addresses', []) 
                                   if a['family'] in ['IPv4', 'IPv6']]
                }
                for i in metrics.interfaces
            ]
        }
    
    def get_monitor_status(self) -> Dict[str, Any]:
        """Retorna status do monitor"""
        return {
            'is_monitoring': self.is_monitoring,
            'update_interval': self.update_interval,
            'bandwidth_test_interval': self.bandwidth_test_interval,
            'latency_targets': self.latency_targets,
            'history_size': len(self.metrics_history),
            'thresholds': self.thresholds,
            'alert_callbacks': len(self.alert_callbacks),
            'last_update': self.last_metrics.timestamp.isoformat() if self.last_metrics else None,
            'last_bandwidth_test': self.last_bandwidth_test.isoformat() if self.last_bandwidth_test else None
        }