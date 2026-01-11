"""
Utilitários de Segurança
Criptografia, hashing, tokens e proteção de dados
"""

import os
import hashlib
import hmac
import base64
import secrets
import json
from typing import Optional, Union, Dict, Any
from datetime import datetime, timedelta
import logging
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
import bcrypt
import jwt

logger = logging.getLogger(__name__)

class SecurityManager:
    """
    Gerenciador central de segurança
    """
    
    def __init__(self, secret_key: str = None):
        """
        Inicializa o gerenciador de segurança
        
        Args:
            secret_key: Chave secreta para operações de criptografia
        """
        self.secret_key = secret_key or os.environ.get('SECRET_KEY', secrets.token_hex(32))
        self.fernet = Fernet(self._generate_fernet_key())
        
        logger.info("SecurityManager inicializado")
    
    def _generate_fernet_key(self) -> bytes:
        """Gera chave Fernet a partir da secret_key"""
        salt = b'security_salt'
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(self.secret_key.encode()))
    
    def encrypt_data(self, data: Union[str, bytes, Dict, List]) -> str:
        """
        Criptografa dados
        
        Args:
            data: Dados a serem criptografados
            
        Returns:
            Dados criptografados em base64
        """
        if isinstance(data, (dict, list)):
            data = json.dumps(data).encode()
        elif isinstance(data, str):
            data = data.encode()
        
        encrypted = self.fernet.encrypt(data)
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt_data(self, encrypted_data: str) -> Union[str, Dict, List]:
        """
        Descriptografa dados
        
        Args:
            encrypted_data: Dados criptografados em base64
            
        Returns:
            Dados originais
        """
        try:
            encrypted = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = self.fernet.decrypt(encrypted)
            
            # Tenta decodificar como JSON
            try:
                return json.loads(decrypted.decode())
            except json.JSONDecodeError:
                return decrypted.decode()
                
        except Exception as e:
            logger.error(f"Erro ao descriptografar dados: {e}")
            raise ValueError("Dados criptografados inválidos")
    
    def hash_password(self, password: str) -> str:
        """
        Gera hash seguro de senha usando bcrypt
        
        Args:
            password: Senha em texto claro
            
        Returns:
            Hash da senha
        """
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode(), salt)
        return hashed.decode()
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """
        Verifica se senha corresponde ao hash
        
        Args:
            password: Senha em texto claro
            hashed_password: Hash da senha
            
        Returns:
            True se senha corresponde
        """
        try:
            return bcrypt.checkpw(password.encode(), hashed_password.encode())
        except Exception as e:
            logger.error(f"Erro ao verificar senha: {e}")
            return False
    
    def generate_token(self, data: Dict[str, Any], expires_in: int = 3600) -> str:
        """
        Gera token JWT
        
        Args:
            data: Dados a serem incluídos no token
            expires_in: Tempo de expiração em segundos
            
        Returns:
            Token JWT
        """
        payload = data.copy()
        payload.update({
            'exp': datetime.utcnow() + timedelta(seconds=expires_in),
            'iat': datetime.utcnow(),
            'iss': 'r2-assistant'
        })
        
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verifica e decodifica token JWT
        
        Args:
            token: Token JWT
            
        Returns:
            Dados do token ou None se inválido
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token expirado")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Token inválido: {e}")
            return None
    
    def generate_hmac(self, data: Union[str, bytes], key: str = None) -> str:
        """
        Gera HMAC para verificação de integridade
        
        Args:
            data: Dados a serem assinados
            key: Chave para HMAC (None para usar secret_key)
            
        Returns:
            HMAC em hex
        """
        key = key or self.secret_key
        
        if isinstance(data, str):
            data = data.encode()
        
        h = hmac.new(key.encode(), data, hashlib.sha256)
        return h.hexdigest()
    
    def verify_hmac(self, data: Union[str, bytes], signature: str, 
                   key: str = None) -> bool:
        """
        Verifica HMAC
        
        Args:
            data: Dados originais
            signature: HMAC a ser verificado
            key: Chave para HMAC
            
        Returns:
            True se HMAC é válido
        """
        expected = self.generate_hmac(data, key)
        return hmac.compare_digest(expected, signature)

