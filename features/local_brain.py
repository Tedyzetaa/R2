import os
import sys
import subprocess

# --- Adicionado para processamento assíncrono correto ---
import asyncio

# --- PROTOCOLO DE AUTO-INSTALAÇÃO DE EMERGÊNCIA ---
try:
    from llama_cpp import Llama
except ImportError:
    print("📦 [BRAIN]: Dependência 'llama-cpp-python' ausente. Iniciando auto-instalação...")
    try:
        # Tenta forçar instalação sem cache para evitar erro [Errno 13]
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "llama-cpp-python", 
            "--no-cache-dir", "--user", "--prefer-binary", "--upgrade"
        ])
        print("✅ [BRAIN]: Instalação concluída. Reiniciando importação...")
        from llama_cpp import Llama
    except Exception as e:
        print(f"❌ [ERRO CRÍTICO]: Falha ao instalar motor neural: {e}")
        Llama = None
# ----------------------------------------------------

class LocalLlamaBrain:
    def __init__(self, config=None):
        # 1. Calcula o caminho exato baseado onde este script está
        # features/local_brain.py -> sobe um nível -> pasta raiz -> models
        current_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(current_dir)
        
        # O caminho que você me passou
        self.model_path = os.path.join(root_dir, "models", "Meta-Llama-3-8B-Instruct.Q4_K_M.gguf")
        
        self.n_ctx = 4096       # Memória de contexto (Llama 3 aguenta até 8k)
        self.n_gpu_layers = 35  # Offload de 35 camadas para GPU. Use -1 para tudo, 0 para CPU.

        print(f"\n🧠 [LOCAL AI]: Inicializando Cérebro On-Premise...")
        print(f"📂 Alvo: {self.model_path}")

        if not os.path.exists(self.model_path):
            print(f"❌ ARQUIVO NÃO ENCONTRADO! Verifique se está em: {self.model_path}")
            self.llm = None
            return

        if Llama:
            try:
                # Carrega o modelo na RAM
                self.llm = Llama(
                    model_path=self.model_path,
                    n_ctx=self.n_ctx,
                    n_gpu_layers=self.n_gpu_layers,
                    verbose=False, # Reduz sujeira no log
                    chat_format="llama-3" # Formata automaticamente para o padrão do Llama 3
                )
                print(f"✅ [LOCAL AI]: Llama-3 Operacional. Tentando offload de {self.n_gpu_layers} camadas para GPU.")
            except Exception as e:
                print(f"❌ [LOCAL AI]: Erro ao carregar na memória: {e}")
                self.llm = None
        else:
            self.llm = None

    async def initialize(self):
        # Método dummy para manter compatibilidade com a GUI antiga
        pass

    async def chat(self, role, prompt):
        """Método simplificado para comandos diretos"""
        history = [{"role": "user", "content": prompt}]
        if role == "system":
            history = [{"role": "system", "content": prompt}]
        return await self.chat_complete(history)

    async def chat_complete(self, history):
        """
        Processa o histórico de chat e retorna a resposta de forma assíncrona.
        """
        if not self.llm:
            return self._criar_resposta_falsa("⚠️ Erro: Cérebro Local não foi carregado corretamente.")

        try:
            # A chamada para a LLM é bloqueante. Usamos run_in_executor
            # para executá-la em uma thread separada e não travar a GUI.
            loop = asyncio.get_running_loop()
            
            def blocking_llm_call():
                return self.llm.create_chat_completion(
                    messages=history,
                    temperature=0.7,
                    max_tokens=600,
                    stop=["<|eot_id|>", "Operador:", "R2:"]
                )

            output = await loop.run_in_executor(None, blocking_llm_call)
            
            texto_resposta = output['choices'][0]['message']['content']
            return self._criar_resposta_falsa(texto_resposta)

        except Exception as e:
            print(f"❌ Erro na inferência: {e}")
            return self._criar_resposta_falsa(f"⚠️ Falha no processamento neural: {e}")

    def _criar_resposta_falsa(self, texto):
        # Cria um objeto simples que tem o atributo .content (para a GUI não quebrar)
        return type('obj', (object,), {'content': texto})