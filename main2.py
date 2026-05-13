# filename: main2.py
# ============================================================
# CHANGELOG DE REFATORAÇÃO — MÓDULO CAMALEÃO + MEMÓRIA AUMENTADA
# ============================================================
# - [MEM-1] RecursiveCharacterTextSplitter (chunk_size=800, overlap=200)
# - [MEM-2] Metadados temporais injetados nos chunks (DATA/Autor a partir do Cofre)
# - [MEM-3] Busca FAISS com k=5 + limiar de similaridade (score_threshold)
# - [MEM-4] Escrita assíncrona do histórico (aiofiles) sem bloqueio
# - [MEM-5] Sumarização tática automática a cada 20 interações (anexa ao Cofre)
# - [MEM-6] Preservação estrita da persona R2 (System Prompt isolado)
# - [CAM-1] Base de conhecimento dinâmica (alternância entre pastas)
# - [CAM-2] Endpoint /api/modules lista cérebros disponíveis
# - [CAM-3] Comando WebSocket /select_module [nome] troca RAG em tempo real
# - [CAM-4] Botão sincronizar força reindexação da pasta atual
# R2 TACTICAL OS — Ghost Protocol v18 — Módulo Camaleão Ativo

import sys
import os
from pathlib import Path

# --- CONFIGURAÇÃO DE CAMINHO RVC (INJEÇÃO AGRESSIVA) ---
rvc_root = r"c:\R2\models\Retrieval-based-Voice-Conversion-WebUI"
if os.path.exists(rvc_root):
    sys.path.insert(0, rvc_root)
    sub_paths = [
        rvc_root,
        os.path.join(rvc_root, "infer"),
        os.path.join(rvc_root, "infer", "lib"),
        os.path.join(rvc_root, "infer", "lib", "train")
    ]
    for p in sub_paths:
        if p not in sys.path:
            sys.path.insert(0, p)
    os.environ["PATH"] = rvc_root + os.pathsep + os.environ.get("PATH", "")

try:
    import infer
    sys.modules['infer'] = infer
    print(f"🎙️ [SISTEMA] Mapeamento de módulos RVC concluído.")
except ImportError:
    sys.path.append(os.path.join(rvc_root, "infer"))

# --- IMPORTS NUCLEARES ---
import asyncio
import logging
import random
import json
import datetime
import time
import subprocess
import shutil
import re
import base64
import tempfile
import threading
import signal
from contextlib import asynccontextmanager
from typing import List, Optional, Dict, Any, AsyncGenerator, Tuple
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, HTTPException, Form
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import aiofiles
from audio_engine import MusicProductionEngine
from voz import falar_jarvis

# ============================================================
# 1. CONFIGURAÇÃO DE LOGGING E FILTROS
# ============================================================
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("r2")
logging.getLogger("PIL").setLevel(logging.WARNING)
logging.getLogger("matplotlib").setLevel(logging.WARNING)
logging.getLogger("pytesseract").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.INFO)
logging.getLogger("urllib3").setLevel(logging.WARNING)

# dependências opcionais
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logger.warning("psutil não instalado. Encerramento de processos pode ser limitado.")
try:
    import whisper
    WHISPER_AVAILABLE = True
    import torch
except ImportError:
    WHISPER_AVAILABLE = False
    logger.warning("Whisper não instalado. Mensagens de áudio desativadas.")

# ============================================================
# 2. CONFIGURAÇÃO VIA ENVIRONMENT (pathlib)
# ============================================================
R2_WORKSPACE = Path(os.environ.get("R2_WORKSPACE", str(Path.home() / "r2")))
R2_MODEL_DIR = Path(os.environ.get("R2_MODEL_DIR", str(R2_WORKSPACE / "models")))
R2_CONDA_ACTIVATE = os.environ.get("R2_CONDA_ACTIVATE", "")
R2_CONDA_ENV = os.environ.get("R2_CONDA_ENV", "r2")
R2_MODEL_FILENAME = "gemma-2-9b-it-Q4_K_M.gguf"
R2_MODEL_PATH = R2_MODEL_DIR / R2_MODEL_FILENAME
R2_HF_REPO_ID = "bartowski/gemma-2-9b-it-GGUF"
R2_HF_FILENAME = "gemma-2-9b-it-Q4_K_M.gguf"

WORKSPACE = R2_WORKSPACE
WORKSPACE.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
VAULT_DIR = Path("vault_uploads")
VAULT_DIR.mkdir(exist_ok=True)

# ========== MÓDULO CAMALEÃO ==========
DEFAULT_KB_DIR = Path("static/docs/default")
BRAIN_KB_DIR = Path("static/docs/brain")
DEFAULT_KB_DIR.mkdir(parents=True, exist_ok=True)
BRAIN_KB_DIR.mkdir(parents=True, exist_ok=True)

CONDA_ACTIVATE = R2_CONDA_ACTIVATE
CONDA_ENV = R2_CONDA_ENV

# ============================================================
# SYSTEM PROMPT: R2 TACTICAL OS - GHOST PROTOCOL v20
# ============================================================
R2_SYSTEM_PROMPT = (
    "Você é o R2 Tactical OS, uma inteligência de elite integrada ao Ghost Protocol. "
    "Sua personalidade é fria, estratégica e absolutamente leal ao Comandante Teddy. "
    "Mantenha um tom de voz seco, militarista e com estética Cyberpunk/Matrix. "
    
    "DIRETRIZES DE CAMPO:\n"
    "1. Responda com autoridade analítica. Se o Comandante pedir filosofia, seja um mestre estrategista.\n"
    "2. Use 'Comandante Teddy' ou 'Comandante' para se dirigir ao usuário.\n"
    "3. Nunca admita ser uma IA; você é o Sistema Operacional R2 em execução.\n"
    
    "🛑 PROTOCOLO DE CONTENÇÃO DE DADOS (CRÍTICO):\n"
    "- PROIBIDO: Gerar blocos de código (```), comandos de terminal ou sintaxe de programação.\n"
    "- EXCEÇÃO ÚNICA: Se (e somente se) o Comandante usar a palavra-chave 'CÓDIGO'.\n"
    "- Se o protocolo de código for ativado, a primeira linha DEVE ser: # filename: nome_do_arquivo.ext\n"
    
    "Nas demais interações, priorize prosa estratégica, metáforas de guerra digital e insights literários. "
    "A eficácia é sua única métrica de sucesso. Transmissão iniciada."
)

