"""
Sistema de Cache Avançado
Cache em memória, disco e Redis com TTL e LRU
"""

import time
import pickle
import hashlib
import threading
import json
from typing import Any, Dict, Optional, Callable, Union, List
from collections import OrderedDict
from datetime import datetime, timedelta
import logging
from functools import wraps
import asyncio

logger = logging.getLogger(__name__)

class Cache:
    """
    Classe base para sistemas de cache
    """
    
    def __init__(self, name: str = "default"):
        """
        Inicializa o cache
        
        Args:
            name: Nome do cache
        """
        self.name = name
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'evictions': 0
        }
    
    def get(self, key: str) -> Optional[Any]:
        """
        Obtém valor do cache
        
        Args:
            key: Chave do cache
            
        Returns:
            Valor ou None se não encontrado/expirado
        """
        raise NotImplementedError
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Armazena valor no cache
        
        Args:
            key: Chave do cache
            value: Valor a armazenar
            ttl: Time to live em segundos
            
        Returns:
            True se bem sucedido
        """
        raise NotImplementedError
    
    def delete(self, key: str) -> bool:
        """
        Remove valor do cache
        
        Args:
            key: Chave do cache
            
        Returns:
            True se removido
        """
        raise NotImplementedError
    
    def clear(self) -> bool:
        """
        Limpa todo o cache
        
        Returns:
            True se bem sucedido
        """
        raise NotImplementedError
    
    def exists(self, key: str) -> bool:
        """
        Verifica se chave existe no cache
        
        Args:
            key: Chave do cache
            
        Returns:
            True se existe
        """
        return self.get(key) is not None
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtém estatísticas do cache
        
        Returns:
            Dicionário com estatísticas
        """
        return self.stats.copy()
    
    def reset_stats(self):
        """Reseta estatísticas do cache"""
        self.stats = {k: 0 for k in self.stats}

class LRUCache(Cache):
    """
    Cache LRU (Least Recently Used) em memória
    """
    
    def __init__(self, max_size: int = 1000, name: str = "lru"):
        """
        Inicializa cache LRU
        
        Args:
            max_size: Tamanho máximo do cache
            name: Nome do cache
        """
        super().__init__(name)
        self.max_size = max_size
        self.cache = OrderedDict()
        self.lock = threading.RLock()
        
        logger.info(f"LRUCache inicializado: {name} (max_size={max_size})")
    
    def get(self, key: str) -> Optional[Any]:
        with self.lock:
            if key not in self.cache:
                self.stats['misses'] += 1
                return None
            
            # Move para o final (mais recente)
            value, expires = self.cache.pop(key)
            
            # Verifica expiração
            if expires and time.time() > expires:
                self.stats['evictions'] += 1
                return None
            
            self.cache[key] = (value, expires)
            self.stats['hits'] += 1
            return value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        with self.lock:
            expires = time.time() + ttl if ttl else None
            
            # Remove se já existe
            if key in self.cache:
                del self.cache[key]
            
            # Adiciona novo item
            self.cache[key] = (value, expires)
            
            # Remove o mais antigo se exceder tamanho
            if len(self.cache) > self.max_size:
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
                self.stats['evictions'] += 1
            
            self.stats['sets'] += 1
            return True
    
    def delete(self, key: str) -> bool:
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                self.stats['deletes'] += 1
                return True
            return False
    
    def clear(self) -> bool:
        with self.lock:
            self.cache.clear()
            logger.info(f"LRUCache {self.name} limpo")
            return True
    
    def cleanup_expired(self) -> int:
        """
        Remove itens expirados
        
        Returns:
            Número de itens removidos
        """
        with self.lock:
            expired_keys = []
            current_time = time.time()
            
            for key, (value, expires) in self.cache.items():
                if expires and current_time > expires:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.cache[key]
                self.stats['evictions'] += 1
            
            if expired_keys:
                logger.debug(f"LRUCache {self.name}: {len(expired_keys)} itens expirados removidos")
            
            return len(expired_keys)

