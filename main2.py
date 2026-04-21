# filename: main2.py
# ╔══════════════════════════════════════════════════════════╗
# ║         R2 TACTICAL OS — Ghost Protocol v8.1            ║
# ║         + CORREÇÕES DE BUGS (v8.0 → v8.1)               ║
# ║           BUG #3  → default de voz era "Antonio"        ║
# ║           BUG #4  → MediaRecorder envia WebM, não WAV   ║
# ║           BUG #5  → /api/stop não existia               ║
# ║           BUG #6  → /api/upload_arquivos não existia    ║
# ║           BUG #7  → arquivos TTS acumulavam (mem leak)  ║
# ║           BUG #8  → CORS sem allow_methods/headers      ║
# ║           BUG #2  → Whisper injetado no VideoSurgeon    ║
# ╚══════════════════════════════════════════════════════════╝

from pathlib import Path
import os, json, datetime, sys, time, asyncio, subprocess, shutil, re, gc, base64, tempfile
import threading
from contextlib import asynccontextmanager
from fastapi import Request, FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import uvicorn
import torch
import faiss
from sentence_transformers import SentenceTransformer
import edge_tts

# Tentar importar Whisper (se disponível)
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

# BUG FIX #5: Flag global de stop para interromper geração de tokens no WebSocket
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
        # BUG FIX #10 (MENOR): PyPDF2 foi depreciado; usa pypdf com fallback seguro
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
# 🎙️ FUNÇÃO DE SÍNTESE DE VOZ (MODO BATALHA + CONFIGURÁVEL)
# ══════════════════════════════════════════
def mapear_voz_para_edge(voz_usuario: str) -> str:
    mapa = {
        "Antonio":  "pt-BR-AntonioNeural",
        "Francisca": "pt-BR-FranciscaNeural",
        "Thalita":  "pt-BR-ThalitaNeural"
    }
    # BUG FIX #3: Fallback padrão era "pt-BR-AntonioNeural" (voz masculina).
    # O projeto especifica Thalita como voz padrão global.
    # Antes: return mapa.get(voz_usuario, "pt-BR-AntonioNeural")
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