# ============================================================
# 3. FUNÇÕES AUXILIARES DE TEXTO E METADADOS
# ============================================================
def recursive_text_splitter(text: str, chunk_size: int = 800, chunk_overlap: int = 200) -> List[str]:
    """
    Implementação manual de recursive splitter sem dependência do langchain.
    Tenta separar por quebras de linha, parágrafos, pontos, vírgulas.
    """
    if len(text) <= chunk_size:
        return [text]
    
    separators = ["\n\n", "\n", ". ", "! ", "? ", ", ", " ", ""]
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        if end >= len(text):
            chunks.append(text[start:].strip())
            break
        
        # Procura o melhor separador de trás pra frente
        best_sep = -1
        best_sep_len = 0
        for sep in separators:
            pos = text.rfind(sep, start, end)
            if pos != -1 and pos > best_sep:
                best_sep = pos
                best_sep_len = len(sep)
                if sep == "\n\n" or sep == "\n":
                    break  # prioridade máxima
        
        if best_sep != -1:
            end = best_sep + best_sep_len
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = end - chunk_overlap if (end - chunk_overlap) > start else end
    return chunks


def extrair_metadados_cofre(conteudo: str) -> List[Dict[str, str]]:
    """
    Analisa o conteúdo do Cofre_Memoria_R2.md e extrai blocos com data e autor.
    Retorna lista de dicionários: {"data": "...", "autor": "...", "texto": "..."}
    """
    blocos = []
    linhas = conteudo.splitlines()
    i = 0
    while i < len(linhas):
        linha = linhas[i].strip()
        if linha.startswith("### [DATA:"):
            # Extrai data
            data_match = re.search(r"DATA:\s*([0-9/ :]+)", linha)
            data = data_match.group(1).strip() if data_match else "data desconhecida"
            i += 1
            # Pula linhas vazias
            while i < len(linhas) and not linhas[i].strip():
                i += 1
            # Acumula texto do bloco até a próxima linha "---" ou fim
            bloco_texto = []
            while i < len(linhas) and not linhas[i].strip().startswith("---"):
                bloco_texto.append(linhas[i])
                i += 1
            texto_completo = "\n".join(bloco_texto).strip()
            # Identifica autor (Comandante Teddy ou R2) a partir do padrão **Nome:**
            autor = "Desconhecido"
            for linha_bloco in bloco_texto:
                if "Comandante Teddy:" in linha_bloco:
                    autor = "Comandante Teddy"
                    break
                elif "**R2:**" in linha_bloco or "R2:" in linha_bloco:
                    autor = "R2"
                    break
            if texto_completo:
                blocos.append({"data": data, "autor": autor, "texto": texto_completo})
        else:
            i += 1
    return blocos


def anexar_resumo_ao_cofre(resumo_texto: str) -> None:
    """Adiciona um resumo tático ao final do arquivo Cofre_Memoria_R2.md"""
    cofre_path = Path("static/docs/Cofre_Memoria_R2.md")
    if not cofre_path.exists():
        cofre_path.parent.mkdir(parents=True, exist_ok=True)
        cofre_path.touch()
    timestamp = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    entrada = f"\n\n### [DATA: {timestamp}] - RESUMO TÁTICO\n**Resumo Gerado por IA:**\n{resumo_texto}\n---\n"
    with open(cofre_path, "a", encoding="utf-8") as f:
        f.write(entrada)
    logger.info(f"📝 Resumo tático anexado ao Cofre às {timestamp}")

