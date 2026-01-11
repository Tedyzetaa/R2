"""
Utilitários do R2 Assistant
Coleção de ferramentas e helpers para desenvolvimento
"""

__version__ = "1.0.0"
__author__ = "R2 Assistant Team"

# Importações principais
from .file_utils import (
    FileManager,
    BackupManager,
    find_files,
    read_json,
    write_json,
    read_yaml,
    write_yaml,
    safe_delete,
    calculate_hash,
    compress_file,
    extract_file
)

from .validation import (
    Validator,
    validate_email,
    validate_url,
    validate_ip,
    validate_phone,
    validate_cpf,
    validate_cnpj,
    validate_json,
    validate_schema,
    sanitize_input
)

from .cache import (
    Cache,
    LRUCache,
    TTLCache,
    RedisCache,
    CacheManager,
    cache_decorator,
    async_cache_decorator
)

from .security import (
    SecurityManager,
    encrypt_data,
    decrypt_data,
    hash_password,
    verify_password,
    generate_token,
    verify_token,
    sanitize_filename,
    check_file_integrity,
    generate_secure_random,
    SecurityMiddleware
)

from .helpers import (
    retry,
    async_retry,
    timeout,
    async_timeout,
    rate_limit,
    async_rate_limit,
    Singleton,
    Observable,
    EventEmitter,
    ProgressBar,
    Spinner,
    TablePrinter,
    ColorFormatter,
    format_bytes,
    format_time,
    format_number,
    generate_id,
    chunk_list,
    flatten_dict,
    deep_merge,
    get_nested_value,
    set_nested_value,
    benchmark,
    async_benchmark
)

# Exportações principais
__all__ = [
    # File Utils
    'FileManager',
    'BackupManager',
    'find_files',
    'read_json',
    'write_json',
    'read_yaml',
    'write_yaml',
    'safe_delete',
    'calculate_hash',
    'compress_file',
    'extract_file',
    
    # Validation
    'Validator',
    'validate_email',
    'validate_url',
    'validate_ip',
    'validate_phone',
    'validate_cpf',
    'validate_cnpj',
    'validate_json',
    'validate_schema',
    'sanitize_input',
    
    # Cache
    'Cache',
    'LRUCache',
    'TTLCache',
    'RedisCache',
    'CacheManager',
    'cache_decorator',
    'async_cache_decorator',
    
    # Security
    'SecurityManager',
    'encrypt_data',
    'decrypt_data',
    'hash_password',
    'verify_password',
    'generate_token',
    'verify_token',
    'sanitize_filename',
    'check_file_integrity',
    'generate_secure_random',
    'SecurityMiddleware',
    
    # Helpers
    'retry',
    'async_retry',
    'timeout',
    'async_timeout',
    'rate_limit',
    'async_rate_limit',
    'Singleton',
    'Observable',
    'EventEmitter',
    'ProgressBar',
    'Spinner',
    'TablePrinter',
    'ColorFormatter',
    'format_bytes',
    'format_time',
    'format_number',
    'generate_id',
    'chunk_list',
    'flatten_dict',
    'deep_merge',
    'get_nested_value',
    'set_nested_value',
    'benchmark',
    'async_benchmark'
]

# Inicialização do logger
import logging
logger = logging.getLogger(__name__)
logger.info(f"Utils v{__version__} carregado")