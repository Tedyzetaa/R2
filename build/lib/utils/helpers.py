"""
Helpers e Utilitários Gerais
Funções auxiliares para programação diária
"""

import time
import asyncio
import inspect
import functools
import itertools
from typing import Any, Callable, Dict, List, Optional, Union, TypeVar, Generator
from datetime import datetime, timedelta
from contextlib import contextmanager
import logging
import threading
from queue import Queue
import signal
import sys

logger = logging.getLogger(__name__)

# Decorators
def retry(max_attempts: int = 3, delay: float = 1.0, 
          exceptions: tuple = (Exception,), backoff: float = 2.0):
    """
    Decorator para retry automático de funções
    
    Args:
        max_attempts: Número máximo de tentativas
        delay: Delay inicial entre tentativas
        exceptions: Exceções que disparam retry
        backoff: Fator de backoff exponencial
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts:
                        logger.error(f"Falha após {max_attempts} tentativas: {e}")
                        raise
                    
                    wait_time = delay * (backoff ** (attempt - 1))
                    logger.warning(f"Tentativa {attempt} falhou, tentando novamente em {wait_time:.1f}s: {e}")
                    time.sleep(wait_time)
            
            raise last_exception
        
        return wrapper
    
    return decorator

def async_retry(max_attempts: int = 3, delay: float = 1.0,
                exceptions: tuple = (Exception,), backoff: float = 2.0):
    """
    Decorator para retry automático de funções async
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts:
                        logger.error(f"Falha após {max_attempts} tentativas: {e}")
                        raise
                    
                    wait_time = delay * (backoff ** (attempt - 1))
                    logger.warning(f"Tentativa {attempt} falhou, tentando novamente em {wait_time:.1f}s: {e}")
                    await asyncio.sleep(wait_time)
            
            raise last_exception
        
        return wrapper
    
    return decorator

def timeout(seconds: float, timeout_message: str = "Timeout excedido"):
    """
    Decorator para timeout de funções síncronas
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = None
            exception = None
            
            def target():
                nonlocal result, exception
                try:
                    result = func(*args, **kwargs)
                except Exception as e:
                    exception = e
            
            thread = threading.Thread(target=target)
            thread.daemon = True
            thread.start()
            thread.join(timeout=seconds)
            
            if thread.is_alive():
                raise TimeoutError(timeout_message)
            
            if exception:
                raise exception
            
            return result
        
        return wrapper
    
    return decorator

def async_timeout(seconds: float):
    """
    Decorator para timeout de funções async
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=seconds
                )
            except asyncio.TimeoutError:
                raise TimeoutError(f"Timeout de {seconds} segundos excedido")
        
        return wrapper
    
    return decorator

def rate_limit(calls_per_second: float = 1.0):
    """
    Decorator para rate limiting de funções
    """
    def decorator(func):
        last_called = [0.0]
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            wait_time = 1.0 / calls_per_second - elapsed
            
            if wait_time > 0:
                time.sleep(wait_time)
            
            last_called[0] = time.time()
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator

def async_rate_limit(calls_per_second: float = 1.0):
    """
    Decorator para rate limiting de funções async
    """
    def decorator(func):
        last_called = [0.0]
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            wait_time = 1.0 / calls_per_second - elapsed
            
            if wait_time > 0:
                await asyncio.sleep(wait_time)
            
            last_called[0] = time.time()
            return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator

# Classes utilitárias
class Singleton(type):
    """
    Metaclass para padrão Singleton
    """
    _instances = {}
    
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]

class Observable:
    """
    Implementação do padrão Observer
    """
    def __init__(self):
        self._observers = []
    
    def add_observer(self, observer):
        """Adiciona observador"""
        if observer not in self._observers:
            self._observers.append(observer)
    
    def remove_observer(self, observer):
        """Remove observador"""
        if observer in self._observers:
            self._observers.remove(observer)
    
    def notify_observers(self, *args, **kwargs):
        """Notifica todos os observadores"""
        for observer in self._observers:
            observer.update(self, *args, **kwargs)

