import json
import time
import re
from pathlib import Path
from datetime import datetime
from collections import Counter
import math

class LongTermMemory:
    def __init__(self, config):
        self.config = config
        self.memory_file = Path(config.DATA_DIR) / "permanent_memory.json"
        self._ensure_memory_file()
        self.memories = self._load_memories()

    def _ensure_memory_file(self):
        if not self.memory_file.parent.exists():
            self.memory_file.parent.mkdir(parents=True)
        if not self.memory_file.exists():
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump([], f)

    def _load_memories(self):
        try:
            with open(self.memory_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []

    def save_interaction(self, user_input, bot_response):
        """Salva uma interação completa com metadados"""
        entry = {
            "id": len(self.memories) + 1,
            "timestamp": datetime.now().isoformat(),
            "user": user_input,
            "bot": bot_response,
            "keywords": self._extract_keywords(user_input + " " + bot_response)
        }
        self.memories.append(entry)
        self._persist()

    def _persist(self):
        with open(self.memory_file, 'w', encoding='utf-8') as f:
            json.dump(self.memories, f, indent=2, ensure_ascii=False)

    def retrieve_relevant_context(self, current_query, limit=3):
        """
        Busca memórias passadas relevantes à query atual.
        Usa um algoritmo de similaridade baseado em palavras-chave (Jaccard/Overlap).
        """
        if not self.memories:
            return ""

        query_keywords = set(self._extract_keywords(current_query))
        scored_memories = []

        for mem in self.memories:
            # Pula memórias muito recentes (já estão no histórico de curto prazo)
            # Assumindo que as últimas 5 já estão no chat context
            if mem['id'] > len(self.memories) - 5:
                continue

            mem_keywords = set(mem['keywords'])
            
            # Cálculo simples de relevância (Interseção de palavras)
            overlap = len(query_keywords.intersection(mem_keywords))
            
            if overlap > 0:
                scored_memories.append((overlap, mem))

        # Ordena por relevância e pega os top N
        scored_memories.sort(key=lambda x: x[0], reverse=True)
        top_memories = scored_memories[:limit]

        if not top_memories:
            return ""

        # Formata para injeção no prompt
        context_str = "\n[MEMÓRIA DE LONGO PRAZO RECUPERADA]:\n"
        for score, mem in top_memories:
            date_str = datetime.fromisoformat(mem['timestamp']).strftime("%d/%m/%Y")
            context_str += f"- Em {date_str}, você disse: '{mem['user']}' e eu respondi: '{mem['bot'][:100]}...'\n"
        
        return context_str

    def _extract_keywords(self, text):
        """Extrai palavras importantes (filtra stop words básicas)"""
        # Stop words simples em PT-BR
        stop_words = {'o', 'a', 'os', 'as', 'um', 'uma', 'de', 'do', 'da', 'em', 'no', 'na', 
                      'que', 'e', 'é', 'para', 'por', 'com', 'não', 'sim', 'eu', 'voce', 'r2'}
        
        # Limpeza
        text = re.sub(r'[^\w\s]', '', text.lower())
        words = text.split()
        
        return [w for w in words if w not in stop_words and len(w) > 2]