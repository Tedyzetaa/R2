"""
Sistema de Cache de Dados
Inicialização do diretório de cache
"""

import os
import json
import pickle
from datetime import datetime
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)

# Garantir que o diretório de cache existe
CACHE_DIR = os.path.dirname(os.path.abspath(__file__))
os.makedirs(CACHE_DIR, exist_ok=True)

# Subdiretórios de cache
CACHE_SUBDIRS = [
    'web',
    'api',
    'models',
    'images',
    'audio',
    'temp'
]

for subdir in CACHE_SUBDIRS:
    os.makedirs(os.path.join(CACHE_DIR, subdir), exist_ok=True)

# Arquivos de índice de cache
CACHE_INDEX_FILE = os.path.join(CACHE_DIR, 'cache_index.json')
CACHE_STATS_FILE = os.path.join(CACHE_DIR, 'cache_stats.json')

class CacheInitializer:
    """
    Inicializador do sistema de cache
    """
    
    @staticmethod
    def initialize_cache_system():
        """
        Inicializa o sistema de cache com estrutura padrão
        """
        # Criar índice de cache se não existir
        if not os.path.exists(CACHE_INDEX_FILE):
            CacheInitializer._create_cache_index()
        
        # Criar estatísticas de cache se não existir
        if not os.path.exists(CACHE_STATS_FILE):
            CacheInitializer._create_cache_stats()
        
        logger.info("Sistema de cache inicializado")
    
    @staticmethod
    def _create_cache_index():
        """Cria índice de cache inicial"""
        cache_index = {
            "version": "1.0.0",
            "created_at": datetime.now().isoformat(),
            "last_cleanup": None,
            "entries": {},
            "categories": {
                "web": {
                    "description": "Cache de requisições web",
                    "max_size": "100MB",
                    "max_age": 86400,  # 24 horas
                    "compression": "gzip"
                },
                "api": {
                    "description": "Cache de respostas de API",
                    "max_size": "50MB",
                    "max_age": 3600,  # 1 hora
                    "compression": "none"
                },
                "models": {
                    "description": "Cache de modelos de ML/IA",
                    "max_size": "1GB",
                    "max_age": 604800,  # 7 dias
                    "compression": "none"
                },
                "images": {
                    "description": "Cache de imagens",
                    "max_size": "500MB",
                    "max_age": 172800,  # 2 dias
                    "compression": "none"
                },
                "audio": {
                    "description": "Cache de áudio",
                    "max_size": "200MB",
                    "max_age": 259200,  # 3 dias
                    "compression": "mp3"
                },
                "temp": {
                    "description": "Cache temporário",
                    "max_size": "100MB",
                    "max_age": 3600,  # 1 hora
                    "compression": "none"
                }
            }
        }
        
        with open(CACHE_INDEX_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache_index, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Índice de cache criado: {CACHE_INDEX_FILE}")
    
    @staticmethod
    def _create_cache_stats():
        """Cria estatísticas de cache iniciais"""
        cache_stats = {
            "version": "1.0.0",
            "created_at": datetime.now().isoformat(),
            "total_entries": 0,
            "total_size_bytes": 0,
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "by_category": {
                "web": {"entries": 0, "size_bytes": 0, "hits": 0, "misses": 0},
                "api": {"entries": 0, "size_bytes": 0, "hits": 0, "misses": 0},
                "models": {"entries": 0, "size_bytes": 0, "hits": 0, "misses": 0},
                "images": {"entries": 0, "size_bytes": 0, "hits": 0, "misses": 0},
                "audio": {"entries": 0, "size_bytes": 0, "hits": 0, "misses": 0},
                "temp": {"entries": 0, "size_bytes": 0, "hits": 0, "misses": 0}
            },
            "daily_stats": {},
            "performance": {
                "avg_hit_time_ms": 0,
                "avg_miss_time_ms": 0,
                "hit_rate": 0.0
            }
        }
        
        with open(CACHE_STATS_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache_stats, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Estatísticas de cache criadas: {CACHE_STATS_FILE}")

class CacheManager:
    """
    Gerenciador de arquivos de cache
    """
    
    @staticmethod
    def get_cache_path(category: str, filename: str) -> str:
        """
        Obtém caminho completo para arquivo de cache
        
        Args:
            category: Categoria do cache
            filename: Nome do arquivo
            
        Returns:
            Caminho completo
        """
        if category not in CACHE_SUBDIRS:
            category = 'temp'
        
        return os.path.join(CACHE_DIR, category, filename)
    
    @staticmethod
    def save_to_cache(category: str, key: str, data: Any, 
                     serializer: str = 'pickle') -> str:
        """
        Salva dados no cache
        
        Args:
            category: Categoria do cache
            key: Chave do cache
            data: Dados a serem salvos
            serializer: 'pickle' ou 'json'
            
        Returns:
            Caminho do arquivo salvo
        """
        filename = f"{key}.{serializer}"
        filepath = CacheManager.get_cache_path(category, filename)
        
        try:
            if serializer == 'json':
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            elif serializer == 'pickle':
                with open(filepath, 'wb') as f:
                    pickle.dump(data, f)
            else:
                raise ValueError(f"Serializador não suportado: {serializer}")
            
            # Atualizar índice
            CacheManager._update_cache_index(category, key, filepath)
            
            logger.debug(f"Dados salvos no cache: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Erro ao salvar no cache: {e}")
            raise
    
    @staticmethod
    def load_from_cache(category: str, key: str, 
                       serializer: str = 'pickle') -> Optional[Any]:
        """
        Carrega dados do cache
        
        Args:
            category: Categoria do cache
            key: Chave do cache
            serializer: 'pickle' ou 'json'
            
        Returns:
            Dados carregados ou None
        """
        filename = f"{key}.{serializer}"
        filepath = CacheManager.get_cache_path(category, filename)
        
        if not os.path.exists(filepath):
            return None
        
        try:
            if serializer == 'json':
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            elif serializer == 'pickle':
                with open(filepath, 'rb') as f:
                    return pickle.load(f)
            else:
                raise ValueError(f"Serializador não suportado: {serializer}")
                
        except Exception as e:
            logger.error(f"Erro ao carregar do cache: {e}")
            return None
    
    @staticmethod
    def delete_from_cache(category: str, key: str) -> bool:
        """
        Remove dados do cache
        
        Args:
            category: Categoria do cache
            key: Chave do cache
            
        Returns:
            True se removido
        """
        # Tentar ambos os serializers
        for serializer in ['pickle', 'json']:
            filename = f"{key}.{serializer}"
            filepath = CacheManager.get_cache_path(category, filename)
            
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                    CacheManager._remove_from_cache_index(category, key)
                    logger.debug(f"Cache removido: {filepath}")
                    return True
                except Exception as e:
                    logger.error(f"Erro ao remover cache: {e}")
        
        return False
    
    @staticmethod
    def clear_category(category: str) -> int:
        """
        Limpa todos os arquivos de uma categoria
        
        Args:
            category: Categoria a ser limpa
            
        Returns:
            Número de arquivos removidos
        """
        if category not in CACHE_SUBDIRS:
            return 0
        
        category_dir = os.path.join(CACHE_DIR, category)
        removed_count = 0
        
        for filename in os.listdir(category_dir):
            if filename not in ['.gitkeep', '__init__.py']:
                try:
                    os.remove(os.path.join(category_dir, filename))
                    removed_count += 1
                except Exception as e:
                    logger.error(f"Erro ao remover {filename}: {e}")
        
        CacheManager._clear_category_index(category)
        logger.info(f"Cache da categoria '{category}' limpo: {removed_count} arquivos")
        
        return removed_count
    
    @staticmethod
    def clear_all_cache() -> Dict[str, int]:
        """
        Limpa todo o cache
        
        Returns:
            Dicionário com contagem por categoria
        """
        results = {}
        
        for category in CACHE_SUBDIRS:
            results[category] = CacheManager.clear_category(category)
        
        logger.info("Todo o cache foi limpo")
        return results
    
    @staticmethod
    def get_cache_info() -> Dict[str, Any]:
        """
        Obtém informações sobre o cache
        
        Returns:
            Dicionário com informações
        """
        info = {
            "cache_dir": CACHE_DIR,
            "categories": {},
            "total_size": 0,
            "total_files": 0
        }
        
        for category in CACHE_SUBDIRS:
            category_dir = os.path.join(CACHE_DIR, category)
            category_info = {
                "path": category_dir,
                "files": [],
                "file_count": 0,
                "total_size": 0
            }
            
            if os.path.exists(category_dir):
                for filename in os.listdir(category_dir):
                    if filename not in ['.gitkeep', '__init__.py']:
                        filepath = os.path.join(category_dir, filename)
                        if os.path.isfile(filepath):
                            category_info["files"].append({
                                "name": filename,
                                "size": os.path.getsize(filepath),
                                "modified": datetime.fromtimestamp(
                                    os.path.getmtime(filepath)
                                ).isoformat()
                            })
                            category_info["file_count"] += 1
                            category_info["total_size"] += os.path.getsize(filepath)
                
                info["total_files"] += category_info["file_count"]
                info["total_size"] += category_info["total_size"]
            
            info["categories"][category] = category_info
        
        return info
    
    @staticmethod
    def _update_cache_index(category: str, key: str, filepath: str):
        """Atualiza índice de cache"""
        try:
            if os.path.exists(CACHE_INDEX_FILE):
                with open(CACHE_INDEX_FILE, 'r', encoding='utf-8') as f:
                    index = json.load(f)
            else:
                index = {"entries": {}}
            
            if "entries" not in index:
                index["entries"] = {}
            
            if category not in index["entries"]:
                index["entries"][category] = {}
            
            index["entries"][category][key] = {
                "filepath": filepath,
                "created": datetime.now().isoformat(),
                "size": os.path.getsize(filepath) if os.path.exists(filepath) else 0
            }
            
            with open(CACHE_INDEX_FILE, 'w', encoding='utf-8') as f:
                json.dump(index, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Erro ao atualizar índice de cache: {e}")
    
    @staticmethod
    def _remove_from_cache_index(category: str, key: str):
        """Remove entrada do índice de cache"""
        try:
            if os.path.exists(CACHE_INDEX_FILE):
                with open(CACHE_INDEX_FILE, 'r', encoding='utf-8') as f:
                    index = json.load(f)
                
                if "entries" in index and category in index["entries"]:
                    if key in index["entries"][category]:
                        del index["entries"][category][key]
                
                with open(CACHE_INDEX_FILE, 'w', encoding='utf-8') as f:
                    json.dump(index, f, indent=2, ensure_ascii=False)
                    
        except Exception as e:
            logger.error(f"Erro ao remover do índice de cache: {e}")
    
    @staticmethod
    def _clear_category_index(category: str):
        """Limpa categoria do índice"""
        try:
            if os.path.exists(CACHE_INDEX_FILE):
                with open(CACHE_INDEX_FILE, 'r', encoding='utf-8') as f:
                    index = json.load(f)
                
                if "entries" in index and category in index["entries"]:
                    index["entries"][category] = {}
                
                with open(CACHE_INDEX_FILE, 'w', encoding='utf-8') as f:
                    json.dump(index, f, indent=2, ensure_ascii=False)
                    
        except Exception as e:
            logger.error(f"Erro ao limpar índice de categoria: {e}")

# Inicializar sistema de cache ao importar
CacheInitializer.initialize_cache_system()

# Exportações
__all__ = [
    'CacheManager',
    'CacheInitializer',
    'CACHE_DIR',
    'CACHE_SUBDIRS'
]

logger.info("Módulo de cache carregado")