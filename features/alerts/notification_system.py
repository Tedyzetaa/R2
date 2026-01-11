"""
Sistema de Notificações Multi-canal
Envia notificações através de múltiplos canais com fallback e priorização
"""

import asyncio
import smtplib
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
import time
import json
import threading
from queue import Queue, PriorityQueue

logger = logging.getLogger(__name__)

class NotificationChannel(Enum):
    """Canais de notificação suportados"""
    IN_APP = "in_app"          # Notificações na aplicação (HUD)
    DESKTOP = "desktop"        # Notificações do sistema operacional
    EMAIL = "email"            # E-mail
    WEBHOOK = "webhook"        # Webhook HTTP
    TELEGRAM = "telegram"      # Telegram Bot
    DISCORD = "discord"        # Discord Webhook
    SLACK = "slack"           # Slack Webhook
    SMS = "sms"               # SMS (via Twilio/plataforma)
    VOICE = "voice"           # Notificação por voz
    LOG = "log"               # Apenas log

class NotificationPriority(Enum):
    """Prioridades para entrega de notificações"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    URGENT = 3

@dataclass
class Notification:
    """Estrutura de dados para notificação"""
    id: str
    title: str
    message: str
    channel: NotificationChannel
    priority: NotificationPriority
    timestamp: float
    data: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    retry_count: int = 0
    max_retries: int = 3
    expires_at: Optional[float] = None
    
    @property
    def is_expired(self) -> bool:
        """Verifica se a notificação expirou"""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at

class NotificationHandler(ABC):
    """Interface base para handlers de notificação"""
    
    @abstractmethod
    async def send(self, notification: Notification) -> bool:
        """Envia uma notificação"""
        pass
    
    @abstractmethod
    def can_send(self, notification: Notification) -> bool:
        """Verifica se pode enviar a notificação"""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Retorna nome do handler"""
        pass

class InAppNotificationHandler(NotificationHandler):
    """Handler para notificações in-app"""
    
    def __init__(self, gui_callback: Optional[Callable] = None):
        self.gui_callback = gui_callback
        self.sent_notifications = []
        
    async def send(self, notification: Notification) -> bool:
        try:
            # Se tiver callback GUI, usar
            if self.gui_callback:
                self.gui_callback(notification)
            
            # Armazenar para histórico
            self.sent_notifications.append({
                'id': notification.id,
                'title': notification.title,
                'time': notification.timestamp
            })
            
            logger.info(f"Notificação in-app enviada: {notification.title}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao enviar notificação in-app: {e}")
            return False
    
    def can_send(self, notification: Notification) -> bool:
        return notification.channel == NotificationChannel.IN_APP
    
    def get_name(self) -> str:
        return "In-App Notification Handler"

class EmailNotificationHandler(NotificationHandler):
    """Handler para notificações por email"""
    
    def __init__(
        self,
        smtp_server: str,
        smtp_port: int,
        username: str,
        password: str,
        from_email: str
    ):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_email = from_email
        self.smtp_connection = None
        
    async def send(self, notification: Notification) -> bool:
        try:
            # Criar mensagem
            msg = MIMEMultipart('alternative')
            msg['Subject'] = notification.title
            msg['From'] = self.from_email
            msg['To'] = notification.data.get('to_email', '')
            
            # Criar conteúdo
            html_content = f"""
            <html>
              <body>
                <h2>{notification.title}</h2>
                <p>{notification.message}</p>
                <hr>
                <p><small>R2 Assistant - {time.strftime('%Y-%m-%d %H:%M:%S')}</small></p>
              </body>
            </html>
            """
            
            msg.attach(MIMEText(notification.message, 'plain'))
            msg.attach(MIMEText(html_content, 'html'))
            
            # Enviar
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                server.login(self.username, self.password)
                server.send_message(msg)
            
            logger.info(f"Email enviado para: {notification.data.get('to_email')}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao enviar email: {e}")
            return False
    
    def can_send(self, notification: Notification) -> bool:
        return (notification.channel == NotificationChannel.EMAIL and 
                'to_email' in notification.data)
    
    def get_name(self) -> str:
        return "Email Notification Handler"

class WebhookNotificationHandler(NotificationHandler):
    """Handler para notificações via webhook"""
    
    def __init__(self, timeout: int = 10):
        import aiohttp
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout))
        
    async def send(self, notification: Notification) -> bool:
        try:
            webhook_url = notification.data.get('webhook_url')
            if not webhook_url:
                return False
            
            payload = {
                'title': notification.title,
                'message': notification.message,
                'timestamp': notification.timestamp,
                'priority': notification.priority.value,
                **notification.data.get('payload', {})
            }
            
            headers = notification.data.get('headers', {})
            
            async with self.session.post(
                webhook_url,
                json=payload,
                headers=headers
            ) as response:
                success = response.status in (200, 201, 202)
                if success:
                    logger.info(f"Webhook enviado para: {webhook_url}")
                else:
                    logger.warning(f"Webhook falhou: {response.status}")
                return success
                
        except Exception as e:
            logger.error(f"Erro ao enviar webhook: {e}")
            return False
    
    def can_send(self, notification: Notification) -> bool:
        return (notification.channel == NotificationChannel.WEBHOOK and 
                'webhook_url' in notification.data)
    
    def get_name(self) -> str:
        return "Webhook Notification Handler"

