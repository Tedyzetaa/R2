"""
Alert system for monitoring and notifying about important events
"""

import threading
import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import requests

class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

class AlertSource(Enum):
    SYSTEM = "system"
    NOAA = "noaa"
    WEATHER = "weather"
    TRADING = "trading"
    NETWORK = "network"
    SECURITY = "security"
    CUSTOM = "custom"

@dataclass
class Alert:
    """Alert definition"""
    id: str
    level: AlertLevel
    title: str
    message: str
    source: AlertSource
    timestamp: float
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def age_seconds(self) -> float:
        """Get alert age in seconds"""
        return time.time() - self.timestamp
    
    @property
    def is_active(self) -> bool:
        """Check if alert is still active"""
        if self.level == AlertLevel.CRITICAL:
            return self.age_seconds < 3600  # 1 hour for critical alerts
        elif self.level == AlertLevel.WARNING:
            return self.age_seconds < 7200  # 2 hours for warnings
        else:
            return self.age_seconds < 14400  # 4 hours for info alerts
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'level': self.level.value,
            'title': self.title,
            'message': self.message,
            'source': self.source.value,
            'timestamp': self.timestamp,
            'datetime': datetime.fromtimestamp(self.timestamp).isoformat(),
            'acknowledged': self.acknowledged,
            'acknowledged_by': self.acknowledged_by,
            'acknowledged_at': self.acknowledged_at,
            'metadata': self.metadata,
            'age_seconds': self.age_seconds,
            'is_active': self.is_active
        }