# Funções utilitárias estáticas
def encrypt_data(data: Union[str, bytes, Dict, List], 
                secret_key: str = None) -> str:
    """
    Criptografa dados
    
    Args:
        data: Dados a serem criptografados
        secret_key: Chave secreta
        
    Returns:
        Dados criptografados
    """
    manager = SecurityManager(secret_key)
    return manager.encrypt_data(data)

def decrypt_data(encrypted_data: str, secret_key: str = None) -> Union[str, Dict, List]:
    """
    Descriptografa dados
    
    Args:
        encrypted_data: Dados criptografados
        secret_key: Chave secreta
        
    Returns:
        Dados originais
    """
    manager = SecurityManager(secret_key)
    return manager.decrypt_data(encrypted_data)

def hash_password(password: str) -> str:
    """
    Gera hash seguro de senha
    
    Args:
        password: Senha em texto claro
        
    Returns:
        Hash da senha
    """
    manager = SecurityManager()
    return manager.hash_password(password)

def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verifica se senha corresponde ao hash
    
    Args:
        password: Senha em texto claro
        hashed_password: Hash da senha
        
    Returns:
        True se senha corresponde
    """
    manager = SecurityManager()
    return manager.verify_password(password, hashed_password)

def generate_token(data: Dict[str, Any], secret_key: str = None, 
                  expires_in: int = 3600) -> str:
    """
    Gera token JWT
    
    Args:
        data: Dados a serem incluídos
        secret_key: Chave secreta
        expires_in: Tempo de expiração em segundos
        
    Returns:
        Token JWT
    """
    manager = SecurityManager(secret_key)
    return manager.generate_token(data, expires_in)

def verify_token(token: str, secret_key: str = None) -> Optional[Dict[str, Any]]:
    """
    Verifica token JWT
    
    Args:
        token: Token JWT
        secret_key: Chave secreta
        
    Returns:
        Dados do token ou None
    """
    manager = SecurityManager(secret_key)
    return manager.verify_token(token)

def sanitize_filename(filename: str) -> str:
    """
    Sanitiza nome de arquivo para segurança
    
    Args:
        filename: Nome original do arquivo
        
    Returns:
        Nome sanitizado
    """
    # Remove caminhos
    filename = os.path.basename(filename)
    
    # Remove caracteres perigosos
    dangerous = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    for char in dangerous:
        filename = filename.replace(char, '_')
    
    # Limita tamanho
    max_length = 255
    if len(filename) > max_length:
        name, ext = os.path.splitext(filename)
        filename = name[:max_length - len(ext)] + ext
    
    return filename

def check_file_integrity(filepath: str, expected_hash: str, 
                        algorithm: str = 'sha256') -> bool:
    """
    Verifica integridade de arquivo via hash
    
    Args:
        filepath: Caminho do arquivo
        expected_hash: Hash esperado
        algorithm: Algoritmo de hash
        
    Returns:
        True se integridade está OK
    """
    import hashlib
    
    hash_func = hashlib.new(algorithm)
    
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            hash_func.update(chunk)
    
    actual_hash = hash_func.hexdigest()
    return hmac.compare_digest(actual_hash, expected_hash)

def generate_secure_random(length: int = 32) -> str:
    """
    Gera string aleatória segura
    
    Args:
        length: Comprimento da string
        
    Returns:
        String aleatória em hex
    """
    return secrets.token_hex(length)

class SecurityMiddleware:
    """
    Middleware para adicionar headers de segurança HTTP
    """
    
    def __init__(self, app):
        self.app = app
    
    def __call__(self, environ, start_response):
        def security_headers(status, headers, exc_info=None):
            # Headers de segurança
            security_headers = [
                ('X-Content-Type-Options', 'nosniff'),
                ('X-Frame-Options', 'DENY'),
                ('X-XSS-Protection', '1; mode=block'),
                ('Strict-Transport-Security', 'max-age=31536000; includeSubDomains'),
                ('Content-Security-Policy', "default-src 'self'"),
                ('Referrer-Policy', 'strict-origin-when-cross-origin'),
                ('Permissions-Policy', 'geolocation=(), microphone=()')
            ]
            
            headers.extend(security_headers)
            return start_response(status, headers, exc_info)
        
        return self.app(environ, security_headers)