class TelegramNotificationHandler(NotificationHandler):
    """Handler para notificações do Telegram"""
    
    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        
    async def send(self, notification: Notification) -> bool:
        try:
            chat_id = notification.data.get('chat_id')
            if not chat_id:
                return False
            
            import aiohttp
            
            message = f"*{notification.title}*\n\n{notification.message}"
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/sendMessage"
                payload = {
                    'chat_id': chat_id,
                    'text': message,
                    'parse_mode': 'Markdown',
                    'disable_notification': notification.priority == NotificationPriority.LOW
                }
                
                async with session.post(url, json=payload) as response:
                    result = await response.json()
                    success = result.get('ok', False)
                    
                    if success:
                        logger.info(f"Mensagem Telegram enviada para chat: {chat_id}")
                    else:
                        logger.warning(f"Telegram falhou: {result}")
                    
                    return success
                    
        except Exception as e:
            logger.error(f"Erro ao enviar Telegram: {e}")
            return False
    
    def can_send(self, notification: Notification) -> bool:
        return (notification.channel == NotificationChannel.TELEGRAM and 
                'chat_id' in notification.data)
    
    def get_name(self) -> str:
        return "Telegram Notification Handler"

class LogNotificationHandler(NotificationHandler):
    """Handler para logging apenas"""
    
    async def send(self, notification: Notification) -> bool:
        level = logging.INFO
        if notification.priority in [NotificationPriority.HIGH, NotificationPriority.URGENT]:
            level = logging.WARNING
        
        logger.log(level, f"[NOTIF] {notification.title}: {notification.message}")
        return True
    
    def can_send(self, notification: Notification) -> bool:
        return notification.channel == NotificationChannel.LOG
    
    def get_name(self) -> str:
        return "Log Notification Handler"

