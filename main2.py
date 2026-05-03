# filename: main2.py
# ============================================================
# CHANGELOG DE REFATORAÇÃO — R2 OS (revisão 2026-05-15)
# ============================================================
# - [BUG-M1-M2-M3] Importação de ActionExecutor, lifespan não bloqueante e upload resiliente.
# - [MELHORIA-4-6-7] Semáforo de geração neural, proteção de WebSocket e histórico atômico.
# R2 TACTICAL OS — Ghost Protocol v16
# Arquitetura assíncrona, log streaming via WebSocket, lifespan gerenciado.
import random
import os
import json
import datetime
import time
import asyncio
import subprocess
import shutil
import re
import base64
import tempfile
import threading
import signal
from voz import falar # [FIXED: batalha-2.1]
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List, Optional, Dict, Any, AsyncGenerator, Tuple

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, HTTPException, Form
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import aiofiles

class NavigateRequest(BaseModel):
    url: str

# --- 1. CONFIGURAÇÃO DE LOGGING --- #
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("r2")

# --- FILTRAR BIBLIOTECAS BARULHENTAS --- #
logging.getLogger("PIL").setLevel(logging.WARNING)
logging.getLogger("matplotlib").setLevel(logging.WARNING)
logging.getLogger("pytesseract").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.INFO)
logging.getLogger("urllib3").setLevel(logging.WARNING)

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logger.warning("psutil não instalado. O encerramento de processos filhos pode não funcionar no Windows.")

# whisper optional
try:
    import whisper
    WHISPER_AVAILABLE = True
    import torch
except ImportError:
    WHISPER_AVAILABLE = False
    logger.warning("Whisper não instalado. Mensagens de áudio desativadas.")

# --- 2. CONFIGURAÇÃO VIA ENVIRONMENT (pathlib) --- #
R2_WORKSPACE = Path(os.environ.get("R2_WORKSPACE", str(Path.home() / "r2")))
R2_MODEL_DIR = Path(os.environ.get("R2_MODEL_DIR", str(R2_WORKSPACE / "models")))
R2_CONDA_ACTIVATE = os.environ.get("R2_CONDA_ACTIVATE", "")
R2_CONDA_ENV = os.environ.get("R2_CONDA_ENV", "r2")
R2_MODEL_FILENAME = "gemma-2-9b-it-Q4_K_M.gguf"
R2_MODEL_PATH = R2_MODEL_DIR / R2_MODEL_FILENAME
R2_HF_REPO_ID = "bartowski/gemma-2-9b-it-GGUF"
R2_HF_FILENAME = "gemma-2-9b-it-Q4_K_M.gguf"

WORKSPACE = R2_WORKSPACE # type: ignore
WORKSPACE.mkdir(parents=True, exist_ok=True) # type: ignore
UPLOAD_DIR = Path("uploads") # type: ignore
UPLOAD_DIR.mkdir(exist_ok=True) # type: ignore

CONDA_ACTIVATE = R2_CONDA_ACTIVATE # type: ignore
CONDA_ENV = R2_CONDA_ENV # type: ignore

R2_SYSTEM_PROMPT = "Você é o R2, IA tática e Mestre Programador. REGRA: A primeira linha do código DEVE ser: # filename: nome.py" # type: ignore

# --- 3. MODELO AUTO-DOWNLOAD --- #
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
            logger.info(f"📥 Modelo baixado: {path}") # type: ignore
            await asyncio.sleep(2)
            return True
        except Exception as e:
            logger.error(f"Falha no download: {e}")
            return False
    return True
 
# --- 4. MÓDULO ALPHA E safe_import --- #
from alpha_module import alpha_engine, ScreenState, InferenceResult, ActionExecutor # type: ignore

def safe_import(module_name: str, class_name: str) -> Any:
    try:
        import importlib
        mod = importlib.import_module(f"features.{module_name}" if "features" not in module_name else module_name)
        return getattr(mod, class_name)
    except Exception as ex:
        try:
            mod = importlib.import_module(module_name)
            return getattr(mod, class_name)
        except Exception as ex2:
            logger.warning(f"Módulo {class_name} indisponível: {ex2}") # type: ignore
            return None

