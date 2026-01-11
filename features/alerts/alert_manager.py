"""
Alert Manager - Sistema centralizado de gerenciamento de alertas
Correlação, deduplicação, escalonamento e gerenciamento de alertas
"""

import logging
import json
import time
import threading
import hashlib
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict, deque
import uuid

logger = logging.getLogger(__name__)

class AlertLevel(Enum):
    """Níveis de severidade de alerta"""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AlertStatus(Enum):
    """Status do alerta"""
    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"
    EXPIRED = "expired"

class AlertSource(Enum):
    """Fontes de alerta"""
    SYSTEM_MONITOR = "system_monitor"
    NETWORK_MONITOR = "network_monitor"
    PERFORMANCE_MONITOR = "performance_monitor"
    TRADING_ENGINE = "trading_engine"
    RISK_MANAGER = "risk_manager"
    NOAA_SERVICE = "noaa_service"
    SECURITY_SCANNER = "security_scanner"
    USER = "user"
    EXTERNAL = "external"

@dataclass
class AlertRule:
    """Regra para processamento de alertas"""
    rule_id: str
    name: str
    description: str
    conditions: List[Dict[str, Any]]
    actions: List[Dict[str, Any]]
    enabled: bool = True
    priority: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def evaluate(self, alert_data: Dict[str, Any]) -> bool:
        """Avalia se a regra se aplica ao alerta"""
        if not self.enabled:
            return False
        
        for condition in self.conditions:
            if not self._evaluate_condition(condition, alert_data):
                return False
        
        return True
    
    def _evaluate_condition(self, condition: Dict[str, Any], alert_data: Dict[str, Any]) -> bool:
        """Avalia uma condição individual"""
        field = condition.get('field')
        operator = condition.get('operator')
        value = condition.get('value')
        
        if field not in alert_data:
            return False
        
        alert_value = alert_data[field]
        
        try:
            if operator == 'equals':
                return str(alert_value) == str(value)
            elif operator == 'not_equals':
                return str(alert_value) != str(value)
            elif operator == 'contains':
                return str(value) in str(alert_value)
            elif operator == 'greater_than':
                return float(alert_value) > float(value)
            elif operator == 'less_than':
                return float(alert_value) < float(value)
            elif operator == 'matches_regex':
                import re
                return bool(re.match(value, str(alert_value)))
            elif operator == 'in_list':
                return str(alert_value) in value
            else:
                logger.warning(f"Operador desconhecido: {operator}")
                return False
                
        except (ValueError, TypeError) as e:
            logger.debug(f"Erro ao avaliar condição: {e}")
            return False

