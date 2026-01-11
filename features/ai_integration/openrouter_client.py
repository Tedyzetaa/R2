"""
OpenRouter API Integration for Mistral 7B and other models
"""
from openai import OpenAI
import os
from core.long_term_memory import LongTermMemory # <--- NOVO IMPORT
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from dotenv import load_dotenv
import re

load_dotenv()

logger = logging.getLogger(__name__)

@dataclass
class AIResponse:
    """AI response container"""
    content: str
    model: str
    tokens_used: int
    finish_reason: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'content': self.content,
            'model': self.model,
            'tokens_used': self.tokens_used,
            'finish_reason': self.finish_reason,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata
        }

class AIIntegrationManager:
    """Manager for AI integration with fallback"""
    
    def __init__(self, config):
        self.config = config
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
        )
        self.model = "mistralai/mistral-7b-instruct" # ou o modelo que vc usa
        self.system_prompt = """
IDENTIDADE: Você é R2, uma IA Tática de Interface Avançada.
ESTILO: Respostas curtas, estilo terminal militar. Use colchetes para dados.
REGRAS:
1. Nunca use marcadores de chat como "Olá", "Claro". Vá direto ao ponto.
2. Se o usuário pedir "Monitoramento", gere um log técnico.

EXEMPLO DE RESPOSTA IDEAL:
[SISTEMA]: Iniciando varredura espectral...
[ALVO]: Sol (Estrela Tipo G)
[TEMP. SUPERFÍCIE]: 5.778 K
[ATIVIDADE]: Estável
[STATUS]: Monitoramento ativo.
"""
        self.memory = LongTermMemory(config) # <--- Inicializa Memória
        self.chat_history = [] # Memória de curto prazo
    
    async def initialize(self):
        """Initialize AI integration"""
        self.active = True
        logger.info("✅ AI Integration Manager (new) initialized.")

    def _limpar_sujeira_llm(self, texto):
        """Remove tags de instrução que vazam do modelo"""
        if not texto: return ""
        
        # Remove [/INST], [INST], <s>, </s> e variações
        texto_limpo = re.sub(r'\[/?INST\]', '', texto)
        texto_limpo = re.sub(r'<?s>', '', texto_limpo)
        texto_limpo = re.sub(r'</?s>', '', texto_limpo)
        texto_limpo = re.sub(r'<<.*?>>', '', texto_limpo) # Remove pensamentos internos
        
        return texto_limpo.strip()
    
    async def chat(self, user_id: str, message: str, use_history: bool = True):
        try:
            # Se for um comando simples conhecido, podemos interceptar antes de gastar IA
            if "ajuda" in message.lower():
                return type('obj', (object,), {'content': "[SISTEMA]: Comandos disponíveis: 'Monitoramento Solar', 'Status', 'Iniciar Trade', 'Rastrear Satélites'."})

            messages_payload = []

            # 1. Recupera Contexto Antigo (RAG)
            # O bot procura nas memórias antigas algo relacionado ao que você falou agora
            past_context = self.memory.retrieve_relevant_context(message)

            # 2. Constrói o System Prompt com a Persona + Memória Recuperada
            system_base = self.system_prompt
            
            if past_context:
                # Injeta a memória no instrução do sistema
                full_system_prompt = f"{system_base}\n\n{past_context}\n\nUSE AS INFORMAÇÕES ACIMA SE FOREM RELEVANTES."
            else:
                full_system_prompt = system_base

            messages_payload.append({"role": "system", "content": full_system_prompt})

            # 3. Adiciona histórico de curto prazo (Conversa atual)
            if use_history:
                for msg in self.chat_history[-6:]: # Mantém últimas 6 trocas para fluidez imediata
                    messages_payload.append(msg)

            # 4. Mensagem atual
            messages_payload.append({"role": "user", "content": message})

            # 5. Chamada API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages_payload,
                temperature=0.7,
                max_tokens=300
            )

            raw_content = response.choices[0].message.content
            ai_reply = self._limpar_sujeira_llm(raw_content)

            # CORREÇÃO: Se a limpeza removeu tudo, devolve o cru ou mensagem de erro
            if not ai_reply or len(ai_reply) < 2:
                logger.warning(f"⚠️ [DEBUG]: Resposta crua era: {raw_content}")
                ai_reply = "[R2]: Não consegui processar os dados. Repita o comando."

            # 6. SALVA NA MEMÓRIA PERMANENTE
            # Salva tudo o que é falado para o futuro
            if use_history:
                self.chat_history.append({"role": "user", "content": message})
                self.chat_history.append({"role": "assistant", "content": ai_reply})
                
                # Persistência no disco
                self.memory.save_interaction(message, ai_reply)

            return type('obj', (object,), {'content': ai_reply})

        except Exception as e:
            print(f"AI Error: {e}")
            return type('obj', (object,), {'content': f"Erro de processamento neural: {e}"})