class EventEmitter:
    """
    Emissor de eventos estilo Node.js
    """
    def __init__(self):
        self._events = {}
    
    def on(self, event: str, callback: Callable):
        """Registra callback para evento"""
        if event not in self._events:
            self._events[event] = []
        self._events[event].append(callback)
    
    def once(self, event: str, callback: Callable):
        """Registra callback que será chamado apenas uma vez"""
        def wrapper(*args, **kwargs):
            self.off(event, wrapper)
            return callback(*args, **kwargs)
        
        self.on(event, wrapper)
    
    def off(self, event: str, callback: Callable):
        """Remove callback de evento"""
        if event in self._events:
            self._events[event] = [cb for cb in self._events[event] if cb != callback]
    
    def emit(self, event: str, *args, **kwargs):
        """Emite evento para todos os callbacks"""
        if event in self._events:
            for callback in self._events[event]:
                try:
                    callback(*args, **kwargs)
                except Exception as e:
                    logger.error(f"Erro no callback do evento {event}: {e}")
    
    def remove_all_listeners(self, event: str = None):
        """Remove todos os listeners"""
        if event:
            self._events.pop(event, None)
        else:
            self._events.clear()

class ProgressBar:
    """
    Barra de progresso para terminal
    """
    def __init__(self, total: int, width: int = 50, 
                 fill: str = '█', empty: str = '░'):
        self.total = total
        self.width = width
        self.fill = fill
        self.empty = empty
        self.current = 0
        self.start_time = time.time()
    
    def update(self, n: int = 1):
        """Atualiza progresso"""
        self.current += n
        self._display()
    
    def _display(self):
        """Exibe barra de progresso"""
        percent = self.current / self.total
        filled_width = int(self.width * percent)
        bar = self.fill * filled_width + self.empty * (self.width - filled_width)
        
        elapsed = time.time() - self.start_time
        if percent > 0:
            eta = elapsed / percent * (1 - percent)
        else:
            eta = float('inf')
        
        sys.stdout.write(f'\r[{bar}] {percent:.1%} | {self.current}/{self.total} | '
                        f'Tempo: {self._format_time(elapsed)} | '
                        f'ETA: {self._format_time(eta)}')
        sys.stdout.flush()
    
    def finish(self):
        """Finaliza barra de progresso"""
        self.update(self.total - self.current)
        print()
    
    @staticmethod
    def _format_time(seconds: float) -> str:
        """Formata tempo em segundos"""
        if seconds == float('inf'):
            return '--:--'
        
        minutes, seconds = divmod(int(seconds), 60)
        hours, minutes = divmod(minutes, 60)
        
        if hours > 0:
            return f'{hours}:{minutes:02d}:{seconds:02d}'
        else:
            return f'{minutes:02d}:{seconds:02d}'

class Spinner:
    """
    Spinner animado para operações longas
    """
    def __init__(self, message: str = "Processando"):
        self.message = message
        self.spinner = itertools.cycle(['-', '\\', '|', '/'])
        self.running = False
        self.thread = None
    
    def start(self):
        """Inicia spinner"""
        self.running = True
        self.thread = threading.Thread(target=self._spin)
        self.thread.daemon = True
        self.thread.start()
    
    def _spin(self):
        """Loop de animação do spinner"""
        while self.running:
            sys.stdout.write(f'\r{self.message} {next(self.spinner)}')
            sys.stdout.flush()
            time.sleep(0.1)
    
    def stop(self, message: str = None):
        """Para spinner"""
        self.running = False
        if self.thread:
            self.thread.join()
        
        sys.stdout.write('\r' + ' ' * (len(self.message) + 2) + '\r')
        if message:
            print(message)
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

class TablePrinter:
    """
    Impressão formatada de tabelas
    """
    def __init__(self, headers: List[str], align: List[str] = None):
        self.headers = headers
        self.rows = []
        self.align = align or ['<'] * len(headers)
    
    def add_row(self, row: List[Any]):
        """Adiciona linha à tabela"""
        self.rows.append(row)
    
    def print(self):
        """Imprime tabela formatada"""
        # Calcula larguras das colunas
        col_widths = []
        for i, header in enumerate(self.headers):
            max_width = len(str(header))
            for row in self.rows:
                if i < len(row):
                    max_width = max(max_width, len(str(row[i])))
            col_widths.append(max_width)
        
        # Imprime cabeçalho
        header_line = ' | '.join(
            f'{str(header):{align}{width}}'
            for header, align, width in zip(self.headers, self.align, col_widths)
        )
        separator = '-' * len(header_line)
        
        print(header_line)
        print(separator)
        
        # Imprime linhas
        for row in self.rows:
            row_line = ' | '.join(
                f'{str(cell if i < len(row) else ""):{align}{width}}'
                for i, (align, width) in enumerate(zip(self.align, col_widths))
            )
            print(row_line)

