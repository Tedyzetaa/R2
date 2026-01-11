"""
Analytics and metrics collection system for R2 Assistant
"""

import time
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from collections import deque, defaultdict
import numpy as np

@dataclass
class MetricPoint:
    """Single data point for a metric"""
    timestamp: float
    value: float
    tags: Dict[str, str] = field(default_factory=dict)

@dataclass
class MetricSummary:
    """Summary statistics for a metric"""
    name: str
    count: int
    mean: float
    median: float
    min: float
    max: float
    std_dev: float
    last_value: float
    trend: float  # Slope of recent values
    
class Analytics:
    """
    Collects and analyzes system metrics in real-time
    """
    
    def __init__(self, retention_hours: int = 24, max_points_per_metric: int = 10000):
        self.retention_hours = retention_hours
        self.max_points = max_points_per_metric
        
        # Store metrics by name
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_points_per_metric))
        
        # System counters
        self.counters: Dict[str, int] = defaultdict(int)
        self.gauges: Dict[str, float] = defaultdict(float)
        
        # Response time tracking
        self.response_times: Dict[str, List[float]] = defaultdict(list)
        
        # Start time for uptime calculation
        self.start_time = time.time()
        
        # Performance windows
        self.window_sizes = [60, 300, 3600]  # 1min, 5min, 1hr
        
    def record_metric(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Record a metric value with optional tags"""
        point = MetricPoint(
            timestamp=time.time(),
            value=value,
            tags=tags or {}
        )
        
        self.metrics[name].append(point)
        
        # Clean old data
        self._clean_old_data(name)
    
    def increment_counter(self, name: str, amount: int = 1):
        """Increment a counter"""
        self.counters[name] += amount
    
    def set_gauge(self, name: str, value: float):
        """Set a gauge value"""
        self.gauges[name] = value
    
    def record_response_time(self, operation: str, response_time: float):
        """Record response time for an operation"""
        self.response_times[operation].append(response_time)
        
        # Keep only recent data
        if len(self.response_times[operation]) > 1000:
            self.response_times[operation] = self.response_times[operation][-1000:]
    
    def get_metric_summary(self, name: str, window_minutes: int = 60) -> Optional[MetricSummary]:
        """Get summary statistics for a metric"""
        if name not in self.metrics or not self.metrics[name]:
            return None
        
        cutoff = time.time() - (window_minutes * 60)
        recent_points = [
            p for p in self.metrics[name] 
            if p.timestamp >= cutoff
        ]
        
        if not recent_points:
            return None
        
        values = [p.value for p in recent_points]
        
        # Calculate trend (slope of last 10 points)
        trend = 0.0
        if len(values) >= 10:
            x = list(range(len(values[-10:])))
            y = values[-10:]
            try:
                trend = np.polyfit(x, y, 1)[0]
            except:
                trend = 0.0
        
        return MetricSummary(
            name=name,
            count=len(values),
            mean=statistics.mean(values),
            median=statistics.median(values),
            min=min(values),
            max=max(values),
            std_dev=statistics.stdev(values) if len(values) > 1 else 0.0,
            last_value=values[-1],
            trend=trend
        )
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        report = {
            'uptime_hours': (time.time() - self.start_time) / 3600,
            'counters': dict(self.counters),
            'gauges': dict(self.gauges),
            'response_times': {},
            'metric_summaries': {},
            'health_score': self._calculate_health_score(),
            'timestamp': datetime.now().isoformat()
        }
        
        # Response time statistics
        for operation, times in self.response_times.items():
            if times:
                report['response_times'][operation] = {
                    'count': len(times),
                    'mean': statistics.mean(times),
                    'p95': np.percentile(times, 95) if len(times) >= 5 else times[-1],
                    'p99': np.percentile(times, 99) if len(times) >= 10 else times[-1],
                    'max': max(times),
                    'min': min(times)
                }
        
        # Key metric summaries
        key_metrics = [
            'voice_recognition_accuracy',
            'ai_response_time',
            'system_cpu_usage',
            'system_memory_usage',
            'network_latency'
        ]
        
        for metric in key_metrics:
            if metric in self.metrics and self.metrics[metric]:
                summary = self.get_metric_summary(metric, 60)
                if summary:
                    report['metric_summaries'][metric] = {
                        'mean': summary.mean,
                        'trend': summary.trend,
                        'last_value': summary.last_value
                    }
        
        # Window-based analysis
        for window in self.window_sizes:
            report[f'last_{window}s'] = self._get_window_analysis(window)
        
        return report
    
    def _get_window_analysis(self, window_seconds: int) -> Dict[str, Any]:
        """Analyze metrics for a specific time window"""
        cutoff = time.time() - window_seconds
        
        analysis = {
            'voice_commands': 0,
            'chat_messages': 0,
            'alerts': 0,
            'errors': 0,
            'avg_response_time': 0.0
        }
        
        # Count events in window
        for name, points in self.metrics.items():
            if 'voice' in name.lower() and 'command' in name.lower():
                recent = [p for p in points if p.timestamp >= cutoff]
                analysis['voice_commands'] += len(recent)
        
        # Get response times in window
        all_response_times = []
        for operation, times in self.response_times.items():
            # We'd need timestamps for each response time to filter by window
            # For simplicity, use all recent times
            if times:
                all_response_times.extend(times[-100:])
        
        if all_response_times:
            analysis['avg_response_time'] = statistics.mean(all_response_times)
        
        return analysis
    
    def _calculate_health_score(self) -> float:
        """Calculate overall system health score (0-100)"""
        scores = []
        
        # Response time score
        for operation, times in self.response_times.items():
            if times and 'ai' in operation.lower():
                avg_time = statistics.mean(times[-10:]) if len(times) >= 10 else times[-1]
                # Score based on response time (lower is better)
                if avg_time < 1.0:
                    scores.append(100)
                elif avg_time < 3.0:
                    scores.append(80)
                elif avg_time < 5.0:
                    scores.append(60)
                else:
                    scores.append(40)
        
        # Voice accuracy score
        if 'voice_recognition_accuracy' in self.metrics and self.metrics['voice_recognition_accuracy']:
            recent_acc = [p.value for p in self.metrics['voice_recognition_accuracy'][-10:]]
            if recent_acc:
                avg_acc = statistics.mean(recent_acc)
                scores.append(avg_acc * 100)  # Convert 0-1 to 0-100
        
        # System resource score
        system_metrics = ['system_cpu_usage', 'system_memory_usage']
        for metric in system_metrics:
            if metric in self.metrics and self.metrics[metric]:
                recent = [p.value for p in self.metrics[metric][-5:]]
                if recent:
                    avg_usage = statistics.mean(recent)
                    # Lower usage is better
                    usage_score = max(0, 100 - avg_usage)
                    scores.append(usage_score)
        
        return statistics.mean(scores) if scores else 100.0
    
    def _clean_old_data(self, metric_name: str):
        """Remove data older than retention period"""
        if metric_name not in self.metrics:
            return
        
        cutoff = time.time() - (self.retention_hours * 3600)
        metrics_list = list(self.metrics[metric_name])
        
        # Remove old points
        self.metrics[metric_name] = deque(
            [p for p in metrics_list if p.timestamp >= cutoff],
            maxlen=self.max_points
        )
    
    def get_realtime_metrics(self) -> Dict[str, Any]:
        """Get metrics for real-time display"""
        return {
            'health_score': self._calculate_health_score(),
            'voice_commands_per_minute': self._calculate_rate('voice_command', 60),
            'chat_messages_per_minute': self._calculate_rate('chat_message', 60),
            'active_alerts': self.counters.get('active_alerts', 0),
            'system_load': self._get_system_load(),
            'timestamp': time.time()
        }
    
    def _calculate_rate(self, event_type: str, window_seconds: int) -> float:
        """Calculate events per second for a given window"""
        # This is a simplified version
        # In production, you'd track timestamps for each event
        return self.counters.get(f'{event_type}_count', 0) / max(1, window_seconds)
    
    def _get_system_load(self) -> Dict[str, float]:
        """Get system load metrics"""
        try:
            import psutil
            return {
                'cpu_percent': psutil.cpu_percent(),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent
            }
        except ImportError:
            return {'cpu_percent': 0.0, 'memory_percent': 0.0, 'disk_percent': 0.0}
    
    def export_data(self, filepath: str, metrics: Optional[List[str]] = None):
        """Export analytics data to file"""
        import json
        
        export_data = {
            'counters': dict(self.counters),
            'gauges': dict(self.gauges),
            'report': self.get_performance_report(),
            'timestamp': datetime.now().isoformat()
        }
        
        if metrics:
            export_data['selected_metrics'] = {
                metric: [p.__dict__ for p in self.metrics[metric]]
                for metric in metrics if metric in self.metrics
            }
        
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)