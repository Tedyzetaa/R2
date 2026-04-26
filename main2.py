# filename: main2.py
# R2 TACTICAL OS — Ghost Protocol v9.0
# CORREÇÕES APLICADAS:
# [BUG1] Streaming Gemma 4 corrigido (executor em background + leitura assíncrona da queue)
# [BUG2] Endpoint /api/broker/calibrar agora usa CLICK_COORD
# [BUG3] Modelo Pydantic CalibrateRequest
# [BUG4] Diagnóstico movido para comando interno DIAGNOSTICO (sem thread extra)
# [BUG5] Import random movido para topo

import random   # [BUG5] movido para topo

from pathlib import Path
import os, json, datetime, sys, time, asyncio, subprocess, shutil, re, gc, base64, tempfile
import threading
from contextlib import asynccontextmanager
from queue import Queue, Empty
from fastapi import Request, FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, HTTPException, Form
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import torch
import faiss
from sentence_transformers import SentenceTransformer
import edge_tts
import glob

from alpha_module import alpha_engine, ScreenState, InferenceResult, ActionExecutor

class AlphaActionRequest(BaseModel):
    action: str

class NavigateRequest(BaseModel):
    url: str = "https://trade.broker10.com/traderoom"

class CalibrateRequest(BaseModel):   # [BUG3] novo modelo
    x: int
    y: int

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    print("[AVISO] Whisper não instalado. Mensagem de áudio desativada.")

# ══════════════════════════════════════════
# CONFIGURAÇÃO DO WORKSPACE E AMBIENTE
# ══════════════════════════════════════════
WORKSPACE = Path(r"c:\r2")
WORKSPACE.mkdir(parents=True, exist_ok=True)
CONDA_ACTIVATE = r"C:\Users\Teddy\miniconda3\Scripts\activate.bat C:\Users\Teddy\miniconda3"
CONDA_ENV = "r2"

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

_stop_generation = False

class CodePayload(BaseModel):
    filename: str
    content: str

# ══════════════════════════════════════════
# 💾 NÚCLEO DE MEMÓRIA (LOCK PROTEGIDO)
# ══════════════════════════════════════════
LOG_HISTORICO = "static/logs/historico_chat.json"
os.makedirs("static/logs", exist_ok=True)
historico_lock = threading.Lock()

def salvar_no_historico_json(usuario, bot):
    interacao = {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "teddy": usuario,
        "r2": bot
    }
    with historico_lock:
        historico = []
        if os.path.exists(LOG_HISTORICO):
            try:
                with open(LOG_HISTORICO, "r", encoding="utf-8") as f:
                    historico = json.load(f)
            except Exception as e:
                print(f"[AVISO] Erro ao ler histórico: {e}")
        historico.append(interacao)
        if len(historico) > 500:
            historico = historico[-500:]
        try:
            with open(LOG_HISTORICO, "w", encoding="utf-8") as f:
                json.dump(historico, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"[AVISO] Erro ao gravar histórico: {e}")

def carregar_historico_na_ram():
    with historico_lock:
        if os.path.exists(LOG_HISTORICO):
            try:
                with open(LOG_HISTORICO, "r", encoding="utf-8") as f:
                    dados = json.load(f)
                    contexto = []
                    for item in dados[-40:]:
                        contexto.append(f"Teddy: {item['teddy']}")
                        contexto.append(f"R2: {item['r2']}")
                    return contexto
            except Exception as e:
                print(f"[AVISO] Erro ao carregar RAM: {e}")
        return []

# ══════════════════════════════════════════
# 📂 IMPORTAÇÕES TÁTICAS SEGURAS
# ══════════════════════════════════════════
def safe_import(module_name, class_name):
    try:
        import importlib
        mod = importlib.import_module(f"features.{module_name}" if "features" not in module_name else module_name)
        return getattr(mod, class_name)
    except Exception as e:
        try:
            import importlib
            mod = importlib.import_module(module_name)
            return getattr(mod, class_name)
        except Exception as ex:
            print(f"⚠️ Módulo {class_name} indisponível: {ex}")
            return None