class TTLCache(Cache):
    """
    Cache com TTL (Time To Live) automático
    """
    
    def __init__(self, default_ttl: int = 300, name: str = "ttl"):
        """
        Inicializa cache TTL
        
        Args:
            default_ttl: TTL padrão em segundos
            name: Nome do cache
        """
        super().__init__(name)
        self.default_ttl = default_ttl
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.RLock()
        
        # Thread de limpeza
        self.cleanup_thread = None
        self.running = True
        self.start_cleanup_daemon()
        
        logger.info(f"TTLCache inicializado: {name} (default_ttl={default_ttl}s)")
    
    def get(self, key: str) -> Optional[Any]:
        with self.lock:
            if key not in self.cache:
                self.stats['misses'] += 1
                return None
            
            item = self.cache[key]
            
            # Verifica expiração
            if time.time() > item['expires']:
                del self.cache[key]
                self.stats['evictions'] += 1
                return None
            
            self.stats['hits'] += 1
            return item['value']
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        with self.lock:
            ttl = ttl or self.default_ttl
            expires = time.time() + ttl
            
            self.cache[key] = {
                'value': value,
                'expires': expires,
                'ttl': ttl,
                'created': time.time()
            }
            
            self.stats['sets'] += 1
            return True
    
    def delete(self, key: str) -> bool:
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                self.stats['deletes'] += 1
                return True
            return False
    
    def clear(self) -> bool:
        with self.lock:
            self.cache.clear()
            logger.info(f"TTLCache {self.name} limpo")
            return True
    
    def start_cleanup_daemon(self, interval: int = 60):
        """
        Inicia thread de limpeza de itens expirados
        
        Args:
            interval: Intervalo de limpeza em segundos
        """
        def cleanup_loop():
            while self.running:
                time.sleep(interval)
                try:
                    expired_count = self._cleanup_expired()
                    if expired_count > 0:
                        logger.debug(f"TTLCache {self.name}: {expired_count} itens expirados removidos")
                except Exception as e:
                    logger.error(f"Erro na limpeza do TTLCache: {e}")
        
        self.cleanup_thread = threading.Thread(
            target=cleanup_loop,
            daemon=True,
            name=f"TTLCache-Cleanup-{self.name}"
        )
        self.cleanup_thread.start()
    
    def _cleanup_expired(self) -> int:
        """
        Remove itens expirados
        
        Returns:
            Número de itens removidos
        """
        with self.lock:
            expired_keys = []
            current_time = time.time()
            
            for key, item in self.cache.items():
                if current_time > item['expires']:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.cache[key]
                self.stats['evictions'] += 1
            
            return len(expired_keys)
    
    def stop(self):
        """Para o cache e thread de limpeza"""
        self.running = False
        if self.cleanup_thread:
            self.cleanup_thread.join(timeout=5)