# --- 5. NÚCLEO DE MEMÓRIA (LOCK) --- #
LOG_HISTORICO = Path("static/logs/historico_chat.json")
LOG_HISTORICO.parent.mkdir(parents=True, exist_ok=True)
historico_lock = asyncio.Lock()

async def salvar_no_historico_json(usuario: str, bot: str) -> None:
    interacao = {"timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "teddy": usuario, "r2": bot}
    async with historico_lock:
        historico = []
        if LOG_HISTORICO.exists():
            try:
                with open(LOG_HISTORICO, "r", encoding="utf-8") as f:
                    historico = json.load(f)
            except Exception:
                pass
        historico.append(interacao)
        tmp_path = LOG_HISTORICO.with_suffix(".tmp")
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(historico[-100:], f, ensure_ascii=False, indent=4)
            os.replace(tmp_path, LOG_HISTORICO)
        except Exception:
            pass

async def carregar_historico_na_ram() -> List[str]: # type: ignore
    async with historico_lock:
        if LOG_HISTORICO.exists():
            try:
                with open(LOG_HISTORICO, "r", encoding="utf-8") as f:
                    dados = json.load(f)
                    return [f"{'Teddy' if k=='teddy' else 'R2'}: {v}" for item in dados[-20:] for k,v in item.items() if k in ('teddy','r2')]
            except Exception:
                pass
        return []

# --- 6. RAG (KnowledgeBase) --- #
class KnowledgeBase:
    def __init__(self, docs_dir: str = "static/docs"):
        self.docs_dir = Path(docs_dir)
        self.index_path = self.docs_dir / "faiss_index.bin"
        self.data_path = self.docs_dir / "rag_data.json"
        self.embedder: Optional[Any] = None
        self.index = None
        self.chunks: List[str] = []
        self.arquivos_indexados: List[str] = []
        self._embedder_lock = threading.Lock()
        self.docs_dir.mkdir(parents=True, exist_ok=True)
        self._ignore_patterns = [".ghost", ".tmp", "~$"]
        if self.index_path.exists() and self.data_path.exists():
            try:
                import faiss
                self.index = faiss.read_index(str(self.index_path))
                with open(self.data_path, "r", encoding="utf-8") as f:
                    dados = json.load(f)
                    self.chunks = dados.get("chunks", [])
                    self.arquivos_indexados = dados.get("arquivos_indexados", [])
            except Exception: # type: ignore
                pass

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
                text = ""
                if arq.suffix.lower() == '.pdf':
                    with open(arq, 'rb') as f:
                        reader = _pdf_lib.PdfReader(f)
                        for page in reader.pages:
                            try:
                                extracted = page.extract_text()
                                if extracted and len(extracted.strip()) > 10:
                                    text += extracted
                            except Exception: # type: ignore
                                continue
                else:
                    with open(arq, 'r', encoding='utf-8', errors='ignore') as f:
                        text = f.read()

                if isinstance(text, str) and text.strip():
                    text = text.replace('\x00', '').replace('\ufffd', '') # type: ignore
                    self.arquivos_indexados.append(arq.name)
                    for i in range(0, len(text), 800):
                        chunk = text[i:i+1000].strip()
                        if isinstance(chunk, str) and len(chunk) > 50:
                            self.chunks.append(f"[Fonte: {arq.name}] {chunk}")
            except Exception as e:
                logger.warning(f"Erro no arquivo {arq.name}: {e}") # type: ignore
                continue

        if not self.chunks:
            return "❌ Falha na extração. Nenhum texto válido encontrado."

        try:
            logger.info(f"RAG: codificando {len(self.chunks)} blocos...") # type: ignore
            embeddings = self.embedder.encode(self.chunks, convert_to_numpy=True)
            self.index = faiss.IndexFlatL2(embeddings.shape[1])
            self.index.add(embeddings)
            faiss.write_index(self.index, str(self.index_path))
            with open(self.data_path, "w", encoding="utf-8") as f:
                json.dump({"chunks": self.chunks, "arquivos_indexados": self.arquivos_indexados}, f, ensure_ascii=False)
            return f"✅ Cérebro RAG Sincronizado! {len(self.arquivos_indexados)} arquivos processados."
        except Exception as e:
            return f"❌ Erro crítico ao criar embeddings: {e}"

    async def search(self, query: str, max_chars: int = 1500) -> str: # type: ignore
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
            _, indices = self.index.search(self.embedder.encode([query], convert_to_numpy=True), 2)
            contexto = ""
            for i in indices[0]:
                if 0 <= i < len(self.chunks) and isinstance(self.chunks[i], str):
                    chunk = self.chunks[i]
                    if len(contexto) + len(chunk) < max_chars:
                        contexto += chunk + "\n\n"
            return contexto
        except Exception as e:
            logger.error(f"Erro na busca RAG: {e}") # type: ignore
            return ""

# --- 7. MÓDULO DE VOZ (EdgeTTSEngine) --- #
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
    async def gerar_voz_r2(texto: str, filepath: Path, voz: str = "Thalita") -> bool: # type: ignore
        try:
            import edge_tts
            voice_code = VoiceEngine.mapear_voz_para_edge(voz)
            communicate = edge_tts.Communicate(texto, voice_code)
            await communicate.save(str(filepath))
            return True
        except Exception as e:
            logger.error(f"Erro ao gerar voz: {e}") # type: ignore
            return False

    @staticmethod
    async def transcrever_audio_base64(base64_audio: str) -> str:
        if not WHISPER_AVAILABLE:
            return "[ERRO] Whisper não instalado."
        model = await asyncio.to_thread(get_whisper_model)
        if model is None: # type: ignore
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
                    if p.exists(): # type: ignore
                        p.unlink()
                except Exception:
                    pass
            return texto if texto else "[Áudio sem fala detectada]"
        except Exception as e:
            logger.error(f"Erro na transcrição: {e}") # type: ignore
            return f"[ERRO] Falha ao transcrever: {str(e)}"

# --- 8. MÓDULO NEURAL (Gemma 2) --- #
class NeuralEngine:
    def __init__(self):
        self.model = None
        self._stop_event = threading.Event()
        self._generation_sem = threading.Semaphore(1)

    async def load(self) -> bool:
        if not await garantir_modelo():
            return False
        try:
            from llama_cpp import Llama # type: ignore
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
            return True # type: ignore
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
                            break # type: ignore
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

neural = NeuralEngine() # type: ignore

# --- 9. FASTAPI APP & LIFESPAN --- #
rag_ops: Optional[KnowledgeBase] = None # type: ignore
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    global rag_ops, eu_ops, pizza_ops, noaa_ops, video_ops, astro_ops, air_ops, tiktok_ops, broker_ops

    Path("static/media").mkdir(parents=True, exist_ok=True) # type: ignore
    logger.info("⚡ Inicializando módulos táticos...") # type: ignore

    rag_ops = KnowledgeBase() # type: ignore
    CortexEU = safe_import("eu", "CORTEX_EU") # type: ignore
    eu_ops = CortexEU("R2") if CortexEU else None # type: ignore
    PizzaINTService = safe_import("pizzint_service", "PizzaINTService") # type: ignore
    pizza_ops = PizzaINTService(config={}) if PizzaINTService else None # type: ignore
    NOAAService = safe_import("noaa_service", "NOAAService") # type: ignore
    noaa_ops = NOAAService() if NOAAService else None # type: ignore
    TikTokCommander = safe_import("tiktok_publisher", "TikTokCommander") # type: ignore
    tiktok_ops = TikTokCommander(alpha_engine=alpha_engine) if TikTokCommander else None # type: ignore
    BrokerOperator = safe_import("broker_operator", "BrokerOperator") # type: ignore
    broker_ops = BrokerOperator(alpha_engine=alpha_engine) if BrokerOperator else None # type: ignore
    AirTrafficControl = safe_import("air_traffic", "AirTrafficControl") # type: ignore
    AstroDefenseSystem = safe_import("astro_defense", "AstroDefenseSystem") # type: ignore
    air_ops = AirTrafficControl() if AirTrafficControl else None # type: ignore
    astro_ops = AstroDefenseSystem() if AstroDefenseSystem else None # type: ignore
    whisper_model_global = await asyncio.to_thread(get_whisper_model) if WHISPER_AVAILABLE else None # type: ignore
    try:
        from video_ops import VideoSurgeon
        video_ops = VideoSurgeon(whisper_model=whisper_model_global)
        logger.info("✂️ Tesoura Neural: ONLINE")
    except Exception as e:
        logger.warning(f"Tesoura Neural: OFFLINE → {e}")
        video_ops = None

    if not await neural.load(): # type: ignore
        logger.error("Sistema incapaz de localizar ou baixar o cérebro.")

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

# --- 10. ENDPOINTS REST --- #
class CodePayload(BaseModel):
    filename: str
    content: str

class CalibrateRequest(BaseModel):
    x: int
    y: int

class AlphaActionRequest(BaseModel):
    action: str

@app.post("/api/open_vscode")
async def open_vscode(payload: CodePayload): # type: ignore
    safe_name = Path(payload.filename).name # type: ignore
    filepath = WORKSPACE / safe_name # type: ignore
    try: # type: ignore
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(payload.content)
        subprocess.Popen(["code", str(filepath)], shell=True)
        return {"ok": True}
    except Exception:
        return {"ok": False}

@app.post("/api/execute_code")
async def execute_code(payload: CodePayload): # type: ignore
    safe_name = Path(payload.filename).name # type: ignore
    filepath = WORKSPACE / safe_name # type: ignore
    try: # type: ignore
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(payload.content)
        cmd = f'cmd.exe /c "call {CONDA_ACTIVATE} && conda activate {CONDA_ENV} && python "{filepath}""' # type: ignore
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
    return await execute_code(payload) # type: ignore

@app.post("/api/stop")
async def stop_generation():
    neural.stop_generation() # type: ignore
    return {"ok": True, "message": "Sinal de parada enviado."}

@app.post("/api/upload_arquivos")
async def upload_arquivos(arquivos: List[UploadFile] = File(...)):
    docs_dir = Path("static/docs") # type: ignore
    docs_dir.mkdir(parents=True, exist_ok=True) # type: ignore
    salvos = []
    erros = []
    for arq in arquivos: # type: ignore
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

@app.get("/api/tiktok/cortes")
async def listar_cortes(): # type: ignore
    pasta = Path("static/media/cortes_virais") # type: ignore
    if not pasta.exists(): # type: ignore
        pasta.mkdir(parents=True, exist_ok=True) # type: ignore
        return []
    mp4s = list(pasta.glob("*.mp4")) # type: ignore
    return [{"name": mp4.name, "path": str(mp4.as_posix())} for mp4 in mp4s] # type: ignore

# --- 11. ALPHA E BROKER ROUTES --- #
@app.get("/api/alpha/status")
async def alpha_status():
    status_raw = alpha_engine.get_status()
    # Garante que o status no HUD inclua o placar em tempo real
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
    logger.info(f"🌐 Recebida requisição para navegar: {body.url}")
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
        "breakout_ready": alpha_engine.classifier.market.breakout_detector.is_valid_breakout_signal("CALL")  # exemplo
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

# --- 12. TIKTOK ENDPOINTS ---
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
    if not tiktok_ops: # type: ignore
        raise HTTPException(status_code=503, detail="TikTok Commander offline") # type: ignore
    if video: # type: ignore
        dest = UPLOAD_DIR / video.filename # type: ignore
        async with aiofiles.open(dest, 'wb') as f:
            while chunk := await video.read(8192):
                await f.write(chunk)
        video_path = str(dest.resolve())
    elif video_path_arsenal:
        video_path = video_path_arsenal
    else:
        raise HTTPException(status_code=400, detail="Nenhum vídeo fornecido")
    item = tiktok_ops.adicionar( # type: ignore
        video_path=video_path,
        titulo=titulo,
        descricao=descricao,
        hashtags=hashtags,
        agendar_para=agendar_para,
    )
    return {"ok": True, "item": item}

@app.post("/api/tiktok/post_now/{item_id}")
async def post_now(item_id: str):
    if not tiktok_ops: # type: ignore
        raise HTTPException(status_code=503, detail="TikTok Commander offline") # type: ignore
    resultado = tiktok_ops.disparar_agora(item_id) # type: ignore
    if not resultado["ok"]:
        raise HTTPException(status_code=400, detail=resultado["erro"]) # type: ignore
    return resultado

@app.delete("/api/tiktok/remover/{item_id}")
async def remover(item_id: str):
    removido = tiktok_ops.remover(item_id) if tiktok_ops else False # type: ignore
    if not removido:
        raise HTTPException(status_code=404, detail="Item não encontrado.") # type: ignore
    return {"ok": True}

@app.get("/api/tiktok/status/{item_id}")
async def status(item_id: str):
    fila = tiktok_ops.get_fila() if tiktok_ops else [] # type: ignore
    item = next((i for i in fila if i["id"] == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado.") # type: ignore
    return {"ok": True, "item": item}

@app.get("/", response_class=HTMLResponse)
async def serve_gui():
    return FileResponse("static/index.html")

# --- 13. WEBSOCKET (com log streaming para Alpha) --- #
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
        logger.warning(f"Limpeza de áudios: {e}") # type: ignore

_modelo_whisper = None
def get_whisper_model() -> Any:
    global _modelo_whisper
    if not WHISPER_AVAILABLE:
        return None
    if _modelo_whisper is None:
        try:
            logger.info("Carregando Whisper...")
            _modelo_whisper = whisper.load_model("base")
        except Exception as e: # type: ignore
            logger.error(f"Erro Whisper: {e}")
            return None
    return _modelo_whisper

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    voz_atual = "Thalita"
    historico_session = await carregar_historico_na_ram() # type: ignore
    sem = asyncio.Semaphore(1) # type: ignore

    # MELHORIA #3: passa o loop atual explicitamente
    loop = asyncio.get_running_loop()

    # Fila para transmissão tática de logs via WebSocket
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
            # call_soon_threadsafe é o ideal para disparar o log da thread do motor para o loop da web
            self.loop.call_soon_threadsafe(self.queue.put_nowait, {"type": "alpha_log", "text": log_entry})
 
    log_handler = QueueLogHandler(log_queue, loop)
    log_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s', '%H:%M:%S'))
    logger.addHandler(log_handler)
    alpha_logger = logging.getLogger("ModuloAlpha")
    alpha_logger.addHandler(log_handler)

    logger.info("📡 WebSocket log handler ativado. Logs em tempo real.")

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
                        voz_atual = data["voice"] # type: ignore
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
                    comando = data.get("text", "") # type: ignore
                    if data.get("voice"):
                        voz_atual = data["voice"]
                else:
                    comando = raw
            else:
                comando = raw

            cmd_l = comando.lower().strip()

            # Comandos especiais (mantidos, versão simplificada)
            if cmd_l.startswith("/cmd "):
                sub = cmd_l.replace("/cmd ", "")
                if sub == "pizza" and pizza_ops: # type: ignore
                    await websocket.send_json({"type": "system", "text": pizza_ops.gerar_html_painel(await asyncio.to_thread(pizza_ops.get_status))}) # type: ignore
                elif sub == "solar" and noaa_ops: # type: ignore
                    await websocket.send_json({"type": "system", "text": noaa_ops.gerar_html_painel(await asyncio.to_thread(noaa_ops.get_full_intel))}) # type: ignore
                elif sub == "radar": # type: ignore
                    if air_ops: # type: ignore
                        filename, qtd, msg = await asyncio.to_thread(air_ops.radar_scan, "Ivinhema") # type: ignore
                        await websocket.send_json({"type": "system", "text": f"{msg}<br><img src='/{filename}' style='max-width:100%;'>"}) # type: ignore
                    else:
                        await websocket.send_json({"type": "system", "text": "📡 Módulo de Radar offline."})
                elif sub == "astro": # type: ignore
                    if astro_ops: # type: ignore
                        texto, astro_id, astro_nome = await asyncio.to_thread(astro_ops.get_asteroid_report) # type: ignore
                        await websocket.send_json({"type": "system", "text": texto}) # type: ignore
                    else:
                        await websocket.send_json({"type": "system", "text": "☄️ Defesa Planetária offline."})
                elif sub == "tiktok": # type: ignore
                    await websocket.send_json({"type": "system", "text": "<button onclick='abrirCentralPostagem()' class='alpha-btn'>📱 Abrir Central</button>"})
                else:
                    await websocket.send_json({"type": "system", "text": f"⚠️ Comando /cmd {sub} desconhecido."})
                continue
            if cmd_l == "/doc sync":
                await websocket.send_json({"type": "system", "text": await rag_ops.sync() if rag_ops else "❌ RAG offline."}) # type: ignore
                continue
            if cmd_l == "/doc list":
                arquivos = rag_ops.arquivos_indexados if rag_ops else [] # type: ignore
                if arquivos:
                    lista = "📋 **Arquivos Indexados:**\n" + "\n".join([f"- `{a}`" for a in arquivos])
                else:
                    lista = "📋 Nenhum arquivo indexado. Use `/doc sync` primeiro."
                await websocket.send_json({"type": "system", "text": lista})
                continue
            if cmd_l.startswith("/ler "): # type: ignore
                nome_arquivo = comando[5:].strip()
                if nome_arquivo:
                    await websocket.send_json({"type": "system", "text": f"📄 Lendo arquivo `{nome_arquivo}`..."})
                    await websocket.send_json({"type": "system", "text": f"Arquivo {nome_arquivo} não encontrado na base."})
                else:
                    await websocket.send_json({"type": "system", "text": "⚠️ Use `/ler <nome_do_arquivo>`."})
                continue
            if cmd_l.startswith("/vid viral "): # type: ignore
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
            if cmd_l.startswith("/vid extract "): # type: ignore
                raw_config = comando[len("/vid extract "):].strip()
                try:
                    config = json.loads(raw_config)
                    video_url = config.get("url", "")
                    if not video_url:
                        await websocket.send_json({"type": "system", "text": "❌ URL não fornecida."}) # type: ignore
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
 
            # Processamento IA com rate limiting
            async with sem:
                if neural.model: # type: ignore
                    ctx = await rag_ops.search(comando) if rag_ops else "" # type: ignore
                    historico_str = "\n".join(historico_session[-10:]) if historico_session else ""
                    prompt = f"<start_of_turn>system\n{R2_SYSTEM_PROMPT}<end_of_turn>\n"
                    if historico_str: # type: ignore
                        prompt += f"<start_of_turn>user\nHistórico recente:\n{historico_str}<end_of_turn>\n<start_of_turn>assistant\nCompreendido.<end_of_turn>\n"
                    prompt += f"<start_of_turn>user\nContexto tático: {ctx}\n\nComando: {comando}<end_of_turn>\n<start_of_turn>model\n"

                    resp_full = ""
                    async for token in neural.generate_stream(prompt):
                        resp_full += token
                        await websocket.send_json({"type": "stream", "text": token})

                    if not resp_full.strip():
                        resp_full = "Comandante, o modelo processou mas não gerou resposta. Verifique a GPU/RAM."

                    await websocket.send_json({"type": "done"})
                    await salvar_no_historico_json(comando, resp_full) # type: ignore
                    historico_session.append(f"Teddy: {comando}") # type: ignore
                    historico_session.append(f"R2: {resp_full}") # type: ignore
                    if len(historico_session) > 20: # type: ignore
                        historico_session = historico_session[-20:]

                    asyncio.create_task(limpar_audios_antigos_async())

                    # [RESTAURADO] Pipeline de voz com sincronização do soundwave [FIXED: batalha-2.3]
                    def _on_speaking_start():
                        loop.call_soon_threadsafe(
                            asyncio.ensure_future,
                            websocket.send_json({"type": "speaking_start"})
                        )

                    def _on_speaking_end():
                        loop.call_soon_threadsafe(
                            asyncio.ensure_future,
                            websocket.send_json({"type": "speaking_end"})
                        )

                    falar(resp_full, on_start=_on_speaking_start, on_end=_on_speaking_end)
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

# --- 14. MAIN ---
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