# ══════════════════════════════════════════
# 📚 NÚCLEO RAG COM MEMÓRIA NO HD
# ══════════════════════════════════════════
class KnowledgeBase:
    def __init__(self, docs_dir="static/docs"):
        self.docs_dir = docs_dir
        self.index_path = os.path.join(self.docs_dir, "faiss_index.bin")
        self.data_path = os.path.join(self.docs_dir, "rag_data.json")
        self.embedder = None; self.index = None; self.chunks = []; self.arquivos_indexados = []
        os.makedirs(self.docs_dir, exist_ok=True)
        self.carregar_memoria()

    def carregar_memoria(self):
        if os.path.exists(self.index_path) and os.path.exists(self.data_path):
            try:
                self.index = faiss.read_index(self.index_path)
                with open(self.data_path, "r", encoding="utf-8") as f:
                    dados = json.load(f)
                    self.chunks = dados.get("chunks", []); self.arquivos_indexados = dados.get("arquivos_indexados", [])
            except Exception as e: 
                print(f"[AVISO] Falha ao carregar disco RAG: {e}")

    def sync(self):
        try:
            import pypdf as _pdf_lib
        except ImportError:
            try:
                import PyPDF2 as _pdf_lib
            except ImportError:
                return "❌ Nenhuma biblioteca PDF encontrada. Execute: pip install pypdf"

        if not self.embedder: self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        self.chunks = []; self.arquivos_indexados = [] 
        arquivos = [f for f in os.listdir(self.docs_dir) if f.lower().endswith(('.pdf', '.md'))]
        for arq in arquivos:
            try:
                p = os.path.join(self.docs_dir, arq)
                if arq.endswith('.pdf'):
                    with open(p, 'rb') as f: text = "".join([pg.extract_text() or "" for pg in _pdf_lib.PdfReader(f).pages])
                else:
                    with open(p, 'r', encoding='utf-8') as f: text = f.read()
                if text.strip():
                    self.arquivos_indexados.append(arq)
                    for i in range(0, len(text), 800):
                        chunk = text[i:i+1000].strip()
                        if len(chunk) > 50: self.chunks.append(f"[Fonte: {arq}] {chunk}")
            except Exception as e: 
                print(f"[AVISO] Erro ao extrair PDF/MD ({arq}): {e}")
                continue
        if not self.chunks: return "❌ Falha na extração de documentos."
        embeddings = self.embedder.encode(self.chunks, convert_to_numpy=True)
        self.index = faiss.IndexFlatL2(embeddings.shape[1]); self.index.add(embeddings)
        faiss.write_index(self.index, self.index_path)
        with open(self.data_path, "w", encoding="utf-8") as f:
            json.dump({"chunks": self.chunks, "arquivos_indexados": self.arquivos_indexados}, f, ensure_ascii=False)
        return f"✅ Cérebro RAG Sincronizado! {len(self.arquivos_indexados)} arquivos."

    def search(self, query):
        if not self.index: return None
        if not self.embedder: self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        _, indices = self.index.search(self.embedder.encode([query], convert_to_numpy=True), 3)
        return "\n\n".join([self.chunks[idx] for idx in indices[0] if idx < len(self.chunks)])

# ══════════════════════════════════════════
# 🎙️ FUNÇÃO DE SÍNTESE DE VOZ
# ══════════════════════════════════════════
def mapear_voz_para_edge(voz_usuario: str) -> str:
    mapa = {
        "Antonio":  "pt-BR-AntonioNeural",
        "Francisca": "pt-BR-FranciscaNeural",
        "Thalita":  "pt-BR-ThalitaNeural"
    }
    return mapa.get(voz_usuario, "pt-BR-ThalitaNeural")

async def gerar_voz_r2(texto: str, filepath: str, voz: str = "Thalita") -> bool:
    try:
        voice_code = mapear_voz_para_edge(voz)
        communicate = edge_tts.Communicate(texto, voice_code)
        await communicate.save(filepath)
        return True
    except Exception as e:
        print(f"[ERRO VOZ] {e}")
        return False

def limpar_audios_antigos(pasta: str = "static/media", max_idade_min: int = 10):
    try:
        agora = time.time()
        for nome in os.listdir(pasta):
            if nome.startswith("r2_voice_") and nome.endswith(".mp3"):
                caminho = os.path.join(pasta, nome)
                idade_min = (agora - os.path.getmtime(caminho)) / 60
                if idade_min > max_idade_min:
                    try:
                        os.unlink(caminho)
                    except Exception:
                        pass
    except Exception as e:
        print(f"[LIMPEZA] Erro: {e}")

# ══════════════════════════════════════════
# 🎤 FUNÇÃO DE TRANSCRIÇÃO DE ÁUDIO (WHISPER)
# ══════════════════════════════════════════
_modelo_whisper = None

def get_whisper_model():
    global _modelo_whisper
    if not WHISPER_AVAILABLE:
        return None
    if _modelo_whisper is None:
        try:
            print("[WHISPER] Carregando modelo base...")
            _modelo_whisper = whisper.load_model("base")
            print("[WHISPER] Modelo pronto.")
        except Exception as e:
            print(f"[WHISPER] Erro ao carregar: {e}")
            return None
    return _modelo_whisper

async def transcrever_audio_base64(base64_audio: str) -> str:
    if not WHISPER_AVAILABLE:
        return "[ERRO] Whisper não está instalado no servidor."
    model = get_whisper_model()
    if model is None:
        return "[ERRO] Modelo Whisper não disponível."
    
    try:
        audio_bytes = base64.b64decode(base64_audio)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp_webm:
            tmp_webm.write(audio_bytes)
            tmp_webm_path = tmp_webm.name

        tmp_wav_path = tmp_webm_path.replace(".webm", "_conv.wav")
        cmd_conv = (
            f'ffmpeg -y -i "{tmp_webm_path}" '
            f'-acodec pcm_s16le -ar 16000 -ac 1 "{tmp_wav_path}"'
        )
        subprocess.run(cmd_conv, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        caminho_para_whisper = tmp_wav_path if os.path.exists(tmp_wav_path) else tmp_webm_path
        result = await asyncio.to_thread(model.transcribe, caminho_para_whisper, language="pt")
        texto = result["text"].strip()
        
        for p in [tmp_webm_path, tmp_wav_path]:
            try:
                if os.path.exists(p):
                    os.unlink(p)
            except Exception:
                pass
        
        return texto if texto else "[Áudio sem fala detectada]"
    except Exception as e:
        print(f"[WHISPER] Erro na transcrição: {e}")
        return f"[ERRO] Falha ao transcrever áudio: {str(e)}"

# ════════════════════════════════════════════
# 🧠 CONFIGURAÇÃO DO MODELO GEMMA 4
# ════════════════════════════════════════════
MODELO_DIR   = r"C:\r2\models"
MODELO_NOME  = "gemma-4-31B-it-Q4_K_M.gguf"
MODELO_PATH  = os.path.join(MODELO_DIR, MODELO_NOME)
HF_REPO_ID   = "unsloth/gemma-4-31B-it-GGUF"

def _encontrar_gguf_q4(repo_id):
    """Lista o repo HF e retorna o filename do melhor candidato GGUF."""
    try:
        from huggingface_hub import list_repo_files
        arquivos = list(list_repo_files(repo_id))
        for prioridade in ["Q4_K_M", "Q4_K_S", "Q4_0", "Q8_0"]:
            candidatos = [f for f in arquivos if prioridade in f and f.endswith(".gguf") and "/" not in f]
            if candidatos:
                return candidatos[0]
        raiz = [f for f in arquivos if f.endswith(".gguf") and "/" not in f]
        return raiz[0] if raiz else None
    except Exception as e:
        print(f"[DOWNLOAD] Erro ao listar repo: {e}")
        return None

def verificar_e_baixar_modelo():
    """
    Verifica se o modelo Gemma 4 existe localmente.
    Se nao existir, baixa automaticamente do Hugging Face.
    Retorna True se o modelo estiver pronto.
    """
    if os.path.exists(MODELO_PATH):
        tamanho_gb = os.path.getsize(MODELO_PATH) / (1024 ** 3)
        print(f"\u2705 [MODELO] Gemma 4 encontrado \u2192 {MODELO_PATH} ({tamanho_gb:.1f} GB)")
        return True

    print(f"\u26a0\ufe0f  [MODELO] Arquivo nao encontrado: {MODELO_PATH}")
    print(f"\U0001f310 [DOWNLOAD] Buscando modelo em: https://huggingface.co/{HF_REPO_ID}")

    try:
        from huggingface_hub import hf_hub_download
    except ImportError:
        print("\u274c [DOWNLOAD] huggingface_hub nao instalado. Execute: pip install huggingface_hub")
        return False

    os.makedirs(MODELO_DIR, exist_ok=True)

    arquivo_remoto = _encontrar_gguf_q4(HF_REPO_ID)
    if not arquivo_remoto:
        print("\u274c [DOWNLOAD] Nenhum arquivo GGUF encontrado no repositorio.")
        print(f"   Acesse manualmente: https://huggingface.co/{HF_REPO_ID}")
        return False

    print(f"\U0001f4e5 [DOWNLOAD] Arquivo selecionado: {arquivo_remoto}")
    print("\u23f3 [DOWNLOAD] Iniciando download (~20 GB para Q4_K_M). Aguarde...")

    try:
        caminho_baixado = hf_hub_download(
            repo_id=HF_REPO_ID,
            filename=arquivo_remoto,
            local_dir=MODELO_DIR,
            local_dir_use_symlinks=False,
        )
        destino = MODELO_PATH
        if os.path.abspath(caminho_baixado) != os.path.abspath(destino):
            shutil.move(caminho_baixado, destino)
        tamanho_gb = os.path.getsize(destino) / (1024 ** 3)
        print(f"\u2705 [DOWNLOAD] Concluido! Salvo em: {destino} ({tamanho_gb:.1f} GB)")
        return True
    except KeyboardInterrupt:
        print("\n\u26a0\ufe0f  [DOWNLOAD] Cancelado. Sera retomado na proxima execucao.")
        return False
    except Exception as e:
        print(f"\u274c [DOWNLOAD] Falha: {e}")
        print(f"   Baixe manualmente: https://huggingface.co/{HF_REPO_ID}")
        print(f"   Salve o arquivo em: {MODELO_PATH}")
        return False

# ══════════════════════════════════════════
# 🌐 SERVIDOR FASTAPI
# ══════════════════════════════════════════
ai_brain = None
rag_ops = None
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
    global ai_brain, rag_ops, eu_ops, pizza_ops, noaa_ops, video_ops, astro_ops, air_ops, tiktok_ops, broker_ops
    
    os.makedirs("static/media", exist_ok=True)
    print("\n⚙️ [BOOT] Inicializando Módulos Táticos...")

    rag_ops = KnowledgeBase()

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

    AirTrafficControl = safe_import("air_traffic", "AirTrafficControl")
    AstroDefenseSystem = safe_import("astro_defense", "AstroDefenseSystem")
    air_ops = AirTrafficControl() if AirTrafficControl else None
    astro_ops = AstroDefenseSystem() if AstroDefenseSystem else None

    whisper_model_global = get_whisper_model() if WHISPER_AVAILABLE else None

    try:
        from video_ops import VideoSurgeon
        video_ops = VideoSurgeon(whisper_model=whisper_model_global)
        print("✂️ [TESOURA]: ONLINE")
    except Exception as e:
        print(f"✂️ [TESOURA]: OFFLINE → {e}")
        video_ops = None

    print("\n🧠 [CÉREBRO] Verificando modelo Gemma 4...")
    modelo_ok = verificar_e_baixar_modelo()
    if modelo_ok:
        try:
            from llama_cpp import Llama
            ai_brain = Llama(
                model_path=MODELO_PATH,
                n_ctx=32768, n_gpu_layers=20, verbose=False
            )
            print("✅ [CÉREBRO] Gemma 4 carregado com sucesso!")
        except Exception as e:
            print(f"❌ [CÉREBRO] Falha ao carregar: {e}")
            ai_brain = None
    else:
        print("❌ [CÉREBRO] Modelo indisponível. Inicie o sistema com o arquivo .gguf em: " + MODELO_PATH)
        ai_brain = None

    motores = {
        "🧠 CÉREBRO (Gemma 4)":       ai_brain,
        "📚 MEMÓRIA (RAG)":           rag_ops and rag_ops.index,
        "✂️ TESOURA (VideoSurgeon)":  video_ops,
        "📡 RADAR (NOAA)":            noaa_ops,
        "🍕 INTELIGÊNCIA (PizzaINT)": pizza_ops,
        "⚙️ CONSCIÊNCIA (CortexEU)":  eu_ops,
        "🎤 WHISPER (STT)":            WHISPER_AVAILABLE,
        "🚀 TIKTOK COMMANDER":        tiktok_ops,
        "🛸 DEFESA AÉREA":            air_ops,
        "☄️ DEFESA ASTEROIDE":        astro_ops,
    }
    for nome, obj in motores.items():
        status = "ONLINE" if obj else "OFFLINE"
        if nome == "🎤 WHISPER (STT)":
            status = "ONLINE" if obj else "OFFLINE (instale openai-whisper)"
        print(f"{nome}: {status}")

    yield
    
    print("[SHUTDOWN] Encerrando motores...")

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8000", "http://localhost:8000"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory="static"), name="static")

# ══════════════════════════════════════════
# 📡 ENDPOINTS REST (mantidos)
# ══════════════════════════════════════════

@app.post("/api/open_vscode")
async def open_vscode(payload: CodePayload):
    filepath = WORKSPACE / payload.filename
    try:
        with open(filepath, "w", encoding="utf-8") as f: f.write(payload.content)
        subprocess.Popen(["code", str(filepath)], shell=True)
        return {"ok": True}
    except Exception:
        return {"ok": False}

@app.post("/api/execute_code")
async def execute_code(payload: CodePayload):
    filepath = WORKSPACE / payload.filename
    try:
        with open(filepath, "w", encoding="utf-8") as f: f.write(payload.content)
        cmd = fr'cmd.exe /c "call {CONDA_ACTIVATE} && conda activate {CONDA_ENV} && python "{filepath}""'
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        out, err = process.communicate()
        return {"ok": True, "output": out + (f"\n--- ERRO ---\n{err}" if err else "")}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.post("/api/stop")
async def stop_generation():
    global _stop_generation
    _stop_generation = True
    return {"ok": True, "message": "Sinal de parada enviado."}

@app.post("/api/upload_arquivos")
async def upload_arquivos(arquivos: List[UploadFile] = File(...)):
    os.makedirs("static/docs", exist_ok=True)
    salvos = []
    erros = []
    for arq in arquivos:
        nome_seguro = re.sub(r'[^\w\-\.]', '_', arq.filename or "arquivo")
        destino = os.path.join("static/docs", nome_seguro)
        try:
            conteudo = await arq.read()
            with open(destino, "wb") as f:
                f.write(conteudo)
            salvos.append(nome_seguro)
        except Exception as e:
            erros.append(f"{arq.filename}: {str(e)}")
    if salvos:
        return {"ok": True, "arquivos": salvos, "erros": erros}
    return {"ok": False, "error": "Nenhum arquivo salvo.", "erros": erros}

@app.get("/api/tiktok/cortes")
async def listar_cortes():
    pasta = "static/media/cortes_virais"
    if not os.path.exists(pasta):
        os.makedirs(pasta, exist_ok=True)
        return []
    mp4s = glob.glob(os.path.join(pasta, "*.mp4"))
    resultado = [{"name": os.path.basename(mp4), "path": mp4.replace("\\", "/")} for mp4 in mp4s]
    return resultado

# ══════════════════════════════════════════
# 🔧 ROTAS ALPHA CORRIGIDAS
# ══════════════════════════════════════════

@app.get("/api/alpha/status")
def alpha_status():
    return alpha_engine.get_status()

@app.post("/api/broker/start")
def start_broker():
    if not broker_ops:
        raise HTTPException(status_code=503, detail="Módulo BrokerOperator offline.")
    return broker_ops.iniciar_sessao()

@app.post("/api/broker/stop_autopilot")
def stop_broker_autopilot():
    if not broker_ops:
        raise HTTPException(status_code=503, detail="Módulo BrokerOperator offline.")
    return broker_ops.execute_safe("AUTOPILOT_STOP")

@app.post("/api/broker/navigate")
def broker_navigate(body: NavigateRequest):
    if not broker_ops or not broker_ops._is_running:
        raise HTTPException(status_code=503, detail="Sessão Broker10 inativa.")
    return broker_ops.execute_safe("NAVIGATE", args={"url": body.url})

@app.post("/api/broker/calibrar")
def calibrar(body: CalibrateRequest):   # [BUG3] usa modelo Pydantic
    if not broker_ops or not broker_ops._is_running:
        raise HTTPException(status_code=503, detail="Broker inativo")
    # [BUG2] agora envia comando CLICK_COORD
    return broker_ops.execute_safe("CLICK_COORD", args={"x": body.x, "y": body.y})

@app.get("/api/broker/diagnostico")
def diagnostico():
    if not broker_ops or not broker_ops._is_running:
        return {"erro": "Broker inativo"}
    # [BUG4] diagnóstico movido para thread do navegador via comando interno
    return broker_ops.execute_safe("DIAGNOSTICO")

@app.post("/api/alpha/analyze")
def alpha_analyze():
    if broker_ops and broker_ops._is_running:
        return broker_ops.execute_safe("ANALYZE")
    if tiktok_ops and hasattr(tiktok_ops, "_page") and tiktok_ops._page:
        alpha_engine.attach(tiktok_ops._page)
        return alpha_engine.perceive_and_act()
    raise HTTPException(status_code=503, detail="Nenhuma sessão tática (Broker ou TikTok) aberta.")

@app.post("/api/alpha/autopilot")
def alpha_autopilot():
    if broker_ops and broker_ops._is_running:
        return broker_ops.execute_safe("AUTOPILOT_START")
    if tiktok_ops and hasattr(tiktok_ops, "_page") and tiktok_ops._page:
        alpha_engine.attach(tiktok_ops._page)
        return alpha_engine.run_until_success(max_cycles=9999, delay_between=0.5)
    raise HTTPException(status_code=503, detail="Nenhuma sessão tática aberta.")

@app.post("/api/alpha/override")
def alpha_override(body: AlphaActionRequest):
    if broker_ops and broker_ops._is_running:
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
def alpha_screenshot():
    if broker_ops and broker_ops._is_running:
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

# ══════════════════════════════════════════
# 📡 ROTAS TIKTOK (mantidas)
# ══════════════════════════════════════════

@app.get("/api/tiktok/fila")
def get_fila():
    return {"ok": True, "fila": tiktok_ops.get_fila() if tiktok_ops else []}

@app.post("/api/tiktok/add")
async def add_video(
    video: UploadFile = File(...),
    titulo: Optional[str]    = Form(None),
    descricao: Optional[str] = Form(None),
    hashtags: Optional[str]  = Form(None),
    agendar_para: Optional[str] = Form(None),
):
    if not tiktok_ops:
        raise HTTPException(status_code=503, detail="Módulo TikTok Commander offline")
    dest = os.path.join(UPLOAD_DIR, video.filename)
    with open(dest, "wb") as f:
        shutil.copyfileobj(video.file, f)
    item = tiktok_ops.adicionar(
        video_path   = os.path.abspath(dest),
        titulo       = titulo,
        descricao    = descricao,
        hashtags     = hashtags,
        agendar_para = agendar_para,
    )
    return {"ok": True, "item": item}

@app.post("/api/tiktok/post_now/{item_id}")
def post_now(item_id: str):
    if not tiktok_ops:
        raise HTTPException(status_code=503, detail="Módulo TikTok Commander offline")
    resultado = tiktok_ops.disparar_agora(item_id)
    if not resultado["ok"]:
        raise HTTPException(status_code=400, detail=resultado["erro"])
    return resultado

@app.delete("/api/tiktok/remover/{item_id}")
def remover(item_id: str):
    removido = tiktok_ops.remover(item_id) if tiktok_ops else False
    if not removido:
        raise HTTPException(status_code=404, detail="Item não encontrado.")
    return {"ok": True}

@app.get("/api/tiktok/status/{item_id}")
def status(item_id: str):
    fila = tiktok_ops.get_fila() if tiktok_ops else []
    item = next((i for i in fila if i["id"] == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado.")
    return {"ok": True, "item": item}

@app.get("/", response_class=HTMLResponse)
async def serve_gui(): 
    return FileResponse("static/index.html")

# ══════════════════════════════════════════
# 🧠 WEBSOCKET (MOTOR R2)
# ══════════════════════════════════════════

# [BUG1] Streaming Gemma 4 corrigido
async def stream_llama(ai_brain, prompt, stop_flag_getter):
    """Roda Gemma 4 em thread separada e yields tokens via queue síncrona."""
    q = Queue()
    
    def _run():
        try:
            for chunk in ai_brain(prompt, max_tokens=-1, stop=["<end_of_turn>"], stream=True):
                if stop_flag_getter():
                    q.put(None)
                    return
                q.put(chunk["choices"][0]["text"])
        finally:
            q.put(None)
    
    loop = asyncio.get_running_loop()
    # Dispara a thread em background sem bloquear
    loop.run_in_executor(None, _run)
    
    while True:
        try:
            token = await asyncio.to_thread(q.get, timeout=30)
            if token is None:
                break
            yield token
        except Empty:
            break

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global _stop_generation
    await websocket.accept()
    sessao_memoria_ram = carregar_historico_na_ram()
    sys_prompt = "Você é o R2, IA tática e Mestre Programador. REGRA: A primeira linha do código DEVE ser: # filename: nome.py"
    voz_atual = "Thalita"
    
    try:
        while True:
            raw = await websocket.receive_text()
            
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                data = None
            
            if data and isinstance(data, dict):
                if data.get("type") == "audio_input":
                    base64_audio = data.get("data", "")
                    if data.get("voice"):
                        voz_atual = data["voice"]
                    if not base64_audio:
                        await websocket.send_json({"type": "system", "text": "❌ Áudio vazio recebido."})
                        continue
                    
                    await websocket.send_json({"type": "system", "text": "🎤 Transcrevendo áudio..."})
                    texto_transcrito = await transcrever_audio_base64(base64_audio)
                    
                    if texto_transcrito.startswith("[ERRO]"):
                        await websocket.send_json({"type": "system", "text": texto_transcrito})
                        continue
                    
                    await websocket.send_json({"type": "system", "text": f"🎙️ Você disse: \"{texto_transcrito}\""})
                    comando = texto_transcrito

                elif data.get("type") == "command":
                    comando = data.get("text", "")
                    if data.get("voice"):
                        voz_atual = data["voice"]
                else:
                    comando = raw
            else:
                comando = raw
            
            cmd_l = comando.lower().strip()
            
            # Comandos do sistema (idênticos ao original)
            if cmd_l.startswith("/cmd "):
                sub = cmd_l.replace("/cmd ", "")
                if sub == "pizza" and pizza_ops:
                    await websocket.send_json({"type": "system", "text": pizza_ops.gerar_html_painel(await asyncio.to_thread(pizza_ops.get_status))})
                elif sub == "solar" and noaa_ops:
                    await websocket.send_json({"type": "system", "text": noaa_ops.gerar_html_painel(await asyncio.to_thread(noaa_ops.get_full_intel))})
                elif sub == "radar":
                    if air_ops:
                        filename, qtd, msg = await asyncio.to_thread(air_ops.radar_scan, "Ivinhema")
                        await websocket.send_json({"type": "system", "text": f"{msg}<br><img src='/{filename}' style='max-width:100%; border-radius:8px;'>"})
                    else:
                        await websocket.send_json({"type": "system", "text": "📡 Módulo de Radar não está disponível."})
                elif sub == "astro":
                    if astro_ops:
                        texto, astro_id, astro_nome = await asyncio.to_thread(astro_ops.get_asteroid_report)
                        await websocket.send_json({"type": "system", "text": texto})
                    else:
                        await websocket.send_json({"type": "system", "text": "☄️ Módulo de Defesa Planetária não está disponível."})
                elif sub == "tiktok":
                    await websocket.send_json({"type": "system", "text": "<button onclick='abrirCentralPostagem()' style='background:#0ea5e9;color:white;padding:10px 20px;border:none;border-radius:8px;cursor:pointer;font-weight:bold;margin-top:10px;'>📱 Abrir Central de Lançamento</button>"})
                else:
                    await websocket.send_json({"type": "system", "text": f"⚠️ Comando /cmd {sub} não reconhecido."})
                continue
                
            if cmd_l == "/doc sync":
                await websocket.send_json({"type": "system", "text": await asyncio.to_thread(rag_ops.sync)})
                continue

            if cmd_l == "/doc list":
                arquivos = rag_ops.arquivos_indexados
                if arquivos:
                    lista = "📋 **Arquivos Indexados:**\n" + "\n".join([f"- `{a}`" for a in arquivos])
                else:
                    lista = "📋 Nenhum arquivo indexado. Use `/doc sync` primeiro."
                await websocket.send_json({"type": "system", "text": lista})
                continue

            if cmd_l.startswith("/vid viral "):
                video_alvo = comando.replace("/vid viral ", "").strip()
                await websocket.send_json({"type": "system", "text": f"⏳ Tesoura Neural V4: Analisando {video_alvo}..."})
                
                if video_ops and ai_brain:
                    res = await asyncio.to_thread(video_ops.processar_video_viral, video_alvo, ai_brain)
                    if isinstance(res, list):
                        msg = "✅ **Cortes Virais Extraídos com Sucesso:**\n"
                        for r in res:
                            nome = os.path.basename(r)
                            url = r.replace("\\", "/")
                            msg += f"🎬 <b>{nome}</b><br><video src='/{url}' controls preload='metadata' style='width: 100%; max-width: 400px; border-radius: 8px; margin-bottom: 15px; border: 1px solid var(--border-hi); box-shadow: 0 0 10px rgba(14,165,233,0.1);'></video><br>"
                        await websocket.send_json({"type": "system", "text": msg})
                    else:
                        await websocket.send_json({"type": "system", "text": str(res)})
                else:
                    await websocket.send_json({"type": "system", "text": "❌ Tesoura Neural ou Cérebro Gemma 4 offline."})
                continue

            if cmd_l.startswith("/vid extract "):
                raw_config = comando[len("/vid extract "):].strip()
                await websocket.send_json({"type": "system", "text": "⏳ Tesoura Neural: Processando configurações de extração..."})
                try:
                    config = json.loads(raw_config)
                    video_url = config.get("url", "")
                    if not video_url:
                        await websocket.send_json({"type": "system", "text": "❌ URL do vídeo não fornecida."})
                        continue
                    if video_ops and ai_brain:
                        res = await asyncio.to_thread(video_ops.processar_video_viral, video_url, ai_brain)
                        if isinstance(res, list):
                            msg = "✅ **Extração concluída:**\n"
                            for r in res:
                                url = r.replace("\\", "/")
                                nome = os.path.basename(r)
                                msg += f"🎬 <b>{nome}</b><br><video src='/{url}' controls preload='metadata' style='width: 100%; max-width: 400px; border-radius: 8px; margin-bottom: 15px; border: 1px solid var(--border-hi); box-shadow: 0 0 10px rgba(14,165,233,0.1);'></video><br>"
                        else:
                            msg = str(res)
                        await websocket.send_json({"type": "system", "text": msg})
                    else:
                        await websocket.send_json({"type": "system", "text": "❌ Tesoura Neural ou Cérebro Gemma 4 offline."})
                except Exception as e:
                    await websocket.send_json({"type": "system", "text": f"❌ Erro ao processar config: {e}"})
                continue

            # Processamento normal pelo Gemma 4
            if ai_brain:
                global _stop_generation
                _stop_generation = False
                sessao_memoria_ram.append(f"Teddy: {comando}")
                ctx = await asyncio.to_thread(rag_ops.search, comando)
                # Gemma 4 chat template
                # Sistema + RAG + consciência injetados no primeiro turn do usuário
                sistema_bloco = sys_prompt
                if ctx: sistema_bloco += f"\n\n[RAG]: {ctx}"
                if eu_ops: sistema_bloco += f"\n\n{eu_ops.injetar_consciencia()}"

                prompt = ""
                historico_msgs = sessao_memoria_ram[-40:-1]
                primeiro_user = True
                i = 0
                while i < len(historico_msgs):
                    msg = historico_msgs[i]
                    if msg.startswith("Teddy: "):
                        conteudo = msg.split(': ', 1)[1]
                        if primeiro_user:
                            conteudo = f"{sistema_bloco}\n\n{conteudo}"
                            primeiro_user = False
                        prompt += f"<start_of_turn>user\n{conteudo}<end_of_turn>\n"
                    else:
                        conteudo = msg.split(': ', 1)[1]
                        prompt += f"<start_of_turn>model\n{conteudo}<end_of_turn>\n"
                    i += 1

                # Mensagem atual do usuário
                conteudo_atual = comando
                if primeiro_user:  # nenhum histórico anterior
                    conteudo_atual = f"{sistema_bloco}\n\n{comando}"
                prompt += f"<start_of_turn>user\n{conteudo_atual}<end_of_turn>\n<start_of_turn>model\n"
                
                resp = ""
                async for token in stream_llama(ai_brain, prompt, lambda: _stop_generation):
                    resp += token
                    await websocket.send_json({"type": "stream", "text": token})
                await websocket.send_json({"type": "done"})
                
                sessao_memoria_ram.append(f"R2: {resp}")
                salvar_no_historico_json(comando, resp)

                limpar_audios_antigos()

                try:
                    frases_taticas = [
                        "Afirmativo, senhor. Dados na tela.",
                        "Operação concluída, senhor. Resultados no console.",
                        "Pronto. Exibindo as informações solicitadas.",
                        "Busca finalizada. Verifique o painel principal.",
                        "Comando processado. Interface atualizada, senhor."
                    ]
                    gatilhos_leitura = ["mais informações", "leia tudo", "detalhes", "me conte mais", "leia para mim"]
                    leitura_completa = any(gatilho in comando.lower() for gatilho in gatilhos_leitura)
                    texto_audio = resp if leitura_completa else random.choice(frases_taticas)
                    
                    timestamp = int(time.time() * 1000)
                    audio_filename = f"r2_voice_{timestamp}.mp3"
                    audio_path = os.path.join("static/media", audio_filename)
                    
                    sucesso = await gerar_voz_r2(texto_audio, audio_path, voz_atual)
                    if sucesso:
                        audio_url = f"/static/media/{audio_filename}"
                        await websocket.send_json({
                            "type": "audio",
                            "url": audio_url,
                            "text": resp
                        })
                    else:
                        print("[AVISO] Falha na geração de áudio")
                except Exception as e:
                    print(f"[ERRO] Áudio pós-resposta: {e}")
                    
    except WebSocketDisconnect:
        pass

if __name__ == "__main__":
    import webview

    def run_server():
        uvicorn.run(app, host="127.0.0.1", port=8000, log_level="error")

    print("🚀 [BOOT] Ligando turbinas do servidor em segundo plano...")
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    print("🖥️ [BOOT] Desenhando Interface Nativa...")
    webview.create_window('R2 · Ghost Protocol', 'http://127.0.0.1:8000', width=1280, height=800)
    webview.start()