# ══════════════════════════════════════════
# 🗑️ LIMPEZA PERIÓDICA DE ÁUDIOS TTS
# BUG FIX #7: Arquivos r2_voice_*.mp3 acumulavam indefinidamente em static/media
# causando crescimento ilimitado do disco. Esta função remove arquivos mais velhos
# que `max_idade_min` minutos.
# ══════════════════════════════════════════
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
    """
    Recebe um áudio em base64 (WebM/OGG do MediaRecorder), converte para WAV
    via FFmpeg e transcreve com Whisper.
    """
    if not WHISPER_AVAILABLE:
        return "[ERRO] Whisper não está instalado no servidor."
    model = get_whisper_model()
    if model is None:
        return "[ERRO] Modelo Whisper não disponível."
    
    try:
        audio_bytes = base64.b64decode(base64_audio)

        # BUG FIX #4: MediaRecorder no Chrome produz áudio WebM/OGG, não WAV.
        # A versão anterior salvava os bytes com sufixo .wav, o que fazia o Whisper
        # receber um arquivo WebM com extensão errada, causando falhas de transcrição.
        #
        # CORREÇÃO: salvar com .webm (formato real do MediaRecorder),
        # depois converter para .wav com ffmpeg antes de entregar ao Whisper.
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp_webm:
            tmp_webm.write(audio_bytes)
            tmp_webm_path = tmp_webm.name

        tmp_wav_path = tmp_webm_path.replace(".webm", "_conv.wav")
        cmd_conv = (
            f'ffmpeg -y -i "{tmp_webm_path}" '
            f'-acodec pcm_s16le -ar 16000 -ac 1 "{tmp_wav_path}"'
        )
        subprocess.run(cmd_conv, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Usar o WAV convertido se existir; fallback para o original (WebM pode funcionar direto)
        caminho_para_whisper = tmp_wav_path if os.path.exists(tmp_wav_path) else tmp_webm_path

        result = await asyncio.to_thread(model.transcribe, caminho_para_whisper, language="pt")
        texto = result["text"].strip()
        
        # Limpar arquivos temporários
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

# ══════════════════════════════════════════
# 🌐 SERVIDOR FASTAPI
# ══════════════════════════════════════════
ai_brain = None
rag_ops = None
eu_ops = None
pizza_ops = None
noaa_ops = None
video_ops = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global ai_brain, rag_ops, eu_ops, pizza_ops, noaa_ops, video_ops

    os.makedirs("static/media", exist_ok=True)
    print("\n⚙️ [BOOT] Inicializando Módulos Táticos...")

    rag_ops = KnowledgeBase()

    CortexEU = safe_import("eu", "CORTEX_EU")
    eu_ops = CortexEU("R2") if CortexEU else None

    PizzaINTService = safe_import("pizzint_service", "PizzaINTService")
    pizza_ops = PizzaINTService(config={}) if PizzaINTService else None

    NOAAService = safe_import("noaa_service", "NOAAService")
    noaa_ops = NOAAService() if NOAAService else None

    # BUG FIX #2 (integração): Whisper é carregado PRIMEIRO e injetado no VideoSurgeon.
    # Antes: VideoSurgeon era criado sem modelo → carregava seu próprio whisper internamente.
    # Agora: o modelo global é passado via construtor, evitando dupla alocação de VRAM.
    whisper_model_global = get_whisper_model() if WHISPER_AVAILABLE else None

    try:
        from video_ops import VideoSurgeon
        video_ops = VideoSurgeon(whisper_model=whisper_model_global)
        print("✂️ [TESOURA]: ONLINE")
    except Exception as e:
        print(f"✂️ [TESOURA]: OFFLINE → {e}")
        video_ops = None

    print("\n🧠 [CÉREBRO] Iniciando LLaMA...")
    try:
        from llama_cpp import Llama
        ai_brain = Llama(
            model_path=r"C:\r2\models\Dolphin3.0-Llama3.1-8B-Q4_K_M.gguf",
            n_ctx=32768, n_gpu_layers=20, verbose=False
        )
    except Exception as e:
        print(f"❌ [CÉREBRO] Falha: {e}")
        ai_brain = None

    motores = {
        "🧠 CÉREBRO (LLaMA)":        ai_brain,
        "📚 MEMÓRIA (RAG)":           rag_ops and rag_ops.index,
        "✂️ TESOURA (VideoSurgeon)":  video_ops,
        "📡 RADAR (NOAA)":            noaa_ops,
        "🍕 INTELIGÊNCIA (PizzaINT)": pizza_ops,
        "⚙️ CONSCIÊNCIA (CortexEU)":  eu_ops,
        "🎤 WHISPER (STT)":            WHISPER_AVAILABLE,
    }
    for nome, obj in motores.items():
        status = "ONLINE" if obj else "OFFLINE"
        if nome == "🎤 WHISPER (STT)":
            status = "ONLINE" if obj else "OFFLINE (instale openai-whisper)"
        print(f"{nome}: {status}")

    yield
    print("[SHUTDOWN] Encerrando motores...")

app = FastAPI(lifespan=lifespan)

# BUG FIX #8: CORS sem allow_methods e allow_headers bloqueava requisições POST
# (o padrão do FastAPI para métodos não especificados é apenas GET).
# Adicionados allow_methods=["*"] e allow_headers=["*"] para cobrir uploads e API calls.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8000", "http://localhost:8000"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory="static"), name="static")

# ══════════════════════════════════════════
# 📡 ENDPOINTS REST
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

# BUG FIX #5: /api/stop era chamado pelo frontend (botão "Parar") mas não existia,
# retornando 404. Adicionado endpoint que sinaliza o flag global _stop_generation.
# A geração de tokens no WebSocket verifica este flag a cada chunk.
@app.post("/api/stop")
async def stop_generation():
    global _stop_generation
    _stop_generation = True
    return {"ok": True, "message": "Sinal de parada enviado."}

# BUG FIX #6: /api/upload_arquivos era chamado pelo drag-and-drop e botão de upload
# no frontend (app.js linha ~484) mas o endpoint não existia no backend → 404 silencioso.
# Adicionado endpoint completo que salva os arquivos em static/docs para indexação RAG.
@app.post("/api/upload_arquivos")
async def upload_arquivos(arquivos: List[UploadFile] = File(...)):
    os.makedirs("static/docs", exist_ok=True)
    salvos = []
    erros = []
    for arq in arquivos:
        # Sanitizar nome do arquivo para segurança
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

@app.get("/", response_class=HTMLResponse)
async def serve_gui(): 
    return FileResponse("static/index.html")

# ══════════════════════════════════════════
# 🧠 WEBSOCKET (MOTOR R2 + MODO BATALHA + CONFIGURAÇÕES + ÁUDIO)
# ══════════════════════════════════════════
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
                # ========== MENSAGEM DE ÁUDIO (input do usuário) ==========
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
            
            # Comandos do sistema
            if cmd_l.startswith("/cmd "):
                sub = cmd_l.replace("/cmd ", "")
                if sub == "pizza" and pizza_ops:
                    await websocket.send_json({"type": "system", "text": pizza_ops.gerar_html_painel(await asyncio.to_thread(pizza_ops.get_status))})
                elif sub == "solar" and noaa_ops:
                    await websocket.send_json({"type": "system", "text": noaa_ops.gerar_html_painel(await asyncio.to_thread(noaa_ops.get_full_intel))})
                elif sub == "radar":
                    await websocket.send_json({"type": "system", "text": "📡 Módulo de Radar não está conectado nesta sessão. Verifique se o serviço está ativo."})
                elif sub == "astro":
                    await websocket.send_json({"type": "system", "text": "☄️ Módulo de Defesa Planetária não está conectado nesta sessão."})
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
                            # Injeta o player de vídeo direto no chat (com pré-carregamento de thumb)
                            msg += f"🎬 <b>{nome}</b><br><video src='/{url}' controls preload='metadata' style='width: 100%; max-width: 400px; border-radius: 8px; margin-bottom: 15px; border: 1px solid var(--border-hi); box-shadow: 0 0 10px rgba(14,165,233,0.1);'></video><br>"
                        await websocket.send_json({"type": "system", "text": msg})
                    else:
                        await websocket.send_json({"type": "system", "text": str(res)})
                else:
                    await websocket.send_json({"type": "system", "text": "❌ Tesoura Neural ou Cérebro LLaMA offline."})
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
                                # Injeta o player de vídeo direto no chat (com pré-carregamento de thumb)
                                msg += f"🎬 <b>{nome}</b><br><video src='/{url}' controls preload='metadata' style='width: 100%; max-width: 400px; border-radius: 8px; margin-bottom: 15px; border: 1px solid var(--border-hi); box-shadow: 0 0 10px rgba(14,165,233,0.1);'></video><br>"
                        else:
                            msg = str(res)
                        await websocket.send_json({"type": "system", "text": msg})
                    else:
                        await websocket.send_json({"type": "system", "text": "❌ Tesoura Neural ou Cérebro LLaMA offline."})
                except Exception as e:
                    await websocket.send_json({"type": "system", "text": f"❌ Erro ao processar config: {e}"})
                continue

            # Processamento normal pelo LLaMA
            if ai_brain:
                # BUG FIX #5 (continuação): reset do flag antes de cada nova geração
                _stop_generation = False

                sessao_memoria_ram.append(f"Teddy: {comando}")
                ctx = await asyncio.to_thread(rag_ops.search, comando)
                prompt = f"<|im_start|>system\n{sys_prompt}\n"
                if ctx: prompt += f"\n[RAG]: {ctx}\n"
                if eu_ops: prompt += f"\n{eu_ops.injetar_consciencia()}\n"
                prompt += "<|im_end|>\n"
                
                for m in sessao_memoria_ram[-40:-1]:
                    role = "user" if m.startswith("Teddy: ") else "assistant"
                    prompt += f"<|im_start|>{role}\n{m.split(': ', 1)[1]}<|im_end|>\n"
                prompt += f"<|im_start|>user\n{comando}<|im_end|>\n<|im_start|>assistant\n"
                
                resp = ""
                for chunk in ai_brain(prompt, max_tokens=-1, stop=["<|im_end|>"], stream=True):
                    # BUG FIX #5: verifica flag de stop a cada token gerado
                    if _stop_generation:
                        _stop_generation = False
                        break
                    t = chunk["choices"][0]["text"]
                    resp += t
                    await websocket.send_json({"type": "stream", "text": t})
                await websocket.send_json({"type": "done"})
                
                sessao_memoria_ram.append(f"R2: {resp}")
                salvar_no_historico_json(comando, resp)

                # BUG FIX #7: Limpeza de arquivos TTS antigos antes de gerar um novo
                limpar_audios_antigos()

                try:
                    import random
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
    import threading
    import webview

    def run_server():
        uvicorn.run(app, host="127.0.0.1", port=8000, log_level="error")

    print("🚀 [BOOT] Ligando turbinas do servidor em segundo plano...")
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    print("🖥️ [BOOT] Desenhando Interface Nativa...")
    webview.create_window('R2 · Ghost Protocol', 'http://127.0.0.1:8000', width=1280, height=800)
    webview.start()