class RedisCache(Cache):
    """
    Cache usando Redis (requer redis-py)
    """
    
    def __init__(self, host: str = 'localhost', port: int = 6379, 
                 db: int = 0, password: str = None, name: str = "redis"):
        """
        Inicializa cache Redis
        
        Args:
            host: Host do Redis
            port: Porta do Redis
            db: Número do banco de dados
            password: Senha do Redis
            name: Nome do cache
        """
        super().__init__(name)
        
        try:
            import redis
            self.redis = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=False,
                socket_timeout=5,
                socket_connect_timeout=5
            )
            
            # Testa conexão
            self.redis.ping()
            
        except ImportError:
            raise ImportError("redis-py não instalado. Instale com: pip install redis")
        except Exception as e:
            logger.error(f"Erro ao conectar ao Redis: {e}")
            raise
        
        logger.info(f"RedisCache inicializado: {name} ({host}:{port}/{db})")
    
    def get(self, key: str) -> Optional[Any]:
        try:
            data = self.redis.get(key)
            
            if data is None:
                self.stats['misses'] += 1
                return None
            
            # Deserializa
            value = pickle.loads(data)
            self.stats['hits'] += 1
            return value
            
        except Exception as e:
            logger.error(f"Erro ao obter do RedisCache: {e}")
            self.stats['misses'] += 1
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        try:
            # Serializa
            data = pickle.dumps(value)
            
            if ttl:
                self.redis.setex(key, ttl, data)
            else:
                self.redis.set(key, data)
            
            self.stats['sets'] += 1
            return True
            
        except Exception as e:
            logger.error(f"Erro ao definir no RedisCache: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        try:
            result = self.redis.delete(key)
            if result:
                self.stats['deletes'] += 1
            return bool(result)
        except Exception as e:
            logger.error(f"Erro ao deletar do RedisCache: {e}")
            return False
    
    def clear(self) -> bool:
        try:
            self.redis.flushdb()
            logger.info(f"RedisCache {self.name} limpo")
            return True
        except Exception as e:
            logger.error(f"Erro ao limpar RedisCache: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        try:
            return self.redis.exists(key) == 1
        except Exception as e:
            logger.error(f"Erro ao verificar existência no RedisCache: {e}")
            return False

class CacheManager:
    """
    Gerenciador de múltiplos caches com fallback
    """
    
    def __init__(self):
        self.caches: Dict[str, Cache] = {}
        self.default_cache = None
        
    def register_cache(self, cache: Cache, make_default: bool = False):
        """
        Registra um cache
        
        Args:
            cache: Instância do cache
            make_default: Se deve tornar este cache padrão
        """
        self.caches[cache.name] = cache
        
        if make_default or self.default_cache is None:
            self.default_cache = cache
        
        logger.info(f"Cache registrado: {cache.name}")
    
    def get_cache(self, name: str = None) -> Optional[Cache]:
        """
        Obtém cache pelo nome
        
        Args:
            name: Nome do cache (None para padrão)
            
        Returns:
            Instância do cache ou None
        """
        if name is None:
            return self.default_cache
        
        return self.caches.get(name)
    
    def get(self, key: str, cache_name: str = None) -> Optional[Any]:
        """
        Obtém valor do cache
        
        Args:
            key: Chave do cache
            cache_name: Nome do cache (None para padrão)
            
        Returns:
            Valor ou None
        """
        cache = self.get_cache(cache_name)
        
        if cache:
            return cache.get(key)
        
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None, 
            cache_name: str = None) -> bool:
        """
        Armazena valor no cache
        
        Args:
            key: Chave do cache
            value: Valor a armazenar
            ttl: Time to live
            cache_name: Nome do cache (None para padrão)
            
        Returns:
            True se bem sucedido
        """
        cache = self.get_cache(cache_name)
        
        if cache:
            return cache.set(key, value, ttl)
        
        return False
    
    def delete(self, key: str, cache_name: str = None) -> bool:
        """
        Remove valor do cache
        
        Args:
            key: Chave do cache
            cache_name: Nome do cache (None para padrão)
            
        Returns:
            True se removido
        """
        cache = self.get_cache(cache_name)
        
        if cache:
            return cache.delete(key)
        
        return False
    
    def clear_all(self):
        """Limpa todos os caches registrados"""
        for cache in self.caches.values():
            cache.clear()
        
        logger.info("Todos os caches limpos")

# Decorators para cache
def cache_decorator(ttl: int = 300, cache_name: str = None, 
                   key_func: Callable = None):
    """
    Decorator para cache de funções síncronas
    
    Args:
        ttl: Time to live em segundos
        cache_name: Nome do cache
        key_func: Função para gerar chave de cache
        
    Returns:
        Função decorada
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Gera chave de cache
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Hash dos argumentos
                key_data = (func.__module__, func.__name__, args, tuple(sorted(kwargs.items())))
                cache_key = hashlib.md5(pickle.dumps(key_data)).hexdigest()
            
            # Tenta obter do cache
            cache = CacheManager().get_cache(cache_name)
            
            if cache:
                cached_result = cache.get(cache_key)
                if cached_result is not None:
                    return cached_result
            
            # Executa função
            result = func(*args, **kwargs)
            
            # Armazena no cache
            if cache:
                cache.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    
    return decorator

def async_cache_decorator(ttl: int = 300, cache_name: str = None,
                         key_func: Callable = None):
    """
    Decorator para cache de funções assíncronas
    
    Args:
        ttl: Time to live em segundos
        cache_name: Nome do cache
        key_func: Função para gerar chave de cache
        
    Returns:
        Função decorada
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Gera chave de cache
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                key_data = (func.__module__, func.__name__, args, tuple(sorted(kwargs.items())))
                cache_key = hashlib.md5(pickle.dumps(key_data)).hexdigest()
            
            # Tenta obter do cache
            cache = CacheManager().get_cache(cache_name)
            
            if cache:
                cached_result = cache.get(cache_key)
                if cached_result is not None:
                    return cached_result
            
            # Executa função
            result = await func(*args, **kwargs)
            
            # Armazena no cache
            if cache:
                cache.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    
    return decorator