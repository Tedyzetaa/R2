# filename: main2.py
# ╔══════════════════════════════════════════════════════════╗
# ║         R2 TACTICAL OS — Ghost Protocol v5.0            ║
# ║         Reconstrução Total — Sem Bugs, Sem Duplicatas   ║
# ╚══════════════════════════════════════════════════════════╝

# ══════════════════════════════════════════
# IMPORTS (limpos, sem duplicatas)
# ══════════════════════════════════════════
from pathlib import Path
import os, json, datetime, sys, time, asyncio, subprocess, shutil, re, gc
import threading
from fastapi import Request, FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import torch
import faiss
from sentence_transformers import SentenceTransformer

# ══════════════════════════════════════════
# CONFIGURAÇÃO DO WORKSPACE
# ══════════════════════════════════════════
WORKSPACE = Path(r"c:\r2")
WORKSPACE.mkdir(parents=True, exist_ok=True)

# ══════════════════════════════════════════
# PAYLOADS PYDANTIC
# ══════════════════════════════════════════
class CodePayload(BaseModel):
    filename: str
    content: str

# ══════════════════════════════════════════
# 💾 MEMÓRIA PERSISTENTE (JSON)
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
    # return []  # <-- REMOVIDA (Bug 7)

# ══════════════════════════════════════════
# 📂 IMPORTAÇÕES TÁTICAS SEGURAS
# ══════════════════════════════════════════
def safe_import(module_name, class_name):
    try:
        import importlib
        mod = importlib.import_module(f"features.{module_name}")
        return getattr(mod, class_name)
    except Exception as e:
        print(f"⚠️ Módulo {class_name} ({module_name}) indisponível: {e}")
        return None

AirTrafficControl  = safe_import("air_traffic",     "AirTrafficControl")
AstroDefenseSystem = safe_import("astro_defense",   "AstroDefenseSystem")
PizzaINTService    = safe_import("pizzint_service",  "PizzaINTService")
NOAAService        = safe_import("noaa_service",     "NOAAService")
GeoSeismicSystem   = safe_import("geo_seismic",     "GeoSeismicSystem")
SpeedTestModule    = safe_import("net_speed",        "SpeedTestModule")
CortexEU           = safe_import("eu",               "CORTEX_EU")

VideoSurgeon = safe_import("video_ops", "VideoSurgeon")
if not VideoSurgeon:
    try:
        from video_ops import VideoSurgeon
        print("✂️ [TESOURA NEURAL]: Carregada da raiz.")
    except:
        VideoSurgeon = None
video_ops = VideoSurgeon() if VideoSurgeon else None

# ══════════════════════════════════════════
# 📚 NÚCLEO RAG COM MEMÓRIA PERSISTENTE
# ══════════════════════════════════════════
class KnowledgeBase:
    def __init__(self, docs_dir="static/docs"):
        self.docs_dir = docs_dir
        self.index_path = os.path.join(self.docs_dir, "faiss_index.bin")
        self.data_path  = os.path.join(self.docs_dir, "rag_data.json")
        self.embedder   = None
        self.index      = None
        self.chunks     = []
        self.arquivos_indexados = []
        os.makedirs(self.docs_dir, exist_ok=True)
        self.carregar_memoria()

    def carregar_memoria(self):
        if os.path.exists(self.index_path) and os.path.exists(self.data_path):
            try:
                self.index = faiss.read_index(self.index_path)
                with open(self.data_path, "r", encoding="utf-8") as f:
                    dados = json.load(f)
                self.chunks = dados.get("chunks", [])
                self.arquivos_indexados = dados.get("arquivos_indexados", [])
                print(f"📚 [RAG]: Memória restaurada! {len(self.arquivos_indexados)} arquivos.")
            except:
                print("⚠️ [RAG]: Erro ao ler memória. Use /doc sync para recriar.")
        else:
            print("⚠️ [RAG]: Cofre vazio. Use /doc sync.")

    def sync(self):
        import PyPDF2
        if not self.embedder:
            self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        self.chunks = []
        self.arquivos_indexados = []
        arquivos = [f for f in os.listdir(self.docs_dir) if f.lower().endswith(('.pdf', '.md'))]
        if not arquivos:
            return "⚠️ Nenhum documento em static/docs."
        for arq in arquivos:
            try:
                p = os.path.join(self.docs_dir, arq)
                if arq.endswith('.pdf'):
                    with open(p, 'rb') as f:
                        text = "".join([pg.extract_text() or "" for pg in PyPDF2.PdfReader(f).pages])
                else:
                    with open(p, 'r', encoding='utf-8') as f:
                        text = f.read()
                if text.strip():
                    self.arquivos_indexados.append(arq)
                    for i in range(0, len(text), 800):
                        chunk = text[i:i+1000].encode('utf-8', 'ignore').decode('utf-8')
                        chunk = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', ' ', chunk).strip()
                        if len(chunk) > 50:
                            self.chunks.append(f"[Fonte: {arq}] {chunk}")
            except:
                continue
        if not self.chunks:
            return "❌ Extração falhou."
        embeddings = self.embedder.encode(self.chunks, convert_to_numpy=True, show_progress_bar=True)
        self.index = faiss.IndexFlatL2(embeddings.shape[1])
        self.index.add(embeddings)
        try:
            faiss.write_index(self.index, self.index_path)
            with open(self.data_path, "w", encoding="utf-8") as f:
                json.dump({"chunks": self.chunks, "arquivos_indexados": self.arquivos_indexados}, f, ensure_ascii=False)
        except Exception as e:
            return f"⚠️ Gravado em RAM, erro no HD: {e}"
        return f"✅ Cérebro blindado! {len(self.arquivos_indexados)} arquivos integrados."

    def search(self, query):
        if not self.index:
            return None
        if not self.embedder:
            self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        q_emb = self.embedder.encode([query], convert_to_numpy=True)
        _, indices = self.index.search(q_emb, 3)
        return "\n\n".join([self.chunks[idx] for idx in indices[0] if idx < len(self.chunks)])

# ══════════════════════════════════════════
# 🎨 MOTOR VISUAL
# ══════════════════════════════════════════
class UltraVisualCore:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.pipe   = None
        self.caminho = "visual_models/Realistic_Vision_V5.1.safetensors"

    def generate(self, prompt):
        if not self.pipe:
            from diffusers import StableDiffusionPipeline
            self.pipe = StableDiffusionPipeline.from_single_file(
                self.caminho, torch_dtype=torch.float16,
                use_safetensors=True, local_files_only=True
            )
            self.pipe.enable_model_cpu_offload()
            self.pipe.enable_attention_slicing()
        with torch.inference_mode():
            return self.pipe(
                prompt=f"RAW photo, {prompt}, 8k uhd",
                negative_prompt="cgi, render, cartoon",
                num_inference_steps=25, height=768, width=512
            ).images[0]

# ══════════════════════════════════════════
# INICIALIZAÇÃO DOS MÓDULOS
# ══════════════════════════════════════════
os.makedirs("static/media", exist_ok=True)
rag_ops   = KnowledgeBase()
eu_ops    = CortexEU("R2") if CortexEU else None
img_ops   = UltraVisualCore()
radar_ops = AirTrafficControl()  if AirTrafficControl  else None
astro_ops = AstroDefenseSystem() if AstroDefenseSystem else None
pizza_ops = PizzaINTService(config={}) if PizzaINTService else None
noaa_ops  = NOAAService()        if NOAAService        else None

# CORREÇÃO: bloco try-except com mensagem detalhada (Bug 9)
try:
    from llama_cpp import Llama
    print("🧠 [CÉREBRO] Iniciando LLaMA otimizado...")
    ai_brain = Llama(
        model_path="models/Dolphin3.0-Llama3.1-8B-Q4_K_M.gguf",
        n_ctx=32768, n_gpu_layers=20, verbose=False
    )
except Exception as e:
    print(f"❌ [CÉREBRO] Falha ao carregar LLaMA: {e}")
    ai_brain = None

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["http://127.0.0.1:8000", "http://localhost:8000"])
app.mount("/static", StaticFiles(directory="static"), name="static")

STOP_GEN   = False


# ══════════════════════════════════════════
# 🖥️ HTML TEMPLATE — INTERFACE RECONSTRUÍDA
# ══════════════════════════════════════════
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=0">
<title>R2 · Ghost Protocol</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;500;600;700&family=Share+Tech+Mono&family=Inter:wght@300;400;500&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/styles/tokyo-night-dark.min.css">
<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/highlight.min.js"></script>
<style>
/* ══ TOKENS ══════════════════════════════════════════ */
:root {
  --bg:        #020b14;
  --surface:   #061221;
  --panel:     #091929;
  --border:    rgba(14,165,233,0.12);
  --border-hi: rgba(14,165,233,0.35);
  --blue:      #0ea5e9;
  --blue-dim:  rgba(14,165,233,0.07);
  --green:     #10b981;
  --green-dim: rgba(16,185,129,0.07);
  --amber:     #f59e0b;
  --red:       #ef4444;
  --purple:    #a855f7;
  --text:      #94a3b8;
  --text-muted:#334155;
  --text-hi:   #e2e8f0;
  --radius:    10px;
  --sidebar-w: 270px;
}

*,*::before,*::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body {
  height: 100%;
  overflow: hidden;
  background: var(--bg);
  color: var(--text);
  font-family: 'Inter', sans-serif;
  font-size: 15px;
  line-height: 1.6;
}

::-webkit-scrollbar { width: 3px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(14,165,233,0.25); border-radius: 2px; }

