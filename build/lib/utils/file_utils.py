"""
Utilitários de Manipulação de Arquivos
Operações seguras e eficientes com arquivos
"""

import os
import json
import yaml
import hashlib
import shutil
import zipfile
import tarfile
import tempfile
import pickle
import csv
import pathlib
from typing import Dict, List, Optional, Any, Union, BinaryIO, Iterator
from datetime import datetime
from contextlib import contextmanager
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import gzip
import lzma
import bz2
import fnmatch

logger = logging.getLogger(__name__)

class FileManager:
    """
    Gerenciador avançado de arquivos com operações seguras
    """
    
    def __init__(self, base_path: str = ".", create_dirs: bool = True):
        """
        Inicializa o gerenciador de arquivos
        
        Args:
            base_path: Diretório base para operações
            create_dirs: Criar diretórios automaticamente
        """
        self.base_path = pathlib.Path(base_path).resolve()
        self.create_dirs = create_dirs
        
        if create_dirs:
            self.base_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"FileManager inicializado em: {self.base_path}")
    
    def read_text(self, filepath: str, encoding: str = 'utf-8') -> str:
        """
        Lê um arquivo de texto de forma segura
        
        Args:
            filepath: Caminho do arquivo (relativo ao base_path)
            encoding: Codificação do arquivo
            
        Returns:
            Conteúdo do arquivo como string
        """
        path = self._resolve_path(filepath)
        
        try:
            with open(path, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            # Tentar outras codificações comuns
            for enc in ['latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    with open(path, 'r', encoding=enc) as f:
                        return f.read()
                except UnicodeDecodeError:
                    continue
            raise
    
    def write_text(self, filepath: str, content: str, encoding: str = 'utf-8', 
                  backup: bool = False) -> bool:
        """
        Escreve em um arquivo de texto de forma segura
        
        Args:
            filepath: Caminho do arquivo
            content: Conteúdo a ser escrito
            encoding: Codificação do arquivo
            backup: Criar backup antes de sobrescrever
            
        Returns:
            True se bem sucedido
        """
        path = self._resolve_path(filepath)
        
        if backup and path.exists():
            backup_path = path.with_suffix(f'{path.suffix}.bak')
            shutil.copy2(path, backup_path)
        
        # Criar diretórios se necessário
        if self.create_dirs:
            path.parent.mkdir(parents=True, exist_ok=True)
        
        # Escrever em arquivo temporário primeiro
        with tempfile.NamedTemporaryFile(mode='w', encoding=encoding, 
                                        delete=False, dir=path.parent) as tmp:
            tmp.write(content)
            tmp_path = pathlib.Path(tmp.name)
        
        # Mover para localização final
        try:
            shutil.move(str(tmp_path), str(path))
            return True
        except Exception as e:
            # Limpar arquivo temporário em caso de erro
            if tmp_path.exists():
                tmp_path.unlink()
            raise e
    
    def read_json(self, filepath: str, default: Any = None) -> Any:
        """
        Lê um arquivo JSON
        
        Args:
            filepath: Caminho do arquivo
            default: Valor padrão se arquivo não existir
            
        Returns:
            Dados JSON
        """
        path = self._resolve_path(filepath)
        
        if not path.exists():
            if default is not None:
                return default
            raise FileNotFoundError(f"Arquivo não encontrado: {filepath}")
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao decodificar JSON: {filepath}")
            raise e
    
    def write_json(self, filepath: str, data: Any, indent: int = 2, 
                  sort_keys: bool = False, backup: bool = False) -> bool:
        """
        Escreve dados em formato JSON
        
        Args:
            filepath: Caminho do arquivo
            data: Dados a serem escritos
            indent: Indentação
            sort_keys: Ordenar chaves
            backup: Criar backup
            
        Returns:
            True se bem sucedido
        """
        return self.write_text(
            filepath,
            json.dumps(data, indent=indent, sort_keys=sort_keys, 
                      ensure_ascii=False, default=str),
            backup=backup
        )
    
    def read_yaml(self, filepath: str, default: Any = None) -> Any:
        """
        Lê um arquivo YAML
        
        Args:
            filepath: Caminho do arquivo
            default: Valor padrão se arquivo não existir
            
        Returns:
            Dados YAML
        """
        path = self._resolve_path(filepath)
        
        if not path.exists():
            if default is not None:
                return default
            raise FileNotFoundError(f"Arquivo não encontrado: {filepath}")
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except yaml.YAMLError as e:
            logger.error(f"Erro ao decodificar YAML: {filepath}")
            raise e
    
    def write_yaml(self, filepath: str, data: Any, default_flow_style: bool = False,
                  backup: bool = False) -> bool:
        """
        Escreve dados em formato YAML
        
        Args:
            filepath: Caminho do arquivo
            data: Dados a serem escritos
            default_flow_style: Estilo de fluxo padrão
            backup: Criar backup
            
        Returns:
            True se bem sucedido
        """
        return self.write_text(
            filepath,
            yaml.dump(data, default_flow_style=default_flow_style, 
                     allow_unicode=True, sort_keys=False),
            backup=backup
        )
    
    def read_csv(self, filepath: str, delimiter: str = ',', 
                encoding: str = 'utf-8') -> List[Dict[str, Any]]:
        """
        Lê um arquivo CSV
        
        Args:
            filepath: Caminho do arquivo
            delimiter: Delimitador
            encoding: Codificação
            
        Returns:
            Lista de dicionários com os dados
        """
        path = self._resolve_path(filepath)
        
        if not path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {filepath}")
        
        with open(path, 'r', encoding=encoding) as f:
            reader = csv.DictReader(f, delimiter=delimiter)
            return list(reader)
    
    def write_csv(self, filepath: str, data: List[Dict[str, Any]], 
                 fieldnames: Optional[List[str]] = None, 
                 delimiter: str = ',', encoding: str = 'utf-8',
                 backup: bool = False) -> bool:
        """
        Escreve dados em formato CSV
        
        Args:
            filepath: Caminho do arquivo
            data: Dados a serem escritos
            fieldnames: Nomes das colunas
            delimiter: Delimitador
            encoding: Codificação
            backup: Criar backup
            
        Returns:
            True se bem sucedido
        """
        path = self._resolve_path(filepath)
        
        if backup and path.exists():
            backup_path = path.with_suffix(f'{path.suffix}.bak')
            shutil.copy2(path, backup_path)
        
        if self.create_dirs:
            path.parent.mkdir(parents=True, exist_ok=True)
        
        if not fieldnames and data:
            fieldnames = list(data[0].keys())
        
        with tempfile.NamedTemporaryFile(mode='w', encoding=encoding,
                                        delete=False, dir=path.parent,
                                        newline='') as tmp:
            writer = csv.DictWriter(tmp, fieldnames=fieldnames, 
                                  delimiter=delimiter)
            writer.writeheader()
            writer.writerows(data)
            tmp_path = pathlib.Path(tmp.name)
        
        try:
            shutil.move(str(tmp_path), str(path))
            return True
        except Exception as e:
            if tmp_path.exists():
                tmp_path.unlink()
            raise e
    
    def find_files(self, pattern: str = "*", recursive: bool = True,
                  include_dirs: bool = False) -> List[pathlib.Path]:
        """
        Encontra arquivos com base em padrão
        
        Args:
            pattern: Padrão glob (ex: "*.py", "**/*.txt")
            recursive: Busca recursiva
            include_dirs: Incluir diretórios nos resultados
            
        Returns:
            Lista de caminhos encontrados
        """
        if recursive:
            pattern = f"**/{pattern}"
        
        files = []
        for path in self.base_path.glob(pattern):
            if include_dirs or path.is_file():
                files.append(path)
        
        return files
    
    def calculate_hash(self, filepath: str, algorithm: str = "sha256") -> str:
        """
        Calcula hash de um arquivo
        
        Args:
            filepath: Caminho do arquivo
            algorithm: Algoritmo de hash
            
        Returns:
            Hash do arquivo
        """
        path = self._resolve_path(filepath)
        
        if not path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {filepath}")
        
        hash_func = hashlib.new(algorithm)
        
        with open(path, 'rb') as f:
            # Ler em chunks para arquivos grandes
            for chunk in iter(lambda: f.read(4096), b''):
                hash_func.update(chunk)
        
        return hash_func.hexdigest()
    
    def copy_file(self, source: str, destination: str, 
                 overwrite: bool = False) -> bool:
        """
        Copia um arquivo de forma segura
        
        Args:
            source: Arquivo de origem
            destination: Arquivo de destino
            overwrite: Sobrescrever se existir
            
        Returns:
            True se bem sucedido
        """
        src = self._resolve_path(source)
        dst = self._resolve_path(destination)
        
        if not src.exists():
            raise FileNotFoundError(f"Arquivo de origem não encontrado: {source}")
        
        if dst.exists() and not overwrite:
            raise FileExistsError(f"Arquivo de destino já existe: {destination}")
        
        if self.create_dirs:
            dst.parent.mkdir(parents=True, exist_ok=True)
        
        # Usar cópia segura via arquivo temporário
        with tempfile.NamedTemporaryFile(delete=False, dir=dst.parent) as tmp:
            tmp_path = pathlib.Path(tmp.name)
        
        try:
            shutil.copy2(src, tmp_path)
            shutil.move(str(tmp_path), str(dst))
            return True
        except Exception as e:
            if tmp_path.exists():
                tmp_path.unlink()
            raise e
    
    def delete_file(self, filepath: str, secure: bool = False) -> bool:
        """
        Exclui um arquivo de forma segura
        
        Args:
            filepath: Caminho do arquivo
            secure: Sobrescrever com zeros antes de excluir
            
        Returns:
            True se bem sucedido
        """
        path = self._resolve_path(filepath)
        
        if not path.exists():
            return False
        
        if secure and path.is_file():
            # Sobrescrever com zeros antes de excluir
            with open(path, 'wb') as f:
                file_size = path.stat().st_size
                f.write(b'\x00' * file_size)
        
        try:
            path.unlink()
            return True
        except Exception as e:
            logger.error(f"Erro ao excluir arquivo {filepath}: {e}")
            return False
    
    def compress_file(self, source: str, destination: str = None,
                     algorithm: str = 'gzip') -> str:
        """
        Comprime um arquivo
        
        Args:
            source: Arquivo de origem
            destination: Arquivo de destino (opcional)
            algorithm: Algoritmo de compressão
            
        Returns:
            Caminho do arquivo comprimido
        """
        src = self._resolve_path(source)
        
        if not src.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {source}")
        
        if destination is None:
            dest = src.with_suffix(f'{src.suffix}.{algorithm}')
        else:
            dest = self._resolve_path(destination)
        
        if self.create_dirs:
            dest.parent.mkdir(parents=True, exist_ok=True)
        
        if algorithm == 'gzip':
            with open(src, 'rb') as f_in:
                with gzip.open(dest, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
        
        elif algorithm == 'bz2':
            with open(src, 'rb') as f_in:
                with bz2.open(dest, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
        
        elif algorithm == 'lzma':
            with open(src, 'rb') as f_in:
                with lzma.open(dest, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
        
        else:
            raise ValueError(f"Algoritmo não suportado: {algorithm}")
        
        return str(dest)
    
    def extract_file(self, source: str, destination: str = None) -> str:
        """
        Extrai um arquivo comprimido
        
        Args:
            source: Arquivo comprimido
            destination: Diretório de destino (opcional)
            
        Returns:
            Caminho do arquivo extraído
        """
        src = self._resolve_path(source)
        
        if not src.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {source}")
        
        # Determinar tipo de compressão pela extensão
        if src.suffix in ['.gz', '.gzip']:
            algorithm = 'gzip'
        elif src.suffix in ['.bz2', '.bzip2']:
            algorithm = 'bz2'
        elif src.suffix in ['.xz', '.lzma']:
            algorithm = 'lzma'
        else:
            # Tentar detectar pelo conteúdo
            with open(src, 'rb') as f:
                magic = f.read(6)
                if magic.startswith(b'\x1f\x8b'):
                    algorithm = 'gzip'
                elif magic.startswith(b'BZh'):
                    algorithm = 'bz2'
                elif magic.startswith(b'\xfd7zXZ'):
                    algorithm = 'lzma'
                else:
                    raise ValueError(f"Tipo de compressão não reconhecido: {source}")
        
        if destination is None:
            dest = src.with_suffix('')  # Remove extensão
        else:
            dest_dir = self._resolve_path(destination)
            if dest_dir.is_dir():
                dest = dest_dir / src.with_suffix('').name
            else:
                dest = dest_dir
        
        if self.create_dirs:
            dest.parent.mkdir(parents=True, exist_ok=True)
        
        if algorithm == 'gzip':
            with gzip.open(src, 'rb') as f_in:
                with open(dest, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
        
        elif algorithm == 'bz2':
            with bz2.open(src, 'rb') as f_in:
                with open(dest, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
        
        elif algorithm == 'lzma':
            with lzma.open(src, 'rb') as f_in:
                with open(dest, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
        
        return str(dest)
    
    def get_file_info(self, filepath: str) -> Dict[str, Any]:
        """
        Obtém informações detalhadas sobre um arquivo
        
        Args:
            filepath: Caminho do arquivo
            
        Returns:
            Dicionário com informações do arquivo
        """
        path = self._resolve_path(filepath)
        
        if not path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {filepath}")
        
        stat = path.stat()
        
        return {
            'path': str(path),
            'name': path.name,
            'stem': path.stem,
            'suffix': path.suffix,
            'parent': str(path.parent),
            'size': stat.st_size,
            'size_human': self._format_bytes(stat.st_size),
            'created': datetime.fromtimestamp(stat.st_ctime),
            'modified': datetime.fromtimestamp(stat.st_mtime),
            'accessed': datetime.fromtimestamp(stat.st_atime),
            'is_file': path.is_file(),
            'is_dir': path.is_dir(),
            'is_symlink': path.is_symlink(),
            'permissions': oct(stat.st_mode)[-3:],
            'hash_md5': self.calculate_hash(filepath, 'md5'),
            'hash_sha256': self.calculate_hash(filepath, 'sha256')
        }
    
    def _resolve_path(self, filepath: str) -> pathlib.Path:
        """Resolve caminho relativo ao base_path"""
        path = pathlib.Path(filepath)
        
        if not path.is_absolute():
            path = self.base_path / path
        
        # Prevenir path traversal
        try:
            resolved = path.resolve()
            if not str(resolved).startswith(str(self.base_path)):
                raise ValueError(f"Acesso a caminho não permitido: {filepath}")
            return resolved
        except Exception as e:
            raise ValueError(f"Caminho inválido: {filepath}") from e
    
    @staticmethod
    def _format_bytes(size: int) -> str:
        """Formata bytes para string legível"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} PB"

class BackupManager:
    """
    Gerenciador de backups com versionamento
    """
    
    def __init__(self, backup_dir: str = "backups", max_backups: int = 10):
        """
        Inicializa o gerenciador de backups
        
        Args:
            backup_dir: Diretório de backups
            max_backups: Número máximo de backups mantidos
        """
        self.backup_dir = pathlib.Path(backup_dir)
        self.max_backups = max_backups
        
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"BackupManager inicializado em: {self.backup_dir}")
    
    def create_backup(self, source: str, tag: str = None) -> str:
        """
        Cria um backup do arquivo ou diretório
        
        Args:
            source: Caminho do arquivo/diretório a ser copiado
            tag: Tag opcional para identificar o backup
            
        Returns:
            Caminho do backup criado
        """
        source_path = pathlib.Path(source)
        
        if not source_path.exists():
            raise FileNotFoundError(f"Arquivo/diretório não encontrado: {source}")
        
        # Nome do backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if tag:
            backup_name = f"{source_path.name}_{tag}_{timestamp}"
        else:
            backup_name = f"{source_path.name}_{timestamp}"
        
        if source_path.is_file():
            backup_path = self.backup_dir / f"{backup_name}{source_path.suffix}"
            shutil.copy2(source_path, backup_path)
        else:
            backup_path = self.backup_dir / backup_name
            shutil.copytree(source_path, backup_path)
        
        # Limitar número de backups
        self._cleanup_old_backups(source_path.name)
        
        logger.info(f"Backup criado: {backup_path}")
        return str(backup_path)
    
    def restore_backup(self, backup_path: str, destination: str = None,
                      overwrite: bool = False) -> str:
        """
        Restaura um backup
        
        Args:
            backup_path: Caminho do backup
            destination: Destino da restauração
            overwrite: Sobrescrever destino se existir
            
        Returns:
            Caminho do arquivo/diretório restaurado
        """
        backup = pathlib.Path(backup_path)
        
        if not backup.exists():
            raise FileNotFoundError(f"Backup não encontrado: {backup_path}")
        
        if destination is None:
            # Inferir nome original
            name_parts = backup.stem.split('_')
            if len(name_parts) >= 3:
                # Formato: nome_tag_timestamp
                original_name = '_'.join(name_parts[:-2])
                suffix = backup.suffix
                destination = f"{original_name}{suffix}"
            else:
                destination = backup.name
        
        dest_path = pathlib.Path(destination)
        
        if dest_path.exists() and not overwrite:
            raise FileExistsError(f"Destino já existe: {destination}")
        
        if backup.is_file():
            shutil.copy2(backup, dest_path)
        else:
            if dest_path.exists():
                shutil.rmtree(dest_path)
            shutil.copytree(backup, dest_path)
        
        logger.info(f"Backup restaurado para: {dest_path}")
        return str(dest_path)
    
    def list_backups(self, pattern: str = "*") -> List[Dict[str, Any]]:
        """
        Lista backups disponíveis
        
        Args:
            pattern: Padrão para filtrar backups
            
        Returns:
            Lista de informações sobre backups
        """
        backups = []
        
        for item in self.backup_dir.glob(pattern):
            stat = item.stat()
            backups.append({
                'name': item.name,
                'path': str(item),
                'size': stat.st_size,
                'size_human': self._format_bytes(stat.st_size),
                'modified': datetime.fromtimestamp(stat.st_mtime),
                'is_file': item.is_file(),
                'is_dir': item.is_dir()
            })
        
        # Ordenar por data de modificação (mais recente primeiro)
        backups.sort(key=lambda x: x['modified'], reverse=True)
        
        return backups
    
    def _cleanup_old_backups(self, base_name: str):
        """
        Remove backups antigos mantendo apenas os mais recentes
        """
        backups = self.list_backups(f"{base_name}_*")
        
        if len(backups) > self.max_backups:
            to_delete = backups[self.max_backups:]
            
            for backup in to_delete:
                path = pathlib.Path(backup['path'])
                if path.is_file():
                    path.unlink()
                else:
                    shutil.rmtree(path)
                
                logger.debug(f"Backup antigo removido: {backup['name']}")
    
    @staticmethod
    def _format_bytes(size: int) -> str:
        """Formata bytes para string legível"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} PB"

# Funções utilitárias estáticas
def find_files(pattern: str, root_dir: str = ".", recursive: bool = True) -> List[str]:
    """
    Encontra arquivos que correspondem ao padrão
    
    Args:
        pattern: Padrão glob
        root_dir: Diretório raiz
        recursive: Busca recursiva
        
    Returns:
        Lista de caminhos encontrados
    """
    root = pathlib.Path(root_dir)
    
    if recursive:
        pattern = f"**/{pattern}"
    
    files = []
    for path in root.glob(pattern):
        if path.is_file():
            files.append(str(path))
    
    return files

def read_json(filepath: str, default: Any = None, encoding: str = 'utf-8') -> Any:
    """
    Lê um arquivo JSON
    
    Args:
        filepath: Caminho do arquivo
        default: Valor padrão se arquivo não existir
        encoding: Codificação
        
    Returns:
        Dados JSON
    """
    try:
        with open(filepath, 'r', encoding=encoding) as f:
            return json.load(f)
    except FileNotFoundError:
        if default is not None:
            return default
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Erro ao decodificar JSON: {filepath}")
        raise e

def write_json(filepath: str, data: Any, indent: int = 2, 
              sort_keys: bool = False, encoding: str = 'utf-8') -> bool:
    """
    Escreve dados em formato JSON
    
    Args:
        filepath: Caminho do arquivo
        data: Dados a serem escritos
        indent: Indentação
        sort_keys: Ordenar chaves
        encoding: Codificação
        
    Returns:
        True se bem sucedido
    """
    try:
        with open(filepath, 'w', encoding=encoding) as f:
            json.dump(data, f, indent=indent, sort_keys=sort_keys,
                     ensure_ascii=False, default=str)
        return True
    except Exception as e:
        logger.error(f"Erro ao escrever JSON: {filepath}")
        raise e

def read_yaml(filepath: str, default: Any = None, encoding: str = 'utf-8') -> Any:
    """
    Lê um arquivo YAML
    
    Args:
        filepath: Caminho do arquivo
        default: Valor padrão se arquivo não existir
        encoding: Codificação
        
    Returns:
        Dados YAML
    """
    try:
        with open(filepath, 'r', encoding=encoding) as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        if default is not None:
            return default
        raise
    except yaml.YAMLError as e:
        logger.error(f"Erro ao decodificar YAML: {filepath}")
        raise e

def write_yaml(filepath: str, data: Any, default_flow_style: bool = False,
              encoding: str = 'utf-8') -> bool:
    """
    Escreve dados em formato YAML
    
    Args:
        filepath: Caminho do arquivo
        data: Dados a serem escritos
        default_flow_style: Estilo de fluxo padrão
        encoding: Codificação
        
    Returns:
        True se bem sucedido
    """
    try:
        with open(filepath, 'w', encoding=encoding) as f:
            yaml.dump(data, f, default_flow_style=default_flow_style,
                     allow_unicode=True, sort_keys=False)
        return True
    except Exception as e:
        logger.error(f"Erro ao escrever YAML: {filepath}")
        raise e

def safe_delete(filepath: str, max_retries: int = 3) -> bool:
    """
    Exclui arquivo com retry em caso de erro
    
    Args:
        filepath: Caminho do arquivo
        max_retries: Número máximo de tentativas
        
    Returns:
        True se bem sucedido
    """
    path = pathlib.Path(filepath)
    
    if not path.exists():
        return True
    
    for attempt in range(max_retries):
        try:
            if path.is_file():
                path.unlink()
            else:
                shutil.rmtree(path)
            return True
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"Falha ao excluir {filepath} após {max_retries} tentativas: {e}")
                return False
            import time
            time.sleep(0.1 * (2 ** attempt))  # Exponential backoff
    
    return False

def calculate_hash(filepath: str, algorithm: str = "sha256") -> str:
    """
    Calcula hash de um arquivo
    
    Args:
        filepath: Caminho do arquivo
        algorithm: Algoritmo de hash
        
    Returns:
        Hash do arquivo
    """
    hash_func = hashlib.new(algorithm)
    
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            hash_func.update(chunk)
    
    return hash_func.hexdigest()

def compress_file(source: str, destination: str = None,
                 algorithm: str = 'gzip') -> str:
    """
    Comprime um arquivo
    
    Args:
        source: Arquivo de origem
        destination: Arquivo de destino
        algorithm: Algoritmo de compressão
        
    Returns:
        Caminho do arquivo comprimido
    """
    fm = FileManager()
    return fm.compress_file(source, destination, algorithm)

def extract_file(source: str, destination: str = None) -> str:
    """
    Extrai um arquivo comprimido
    
    Args:
        source: Arquivo comprimido
        destination: Diretório de destino
        
    Returns:
        Caminho do arquivo extraído
    """
    fm = FileManager()
    return fm.extract_file(source, destination)