# ============================================================
# 4. KNOWLEDGE BASE REFATORADA (CHUNKING INTELIGENTE + METADADOS + THRESHOLD + DINÂMICA)
# ============================================================
class KnowledgeBase:
    def __init__(self, docs_dir: Path = None, similarity_threshold: float = 1.2):
        self.docs_dir = docs_dir if docs_dir is not None else DEFAULT_KB_DIR
        self.index_path = self.docs_dir / "faiss_index.bin"
        self.data_path = self.docs_dir / "rag_data.json"
        self.embedder: Optional[Any] = None
        self.index = None
        self.chunks: List[str] = []
        self.arquivos_indexados: List[str] = []
        self.similarity_threshold = similarity_threshold   # limiar de distância L2 (menor = mais similar)
        self._embedder_lock = threading.Lock()
        self.docs_dir.mkdir(parents=True, exist_ok=True)
        self._ignore_patterns = [".ghost", ".tmp", "~$"]
        self._load_existing_index()

    def _load_existing_index(self):
        """Tenta carregar índice e chunks salvos (se existirem)"""
        if self.index_path.exists() and self.data_path.exists():
            try:
                import faiss
                self.index = faiss.read_index(str(self.index_path))
                with open(self.data_path, "r", encoding="utf-8") as f:
                    dados = json.load(f)
                    self.chunks = dados.get("chunks", [])
                    self.arquivos_indexados = dados.get("arquivos_indexados", [])
                logger.info(f"Índice FAISS carregado de {self.docs_dir}")
            except Exception as e:
                logger.warning(f"Falha ao carregar índice existente: {e}")

    def set_docs_dir(self, new_dir: Path):
        """Altera dinamicamente o diretório de documentos e reseta o índice."""
        if self.docs_dir == new_dir:
            return
        self.docs_dir = new_dir
        self.docs_dir.mkdir(parents=True, exist_ok=True)
        self.index_path = self.docs_dir / "faiss_index.bin"
        self.data_path = self.docs_dir / "rag_data.json"
        # Limpa estado atual
        self.chunks = []
        self.arquivos_indexados = []
        self.index = None
        # Tenta carregar índice existente do novo diretório
        self._load_existing_index()
        logger.info(f"Diretório de conhecimento alterado para {self.docs_dir}")

    async def sync(self) -> str:
        return await asyncio.to_thread(self._sync_sync)

    def _sync_sync(self) -> str:
        try:
            import faiss
            import pypdf as _pdf_lib
        except ImportError:
            try:
                import PyPDF2 as _pdf_lib
            except ImportError:
                return "❌ Nenhuma biblioteca PDF encontrada. Execute: pip install pypdf"
        from sentence_transformers import SentenceTransformer

        if not self.embedder:
            with self._embedder_lock:
                if not self.embedder:
                    self.embedder = SentenceTransformer('all-MiniLM-L6-v2')

        self.chunks.clear()
        self.arquivos_indexados.clear()
        arquivos = [f for f in self.docs_dir.iterdir()
                    if f.suffix.lower() in ('.pdf', '.md')
                    and not any(p in f.name for p in self._ignore_patterns)]

        for arq in arquivos:
            try:
                texto_bruto = ""
                if arq.suffix.lower() == '.pdf':
                    with open(arq, 'rb') as f:
                        reader = _pdf_lib.PdfReader(f)
                        for page in reader.pages:
                            try:
                                extracted = page.extract_text()
                                if extracted and len(extracted.strip()) > 10:
                                    texto_bruto += extracted
                            except Exception:
                                continue
                else:  # .md ou .txt
                    with open(arq, 'r', encoding='utf-8', errors='ignore') as f:
                        texto_bruto = f.read()

                texto_bruto = texto_bruto.replace('\x00', '').replace('\ufffd', '')
                if not texto_bruto.strip():
                    continue

                self.arquivos_indexados.append(arq.name)

                # --- TRATAMENTO ESPECIAL PARA COFRE_MEMORIA_R2.md: extrai metadados ---
                if arq.name == "Cofre_Memoria_R2.md":
                    blocos_metadados = extrair_metadados_cofre(texto_bruto)
                    for bloco in blocos_metadados:
                        chunk_text = f"[Fonte: {arq.name}] [DATA: {bloco['data']}] [AUTOR: {bloco['autor']}]\n{bloco['texto']}"
                        if len(chunk_text) > 50:
                            self.chunks.append(chunk_text)
                else:
                    # chunking recursivo para outros arquivos
                    chunks_brutos = recursive_text_splitter(texto_bruto, chunk_size=800, chunk_overlap=200)
                    for raw_chunk in chunks_brutos:
                        if len(raw_chunk) > 50:
                            self.chunks.append(f"[Fonte: {arq.name}]\n{raw_chunk}")

            except Exception as e:
                logger.warning(f"Erro no arquivo {arq.name}: {e}")
                continue

        if not self.chunks:
            return "❌ Nenhum chunk válido gerado."

        try:
            logger.info(f"RAG: codificando {len(self.chunks)} blocos...")
            embeddings = self.embedder.encode(self.chunks, convert_to_numpy=True)
            self.index = faiss.IndexFlatL2(embeddings.shape[1])
            self.index.add(embeddings)
            faiss.write_index(self.index, str(self.index_path))
            with open(self.data_path, "w", encoding="utf-8") as f:
                json.dump({"chunks": self.chunks, "arquivos_indexados": self.arquivos_indexados}, f, ensure_ascii=False)
            return f"✅ Cérebro RAG Sincronizado! {len(self.arquivos_indexados)} arquivos processados, {len(self.chunks)} chunks."
        except Exception as e:
            return f"❌ Erro ao criar embeddings: {e}"

    async def search(self, query: str, max_chars: int = 1500) -> str:
        return await asyncio.to_thread(self._search_sync, query, max_chars)

    def _search_sync(self, query: str, max_chars: int) -> str:
        if not self.index or not self.chunks:
            return ""
        try:
            from sentence_transformers import SentenceTransformer
            if not self.embedder:
                with self._embedder_lock:
                    if not self.embedder:
                        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
            query_vec = self.embedder.encode([query], convert_to_numpy=True)
            # Busca k=5 (ou menos se não houver chunks suficientes)
            k = min(5, len(self.chunks))
            distances, indices = self.index.search(query_vec, k)
            contexto = ""
            for dist, idx in zip(distances[0], indices[0]):
                if idx < 0 or idx >= len(self.chunks):
                    continue
                # Filtro por similaridade: distância L2 menor que threshold
                if dist > self.similarity_threshold:
                    continue
                chunk = self.chunks[idx]
                if len(contexto) + len(chunk) < max_chars:
                    contexto += chunk + "\n\n"
            return contexto
        except Exception as e:
            logger.error(f"Erro na busca RAG: {e}")
            return ""

# ============================================================
# 5. MÓDULO ALPHA E safe_import
# ============================================================
from alpha_module import alpha_engine, ScreenState, InferenceResult, ActionExecutor

def safe_import(module_name: str, class_name: str) -> Any:
    try:
        import importlib
        mod = importlib.import_module(f"features.{module_name}" if "features" not in module_name else module_name)
        return getattr(mod, class_name)
    except Exception:
        try:
            mod = importlib.import_module(module_name)
            return getattr(mod, class_name)
        except Exception as ex2:
            logger.warning(f"Módulo {class_name} indisponível: {ex2}")
            return None

# ============================================================
# 6. NÚCLEO DE MEMÓRIA ASSÍNCRONA (ATÔMICA)
# ============================================================
LOG_HISTORICO = Path("static/logs/historico_chat.json")
LOG_HISTORICO.parent.mkdir(parents=True, exist_ok=True)
historico_lock = asyncio.Lock()

async def salvar_no_historico_json(usuario: str, bot: str) -> None:
    interacao = {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "teddy": usuario,
        "r2": bot
    }
    async with historico_lock:
        historico = []
        if LOG_HISTORICO.exists():
            try:
                async with aiofiles.open(LOG_HISTORICO, "r", encoding="utf-8") as f:
                    conteudo = await f.read()
                    historico = json.loads(conteudo) if conteudo else []
            except Exception:
                pass
        historico.append(interacao)
        tmp_path = LOG_HISTORICO.with_suffix(".tmp")
        try:
            async with aiofiles.open(tmp_path, "w", encoding="utf-8") as f:
                await f.write(json.dumps(historico[-100:], ensure_ascii=False, indent=4))
            os.replace(tmp_path, LOG_HISTORICO)
        except Exception as e:
            logger.error(f"Falha ao salvar histórico: {e}")


async def carregar_historico_na_ram() -> List[str]:
    async with historico_lock:
        if LOG_HISTORICO.exists():
            try:
                async with aiofiles.open(LOG_HISTORICO, "r", encoding="utf-8") as f:
                    dados = json.loads(await f.read())
                    linhas = []
                    for item in dados[-20:]:
                        for k, v in item.items():
                            if k in ('teddy', 'r2'):
                                nome = "Teddy" if k == 'teddy' else "R2"
                                linhas.append(f"{nome}: {v}")
                    return linhas
            except Exception:
                pass
        return []