/* ══ GRID BACKGROUND ══════════════════════════════════ */
body::before {
  content: '';
  position: fixed; inset: 0;
  background-image:
    linear-gradient(rgba(14,165,233,0.025) 1px, transparent 1px),
    linear-gradient(90deg, rgba(14,165,233,0.025) 1px, transparent 1px);
  background-size: 52px 52px;
  pointer-events: none; z-index: 0;
}
body::after {
  content: '';
  position: fixed; inset: 0;
  background:
    radial-gradient(ellipse 70% 50% at 50% -10%, rgba(14,165,233,0.08) 0%, transparent 70%),
    radial-gradient(ellipse 40% 30% at 90% 90%, rgba(168,85,247,0.04) 0%, transparent 60%);
  pointer-events: none; z-index: 0;
}

/* ══ SCANLINE ══════════════════════════════════════════ */
@keyframes scanline {
  0%   { transform: translateY(-100vh); }
  100% { transform: translateY(200vh); }
}
.scanline {
  position: fixed; top: 0; left: 0; right: 0; height: 1px;
  background: linear-gradient(90deg, transparent 0%, rgba(14,165,233,0.2) 50%, transparent 100%);
  animation: scanline 10s linear infinite;
  pointer-events: none; z-index: 1;
}

/* ══ LAYOUT ══════════════════════════════════════════ */
#app {
  position: relative;
  display: flex;
  flex-direction: column;
  height: 100vh;
  z-index: 2;
}

/* ══ HEADER ══════════════════════════════════════════ */
#header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  height: 58px;
  background: rgba(6, 18, 33, 0.96);
  border-bottom: 1px solid var(--border);
  backdrop-filter: blur(16px);
  flex-shrink: 0;
  position: relative;
  z-index: 5000;
}

.header-left  { display: flex; align-items: center; gap: 14px; }
.header-right { display: flex; align-items: center; gap: 12px; }

#menu-btn {
  background: none;
  border: 1px solid var(--border);
  color: var(--blue);
  width: 36px; height: 36px;
  border-radius: 8px;
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: all 0.2s;
  flex-shrink: 0;
}
#menu-btn:hover {
  background: var(--blue-dim);
  border-color: var(--border-hi);
  box-shadow: 0 0 14px rgba(14,165,233,0.18);
}
#menu-btn svg { width: 17px; height: 17px; }

.logo { display: flex; align-items: center; gap: 10px; }
.logo-icon {
  width: 32px; height: 32px;
  background: linear-gradient(135deg, rgba(14,165,233,0.2), rgba(168,85,247,0.1));
  border: 1px solid var(--border-hi);
  border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  font-family: 'Share Tech Mono', monospace;
  font-size: 12px;
  color: var(--blue);
  font-weight: bold;
  box-shadow: 0 0 12px rgba(14,165,233,0.15);
}
.logo-text { display: flex; flex-direction: column; line-height: 1.1; }
.logo-title {
  font-family: 'Rajdhani', sans-serif;
  font-size: 16px; font-weight: 700;
  color: var(--text-hi);
  letter-spacing: 2px; text-transform: uppercase;
}
.logo-sub {
  font-family: 'Share Tech Mono', monospace;
  font-size: 9px; color: var(--text-muted);
  letter-spacing: 2.5px;
}

/* Status pill */
.status-pill {
  display: flex; align-items: center; gap: 7px;
  font-family: 'Share Tech Mono', monospace;
  font-size: 10px; color: var(--green);
  background: var(--green-dim);
  border: 1px solid rgba(16,185,129,0.2);
  padding: 5px 12px; border-radius: 20px;
  letter-spacing: 1.5px;
  transition: all 0.3s;
}
.status-pill.offline {
  color: var(--red);
  background: rgba(239,68,68,0.06);
  border-color: rgba(239,68,68,0.2);
}
@keyframes pulse-dot {
  0%,100% { opacity: 1; transform: scale(1); }
  50%      { opacity: 0.4; transform: scale(0.65); }
}
.status-dot {
  width: 7px; height: 7px; border-radius: 50%;
  background: var(--green);
  box-shadow: 0 0 7px var(--green);
  animation: pulse-dot 2s ease-in-out infinite;
}
.status-dot.offline {
  background: var(--red);
  box-shadow: 0 0 7px var(--red);
  animation: none;
}

/* Clear btn */
#clear-btn {
  background: none;
  border: 1px solid var(--border);
  color: var(--text-muted);
  width: 32px; height: 32px;
  border-radius: 8px;
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: all 0.2s;
  font-size: 13px;
}
#clear-btn:hover { border-color: rgba(239,68,68,0.4); color: var(--red); background: rgba(239,68,68,0.06); }

/* ══ SIDEBAR OVERLAY ══════════════════════════════════ */
#overlay {
  display: none; position: fixed; inset: 0;
  background: rgba(0,0,0,0.55);
  backdrop-filter: blur(3px);
  z-index: 200; opacity: 0;
  transition: opacity 0.3s;
}
#overlay.active { display: block; opacity: 1; }

/* ══ SIDEBAR ══════════════════════════════════════════ */
#sidebar {
  position: fixed;
  left: calc(-1 * var(--sidebar-w) - 20px);
  top: 0; width: var(--sidebar-w); height: 100%;
  background: rgba(6, 18, 33, 0.99);
  border-right: 1px solid var(--border);
  z-index: 300;
  padding: 18px 14px;
  display: flex; flex-direction: column; gap: 4px;
  transition: left 0.32s cubic-bezier(0.4,0,0.2,1);
  overflow-y: auto;
  backdrop-filter: blur(24px);
}
#sidebar.open { left: 0; }

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 6px 16px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 8px;
}
.sidebar-brand {
  font-family: 'Rajdhani', sans-serif;
  font-size: 14px; font-weight: 700;
  color: var(--text-hi); letter-spacing: 2px;
  text-transform: uppercase;
}
.sidebar-close {
  background: none; border: none;
  color: var(--text-muted); cursor: pointer;
  font-size: 16px; line-height: 1;
  padding: 4px;
  transition: color 0.2s;
}
.sidebar-close:hover { color: var(--text-hi); }

.sidebar-label {
  font-family: 'Share Tech Mono', monospace;
  font-size: 9px; color: var(--text-muted);
  letter-spacing: 3px; padding: 12px 8px 6px;
  text-transform: uppercase;
}

.mod-btn {
  display: flex; align-items: center; gap: 11px;
  padding: 10px 12px;
  background: transparent;
  border: 1px solid transparent;
  border-radius: var(--radius);
  color: var(--text);
  font-family: 'Inter', sans-serif;
  font-size: 13.5px; font-weight: 500;
  cursor: pointer; text-align: left;
  transition: all 0.18s; width: 100%;
}
.mod-btn .icon {
  width: 30px; height: 30px; border-radius: 7px;
  display: flex; align-items: center; justify-content: center;
  font-size: 14px; flex-shrink: 0;
  background: var(--blue-dim);
  border: 1px solid var(--border);
  transition: all 0.18s;
}
.mod-btn:hover {
  background: var(--blue-dim);
  border-color: var(--border-hi);
  color: var(--text-hi);
  transform: translateX(3px);
}
.mod-btn:hover .icon {
  background: rgba(14,165,233,0.14);
  border-color: var(--border-hi);
  box-shadow: 0 0 10px rgba(14,165,233,0.18);
}

.sidebar-divider { height: 1px; background: var(--border); margin: 6px 0; }

/* ══ CHAT AREA ══════════════════════════════════════ */
#chat-wrapper {
  flex: 1; overflow-y: auto;
  padding: 24px 16px;
  display: flex; flex-direction: column; align-items: center;
}
#chat {
  width: 100%; max-width: 860px;
  display: flex; flex-direction: column; gap: 14px;
}

/* Boot screen */
.boot-msg {
  text-align: center;
  padding: 52px 20px 36px;
  animation: fadeUp 0.7s ease both;
}
.boot-logo {
  font-family: 'Rajdhani', sans-serif;
  font-size: 56px; font-weight: 700;
  background: linear-gradient(135deg, var(--blue) 0%, #60a5fa 50%, var(--purple) 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  letter-spacing: 8px; margin-bottom: 8px;
  filter: drop-shadow(0 0 30px rgba(14,165,233,0.3));
}
.boot-tagline {
  font-family: 'Share Tech Mono', monospace;
  font-size: 11px; color: var(--text-muted);
  letter-spacing: 4px; margin-bottom: 36px;
  text-transform: uppercase;
}
.boot-grid {
  display: grid; grid-template-columns: repeat(3, 1fr);
  gap: 8px; max-width: 460px; margin: 0 auto;
}
.boot-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 13px 10px;
  font-size: 11px; color: var(--text-muted);
  cursor: pointer; transition: all 0.2s;
  font-family: 'Share Tech Mono', monospace;
  letter-spacing: 0.5px;
}
.boot-card:hover {
  border-color: var(--border-hi);
  color: var(--blue);
  background: var(--blue-dim);
  transform: translateY(-1px);
}

/* Message animations */
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(10px); }
  to   { opacity: 1; transform: translateY(0); }
}

/* Messages */
.msg { display: flex; gap: 11px; animation: fadeUp 0.22s ease both; max-width: 100%; }
.msg.user { flex-direction: row-reverse; }

