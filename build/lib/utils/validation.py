"""
Utilitários de Validação e Sanitização
Validação de dados, sanitização e verificação de integridade
"""

import re
import json
import datetime
from typing import Any, Dict, List, Optional, Union, Callable, Pattern
import ipaddress
import phonenumbers
from email.utils import parseaddr
import logging
from functools import wraps
import inspect

logger = logging.getLogger(__name__)

class Validator:
    """
    Validator de dados com suporte a schemas
    """
    
    def __init__(self):
        self.rules: Dict[str, Callable] = {}
        self.custom_validators: Dict[str, Callable] = {}
        
        # Registrar validadores padrão
        self._register_default_rules()
    
    def _register_default_rules(self):
        """Registra regras de validação padrão"""
        self.rules = {
            'required': self._validate_required,
            'string': self._validate_string,
            'integer': self._validate_integer,
            'float': self._validate_float,
            'boolean': self._validate_boolean,
            'email': self._validate_email,
            'url': self._validate_url,
            'ip': self._validate_ip,
            'phone': self._validate_phone,
            'date': self._validate_date,
            'datetime': self._validate_datetime,
            'regex': self._validate_regex,
            'in': self._validate_in,
            'min': self._validate_min,
            'max': self._validate_max,
            'min_length': self._validate_min_length,
            'max_length': self._validate_max_length,
            'between': self._validate_between,
            'uuid': self._validate_uuid,
            'json': self._validate_json
        }
    
    def validate(self, data: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Valida dados contra um schema
        
        Args:
            data: Dados a serem validados
            schema: Schema de validação
            
        Returns:
            Dicionário com erros por campo
        """
        errors = {}
        
        for field, rules in schema.items():
            field_errors = []
            value = data.get(field)
            
            # Verificar regras
            for rule_name, rule_value in rules.items():
                if rule_name in self.rules:
                    try:
                        if not self.rules[rule_name](value, rule_value, field):
                            field_errors.append(self._format_error(rule_name, rule_value, field))
                    except Exception as e:
                        field_errors.append(f"Erro na validação {rule_name}: {str(e)}")
                elif rule_name in self.custom_validators:
                    try:
                        if not self.custom_validators[rule_name](value, rule_value, field):
                            field_errors.append(self._format_error(rule_name, rule_value, field))
                    except Exception as e:
                        field_errors.append(f"Erro no validador customizado {rule_name}: {str(e)}")
                else:
                    field_errors.append(f"Regra de validação desconhecida: {rule_name}")
            
            if field_errors:
                errors[field] = field_errors
        
        return errors
    
    def register_validator(self, name: str, validator: Callable):
        """
        Registra um validador customizado
        
        Args:
            name: Nome do validador
            validator: Função de validação
        """
        self.custom_validators[name] = validator
        logger.info(f"Validador customizado registrado: {name}")
    
    # Validadores padrão
    def _validate_required(self, value: Any, rule_value: Any, field: str) -> bool:
        """Valida se campo é obrigatório"""
        if rule_value:
            return value is not None and value != ""
        return True
    
    def _validate_string(self, value: Any, rule_value: Any, field: str) -> bool:
        """Valida se é string"""
        if value is None:
            return True
        return isinstance(value, str)
    
    def _validate_integer(self, value: Any, rule_value: Any, field: str) -> bool:
        """Valida se é inteiro"""
        if value is None:
            return True
        return isinstance(value, int) and not isinstance(value, bool)
    
    def _validate_float(self, value: Any, rule_value: Any, field: str) -> bool:
        """Valida se é float"""
        if value is None:
            return True
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    
    def _validate_boolean(self, value: Any, rule_value: Any, field: str) -> bool:
        """Valida se é booleano"""
        if value is None:
            return True
        return isinstance(value, bool)
    
    def _validate_email(self, value: Any, rule_value: Any, field: str) -> bool:
        """Valida formato de email"""
        if value is None:
            return True
        if not isinstance(value, str):
            return False
        
        # Validação simples
        if '@' not in value:
            return False
        
        # Validação mais rigorosa
        name, addr = parseaddr(value)
        return '@' in addr and '.' in addr.split('@')[1]
    
    def _validate_url(self, value: Any, rule_value: Any, field: str) -> bool:
        """Valida formato de URL"""
        if value is None:
            return True
        if not isinstance(value, str):
            return False
        
        # Padrão de URL
        url_pattern = re.compile(
            r'^(https?://)?'  # Protocolo
            r'([a-zA-Z0-9.-]+)'  # Domínio
            r'(\.[a-zA-Z]{2,})'  # TLD
            r'(:\d+)?'  # Porta
            r'(/.*)?$'  # Caminho
        )
        
        return bool(url_pattern.match(value))
    
    def _validate_ip(self, value: Any, rule_value: Any, field: str) -> bool:
        """Valida endereço IP"""
        if value is None:
            return True
        if not isinstance(value, str):
            return False
        
        try:
            ipaddress.ip_address(value)
            return True
        except ValueError:
            return False
    
    def _validate_phone(self, value: Any, rule_value: Any, field: str) -> bool:
        """Valida número de telefone"""
        if value is None:
            return True
        if not isinstance(value, str):
            return False
        
        try:
            # Tenta parsear como número internacional
            phone = phonenumbers.parse(value, None)
            return phonenumbers.is_valid_number(phone)
        except phonenumbers.NumberParseException:
            # Fallback para validação simples
            phone_pattern = re.compile(r'^\+?[\d\s\-\(\)]{10,}$')
            return bool(phone_pattern.match(value))
    
    def _validate_date(self, value: Any, rule_value: Any, field: str) -> bool:
        """Valida data"""
        if value is None:
            return True
        
        if isinstance(value, datetime.date):
            return True
        
        if isinstance(value, str):
            try:
                datetime.datetime.strptime(value, '%Y-%m-%d')
                return True
            except ValueError:
                pass
        
        return False
    
    def _validate_datetime(self, value: Any, rule_value: Any, field: str) -> bool:
        """Valida data e hora"""
        if value is None:
            return True
        
        if isinstance(value, datetime.datetime):
            return True
        
        if isinstance(value, str):
            try:
                # Tenta formatos comuns
                for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', 
                           '%d/%m/%Y %H:%M:%S', '%Y-%m-%d %H:%M']:
                    try:
                        datetime.datetime.strptime(value, fmt)
                        return True
                    except ValueError:
                        continue
            except Exception:
                pass
        
        return False
    
    def _validate_regex(self, value: Any, rule_value: Any, field: str) -> bool:
        """Valida contra regex"""
        if value is None:
            return True
        if not isinstance(value, str):
            return False
        
        if isinstance(rule_value, str):
            pattern = re.compile(rule_value)
        elif isinstance(rule_value, Pattern):
            pattern = rule_value
        else:
            return False
        
        return bool(pattern.match(value))
    
    def _validate_in(self, value: Any, rule_value: Any, field: str) -> bool:
        """Valida se valor está em lista"""
        if value is None:
            return True
        return value in rule_value
    
    def _validate_min(self, value: Any, rule_value: Any, field: str) -> bool:
        """Valida valor mínimo"""
        if value is None:
            return True
        try:
            return float(value) >= float(rule_value)
        except (ValueError, TypeError):
            return False
    
    def _validate_max(self, value: Any, rule_value: Any, field: str) -> bool:
        """Valida valor máximo"""
        if value is None:
            return True
        try:
            return float(value) <= float(rule_value)
        except (ValueError, TypeError):
            return False
    
    def _validate_min_length(self, value: Any, rule_value: Any, field: str) -> bool:
        """Valida comprimento mínimo"""
        if value is None:
            return True
        try:
            return len(str(value)) >= int(rule_value)
        except (ValueError, TypeError):
            return False
    
    def _validate_max_length(self, value: Any, rule_value: Any, field: str) -> bool:
        """Valida comprimento máximo"""
        if value is None:
            return True
        try:
            return len(str(value)) <= int(rule_value)
        except (ValueError, TypeError):
            return False
    
    def _validate_between(self, value: Any, rule_value: Any, field: str) -> bool:
        """Valida se valor está entre min e max"""
        if value is None:
            return True
        try:
            num_value = float(value)
            return rule_value[0] <= num_value <= rule_value[1]
        except (ValueError, TypeError, IndexError):
            return False
    
    def _validate_uuid(self, value: Any, rule_value: Any, field: str) -> bool:
        """Valida formato UUID"""
        if value is None:
            return True
        if not isinstance(value, str):
            return False
        
        uuid_pattern = re.compile(
            r'^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$',
            re.I
        )
        return bool(uuid_pattern.match(value))
    
    def _validate_json(self, value: Any, rule_value: Any, field: str) -> bool:
        """Valida se é JSON válido"""
        if value is None:
            return True
        
        if isinstance(value, (dict, list)):
            return True
        
        if isinstance(value, str):
            try:
                json.loads(value)
                return True
            except json.JSONDecodeError:
                return False
        
        return False
    
    def _format_error(self, rule_name: str, rule_value: Any, field: str) -> str:
        """Formata mensagem de erro"""
        error_messages = {
            'required': f"O campo '{field}' é obrigatório",
            'string': f"O campo '{field}' deve ser uma string",
            'integer': f"O campo '{field}' deve ser um número inteiro",
            'float': f"O campo '{field}' deve ser um número decimal",
            'boolean': f"O campo '{field}' deve ser verdadeiro ou falso",
            'email': f"O campo '{field}' deve ser um email válido",
            'url': f"O campo '{field}' deve ser uma URL válida",
            'ip': f"O campo '{field}' deve ser um endereço IP válido",
            'phone': f"O campo '{field}' deve ser um número de telefone válido",
            'date': f"O campo '{field}' deve ser uma data válida",
            'datetime': f"O campo '{field}' deve ser uma data e hora válidas",
            'regex': f"O campo '{field}' não corresponde ao padrão esperado",
            'in': f"O campo '{field}' deve ser um dos valores: {rule_value}",
            'min': f"O campo '{field}' deve ser no mínimo {rule_value}",
            'max': f"O campo '{field}' deve ser no máximo {rule_value}",
            'min_length': f"O campo '{field}' deve ter no mínimo {rule_value} caracteres",
            'max_length': f"O campo '{field}' deve ter no máximo {rule_value} caracteres",
            'between': f"O campo '{field}' deve estar entre {rule_value[0]} e {rule_value[1]}",
            'uuid': f"O campo '{field}' deve ser um UUID válido",
            'json': f"O campo '{field}' deve ser um JSON válido"
        }
        
        return error_messages.get(rule_name, f"Erro na validação do campo '{field}'")

# Funções utilitárias estáticas
def validate_email(email: str) -> bool:
    """
    Valida formato de email
    
    Args:
        email: Email a ser validado
        
    Returns:
        True se email é válido
    """
    if not email or not isinstance(email, str):
        return False
    
    # Padrão de email
    pattern = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    
    if not pattern.match(email):
        return False
    
    # Verificação adicional
    name, addr = parseaddr(email)
    return '@' in addr and '.' in addr.split('@')[1]

def validate_url(url: str, require_protocol: bool = False) -> bool:
    """
    Valida formato de URL
    
    Args:
        url: URL a ser validada
        require_protocol: Se protocolo é obrigatório
        
    Returns:
        True se URL é válida
    """
    if not url or not isinstance(url, str):
        return False
    
    pattern = re.compile(
        r'^' +
        (r'https?://' if require_protocol else r'(https?://)?') +
        r'([a-zA-Z0-9.-]+)' +
        r'(\.[a-zA-Z]{2,})' +
        r'(:\d+)?' +
        r'(/.*)?$'
    )
    
    return bool(pattern.match(url))

def validate_ip(ip: str, ipv6: bool = True) -> bool:
    """
    Valida endereço IP
    
    Args:
        ip: Endereço IP a ser validado
        ipv6: Se deve validar IPv6 também
        
    Returns:
        True se IP é válido
    """
    if not ip or not isinstance(ip, str):
        return False
    
    try:
        addr = ipaddress.ip_address(ip)
        
        if not ipv6 and addr.version == 6:
            return False
        
        return True
    except ValueError:
        return False

def validate_phone(phone: str, country: str = None) -> bool:
    """
    Valida número de telefone
    
    Args:
        phone: Número de telefone
        country: Código do país (ex: 'BR', 'US')
        
    Returns:
        True se telefone é válido
    """
    if not phone or not isinstance(phone, str):
        return False
    
    try:
        phone_obj = phonenumbers.parse(phone, country)
        return phonenumbers.is_valid_number(phone_obj)
    except phonenumbers.NumberParseException:
        # Validação simplificada
        pattern = re.compile(r'^\+?[\d\s\-\(\)]{10,}$')
        return bool(pattern.match(phone))

def validate_cpf(cpf: str) -> bool:
    """
    Valida CPF brasileiro
    
    Args:
        cpf: CPF a ser validado
        
    Returns:
        True se CPF é válido
    """
    if not cpf or not isinstance(cpf, str):
        return False
    
    # Remove caracteres não numéricos
    cpf = re.sub(r'\D', '', cpf)
    
    # Verifica tamanho
    if len(cpf) != 11:
        return False
    
    # Verifica se todos os dígitos são iguais
    if cpf == cpf[0] * 11:
        return False
    
    # Calcula primeiro dígito verificador
    soma = 0
    for i in range(9):
        soma += int(cpf[i]) * (10 - i)
    
    resto = soma % 11
    digito1 = 0 if resto < 2 else 11 - resto
    
    if digito1 != int(cpf[9]):
        return False
    
    # Calcula segundo dígito verificador
    soma = 0
    for i in range(10):
        soma += int(cpf[i]) * (11 - i)
    
    resto = soma % 11
    digito2 = 0 if resto < 2 else 11 - resto
    
    return digito2 == int(cpf[10])

def validate_cnpj(cnpj: str) -> bool:
    """
    Valida CNPJ brasileiro
    
    Args:
        cnpj: CNPJ a ser validado
        
    Returns:
        True se CNPJ é válido
    """
    if not cnpj or not isinstance(cnpj, str):
        return False
    
    # Remove caracteres não numéricos
    cnpj = re.sub(r'\D', '', cnpj)
    
    # Verifica tamanho
    if len(cnpj) != 14:
        return False
    
    # Verifica se todos os dígitos são iguais
    if cnpj == cnpj[0] * 14:
        return False
    
    # Validação do primeiro dígito
    peso = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma = 0
    
    for i in range(12):
        soma += int(cnpj[i]) * peso[i]
    
    resto = soma % 11
    digito1 = 0 if resto < 2 else 11 - resto
    
    if digito1 != int(cnpj[12]):
        return False
    
    # Validação do segundo dígito
    peso = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma = 0
    
    for i in range(13):
        soma += int(cnpj[i]) * peso[i]
    
    resto = soma % 11
    digito2 = 0 if resto < 2 else 11 - resto
    
    return digito2 == int(cnpj[13])

def validate_json(json_str: str) -> bool:
    """
    Valida se string é JSON válido
    
    Args:
        json_str: String JSON
        
    Returns:
        True se JSON é válido
    """
    if not json_str or not isinstance(json_str, str):
        return False
    
    try:
        json.loads(json_str)
        return True
    except json.JSONDecodeError:
        return False

def validate_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, List[str]]:
    """
    Valida dados contra schema usando Validator
    
    Args:
        data: Dados a serem validados
        schema: Schema de validação
        
    Returns:
        Dicionário com erros por campo
    """
    validator = Validator()
    return validator.validate(data, schema)

def sanitize_input(input_str: str, allowed_chars: str = None, 
                  max_length: int = None) -> str:
    """
    Sanitiza entrada de usuário
    
    Args:
        input_str: String de entrada
        allowed_chars: Caracteres permitidos (regex pattern)
        max_length: Comprimento máximo
        
    Returns:
        String sanitizada
    """
    if not input_str or not isinstance(input_str, str):
        return ""
    
    # Remove espaços extras
    sanitized = input_str.strip()
    
    # Aplica comprimento máximo
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    # Filtra caracteres permitidos
    if allowed_chars:
        pattern = re.compile(f'[^{re.escape(allowed_chars)}]')
        sanitized = pattern.sub('', sanitized)
    
    return sanitized

# Decorator para validação automática
def validate_args(schema: Dict[str, Any]):
    """
    Decorator para validar argumentos de função
    
    Args:
        schema: Schema de validação para argumentos
        
    Returns:
        Função decorada
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Combinar args e kwargs
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            # Validar
            validator = Validator()
            errors = validator.validate(bound_args.arguments, schema)
            
            if errors:
                raise ValueError(f"Erros de validação: {errors}")
            
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator