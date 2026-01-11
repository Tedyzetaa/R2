"""
Performance Monitor - Monitoramento avançado de performance
Análise de gargalos, otimização e profiling
"""

import logging
import time
import threading
import tracemalloc
import cProfile
import pstats
import io
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
from collections import deque, defaultdict
import gc
import sys
import os

logger = logging.getLogger(__name__)

class PerformanceLevel(Enum):
    """Níveis de performance"""
    OPTIMAL = "optimal"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    DEGRADED = "degraded"
    POOR = "poor"

class BottleneckType(Enum):
    """Tipos de gargalo"""
    CPU = "cpu"
    MEMORY = "memory"
    DISK_IO = "disk_io"
    NETWORK_IO = "network_io"
    DATABASE = "database"
    GARBAGE_COLLECTION = "garbage_collection"
    THREAD_CONTENTION = "thread_contention"
    LOCK_CONTENTION = "lock_contention"

@dataclass
class ResourceUsage:
    """Uso de recursos por componente"""
    component: str
    cpu_percent: float
    memory_mb: float
    disk_io_mbps: float
    network_io_mbps: float
    call_count: int
    avg_response_time_ms: float
    error_rate: float
    timestamp: datetime
    
    @property
    def efficiency_score(self) -> float:
        """Score de eficiência (0-100)"""
        # Penalizar alto uso de recursos com baixa produtividade
        resource_usage = (self.cpu_percent + (self.memory_mb / 100)) / 2
        productivity = 100 / max(1, self.avg_response_time_ms)
        
        if resource_usage > 0:
            efficiency = (productivity / resource_usage) * 100
            return min(efficiency, 100)
        return 100

@dataclass
class Bottleneck:
    """Gargalo identificado"""
    type: BottleneckType
    severity: float  # 0-100
    location: str
    description: str
    impact: str
    recommendations: List[str]
    timestamp: datetime
    metrics: Dict[str, float] = field(default_factory=dict)
    
    @property
    def priority(self) -> str:
        """Prioridade do gargalo"""
        if self.severity >= 80:
            return "critical"
        elif self.severity >= 60:
            return "high"
        elif self.severity >= 40:
            return "medium"
        else:
            return "low"

@dataclass
class PerformanceMetrics:
    """Métricas completas de performance"""
    timestamp: datetime
    overall_score: float  # 0-100
    performance_level: PerformanceLevel
    resource_usage: List[ResourceUsage]
    bottlenecks: List[Bottleneck]
    throughput: Dict[str, float]  # ops/segundo por tipo
    latency: Dict[str, float]  # latência por operação
    error_rates: Dict[str, float]
    garbage_collection: Dict[str, Any]
    thread_stats: Dict[str, Any]
    memory_leaks: List[Dict[str, Any]]
    profiling_data: Optional[Dict[str, Any]] = None
    
    @property
    def is_healthy(self) -> bool:
        """Se a performance está saudável"""
        return self.performance_level in [PerformanceLevel.OPTIMAL, PerformanceLevel.GOOD]
    
    @property
    def critical_bottlenecks(self) -> List[Bottleneck]:
        """Gargalos críticos"""
        return [b for b in self.bottlenecks if b.priority == "critical"]
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'overall_score': self.overall_score,
            'performance_level': self.performance_level.value,
            'is_healthy': self.is_healthy,
            'critical_bottlenecks_count': len(self.critical_bottlenecks),
            'total_bottlenecks': len(self.bottlenecks),
            'throughput_total': sum(self.throughput.values()),
            'avg_latency_ms': np.mean(list(self.latency.values())) if self.latency else 0,
            'error_rate_avg': np.mean(list(self.error_rates.values())) if self.error_rates else 0,
            'memory_leaks_count': len(self.memory_leaks),
            'resource_usage': [
                {
                    'component': r.component,
                    'efficiency_score': r.efficiency_score,
                    'cpu_percent': r.cpu_percent
                }
                for r in self.resource_usage
            ]
        }