class AlertSystem:
    """
    Alert monitoring and notification system
    """
    
    def __init__(self, config, notification_callback: Optional[Callable] = None):
        self.config = config
        self.notification_callback = notification_callback
        
        # Alert storage
        self.alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.max_alerts = 1000
        
        # Monitoring threads
        self.monitoring_threads: Dict[str, threading.Thread] = {}
        self.is_monitoring = False
        
        # Statistics
        self.stats = {
            'total_alerts': 0,
            'active_alerts': 0,
            'acknowledged_alerts': 0,
            'alerts_by_level': {},
            'alerts_by_source': {},
            'last_alert_time': 0
        }
        
        # Alert templates
        self.templates = self._load_templates()
        
        # Start monitoring
        self.start_monitoring()
    
    def _load_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load alert templates"""
        return {
            'system_high_cpu': {
                'title': 'CPU Usage High',
                'message': 'CPU usage is above {threshold}%',
                'level': AlertLevel.WARNING,
                'source': AlertSource.SYSTEM
            },
            'system_high_memory': {
                'title': 'Memory Usage High',
                'message': 'Memory usage is above {threshold}%',
                'level': AlertLevel.WARNING,
                'source': AlertSource.SYSTEM
            },
            'system_disk_space': {
                'title': 'Low Disk Space',
                'message': 'Disk space is below {threshold}%',
                'level': AlertLevel.WARNING,
                'source': AlertSource.SYSTEM
            },
            'noaa_solar_flare': {
                'title': 'Solar Flare Detected',
                'message': 'Solar flare activity detected: {details}',
                'level': AlertLevel.CRITICAL,
                'source': AlertSource.NOAA
            },
            'noaa_geomagnetic_storm': {
                'title': 'Geomagnetic Storm',
                'message': 'Geomagnetic storm detected: {details}',
                'level': AlertLevel.WARNING,
                'source': AlertSource.NOAA
            },
            'weather_severe': {
                'title': 'Severe Weather Alert',
                'message': 'Severe weather warning: {details}',
                'level': AlertLevel.WARNING,
                'source': AlertSource.WEATHER
            },
            'trading_price_alert': {
                'title': 'Price Alert',
                'message': '{symbol} price {direction} {threshold}',
                'level': AlertLevel.INFO,
                'source': AlertSource.TRADING
            },
            'network_down': {
                'title': 'Network Connection Lost',
                'message': 'Network connection interrupted',
                'level': AlertLevel.CRITICAL,
                'source': AlertSource.NETWORK
            }
        }
    
    def start_monitoring(self):
        """Start all monitoring threads"""
        if self.is_monitoring:
            print("⚠️ Alert system already monitoring")
            return
        
        self.is_monitoring = True
        
        # Start system monitoring
        self._start_monitoring_thread('system', self._monitor_system, 60)
        
        # Start NOAA monitoring if API key available
        if self.config.WEATHER_API_KEY:
            self._start_monitoring_thread('noaa', self._monitor_noaa, 300)  # 5 minutes
        
        # Start network monitoring
        self._start_monitoring_thread('network', self._monitor_network, 30)
        
        print("🔍 Alert system monitoring started")
    
    def stop_monitoring(self):
        """Stop all monitoring threads"""
        self.is_monitoring = False
        
        for thread_name, thread in self.monitoring_threads.items():
            if thread.is_alive():
                thread.join(timeout=2.0)
        
        print("🛑 Alert system monitoring stopped")
    
    def _start_monitoring_thread(self, name: str, target: Callable, interval: int):
        """Start a monitoring thread"""
        def monitoring_loop():
            while self.is_monitoring:
                try:
                    target()
                except Exception as e:
                    print(f"❌ Error in {name} monitoring: {e}")
                
                time.sleep(interval)
        
        thread = threading.Thread(target=monitoring_loop, daemon=True)
        thread.name = f"AlertMonitor-{name}"
        self.monitoring_threads[name] = thread
        thread.start()
    
    def create_alert(self, template_name: str, **kwargs) -> Optional[str]:
        """
        Create an alert from template
        
        Returns:
            Alert ID if created, None otherwise
        """
        if template_name not in self.templates:
            print(f"❌ Alert template '{template_name}' not found")
            return None
        
        template = self.templates[template_name]
        
        # Format message with kwargs
        try:
            message = template['message'].format(**kwargs)
        except KeyError as e:
            print(f"❌ Missing parameter for alert template: {e}")
            return None
        
        alert_id = f"alert_{int(time.time())}_{len(self.alerts)}"
        
        alert = Alert(
            id=alert_id,
            level=template['level'],
            title=template['title'],
            message=message,
            source=template['source'],
            timestamp=time.time(),
            metadata=kwargs
        )
        
        # Store alert
        self.alerts[alert_id] = alert
        self.alert_history.append(alert)
        
        # Update statistics
        self._update_statistics(alert)
        
        # Trim history
        if len(self.alert_history) > self.max_alerts:
            self.alert_history = self.alert_history[-self.max_alerts:]
        
        # Notify via callback
        if self.notification_callback:
            self.notification_callback(alert.to_dict())
        
        print(f"🚨 Alert created: {alert.title} ({alert.level.value})")
        
        return alert_id
    
    def create_custom_alert(self, level: AlertLevel, title: str, message: str,
                          source: AlertSource, **metadata) -> str:
        """Create a custom alert"""
        alert_id = f"alert_{int(time.time())}_{len(self.alerts)}"
        
        alert = Alert(
            id=alert_id,
            level=level,
            title=title,
            message=message,
            source=source,
            timestamp=time.time(),
            metadata=metadata
        )
        
        # Store alert
        self.alerts[alert_id] = alert
        self.alert_history.append(alert)
        
        # Update statistics
        self._update_statistics(alert)
        
        # Notify via callback
        if self.notification_callback:
            self.notification_callback(alert.to_dict())
        
        print(f"🚨 Custom alert created: {title} ({level.value})")
        
        return alert_id
    
    def acknowledge_alert(self, alert_id: str, acknowledged_by: str = "system"):
        """Acknowledge an alert"""
        if alert_id not in self.alerts:
            print(f"⚠️ Alert '{alert_id}' not found")
            return False
        
        alert = self.alerts[alert_id]
        
        if not alert.acknowledged:
            alert.acknowledged = True
            alert.acknowledged_by = acknowledged_by
            alert.acknowledged_at = time.time()
            
            # Update statistics
            self.stats['acknowledged_alerts'] += 1
            self.stats['active_alerts'] = max(0, self.stats['active_alerts'] - 1)
            
            print(f"✅ Alert acknowledged: {alert.title}")
            return True
        
        return False
    
    def dismiss_alert(self, alert_id: str):
        """Dismiss an alert (remove from active alerts)"""
        if alert_id in self.alerts:
            del self.alerts[alert_id]
            
            # Update statistics
            self.stats['active_alerts'] = max(0, self.stats['active_alerts'] - 1)
            
            print(f"🗑️ Alert dismissed: {alert_id}")
            return True
        
        return False
    
    def get_active_alerts(self, level: Optional[AlertLevel] = None,
                         source: Optional[AlertSource] = None) -> List[Alert]:
        """Get active alerts with optional filtering"""
        active_alerts = []
        
        for alert in self.alerts.values():
            if not alert.is_active:
                continue
            
            if level and alert.level != level:
                continue
            
            if source and alert.source != source:
                continue
            
            active_alerts.append(alert)
        
        # Sort by timestamp (newest first)
        active_alerts.sort(key=lambda a: a.timestamp, reverse=True)
        
        return active_alerts
    
    def get_recent_alerts(self, limit: int = 50, 
                         include_acknowledged: bool = True) -> List[Dict[str, Any]]:
        """Get recent alerts"""
        recent_alerts = []
        
        for alert in reversed(self.alert_history[-limit:]):
            if not include_acknowledged and alert.acknowledged:
                continue
            
            recent_alerts.append(alert.to_dict())
        
        return recent_alerts
    
    def _update_statistics(self, alert: Alert):
        """Update alert statistics"""
        self.stats['total_alerts'] += 1
        self.stats['last_alert_time'] = alert.timestamp
        
        # Update by level
        level_key = alert.level.value
        if level_key not in self.stats['alerts_by_level']:
            self.stats['alerts_by_level'][level_key] = 0
        self.stats['alerts_by_level'][level_key] += 1
        
        # Update by source
        source_key = alert.source.value
        if source_key not in self.stats['alerts_by_source']:
            self.stats['alerts_by_source'][source_key] = 0
        self.stats['alerts_by_source'][source_key] += 1
        
        # Update active alerts count
        if alert.is_active and not alert.acknowledged:
            self.stats['active_alerts'] += 1
    
    # Monitoring functions
    
    def _monitor_system(self):
        """Monitor system resources"""
        try:
            import psutil
            
            # Check CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > 80:
                self.create_alert('system_high_cpu', threshold=80, current=cpu_percent)
            
            # Check memory usage
            memory = psutil.virtual_memory()
            if memory.percent > 85:
                self.create_alert('system_high_memory', threshold=85, current=memory.percent)
            
            # Check disk space
            disk = psutil.disk_usage('/')
            if disk.percent > 90:
                self.create_alert('system_disk_space', threshold=10, current=100-disk.percent)
            
        except ImportError:
            print("⚠️ psutil not installed, system monitoring disabled")
        except Exception as e:
            print(f"❌ System monitoring error: {e}")
    
    def _monitor_noaa(self):
        """Monitor NOAA space weather"""
        try:
            # NOAA Space Weather Alerts
            response = requests.get(
                "https://services.swpc.noaa.gov/products/alerts.json",
                timeout=10
            )
            
            if response.status_code == 200:
                alerts = response.json()
                
                for alert in alerts[-5:]:  # Check last 5 alerts
                    alert_text = str(alert).lower()
                    
                    # Check for solar flares
                    if 'x-ray' in alert_text and 'flare' in alert_text:
                        self.create_alert(
                            'noaa_solar_flare',
                            details=alert_text[:100]  # Truncate if too long
                        )
                    
                    # Check for geomagnetic storms
                    if 'geomagnetic' in alert_text and 'storm' in alert_text:
                        self.create_alert(
                            'noaa_geomagnetic_storm',
                            details=alert_text[:100]
                        )
            
        except Exception as e:
            print(f"❌ NOAA monitoring error: {e}")
    
    def _monitor_network(self):
        """Monitor network connectivity"""
        try:
            # Simple network check
            response = requests.get("https://www.google.com", timeout=5)
            
            if response.status_code != 200:
                self.create_custom_alert(
                    level=AlertLevel.WARNING,
                    title="Network Issues",
                    message=f"Network request failed with status {response.status_code}",
                    source=AlertSource.NETWORK
                )
            
        except requests.exceptions.ConnectionError:
            self.create_alert('network_down')
        except Exception as e:
            print(f"❌ Network monitoring error: {e}")
    
    def add_template(self, name: str, template: Dict[str, Any]):
        """Add a new alert template"""
        self.templates[name] = template
        print(f"📝 Added alert template: {name}")
    
    def remove_template(self, name: str):
        """Remove an alert template"""
        if name in self.templates:
            del self.templates[name]
            print(f"🗑️ Removed alert template: {name}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get alert system statistics"""
        return {
            **self.stats,
            'is_monitoring': self.is_monitoring,
            'monitoring_threads': list(self.monitoring_threads.keys()),
            'templates_count': len(self.templates),
            'current_time': time.time()
        }
    
    def export_alerts(self, filepath: str, 
                     include_history: bool = True,
                     max_history: int = 1000):
        """Export alerts to file"""
        import json
        
        export_data = {
            'active_alerts': [a.to_dict() for a in self.alerts.values()],
            'statistics': self.get_statistics(),
            'templates': self.templates,
            'timestamp': time.time()
        }
        
        if include_history:
            history_limit = min(max_history, len(self.alert_history))
            export_data['history'] = [
                a.to_dict() for a in self.alert_history[-history_limit:]
            ]
        
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)
    
    def import_alerts(self, filepath: str):
        """Import alerts from file"""
        try:
            with open(filepath, 'r') as f:
                import_data = json.load(f)
            
            # Note: This would need to recreate alerts
            # Implementation depends on serialization format
            print(f"📥 Imported alerts from {filepath}")
            
        except Exception as e:
            print(f"❌ Error importing alerts: {e}")