.msg-avatar {
  width: 30px; height: 30px; border-radius: 8px;
  flex-shrink: 0; display: flex;
  align-items: center; justify-content: center;
  font-family: 'Share Tech Mono', monospace;
  font-size: 10px; font-weight: bold;
  align-self: flex-end;
}
.msg.user .msg-avatar {
  background: rgba(14,165,233,0.13);
  border: 1px solid rgba(14,165,233,0.28);
  color: var(--blue);
}
.msg.bot .msg-avatar {
  background: rgba(16,185,129,0.1);
  border: 1px solid rgba(16,185,129,0.22);
  color: var(--green);
}
.msg.sys .msg-avatar {
  background: rgba(245,158,11,0.09);
  border: 1px solid rgba(245,158,11,0.22);
  color: var(--amber);
}

.msg-body {
  display: flex; flex-direction: column; gap: 3px;
  max-width: calc(100% - 42px);
}
.msg.user .msg-body { align-items: flex-end; }

.msg-sender {
  font-family: 'Share Tech Mono', monospace;
  font-size: 9px; color: var(--text-muted);
  letter-spacing: 2px; text-transform: uppercase;
}

.msg-bubble {
  padding: 11px 15px; border-radius: 12px;
  font-size: 14.5px; line-height: 1.68;
  word-break: break-word; max-width: 100%;
}
.msg.user .msg-bubble {
  background: rgba(14,165,233,0.09);
  border: 1px solid rgba(14,165,233,0.22);
  border-bottom-right-radius: 3px;
  color: var(--text-hi);
}
.msg.bot .msg-bubble {
  background: var(--surface);
  border: 1px solid var(--border);
  border-bottom-left-radius: 3px;
  color: var(--text); width: 100%;
}
.msg.sys .msg-bubble {
  background: rgba(245,158,11,0.05);
  border: 1px solid rgba(245,158,11,0.18);
  color: #fbbf24;
  font-family: 'Share Tech Mono', monospace;
  font-size: 13px;
}

/* Markdown in bot messages */
.msg-bubble h1,.msg-bubble h2,.msg-bubble h3 {
  color: var(--text-hi);
  font-family: 'Rajdhani', sans-serif;
  letter-spacing: 0.5px; margin: 14px 0 6px;
}
.msg-bubble p  { margin: 6px 0; }
.msg-bubble ul,.msg-bubble ol { padding-left: 20px; margin: 4px 0; }
.msg-bubble a  { color: var(--blue); }
.msg-bubble b,.msg-bubble strong { color: var(--text-hi); }
.msg-bubble img   { max-width: 100%; border-radius: 8px; margin-top: 8px; }
.msg-bubble video { max-width: 100%; border-radius: 8px; margin-top: 8px; }

/* Inline code */
.msg-bubble code {
  background: rgba(14,165,233,0.1);
  border: 1px solid var(--border);
  padding: 1px 6px; border-radius: 4px;
  font-family: 'Share Tech Mono', monospace;
  font-size: 13px; color: var(--blue);
}

/* Code block */
.msg-bubble pre {
  background: #050d18;
  border: 1px solid var(--border);
  border-radius: 10px 10px 0 0;
  padding: 14px 16px;
  overflow-x: auto; margin: 12px 0 0;
  position: relative;
}
.msg-bubble pre code {
  background: none; border: none;
  padding: 0; color: inherit;
  font-size: 13px;
}

/* ══ CODE ACTION BAR ══════════════════════════════════ */
.code-action-bar {
  display: flex; align-items: center; justify-content: space-between;
  background: #040c16;
  border: 1px solid var(--border);
  border-top: 1px solid rgba(14,165,233,0.08);
  border-radius: 0 0 10px 10px;
  margin-bottom: 12px;
  padding: 7px 12px;
  font-family: 'Share Tech Mono', monospace;
  font-size: 11px;
}
.code-filename {
  display: flex; align-items: center; gap: 6px;
  color: rgba(14,165,233,0.6);
  letter-spacing: 0.5px;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.code-filename svg { flex-shrink: 0; opacity: 0.7; }
.code-actions { display: flex; gap: 6px; flex-shrink: 0; }

.code-btn {
  display: flex; align-items: center; gap: 5px;
  padding: 4px 10px; border-radius: 6px;
  font-family: 'Share Tech Mono', monospace;
  font-size: 10px; cursor: pointer;
  transition: all 0.18s; border: 1px solid;
  letter-spacing: 0.5px; white-space: nowrap;
}
.code-btn.vscode {
  background: rgba(0,120,212,0.1);
  border-color: rgba(0,120,212,0.35);
  color: #60a5fa;
}
.code-btn.vscode:hover {
  background: rgba(0,120,212,0.22);
  border-color: rgba(0,120,212,0.6);
  color: #93c5fd;
  box-shadow: 0 0 10px rgba(0,120,212,0.2);
}
.code-btn.exec {
  background: rgba(16,185,129,0.1);
  border-color: rgba(16,185,129,0.3);
  color: var(--green);
}
.code-btn.exec:hover {
  background: rgba(16,185,129,0.2);
  border-color: rgba(16,185,129,0.55);
  box-shadow: 0 0 10px rgba(16,185,129,0.2);
}
.code-btn:disabled { opacity: 0.45; cursor: not-allowed; }
.code-btn svg { width: 11px; height: 11px; }

/* Exec output terminal */
.exec-terminal {
  background: #000;
  border: 1px solid rgba(16,185,129,0.25);
  border-top: none;
  border-radius: 0 0 10px 10px;
  padding: 10px 14px;
  font-family: 'Share Tech Mono', monospace;
  font-size: 12px;
  color: #10b981;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: none;
  overflow-y: auto;
  margin-top: -12px;
  margin-bottom: 12px;
  display: none;
}
.exec-terminal.visible { display: block; }
.exec-terminal .err { color: #f87171; }

/* ══ TYPING ══════════════════════════════════════════ */
@keyframes blink {
  0%,80%,100% { transform: scale(0.6); opacity: 0.25; }
  40%         { transform: scale(1); opacity: 1; }
}
.typing-dots { display: flex; align-items: center; gap: 5px; padding: 4px 0; }
.typing-dots span {
  width: 7px; height: 7px;
  background: var(--green); border-radius: 50%;
  box-shadow: 0 0 6px var(--green);
  animation: blink 1.4s infinite ease-in-out both;
}
.typing-dots span:nth-child(1) { animation-delay: -0.32s; }
.typing-dots span:nth-child(2) { animation-delay: -0.16s; }

/* ══ INPUT AREA ══════════════════════════════════════ */
#input-wrapper {
  flex-shrink: 0;
  padding: 10px 16px 14px;
  background: rgba(6,18,33,0.96);
  border-top: 1px solid var(--border);
  backdrop-filter: blur(16px);
  position: relative;
  z-index: 4999;
}
#input-row {
  display: flex; gap: 10px;
  max-width: 860px; margin: 0 auto;
  align-items: flex-end;
}
#msgBox {
  flex: 1;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 11px 15px;
  color: var(--text-hi);
  font-family: 'Inter', sans-serif;
  font-size: 14.5px; resize: none;
  max-height: 50vh;
  transition: border-color 0.2s, box-shadow 0.2s;
  line-height: 1.5;
}
#msgBox::placeholder { color: var(--text-muted); }
#msgBox:focus {
  outline: none;
  border-color: var(--border-hi);
  box-shadow: 0 0 0 3px rgba(14,165,233,0.07), inset 0 0 14px rgba(14,165,233,0.03);
}
#send-btn {
  background: linear-gradient(135deg, #0ea5e9, #0284c7);
  border: none; color: #fff;
  padding: 0 22px; height: 44px;
  border-radius: var(--radius);
  font-family: 'Rajdhani', sans-serif;
  font-weight: 700; font-size: 13px;
  letter-spacing: 1.5px; text-transform: uppercase;
  cursor: pointer; transition: all 0.2s;
  flex-shrink: 0; display: flex;
  align-items: center; gap: 8px;
  box-shadow: 0 0 0 rgba(14,165,233,0);
}
#send-btn:hover {
  background: linear-gradient(135deg, #38bdf8, #0ea5e9);
  box-shadow: 0 0 22px rgba(14,165,233,0.35);
  transform: translateY(-1px);
}
#send-btn:active { transform: translateY(0); }
#send-btn svg { width: 15px; height: 15px; }

/* BOTAO STOP */
#send-btn.stop-mode {
  background: linear-gradient(135deg, #ef4444, #b91c1c);
  box-shadow: 0 0 15px rgba(239,68,68,0.4);
}
#send-btn.stop-mode:hover {
  background: linear-gradient(135deg, #f87171, #ef4444);
}

/* UPLOAD E DRAG DROP */
#upload-btn {
  background: rgba(14,165,233,0.05); border: 1px solid var(--border);
  color: var(--blue); width: 44px; height: 44px; border-radius: var(--radius);
  cursor: pointer; display: flex; align-items: center; justify-content: center;
  transition: all 0.2s; flex-shrink: 0;
}
#upload-btn:hover { background: rgba(14,165,233,0.18); border-color: var(--border-hi); box-shadow: 0 0 10px rgba(14,165,233,0.2); }
#upload-btn svg { width: 20px; height: 20px; }
body.drag-over::after {
  content: 'SOLTE OS ARQUIVOS AQUI'; position: fixed; inset: 0;
  background: rgba(6,18,33,0.85); backdrop-filter: blur(8px);
  z-index: 9999; display: flex; align-items: center; justify-content: center;
  font-family: 'Rajdhani', sans-serif; font-size: 32px; font-weight: 700;
  color: var(--blue); letter-spacing: 4px; border: 4px dashed var(--blue);
}
.input-hint {
  max-width: 860px; margin: 5px auto 0;
  font-size: 10px; color: var(--text-muted);
  font-family: 'Share Tech Mono', monospace;
  letter-spacing: 0.5px;
}

