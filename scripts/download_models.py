#!/usr/bin/env python3
"""
Downloader de Modelos do R2 Assistant
Script para baixar e gerenciar modelos de ML/IA
"""

import os
import sys
import json
import hashlib
import shutil
import zipfile
import tarfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime
import platform
import subprocess

# Tentar importar dependências opcionais
try:
    import requests
    from tqdm import tqdm
    HAS_DEPENDENCIES = True
except ImportError:
    HAS_DEPENDENCIES = False

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ModelDownloader:
    """
    Gerenciador de download de modelos
    """
    
    def __init__(self, models_dir: str = None, config_file: str = None):
        """
        Inicializa o downloader de modelos
        
        Args:
            models_dir: Diretório para armazenar modelos
            config_file: Arquivo de configuração de modelos
        """
        self.project_root = Path(__file__).parent.parent
        
        # Diretório de modelos
        if models_dir:
            self.models_dir = Path(models_dir)
        else:
            self.models_dir = self.project_root / "data" / "models"
        
        # Criar estrutura de diretórios
        self.model_categories = [
            "audio",
            "vision", 
            "nlp",
            "trading",
            "cache",
            "configs"
        ]
        
        for category in self.model_categories:
            (self.models_dir / category).mkdir(parents=True, exist_ok=True)
        
        # Arquivo de configuração
        if config_file:
            self.config_file = Path(config_file)
        else:
            self.config_file = self.models_dir / "configs" / "download_list.json"
        
        # Cache de downloads
        self.cache_dir = self.models_dir / "cache"
        self.cache_dir.mkdir(exist_ok=True)
        
        # Histórico de downloads
        self.history_file = self.models_dir / "configs" / "download_history.json"
        self.history_file.parent.mkdir(exist_ok=True)
        
        logger.info(f"ModelDownloader inicializado em: {self.models_dir}")
        
        # Verificar dependências
        if not HAS_DEPENDENCIES:
            logger.warning("Algumas dependências não estão instaladas. Instale com:")
            logger.warning("  pip install requests tqdm")
    
    def load_model_config(self) -> Dict:
        """
        Carrega configuração de modelos
        
        Returns:
            Dicionário com configuração de modelos
        """
        default_config = {
            "version": "1.0.0",
            "last_updated": datetime.now().isoformat(),
            "models": [],
            "sources": {
                "huggingface": {
                    "base_url": "https://huggingface.co",
                    "mirrors": [
                        "https://hf-mirror.com"
                    ]
                },
                "github": {
                    "base_url": "https://github.com"
                },
                "direct": {}
            }
        }
        
        if not self.config_file.exists():
            logger.warning(f"Arquivo de configuração não encontrado: {self.config_file}")
            logger.info(f"Criando configuração padrão em: {self.config_file}")
            
            # Criar configuração padrão
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            
            return default_config
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Garantir que campos obrigatórios existam
            config.setdefault("models", [])
            config.setdefault("sources", default_config["sources"])
            
            return config
            
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao ler arquivo de configuração: {e}")
            return default_config
        except Exception as e:
            logger.error(f"Erro ao carregar configuração: {e}")
            return default_config
    
    def save_model_config(self, config: Dict):
        """
        Salva configuração de modelos
        
        Args:
            config: Configuração a ser salva
        """
        try:
            config["last_updated"] = datetime.now().isoformat()
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"Configuração salva em: {self.config_file}")
            
        except Exception as e:
            logger.error(f"Erro ao salvar configuração: {e}")
    
    def add_model_to_config(self, model_info: Dict):
        """
        Adiciona modelo à configuração
        
        Args:
            model_info: Informações do modelo
        """
        config = self.load_model_config()
        
        # Verificar se modelo já existe
        for i, model in enumerate(config["models"]):
            if model.get("name") == model_info.get("name"):
                config["models"][i] = model_info
                logger.info(f"Modelo atualizado: {model_info['name']}")
                break
        else:
            config["models"].append(model_info)
            logger.info(f"Modelo adicionado: {model_info['name']}")
        
        self.save_model_config(config)
    
    def get_model_info(self, model_name: str) -> Optional[Dict]:
        """
        Obtém informações de um modelo
        
        Args:
            model_name: Nome do modelo
            
        Returns:
            Informações do modelo ou None
        """
        config = self.load_model_config()
        
        for model in config["models"]:
            if model.get("name") == model_name:
                return model
        
        return None
    
    def list_available_models(self) -> List[Dict]:
        """
        Lista modelos disponíveis para download
        
        Returns:
            Lista de modelos
        """
        config = self.load_model_config()
        return config.get("models", [])
    
    def list_installed_models(self) -> List[Dict]:
        """
        Lista modelos instalados
        
        Returns:
            Lista de modelos instalados
        """
        installed = []
        
        for category in self.model_categories:
            if category == "cache" or category == "configs":
                continue
            
            category_dir = self.models_dir / category
            if category_dir.exists():
                for item in category_dir.iterdir():
                    if item.is_dir():
                        # Verificar se tem metadados
                        metadata_file = item / "metadata.json"
                        if metadata_file.exists():
                            try:
                                with open(metadata_file, 'r', encoding='utf-8') as f:
                                    metadata = json.load(f)
                                installed.append(metadata)
                            except:
                                # Modelo sem metadados
                                installed.append({
                                    "name": item.name,
                                    "path": str(item),
                                    "category": category,
                                    "size": self._get_directory_size(item)
                                })
        
        return installed
    
    def download_model(self, model_name: str, force: bool = False, 
                      mirror: bool = True) -> bool:
        """
        Baixa um modelo
        
        Args:
            model_name: Nome do modelo
            force: Forçar redownload mesmo se já existir
            mirror: Usar mirror se disponível
            
        Returns:
            True se download foi bem sucedido
        """
        if not HAS_DEPENDENCIES:
            logger.error("Dependências necessárias não instaladas")
            logger.error("Execute: pip install requests tqdm")
            return False
        
        # Obter informações do modelo
        model_info = self.get_model_info(model_name)
        if not model_info:
            logger.error(f"Modelo não encontrado: {model_name}")
            return False
        
        # Verificar se já está instalado
        if not force and self.is_model_installed(model_name):
            logger.info(f"Modelo já instalado: {model_name}")
            return True
        
        logger.info(f"Baixando modelo: {model_name}")
        logger.info(f"Tipo: {model_info.get('type', 'unknown')}")
        logger.info(f"Tamanho: {model_info.get('size_mb', '?')} MB")
        
        try:
            # Determinar diretório de destino
            category = model_info.get("category", "unknown")
            dest_dir = self.models_dir / category / model_name
            dest_dir.mkdir(parents=True, exist_ok=True)
            
            # Baixar baseado na fonte
            source = model_info.get("source", "direct")
            
            if source == "huggingface":
                success = self._download_from_huggingface(model_info, dest_dir, mirror)
            elif source == "github":
                success = self._download_from_github(model_info, dest_dir)
            else:
                success = self._download_direct(model_info, dest_dir)
            
            if success:
                # Salvar metadados
                metadata = model_info.copy()
                metadata["download_date"] = datetime.now().isoformat()
                metadata["installed_path"] = str(dest_dir)
                
                metadata_file = dest_dir / "metadata.json"
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=2, ensure_ascii=False)
                
                # Registrar no histórico
                self._add_to_history(model_name, "download", success=True)
                
                logger.info(f"✓ Modelo baixado com sucesso: {model_name}")
                return True
            else:
                self._add_to_history(model_name, "download", success=False)
                return False
                
        except Exception as e:
            logger.error(f"Erro ao baixar modelo {model_name}: {e}")
            self._add_to_history(model_name, "download", success=False, error=str(e))
            return False
    
    def _download_from_huggingface(self, model_info: Dict, dest_dir: Path, 
                                 mirror: bool = True) -> bool:
        """
        Baixa modelo do Hugging Face
        
        Args:
            model_info: Informações do modelo
            dest_dir: Diretório de destino
            mirror: Usar mirror
            
        Returns:
            True se download foi bem sucedido
        """
        try:
            repo = model_info.get("repo")
            if not repo:
                logger.error("Repositório Hugging Face não especificado")
                return False
            
            # Obter lista de arquivos do repositório
            base_url = "https://huggingface.co"
            if mirror:
                # Tentar mirror primeiro
                try:
                    base_url = "https://hf-mirror.com"
                    api_url = f"{base_url}/api/models/{repo}"
                    response = requests.get(api_url, timeout=10)
                    response.raise_for_status()
                except:
                    # Fallback para URL original
                    base_url = "https://huggingface.co"
                    api_url = f"{base_url}/api/models/{repo}"
            
            api_url = f"{base_url}/api/models/{repo}"
            response = requests.get(api_url, timeout=30)
            response.raise_for_status()
            
            repo_info = response.json()
            
            # Determinar arquivos para baixar
            files_to_download = model_info.get("files", [])
            if not files_to_download:
                # Baixar todos os arquivos
                siblings = repo_info.get("siblings", [])
                files_to_download = [sib["rfilename"] for sib in siblings]
            
            # Baixar cada arquivo
            for filename in files_to_download:
                file_url = f"{base_url}/{repo}/resolve/main/{filename}"
                dest_path = dest_dir / filename
                
                logger.info(f"  Baixando: {filename}")
                
                # Criar diretórios se necessário
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Download com progress bar
                self._download_file_with_progress(file_url, dest_path)
                
                # Verificar checksum se disponível
                expected_hash = model_info.get("checksum")
                if expected_hash and ":" in expected_hash:
                    algo, expected = expected_hash.split(":")
                    if self._verify_file_hash(dest_path, expected, algo):
                        logger.info(f"    ✓ Checksum verificado ({algo})")
                    else:
                        logger.warning(f"    ✗ Checksum falhou para {filename}")
                        return False
            
            return True
            
        except requests.RequestException as e:
            logger.error(f"Erro de rede ao baixar do Hugging Face: {e}")
            return False
        except Exception as e:
            logger.error(f"Erro ao baixar do Hugging Face: {e}")
            return False
    
    def _download_from_github(self, model_info: Dict, dest_dir: Path) -> bool:
        """
        Baixa modelo do GitHub
        
        Args:
            model_info: Informações do modelo
            dest_dir: Diretório de destino
            
        Returns:
            True se download foi bem sucedido
        """
        try:
            url = model_info.get("url")
            if not url:
                logger.error("URL do GitHub não especificada")
                return False
            
            # Extrair nome do arquivo da URL
            filename = url.split("/")[-1]
            dest_path = dest_dir / filename
            
            logger.info(f"  Baixando: {filename}")
            
            # Download do arquivo
            self._download_file_with_progress(url, dest_path)
            
            # Extrair se for arquivo compactado
            if filename.endswith(('.zip', '.tar.gz', '.tar.bz2', '.tgz')):
                logger.info(f"  Extraindo: {filename}")
                self._extract_archive(dest_path, dest_dir)
                
                # Remover arquivo compactado após extração
                dest_path.unlink()
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao baixar do GitHub: {e}")
            return False
    
    def _download_direct(self, model_info: Dict, dest_dir: Path) -> bool:
        """
        Baixa modelo via URL direta
        
        Args:
            model_info: Informações do modelo
            dest_dir: Diretório de destino
            
        Returns:
            True se download foi bem sucedido
        """
        try:
            url = model_info.get("url")
            if not url:
                logger.error("URL não especificada")
                return False
            
            filename = model_info.get("filename")
            if not filename:
                # Extrair nome do arquivo da URL
                filename = url.split("/")[-1]
                if "?" in filename:
                    filename = filename.split("?")[0]
            
            dest_path = dest_dir / filename
            
            logger.info(f"  Baixando: {filename}")
            
            # Download do arquivo
            self._download_file_with_progress(url, dest_path)
            
            # Verificar checksum
            expected_hash = model_info.get("checksum")
            if expected_hash and ":" in expected_hash:
                algo, expected = expected_hash.split(":")
                if self._verify_file_hash(dest_path, expected, algo):
                    logger.info(f"    ✓ Checksum verificado ({algo})")
                else:
                    logger.error(f"    ✗ Checksum falhou")
                    dest_path.unlink()
                    return False
            
            # Extrair se necessário
            if filename.endswith(('.zip', '.tar.gz', '.tar.bz2', '.tgz', '.7z')):
                logger.info(f"  Extraindo: {filename}")
                if self._extract_archive(dest_path, dest_dir):
                    # Remover arquivo compactado após extração
                    dest_path.unlink()
                else:
                    logger.error(f"  Falha ao extrair {filename}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao baixar arquivo: {e}")
            return False
    
    def _download_file_with_progress(self, url: str, dest_path: Path):
        """
        Baixa arquivo com barra de progresso
        
        Args:
            url: URL do arquivo
            dest_path: Caminho de destino
        """
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        
        with open(dest_path, 'wb') as f, tqdm(
            desc=dest_path.name,
            total=total_size,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
        ) as pbar:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    pbar.update(len(chunk))
    
    def _verify_file_hash(self, filepath: Path, expected_hash: str, 
                         algorithm: str = "sha256") -> bool:
        """
        Verifica hash de arquivo
        
        Args:
            filepath: Caminho do arquivo
            expected_hash: Hash esperado
            algorithm: Algoritmo de hash
            
        Returns:
            True se hash corresponde
        """
        hash_func = hashlib.new(algorithm)
        
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_func.update(chunk)
        
        actual_hash = hash_func.hexdigest()
        return actual_hash == expected_hash.lower()
    
    def _extract_archive(self, archive_path: Path, dest_dir: Path) -> bool:
        """
        Extrai arquivo compactado
        
        Args:
            archive_path: Caminho do arquivo compactado
            dest_dir: Diretório de destino
            
        Returns:
            True se extração foi bem sucedida
        """
        try:
            if archive_path.suffix == '.zip':
                with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                    zip_ref.extractall(dest_dir)
            elif archive_path.suffix in ['.tar.gz', '.tgz', '.tar.bz2']:
                mode = 'r:gz' if archive_path.suffix in ['.tar.gz', '.tgz'] else 'r:bz2'
                with tarfile.open(archive_path, mode) as tar_ref:
                    tar_ref.extractall(dest_dir)
            else:
                logger.warning(f"Formato não suportado: {archive_path.suffix}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao extrair arquivo: {e}")
            return False
    
    def is_model_installed(self, model_name: str) -> bool:
        """
        Verifica se modelo está instalado
        
        Args:
            model_name: Nome do modelo
            
        Returns:
            True se modelo está instalado
        """
        config = self.load_model_config()
        
        for model in config["models"]:
            if model.get("name") == model_name:
                category = model.get("category", "unknown")
                model_dir = self.models_dir / category / model_name
                
                # Verificar se diretório existe e tem conteúdo
                if model_dir.exists() and any(model_dir.iterdir()):
                    # Verificar metadados
                    metadata_file = model_dir / "metadata.json"
                    if metadata_file.exists():
                        return True
        
        return False
    
    def remove_model(self, model_name: str) -> bool:
        """
        Remove modelo instalado
        
        Args:
            model_name: Nome do modelo
            
        Returns:
            True se remoção foi bem sucedida
        """
        if not self.is_model_installed(model_name):
            logger.warning(f"Modelo não instalado: {model_name}")
            return False
        
        # Encontrar diretório do modelo
        model_info = self.get_model_info(model_name)
        if not model_info:
            logger.error(f"Informações do modelo não encontradas: {model_name}")
            return False
        
        category = model_info.get("category", "unknown")
        model_dir = self.models_dir / category / model_name
        
        try:
            # Remover diretório
            if model_dir.exists():
                shutil.rmtree(model_dir)
                logger.info(f"Modelo removido: {model_name}")
                
                # Registrar no histórico
                self._add_to_history(model_name, "remove", success=True)
                return True
            else:
                logger.warning(f"Diretório do modelo não encontrado: {model_dir}")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao remover modelo: {e}")
            self._add_to_history(model_name, "remove", success=False, error=str(e))
            return False
    
    def verify_model_integrity(self, model_name: str) -> Dict:
        """
        Verifica integridade do modelo
        
        Args:
            model_name: Nome do modelo
            
        Returns:
            Dicionário com resultados da verificação
        """
        if not self.is_model_installed(model_name):
            return {"status": "not_installed", "model": model_name}
        
        model_info = self.get_model_info(model_name)
        if not model_info:
            return {"status": "unknown", "model": model_name}
        
        category = model_info.get("category", "unknown")
        model_dir = self.models_dir / category / model_name
        
        results = {
            "model": model_name,
            "status": "checking",
            "files": [],
            "missing_files": [],
            "corrupted_files": [],
            "total_size": 0
        }
        
        # Verificar arquivos esperados
        expected_files = model_info.get("files", [])
        
        for filename in expected_files:
            filepath = model_dir / filename
            file_info = {
                "name": filename,
                "exists": filepath.exists()
            }
            
            if filepath.exists():
                file_info["size"] = filepath.stat().st_size
                results["total_size"] += file_info["size"]
                
                # Verificar checksum se disponível
                expected_hash = model_info.get("checksum")
                if expected_hash and ":" in expected_hash:
                    algo, expected = expected_hash.split(":")
                    file_info["checksum_verified"] = self._verify_file_hash(
                        filepath, expected, algo
                    )
                    
                    if not file_info["checksum_verified"]:
                        results["corrupted_files"].append(filename)
                
                results["files"].append(file_info)
            else:
                file_info["exists"] = False
                results["missing_files"].append(filename)
                results["files"].append(file_info)
        
        # Determinar status final
        if results["missing_files"]:
            results["status"] = "incomplete"
        elif results["corrupted_files"]:
            results["status"] = "corrupted"
        else:
            results["status"] = "ok"
        
        return results
    
    def cleanup_cache(self) -> Tuple[int, int]:
        """
        Limpa cache de downloads
        
        Returns:
            Tupla com (arquivos_removidos, bytes_liberados)
        """
        if not self.cache_dir.exists():
            return 0, 0
        
        removed_count = 0
        freed_bytes = 0
        
        for item in self.cache_dir.iterdir():
            try:
                if item.is_file():
                    size = item.stat().st_size
                    item.unlink()
                    removed_count += 1
                    freed_bytes += size
                elif item.is_dir():
                    # Remover diretórios vazios
                    if not any(item.iterdir()):
                        item.rmdir()
            except Exception as e:
                logger.debug(f"Erro ao remover {item}: {e}")
        
        logger.info(f"Cache limpo: {removed_count} arquivos, "
                   f"{self._format_bytes(freed_bytes)} liberados")
        
        return removed_count, freed_bytes
    
    def _add_to_history(self, model_name: str, action: str, 
                       success: bool, error: str = None):
        """
        Adiciona entrada ao histórico de downloads
        
        Args:
            model_name: Nome do modelo
            action: Ação realizada
            success: Se ação foi bem sucedida
            error: Mensagem de erro (se houver)
        """
        history = []
        
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            except:
                pass
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "model": model_name,
            "action": action,
            "success": success,
            "error": error
        }
        
        history.append(entry)
        
        # Manter apenas as últimas 100 entradas
        if len(history) > 100:
            history = history[-100:]
        
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
        except:
            pass
    
    def _get_directory_size(self, path: Path) -> int:
        """
        Calcula tamanho total de diretório
        
        Args:
            path: Caminho do diretório
            
        Returns:
            Tamanho em bytes
        """
        total = 0
        for entry in path.rglob('*'):
            if entry.is_file():
                total += entry.stat().st_size
        return total
    
    @staticmethod
    def _format_bytes(size: int) -> str:
        """
        Formata bytes para string legível
        
        Args:
            size: Tamanho em bytes
            
        Returns:
            String formatada
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} PB"
    
    def run_interactive(self):
        """
        Executa interface interativa
        """
        print("\n" + "=" * 60)
        print("R2 ASSISTANT - GERENCIADOR DE MODELOS")
        print("=" * 60)
        
        while True:
            print("\nOpções:")
            print("  1. Listar modelos disponíveis")
            print("  2. Listar modelos instalados")
            print("  3. Baixar modelo")
            print("  4. Verificar modelo")
            print("  5. Remover modelo")
            print("  6. Limpar cache")
            print("  7. Verificar dependências")
            print("  8. Sair")
            
            choice = input("\nEscolha uma opção (1-8): ").strip()
            
            if choice == "1":
                self._list_available_interactive()
            elif choice == "2":
                self._list_installed_interactive()
            elif choice == "3":
                self._download_interactive()
            elif choice == "4":
                self._verify_interactive()
            elif choice == "5":
                self._remove_interactive()
            elif choice == "6":
                self._cleanup_interactive()
            elif choice == "7":
                self._check_dependencies_interactive()
            elif choice == "8":
                print("\nAté logo!")
                break
            else:
                print("Opção inválida. Tente novamente.")
    
    def _list_available_interactive(self):
        """Lista modelos disponíveis (modo interativo)"""
        models = self.list_available_models()
        
        if not models:
            print("\nNenhum modelo configurado.")
            return
        
        print(f"\nModelos disponíveis ({len(models)}):")
        print("-" * 80)
        
        for i, model in enumerate(models, 1):
            installed = "✓" if self.is_model_installed(model["name"]) else " "
            print(f"{i:2d}. [{installed}] {model['name']:30} "
                  f"{model.get('type', 'unknown'):15} "
                  f"{model.get('size_mb', '?')} MB")
            
            if model.get("description"):
                print(f"     {model['description']}")
        
        print("-" * 80)
    
    def _list_installed_interactive(self):
        """Lista modelos instalados (modo interativo)"""
        models = self.list_installed_models()
        
        if not models:
            print("\nNenhum modelo instalado.")
            return
        
        print(f"\nModelos instalados ({len(models)}):")
        print("-" * 80)
        
        for i, model in enumerate(models, 1):
            size = self._format_bytes(model.get("size", 0))
            print(f"{i:2d}. {model['name']:30} "
                  f"{model.get('category', 'unknown'):15} {size}")
        
        print("-" * 80)
    
    def _download_interactive(self):
        """Download de modelo (modo interativo)"""
        models = self.list_available_models()
        
        if not models:
            print("\nNenhum modelo configurado.")
            return
        
        print("\nModelos disponíveis para download:")
        for i, model in enumerate(models, 1):
            installed = "✓" if self.is_model_installed(model["name"]) else " "
            print(f"{i:2d}. [{installed}] {model['name']}")
        
        try:
            choice = input("\nNúmero do modelo (ou nome): ").strip()
            
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(models):
                    model_name = models[idx]["name"]
                else:
                    print("Número inválido.")
                    return
            else:
                model_name = choice
            
            force = input("Forçar redownload? (s/N): ").strip().lower() == 's'
            mirror = input("Usar mirror? (S/n): ").strip().lower() != 'n'
            
            print(f"\nBaixando {model_name}...")
            success = self.download_model(model_name, force=force, mirror=mirror)
            
            if success:
                print(f"✓ Modelo {model_name} baixado com sucesso!")
            else:
                print(f"✗ Falha ao baixar {model_name}")
                
        except KeyboardInterrupt:
            print("\nDownload cancelado.")
        except Exception as e:
            print(f"Erro: {e}")
    
    def _verify_interactive(self):
        """Verificação de modelo (modo interativo)"""
        models = self.list_installed_models()
        
        if not models:
            print("\nNenhum modelo instalado.")
            return
        
        print("\nModelos instalados:")
        for i, model in enumerate(models, 1):
            print(f"{i:2d}. {model['name']}")
        
        try:
            choice = input("\nNúmero do modelo (ou nome): ").strip()
            
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(models):
                    model_name = models[idx]["name"]
                else:
                    print("Número inválido.")
                    return
            else:
                model_name = choice
            
            print(f"\nVerificando {model_name}...")
            result = self.verify_model_integrity(model_name)
            
            print(f"\nStatus: {result['status'].upper()}")
            
            if result.get("missing_files"):
                print(f"Arquivos faltando: {len(result['missing_files'])}")
                for f in result['missing_files']:
                    print(f"  - {f}")
            
            if result.get("corrupted_files"):
                print(f"Arquivos corrompidos: {len(result['corrupted_files'])}")
                for f in result['corrupted_files']:
                    print(f"  - {f}")
            
            if result['status'] == 'ok':
                size = self._format_bytes(result['total_size'])
                print(f"✓ Modelo íntegro ({size})")
                
        except Exception as e:
            print(f"Erro: {e}")
    
    def _remove_interactive(self):
        """Remoção de modelo (modo interativo)"""
        models = self.list_installed_models()
        
        if not models:
            print("\nNenhum modelo instalado.")
            return
        
        print("\nModelos instalados:")
        for i, model in enumerate(models, 1):
            print(f"{i:2d}. {model['name']}")
        
        try:
            choice = input("\nNúmero do modelo para remover: ").strip()
            
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(models):
                    model_name = models[idx]["name"]
                else:
                    print("Número inválido.")
                    return
            else:
                model_name = choice
            
            confirm = input(f"\nTem certeza que deseja remover {model_name}? (s/N): ")
            
            if confirm.strip().lower() == 's':
                print(f"\nRemovendo {model_name}...")
                success = self.remove_model(model_name)
                
                if success:
                    print(f"✓ Modelo {model_name} removido.")
                else:
                    print(f"✗ Falha ao remover {model_name}.")
            else:
                print("Remoção cancelada.")
                
        except Exception as e:
            print(f"Erro: {e}")
    
    def _cleanup_interactive(self):
        """Limpeza de cache (modo interativo)"""
        try:
            confirm = input("\nLimpar cache de downloads? (s/N): ")
            
            if confirm.strip().lower() == 's':
                print("\nLimpando cache...")
                count, freed = self.cleanup_cache()
                
                if count > 0:
                    size = self._format_bytes(freed)
                    print(f"✓ Cache limpo: {count} arquivos, {size} liberados.")
                else:
                    print("✓ Cache já está limpo.")
            else:
                print("Limpeza cancelada.")
                
        except Exception as e:
            print(f"Erro: {e}")
    
    def _check_dependencies_interactive(self):
        """Verificação de dependências (modo interativo)"""
        print("\nVerificando dependências...")
        
        if not HAS_DEPENDENCIES:
            print("✗ Dependências não instaladas:")
            print("  - requests")
            print("  - tqdm")
            print("\nInstale com: pip install requests tqdm")
        else:
            print("✓ Todas as dependências estão instaladas.")

def main():
    """Função principal"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Gerenciador de modelos do R2 Assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  %(prog)s --list                     # Lista modelos disponíveis
  %(prog)s --installed                # Lista modelos instalados
  %(prog)s --download whisper-base    # Baixa modelo específico
  %(prog)s --verify yolov8            # Verifica modelo instalado
  %(prog)s --remove old-model         # Remove modelo
  %(prog)s --interactive              # Modo interativo
        """
    )
    
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="Lista modelos disponíveis para download"
    )
    
    parser.add_argument(
        "--installed", "-i",
        action="store_true",
        help="Lista modelos instalados"
    )
    
    parser.add_argument(
        "--download", "-d",
        metavar="MODEL",
        help="Baixa um modelo específico"
    )
    
    parser.add_argument(
        "--verify", "-v",
        metavar="MODEL",
        help="Verifica integridade de um modelo"
    )
    
    parser.add_argument(
        "--remove", "-r",
        metavar="MODEL",
        help="Remove um modelo instalado"
    )
    
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Limpa cache de downloads"
    )
    
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Executa em modo interativo"
    )
    
    parser.add_argument(
        "--force",
        action="store_true",
        help="Força redownload (com --download)"
    )
    
    parser.add_argument(
        "--no-mirror",
        action="store_true",
        help="Não usa mirror para downloads"
    )
    
    parser.add_argument(
        "--models-dir",
        help="Diretório personalizado para modelos"
    )
    
    parser.add_argument(
        "--config",
        help="Arquivo de configuração personalizado"
    )
    
    args = parser.parse_args()
    
    # Verificar dependências
    if not HAS_DEPENDENCIES and any([args.download, args.interactive]):
        logger.error("Dependências necessárias não instaladas")
        logger.error("Execute: pip install requests tqdm")
        sys.exit(1)
    
    # Criar downloader
    downloader = ModelDownloader(
        models_dir=args.models_dir,
        config_file=args.config
    )
    
    # Executar ação solicitada
    if args.interactive:
        downloader.run_interactive()
    elif args.list:
        models = downloader.list_available_models()
        
        if models:
            print(f"\nModelos disponíveis ({len(models)}):")
            for model in models:
                installed = "✓" if downloader.is_model_installed(model["name"]) else " "
                print(f"[{installed}] {model['name']:30} "
                      f"{model.get('type', 'unknown'):15} "
                      f"{model.get('size_mb', '?')} MB")
        else:
            print("Nenhum modelo configurado.")
            
    elif args.installed:
        models = downloader.list_installed_models()
        
        if models:
            print(f"\nModelos instalados ({len(models)}):")
            for model in models:
                size = downloader._format_bytes(model.get("size", 0))
                print(f"  {model['name']:30} "
                      f"{model.get('category', 'unknown'):15} {size}")
        else:
            print("Nenhum modelo instalado.")
            
    elif args.download:
        success = downloader.download_model(
            args.download,
            force=args.force,
            mirror=not args.no_mirror
        )
        sys.exit(0 if success else 1)
        
    elif args.verify:
        result = downloader.verify_model_integrity(args.verify)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
    elif args.remove:
        success = downloader.remove_model(args.remove)
        sys.exit(0 if success else 1)
        
    elif args.cleanup:
        count, freed = downloader.cleanup_cache()
        print(f"Cache limpo: {count} arquivos, "
              f"{downloader._format_bytes(freed)} liberados.")
        
    else:
        # Nenhuma ação especificada, mostrar ajuda
        parser.print_help()

if __name__ == "__main__":
    main()