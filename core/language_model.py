"""
Language model integration with OpenRouter and other AI providers
"""

import json
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import time
from functools import lru_cache

class AIModel(Enum):
    """Available AI models"""
    MISTRAL_7B = "mistralai/mistral-7b-instruct:free"
    MISTRAL_8X7B = "mistralai/mixtral-8x7b-instruct"
    GPT_3_5 = "openai/gpt-3.5-turbo"
    GPT_4 = "openai/gpt-4"
    CLAUDE_3 = "anthropic/claude-3-haiku"
    LLAMA_2 = "meta-llama/llama-2-13b-chat"

@dataclass
class Message:
    """Chat message"""
    role: str  # system, user, assistant
    content: str
    timestamp: float = field(default_factory=time.time)

@dataclass
class AIResponse:
    """AI response with metadata"""
    content: str
    model: str
    tokens_used: int
    response_time: float
    finish_reason: str
    cached: bool = False

class LanguageModel:
    """
    Language model interface with caching and fallback support
    """
    
    def __init__(self, config):
        self.config = config
        self.api_key = config.OPENROUTER_API_KEY
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        
        # Response cache
        self.cache = {}
        self.cache_hits = 0
        self.cache_misses = 0
        
        # Conversation history
        self.conversations: Dict[str, List[Message]] = {}
        
        # System prompts
        self.system_prompts = self._load_system_prompts()
        
        # Statistics
        self.stats = {
            'total_requests': 0,
            'total_tokens': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'avg_response_time': 0.0,
            'total_cost': 0.0
        }
    
    def _load_system_prompts(self) -> Dict[str, str]:
        """Load system prompts for different contexts"""
        return {
            'default': """Você é o R2, um assistente de IA inspirado no R2-D2 de Star Wars. 
            Você é útil, amigável e tem personalidade. 
            Responda de forma concisa e técnica quando apropriado.
            Use emojis ocasionalmente para expressar emoções.
            Idioma: Português do Brasil.""",
            
            'technical': """Você é o R2, um assistente técnico especializado.
            Forneça respostas precisas e técnicas.
            Inclua detalhes relevantes e seja específico.
            Use termos técnicos quando apropriado.""",
            
            'trading': """Você é o R2, um assistente de trading quantitativo.
            Analise dados de mercado e forneça insights.
            Seja preciso com números e estatísticas.
            Inclua análises de risco quando relevante.""",
            
            'casual': """Você é o R2, um assistente amigável e descontraído.
            Seja divertido e use humor quando apropriado.
            Mantenha as respostas leves e agradáveis."""
        }
    
    def get_response(self, prompt: str, 
                    context: str = 'default',
                    conversation_id: Optional[str] = None,
                    use_cache: bool = True) -> AIResponse:
        """
        Get AI response for a prompt
        
        Args:
            prompt: User prompt
            context: Context for system prompt
            conversation_id: ID for continuing conversation
            use_cache: Whether to use response cache
            
        Returns:
            AIResponse object
        """
        start_time = time.time()
        
        # Check cache
        cache_key = self._generate_cache_key(prompt, context)
        if use_cache and cache_key in self.cache:
            self.cache_hits += 1
            cached_response = self.cache[cache_key]
            return AIResponse(
                content=cached_response['content'],
                model=cached_response['model'],
                tokens_used=cached_response['tokens_used'],
                response_time=time.time() - start_time,
                finish_reason=cached_response['finish_reason'],
                cached=True
            )
        
        self.cache_misses += 1
        self.stats['total_requests'] += 1
        
        try:
            # Prepare messages
            messages = self._prepare_messages(prompt, context, conversation_id)
            
            # Make API request
            response = self._make_api_request(messages)
            
            # Parse response
            ai_response = self._parse_response(response)
            ai_response.response_time = time.time() - start_time
            
            # Update cache
            if use_cache:
                self.cache[cache_key] = {
                    'content': ai_response.content,
                    'model': ai_response.model,
                    'tokens_used': ai_response.tokens_used,
                    'finish_reason': ai_response.finish_reason,
                    'timestamp': time.time()
                }
                
                # Clean old cache entries
                self._clean_cache()
            
            # Update conversation history
            if conversation_id:
                self._update_conversation(conversation_id, prompt, ai_response.content)
            
            # Update statistics
            self.stats['successful_requests'] += 1
            self.stats['total_tokens'] += ai_response.tokens_used
            self.stats['avg_response_time'] = (
                (self.stats['avg_response_time'] * (self.stats['successful_requests'] - 1) + 
                 ai_response.response_time) / self.stats['successful_requests']
            )
            
            return ai_response
            
        except Exception as e:
            self.stats['failed_requests'] += 1
            print(f"❌ AI request failed: {e}")
            
            # Return fallback response
            return AIResponse(
                content=self._get_fallback_response(prompt),
                model="fallback",
                tokens_used=0,
                response_time=time.time() - start_time,
                finish_reason="error",
                cached=False
            )
    
    def _prepare_messages(self, prompt: str, context: str, 
                         conversation_id: Optional[str]) -> List[Dict[str, str]]:
        """Prepare messages for API request"""
        messages = []
        
        # Add system prompt
        system_prompt = self.system_prompts.get(context, self.system_prompts['default'])
        messages.append({"role": "system", "content": system_prompt})
        
        # Add conversation history if available
        if conversation_id and conversation_id in self.conversations:
            for msg in self.conversations[conversation_id][-10:]:  # Last 10 messages
                messages.append({"role": msg.role, "content": msg.content})
        
        # Add current prompt
        messages.append({"role": "user", "content": prompt})
        
        return messages
    
    def _make_api_request(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Make API request to OpenRouter"""
        import requests
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/yourusername/r2-assistant",
            "X-Title": "R2 Assistant"
        }
        
        data = {
            "model": self.config.AI_MODEL,
            "messages": messages,
            "max_tokens": self.config.AI_MAX_TOKENS,
            "temperature": self.config.AI_TEMPERATURE,
            "stream": False
        }
        
        response = requests.post(
            self.base_url,
            headers=headers,
            json=data,
            timeout=self.config.API_TIMEOUT
        )
        
        response.raise_for_status()
        return response.json()
    
    def _parse_response(self, api_response: Dict[str, Any]) -> AIResponse:
        """Parse API response"""
        choices = api_response.get('choices', [])
        if not choices:
            raise ValueError("No choices in API response")
        
        choice = choices[0]
        message = choice.get('message', {})
        
        return AIResponse(
            content=message.get('content', ''),
            model=api_response.get('model', 'unknown'),
            tokens_used=api_response.get('usage', {}).get('total_tokens', 0),
            response_time=0.0,  # Will be set later
            finish_reason=choice.get('finish_reason', 'stop')
        )
    
    def _generate_cache_key(self, prompt: str, context: str) -> str:
        """Generate cache key for prompt"""
        content = f"{context}:{prompt}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _clean_cache(self):
        """Clean old cache entries"""
        max_cache_size = self.config.AI_CACHE_SIZE
        if len(self.cache) > max_cache_size:
            # Remove oldest entries
            sorted_items = sorted(
                self.cache.items(), 
                key=lambda x: x[1]['timestamp']
            )
            items_to_remove = len(self.cache) - max_cache_size
            
            for key, _ in sorted_items[:items_to_remove]:
                del self.cache[key]
    
    def _update_conversation(self, conversation_id: str, 
                           user_message: str, assistant_message: str):
        """Update conversation history"""
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []
        
        # Add user message
        self.conversations[conversation_id].append(
            Message(role="user", content=user_message)
        )
        
        # Add assistant message
        self.conversations[conversation_id].append(
            Message(role="assistant", content=assistant_message)
        )
        
        # Limit conversation history
        max_messages = 50
        if len(self.conversations[conversation_id]) > max_messages:
            self.conversations[conversation_id] = self.conversations[conversation_id][-max_messages:]
    
    def _get_fallback_response(self, prompt: str) -> str:
        """Get fallback response when AI is unavailable"""
        fallback_responses = [
            "Desculpe, estou tendo problemas para acessar meus recursos de IA no momento. "
            "Por favor, tente novamente em alguns instantes.",
            
            "Parece que meu sistema de IA está temporariamente indisponível. "
            "Enquanto isso, posso ajudá-lo com comandos locais do sistema.",
            
            "Estou passando por uma manutenção rápida em meu cérebro de IA. "
            "Voltarei a funcionar em breve!",
            
            "No momento, não consigo acessar meus recursos de processamento de linguagem. "
            "Você pode tentar um comando de voz ou ação do sistema."
        ]
        
        import random
        return random.choice(fallback_responses)
    
    def start_conversation(self, context: str = 'default') -> str:
        """Start a new conversation and return its ID"""
        import uuid
        conversation_id = str(uuid.uuid4())
        self.conversations[conversation_id] = []
        
        # Add initial system message
        self.conversations[conversation_id].append(
            Message(
                role="system",
                content=self.system_prompts.get(context, self.system_prompts['default'])
            )
        )
        
        return conversation_id
    
    def end_conversation(self, conversation_id: str):
        """End a conversation and clean up its history"""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
    
    def clear_conversation(self, conversation_id: str):
        """Clear messages from a conversation"""
        if conversation_id in self.conversations:
            self.conversations[conversation_id] = []
    
    def get_conversation_history(self, conversation_id: str, 
                                limit: int = 20) -> List[Message]:
        """Get conversation history"""
        if conversation_id not in self.conversations:
            return []
        
        messages = self.conversations[conversation_id]
        return messages[-limit:] if limit else messages
    
    def set_system_prompt(self, context: str, prompt: str):
        """Set custom system prompt for a context"""
        self.system_prompts[context] = prompt
    
    def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """Analyze sentiment of text"""
        # This is a simplified version
        # In production, you'd use a proper sentiment analysis model
        
        positive_words = ['bom', 'ótimo', 'excelente', 'maravilhoso', 'feliz', 'gostei']
        negative_words = ['ruim', 'péssimo', 'horrível', 'triste', 'odeio', 'problema']
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        total_words = len(text.split())
        
        if total_words == 0:
            return {'positive': 0.0, 'negative': 0.0, 'neutral': 1.0}
        
        positive_score = positive_count / total_words
        negative_score = negative_count / total_words
        neutral_score = 1.0 - positive_score - negative_score
        
        return {
            'positive': max(0.0, positive_score),
            'negative': max(0.0, negative_score),
            'neutral': max(0.0, neutral_score)
        }
    
    def summarize_text(self, text: str, max_length: int = 200) -> str:
        """Summarize text"""
        # Simplified summarization
        sentences = text.split('. ')
        if len(sentences) <= 3:
            return text
        
        # Take first, middle, and last sentences
        summary_sentences = [sentences[0]]
        if len(sentences) > 1:
            summary_sentences.append(sentences[len(sentences) // 2])
        if len(sentences) > 2:
            summary_sentences.append(sentences[-1])
        
        summary = '. '.join(summary_sentences) + '.'
        
        if len(summary) > max_length:
            summary = summary[:max_length] + '...'
        
        return summary
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get language model statistics"""
        return {
            **self.stats,
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'cache_size': len(self.cache),
            'cache_hit_rate': self.cache_hits / max(1, self.cache_hits + self.cache_misses),
            'active_conversations': len(self.conversations),
            'current_model': self.config.AI_MODEL
        }
    
    def estimate_cost(self, tokens: int) -> float:
        """Estimate cost for token usage"""
        # Rough estimates (prices per 1M tokens)
        model_prices = {
            "mistralai/mistral-7b-instruct:free": 0.0,
            "openai/gpt-3.5-turbo": 1.0,  # $1.0 per 1M tokens
            "openai/gpt-4": 30.0,  # $30 per 1M tokens
        }
        
        price_per_million = model_prices.get(self.config.AI_MODEL, 1.0)
        return (tokens / 1_000_000) * price_per_million