/* ══ VIDEO STUDIO MODAL ══════════════════════════════ */
#studio-backdrop {
  display: none; position: fixed; inset: 0;
  background: rgba(0,0,0,0.78);
  backdrop-filter: blur(8px); z-index: 400;
  align-items: center; justify-content: center; padding: 20px;
}
#studio-backdrop.open { display: flex; }
#video-studio {
  background: var(--panel);
  border: 1px solid var(--border-hi);
  border-radius: 16px; width: 100%; max-width: 760px;
  max-height: 90vh; overflow-y: auto;
  box-shadow: 0 0 80px rgba(14,165,233,0.1), 0 40px 80px rgba(0,0,0,0.7);
  animation: fadeUp 0.3s ease both;
}
.studio-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 18px 22px 14px; border-bottom: 1px solid var(--border);
}
.studio-title {
  font-family: 'Rajdhani', sans-serif;
  font-size: 17px; font-weight: 700; color: var(--text-hi);
  letter-spacing: 1px; text-transform: uppercase;
  display: flex; align-items: center; gap: 10px;
}
.studio-badge {
  font-size: 10px;
  background: rgba(14,165,233,0.12);
  border: 1px solid var(--border-hi);
  color: var(--blue); padding: 3px 10px;
  border-radius: 20px;
  font-family: 'Share Tech Mono', monospace;
  letter-spacing: 1px; font-weight: normal;
}
.close-studio {
  background: rgba(239,68,68,0.08);
  border: 1px solid rgba(239,68,68,0.25);
  color: var(--red); width: 30px; height: 30px;
  border-radius: 8px; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  font-size: 14px; transition: all 0.2s;
}
.close-studio:hover { background: rgba(239,68,68,0.18); box-shadow: 0 0 10px rgba(239,68,68,0.25); }
.studio-body {
  padding: 18px 22px 22px;
  display: grid; grid-template-columns: auto 1fr; gap: 18px;
  align-items: start;
}
@media (max-width: 580px) { .studio-body { grid-template-columns: 1fr; } }
.preview-box {
  width: 150px; aspect-ratio: 9/16;
  background: #000 url('https://images.unsplash.com/photo-1611162617474-5b21e879e113?q=80&w=300&auto=format&fit=crop') center/cover;
  border-radius: 10px; border: 1px solid var(--border);
  position: relative; overflow: hidden; flex-shrink: 0;
}
.preview-box::before {
  content: ''; position: absolute; inset: 0;
  background: linear-gradient(to top, rgba(0,0,0,0.6) 0%, transparent 50%);
}
#preview-subtitle {
  position: absolute; bottom: 18%; left: 50%;
  transform: translateX(-50%); text-align: center;
  font-family: 'Rajdhani', sans-serif;
  font-size: 12px; font-weight: 700; color: #fff;
  text-transform: uppercase; white-space: nowrap;
  transition: all 0.15s; width: 90%;
}
.controls-panel { display: flex; flex-direction: column; gap: 11px; }
.ctrl-row { display: grid; grid-template-columns: 1fr 1fr; gap: 11px; }
@media (max-width: 460px) { .ctrl-row { grid-template-columns: 1fr; } }
.ctrl-group { display: flex; flex-direction: column; gap: 5px; }
.ctrl-group.full { grid-column: span 2; }
@media (max-width: 460px) { .ctrl-group.full { grid-column: span 1; } }
.ctrl-label {
  font-size: 10px; color: var(--text-muted);
  font-family: 'Share Tech Mono', monospace;
  letter-spacing: 1px; text-transform: uppercase;
}
.ctrl-input {
  background: var(--surface); border: 1px solid var(--border);
  color: var(--text-hi); padding: 8px 11px; border-radius: 8px;
  font-family: 'Inter', sans-serif; font-size: 13px;
  transition: border-color 0.2s; width: 100%;
}
.ctrl-input:focus { outline: none; border-color: var(--border-hi); }
.ctrl-input option { background: var(--panel); }
input[type="range"].ctrl-input { padding: 4px 0; border: none; background: none; accent-color: var(--blue); cursor: pointer; }
input[type="color"].ctrl-input { padding: 3px; height: 36px; cursor: pointer; }
.toggle-row {
  display: flex; align-items: center; gap: 10px;
  padding: 8px 11px;
  background: var(--surface); border: 1px solid var(--border); border-radius: 8px;
}
.toggle-row span { font-size: 13px; color: var(--text); }
input[type="checkbox"] { width: 15px; height: 15px; accent-color: var(--blue); cursor: pointer; }
.action-btn {
  width: 100%; padding: 12px;
  background: linear-gradient(135deg, #0ea5e9, #0284c7);
  border: none; color: #fff;
  border-radius: var(--radius);
  font-family: 'Rajdhani', sans-serif;
  font-weight: 700; font-size: 14px;
  letter-spacing: 1.5px; text-transform: uppercase;
  cursor: pointer; margin-top: 4px; transition: all 0.2s;
}
.action-btn:hover {
  background: linear-gradient(135deg, #38bdf8, #0ea5e9);
  box-shadow: 0 0 24px rgba(14,165,233,0.35);
  transform: translateY(-2px);
}

/* ══ TOAST ══════════════════════════════════════════ */
#toast {
  position: fixed; bottom: 80px; left: 50%;
  transform: translateX(-50%) translateY(16px);
  background: rgba(6,18,33,0.97);
  border: 1px solid var(--border-hi);
  border-radius: 8px; padding: 9px 18px;
  font-family: 'Share Tech Mono', monospace;
  font-size: 11px; color: var(--blue);
  opacity: 0; transition: all 0.28s;
  pointer-events: none; z-index: 500;
  white-space: nowrap;
}
#toast.show { opacity: 1; transform: translateX(-50%) translateY(0); }

/* ══ RESPONSIVE ══════════════════════════════════════ */
@media (max-width: 600px) {
  #header { padding: 0 12px; }
  .logo-sub { display: none; }
  #chat-wrapper { padding: 14px 10px; }
  .boot-grid { grid-template-columns: 1fr 1fr; }
  .code-actions { gap: 4px; }
  .code-btn { padding: 4px 7px; font-size: 9px; }
}
@media (max-width: 400px) {
  .boot-grid { grid-template-columns: 1fr; }
  #send-btn span { display: none; }
}
</style>
</head>

<body>
<div class="scanline"></div>
<div id="toast"></div>
<div id="debug-hud" style="display:none"></div>

<div id="app">

  <!-- HEADER -->
  <header id="header">
    <div class="header-left">
      <button type="button" id="menu-btn" aria-label="Menu">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
          <line x1="3" y1="6"  x2="21" y2="6"/>
          <line x1="3" y1="12" x2="21" y2="12"/>
          <line x1="3" y1="18" x2="21" y2="18"/>
        </svg>
      </button>
      <div class="logo">
        <div class="logo-icon">R2</div>
        <div class="logo-text">
          <span class="logo-title">Ghost Protocol</span>
          <span class="logo-sub">Tactical OS · v5.0</span>
        </div>
      </div>
    </div>
    <div class="header-right">
      <button type="button" id="clear-btn" title="Limpar chat">🗑</button>
      <div class="status-pill" id="status-pill">
        <div class="status-dot" id="status-dot"></div>
        <span id="status-text">ONLINE</span>
      </div>
    </div>
  </header>

  <!-- OVERLAY -->
  <div id="overlay" role="presentation"></div>

  <!-- SIDEBAR -->
  <nav id="sidebar">
    <div class="sidebar-header">
      <span class="sidebar-brand">R2 · Menu</span>
      <button type="button" class="sidebar-close">✕</button>
    </div>

    <div class="sidebar-label">Documentos</div>
    <button class="mod-btn" onclick="execCmd('/doc sync','📚 Sincronizando matriz de conhecimento...')">
      <div class="icon">📚</div><span>Sincronizar PDFs</span>
    </button>
    <button class="mod-btn" onclick="execCmd('/doc list','📋 Verificando inventário...')">
      <div class="icon">📋</div><span>Listar Arquivos</span>
    </button>

    <div class="sidebar-divider"></div>
    <div class="sidebar-label">Inteligência Tática</div>
    <button class="mod-btn" onclick="execCmd('/cmd radar','📡 Ativando radar de voos...')">
      <div class="icon">📡</div><span>Radar de Voos</span>
    </button>
    <button class="mod-btn" onclick="execCmd('/cmd astro','☄️ Consultando banco da NASA...')">
      <div class="icon">☄️</div><span>Defesa Planetária</span>
    </button>
    <button class="mod-btn" onclick="execCmd('/cmd pizza','🍕 Checando monitor PizzINT...')">
      <div class="icon">🍕</div><span>Monitor PizzINT</span>
    </button>
    <button class="mod-btn" onclick="execCmd('/cmd solar','☀️ Consultando dados solares...')">
      <div class="icon">☀️</div><span>Clima Espacial</span>
    </button>

    <div class="sidebar-divider"></div>
    <div class="sidebar-label">Produção</div>
    <button class="mod-btn" onclick="openStudio()">
      <div class="icon">🎬</div><span>Estúdio de Cortes</span>
    </button>
  </nav>

  <!-- CHAT -->
  <main id="chat-wrapper">
    <div id="chat">
      <div class="boot-msg" id="boot-screen">
        <div class="boot-logo">R2</div>
        <div class="boot-tagline">Ghost Protocol · Sistema Tático Online</div>
        <div class="boot-grid">
          <div class="boot-card" onclick="quickPrompt('Qual é seu status de operação atual?')">Status do sistema</div>
          <div class="boot-card" onclick="quickPrompt('Liste os módulos táticos disponíveis.')">Módulos ativos</div>
          <div class="boot-card" onclick="quickPrompt('O que você pode fazer por mim?')">Capacidades</div>
          <div class="boot-card" onclick="execCmd('/cmd radar','📡 Ativando radar...')">Escanear radar</div>
          <div class="boot-card" onclick="execCmd('/cmd astro','☄️ Consultando NASA...')">Asteroides</div>
          <div class="boot-card" onclick="openStudio()">Estúdio de vídeo</div>
        </div>
      </div>
    </div>
  </main>

  <!-- INPUT -->
  <footer id="input-wrapper">
    <div id="input-row">
      <button type="button" id="upload-btn" title="Anexar arquivo (ou Arraste para a tela)">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
          <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"></path>
        </svg>
      </button>
      <input type="file" id="file-input" style="display:none" multiple>
      <textarea
        id="msgBox"
        rows="1"
        placeholder="Digite sua ordem, Comandante..."
        oninput="autoResize(this)"
        onkeydown="handleKey(event)"
      ></textarea>
      <button type="button" id="send-btn">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <line x1="22" y1="2" x2="11" y2="13"/>
          <polygon points="22 2 15 22 11 13 2 9 22 2"/>
        </svg>
        <span>Enviar</span>
      </button>
    </div>
    <div class="input-hint">Enter · enviar &nbsp;|&nbsp; Shift+Enter · nova linha</div>
  </footer>
</div>

<!-- VIDEO STUDIO MODAL -->
<div id="studio-backdrop" onclick="closeStudioOnBack(event)">
  <div id="video-studio">
    <div class="studio-header">
      <div class="studio-title">
        Estúdio de Cortes
        <span class="studio-badge">TESOURA NEURAL</span>
      </div>
      <button class="close-studio" onclick="closeStudio()">✕</button>
    </div>
    <div class="studio-body">
      <div class="preview-box">
        <div id="preview-subtitle">JORNADA<br>DO HERÓI!</div>
      </div>
      <div class="controls-panel">
        <div class="ctrl-group full">
          <label class="ctrl-label">URL do YouTube</label>
          <input type="text" id="vid-url" class="ctrl-input" placeholder="https://youtube.com/watch?v=...">
        </div>
        <div class="ctrl-row">
          <div class="ctrl-group">
            <label class="ctrl-label">Legendas</label>
            <div class="toggle-row">
              <input type="checkbox" id="sub-active" checked>
              <span>Ativar Legendas</span>
            </div>
          </div>
          <div class="ctrl-group">
            <label class="ctrl-label">Posição Automática</label>
            <div class="toggle-row">
              <input type="checkbox" id="sub-pos-auto" checked
                onchange="document.getElementById('sub-pos').disabled=this.checked">
              <span>IA decide posição</span>
            </div>
          </div>
        </div>
        <div class="ctrl-row">
          <div class="ctrl-group">
            <label class="ctrl-label">Cor da Legenda</label>
            <input type="color" id="sub-color" class="ctrl-input" value="#ffffff" oninput="updatePreview()">
          </div>
          <div class="ctrl-group">
            <label class="ctrl-label">Tamanho: <span id="size-val">13px</span></label>
            <input type="range" id="sub-size" class="ctrl-input" min="10" max="22" value="13"
              oninput="updatePreview(); document.getElementById('size-val').textContent=this.value+'px'">
          </div>
        </div>
        <div class="ctrl-row">
          <div class="ctrl-group">
            <label class="ctrl-label">Posição Y: <span id="pos-val">18%</span></label>
            <input type="range" id="sub-pos" class="ctrl-input" min="5" max="95" value="18" disabled
              oninput="updatePreview(); document.getElementById('pos-val').textContent=this.value+'%'">
          </div>
          <div class="ctrl-group">
            <label class="ctrl-label">Estilo Visual</label>
            <select id="sub-style" class="ctrl-input" onchange="updatePreview()">
              <option value="outline">Borda Preta Grossa</option>
              <option value="shadow">Sombra Suave</option>
              <option value="box">Fundo Transparente</option>
              <option value="yellow">Destaque Amarelo</option>
            </select>
          </div>
        </div>
        <button class="action-btn" onclick="startVideoExtraction()">🚀 Iniciar Extração Tática</button>
      </div>
    </div>
  </div>
</div>

<script>
/* ================================================================
   R2 Tactical OS - Ghost Protocol v5.0
   JS Engine - ES5 puro (compativel com lockdown-install.js)
   SEM: let, const, arrow functions (=>), fetch, classList.toggle
   ================================================================ */

var ws          = null;
var isConnected = false;
var toastTimer  = null;
var isGenerating = false;

function stopGeneration() {
  var xhr = new XMLHttpRequest();
  xhr.open('POST', '/api/stop', true);
  xhr.send();
  var sb = document.getElementById('send-btn');
  if(sb) { sb.disabled = true; sb.querySelector('span').textContent = 'Parando...'; }
}

function toggleSendButton(generating) {
  isGenerating = generating;
  var btn = document.getElementById('send-btn');
  if (!btn) return;
  var span = btn.querySelector('span');
  var svg = btn.querySelector('svg');
  
  if (generating) {
    btn.className = 'stop-mode';
    span.textContent = 'Parar';
    svg.innerHTML = '<rect x="6" y="6" width="12" height="12" rx="2" ry="2"></rect>';
    btn.onclick = function(e) { e.preventDefault(); stopGeneration(); };
  } else {
    btn.className = '';
    btn.disabled = false;
    span.textContent = 'Enviar';
    svg.innerHTML = '<line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>';
    btn.onclick = function(e) { e.preventDefault(); sendMsg(); };
  }
}

/* WEBSOCKET */
function wsEndpoint() {
  if (location.protocol === 'file:') return 'ws://127.0.0.1:8000/ws';
  var p = location.protocol === 'https:' ? 'wss:' : 'ws:';
  return p + '//' + location.host + '/ws';
}

function conectarMatriz() {
  try { ws = new WebSocket(wsEndpoint()); }
  catch(e) { setTimeout(conectarMatriz, 3000); return; }

  ws.onopen = function() {
    isConnected = true;
    setStatus(true);
    showToast('Conexao estabelecida com o servidor');
  };

  ws.onmessage = function(event) {
    var data;
    try { data = JSON.parse(event.data); } catch(e) { return; }
    if (data.type === 'system') {
      hideTyping();
      appendMsg('sys', 'SYS', data.text);
    } else if (data.type === 'stream') {
      hideTyping();
      var chatEl = document.getElementById('chat');
      if (!chatEl) return;
      var last = chatEl.lastElementChild;
      if (last && last.getAttribute('data-role') === 'bot') {
        var raw = last.querySelector('.bot-raw');
        if (raw) raw.textContent += data.text;
      } else {
        appendMsg('bot', 'R2', data.text);
      }
      chatEl.parentElement.scrollTop = chatEl.parentElement.scrollHeight;
    } else if (data.type === 'done') {
      hideTyping();
      renderLastBot();
      toggleSendButton(false);
    } else if (data.type === 'image') {
      hideTyping();
      appendMsg('sys', 'SYS', '<b>' + escHtml(data.text) + '</b><br><img src="' + escHtml(data.url) + '" alt="img">');
    }
  };

  ws.onclose = function() {
    isConnected = false;
    setStatus(false);
    toggleSendButton(false);
    showToast('Reconectando em 3s...');
    setTimeout(conectarMatriz, 3000);
  };

  ws.onerror = function() { console.error('R2: WS error'); };
}

/* STATUS */
function setStatus(online) {
  var dot  = document.getElementById('status-dot');
  var text = document.getElementById('status-text');
  var pill = document.getElementById('status-pill');
  if (!dot || !text || !pill) return;
  if (online) {
    dot.className    = 'status-dot';
    text.textContent = 'ONLINE';
    pill.className   = 'status-pill';
  } else {
    dot.className    = 'status-dot offline';
    text.textContent = 'OFFLINE';
    pill.className   = 'status-pill offline';
  }
}

/* TOAST */
function showToast(msg) {
  var t = document.getElementById('toast');
  if (!t) return;
  t.textContent = msg;
  t.className   = 'show';
  clearTimeout(toastTimer);
  toastTimer = setTimeout(function() { t.className = ''; }, 2800);
}

/* HELPERS */
function escHtml(s) {
  return String(s || '')
    .replace(/&/g,  '&amp;')
    .replace(/</g,  '&lt;')
    .replace(/>/g,  '&gt;')
    .replace(/"/g,  '&quot;');
}

function removeBootScreen() {
  var boot = document.getElementById('boot-screen');
  if (boot && boot.parentNode) boot.parentNode.removeChild(boot);
}

/* APPEND MESSAGE */
function appendMsg(role, sender, text) {
  removeBootScreen();
  var chat = document.getElementById('chat');
  if (!chat) return;
  var wrapper = document.createElement('div');
  wrapper.className = 'msg ' + role;
  if (role === 'bot') {
    wrapper.setAttribute('data-role', 'bot');
    var avB = document.createElement('div'); avB.className = 'msg-avatar'; avB.textContent = 'R2';
    var bdB = document.createElement('div'); bdB.className = 'msg-body';
    var snB = document.createElement('div'); snB.className = 'msg-sender'; snB.textContent = 'R2';
    var buB = document.createElement('div'); buB.className = 'msg-bubble';
    var rw  = document.createElement('span'); rw.className = 'bot-raw'; rw.style.display = 'none'; rw.textContent = text || '';
    var ct  = document.createElement('div');  ct.className = 'bot-content';
    buB.appendChild(rw); buB.appendChild(ct);
    bdB.appendChild(snB); bdB.appendChild(buB);
    wrapper.appendChild(avB); wrapper.appendChild(bdB);
  } else {
    var avO = document.createElement('div'); avO.className = 'msg-avatar'; avO.textContent = (role === 'user') ? 'TED' : 'SYS';
    var bdO = document.createElement('div'); bdO.className = 'msg-body';
    var snO = document.createElement('div'); snO.className = 'msg-sender'; snO.textContent = sender;
    var buO = document.createElement('div'); buO.className = 'msg-bubble'; buO.innerHTML = text;
    bdO.appendChild(snO); bdO.appendChild(buO);
    wrapper.appendChild(avO); wrapper.appendChild(bdO);
  }
  chat.appendChild(wrapper);
  if (chat.parentElement) chat.parentElement.scrollTop = chat.parentElement.scrollHeight;
}

/* RENDER MARKDOWN + CODE CARDS */
function renderLastBot() {
  var chat = document.getElementById('chat');
  if (!chat) return;
  var bots = [], kids = chat.children;
  for (var i = 0; i < kids.length; i++) {
    if (kids[i].getAttribute('data-role') === 'bot') bots.push(kids[i]);
  }
  var lastBot = bots[bots.length - 1];
  if (!lastBot) return;
  var rawEl = lastBot.querySelector('.bot-raw');
  var ctEl  = lastBot.querySelector('.bot-content');
  if (!rawEl || !ctEl) return;
  var rawText = rawEl.textContent;
  rawEl.style.display = 'none';
  try { ctEl.innerHTML = marked.parse(rawText); } catch(e) { ctEl.textContent = rawText; }
  var blocks = ctEl.querySelectorAll('pre code');
  for (var b = 0; b < blocks.length; b++) { injectCodeCard(blocks[b]); }
  if (chat.parentElement) chat.parentElement.scrollTop = chat.parentElement.scrollHeight;
}

function injectCodeCard(block) {
  var codeText  = block.textContent || '';
  try { hljs.highlightElement(block); } catch(e) {}
  var lines     = codeText.split(String.fromCharCode(10));
  var firstLine = (lines[0] || '').replace(/^\s+|\s+$/g, '');
  var m         = firstLine.match(/(?:#|\/\/|<!--)\s*filename:\s*(\S+)/i);
  var filename  = m ? m[1].replace(/-->$/, '').replace(/^\s+|\s+$/g, '') : null;
  var pre = block.parentNode;
  while (pre && pre.tagName !== 'PRE') pre = pre.parentNode;
  if (!pre || !pre.parentNode) return;
  var nxt = pre.nextSibling;
  while (nxt && nxt.nodeType === 3) nxt = nxt.nextSibling;
  if (nxt && nxt.className === 'code-action-bar') return;
  pre.style.borderRadius = '10px 10px 0 0';
  pre.style.marginBottom = '0';

  var fnSpan = document.createElement('span');
  fnSpan.className = 'code-filename';
  if (filename) {
    fnSpan.innerHTML = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>' + escHtml(filename);
  } else {
    fnSpan.textContent = 'codigo gerado';
  }

  var actDiv = document.createElement('div');
  actDiv.className = 'code-actions';

  if (filename) {
    var execBtn = document.createElement('button');
    execBtn.type = 'button'; execBtn.className = 'code-btn exec'; execBtn.innerHTML = '&#9654; Executar';
    (function(fn, code, btn) { btn.onclick = function() { executeCode(btn, fn, code); }; }(filename, codeText, execBtn));
    actDiv.appendChild(execBtn);
  }

  var vsBtn = document.createElement('button');
  vsBtn.type = 'button'; vsBtn.className = 'code-btn vscode'; vsBtn.innerHTML = '&#60;/&#62; VS Code';
  var vsName = filename || 'r2_snippet.txt';
  (function(fn, code, btn) { btn.onclick = function() { openVSCode(btn, fn, code); }; }(vsName, codeText, vsBtn));
  actDiv.appendChild(vsBtn);

  var bar = document.createElement('div');
  bar.className = 'code-action-bar';
  bar.appendChild(fnSpan); bar.appendChild(actDiv);

  var term = document.createElement('div');
  term.className = 'exec-terminal';

  pre.parentNode.insertBefore(bar,  pre.nextSibling);
  bar.parentNode.insertBefore(term, bar.nextSibling);
}

/* VS CODE */
function openVSCode(btn, filename, content) {
  btn.disabled = true; btn.textContent = '...';
  var xhr = new XMLHttpRequest();
  xhr.open('POST', '/api/open_vscode', true);
  xhr.setRequestHeader('Content-Type', 'application/json');
  xhr.onload = function() {
    var data; try { data = JSON.parse(xhr.responseText); } catch(e) { data = {}; }
    if (data.ok) {
      btn.textContent = 'Aberto!';
      setTimeout(function() { btn.innerHTML = '&#60;/&#62; VS Code'; btn.disabled = false; }, 2500);
    } else {
      btn.textContent = 'Erro';
      setTimeout(function() { btn.innerHTML = '&#60;/&#62; VS Code'; btn.disabled = false; }, 2500);
    }
  };
  xhr.onerror = function() { btn.textContent = 'Falha'; btn.disabled = false; };
  xhr.send(JSON.stringify({ filename: filename, content: content || '' }));
}

/* EXECUTE CODE */
function executeCode(btn, filename, content) {
  btn.disabled = true; btn.textContent = 'Executando...';
  var bar = btn.parentNode ? btn.parentNode.parentNode : null;
  var term = bar ? bar.nextSibling : null;
  while (term && term.nodeType === 3) term = term.nextSibling;
  if (term && term.className.indexOf('exec-terminal') > -1) {
    term.className = 'exec-terminal visible'; term.textContent = 'Aguarde...';
  }
  var xhr = new XMLHttpRequest();
  xhr.open('POST', '/api/execute_code', true);
  xhr.setRequestHeader('Content-Type', 'application/json');
  xhr.onload = function() {
    var data; try { data = JSON.parse(xhr.responseText); } catch(e) { data = { ok: false, error: 'parse error' }; }
    if (term && term.className.indexOf('exec-terminal') > -1) {
      if (data.ok) { term.textContent = data.output || 'Executado sem saida.'; }
      else { term.innerHTML = '<span class="err">ERRO: ' + escHtml(data.error || 'desconhecido') + '</span>'; }
    }
    btn.textContent = 'Executar'; btn.disabled = false;
  };
  xhr.onerror = function() { if (term) term.textContent = 'Falha.'; btn.textContent = 'Executar'; btn.disabled = false; };
  xhr.send(JSON.stringify({ filename: filename, content: content || '' }));
}

/* TYPING */
function showTyping() {
  removeBootScreen();
  if (document.getElementById('typing-row')) return;
  var chat = document.getElementById('chat'); if (!chat) return;
  var row = document.createElement('div'); row.id = 'typing-row'; row.className = 'msg bot';
  var av = document.createElement('div'); av.className = 'msg-avatar'; av.textContent = 'R2';
  var bd = document.createElement('div'); bd.className = 'msg-body';
  var sn = document.createElement('div'); sn.className = 'msg-sender'; sn.textContent = 'R2';
  var bu = document.createElement('div'); bu.className = 'msg-bubble';
  var dt = document.createElement('div'); dt.className = 'typing-dots'; dt.innerHTML = '<span></span><span></span><span></span>';
  bu.appendChild(dt); bd.appendChild(sn); bd.appendChild(bu); row.appendChild(av); row.appendChild(bd);
  chat.appendChild(row);
  if (chat.parentElement) chat.parentElement.scrollTop = chat.parentElement.scrollHeight;
  toggleSendButton(true);
}
function hideTyping() {
  var t = document.getElementById('typing-row');
  if (t && t.parentNode) t.parentNode.removeChild(t);
}

/* SEND */
function sendMsg() {
  var box = document.getElementById('msgBox'); if (!box) return;
  var msg = box.value.replace(/^\s+|\s+$/g, '');
  if (!msg) return;
  if (!ws || ws.readyState !== 1) { showToast('Servidor offline. Aguarde reconexao...'); return; }
  appendMsg('user', 'TEDDY', escHtml(msg));
  ws.send(msg);
  box.value = ''; box.style.height = '';
  showTyping();
}
function execCmd(cmd, label) {
  if (!ws || ws.readyState !== 1) { showToast('Servidor offline.'); return; }
  closeSidebar();
  appendMsg('user', 'TEDDY', escHtml(label));
  ws.send(cmd);
  showTyping();
}
function quickPrompt(text) {
  var box = document.getElementById('msgBox'); if (box) box.value = text; sendMsg();
}
function clearChat() {
  var chat = document.getElementById('chat'); if (chat) chat.innerHTML = '';
  showToast('Chat limpo.');
}

/* SIDEBAR */
function toggleSidebar() {
  var sb = document.getElementById('sidebar');
  var ov = document.getElementById('overlay');
  if (!sb) return;
  
  if (sb.className.indexOf('open') > -1 || sb.getAttribute('class') === 'open') {
    closeSidebar();
  } else {
    sb.className = 'open';
    if (ov) ov.className = 'active';
  }
}

function closeSidebar() {
  var sb = document.getElementById('sidebar');
  var ov = document.getElementById('overlay');
  
  if (sb) {
    sb.className = '';
    sb.removeAttribute('class'); 
  }
  if (ov) {
    ov.className = '';
    ov.removeAttribute('class');
  }
}

/* INPUT */
function autoResize(el) { if (!el) return; el.style.height = ''; el.style.height = Math.min(el.scrollHeight, 130) + 'px'; }
function handleKey(e) { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); if(!isGenerating) sendMsg(); } }

/* VIDEO STUDIO */
function openStudio() {
  var el = document.getElementById('studio-backdrop');
  if (el) el.className = 'open';
  closeSidebar();
}
function closeStudio() {
  var el = document.getElementById('studio-backdrop');
  if (el) {
    el.className = '';
    el.removeAttribute('class');
  }
}
function closeStudioOnBack(e) {
  if (e.target === document.getElementById('studio-backdrop')) closeStudio();
}
function updatePreview() {
  var sub = document.getElementById('preview-subtitle');
  var color = document.getElementById('sub-color');
  var size  = document.getElementById('sub-size');
  var pos   = document.getElementById('sub-pos');
  var style = document.getElementById('sub-style');
  if (!sub || !color || !size || !pos || !style) return;
  sub.style.color = color.value; sub.style.fontSize = size.value + 'px'; sub.style.bottom = pos.value + '%';
  var sm = {
    outline: { textShadow:'1px 1px 0 #000,-1px -1px 0 #000,1px -1px 0 #000,-1px 1px 0 #000', background:'transparent', padding:'0' },
    shadow:  { textShadow:'3px 3px 6px rgba(0,0,0,0.9)', background:'transparent', padding:'0' },
    box:     { textShadow:'none', background:'rgba(0,0,0,0.65)', padding:'3px 10px', borderRadius:'5px' },
    yellow:  { textShadow:'2px 2px 0 #000', background:'transparent', padding:'0', color:'#ffff00' }
  };
  var s = sm[style.value] || sm['outline'];
  for (var k in s) { if (Object.prototype.hasOwnProperty.call(s,k)) sub.style[k] = s[k]; }
  sub.style.color = (style.value === 'yellow') ? '#ffff00' : color.value;
}
function startVideoExtraction() {
  var urlEl = document.getElementById('vid-url'); if (!urlEl) return;
  var url = urlEl.value.replace(/^\s+|\s+$/g,'');
  if (!url) { showToast('Insira o link do video alvo!'); return; }
  var config = {
    url: url,
    active:  document.getElementById('sub-active')   ? document.getElementById('sub-active').checked   : false,
    autoPos: document.getElementById('sub-pos-auto') ? document.getElementById('sub-pos-auto').checked : false,
    color:   document.getElementById('sub-color')    ? document.getElementById('sub-color').value      : '#ffffff',
    size:    document.getElementById('sub-size')     ? document.getElementById('sub-size').value       : '13',
    style:   document.getElementById('sub-style')    ? document.getElementById('sub-style').value      : 'outline',
    pos:     document.getElementById('sub-pos')      ? document.getElementById('sub-pos').value        : '18'
  };
  closeStudio();
  execCmd('/vid extract ' + JSON.stringify(config), 'Operacao iniciada...');
}

/* DRAG AND DROP & UPLOAD */
function handleFiles(files) {
  if (!files || !files.length) return;
  showToast('Transmitindo ' + files.length + ' arquivo(s)...');
  var formData = new FormData();
  for (var i = 0; i < files.length; i++) { formData.append('arquivos', files[i]); }
  
  var xhr = new XMLHttpRequest();
  xhr.open('POST', '/api/upload_arquivos', true);
  xhr.onload = function() {
    if (xhr.status === 200) {
      var res = JSON.parse(xhr.responseText);
      if (res.ok) {
        var box = document.getElementById('msgBox');
        var cmds = res.arquivos.map(function(a) { return '/ler ' + a; }).join(' ');
        box.value = (box.value ? box.value + ' ' : '') + cmds + ' ';
        autoResize(box);
        box.focus();
        showToast('✅ Arquivos na base! Digite sua ordem.');
      } else { showToast('❌ Erro tático: ' + res.error); }
    }
  };
  xhr.onerror = function() { showToast('❌ Falha na conexão de rede.'); };
  xhr.send(formData);
}

function setupDragAndDrop() {
  var ub = document.getElementById('upload-btn');
  var fi = document.getElementById('file-input');
  if (ub && fi) {
    ub.onclick = function() { fi.click(); };
    fi.onchange = function(e) { handleFiles(e.target.files); fi.value = ''; };
  }
  
  window.addEventListener('dragover', function(e) { 
      e.preventDefault(); 
      document.body.className = 'drag-over'; 
  });
  window.addEventListener('dragleave', function(e) {
    if (e.clientX === 0 || e.clientY === 0) document.body.className = document.body.className.replace('drag-over', '').trim();
  });
  window.addEventListener('drop', function(e) {
    e.preventDefault();
    document.body.className = document.body.className.replace('drag-over', '').trim();
    handleFiles(e.dataTransfer.files);
  });
}

/* INIT */
(function init() {
  setupDragAndDrop();
  var mb = document.getElementById('menu-btn');  if (mb) mb.onclick = function(e) { e.preventDefault(); toggleSidebar(); };
  var sb = document.getElementById('send-btn');  if (sb) sb.onclick = function(e) { e.preventDefault(); sendMsg(); };
  var cb = document.getElementById('clear-btn'); if (cb) cb.onclick = function(e) { e.preventDefault(); clearChat(); };
  var ov = document.getElementById('overlay');   if (ov) ov.onclick = closeSidebar;
  var sc = document.querySelector('.sidebar-close'); if (sc) sc.onclick = function(e) { e.preventDefault(); closeSidebar(); };
  var box = document.getElementById('msgBox');
  if (box) { box.oninput = function() { autoResize(this); }; box.onkeydown = function(e) { handleKey(e); }; }
  conectarMatriz();
}());
</script>
</body>
</html>"""

# ══════════════════════════════════════════
# ROTAS FASTAPI
# ══════════════════════════════════════════

@app.get("/", response_class=HTMLResponse)
async def serve_gui():
    return HTML_TEMPLATE


@app.post("/api/open_vscode")
async def api_open_vscode(payload: CodePayload):
    """Grava no workspace tático e abre o mesmo arquivo no VS Code (alinha com /api/execute_code)."""
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    safe_name = re.sub(r"[^\w.\-]", "_", os.path.basename(payload.filename)) or "r2_snippet.txt"
    filepath  = WORKSPACE / safe_name
    try:
        filepath.write_text(payload.content or "", encoding="utf-8")
        opened = False
        for cmd in (
            ["code", str(filepath)],
            [r"C:\Program Files\Microsoft VS Code\Code.exe", str(filepath)],
            [r"C:\Program Files (x86)\Microsoft VS Code\Code.exe", str(filepath)],
        ):
            try:
                subprocess.Popen(cmd)
                opened = True
                break
            except FileNotFoundError:
                continue
        if opened:
            return {"ok": True, "path": str(filepath)}
        return {"ok": False, "error": "VS Code não encontrado no PATH"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


from fastapi import UploadFile, File
from typing import List

@app.post("/api/stop")
async def api_stop():
    global STOP_GEN
    STOP_GEN = True
    return {"ok": True}

@app.post("/api/upload_arquivos")
async def api_upload_arquivos(arquivos: List[UploadFile] = File(...)):
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    salvos = []
    try:
        for arq in arquivos:
            safe_name = re.sub(r"[^\w.\-]", "_", os.path.basename(arq.filename))
            caminho = WORKSPACE / safe_name
            with open(caminho, "wb") as f:
                f.write(await arq.read())
            salvos.append(safe_name)
        return {"ok": True, "arquivos": salvos}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# CORREÇÃO: rota /api/execute_code com quebra de linha correta (Bug 10)
@app.post("/api/execute_code")
async def api_execute_code(payload: CodePayload):
    """Executa um script do workspace no ambiente Conda r2."""
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    safe_name = re.sub(r"[^\w.\-]", "_", os.path.basename(payload.filename)) or "script.py"
    filepath  = WORKSPACE / safe_name

    if payload.content:
        filepath.write_text(payload.content, encoding="utf-8")

    if not filepath.exists():
        return {"ok": False, "error": f"Arquivo {safe_name} não encontrado no workspace."}

    try:
        cmd = (
            fr'cmd.exe /c "call C:\Users\Teddy\miniconda3\Scripts\activate.bat '
            fr'C:\Users\Teddy\miniconda3 && conda activate r2 && python "{filepath}""'
        )
        proc = subprocess.Popen(
            cmd, shell=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding="utf-8", errors="replace"
        )
        stdout, stderr = proc.communicate()
        output = stdout
        if stderr:
            output += f"\n--- STDERR ---\n{stderr}" if output else stderr
        return {"ok": True, "output": output or "✅ Executado sem saída de texto."}

    except Exception as e:
        return {"ok": False, "error": str(e)}


# ══════════════════════════════════════════
# 🧠 WEBSOCKET — ROTEADOR LÓGICO
# ══════════════════════════════════════════
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    sessao_memoria_ram = carregar_historico_na_ram() # <--- ADICIONE ESTA LINHA AQUI
    sys_prompt = "Você é o R2, IA tática e Mestre Programador. REGRA: A primeira linha do código DEVE ser: # filename: nome.py"

    async def processar_midia(caminho):
        if caminho and os.path.exists(caminho):
            n = f"scan_{int(time.time())}_{os.path.basename(caminho)}"
            shutil.copy(caminho, os.path.join("static/media", n))
            return f"/static/media/{n}"
        return None

    try:
        while True:
            comando = await websocket.receive_text()
            cmd_l   = comando.lower().strip()

            # ── Comandos /cmd ──────────────────────────────
            if cmd_l.startswith("/cmd "):
                sub = cmd_l.replace("/cmd ", "").strip()

                if sub == "pizza" and pizza_ops:
                    st = await asyncio.to_thread(pizza_ops.get_status)
                    if st.get('level', -1) == -1:
                        msg = "❌ Falha ao interceptar a rede PizzINT."
                    else:
                        nivel  = st['level']
                        defcon = 5 if nivel < 20 else (4 if nivel < 40 else (3 if nivel < 60 else (2 if nivel < 80 else 1)))
                        msg = f"🍕 <b>Monitor PizzINT</b><br>Pedidos: <b>{nivel:.0f}/h</b><br>🚨 <b>DEFCON: {defcon}</b><br><br><b>Últimas:</b><br>"
                        for n in (st.get('news') or []):
                            msg += f"• <a href='{n['url']}' target='_blank' style='color:#0ea5e9'>{n['titulo']}</a><br>"
                    await websocket.send_json({"type": "system", "text": msg})
                    continue

                elif sub == "solar" and noaa_ops:
                    await websocket.send_json({"type": "system", "text": "🛰️ Varrendo clima espacial — aguarde telemetria..."})
                    intel      = await asyncio.to_thread(noaa_ops.get_full_intel)
                    painel_html = noaa_ops.gerar_html_painel(intel)
                    await websocket.send_json({"type": "system", "text": painel_html})
                    drap_path, _ = intel.get("media", {}).get("drap", (None, None))
                    if drap_path:
                        u = await processar_midia(drap_path)
                        if u:
                            await websocket.send_json({"type": "image", "url": u, "text": "🗺️ Mapa D-RAP"})
                    continue

                elif sub == "radar" and radar_ops:
                    await websocket.send_json({"type": "system", "text": "📡 Escaneando espaço aéreo tático da base..."})
                    try:
                        filename, qtd, msg_status = await asyncio.to_thread(radar_ops.radar_scan) 
                        await websocket.send_json({"type": "system", "text": f"<b>{msg_status}</b>"})
                        if filename and os.path.exists(filename):
                            img_url = await processar_midia(filename)
                            if img_url:
                                await websocket.send_json({"type": "image", "url": img_url, "text": "🗺️ Gráfico de Telemetria"})
                    except Exception as e:
                        await websocket.send_json({"type": "system", "text": f"❌ Erro no Radar: {str(e)}"})
                    continue

                elif sub == "astro" and astro_ops:
                    await websocket.send_json({"type": "system", "text": "☄️ Acessando matriz de defesa planetária da NASA..."})
                    try:
                        texto, p_id, p_nome = await asyncio.to_thread(astro_ops.get_asteroid_report)
                        if texto:
                            html_texto = texto.replace('\n', '<br>')
                            await websocket.send_json({"type": "system", "text": html_texto})
                    except Exception as e:
                        await websocket.send_json({"type": "system", "text": f"❌ Erro na telemetria Astro: {str(e)}"})
                    continue

                else:
                    status = "offline" if (sub in ["radar", "astro"] and not (radar_ops or astro_ops)) else "desconhecido"
                    await websocket.send_json({"type": "system", "text": f"⚠️ Módulo '{sub}' {status} ou não implementado."})
                    continue

            # ── NOVA ROTA: /vid viral (Bugs 5 e 8) ───────────────────────────
            if cmd_l.startswith("/vid viral "):
                video_alvo = comando.replace("/vid viral ", "").strip()
                await websocket.send_json({"type": "system", "text": f"⏳ Tesoura Neural V4: Transcrevendo e analisando {video_alvo}..."})
                
                if video_ops and ai_brain:
                    res = await asyncio.to_thread(video_ops.processar_video_viral, video_alvo, ai_brain)
                    
                    if isinstance(res, list):
                        msg = "✅ **Cortes Virais Extraídos com Sucesso:**\n"
                        for r in res:
                            msg += f"- `{r}`\n"
                        await websocket.send_json({"type": "system", "text": msg})
                    else:
                        await websocket.send_json({"type": "system", "text": str(res)})
                else:
                    await websocket.send_json({"type": "system", "text": "❌ Tesoura Neural ou Cérebro LLaMA offline."})
                continue

            # ── Comandos /doc ──────────────────────────────
            if cmd_l == "/doc sync":
                res = await asyncio.to_thread(rag_ops.sync)
                await websocket.send_json({"type": "system", "text": res})
                continue
            if cmd_l == "/doc list":
                res = f"📋 <b>Arquivos:</b> {', '.join(rag_ops.arquivos_indexados)}" if rag_ops.arquivos_indexados else "⚠️ Nenhum arquivo indexado."
                await websocket.send_json({"type": "system", "text": res})
                continue

            # ── IA (LLM) ───────────────────────────────────
            if ai_brain:
                arquivos_injetados = ""
                matches = re.findall(r'/ler\s+([\w.\-]+)', comando, re.IGNORECASE)
                cmd_limpo = comando
                for arq in matches:
                    caminho_arq = WORKSPACE / arq
                    if caminho_arq.exists():
                        conteudo = caminho_arq.read_text(encoding="utf-8", errors="replace")
                        arquivos_injetados += f"\n\n[CONTEÚDO DO ARQUIVO: {arq}]\n```python\n{conteudo}\n```\n"
                    else:
                        arquivos_injetados += f"\n\n[AVISO: Arquivo '{arq}' não encontrado no workspace.]\n"
                    cmd_limpo = re.sub(fr'/ler\s+{re.escape(arq)}', '', cmd_limpo, flags=re.IGNORECASE).strip()

                if not cmd_limpo and arquivos_injetados:
                    cmd_limpo = "Analise o(s) arquivo(s) acima e aguarde instruções."

                comando_final = f"{cmd_limpo}{arquivos_injetados}"

                sessao_memoria_ram.append(f"Teddy: {comando}")
                ctx = await asyncio.to_thread(rag_ops.search, cmd_limpo)

                sys_prompt = (
                    "Você é o R2 Tactical OS, IA tática de elite e Mestre Programador.\n"
                    "REGRA ABSOLUTA DE CÓDIGO: Sempre que gerar qualquer bloco de código, "
                    "a PRIMEIRA linha DEVE ser um comentário com o nome do arquivo:\n"
                    "  Python/Shell: # filename: nome.py\n"
                    "  JavaScript/CSS: // filename: nome.js\n"
                    "  HTML: \n"
                    "Sem exceções. Explique o código antes de exibi-lo."
                )

                prompt = f"<|im_start|>system\n{sys_prompt}\n"
                if ctx:
                    prompt += f"\n[RAG PDFs]:\n{ctx}\n"
                if eu_ops:
                    prompt += f"\n{eu_ops.injetar_consciencia()}\n"
                prompt += "<|im_end|>\n"
                for m in sessao_memoria_ram[-40:-1]:
                    if m.startswith("Teddy: "):
                        prompt += f"<|im_start|>user\n{m[7:]}<|im_end|>\n"
                    else:
                        prompt += f"<|im_start|>assistant\n{m[4:]}<|im_end|>\n"
                prompt += f"<|im_start|>user\n{comando_final}<|im_end|>\n<|im_start|>assistant\n"

                global STOP_GEN
                STOP_GEN = False
                resp_completa = ""
                try:
                    stream = ai_brain(prompt, max_tokens=-1, stop=["<|im_end|>"], stream=True, temperature=0.5)
                    for chunk in stream:
                        if STOP_GEN:
                            break
                        token = chunk["choices"][0]["text"]
                        resp_completa += token
                        await websocket.send_json({"type": "stream", "text": token})
                    await websocket.send_json({"type": "done"})
                    sessao_memoria_ram.append(f"R2: {resp_completa}")
                    salvar_no_historico_json(comando, resp_completa)
                except ValueError as e:
                    erro_msg = f"⚠️ <b>Capacidade Analítica Excedida:</b> O arquivo ou texto é grande demais para o limite atual de tokens. Tente fatiar o arquivo.<br><i>Detalhes: {str(e)}</i>"
                    await websocket.send_json({"type": "system", "text": erro_msg})
                    await websocket.send_json({"type": "done"})
                except Exception as e:
                    await websocket.send_json({"type": "system", "text": f"❌ <b>Falha Crítica no Cérebro LLM:</b> {str(e)}"})
                    await websocket.send_json({"type": "done"})
            else:
                await websocket.send_json({"type": "system", "text": "⚠️ Cérebro LLM não carregado. Verifique o modelo GGUF."})

    except WebSocketDisconnect:
        pass

# ══════════════════════════════════════════
# ENTRYPOINT (AUTO-BOOT DESKTOP)
# ══════════════════════════════════════════
if __name__ == "__main__":
    import threading
    import webview
    import time
    import os

    def run_server():
        uvicorn.run(app, host="127.0.0.1", port=8000, log_level="error")

    print("🚀 [BOOT] Ligando turbinas do servidor em segundo plano...")
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    print("🖥️ [BOOT] Desenhando Interface Nativa...")
    janela = webview.create_window(
        'R2 · Ghost Protocol', 
        'http://127.0.0.1:8000',
        width=1280, 
        height=800,
        background_color='#020b14',
        text_select=True
    )
    
    webview.start()
    
    print("🛑 [SHUTDOWN] Janela fechada. Cortando energia do terminal...")
    os._exit(0)