class NotificationSystem:
    """
    Sistema de notificações multi-canal com:
    - Suporte a múltiplos handlers
    - Sistema de filas com prioridade
    - Retry automático
    - Fallback entre canais
    - Limitação de rate
    """
    
    def __init__(self, max_queue_size: int = 10000):
        """
        Inicializa o sistema de notificações
        
        Args:
            max_queue_size: Tamanho máximo da fila
        """
        self.max_queue_size = max_queue_size
        
        # Handlers registrados
        self.handlers: List[NotificationHandler] = []
        
        # Fila de notificações (PriorityQueue)
        self.notification_queue = PriorityQueue(maxsize=max_queue_size)
        
        # Threads de worker
        self.worker_threads: List[threading.Thread] = []
        self.running = False
        
        # Estatísticas
        self.stats = {
            'sent': 0,
            'failed': 0,
            'queued': 0,
            'by_channel': {c.value: 0 for c in NotificationChannel}
        }
        
        # Rate limiting
        self.rate_limits: Dict[NotificationChannel, Dict[str, Any]] = {}
        
        # Callbacks
        self.callbacks = {
            'on_sent': [],
            'on_failed': [],
            'on_queued': []
        }
        
        self.lock = threading.RLock()
        logger.info("NotificationSystem inicializado")
    
    def register_handler(self, handler: NotificationHandler):
        """Registra um handler de notificação"""
        with self.lock:
            self.handlers.append(handler)
            logger.info(f"Handler registrado: {handler.get_name()}")
    
    def register_default_handlers(self, config: Optional[Dict[str, Any]] = None):
        """Registra handlers padrão baseados em configuração"""
        config = config or {}
        
        # Handler de log (sempre disponível)
        self.register_handler(LogNotificationHandler())
        
        # Handler in-app (se configurado)
        if config.get('in_app', {}).get('enabled', False):
            gui_callback = config['in_app'].get('gui_callback')
            self.register_handler(InAppNotificationHandler(gui_callback))
        
        # Handler de email (se configurado)
        email_config = config.get('email', {})
        if email_config.get('enabled', False):
            try:
                handler = EmailNotificationHandler(
                    smtp_server=email_config['smtp_server'],
                    smtp_port=email_config['smtp_port'],
                    username=email_config['username'],
                    password=email_config['password'],
                    from_email=email_config['from_email']
                )
                self.register_handler(handler)
            except Exception as e:
                logger.error(f"Erro ao configurar email handler: {e}")
        
        # Handler de Telegram (se configurado)
        telegram_config = config.get('telegram', {})
        if telegram_config.get('enabled', False):
            try:
                handler = TelegramNotificationHandler(
                    bot_token=telegram_config['bot_token']
                )
                self.register_handler(handler)
            except Exception as e:
                logger.error(f"Erro ao configurar Telegram handler: {e}")
        
        # Handler de Webhook (se configurado)
        webhook_config = config.get('webhook', {})
        if webhook_config.get('enabled', False):
            try:
                handler = WebhookNotificationHandler(
                    timeout=webhook_config.get('timeout', 10)
                )
                self.register_handler(handler)
            except Exception as e:
                logger.error(f"Erro ao configurar Webhook handler: {e}")
    
    def send_notification(
        self,
        title: str,
        message: str,
        channel: NotificationChannel,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        data: Optional[Dict[str, Any]] = None,
        max_retries: int = 3,
        ttl_seconds: Optional[int] = None
    ) -> str:
        """
        Enfileira uma notificação para envio
        
        Returns:
            ID da notificação
        """
        with self.lock:
            # Verificar se a fila está cheia
            if self.notification_queue.qsize() >= self.max_queue_size:
                logger.warning("Fila de notificações cheia")
                return ""
            
            # Gerar ID
            notification_id = f"notif_{int(time.time() * 1000)}_{self.stats['queued']}"
            
            # Calcular expiração
            expires_at = None
            if ttl_seconds:
                expires_at = time.time() + ttl_seconds
            
            # Criar notificação
            notification = Notification(
                id=notification_id,
                title=title,
                message=message,
                channel=channel,
                priority=priority,
                timestamp=time.time(),
                data=data or {},
                max_retries=max_retries,
                expires_at=expires_at
            )
            
            # Adicionar à fila com prioridade (menor número = maior prioridade)
            # Usamos negativo para que URGENT (3) venha primeiro
            priority_value = -priority.value
            
            try:
                self.notification_queue.put((priority_value, time.time(), notification))
                self.stats['queued'] += 1
                self.stats['by_channel'][channel.value] += 1
                
                # Disparar callback
                self._trigger_callbacks('on_queued', notification)
                
                logger.debug(f"Notificação enfileirada: {notification_id} [{channel.value}]")
                
                return notification_id
                
            except Exception as e:
                logger.error(f"Erro ao enfileirar notificação: {e}")
                return ""
    
    def send_notification_with_fallback(
        self,
        title: str,
        message: str,
        primary_channel: NotificationChannel,
        fallback_channels: List[NotificationChannel],
        **kwargs
    ) -> List[str]:
        """
        Tenta enviar por canal primário, com fallback para outros
        
        Returns:
            Lista de IDs de notificações criadas
        """
        notification_ids = []
        
        # Primeiro, tentar canal primário
        notification_id = self.send_notification(
            title=title,
            message=message,
            channel=primary_channel,
            **kwargs
        )
        
        if notification_id:
            notification_ids.append(notification_id)
        
        # Se falhou ou para alta prioridade, adicionar fallbacks
        if not notification_id or kwargs.get('priority') == NotificationPriority.URGENT:
            for fallback_channel in fallback_channels:
                fb_id = self.send_notification(
                    title=f"[Fallback] {title}",
                    message=message,
                    channel=fallback_channel,
                    **{**kwargs, 'priority': NotificationPriority.LOW}
                )
                if fb_id:
                    notification_ids.append(fb_id)
        
        return notification_ids
    
    def _worker_loop(self, worker_id: int):
        """Loop do worker para processar notificações"""
        logger.info(f"Worker {worker_id} iniciado")
        
        while self.running or not self.notification_queue.empty():
            try:
                # Obter próxima notificação
                priority, timestamp, notification = self.notification_queue.get(
                    timeout=1  # Timeout para verificar self.running
                )
                
                # Verificar expiração
                if notification.is_expired:
                    logger.debug(f"Notificação expirada: {notification.id}")
                    self.notification_queue.task_done()
                    continue
                
                # Encontrar handler apropriado
                handler = None
                for h in self.handlers:
                    if h.can_send(notification):
                        handler = h
                        break
                
                if not handler:
                    logger.warning(f"Nenhum handler para canal: {notification.channel}")
                    self.notification_queue.task_done()
                    continue
                
                # Verificar rate limit
                if self._check_rate_limit(notification.channel):
                    logger.debug(f"Rate limit atingido para: {notification.channel}")
                    # Re-enfileirar com pequeno atraso
                    time.sleep(1)
                    self.notification_queue.put((priority, timestamp, notification))
                    self.notification_queue.task_done()
                    continue
                
                # Tentar enviar
                success = False
                try:
                    # Executar handler assíncrono em thread separada
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    success = loop.run_until_complete(handler.send(notification))
                    loop.close()
                except Exception as e:
                    logger.error(f"Erro no handler {handler.get_name()}: {e}")
                    success = False
                
                # Atualizar estatísticas e processar retry
                with self.lock:
                    if success:
                        self.stats['sent'] += 1
                        self._trigger_callbacks('on_sent', notification)
                        logger.debug(f"Notificação enviada: {notification.id}")
                    else:
                        self.stats['failed'] += 1
                        self._trigger_callbacks('on_failed', notification)
                        
                        # Tentar novamente se possível
                        if notification.retry_count < notification.max_retries:
                            notification.retry_count += 1
                            # Re-enfileirar com menor prioridade
                            new_priority = priority + 1  # Diminuir prioridade
                            self.notification_queue.put(
                                (new_priority, time.time(), notification)
                            )
                            logger.debug(f"Retry {notification.retry_count} para: {notification.id}")
                        else:
                            logger.warning(f"Notificação falhou após {notification.max_retries} tentativas: {notification.id}")
                
                self.notification_queue.task_done()
                
            except Exception as e:
                if self.running:  # Apenas log se não for timeout esperado
                    logger.error(f"Erro no worker {worker_id}: {e}")
    
    def _check_rate_limit(self, channel: NotificationChannel) -> bool:
        """Verifica rate limit para um canal"""
        if channel not in self.rate_limits:
            return False
        
        limit_config = self.rate_limits[channel]
        current_time = time.time()
        
        # Implementação básica de rate limiting
        if 'last_sent' in limit_config:
            time_since_last = current_time - limit_config['last_sent']
            if time_since_last < limit_config.get('min_interval', 0):
                return True
        
        limit_config['last_sent'] = current_time
        return False
    
    def set_rate_limit(
        self,
        channel: NotificationChannel,
        min_interval: float
    ):
        """Configura rate limit para um canal"""
        self.rate_limits[channel] = {
            'min_interval': min_interval,
            'last_sent': 0
        }
    
    def start_workers(self, num_workers: int = 3):
        """Inicia workers para processar notificações"""
        if self.running:
            return
        
        self.running = True
        
        for i in range(num_workers):
            worker = threading.Thread(
                target=self._worker_loop,
                args=(i,),
                daemon=True,
                name=f"NotificationWorker-{i}"
            )
            worker.start()
            self.worker_threads.append(worker)
        
        logger.info(f"{num_workers} workers de notificação iniciados")
    
    def stop(self, wait: bool = True):
        """Para o sistema de notificações"""
        self.running = False
        
        if wait:
            # Esperar workers terminarem
            for worker in self.worker_threads:
                worker.join(timeout=5)
            
            # Processar itens restantes na fila
            self._process_remaining()
        
        logger.info("NotificationSystem parado")
    
    def _process_remaining(self):
        """Processa itens restantes na fila"""
        logger.info("Processando notificações restantes na fila...")
        
        while not self.notification_queue.empty():
            try:
                priority, timestamp, notification = self.notification_queue.get_nowait()
                
                # Tentar enviar imediatamente
                for handler in self.handlers:
                    if handler.can_send(notification):
                        try:
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            loop.run_until_complete(handler.send(notification))
                            loop.close()
                            logger.debug(f"Notificação processada no shutdown: {notification.id}")
                        except Exception as e:
                            logger.error(f"Erro ao processar notificação no shutdown: {e}")
                        break
                
                self.notification_queue.task_done()
                
            except Exception as e:
                logger.error(f"Erro ao processar fila restante: {e}")
                break
    
    def register_callback(self, event: str, callback: Callable[[Notification], None]):
        """Registra callback para eventos"""
        if event not in self.callbacks:
            raise ValueError(f"Evento inválido: {event}")
        
        self.callbacks[event].append(callback)
    
    def _trigger_callbacks(self, event: str, notification: Notification):
        """Dispara callbacks para um evento"""
        for callback in self.callbacks.get(event, []):
            try:
                callback(notification)
            except Exception as e:
                logger.error(f"Erro em callback {event}: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do sistema"""
        with self.lock:
            stats = self.stats.copy()
            stats['queue_size'] = self.notification_queue.qsize()
            stats['active_workers'] = sum(1 for w in self.worker_threads if w.is_alive())
            stats['handlers'] = [h.get_name() for h in self.handlers]
            return stats
    
    def clear_queue(self):
        """Limpa a fila de notificações"""
        with self.lock:
            while not self.notification_queue.empty():
                try:
                    self.notification_queue.get_nowait()
                    self.notification_queue.task_done()
                except Exception:
                    break
            
            self.stats['queued'] = 0
            logger.info("Fila de notificações limpa")