class ColorFormatter:
    """
    Formatação de cores para terminal
    """
    COLORS = {
        'black': '\033[30m',
        'red': '\033[31m',
        'green': '\033[32m',
        'yellow': '\033[33m',
        'blue': '\033[34m',
        'magenta': '\033[35m',
        'cyan': '\033[36m',
        'white': '\033[37m',
        'reset': '\033[0m',
        'bold': '\033[1m',
        'underline': '\033[4m'
    }
    
    @classmethod
    def colorize(cls, text: str, color: str = None, 
                bg_color: str = None, bold: bool = False,
                underline: bool = False) -> str:
        """
        Aplica cores e formatação ao texto
        
        Args:
            text: Texto a ser colorido
            color: Cor do texto
            bg_color: Cor do fundo
            bold: Texto em negrito
            underline: Texto sublinhado
            
        Returns:
            Texto formatado
        """
        codes = []
        
        if color and color in cls.COLORS:
            codes.append(cls.COLORS[color])
        
        if bg_color:
            bg_code = cls.COLORS.get(bg_color, '').replace('[3', '[4')
            if bg_code:
                codes.append(bg_code)
        
        if bold:
            codes.append(cls.COLORS['bold'])
        
        if underline:
            codes.append(cls.COLORS['underline'])
        
        if codes:
            return f"{''.join(codes)}{text}{cls.COLORS['reset']}"
        
        return text
    
    @classmethod
    def print(cls, text: str, color: str = None, **kwargs):
        """Imprime texto colorido"""
        print(cls.colorize(text, color, **kwargs))

# Funções utilitárias
def format_bytes(size: int) -> str:
    """
    Formata bytes para string legível
    
    Args:
        size: Tamanho em bytes
        
    Returns:
        String formatada
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB', 'PB']:
        if size < 1024.0 or unit == 'PB':
            break
        size /= 1024.0
    return f"{size:.2f} {unit}"

def format_time(seconds: float, show_ms: bool = False) -> str:
    """
    Formata tempo em segundos para string legível
    
    Args:
        seconds: Tempo em segundos
        show_ms: Mostrar milissegundos
        
    Returns:
        String formatada
    """
    if seconds < 1:
        if show_ms:
            return f"{seconds*1000:.1f}ms"
        return f"{seconds:.3f}s"
    
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    
    parts = []
    if days > 0:
        parts.append(f"{int(days)}d")
    if hours > 0:
        parts.append(f"{int(hours)}h")
    if minutes > 0:
        parts.append(f"{int(minutes)}m")
    if seconds > 0 or not parts:
        parts.append(f"{seconds:.1f}s")
    
    return ' '.join(parts)

def format_number(number: float, precision: int = 2) -> str:
    """
    Formata número com separadores de milhar
    
    Args:
        number: Número a ser formatado
        precision: Casas decimais
        
    Returns:
        String formatada
    """
    if number == 0:
        return "0"
    
    if abs(number) < 0.001:
        return f"{number:.2e}"
    
    if abs(number) >= 1000000:
        return f"{number/1000000:.{precision}f}M"
    
    if abs(number) >= 1000:
        return f"{number/1000:.{precision}f}K"
    
    return f"{number:.{precision}f}"

def generate_id(prefix: str = '', length: int = 8) -> str:
    """
    Gera ID único
    
    Args:
        prefix: Prefixo para o ID
        length: Comprimento do ID (sem o prefixo)
        
    Returns:
        ID único
    """
    import random
    import string
    
    chars = string.ascii_letters + string.digits
    random_id = ''.join(random.choice(chars) for _ in range(length))
    return f"{prefix}{random_id}" if prefix else random_id

def chunk_list(lst: List, chunk_size: int) -> Generator[List, None, None]:
    """
    Divide lista em chunks
    
    Args:
        lst: Lista original
        chunk_size: Tamanho de cada chunk
        
    Yields:
        Chunks da lista
    """
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]

def flatten_dict(d: Dict, parent_key: str = '', sep: str = '.') -> Dict:
    """
    Achata dicionário aninhado
    
    Args:
        d: Dicionário aninhado
        parent_key: Chave pai
        sep: Separador
        
    Returns:
        Dicionário achatado
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep).items())
        else:
            items.append((new_key, v))
    
    return dict(items)

