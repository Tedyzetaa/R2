"""
History manager with Windows compatibility
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Any
from collections import deque
from pathlib import Path
from enum import Enum

# Adicione esta classe antes da classe HistoryManager
class EventType(Enum):
    """Tipos de eventos para histórico"""
    COMMAND = "command"
    RESPONSE = "response" 
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    SYSTEM = "system"
    VOICE = "voice"
    AI = "ai"
    ALERT = "alert"
    TRADING = "trading"
    NETWORK = "network"
    SECURITY = "security"
    CUSTOM = "custom"


class HistoryManager:
    """Gerenciador de histórico compatível com Windows"""
    
    def __init__(self, max_size: int = 1000, persist_file: Optional[str] = None, config=None):
        """
        Inicializa o gerenciador de histórico
        
        Args:
            max_size: Tamanho máximo do histórico em memória
            persist_file: Caminho para arquivo de persistência
            config: Objeto de configuração (opcional)
        """
        # Compatibilidade: aceitar config ou kwargs
        if config is not None:
            if hasattr(config, 'MAX_HISTORY_SIZE'):
                max_size = config.MAX_HISTORY_SIZE
            if hasattr(config, 'DATA_DIR') and persist_file is None:
                persist_file = os.path.join(config.DATA_DIR, 'history.json')
        
        self.max_size = max_size
        self.persist_file = str(persist_file) if persist_file else None
        
        # Usar deque para histórico eficiente
        self.history = deque(maxlen=max_size)
        
        # Carregar histórico persistido
        self._load_persisted()
        
        print(f"✅ HistoryManager inicializado (max_size={max_size}, persist_file={self.persist_file})")
    
    def _load_persisted(self):
        """Carrega histórico do arquivo se existir"""
        if self.persist_file and os.path.exists(self.persist_file):
            try:
                with open(self.persist_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.history.extend(data[-self.max_size:])
                        print(f"📁 Histórico carregado: {len(data)} entradas")
            except (json.JSONDecodeError, IOError) as e:
                print(f"⚠️  Erro ao carregar histórico: {e}")
    
    def _save_persisted(self):
        """Salva histórico no arquivo"""
        if self.persist_file:
            try:
                os.makedirs(os.path.dirname(self.persist_file), exist_ok=True)
                with open(self.persist_file, 'w', encoding='utf-8') as f:
                    json.dump(list(self.history), f, indent=2, ensure_ascii=False)
            except IOError as e:
                print(f"⚠️  Erro ao salvar histórico: {e}")
    
    def add_entry(self, entry_type: EventType, content: Any, metadata: Optional[Dict] = None):
        """
        Adiciona uma entrada ao histórico
        
        Args:
            entry_type: Tipo da entrada, usando a enumeração EventType.
            content: Conteúdo da entrada
            metadata: Metadados adicionais
        """
        if not isinstance(entry_type, EventType):
            raise TypeError("entry_type deve ser um membro da enumeração EventType")
        entry = {
            'timestamp': datetime.now().isoformat(),
            'type': entry_type.value,
            'content': content,
            'metadata': metadata or {}
        }
        
        self.history.append(entry)
        
        # Salvar periodicamente (a cada 10 entradas)
        if len(self.history) % 10 == 0:
            self._save_persisted()
        
        return entry
    
    def get_recent(self, limit: int = 10, entry_type: Optional[str] = None) -> List[Dict]:
        """
        Obtém entradas recentes do histórico
        
        Args:
            limit: Número máximo de entradas a retornar
            entry_type: Filtrar por tipo (opcional)
            
        Returns:
            Lista de entradas recentes
        """
        if entry_type:
            filtered = [entry for entry in self.history if entry['type'] == entry_type]
            return list(filtered)[-limit:]
        else:
            return list(self.history)[-limit:]
    
    def search(self, query: str, limit: int = 20) -> List[Dict]:
        """
        Busca no histórico
        
        Args:
            query: Texto para buscar
            limit: Número máximo de resultados
            
        Returns:
            Lista de entradas que correspondem à busca
        """
        query_lower = query.lower()
        results = []
        
        for entry in reversed(self.history):
            # Buscar em content e metadata
            content_str = str(entry.get('content', '')).lower()
            metadata_str = str(entry.get('metadata', {})).lower()
            
            if query_lower in content_str or query_lower in metadata_str:
                results.append(entry)
                if len(results) >= limit:
                    break
        
        return results
    
    def clear(self, entry_type: Optional[str] = None):
        """
        Limpa o histórico
        
        Args:
            entry_type: Se especificado, limpa apenas entradas desse tipo
        """
        if entry_type:
            self.history = deque(
                [entry for entry in self.history if entry['type'] != entry_type],
                maxlen=self.max_size
            )
        else:
            self.history.clear()
        
        self._save_persisted()
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas do histórico"""
        by_type = {}
        for entry in self.history:
            entry_type = entry['type']
            by_type[entry_type] = by_type.get(entry_type, 0) + 1
        
        return {
            'total_entries': len(self.history),
            'by_type': by_type,
            'max_size': self.max_size,
            'persisted': self.persist_file is not None
        }
    
    def export_to_file(self, filepath: str):
        """Exporta histórico para arquivo"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(list(self.history), f, indent=2, ensure_ascii=False)
            return True
        except IOError as e:
            print(f"❌ Erro ao exportar histórico: {e}")
            return False
    
    def __len__(self):
        return len(self.history)
    
    def __iter__(self):
        return iter(self.history)