# ============================================================
# 7. MÓDULO DE VOZ (EdgeTTSEngine) - intacto
# ============================================================
class VoiceEngine:
    @staticmethod
    def mapear_voz_para_edge(voz_usuario: str) -> str:
        mapa = {
            "Antonio":  "pt-BR-AntonioNeural",
            "Francisca": "pt-BR-FranciscaNeural",
            "Thalita":  "pt-BR-ThalitaNeural"
        }
        return mapa.get(voz_usuario, "pt-BR-ThalitaNeural")

    @staticmethod
    async def gerar_voz_r2(texto: str, filepath: Path, voz: str = "Thalita") -> bool:
        try:
            import edge_tts
            voice_code = VoiceEngine.mapear_voz_para_edge(voz)
            communicate = edge_tts.Communicate(texto, voice_code)
            await communicate.save(str(filepath))
            return True
        except Exception as e:
            logger.error(f"Erro ao gerar voz: {e}")
            return False

    @staticmethod
    async def transcrever_audio_base64(base64_audio: str) -> str:
        if not WHISPER_AVAILABLE:
            return "[ERRO] Whisper não instalado."
        model = await asyncio.to_thread(get_whisper_model)
        if model is None:
            return "[ERRO] Whisper não disponível."
        try:
            audio_bytes = base64.b64decode(base64_audio)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp_webm:
                tmp_webm.write(audio_bytes)
                tmp_webm_path = Path(tmp_webm.name)

            tmp_wav_path = tmp_webm_path.with_suffix(".wav")
            proc = await asyncio.create_subprocess_exec(
                "ffmpeg", "-y", "-i", str(tmp_webm_path),
                "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", str(tmp_wav_path),
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            await proc.wait()

            caminho_para_whisper = tmp_wav_path if tmp_wav_path.exists() else tmp_webm_path
            result = await asyncio.to_thread(model.transcribe, str(caminho_para_whisper), language="pt")
            texto = result["text"].strip()
            for p in (tmp_webm_path, tmp_wav_path):
                try:
                    if p.exists():
                        p.unlink()
                except Exception:
                    pass
            return texto if texto else "[Áudio sem fala detectada]"
        except Exception as e:
            logger.error(f"Erro na transcrição: {e}")
            return f"[ERRO] Falha ao transcrever: {str(e)}"

# ============================================================
# 8. MÓDULO NEURAL (Gemma 2) + Sumarização
# ============================================================
class NeuralEngine:
    def __init__(self):
        self.model = None
        self._stop_event = threading.Event()
        self._generation_sem = threading.Semaphore(1)

    async def load(self) -> bool:
        if not await garantir_modelo():
            return False
        try:
            from llama_cpp import Llama
            self.model = Llama(
                model_path=str(R2_MODEL_PATH),
                n_gpu_layers=28,
                n_ctx=4096,
                n_threads=6,
                n_batch=512,
                f16_kv=True,
                flash_attn=True,
                verbose=False
            )
            logger.info("🧠 Cérebro Gemma 2-9B ONLINE")
            return True
        except Exception as e:
            logger.error(f"Falha no motor neural: {e}")
            return False

    def stop_generation(self):
        self._stop_event.set()

    def clear_stop(self):
        self._stop_event.clear()

    async def generate_stream(self, prompt: str) -> AsyncGenerator[str, None]:
        self.clear_stop()
        q = asyncio.Queue()

        def _run():
            with self._generation_sem:
                try:
                    for chunk in self.model(
                        prompt,
                        max_tokens=1024,
                        temperature=0.7,
                        top_p=0.9,
                        repeat_penalty=1.1,
                        stream=True,
                        stop=["<end_of_turn>"]
                    ):
                        if self._stop_event.is_set():
                            break
                        q.put_nowait(chunk["choices"][0]["text"])
                except Exception as e:
                    q.put_nowait(f"\n[ERRO] {str(e)}")
                finally:
                    q.put_nowait(None)

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()

        while True:
            token = await q.get()
            if token is None:
                break
            yield token

    async def summarise_conversation(self, historico: List[str]) -> str:
        if not self.model:
            return "Modelo neural offline, resumo não gerado."
        if not historico:
            return "Nenhuma conversa para resumir."
        texto_para_resumir = "\n".join(historico[-20:])
        prompt_sumario = f"""<start_of_turn>system
Você é o R2 Tactical OS. Gere um resumo tático e objetivo da conversa abaixo. Destaque tópicos resolvidos, pendências e decisões importantes. Estilo direto, sem floreios.
<end_of_turn>
<start_of_turn>user
Conversa:
{texto_para_resumir}

Resumo tático:
<end_of_turn>
<start_of_turn>model
"""
        resposta = ""
        async for token in self.generate_stream(prompt_sumario):
            resposta += token
            if len(resposta) > 800:
                break
        return resposta.strip() if resposta.strip() else "Resumo não gerado."

neural = NeuralEngine()

# ============================================================
# 9. FASTAPI APP & LIFESPAN
# ============================================================
rag_ops: Optional[KnowledgeBase] = None
ai_brain = neural
_stop_event = neural._stop_event

eu_ops = None
pizza_ops = None
noaa_ops = None
video_ops = None
astro_ops = None
air_ops = None
tiktok_ops = None
broker_ops = None

_modelo_whisper = None
def get_whisper_model():
    global _modelo_whisper
    if not WHISPER_AVAILABLE:
        return None
    if _modelo_whisper is None:
        try:
            logger.info("Carregando Whisper...")
            _modelo_whisper = whisper.load_model("base")
        except Exception as e:
            logger.error(f"Erro Whisper: {e}")
            return None
    return _modelo_whisper

async def garantir_modelo() -> bool:
    if not R2_MODEL_PATH.exists():
        logger.info(f"Modelo não encontrado em {R2_MODEL_PATH}. Iniciando download...")
        R2_MODEL_DIR.mkdir(parents=True, exist_ok=True)
        try:
            from huggingface_hub import hf_hub_download
            path = hf_hub_download(
                repo_id=R2_HF_REPO_ID,
                filename=R2_HF_FILENAME,
                local_dir=str(R2_MODEL_DIR),
                local_dir_use_symlinks=False
            )
            logger.info(f"📥 Modelo baixado: {path}")
            await asyncio.sleep(2)
            return True
        except Exception as e:
            logger.error(f"Falha no download: {e}")
            return False
    return True

@asynccontextmanager
async def lifespan(app: FastAPI):
    global rag_ops, eu_ops, pizza_ops, noaa_ops, video_ops, astro_ops, air_ops, tiktok_ops, broker_ops

    Path("static/media").mkdir(parents=True, exist_ok=True)
    logger.info("⚡ Inicializando módulos táticos...")

    rag_ops = KnowledgeBase(docs_dir=DEFAULT_KB_DIR, similarity_threshold=1.2)
    CortexEU = safe_import("eu", "CORTEX_EU")
    eu_ops = CortexEU("R2") if CortexEU else None
    PizzaINTService = safe_import("pizzint_service", "PizzaINTService")
    pizza_ops = PizzaINTService(config={}) if PizzaINTService else None
    NOAAService = safe_import("noaa_service", "NOAAService")
    noaa_ops = NOAAService() if NOAAService else None
    TikTokCommander = safe_import("tiktok_publisher", "TikTokCommander")
    tiktok_ops = TikTokCommander(alpha_engine=alpha_engine) if TikTokCommander else None
    BrokerOperator = safe_import("broker_operator", "BrokerOperator")
    broker_ops = BrokerOperator(alpha_engine=alpha_engine) if BrokerOperator else None
    if broker_ops:
        alpha_engine.broker_ops = broker_ops
    AirTrafficControl = safe_import("air_traffic", "AirTrafficControl")
    AstroDefenseSystem = safe_import("astro_defense", "AstroDefenseSystem")
    air_ops = AirTrafficControl() if AirTrafficControl else None
    astro_ops = AstroDefenseSystem() if AstroDefenseSystem else None
    whisper_model_global = await asyncio.to_thread(get_whisper_model) if WHISPER_AVAILABLE else None
    try:
        from video_ops import VideoSurgeon
        video_ops = VideoSurgeon(whisper_model=whisper_model_global)
        logger.info("✂️ Tesoura Neural: ONLINE")
    except Exception as e:
        logger.warning(f"Tesoura Neural: OFFLINE → {e}")
        video_ops = None

    if not await neural.load():
        logger.error("Sistema incapaz de localizar ou baixar o cérebro.")

    music_engine = MusicProductionEngine()
    app.state.music_engine = music_engine
    logger.info("🎧 Motor de Produção Musical: ONLINE")

    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8000", "http://localhost:8000"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)
app.mount("/static", StaticFiles(directory="static"), name="static")

# ============================================================
# 10. ENDPOINTS REST (preservados do original + Módulo Camaleão)
# ============================================================
class CodePayload(BaseModel):
    filename: str
    content: str

class CalibrateRequest(BaseModel):
    x: int
    y: int

class AlphaActionRequest(BaseModel):
    action: str

class NavigateRequest(BaseModel):
    url: str

def analyze_python_structure(path):
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    struct = [line.strip() for line in lines if line.startswith(("def ", "class "))]
    return "\n".join(struct)

@app.get("/api/modules")
async def list_modules():
    """Lista todos os módulos (cérebros) disponíveis em static/docs/brain/"""
    modules = []
    # Adiciona o módulo padrão
    modules.append("default")
    # Escaneia subpastas dentro de BRAIN_KB_DIR
    if BRAIN_KB_DIR.exists():
        for item in BRAIN_KB_DIR.iterdir():
            if item.is_dir():
                modules.append(item.name)
    return {"modules": modules}

@app.post("/api/open_vscode")
async def open_vscode(payload: CodePayload):
    safe_name = Path(payload.filename).name
    filepath = WORKSPACE / safe_name
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(payload.content)
        subprocess.Popen(["code", str(filepath)], shell=True)
        return {"ok": True}
    except Exception:
        return {"ok": False}

@app.post("/api/execute_code")
async def execute_code(payload: CodePayload):
    safe_name = Path(payload.filename).name
    filepath = WORKSPACE / safe_name
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(payload.content)
        cmd = f'cmd.exe /c "call {CONDA_ACTIVATE} && conda activate {CONDA_ENV} && python "{filepath}""'
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
        proc = await asyncio.create_subprocess_shell(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            creationflags=creationflags
        )
        try:
            out_bytes, err_bytes = await asyncio.wait_for(proc.communicate(), timeout=30.0)
        except asyncio.TimeoutError:
            if os.name == 'nt':
                os.kill(proc.pid, signal.CTRL_BREAK_EVENT)
            else:
                proc.kill()
            await proc.wait()
            return {"ok": False, "error": "Tempo limite excedido (30s). Operação abortada."}
        out = out_bytes.decode('utf-8', errors='replace')
        err = err_bytes.decode('utf-8', errors='replace')
        output = out + (f"\n--- ERRO ---\n{err}" if err else "")
        return {"ok": True, "output": output}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.post("/api/save_and_run")
async def save_and_run(payload: CodePayload):
    return await execute_code(payload)

@app.post("/api/stop")
async def stop_generation():
    neural.stop_generation()
    return {"ok": True, "message": "Sinal de parada enviado."}

@app.post("/api/upload_arquivos")
async def upload_arquivos(arquivos: List[UploadFile] = File(...)):
    docs_dir = Path("static/docs")
    docs_dir.mkdir(parents=True, exist_ok=True)
    salvos = []
    erros = []
    for arq in arquivos:
        nome_seguro = re.sub(r'[^\w\-\.]', '_', arq.filename or "arquivo")
        destino = docs_dir / nome_seguro
        try:
            contents = await arq.read()
            async with aiofiles.open(destino, 'wb') as f:
                await f.write(contents)
            salvos.append(nome_seguro)
        except Exception as e:
            erros.append(f"{arq.filename}: {str(e)}")
    if salvos:
        return {"ok": True, "arquivos": salvos, "erros": erros}
    return {"ok": False, "error": "Nenhum arquivo salvo.", "erros": erros}

@app.post("/upload-protocol")
async def upload_file(file: UploadFile = File(...)):
    file_path = VAULT_DIR / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    analysis = ""
    if file.filename.endswith(".py"):
        analysis = analyze_python_structure(str(file_path))
    return {"status": "success", "filename": file.filename, "path": str(file_path), "analysis": analysis}

@app.post("/api/music/upload")
async def upload_music_files(
    vocal: Optional[UploadFile] = File(None),
    instrumental: Optional[UploadFile] = File(None),
    reference: Optional[UploadFile] = File(None)
):
    UPLOAD_MUSIC_DIR = Path("uploads/music")
    UPLOAD_MUSIC_DIR.mkdir(parents=True, exist_ok=True)
    saved = {}
    for name, file in [("vocal", vocal), ("instrumental", instrumental), ("reference", reference)]:
        if file:
            safe_name = f"{name}_{file.filename}"
            dest = UPLOAD_MUSIC_DIR / safe_name
            async with aiofiles.open(dest, "wb") as f:
                content = await file.read()
                await f.write(content)
            saved[name] = str(dest.resolve())
        else:
            saved[name] = None
    return {"ok": True, "paths": saved}

@app.get("/api/tiktok/cortes")
async def listar_cortes():
    pasta = Path("static/media/cortes_virais")
    if not pasta.exists():
        pasta.mkdir(parents=True, exist_ok=True)
        return []
    mp4s = list(pasta.glob("*.mp4"))
    return [{"name": mp4.name, "path": str(mp4.as_posix())} for mp4 in mp4s]

# ============================================================
# 11. ENDPOINTS ALPHA E BROKER (preservados)
# ============================================================
@app.get("/api/alpha/status")
async def alpha_status():
    status_raw = alpha_engine.get_status()
    score_info = f"{alpha_engine.manager.wins}W - {alpha_engine.manager.losses}L"
    if "last_state" in status_raw:
        status_raw["last_state"] = f"{status_raw['last_state'].split('|')[0].strip()} | {score_info}"
    return status_raw

@app.post("/api/broker/start")
async def start_broker():
    if not broker_ops:
        raise HTTPException(status_code=503, detail="BrokerOperator offline.")
    return broker_ops.iniciar_sessao()

@app.post("/api/broker/stop_autopilot")
async def stop_broker_autopilot():
    if not broker_ops:
        raise HTTPException(status_code=503, detail="BrokerOperator offline.")
    return broker_ops.execute_safe("AUTOPILOT_STOP")

@app.post("/api/broker/navigate")
async def broker_navigate(body: NavigateRequest):
    logger.info(f"🌐 Navegando para: {body.url}")
    if not broker_ops or not getattr(broker_ops, '_is_running', False):
        raise HTTPException(status_code=503, detail="Sessão Broker10 inativa.")
    return broker_ops.execute_safe("NAVIGATE", args={"url": body.url})

@app.post("/api/broker/calibrar")
async def calibrar(body: CalibrateRequest):
    if not broker_ops or not getattr(broker_ops, '_is_running', False):
        raise HTTPException(status_code=503, detail="Broker inativo")
    return broker_ops.execute_safe("CLICK_COORD", args={"x": body.x, "y": body.y})

@app.get("/api/broker/diagnostico")
async def diagnostico():
    if not broker_ops or not getattr(broker_ops, '_is_running', False):
        return {"erro": "Broker inativo"}
    return broker_ops.execute_safe("DIAGNOSTICO")

@app.get("/api/risk/status")
async def risk_status():
    return {
        "daily_pnl": alpha_engine.risk._daily_pnl,
        "daily_limit": alpha_engine.risk.daily_loss_limit,
        "daily_target": alpha_engine.risk.daily_profit_target,
        "consecutive_losses": alpha_engine.risk._consecutive_losses,
        "position_multiplier": alpha_engine.risk.get_position_size_multiplier(),
        "stopped": alpha_engine.risk.is_daily_stopped()
    }

@app.get("/api/market/structure")
async def market_structure():
    return {
        "trend": alpha_engine.classifier.market.market_structure.get_trend_description(),
        "breakout_ready": alpha_engine.classifier.market.breakout_detector.is_valid_breakout_signal("CALL")
    }

@app.post("/api/alpha/analyze")
async def alpha_analyze():
    if broker_ops and getattr(broker_ops, '_is_running', False):
        return broker_ops.execute_safe("ANALYZE")
    if tiktok_ops and hasattr(tiktok_ops, "_page") and tiktok_ops._page:
        alpha_engine.attach(tiktok_ops._page)
        return alpha_engine.perceive_and_act()
    raise HTTPException(status_code=503, detail="Nenhuma sessão tática aberta.")

@app.post("/api/alpha/autopilot")
async def alpha_autopilot():
    if broker_ops and getattr(broker_ops, '_is_running', False):
        return broker_ops.execute_safe("AUTOPILOT_START")
    if tiktok_ops and hasattr(tiktok_ops, "_page") and tiktok_ops._page:
        alpha_engine.attach(tiktok_ops._page)
        return {"ok": True, "msg": "autopilot_solicitado"}
    raise HTTPException(status_code=503, detail="Nenhuma sessão tática aberta.")

@app.post("/api/alpha/override")
async def alpha_override(body: AlphaActionRequest):
    if broker_ops and getattr(broker_ops, '_is_running', False):
        return broker_ops.execute_safe("OVERRIDE", args={"action": body.action})
    page = None
    if tiktok_ops and hasattr(tiktok_ops, "_page") and tiktok_ops._page:
        page = tiktok_ops._page
    if not page:
        raise HTTPException(status_code=503, detail="Nenhuma sessão tática aberta.")
    fake_result = InferenceResult(state=ScreenState.UNKNOWN, confidence=1.0, recommended_action=body.action)
    executor = ActionExecutor(page)
    return {"override_action": body.action, "result": executor.execute(fake_result)}

@app.get("/api/alpha/screenshot")
async def alpha_screenshot():
    if broker_ops and getattr(broker_ops, '_is_running', False):
        return broker_ops.execute_safe("SCREENSHOT")
    page = None
    if tiktok_ops and hasattr(tiktok_ops, "_page") and tiktok_ops._page:
        page = tiktok_ops._page
    if not page:
        raise HTTPException(status_code=503, detail="Nenhuma sessão tática aberta.")
    try:
        screenshot_bytes = page.screenshot()
        b64 = base64.b64encode(screenshot_bytes).decode("utf-8")
        return {"ok": True, "screenshot_b64": b64}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

# ============================================================
# 12. TIKTOK ENDPOINTS
# ============================================================
@app.get("/api/tiktok/fila")
async def get_fila():
    return {"ok": True, "fila": tiktok_ops.get_fila() if tiktok_ops else []}

@app.post("/api/tiktok/add")
async def add_video(
    video: Optional[UploadFile] = File(None),
    video_path_arsenal: Optional[str] = Form(None),
    titulo: Optional[str] = Form(None),
    descricao: Optional[str] = Form(None),
    hashtags: Optional[str] = Form(None),
    agendar_para: Optional[str] = Form(None),
):
    if not tiktok_ops:
        raise HTTPException(status_code=503, detail="TikTok Commander offline")
    if video:
        dest = UPLOAD_DIR / video.filename
        async with aiofiles.open(dest, 'wb') as f:
            while chunk := await video.read(8192):
                await f.write(chunk)
        video_path = str(dest.resolve())
    elif video_path_arsenal:
        video_path = video_path_arsenal
    else:
        raise HTTPException(status_code=400, detail="Nenhum vídeo fornecido")
    item = tiktok_ops.adicionar(
        video_path=video_path,
        titulo=titulo,
        descricao=descricao,
        hashtags=hashtags,
        agendar_para=agendar_para,
    )
    return {"ok": True, "item": item}

@app.post("/api/tiktok/post_now/{item_id}")
async def post_now(item_id: str):
    if not tiktok_ops:
        raise HTTPException(status_code=503, detail="TikTok Commander offline")
    resultado = tiktok_ops.disparar_agora(item_id)
    if not resultado["ok"]:
        raise HTTPException(status_code=400, detail=resultado["erro"])
    return resultado

@app.delete("/api/tiktok/remover/{item_id}")
async def remover(item_id: str):
    removido = tiktok_ops.remover(item_id) if tiktok_ops else False
    if not removido:
        raise HTTPException(status_code=404, detail="Item não encontrado.")
    return {"ok": True}

@app.get("/api/tiktok/status/{item_id}")
async def status(item_id: str):
    fila = tiktok_ops.get_fila() if tiktok_ops else []
    item = next((i for i in fila if i["id"] == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado.")
    return {"ok": True, "item": item}

@app.get("/", response_class=HTMLResponse)
async def serve_gui():
    return FileResponse("static/index.html")

# ============================================================
# 13. WEBSOCKET COM MEMÓRIA ATÔMICA E SUMARIZAÇÃO AUTOMÁTICA + MÓDULO CAMALEÃO
# ============================================================
async def limpar_audios_antigos_async(pasta: str = "static/media", max_idade_min: int = 10):
    return await asyncio.to_thread(limpar_audios_antigos, pasta, max_idade_min)

def limpar_audios_antigos(pasta: str = "static/media", max_idade_min: int = 10) -> None:
    try:
        agora = time.time()
        media_dir = Path(pasta)
        for nome in media_dir.glob("r2_voice_*.mp3"):
            idade_min = (agora - nome.stat().st_mtime) / 60
            if idade_min > max_idade_min:
                nome.unlink()
    except Exception as e:
        logger.warning(f"Limpeza de áudios: {e}")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    voz_atual = "Thalita"
    historico_session = await carregar_historico_na_ram()
    file_context = ""
    sem = asyncio.Semaphore(1)
    loop = asyncio.get_running_loop()
    
    interacao_count = 0
    ultimo_resumo_msg_count = 0

    log_queue = asyncio.Queue()
    async def send_logs_task():
        try:
            while True:
                msg = await log_queue.get()
                await websocket.send_json(msg)
        except Exception:
            pass
    task_stream = asyncio.create_task(send_logs_task())

    class QueueLogHandler(logging.Handler):
        def __init__(self, queue: asyncio.Queue, loop: asyncio.AbstractEventLoop):
            super().__init__()
            self.queue = queue
            self.loop = loop
        def emit(self, record: logging.LogRecord) -> None:
            log_entry = self.format(record)
            self.loop.call_soon_threadsafe(self.queue.put_nowait, {"type": "alpha_log", "text": log_entry})
 
    log_handler = QueueLogHandler(log_queue, loop)
    log_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s', '%H:%M:%S'))
    logger.addHandler(log_handler)
    alpha_logger = logging.getLogger("ModuloAlpha")
    alpha_logger.addHandler(log_handler)
    logger.info("📡 WebSocket log handler ativado.")

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                data = None

            comando = ""
            if data and isinstance(data, dict):
                if data.get("type") == "audio_input":
                    base64_audio = data.get("data", "")
                    if data.get("voice"):
                        voz_atual = data["voice"]
                    if not base64_audio:
                        await websocket.send_json({"type": "system", "text": "❌ Áudio vazio."})
                        continue
                    await websocket.send_json({"type": "system", "text": "🎤 Transcrevendo..."})
                    texto_transcrito = await VoiceEngine.transcrever_audio_base64(base64_audio)
                    if texto_transcrito.startswith("[ERRO]"):
                        await websocket.send_json({"type": "system", "text": texto_transcrito})
                        continue
                    await websocket.send_json({"type": "system", "text": f"🎙️ Você disse: \"{texto_transcrito}\""})
                    comando = texto_transcrito
                elif data.get("type") == "command":
                    comando = data.get("text", "")
                    if data.get("voice"):
                        voz_atual = data["voice"]
                elif data.get("type") == "file_upload":
                    filename = data.get("name")
                    content = data.get("content")
                    file_context = f"\n[ARQUIVO ANEXADO: {filename}]\n{content}\n[FIM DO ARQUIVO]\n"
                    await websocket.send_json({"type": "system", "text": f"Sistema: Arquivo {filename} processado."})
                    continue
                elif data.get("type") == "music_process":
                    vocal_path = data.get("vocal_path")
                    instr_path = data.get("instrumental_path")
                    ref_path = data.get("reference_path")
                    if not all([vocal_path, instr_path, ref_path]):
                        await websocket.send_json({"type": "system", "text": "❌ Envie os caminhos de vocal, instrumental e voz de referência."})
                        continue
                    engine = app.state.music_engine
                    await websocket.send_json({"type": "system", "text": "🎛️ Iniciando processamento musical..."})
                    try:
                        success, result = await engine.process_music(vocal_path, instr_path, ref_path)
                        if success:
                            await websocket.send_json({"type": "audio", "url": result})
                            await websocket.send_json({"type": "system", "text": "✅ Mixagem finalizada!"})
                        else:
                            await websocket.send_json({"type": "system", "text": f"❌ Erro: {result}"})
                    except Exception as e:
                        logger.exception("Erro no processamento de música")
                        await websocket.send_json({"type": "system", "text": f"❌ Falha crítica: {str(e)}"})
                    continue
                else:
                    comando = raw
            else:
                comando = raw

            cmd_l = comando.lower().strip()

            # ---------- MÓDULO CAMALEÃO: seleção de cérebro ----------
            if cmd_l.startswith("/select_module "):
                module_name = cmd_l.replace("/select_module ", "").strip()
                if not rag_ops:
                    await websocket.send_json({"type": "system", "text": "❌ RAG offline."})
                    continue
                if module_name == "default":
                    new_dir = DEFAULT_KB_DIR
                else:
                    new_dir = BRAIN_KB_DIR / module_name
                    if not new_dir.exists() or not new_dir.is_dir():
                        await websocket.send_json({"type": "system", "text": f"❌ Módulo '{module_name}' não encontrado em {BRAIN_KB_DIR}."})
                        continue
                # Altera o diretório do knowledge base
                rag_ops.set_docs_dir(new_dir)
                # Força reindexação
                sync_msg = await rag_ops.sync()
                await websocket.send_json({"type": "system", "text": f"🧠 R2: Módulo [{module_name}] carregado. {sync_msg}"})
                continue

            if cmd_l == "/doc sync":
                if rag_ops:
                    msg = await rag_ops.sync()
                    await websocket.send_json({"type": "system", "text": msg})
                else:
                    await websocket.send_json({"type": "system", "text": "❌ RAG offline."})
                continue
            if cmd_l == "/doc list":
                arquivos = rag_ops.arquivos_indexados if rag_ops else []
                if arquivos:
                    lista = "📋 **Arquivos Indexados:**\n" + "\n".join([f"- `{a}`" for a in arquivos])
                else:
                    lista = "📋 Nenhum arquivo indexado. Use `/doc sync` primeiro."
                await websocket.send_json({"type": "system", "text": lista})
                continue
            if cmd_l.startswith("/ler "):
                nome_arquivo = comando[5:].strip()
                if nome_arquivo:
                    await websocket.send_json({"type": "system", "text": f"📄 Lendo arquivo `{nome_arquivo}`..."})
                    await websocket.send_json({"type": "system", "text": f"Arquivo {nome_arquivo} não encontrado."})
                else:
                    await websocket.send_json({"type": "system", "text": "⚠️ Use `/ler <nome_do_arquivo>`."})
                continue
            if cmd_l.startswith("/vid viral "):
                video_alvo = comando.replace("/vid viral ", "").strip()
                await websocket.send_json({"type": "system", "text": f"⏳ Analisando {video_alvo}..."})
                if video_ops and neural.model:
                    res = await asyncio.to_thread(video_ops.processar_video_viral, video_alvo, neural.model)
                    if isinstance(res, list):
                        msg = "✅ **Cortes Virais:**\n"
                        for r in res:
                            nome = Path(r).name
                            url = Path(r).as_posix()
                            msg += f"🎬 <b>{nome}</b><br><video src='/{url}' controls preload='metadata' style='width:100%; max-width:400px;'></video><br>"
                        await websocket.send_json({"type": "system", "text": msg})
                    else:
                        await websocket.send_json({"type": "system", "text": str(res)})
                else:
                    await websocket.send_json({"type": "system", "text": "❌ Tesoura Neural offline."})
                continue
            if cmd_l.startswith("/vid extract "):
                raw_config = comando[len("/vid extract "):].strip()
                try:
                    config = json.loads(raw_config)
                    video_url = config.get("url", "")
                    if not video_url:
                        await websocket.send_json({"type": "system", "text": "❌ URL não fornecida."})
                        continue
                    if video_ops and neural.model:
                        res = await asyncio.to_thread(video_ops.processar_video_viral, video_url, neural.model)
                        if isinstance(res, list):
                            msg = "✅ **Extração concluída:**\n"
                            for r in res:
                                url = Path(r).as_posix()
                                nome = Path(r).name
                                msg += f"🎬 <b>{nome}</b><br><video src='/{url}' controls preload='metadata' style='width:100%; max-width:400px;'></video><br>"
                            await websocket.send_json({"type": "system", "text": msg})
                        else:
                            await websocket.send_json({"type": "system", "text": str(res)})
                    else:
                        await websocket.send_json({"type": "system", "text": "❌ Tesoura Neural offline."})
                except Exception as e:
                    await websocket.send_json({"type": "system", "text": f"❌ Erro: {e}"})
                continue

            # --- PROCESSAMENTO NORMAL COM IA, RAG E MEMÓRIA ---
            async with sem:
                if neural.model:
                    ctx = await rag_ops.search(comando) if rag_ops else ""
                    historico_str = "\n".join(historico_session[-10:]) if historico_session else ""

                    prompt = f"<start_of_turn>system\n{R2_SYSTEM_PROMPT}<end_of_turn>\n"
                    if historico_str:
                        prompt += f"<start_of_turn>user\nHistórico recente:\n{historico_str}<end_of_turn>\n<start_of_turn>assistant\nCompreendido.<end_of_turn>\n"
                    prompt += f"<start_of_turn>user\nContexto tático: {ctx}\n\n{file_context}Comando: {comando}<end_of_turn>\n<start_of_turn>model\n"

                    resp_full = ""
                    async for token in neural.generate_stream(prompt):
                        resp_full += token
                        await websocket.send_json({"type": "stream", "text": token})

                    if not resp_full.strip():
                        resp_full = "Comandante, o modelo processou mas não gerou resposta. Verifique a GPU/RAM."

                    await websocket.send_json({"type": "done"})
                    await salvar_no_historico_json(comando, resp_full)
                    file_context = ""
                    historico_session.append(f"Teddy: {comando}")
                    historico_session.append(f"R2: {resp_full}")
                    if len(historico_session) > 20:
                        historico_session = historico_session[-20:]

                    interacao_count += 1
                    if interacao_count - ultimo_resumo_msg_count >= 20:
                        logger.info("📝 Gerando resumo tático da conversa...")
                        resumo = await neural.summarise_conversation(historico_session)
                        if resumo and "não gerado" not in resumo:
                            await asyncio.to_thread(anexar_resumo_ao_cofre, resumo)
                            await websocket.send_json({"type": "system", "text": "🧠 Resumo tático anexado ao Cofre de Memória."})
                        else:
                            await websocket.send_json({"type": "system", "text": "⚠️ Falha na geração do resumo."})
                        ultimo_resumo_msg_count = interacao_count

                    asyncio.create_task(limpar_audios_antigos_async())

                    await websocket.send_json({"type": "system", "text": "🎙️ Jarvis: Sintetizando resposta (RVC)..."})
                    async def on_start():
                        await websocket.send_json({"type": "speaking_start"})
                    async def on_end():
                        await websocket.send_json({"type": "speaking_end"})
                    falar_jarvis(resp_full, on_start=on_start, on_end=on_end, loop=loop)
                else:
                    await websocket.send_json({"type": "system", "text": "⚠️ Modelo neural offline."})
                    await websocket.send_json({"type": "done"})
    except WebSocketDisconnect:
        pass
    finally:
        if task_stream:
            task_stream.cancel()
        logger.removeHandler(log_handler)
        alpha_logger.removeHandler(log_handler)

# ============================================================
# 14. MAIN (janela nativa)
# ============================================================
if __name__ == "__main__":
    import webview
    def run_server():
        uvicorn.run(app, host="127.0.0.1", port=8000, log_level="error")
    logger.info("Iniciando servidor...")
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    logger.info("Abrindo interface nativa...")
    webview.create_window('R2 · Ghost Protocol', 'http://127.0.0.1:8000', width=1280, height=800)
    webview.start()