def deep_merge(source: Dict, destination: Dict) -> Dict:
    """
    Merge profundo de dicionários
    
    Args:
        source: Dicionário fonte
        destination: Dicionário destino
        
    Returns:
        Dicionário mergeado
    """
    for key, value in source.items():
        if isinstance(value, dict):
            node = destination.setdefault(key, {})
            deep_merge(value, node)
        else:
            destination[key] = value
    
    return destination

def get_nested_value(obj: Dict, key_path: str, default: Any = None, 
                    separator: str = '.') -> Any:
    """
    Obtém valor aninhado de dicionário
    
    Args:
        obj: Dicionário
        key_path: Caminho da chave
        default: Valor padrão
        separator: Separador
        
    Returns:
        Valor ou default
    """
    keys = key_path.split(separator)
    value = obj
    
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return default
    
    return value

def set_nested_value(obj: Dict, key_path: str, value: Any, 
                    separator: str = '.') -> Dict:
    """
    Define valor aninhado em dicionário
    
    Args:
        obj: Dicionário
        key_path: Caminho da chave
        value: Valor a ser definido
        separator: Separador
        
    Returns:
        Dicionário atualizado
    """
    keys = key_path.split(separator)
    current = obj
    
    for i, key in enumerate(keys[:-1]):
        if key not in current or not isinstance(current[key], dict):
            current[key] = {}
        current = current[key]
    
    current[keys[-1]] = value
    return obj

def benchmark(func: Callable, *args, **kwargs) -> Dict[str, Any]:
    """
    Benchmark de função
    
    Args:
        func: Função a ser benchmarkada
        *args: Argumentos da função
        **kwargs: Keyword arguments da função
        
    Returns:
        Dicionário com resultados do benchmark
    """
    import timeit
    
    start_time = time.time()
    start_mem = _get_memory_usage()
    
    result = func(*args, **kwargs)
    
    end_time = time.time()
    end_mem = _get_memory_usage()
    
    return {
        'result': result,
        'execution_time': end_time - start_time,
        'memory_used': end_mem - start_mem,
        'start_time': start_time,
        'end_time': end_time
    }

def async_benchmark(func: Callable, *args, **kwargs) -> Dict[str, Any]:
    """
    Benchmark de função async
    """
    import asyncio
    
    async def run():
        start_time = time.time()
        start_mem = _get_memory_usage()
        
        result = await func(*args, **kwargs)
        
        end_time = time.time()
        end_mem = _get_memory_usage()
        
        return {
            'result': result,
            'execution_time': end_time - start_time,
            'memory_used': end_mem - start_mem,
            'start_time': start_time,
            'end_time': end_time
        }
    
    return asyncio.run(run())

def _get_memory_usage() -> int:
    """Obtém uso de memória atual"""
    try:
        import psutil
        return psutil.Process().memory_info().rss
    except ImportError:
        return 0

@contextmanager
def timeout_context(seconds: float):
    """
    Context manager para timeout
    
    Args:
        seconds: Timeout em segundos
    """
    def timeout_handler(signum, frame):
        raise TimeoutError(f"Timeout de {seconds} segundos excedido")
    
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(int(seconds))
    
    try:
        yield
    finally:
        signal.alarm(0)

def memoize(maxsize: int = 128):
    """
    Decorator para memoização de funções
    
    Args:
        maxsize: Tamanho máximo do cache
    """
    def decorator(func):
        cache = {}
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key = (args, tuple(sorted(kwargs.items())))
            
            if key in cache:
                return cache[key]
            
            result = func(*args, **kwargs)
            
            if len(cache) >= maxsize:
                cache.pop(next(iter(cache)))
            
            cache[key] = result
            return result
        
        return wrapper
    
    return decorator