@dataclass
class Alert:
    """Alerta do sistema"""
    alert_id: str
    source: AlertSource
    level: AlertLevel
    title: str
    description: str
    timestamp: datetime
    status: AlertStatus = AlertStatus.NEW
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    assigned_to: Optional[str] = None
    category: str = ""
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    related_alerts: List[str] = field(default_factory=list)
    expiry_time: Optional[datetime] = None
    notifications_sent: int = 0
    escalation_level: int = 0
    hash: Optional[str] = None
    
    def __post_init__(self):
        """Calcula hash do alerta para deduplicação"""
        if self.hash is None:
            self.hash = self.calculate_hash()
    
    def calculate_hash(self) -> str:
        """Calcula hash único para deduplicação"""
        hash_string = f"{self.source.value}:{self.level.value}:{self.title}:{self.description}"
        return hashlib.md5(hash_string.encode()).hexdigest()
    
    @property
    def is_active(self) -> bool:
        """Se o alerta está ativo (não resolvido ou suprimido)"""
        return self.status in [AlertStatus.NEW, AlertStatus.ACKNOWLEDGED]
    
    @property
    def age_seconds(self) -> float:
        """Idade do alerta em segundos"""
        return (datetime.now() - self.timestamp).total_seconds()
    
    @property
    def requires_attention(self) -> bool:
        """Se o alerta requer atenção imediata"""
        if self.status in [AlertStatus.RESOLVED, AlertStatus.SUPPRESSED, AlertStatus.EXPIRED]:
            return False
        
        # Alertas críticos sempre requerem atenção
        if self.level == AlertLevel.CRITICAL:
            return True
        
        # Alertas não reconhecidos
        if self.status == AlertStatus.NEW and self.age_seconds > 300:  # 5 minutos
            return True
        
        # Alertas com múltiplas notificações
        if self.notifications_sent >= 3 and self.status == AlertStatus.NEW:
            return True
        
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte alerta para dicionário"""
        return {
            'alert_id': self.alert_id,
            'source': self.source.value,
            'level': self.level.value,
            'title': self.title,
            'description': self.description,
            'timestamp': self.timestamp.isoformat(),
            'status': self.status.value,
            'category': self.category,
            'tags': self.tags,
            'is_active': self.is_active,
            'requires_attention': self.requires_attention,
            'age_seconds': self.age_seconds,
            'metadata': self.metadata,
            'escalation_level': self.escalation_level
        }
    
    def acknowledge(self, user: str = "system"):
        """Reconhece o alerta"""
        self.status = AlertStatus.ACKNOWLEDGED
        self.acknowledged_by = user
        self.acknowledged_at = datetime.now()
        logger.info(f"Alerta {self.alert_id} reconhecido por {user}")
    
    def resolve(self, user: str = "system"):
        """Resolve o alerta"""
        self.status = AlertStatus.RESOLVED
        self.resolved_by = user
        self.resolved_at = datetime.now()
        logger.info(f"Alerta {self.alert_id} resolvido por {user}")
    
    def suppress(self, reason: str = ""):
        """Suprime o alerta"""
        self.status = AlertStatus.SUPPRESSED
        self.metadata['suppression_reason'] = reason
        logger.info(f"Alerta {self.alert_id} suprimido: {reason}")
    
    def escalate(self):
        """Escalona o alerta"""
        self.escalation_level += 1
        logger.info(f"Alerta {self.alert_id} escalonado para nível {self.escalation_level}")

class AlertManager:
    """
    Gerenciador central de alertas
    Processa, correlaciona e gerencia alertas de múltiplas fontes
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Inicializa o gerenciador de alertas
        
        Args:
            config: Configuração do alert manager
        """
        self.config = config or {}
        
        # Armazenamento de alertas
        self.alerts: Dict[str, Alert] = {}
        self.alert_history: deque = deque(maxlen=self.config.get('history_size', 1000))
        
        # Regras de alerta
        self.rules: Dict[str, AlertRule] = {}
        self._load_default_rules()
        
        # Deduplicação
        self.alert_hashes: Set[str] = set()
        self.duplicate_window = self.config.get('duplicate_window', 300)  # 5 minutos
        
        # Correlação
        self.correlation_window = self.config.get('correlation_window', 60)  # 1 minuto
        self.correlation_rules: List[Dict[str, Any]] = []
        
        # Escalonamento
        self.escalation_policies: Dict[str, List[Dict[str, Any]]] = {}
        
        # Estado
        self.is_processing = False
        self.processing_thread: Optional[threading.Thread] = None
        self.process_interval = self.config.get('process_interval', 5.0)
        
        # Callbacks
        self.notification_callbacks = []
        self.escalation_callbacks = []
        self.alert_handlers: Dict[AlertSource, List[callable]] = defaultdict(list)
        
        # Estatísticas
        self.stats = {
            'alerts_received': 0,
            'alerts_processed': 0,
            'alerts_correlated': 0,
            'alerts_escalated': 0,
            'duplicates_filtered': 0,
            'last_processed': None
        }
        
        logger.info("Alert Manager inicializado")
    
    def start_processing(self):
        """Inicia processamento de alertas"""
        if self.is_processing:
            logger.warning("Alert Manager já está processando")
            return
        
        self.is_processing = True
        self.processing_thread = threading.Thread(target=self._processing_loop, daemon=True)
        self.processing_thread.start()
        
        logger.info("Alert Manager iniciado")
    
    def stop_processing(self):
        """Para processamento de alertas"""
        self.is_processing = False
        if self.processing_thread:
            self.processing_thread.join(timeout=5)
        
        logger.info("Alert Manager parado")
    
    def _processing_loop(self):
        """Loop de processamento de alertas"""
        import time
        
        while self.is_processing:
            try:
                start_time = time.time()
                
                # Processar alertas pendentes
                self._process_pending_alerts()
                
                # Executar manutenção
                self._maintenance()
                
                # Calcular tempo de processamento
                processing_time = time.time() - start_time
                
                # Aguardar próximo ciclo
                sleep_time = max(0, self.process_interval - processing_time)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    
            except Exception as e:
                logger.error(f"Erro no loop de processamento: {e}")
                time.sleep(10)
    
    def receive_alert(self, source: AlertSource, level: AlertLevel,
                     title: str, description: str,
                     metadata: Optional[Dict[str, Any]] = None,
                     category: str = "", tags: List[str] = None) -> Optional[str]:
        """
        Recebe um novo alerta
        
        Args:
            source: Fonte do alerta
            level: Nível de severidade
            title: Título do alerta
            description: Descrição do alerta
            metadata: Metadados adicionais
            category: Categoria do alerta
            tags: Tags do alerta
            
        Returns:
            ID do alerta criado ou None se filtrado
        """
        self.stats['alerts_received'] += 1
        
        # Criar alerta
        alert_id = f"ALERT-{int(time.time())}-{uuid.uuid4().hex[:8]}"
        
        alert = Alert(
            alert_id=alert_id,
            source=source,
            level=level,
            title=title,
            description=description,
            timestamp=datetime.now(),
            category=category,
            tags=tags or [],
            metadata=metadata or {}
        )
        
        # Verificar duplicação
        if self._is_duplicate(alert):
            self.stats['duplicates_filtered'] += 1
            logger.debug(f"Alerta duplicado filtrado: {alert.hash}")
            return None
        
        # Aplicar regras
        self._apply_rules(alert)
        
        # Adicionar ao armazenamento
        self.alerts[alert_id] = alert
        self.alert_hashes.add(alert.hash)
        
        # Adicionar ao histórico
        self.alert_history.append(alert.to_dict())
        
        # Executar handlers específicos da fonte
        if source in self.alert_handlers:
            for handler in self.alert_handlers[source]:
                try:
                    handler(alert)
                except Exception as e:
                    logger.error(f"Erro no handler de alerta: {e}")
        
        logger.info(f"Alerta recebido: {alert_id} - {title} ({level.value})")
        return alert_id
    
    def _is_duplicate(self, alert: Alert) -> bool:
        """Verifica se o alerta é duplicado"""
        # Verificar hash no window time
        if alert.hash in self.alert_hashes:
            # Verificar se existe alerta similar recente
            cutoff_time = datetime.now() - timedelta(seconds=self.duplicate_window)
            
            for existing_alert in self.alerts.values():
                if (existing_alert.hash == alert.hash and 
                    existing_alert.timestamp >= cutoff_time and
                    existing_alert.is_active):
                    
                    # Incrementar contador de duplicação
                    if 'duplicate_count' not in existing_alert.metadata:
                        existing_alert.metadata['duplicate_count'] = 1
                    existing_alert.metadata['duplicate_count'] += 1
                    existing_alert.metadata['last_duplicate'] = datetime.now().isoformat()
                    
                    return True
        
        return False
    
    def _apply_rules(self, alert: Alert):
        """Aplica regras ao alerta"""
        alert_data = alert.to_dict()
        alert_data.update(alert.metadata)
        
        for rule in self.rules.values():
            if rule.evaluate(alert_data):
                logger.debug(f"Regra aplicada: {rule.name} ao alerta {alert.alert_id}")
                
                # Executar ações
                for action in rule.actions:
                    self._execute_action(action, alert)
    
    def _execute_action(self, action: Dict[str, Any], alert: Alert):
        """Executa uma ação de regra"""
        action_type = action.get('type')
        
        if action_type == 'set_category':
            alert.category = action.get('value', alert.category)
        
        elif action_type == 'add_tag':
            if 'value' in action:
                if isinstance(action['value'], list):
                    alert.tags.extend(action['value'])
                else:
                    alert.tags.append(str(action['value']))
        
        elif action_type == 'set_metadata':
            key = action.get('key')
            value = action.get('value')
            if key:
                alert.metadata[key] = value
        
        elif action_type == 'escalate':
            alert.escalate()
            self.stats['alerts_escalated'] += 1
        
        elif action_type == 'suppress':
            reason = action.get('reason', 'Suppressed by rule')
            alert.suppress(reason)
        
        elif action_type == 'notify':
            # Disparar notificação
            self._trigger_notification(alert, action.get('channel', 'all'))
        
        elif action_type == 'execute_handler':
            handler_name = action.get('handler')
            if handler_name:
                self._execute_custom_handler(handler_name, alert)
    
    def _execute_custom_handler(self, handler_name: str, alert: Alert):
        """Executa handler customizado"""
        # Em implementação real, chamaria handlers registrados
        logger.debug(f"Executando handler customizado: {handler_name} para alerta {alert.alert_id}")
    
    def _process_pending_alerts(self):
        """Processa alertas pendentes"""
        # Correlação de alertas
        self._correlate_alerts()
        
        # Escalonamento
        self._check_escalation()
        
        # Expiração
        self._check_expiry()
        
        self.stats['last_processed'] = datetime.now()
    
    def _correlate_alerts(self):
        """Correlaciona alertas relacionados"""
        cutoff_time = datetime.now() - timedelta(seconds=self.correlation_window)
        
        # Agrupar alertas por fonte e categoria
        recent_alerts = [
            a for a in self.alerts.values()
            if a.timestamp >= cutoff_time and a.is_active
        ]
        
        # Agrupar por hash para correlacionar duplicatas
        alerts_by_hash = defaultdict(list)
        for alert in recent_alerts:
            alerts_by_hash[alert.hash].append(alert)
        
        # Correlacionar grupos com múltiplos alertas
        for alert_hash, alert_group in alerts_by_hash.items():
            if len(alert_group) > 1:
                # Encontrar alerta principal (o mais antigo)
                primary_alert = min(alert_group, key=lambda a: a.timestamp)
                
                # Adicionar relacionamentos
                for alert in alert_group:
                    if alert.alert_id != primary_alert.alert_id:
                        if primary_alert.alert_id not in alert.related_alerts:
                            alert.related_alerts.append(primary_alert.alert_id)
                        
                        # Incrementar contador de correlação
                        if 'correlation_count' not in primary_alert.metadata:
                            primary_alert.metadata['correlation_count'] = 0
                        primary_alert.metadata['correlation_count'] += 1
                        
                        # Se muitos alertas correlacionados, escalonar
                        if primary_alert.metadata['correlation_count'] >= 3:
                            primary_alert.escalate()
                            self.stats['alerts_correlated'] += 1
        
        self.stats['alerts_processed'] = len(recent_alerts)
    
    def _check_escalation(self):
        """Verifica necessidade de escalonamento"""
        for alert in list(self.alerts.values()):
            if not alert.is_active:
                continue
            
            # Verificar tempo desde criação
            if alert.age_seconds > 300 and alert.status == AlertStatus.NEW:  # 5 minutos
                alert.escalate()
            
            # Verificar nível de severidade
            if alert.level == AlertLevel.CRITICAL and alert.escalation_level < 2:
                alert.escalate()
            
            # Executar política de escalonamento se definida
            if alert.category in self.escalation_policies:
                self._apply_escalation_policy(alert)
    
    def _apply_escalation_policy(self, alert: Alert):
        """Aplica política de escalonamento"""
        policy = self.escalation_policies.get(alert.category, [])
        
        for level in policy:
            if alert.escalation_level == level.get('level', 0):
                actions = level.get('actions', [])
                for action in actions:
                    self._execute_action(action, alert)
    
    def _check_expiry(self):
        """Verifica alertas expirados"""
        current_time = datetime.now()
        
        for alert in list(self.alerts.values()):
            if alert.expiry_time and current_time > alert.expiry_time:
                alert.status = AlertStatus.EXPIRED
                logger.info(f"Alerta {alert.alert_id} expirado")
    
    def _maintenance(self):
        """Executa tarefas de manutenção"""
        # Limpar hashes antigos
        cutoff_time = datetime.now() - timedelta(seconds=self.duplicate_window * 2)
        
        hashes_to_remove = set()
        for alert_hash in self.alert_hashes:
            # Verificar se há alertas recentes com este hash
            recent_alert = False
            for alert in self.alerts.values():
                if alert.hash == alert_hash and alert.timestamp >= cutoff_time:
                    recent_alert = True
                    break
            
            if not recent_alert:
                hashes_to_remove.add(alert_hash)
        
        for alert_hash in hashes_to_remove:
            self.alert_hashes.remove(alert_hash)
        
        # Limpar alertas resolvidos/expirados antigos
        alert_ids_to_remove = []
        cutoff_time = datetime.now() - timedelta(days=7)  # Manter por 7 dias
        
        for alert_id, alert in self.alerts.items():
            if (alert.status in [AlertStatus.RESOLVED, AlertStatus.EXPIRED, AlertStatus.SUPPRESSED] and
                alert.timestamp < cutoff_time):
                alert_ids_to_remove.append(alert_id)
        
        for alert_id in alert_ids_to_remove:
            del self.alerts[alert_id]
        
        if alert_ids_to_remove:
            logger.debug(f"Removidos {len(alert_ids_to_remove)} alertas antigos")
    
    def _load_default_rules(self):
        """Carrega regras padrão"""
        default_rules = [
            AlertRule(
                rule_id="RULE-001",
                name="Alertas Críticos - Notificação Imediata",
                description="Notificação imediata para alertas críticos",
                conditions=[
                    {"field": "level", "operator": "equals", "value": "critical"}
                ],
                actions=[
                    {"type": "notify", "channel": "all"},
                    {"type": "escalate"}
                ],
                priority=100
            ),
            AlertRule(
                rule_id="RULE-002",
                name="Alertas de Sistema - Categorização",
                description="Categoriza alertas do system monitor",
                conditions=[
                    {"field": "source", "operator": "equals", "value": "system_monitor"}
                ],
                actions=[
                    {"type": "set_category", "value": "system"},
                    {"type": "add_tag", "value": ["hardware", "performance"]}
                ],
                priority=50
            ),
            AlertRule(
                rule_id="RULE-003",
                name="Alertas de Rede - Categorização",
                description="Categoriza alertas do network monitor",
                conditions=[
                    {"field": "source", "operator": "equals", "value": "network_monitor"}
                ],
                actions=[
                    {"type": "set_category", "value": "network"},
                    {"type": "add_tag", "value": ["connectivity", "security"]}
                ],
                priority=50
            ),
            AlertRule(
                rule_id="RULE-004",
                name="Alertas Duplicados - Supressão",
                description="Suprime alertas duplicados recentes",
                conditions=[
                    {"field": "metadata.duplicate_count", "operator": "greater_than", "value": "3"}
                ],
                actions=[
                    {"type": "suppress", "reason": "Múltiplas ocorrências em curto período"}
                ],
                priority=30
            )
        ]
        
        for rule in default_rules:
            self.rules[rule.rule_id] = rule
        
        logger.info(f"Carregadas {len(default_rules)} regras padrão")
    
    def register_alert_handler(self, source: AlertSource, handler: callable):
        """Registra handler para alertas de uma fonte específica"""
        self.alert_handlers[source].append(handler)
        logger.debug(f"Handler registrado para fonte {source.value}: {handler.__name__}")
    
    def register_notification_callback(self, callback: callable):
        """Registra callback para notificações"""
        self.notification_callbacks.append(callback)
        logger.debug(f"Callback de notificação registrado: {callback.__name__}")
    
    def register_escalation_callback(self, callback: callable):
        """Registra callback para escalonamento"""
        self.escalation_callbacks.append(callback)
        logger.debug(f"Callback de escalonamento registrado: {callback.__name__}")
    
    def _trigger_notification(self, alert: Alert, channel: str = "all"):
        """Dispara notificação"""
        alert.notifications_sent += 1
        
        for callback in self.notification_callbacks:
            try:
                callback(alert, channel)
            except Exception as e:
                logger.error(f"Erro no callback de notificação: {e}")
    
    def get_alert(self, alert_id: str) -> Optional[Alert]:
        """Obtém um alerta pelo ID"""
        return self.alerts.get(alert_id)
    
    def get_alerts(self, filters: Optional[Dict[str, Any]] = None) -> List[Alert]:
        """
        Obtém alertas com filtros
        
        Args:
            filters: Filtros para aplicar
            
        Returns:
            Lista de alertas filtrados
        """
        alerts = list(self.alerts.values())
        
        if not filters:
            return alerts
        
        filtered_alerts = []
        
        for alert in alerts:
            include = True
            
            for key, value in filters.items():
                if key == 'status':
                    if alert.status.value != value:
                        include = False
                        break
                elif key == 'level':
                    if alert.level.value != value:
                        include = False
                        break
                elif key == 'source':
                    if alert.source.value != value:
                        include = False
                        break
                elif key == 'category':
                    if alert.category != value:
                        include = False
                        break
                elif key == 'tag':
                    if value not in alert.tags:
                        include = False
                        break
                elif key == 'active':
                    if alert.is_active != value:
                        include = False
                        break
                elif key == 'requires_attention':
                    if alert.requires_attention != value:
                        include = False
                        break
                elif key == 'min_age_seconds':
                    if alert.age_seconds < value:
                        include = False
                        break
                elif key == 'max_age_seconds':
                    if alert.age_seconds > value:
                        include = False
                        break
            
            if include:
                filtered_alerts.append(alert)
        
        return filtered_alerts
    
    def get_active_alerts(self) -> List[Alert]:
        """Obtém alertas ativos"""
        return [a for a in self.alerts.values() if a.is_active]
    
    def get_alerts_requiring_attention(self) -> List[Alert]:
        """Obtém alertas que requerem atenção"""
        return [a for a in self.alerts.values() if a.requires_attention]
    
    def acknowledge_alert(self, alert_id: str, user: str = "user"):
        """Reconhece um alerta"""
        alert = self.get_alert(alert_id)
        if alert and alert.is_active:
            alert.acknowledge(user)
            return True
        return False
    
    def resolve_alert(self, alert_id: str, user: str = "user"):
        """Resolve um alerta"""
        alert = self.get_alert(alert_id)
        if alert and alert.is_active:
            alert.resolve(user)
            return True
        return False
    
    def suppress_alert(self, alert_id: str, reason: str = ""):
        """Suprime um alerta"""
        alert = self.get_alert(alert_id)
        if alert and alert.is_active:
            alert.suppress(reason)
            return True
        return False
    
    def add_rule(self, rule: AlertRule):
        """Adiciona uma nova regra"""
        self.rules[rule.rule_id] = rule
        logger.info(f"Regra adicionada: {rule.name}")
    
    def remove_rule(self, rule_id: str):
        """Remove uma regra"""
        if rule_id in self.rules:
            del self.rules[rule_id]
            logger.info(f"Regra removida: {rule_id}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Obtém estatísticas do alert manager"""
        active_alerts = self.get_active_alerts()
        attention_alerts = self.get_alerts_requiring_attention()
        
        # Contagem por nível
        levels_count = defaultdict(int)
        sources_count = defaultdict(int)
        categories_count = defaultdict(int)
        
        for alert in self.alerts.values():
            levels_count[alert.level.value] += 1
            sources_count[alert.source.value] += 1
            if alert.category:
                categories_count[alert.category] += 1
        
        return {
            **self.stats,
            'total_alerts': len(self.alerts),
            'active_alerts': len(active_alerts),
            'attention_required': len(attention_alerts),
            'rules_count': len(self.rules),
            'levels_count': dict(levels_count),
            'sources_count': dict(sources_count),
            'categories_count': dict(categories_count),
            'is_processing': self.is_processing,
            'duplicate_window': self.duplicate_window,
            'correlation_window': self.correlation_window
        }
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """Obtém resumo dos alertas"""
        active_alerts = self.get_active_alerts()
        attention_alerts = self.get_alerts_requiring_attention()
        
        # Agrupar por nível
        critical_alerts = [a for a in active_alerts if a.level == AlertLevel.CRITICAL]
        high_alerts = [a for a in active_alerts if a.level == AlertLevel.HIGH]
        medium_alerts = [a for a in active_alerts if a.level == AlertLevel.MEDIUM]
        
        # Alertas recentes (última hora)
        cutoff_time = datetime.now() - timedelta(hours=1)
        recent_alerts = [
            a for a in self.alerts.values()
            if a.timestamp >= cutoff_time
        ]
        
        return {
            'timestamp': datetime.now().isoformat(),
            'total_active': len(active_alerts),
            'requires_attention': len(attention_alerts),
            'critical': len(critical_alerts),
            'high': len(high_alerts),
            'medium': len(medium_alerts),
            'recent_hour': len(recent_alerts),
            'top_categories': sorted(
                [(cat, count) for cat, count in 
                 {a.category: len([a2 for a2 in active_alerts if a2.category == a.category]) 
                  for a in active_alerts}.items() if cat],
                key=lambda x: x[1],
                reverse=True
            )[:5],
            'oldest_active': min([a.timestamp for a in active_alerts]).isoformat() if active_alerts else None
        }