class PerformanceMonitor:
    """
    Monitor avançado de performance
    Identifica gargalos, otimizações e problemas de performance
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Inicializa o monitor de performance
        
        Args:
            config: Configuração do monitor
        """
        self.config = config or {}
        self.update_interval = self.config.get('update_interval', 5.0)
        self.profiling_enabled = self.config.get('profiling_enabled', True)
        self.memory_leak_detection = self.config.get('memory_leak_detection', True)
        
        # Componentes monitorados
        self.components: Dict[str, Dict[str, Any]] = {}
        self.component_metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        
        # Histórico
        self.metrics_history: deque = deque(maxlen=200)
        self.bottleneck_history: Dict[BottleneckType, deque] = defaultdict(lambda: deque(maxlen=50))
        
        # Estado
        self.is_monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.last_metrics: Optional[PerformanceMetrics] = None
        
        # Trackers
        self.operation_tracker: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'count': 0,
            'total_time': 0.0,
            'errors': 0,
            'last_update': datetime.now()
        })
        
        # Callbacks
        self.alert_callbacks = []
        self.optimization_callbacks = []
        
        # Profiling
        self.profiler = None
        self.profiling_start_time = None
        
        # Limites
        self.thresholds = {
            'cpu_per_component': 50.0,
            'memory_per_component_mb': 512.0,
            'response_time_ms': 1000.0,
            'error_rate': 5.0,
            'throughput_degradation': 0.5,  # 50% redução
            'memory_growth_mb_per_min': 10.0  # 10MB/min de crescimento
        }
        
        # Inicializar trace de memória se habilitado
        if self.memory_leak_detection:
            tracemalloc.start()
            self.snapshot_start = tracemalloc.take_snapshot()
        
        logger.info("Performance Monitor inicializado")
    
    def start_monitoring(self):
        """Inicia o monitoramento"""
        if self.is_monitoring:
            logger.warning("Performance Monitor já está rodando")
            return
        
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        
        # Iniciar profiling se habilitado
        if self.profiling_enabled and not self.profiler:
            self.start_profiling()
        
        logger.info("Performance Monitor iniciado")
    
    def stop_monitoring(self):
        """Para o monitoramento"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        # Parar profiling
        if self.profiler:
            self.stop_profiling()
        
        logger.info("Performance Monitor parado")
    
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
                
                # Atualizar histórico de componentes
                self._update_component_history(metrics)
                
                # Identificar gargalos
                bottlenecks = self._identify_bottlenecks(metrics)
                metrics.bottlenecks = bottlenecks
                
                # Atualizar histórico de gargalos
                for bottleneck in bottlenecks:
                    self.bottleneck_history[bottleneck.type].append(bottleneck)
                
                # Verificar alertas
                self._check_alerts(metrics, bottlenecks)
                
                # Sugerir otimizações
                self._suggest_optimizations(bottlenecks)
                
                # Verificar memory leaks
                if self.memory_leak_detection:
                    leaks = self._detect_memory_leaks()
                    metrics.memory_leaks = leaks
                
                # Calcular tempo de processamento
                processing_time = time.time() - start_time
                
                # Aguardar próximo ciclo
                sleep_time = max(0, self.update_interval - processing_time)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    
            except Exception as e:
                logger.error(f"Erro no loop de monitoramento: {e}")
                time.sleep(10)
    
    def register_component(self, component_name: str, config: Dict[str, Any] = None):
        """
        Registra um componente para monitoramento
        
        Args:
            component_name: Nome do componente
            config: Configuração do componente
        """
        self.components[component_name] = {
            'config': config or {},
            'registered_at': datetime.now(),
            'metrics': {
                'cpu_history': deque(maxlen=100),
                'memory_history': deque(maxlen=100),
                'response_time_history': deque(maxlen=100),
                'error_history': deque(maxlen=100)
            }
        }
        
        logger.info(f"Componente registrado: {component_name}")
    
    def track_operation(self, component: str, operation: str, 
                       start_time: Optional[float] = None,
                       error: bool = False):
        """
        Rastreia uma operação
        
        Args:
            component: Nome do componente
            operation: Tipo de operação
            start_time: Timestamp de início (se None, usa tempo atual)
            error: Se a operação falhou
        """
        end_time = time.time()
        if start_time is None:
            start_time = end_time - 0.001  # Assume 1ms se não fornecido
        
        duration_ms = (end_time - start_time) * 1000
        
        # Atualizar tracker
        tracker_key = f"{component}.{operation}"
        tracker = self.operation_tracker[tracker_key]
        
        tracker['count'] += 1
        tracker['total_time'] += duration_ms
        if error:
            tracker['errors'] += 1
        tracker['last_update'] = datetime.now()
    
    def collect_metrics(self) -> PerformanceMetrics:
        """Coleta métricas completas de performance"""
        try:
            timestamp = datetime.now()
            
            # Uso de recursos por componente
            resource_usage = self._collect_resource_usage()
            
            # Throughput e latência
            throughput, latency = self._calculate_throughput_latency()
            
            # Taxas de erro
            error_rates = self._calculate_error_rates()
            
            # Garbage collection stats
            gc_stats = self._get_garbage_collection_stats()
            
            # Thread stats
            thread_stats = self._get_thread_stats()
            
            # Score geral
            overall_score = self._calculate_overall_score(
                resource_usage, throughput, latency, error_rates
            )
            
            # Nível de performance
            performance_level = self._determine_performance_level(overall_score)
            
            # Dados de profiling
            profiling_data = None
            if self.profiler and self.profiling_start_time:
                profiling_data = self._get_profiling_data()
            
            return PerformanceMetrics(
                timestamp=timestamp,
                overall_score=overall_score,
                performance_level=performance_level,
                resource_usage=resource_usage,
                bottlenecks=[],  # Será preenchido depois
                throughput=throughput,
                latency=latency,
                error_rates=error_rates,
                garbage_collection=gc_stats,
                thread_stats=thread_stats,
                memory_leaks=[],
                profiling_data=profiling_data
            )
            
        except Exception as e:
            logger.error(f"Erro ao coletar métricas de performance: {e}")
            return PerformanceMetrics(
                timestamp=datetime.now(),
                overall_score=0.0,
                performance_level=PerformanceLevel.POOR,
                resource_usage=[],
                bottlenecks=[],
                throughput={},
                latency={},
                error_rates={},
                garbage_collection={},
                thread_stats={},
                memory_leaks=[]
            )
    
    def _collect_resource_usage(self) -> List[ResourceUsage]:
        """Coleta uso de recursos por componente"""
        import psutil
        import threading
        
        current_process = psutil.Process()
        
        resource_usage = []
        
        # Coletar métricas do processo principal
        main_component_usage = ResourceUsage(
            component='main',
            cpu_percent=current_process.cpu_percent(),
            memory_mb=current_process.memory_info().rss / (1024**2),
            disk_io_mbps=0.0,  # Seria calculado com histórico
            network_io_mbps=0.0,  # Seria calculado com histórico
            call_count=0,
            avg_response_time_ms=0.0,
            error_rate=0.0,
            timestamp=datetime.now()
        )
        resource_usage.append(main_component_usage)
        
        # Coletar para componentes registrados
        for component_name, component_data in self.components.items():
            # Em implementação real, coletaríamos métricas específicas
            # Aqui usamos valores simulados
            
            avg_response_time = 0.0
            error_rate = 0.0
            call_count = 0
            
            # Calcular métricas das operações
            component_operations = {
                k: v for k, v in self.operation_tracker.items()
                if k.startswith(f"{component_name}.")
            }
            
            if component_operations:
                total_calls = sum(op['count'] for op in component_operations.values())
                total_time = sum(op['total_time'] for op in component_operations.values())
                total_errors = sum(op['errors'] for op in component_operations.values())
                
                if total_calls > 0:
                    call_count = total_calls
                    avg_response_time = total_time / total_calls
                    error_rate = (total_errors / total_calls) * 100
            
            component_usage = ResourceUsage(
                component=component_name,
                cpu_percent=np.random.uniform(5, 30),  # Simulado
                memory_mb=np.random.uniform(10, 100),  # Simulado
                disk_io_mbps=0.0,
                network_io_mbps=0.0,
                call_count=call_count,
                avg_response_time_ms=avg_response_time,
                error_rate=error_rate,
                timestamp=datetime.now()
            )
            resource_usage.append(component_usage)
        
        return resource_usage
    
    def _calculate_throughput_latency(self) -> Tuple[Dict[str, float], Dict[str, float]]:
        """Calcula throughput e latência"""
        throughput = {}
        latency = {}
        
        # Agrupar operações por tipo
        operation_groups = defaultdict(list)
        
        for op_key, tracker in self.operation_tracker.items():
            component, operation = op_key.split('.', 1)
            
            # Calcular throughput (ops/segundo)
            time_diff = (datetime.now() - tracker['last_update']).total_seconds()
            if time_diff > 0:
                ops_per_sec = tracker['count'] / time_diff
            else:
                ops_per_sec = tracker['count']
            
            # Calcular latência média
            if tracker['count'] > 0:
                avg_latency = tracker['total_time'] / tracker['count']
            else:
                avg_latency = 0.0
            
            # Adicionar ao grupo
            operation_groups[operation].append({
                'throughput': ops_per_sec,
                'latency': avg_latency
            })
        
        # Consolidar por tipo de operação
        for operation, metrics_list in operation_groups.items():
            if metrics_list:
                throughput[operation] = sum(m['throughput'] for m in metrics_list)
                latency[operation] = np.mean([m['latency'] for m in metrics_list])
        
        return throughput, latency
    
    def _calculate_error_rates(self) -> Dict[str, float]:
        """Calcula taxas de erro"""
        error_rates = {}
        
        for op_key, tracker in self.operation_tracker.items():
            component, operation = op_key.split('.', 1)
            
            if tracker['count'] > 0:
                error_rate = (tracker['errors'] / tracker['count']) * 100
                error_rates[op_key] = error_rate
        
        return error_rates
    
    def _get_garbage_collection_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas de garbage collection"""
        import gc
        
        return {
            'enabled': gc.isenabled(),
            'threshold': gc.get_threshold(),
            'count': gc.get_count(),
            'collected': sum(gc.get_count()),
            'garbage': len(gc.garbage)
        }
    
    def _get_thread_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas de threads"""
        import threading
        
        return {
            'active_count': threading.active_count(),
            'current_thread': threading.current_thread().name,
            'main_thread': threading.main_thread().name,
            'enumerate': len(threading.enumerate())
        }
    
    def _calculate_overall_score(self, resource_usage: List[ResourceUsage],
                               throughput: Dict[str, float],
                               latency: Dict[str, float],
                               error_rates: Dict[str, float]) -> float:
        """Calcula score geral de performance"""
        scores = []
        
        # Score baseado em uso de recursos
        if resource_usage:
            efficiency_scores = [r.efficiency_score for r in resource_usage]
            scores.append(np.mean(efficiency_scores))
        
        # Score baseado em throughput
        if throughput:
            # Normalizar throughput (assumindo meta de 1000 ops/seg)
            throughput_values = list(throughput.values())
            throughput_score = min(100, np.mean(throughput_values) / 10)  # 1000 ops = 100 pontos
            scores.append(throughput_score)
        
        # Score baseado em latência
        if latency:
            latency_values = list(latency.values())
            if latency_values:
                # Inverter latência (menor é melhor)
                avg_latency = np.mean(latency_values)
                latency_score = max(0, 100 - (avg_latency / 10))  # 10ms = 90 pontos
                scores.append(latency_score)
        
        # Score baseado em erros
        if error_rates:
            error_values = list(error_rates.values())
            if error_values:
                avg_error = np.mean(error_values)
                error_score = max(0, 100 - (avg_error * 2))  # 0% erro = 100 pontos
                scores.append(error_score)
        
        return np.mean(scores) if scores else 0.0
    
    def _determine_performance_level(self, score: float) -> PerformanceLevel:
        """Determina nível de performance baseado no score"""
        if score >= 90:
            return PerformanceLevel.OPTIMAL
        elif score >= 75:
            return PerformanceLevel.GOOD
        elif score >= 60:
            return PerformanceLevel.ACCEPTABLE
        elif score >= 40:
            return PerformanceLevel.DEGRADED
        else:
            return PerformanceLevel.POOR
    
    def _identify_bottlenecks(self, metrics: PerformanceMetrics) -> List[Bottleneck]:
        """Identifica gargalos de performance"""
        bottlenecks = []
        
        # 1. Gargalos de CPU
        cpu_bottlenecks = self._identify_cpu_bottlenecks(metrics)
        bottlenecks.extend(cpu_bottlenecks)
        
        # 2. Gargalos de memória
        memory_bottlenecks = self._identify_memory_bottlenecks(metrics)
        bottlenecks.extend(memory_bottlenecks)
        
        # 3. Gargalos de I/O
        io_bottlenecks = self._identify_io_bottlenecks(metrics)
        bottlenecks.extend(io_bottlenecks)
        
        # 4. Gargalos de latência
        latency_bottlenecks = self._identify_latency_bottlenecks(metrics)
        bottlenecks.extend(latency_bottlenecks)
        
        # 5. Gargalos de thread contention
        thread_bottlenecks = self._identify_thread_bottlenecks(metrics)
        bottlenecks.extend(thread_bottlenecks)
        
        return bottlenecks
    
    def _identify_cpu_bottlenecks(self, metrics: PerformanceMetrics) -> List[Bottleneck]:
        """Identifica gargalos de CPU"""
        bottlenecks = []
        
        for resource in metrics.resource_usage:
            if resource.cpu_percent > self.thresholds['cpu_per_component']:
                bottlenecks.append(Bottleneck(
                    type=BottleneckType.CPU,
                    severity=min(100, resource.cpu_percent),
                    location=resource.component,
                    description=f"Alto uso de CPU no componente {resource.component}: {resource.cpu_percent:.1f}%",
                    impact="Redução de throughput e aumento de latência",
                    recommendations=[
                        f"Otimizar algoritmos no componente {resource.component}",
                        "Considerar multiprocessamento ou threading",
                        "Implementar cache para reduzir processamento",
                        "Verificar loops infinitos ou recursão excessiva"
                    ],
                    timestamp=datetime.now(),
                    metrics={'cpu_percent': resource.cpu_percent}
                ))
        
        return bottlenecks
    
    def _identify_memory_bottlenecks(self, metrics: PerformanceMetrics) -> List[Bottleneck]:
        """Identifica gargalos de memória"""
        bottlenecks = []
        
        for resource in metrics.resource_usage:
            if resource.memory_mb > self.thresholds['memory_per_component_mb']:
                bottlenecks.append(Bottleneck(
                    type=BottleneckType.MEMORY,
                    severity=min(100, (resource.memory_mb / self.thresholds['memory_per_component_mb']) * 100),
                    location=resource.component,
                    description=f"Alto uso de memória no componente {resource.component}: {resource.memory_mb:.1f} MB",
                    impact="Swap usage, thrashing e degradação geral",
                    recommendations=[
                        f"Investigar memory leaks no componente {resource.component}",
                        "Implementar cache com limite de tamanho",
                        "Usar geradores ao invés de listas para grandes datasets",
                        "Considerar garbage collection manual para objetos grandes"
                    ],
                    timestamp=datetime.now(),
                    metrics={'memory_mb': resource.memory_mb}
                ))
        
        return bottlenecks
    
    def _identify_io_bottlenecks(self, metrics: PerformanceMetrics) -> List[Bottleneck]:
        """Identifica gargalos de I/O"""
        bottlenecks = []
        
        # Verificar latência de operações
        for operation, latency in metrics.latency.items():
            if latency > self.thresholds['response_time_ms']:
                bottlenecks.append(Bottleneck(
                    type=BottleneckType.DISK_IO,
                    severity=min(100, (latency / self.thresholds['response_time_ms']) * 50),
                    location=f"Operation: {operation}",
                    description=f"Alta latência na operação {operation}: {latency:.1f} ms",
                    impact="Experiência do usuário degradada",
                    recommendations=[
                        f"Otimizar acesso a disco para {operation}",
                        "Implementar cache em memória",
                        "Usar índices de banco de dados apropriados",
                        "Considerar batch processing"
                    ],
                    timestamp=datetime.now(),
                    metrics={'latency_ms': latency}
                ))
        
        return bottlenecks
    
    def _identify_latency_bottlenecks(self, metrics: PerformanceMetrics) -> List[Bottleneck]:
        """Identifica gargalos de latência"""
        bottlenecks = []
        
        # Verificar operações lentas
        slow_operations = [
            (op, lat) for op, lat in metrics.latency.items()
            if lat > 100  # Mais de 100ms
        ]
        
        for operation, latency in slow_operations:
            bottlenecks.append(Bottleneck(
                type=BottleneckType.CPU,  # Latência geralmente relacionada a CPU
                severity=min(100, latency / 10),
                location=f"Operation: {operation}",
                description=f"Operação {operation} lenta: {latency:.1f} ms",
                impact="Throughput reduzido e tempo de resposta alto",
                recommendations=[
                    f"Profile da operação {operation}",
                    "Otimizar algoritmos ou queries",
                    "Implementar cache",
                    "Considerar processamento assíncrono"
                ],
                timestamp=datetime.now(),
                metrics={'latency_ms': latency}
            ))
        
        return bottlenecks
    
    def _identify_thread_bottlenecks(self, metrics: PerformanceMetrics) -> List[Bottleneck]:
        """Identifica gargalos de thread contention"""
        bottlenecks = []
        
        # Verificar se há muitas threads ativas
        if metrics.thread_stats.get('active_count', 0) > 100:
            bottlenecks.append(Bottleneck(
                type=BottleneckType.THREAD_CONTENTION,
                severity=min(100, metrics.thread_stats['active_count']),
                location="System",
                description=f"Muitas threads ativas: {metrics.thread_stats['active_count']}",
                impact="Context switching overhead e uso alto de memória",
                recommendations=[
                    "Implementar thread pool com limite",
                    "Usar async/await ao invés de threads",
                    "Reduzir número de workers",
                    "Monitorar thread creation/destruction"
                ],
                timestamp=datetime.now(),
                metrics={'thread_count': metrics.thread_stats['active_count']}
            ))
        
        return bottlenecks
    
    def _detect_memory_leaks(self) -> List[Dict[str, Any]]:
        """Detecta memory leaks"""
        leaks = []
        
        if not self.memory_leak_detection:
            return leaks
        
        try:
            # Comparar snapshots de memória
            current_snapshot = tracemalloc.take_snapshot()
            top_stats = current_snapshot.compare_to(self.snapshot_start, 'lineno')
            
            # Identificar possíveis leaks
            for stat in top_stats[:10]:  # Top 10
                if stat.size_diff > 1024 * 1024:  # Mais de 1MB de crescimento
                    leaks.append({
                        'file': stat.traceback[0].filename if stat.traceback else 'Unknown',
                        'line': stat.traceback[0].lineno if stat.traceback else 0,
                        'size_diff_kb': stat.size_diff / 1024,
                        'count_diff': stat.count_diff,
                        'traceback': str(stat.traceback) if stat.traceback else ''
                    })
            
            # Atualizar snapshot para próxima comparação
            self.snapshot_start = current_snapshot
            
        except Exception as e:
            logger.debug(f"Erro na detecção de memory leaks: {e}")
        
        return leaks
    
    def start_profiling(self):
        """Inicia profiling de performance"""
        if self.profiler:
            logger.warning("Profiling já está ativo")
            return
        
        self.profiler = cProfile.Profile()
        self.profiler.enable()
        self.profiling_start_time = datetime.now()
        
        logger.info("Profiling iniciado")
    
    def stop_profiling(self):
        """Para profiling de performance"""
        if not self.profiler:
            logger.warning("Profiling não está ativo")
            return
        
        self.profiler.disable()
        self.profiling_start_time = None
        
        logger.info("Profiling parado")
    
    def _get_profiling_data(self) -> Dict[str, Any]:
        """Obtém dados de profiling"""
        if not self.profiler:
            return {}
        
        try:
            # Capturar estatísticas
            s = io.StringIO()
            ps = pstats.Stats(self.profiler, stream=s).sort_stats('cumulative')
            ps.print_stats(20)  # Top 20 funções
            
            profiling_output = s.getvalue()
            
            # Analisar output
            lines = profiling_output.split('\n')
            top_functions = []
            
            for line in lines[5:25]:  # Linhas com dados das funções
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 6:
                        try:
                            top_functions.append({
                                'calls': int(parts[0]),
                                'total_time': float(parts[3]),
                                'per_call': float(parts[4]),
                                'function': ' '.join(parts[5:])
                            })
                        except:
                            continue
            
            return {
                'output': profiling_output[:1000],  # Primeiros 1000 chars
                'top_functions': top_functions,
                'profiling_duration': (datetime.now() - self.profiling_start_time).total_seconds()
                            if self.profiling_start_time else 0
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter dados de profiling: {e}")
            return {}
    
    def _update_component_history(self, metrics: PerformanceMetrics):
        """Atualiza histórico de componentes"""
        for resource in metrics.resource_usage:
            component = resource.component
            
            self.component_metrics[component].append({
                'timestamp': resource.timestamp,
                'cpu_percent': resource.cpu_percent,
                'memory_mb': resource.memory_mb,
                'avg_response_time_ms': resource.avg_response_time_ms,
                'error_rate': resource.error_rate,
                'efficiency_score': resource.efficiency_score
            })
    
    def _check_alerts(self, metrics: PerformanceMetrics, bottlenecks: List[Bottleneck]):
        """Verifica e envia alertas"""
        alerts = []
        
        # Performance geral
        if not metrics.is_healthy:
            alerts.append({
                'type': 'performance',
                'level': 'warning',
                'message': f'Performance degradada: {metrics.performance_level.value} (score: {metrics.overall_score:.1f})',
                'performance_level': metrics.performance_level.value,
                'score': metrics.overall_score
            })
        
        # Gargalos críticos
        for bottleneck in bottlenecks:
            if bottleneck.priority == 'critical':
                alerts.append({
                    'type': 'bottleneck',
                    'level': 'critical',
                    'message': f'Gargalo crítico: {bottleneck.description}',
                    'bottleneck_type': bottleneck.type.value,
                    'severity': bottleneck.severity,
                    'location': bottleneck.location
                })
            elif bottleneck.priority == 'high':
                alerts.append({
                    'type': 'bottleneck',
                    'level': 'warning',
                    'message': f'Gargalo importante: {bottleneck.description}',
                    'bottleneck_type': bottleneck.type.value,
                    'severity': bottleneck.severity,
                    'location': bottleneck.location
                })
        
        # Memory leaks
        if metrics.memory_leaks:
            total_leak_kb = sum(leak['size_diff_kb'] for leak in metrics.memory_leaks)
            alerts.append({
                'type': 'memory_leak',
                'level': 'warning',
                'message': f'Memory leaks detectados: {len(metrics.memory_leaks)} leaks, total {total_leak_kb:.1f} KB',
                'leak_count': len(metrics.memory_leaks),
                'total_leak_kb': total_leak_kb
            })
        
        # Alto índice de erros
        for operation, error_rate in metrics.error_rates.items():
            if error_rate > self.thresholds['error_rate']:
                alerts.append({
                    'type': 'error_rate',
                    'level': 'warning',
                    'message': f'Alta taxa de erros na operação {operation}: {error_rate:.1f}%',
                    'operation': operation,
                    'error_rate': error_rate
                })
        
        # Enviar alertas para callbacks
        for alert in alerts:
            self._send_alert(alert)
    
    def _suggest_optimizations(self, bottlenecks: List[Bottleneck]):
        """Sugere otimizações baseadas nos gargalos"""
        optimizations = []
        
        # Agrupar gargalos por tipo
        bottlenecks_by_type = defaultdict(list)
        for bottleneck in bottlenecks:
            bottlenecks_by_type[bottleneck.type].append(bottleneck)
        
        # Gerar otimizações
        for bottleneck_type, b_list in bottlenecks_by_type.items():
            if b_list:
                # Encontrar gargalo mais severo deste tipo
                most_severe = max(b_list, key=lambda b: b.severity)
                
                optimization = {
                    'type': 'optimization',
                    'bottleneck_type': bottleneck_type.value,
                    'severity': most_severe.severity,
                    'location': most_severe.location,
                    'recommendations': most_severe.recommendations[:3],  # Top 3 recomendações
                    'potential_improvement': f"{min(100, most_severe.severity * 0.8):.1f}%"  # Estimativa
                }
                optimizations.append(optimization)
        
        # Enviar otimizações para callbacks
        for optimization in optimizations:
            self._send_optimization(optimization)
    
    def register_alert_callback(self, callback):
        """Registra callback para receber alertas"""
        self.alert_callbacks.append(callback)
        logger.debug(f"Callback de alerta registrado: {callback.__name__}")
    
    def register_optimization_callback(self, callback):
        """Registra callback para receber sugestões de otimização"""
        self.optimization_callbacks.append(callback)
        logger.debug(f"Callback de otimização registrado: {callback.__name__}")
    
    def _send_alert(self, alert: Dict[str, Any]):
        """Envia alerta para callbacks registrados"""
        alert['timestamp'] = datetime.now().isoformat()
        alert['source'] = 'performance_monitor'
        
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Erro no callback de alerta: {e}")
    
    def _send_optimization(self, optimization: Dict[str, Any]):
        """Envia sugestão de otimização para callbacks"""
        optimization['timestamp'] = datetime.now().isoformat()
        optimization['source'] = 'performance_monitor'
        
        for callback in self.optimization_callbacks:
            try:
                callback(optimization)
            except Exception as e:
                logger.error(f"Erro no callback de otimização: {e}")
    
    def get_current_metrics(self) -> Optional[PerformanceMetrics]:
        """Obtém métricas atuais"""
        return self.last_metrics
    
    def get_component_history(self, component: str, hours: int = 1) -> List[Dict[str, Any]]:
        """Obtém histórico de um componente"""
        if component not in self.component_metrics:
            return []
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        history = []
        for entry in self.component_metrics[component]:
            if entry['timestamp'] >= cutoff_time:
                history.append(entry)
        
        return history
    
    def get_bottleneck_history(self, bottleneck_type: Optional[str] = None, 
                             hours: int = 24) -> List[Bottleneck]:
        """Obtém histórico de gargalos"""
        if bottleneck_type:
            # Histórico específico
            bt_enum = BottleneckType(bottleneck_type)
            if bt_enum not in self.bottleneck_history:
                return []
            
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            history = []
            for bottleneck in self.bottleneck_history[bt_enum]:
                if bottleneck.timestamp >= cutoff_time:
                    history.append(bottleneck)
            
            return history
        else:
            # Todos os gargalos
            all_bottlenecks = []
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            for bottlenecks in self.bottleneck_history.values():
                for bottleneck in bottlenecks:
                    if bottleneck.timestamp >= cutoff_time:
                        all_bottlenecks.append(bottleneck)
            
            # Ordenar por severidade
            all_bottlenecks.sort(key=lambda b: b.severity, reverse=True)
            return all_bottlenecks
    
    def profile_function(self, func: Callable, *args, **kwargs) -> Dict[str, Any]:
        """
        Profile uma função específica
        
        Args:
            func: Função para profile
            *args, **kwargs: Argumentos para a função
            
        Returns:
            Estatísticas de profiling
        """
        import time
        
        start_time = time.time()
        start_memory = self._get_current_memory()
        
        # Executar função
        result = func(*args, **kwargs)
        
        end_time = time.time()
        end_memory = self._get_current_memory()
        
        execution_time = end_time - start_time
        memory_used = end_memory - start_memory
        
        return {
            'function': func.__name__,
            'execution_time_ms': execution_time * 1000,
            'memory_used_mb': memory_used / (1024**2),
            'result': result if result is None else str(result)[:100],
            'success': True
        }
    
    def _get_current_memory(self) -> int:
        """Obtém uso atual de memória"""
        import psutil
        process = psutil.Process()
        return process.memory_info().rss
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Obtém resumo de performance"""
        if not self.last_metrics:
            return {}
        
        metrics = self.last_metrics
        
        return {
            'timestamp': metrics.timestamp.isoformat(),
            'overall_score': metrics.overall_score,
            'performance_level': metrics.performance_level.value,
            'is_healthy': metrics.is_healthy,
            'critical_bottlenecks': len(metrics.critical_bottlenecks),
            'total_throughput': sum(metrics.throughput.values()),
            'avg_latency_ms': np.mean(list(metrics.latency.values())) if metrics.latency else 0,
            'avg_error_rate': np.mean(list(metrics.error_rates.values())) if metrics.error_rates else 0,
            'memory_leaks': len(metrics.memory_leaks),
            'components_monitored': len(self.components),
            'active_threads': metrics.thread_stats.get('active_count', 0),
            'gc_enabled': metrics.garbage_collection.get('enabled', False)
        }
    
    def get_monitor_status(self) -> Dict[str, Any]:
        """Retorna status do monitor"""
        return {
            'is_monitoring': self.is_monitoring,
            'update_interval': self.update_interval,
            'profiling_enabled': self.profiling_enabled,
            'memory_leak_detection': self.memory_leak_detection,
            'components_registered': len(self.components),
            'operations_tracked': len(self.operation_tracker),
            'metrics_history': len(self.metrics_history),
            'thresholds': self.thresholds,
            'alert_callbacks': len(self.alert_callbacks),
            'optimization_callbacks': len(self.optimization_callbacks),
            'last_update': self.last_metrics.timestamp.isoformat() if self.last_metrics else None
        }