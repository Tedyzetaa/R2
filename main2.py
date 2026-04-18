import os, json, datetime, sys, time, asyncio, urllib.request, subprocess, shutil, re, gc
from io import BytesIO
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import torch
import faiss
from sentence_transformers import SentenceTransformer

# ==========================================
# 📂 IMPORTAÇÕES TÁTICAS SEGURAS
# ==========================================
def safe_import(module_name, class_name):
    try:
        import importlib
        mod = importlib.import_module(f"features.{module_name}")
        return getattr(mod, class_name)
    except Exception as e:
        print(f"⚠️ Módulo {class_name} ({module_name}) indisponível: {e}")
        return None

AirTrafficControl = safe_import("air_traffic", "AirTrafficControl")
AstroDefenseSystem = safe_import("astro_defense", "AstroDefenseSystem")
PizzaINTService = safe_import("pizzint_service", "PizzaINTService")
NOAAService = safe_import("noaa_service", "NOAAService")
GeoSeismicSystem = safe_import("geo_seismic", "GeoSeismicSystem")
SpeedTestModule = safe_import("net_speed", "SpeedTestModule")

VideoSurgeon = safe_import("video_ops", "VideoSurgeon")
if not VideoSurgeon:
    try:
        from video_ops import VideoSurgeon
        print("✂️ [TESOURA NEURAL]: Carregada da raiz.")
    except: VideoSurgeon = None
video_ops = VideoSurgeon() if VideoSurgeon else None

# ==========================================
# 📚 NÚCLEO RAG COM MEMÓRIA PERSISTENTE NO HD
# ==========================================
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
                print(f"📚 [RAG]: Memória restaurada do HD! {len(self.arquivos_indexados)} arquivos no gatilho.")
            except: print("⚠️ [RAG]: Erro ao ler memória. Use /doc sync para recriar.")
        else: print("⚠️ [RAG]: Cofre vazio. Use /doc sync para gravar pela primeira vez.")

    def sync(self):
        import PyPDF2
        if not self.embedder: self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        self.chunks = []; self.arquivos_indexados = [] 
        arquivos = [f for f in os.listdir(self.docs_dir) if f.lower().endswith(('.pdf', '.md'))]
        if not arquivos: return "⚠️ Nenhum documento em static/docs."
        
        for arq in arquivos:
            try:
                p = os.path.join(self.docs_dir, arq)
                if arq.endswith('.pdf'):
                    with open(p, 'rb') as f: text = "".join([pg.extract_text() or "" for pg in PyPDF2.PdfReader(f).pages])
                else:
                    with open(p, 'r', encoding='utf-8') as f: text = f.read()
                
                if text.strip():
                    self.arquivos_indexados.append(arq) 
                    for i in range(0, len(text), 800):
                        chunk = text[i:i+1000].encode('utf-8', 'ignore').decode('utf-8')
                        chunk = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', ' ', chunk).strip()
                        if len(chunk) > 50: self.chunks.append(f"[Fonte: {arq}] {chunk}")
            except: continue

        if not self.chunks: return "❌ Extração falhou."
        embeddings = self.embedder.encode(self.chunks, convert_to_numpy=True, show_progress_bar=True)
        self.index = faiss.IndexFlatL2(embeddings.shape[1])
        self.index.add(embeddings)
        
        try:
            faiss.write_index(self.index, self.index_path)
            with open(self.data_path, "w", encoding="utf-8") as f:
                json.dump({"chunks": self.chunks, "arquivos_indexados": self.arquivos_indexados}, f, ensure_ascii=False)
        except Exception as e: return f"⚠️ Gravado em RAM, erro no HD: {e}"
        return f"✅ Cérebro Blindado no HD! {len(self.arquivos_indexados)} arquivos integrados."

    def search(self, query):
        if not self.index: return None
        if not self.embedder: self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        q_emb = self.embedder.encode([query], convert_to_numpy=True)
        _, indices = self.index.search(q_emb, 3)
        return "\n\n".join([self.chunks[idx] for idx in indices[0] if idx < len(self.chunks)])

# ==========================================
# 🎨 MOTOR VISUAL E INICIALIZAÇÃO
# ==========================================
class UltraVisualCore:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.pipe = None; self.caminho = "visual_models/Realistic_Vision_V5.1.safetensors"
    def generate(self, prompt):
        if not self.pipe:
            from diffusers import StableDiffusionPipeline
            self.pipe = StableDiffusionPipeline.from_single_file(self.caminho, torch_dtype=torch.float16, use_safetensors=True, local_files_only=True)
            self.pipe.enable_model_cpu_offload()
            self.pipe.enable_attention_slicing()
        with torch.inference_mode():
            return self.pipe(prompt=f"RAW photo, {prompt}, 8k uhd", negative_prompt="cgi, render, cartoon", num_inference_steps=25, height=768, width=512).images[0]

os.makedirs("static/media", exist_ok=True)
rag_ops = KnowledgeBase(); img_ops = UltraVisualCore()
radar_ops = AirTrafficControl() if AirTrafficControl else None
astro_ops = AstroDefenseSystem() if AstroDefenseSystem else None
pizza_ops = PizzaINTService(config={}) if PizzaINTService else None
noaa_ops = NOAAService() if NOAAService else None

try:
    from llama_cpp import Llama
    print("🧠 [CÉREBRO] Iniciando LLaMA otimizado...")
    ai_brain = Llama(model_path="models/Dolphin3.0-Llama3.1-8B-Q4_K_M.gguf", n_ctx=10240, n_gpu_layers=20, verbose=False)
except: ai_brain = None

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"])
app.mount("/static", StaticFiles(directory="static"), name="static")

STOP_GEN = False
memoria_ram = []

# ==========================================
# INJEÇÃO HTML AUTOMÁTICA
# ==========================================
HTML_TEMPLATE = """
<!DOCTYPE html>
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
/* ═══════════════════════════════════════════
   TOKENS & RESET
═══════════════════════════════════════════ */
:root {
  --bg:        #030a12;
  --surface:   #07111e;
  --panel:     #0b1929;
  --border:    rgba(14, 165, 233, 0.15);
  --border-hi: rgba(14, 165, 233, 0.4);
  --blue:      #0ea5e9;
  --blue-dim:  rgba(14, 165, 233, 0.08);
  --green:     #10b981;
  --green-dim: rgba(16, 185, 129, 0.08);
  --amber:     #f59e0b;
  --red:       #ef4444;
  --text:      #cbd5e1;
  --text-muted:#4b6280;
  --text-hi:   #e2e8f0;
  --radius:    10px;
  --sidebar-w: 280px;
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body {
  height: 100%;
  overflow: hidden;
  background: var(--bg);
  color: var(--text);
  font-family: 'Inter', sans-serif;
  font-size: 15px;
  line-height: 1.6;
}

::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border-hi); border-radius: 2px; }

/* ═══════════════════════════════════════════
   HEX GRID BACKGROUND
═══════════════════════════════════════════ */
body::before {
  content: '';
  position: fixed;
  inset: 0;
  background-image:
    linear-gradient(rgba(14,165,233,0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(14,165,233,0.03) 1px, transparent 1px);
  background-size: 48px 48px;
  pointer-events: none;
  z-index: 0;
}

body::after {
  content: '';
  position: fixed;
  inset: 0;
  background: radial-gradient(ellipse 80% 60% at 50% 0%, rgba(14,165,233,0.06) 0%, transparent 70%);
  pointer-events: none;
  z-index: 0;
}

/* SCAN LINE */
@keyframes scanline {
  0%   { transform: translateY(-100vh); }
  100% { transform: translateY(100vh); }
}
.scanline {
  position: fixed;
  top: 0; left: 0; right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, rgba(14,165,233,0.15), transparent);
  animation: scanline 8s linear infinite;
  pointer-events: none;
  z-index: 1;
}

/* ═══════════════════════════════════════════
   LAYOUT SHELL
═══════════════════════════════════════════ */
#app {
  position: relative;
  display: flex;
  flex-direction: column;
  height: 100vh;
  z-index: 2;
}

/* ═══════════════════════════════════════════
   HEADER
═══════════════════════════════════════════ */
#header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  height: 60px;
  background: rgba(7, 17, 30, 0.95);
  border-bottom: 1px solid var(--border);
  backdrop-filter: blur(12px);
  flex-shrink: 0;
  z-index: 100;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 14px;
}

#menu-btn {
  background: none;
  border: 1px solid var(--border);
  color: var(--blue);
  width: 36px;
  height: 36px;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  flex-shrink: 0;
}
#menu-btn:hover {
  background: var(--blue-dim);
  border-color: var(--border-hi);
  box-shadow: 0 0 12px rgba(14,165,233,0.2);
}
#menu-btn svg { width: 18px; height: 18px; }

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
}

.logo-icon {
  width: 34px;
  height: 34px;
  background: linear-gradient(135deg, rgba(14,165,233,0.2), rgba(16,185,129,0.1));
  border: 1px solid var(--border-hi);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: 'Share Tech Mono', monospace;
  font-size: 13px;
  color: var(--blue);
  font-weight: bold;
}

.logo-text {
  display: flex;
  flex-direction: column;
  line-height: 1.1;
}
.logo-title {
  font-family: 'Rajdhani', sans-serif;
  font-size: 17px;
  font-weight: 700;
  color: var(--text-hi);
  letter-spacing: 1.5px;
  text-transform: uppercase;
}
.logo-sub {
  font-family: 'Share Tech Mono', monospace;
  font-size: 10px;
  color: var(--text-muted);
  letter-spacing: 2px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.status-pill {
  display: flex;
  align-items: center;
  gap: 7px;
  font-family: 'Share Tech Mono', monospace;
  font-size: 11px;
  color: var(--green);
  background: var(--green-dim);
  border: 1px solid rgba(16,185,129,0.25);
  padding: 5px 12px;
  border-radius: 20px;
  letter-spacing: 1px;
}

@keyframes pulse-dot {
  0%, 100% { opacity: 1; transform: scale(1); }
  50%       { opacity: 0.5; transform: scale(0.7); }
}
.status-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--green);
  box-shadow: 0 0 6px var(--green);
  animation: pulse-dot 2s ease-in-out infinite;
}
.status-dot.offline {
  background: var(--red);
  box-shadow: 0 0 6px var(--red);
  animation: none;
}

/* ═══════════════════════════════════════════
   SIDEBAR OVERLAY
═══════════════════════════════════════════ */
#overlay {
  display: none;
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.6);
  backdrop-filter: blur(4px);
  z-index: 200;
  opacity: 0;
  transition: opacity 0.3s;
}
#overlay.active {
  display: block;
  opacity: 1;
}

/* ═══════════════════════════════════════════
   SIDEBAR
═══════════════════════════════════════════ */
#sidebar {
  position: fixed;
  left: calc(-1 * var(--sidebar-w) - 20px);
  top: 0;
  width: var(--sidebar-w);
  height: 100%;
  background: rgba(7, 17, 30, 0.98);
  border-right: 1px solid var(--border);
  z-index: 300;
  padding: 20px 16px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  transition: left 0.35s cubic-bezier(0.4,0,0.2,1);
  overflow-y: auto;
  backdrop-filter: blur(20px);
}
#sidebar.open { left: 0; }

.sidebar-label {
  font-family: 'Share Tech Mono', monospace;
  font-size: 10px;
  color: var(--text-muted);
  letter-spacing: 3px;
  padding: 14px 10px 8px;
  text-transform: uppercase;
}
.sidebar-label:first-child { padding-top: 8px; }

.mod-btn {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 11px 14px;
  background: transparent;
  border: 1px solid transparent;
  border-radius: var(--radius);
  color: var(--text);
  font-family: 'Inter', sans-serif;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  text-align: left;
  transition: all 0.2s;
  width: 100%;
}
.mod-btn .icon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 15px;
  flex-shrink: 0;
  background: var(--blue-dim);
  border: 1px solid var(--border);
  transition: all 0.2s;
}
.mod-btn:hover {
  background: var(--blue-dim);
  border-color: var(--border-hi);
  color: var(--text-hi);
  transform: translateX(4px);
}
.mod-btn:hover .icon {
  background: rgba(14,165,233,0.15);
  border-color: var(--border-hi);
  box-shadow: 0 0 10px rgba(14,165,233,0.2);
}

.sidebar-divider {
  height: 1px;
  background: var(--border);
  margin: 8px 0;
}

/* ═══════════════════════════════════════════
   CHAT AREA
═══════════════════════════════════════════ */
#chat-wrapper {
  flex: 1;
  overflow-y: auto;
  padding: 24px 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

#chat {
  width: 100%;
  max-width: 860px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* Boot message */
.boot-msg {
  text-align: center;
  padding: 48px 20px 32px;
  animation: fadeUp 0.6s ease both;
}
.boot-logo {
  font-family: 'Rajdhani', sans-serif;
  font-size: 42px;
  font-weight: 700;
  color: var(--blue);
  letter-spacing: 6px;
  text-shadow: 0 0 40px rgba(14,165,233,0.3);
  margin-bottom: 8px;
}
.boot-sub {
  font-family: 'Share Tech Mono', monospace;
  font-size: 12px;
  color: var(--text-muted);
  letter-spacing: 4px;
  margin-bottom: 32px;
}
.boot-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  max-width: 480px;
  margin: 0 auto;
}
.boot-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 14px 12px;
  font-size: 12px;
  color: var(--text-muted);
  cursor: pointer;
  transition: all 0.2s;
  font-family: 'Share Tech Mono', monospace;
}
.boot-card:hover {
  border-color: var(--border-hi);
  color: var(--blue);
  background: var(--blue-dim);
}

/* Message animations */
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(12px); }
  to   { opacity: 1; transform: translateY(0); }
}

/* Base message */
.msg {
  display: flex;
  gap: 12px;
  animation: fadeUp 0.25s ease both;
  max-width: 100%;
}

/* User message */
.msg.user {
  flex-direction: row-reverse;
}

.msg-avatar {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: 'Share Tech Mono', monospace;
  font-size: 11px;
  font-weight: bold;
  align-self: flex-end;
}
.msg.user .msg-avatar {
  background: rgba(14,165,233,0.15);
  border: 1px solid rgba(14,165,233,0.3);
  color: var(--blue);
}
.msg.bot .msg-avatar {
  background: rgba(16,185,129,0.1);
  border: 1px solid rgba(16,185,129,0.25);
  color: var(--green);
}
.msg.sys .msg-avatar {
  background: rgba(245,158,11,0.1);
  border: 1px solid rgba(245,158,11,0.25);
  color: var(--amber);
}

.msg-body {
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-width: calc(100% - 44px);
}
.msg.user .msg-body { align-items: flex-end; }

.msg-sender {
  font-family: 'Share Tech Mono', monospace;
  font-size: 10px;
  color: var(--text-muted);
  letter-spacing: 1.5px;
  text-transform: uppercase;
}

.msg-bubble {
  padding: 12px 16px;
  border-radius: 12px;
  font-size: 14.5px;
  line-height: 1.65;
  word-break: break-word;
  max-width: 100%;
}
.msg.user .msg-bubble {
  background: rgba(14,165,233,0.1);
  border: 1px solid rgba(14,165,233,0.25);
  border-bottom-right-radius: 4px;
  color: var(--text-hi);
}
.msg.bot .msg-bubble {
  background: var(--surface);
  border: 1px solid var(--border);
  border-bottom-left-radius: 4px;
  color: var(--text);
  width: 100%;
}
.msg.sys .msg-bubble {
  background: rgba(245,158,11,0.06);
  border: 1px solid rgba(245,158,11,0.2);
  color: #fbbf24;
  font-family: 'Share Tech Mono', monospace;
  font-size: 13px;
}

/* Markdown inside bot messages */
.msg-bubble h1,.msg-bubble h2,.msg-bubble h3 {
  color: var(--text-hi);
  font-family: 'Rajdhani', sans-serif;
  letter-spacing: 0.5px;
  margin: 12px 0 6px;
}
.msg-bubble p { margin: 6px 0; }
.msg-bubble code {
  background: rgba(14,165,233,0.1);
  border: 1px solid var(--border);
  padding: 1px 6px;
  border-radius: 4px;
  font-family: 'Share Tech Mono', monospace;
  font-size: 13px;
  color: var(--blue);
}
.msg-bubble pre {
  background: #070f1a;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 14px;
  overflow-x: auto;
  margin: 10px 0;
}
.msg-bubble pre code {
  background: none;
  border: none;
  padding: 0;
  color: inherit;
  font-size: 13px;
}
.msg-bubble ul,.msg-bubble ol { padding-left: 20px; }
.msg-bubble a { color: var(--blue); }
.msg-bubble img { max-width: 100%; border-radius: 8px; margin-top: 8px; }
.msg-bubble video { max-width: 100%; border-radius: 8px; margin-top: 8px; }
.msg-bubble b,.msg-bubble strong { color: var(--text-hi); }

/* Typing indicator */
@keyframes blink {
  0%,80%,100% { transform: scale(0.6); opacity: 0.3; }
  40%         { transform: scale(1);   opacity: 1;   }
}
.typing-dots {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 4px 0;
}
.typing-dots span {
  width: 7px; height: 7px;
  background: var(--green);
  border-radius: 50%;
  box-shadow: 0 0 6px var(--green);
  animation: blink 1.4s infinite ease-in-out both;
}
.typing-dots span:nth-child(1) { animation-delay: -0.32s; }
.typing-dots span:nth-child(2) { animation-delay: -0.16s; }

/* ═══════════════════════════════════════════
   INPUT AREA
═══════════════════════════════════════════ */
#input-wrapper {
  flex-shrink: 0;
  padding: 12px 16px 16px;
  background: rgba(7,17,30,0.95);
  border-top: 1px solid var(--border);
  backdrop-filter: blur(12px);
}

#input-row {
  display: flex;
  gap: 10px;
  max-width: 860px;
  margin: 0 auto;
  align-items: flex-end;
}

#msgBox {
  flex: 1;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 12px 16px;
  color: var(--text-hi);
  font-family: 'Inter', sans-serif;
  font-size: 14.5px;
  resize: none;
  max-height: 130px;
  transition: border-color 0.2s, box-shadow 0.2s;
  line-height: 1.5;
}
#msgBox::placeholder { color: var(--text-muted); }
#msgBox:focus {
  outline: none;
  border-color: var(--border-hi);
  box-shadow: 0 0 0 3px rgba(14,165,233,0.08), inset 0 0 12px rgba(14,165,233,0.04);
}

#send-btn {
  background: var(--blue);
  border: none;
  color: #030a12;
  padding: 0 20px;
  height: 46px;
  border-radius: var(--radius);
  font-family: 'Rajdhani', sans-serif;
  font-weight: 700;
  font-size: 14px;
  letter-spacing: 1.5px;
  text-transform: uppercase;
  cursor: pointer;
  transition: all 0.2s;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}
#send-btn:hover {
  background: #38bdf8;
  box-shadow: 0 0 20px rgba(14,165,233,0.4);
  transform: translateY(-1px);
}
#send-btn:active { transform: translateY(0); }
#send-btn svg { width: 16px; height: 16px; }

.input-hint {
  max-width: 860px;
  margin: 6px auto 0;
  font-size: 11px;
  color: var(--text-muted);
  font-family: 'Share Tech Mono', monospace;
  letter-spacing: 0.5px;
}

/* ═══════════════════════════════════════════
   VIDEO STUDIO MODAL
═══════════════════════════════════════════ */
#studio-backdrop {
  display: none;
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.75);
  backdrop-filter: blur(6px);
  z-index: 400;
  align-items: center;
  justify-content: center;
  padding: 20px;
}
#studio-backdrop.open { display: flex; }

#video-studio {
  background: var(--panel);
  border: 1px solid var(--border-hi);
  border-radius: 14px;
  width: 100%;
  max-width: 780px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 0 60px rgba(14,165,233,0.12), 0 40px 80px rgba(0,0,0,0.6);
  animation: fadeUp 0.3s ease both;
}

.studio-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px 16px;
  border-bottom: 1px solid var(--border);
}
.studio-title {
  font-family: 'Rajdhani', sans-serif;
  font-size: 18px;
  font-weight: 700;
  color: var(--text-hi);
  letter-spacing: 1px;
  text-transform: uppercase;
  display: flex;
  align-items: center;
  gap: 10px;
}
.studio-title-badge {
  font-size: 11px;
  background: rgba(14,165,233,0.15);
  border: 1px solid var(--border-hi);
  color: var(--blue);
  padding: 3px 10px;
  border-radius: 20px;
  font-family: 'Share Tech Mono', monospace;
  letter-spacing: 1px;
  font-weight: normal;
}
.close-studio {
  background: rgba(239,68,68,0.1);
  border: 1px solid rgba(239,68,68,0.3);
  color: var(--red);
  width: 32px; height: 32px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 16px;
  display: flex; align-items: center; justify-content: center;
  transition: all 0.2s;
  flex-shrink: 0;
}
.close-studio:hover {
  background: rgba(239,68,68,0.2);
  box-shadow: 0 0 10px rgba(239,68,68,0.3);
}

.studio-body {
  padding: 20px 24px 24px;
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 20px;
  align-items: start;
}
@media (max-width: 600px) {
  .studio-body { grid-template-columns: 1fr; }
}

.preview-box {
  width: 160px;
  aspect-ratio: 9/16;
  background: #000 url('https://images.unsplash.com/photo-1611162617474-5b21e879e113?q=80&w=300&auto=format&fit=crop') center/cover;
  border-radius: 10px;
  border: 1px solid var(--border);
  position: relative;
  overflow: hidden;
  flex-shrink: 0;
}
.preview-box::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(to top, rgba(0,0,0,0.6) 0%, transparent 50%);
}
#preview-subtitle {
  position: absolute;
  bottom: 18%;
  left: 50%;
  transform: translateX(-50%);
  text-align: center;
  font-family: 'Rajdhani', sans-serif;
  font-size: 13px;
  font-weight: 700;
  color: #fff;
  text-transform: uppercase;
  white-space: nowrap;
  transition: all 0.15s;
  width: 90%;
}

.controls-panel { display: flex; flex-direction: column; gap: 12px; }

.ctrl-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
@media (max-width: 480px) { .ctrl-row { grid-template-columns: 1fr; } }

.ctrl-group { display: flex; flex-direction: column; gap: 5px; }
.ctrl-group.full { grid-column: span 2; }
@media (max-width: 480px) { .ctrl-group.full { grid-column: span 1; } }

.ctrl-label {
  font-size: 11px;
  color: var(--text-muted);
  font-family: 'Share Tech Mono', monospace;
  letter-spacing: 1px;
  text-transform: uppercase;
}

.ctrl-input {
  background: var(--surface);
  border: 1px solid var(--border);
  color: var(--text-hi);
  padding: 9px 12px;
  border-radius: 8px;
  font-family: 'Inter', sans-serif;
  font-size: 13.5px;
  transition: border-color 0.2s;
  width: 100%;
}
.ctrl-input:focus {
  outline: none;
  border-color: var(--border-hi);
}
.ctrl-input option { background: var(--panel); }

input[type="range"].ctrl-input {
  padding: 4px 0;
  border: none;
  background: none;
  accent-color: var(--blue);
  cursor: pointer;
}
input[type="color"].ctrl-input {
  padding: 3px;
  height: 38px;
  cursor: pointer;
}

.toggle-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 12px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
}
.toggle-row span {
  font-size: 13.5px;
  color: var(--text);
}
input[type="checkbox"] {
  width: 16px; height: 16px;
  accent-color: var(--blue);
  cursor: pointer;
}

.action-btn {
  width: 100%;
  padding: 13px;
  background: var(--blue);
  border: none;
  color: #030a12;
  border-radius: var(--radius);
  font-family: 'Rajdhani', sans-serif;
  font-weight: 700;
  font-size: 15px;
  letter-spacing: 1.5px;
  text-transform: uppercase;
  cursor: pointer;
  margin-top: 4px;
  transition: all 0.2s;
}
.action-btn:hover {
  background: #38bdf8;
  box-shadow: 0 0 24px rgba(14,165,233,0.4);
  transform: translateY(-2px);
}

/* ═══════════════════════════════════════════
   CONNECTION TOAST
═══════════════════════════════════════════ */
#toast {
  position: fixed;
  bottom: 90px;
  left: 50%;
  transform: translateX(-50%) translateY(20px);
  background: rgba(7,17,30,0.95);
  border: 1px solid var(--border-hi);
  border-radius: 8px;
  padding: 10px 20px;
  font-family: 'Share Tech Mono', monospace;
  font-size: 12px;
  color: var(--blue);
  opacity: 0;
  transition: all 0.3s;
  pointer-events: none;
  z-index: 500;
  white-space: nowrap;
}
#toast.show {
  opacity: 1;
  transform: translateX(-50%) translateY(0);
}

/* ═══════════════════════════════════════════
   RESPONSIVE
═══════════════════════════════════════════ */
@media (max-width: 600px) {
  #header { padding: 0 12px; }
  .logo-sub { display: none; }
  #chat-wrapper { padding: 16px 10px; }
  .boot-grid { grid-template-columns: 1fr 1fr; }
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

<div id="app">
  <!-- HEADER -->
  <header id="header">
    <div class="header-left">
      <button id="menu-btn" onclick="toggleSidebar()" aria-label="Menu">
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
          <span class="logo-sub">Tactical OS · v4.2</span>
        </div>
      </div>
    </div>
    <div class="header-right">
      <div class="status-pill" id="status-pill">
        <div class="status-dot" id="status-dot"></div>
        <span id="status-text">ONLINE</span>
      </div>
    </div>
  </header>

  <!-- SIDEBAR OVERLAY -->
  <div id="overlay" onclick="toggleSidebar()"></div>

  <!-- SIDEBAR -->
  <nav id="sidebar">
    <div class="sidebar-label">Documentos</div>
    <button class="mod-btn" onclick="execCmd('/doc sync', '📚 Sincronizando matriz de conhecimento...')">
      <div class="icon">📚</div>
      <span>Sincronizar PDFs</span>
    </button>
    <button class="mod-btn" onclick="execCmd('/doc list', '📋 Verificando inventário de arquivos...')">
      <div class="icon">📋</div>
      <span>Listar Arquivos</span>
    </button>

    <div class="sidebar-divider"></div>
    <div class="sidebar-label">Inteligência</div>

    <button class="mod-btn" onclick="execCmd('/cmd radar', '📡 Ativando radar de voos...')">
      <div class="icon">📡</div>
      <span>Radar de Voos</span>
    </button>
    <button class="mod-btn" onclick="execCmd('/cmd astro', '☄️ Consultando banco da NASA...')">
      <div class="icon">☄️</div>
      <span>Defesa Planetária</span>
    </button>
    <button class="mod-btn" onclick="execCmd('/cmd pizza', '🍕 Checando monitor PizzINT...')">
      <div class="icon">🍕</div>
      <span>Monitor PizzINT</span>
    </button>
    <button class="mod-btn" onclick="execCmd('/cmd solar', '☀️ Consultando dados solares...')">
      <div class="icon">☀️</div>
      <span>Clima Espacial</span>
    </button>

    <div class="sidebar-divider"></div>
    <div class="sidebar-label">Produção</div>

    <button class="mod-btn" onclick="openStudio()">
      <div class="icon">🎬</div>
      <span>Estúdio de Cortes</span>
    </button>
  </nav>

  <!-- CHAT AREA -->
  <main id="chat-wrapper">
    <div id="chat">
      <div class="boot-msg" id="boot-screen">
        <div class="boot-logo">R2</div>
        <div class="boot-sub">Ghost Protocol · Sistema Tático Online</div>
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
      <textarea
        id="msgBox"
        rows="1"
        placeholder="Digite sua ordem, Comandante..."
        oninput="autoResize(this)"
        onkeydown="handleKey(event)"
      ></textarea>
      <button id="send-btn" onclick="sendMsg()">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <line x1="22" y1="2" x2="11" y2="13"/>
          <polygon points="22 2 15 22 11 13 2 9 22 2"/>
        </svg>
        <span>Enviar</span>
      </button>
    </div>
    <div class="input-hint">Enter para enviar · Shift+Enter para nova linha</div>
  </footer>
</div>

<!-- VIDEO STUDIO MODAL -->
<div id="studio-backdrop" onclick="closeStudioOnBack(event)">
  <div id="video-studio">
    <div class="studio-header">
      <div class="studio-title">
        Estúdio de Cortes
        <span class="studio-title-badge">TESOURA NEURAL</span>
      </div>
      <button class="close-studio" onclick="closeStudio()">✕</button>
    </div>
    <div class="studio-body">
      <div class="preview-box">
        <div id="preview-subtitle">A JORNADA<br>COMEÇA AQUI!</div>
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
              <input type="checkbox" id="sub-pos-auto" checked onchange="document.getElementById('sub-pos').disabled=this.checked">
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
            <input type="range" id="sub-size" class="ctrl-input" min="10" max="22" value="13" oninput="updatePreview(); document.getElementById('size-val').textContent=this.value+'px'">
          </div>
        </div>
        <div class="ctrl-row">
          <div class="ctrl-group">
            <label class="ctrl-label">Posição Y: <span id="pos-val">18%</span></label>
            <input type="range" id="sub-pos" class="ctrl-input" min="5" max="95" value="18" disabled oninput="updatePreview(); document.getElementById('pos-val').textContent=this.value+'%'">
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
// ═══════════════════════════════
// WEBSOCKET ENGINE
// ═══════════════════════════════
let ws = null;
let isConnected = false;

function conectarMatriz() {
  const proto = location.protocol === 'https:' ? 'wss://' : 'ws://';
  ws = new WebSocket(`${proto}${location.host}/ws`);

  ws.onopen = () => {
    isConnected = true;
    setStatus(true);
    showToast('Conexão estabelecida com o servidor');
  };

  ws.onmessage = (event) => {
    let data;
    try { data = JSON.parse(event.data); } catch { return; }

    if (data.type === 'system') {
      hideTyping();
      appendMsg('sys', 'SYS', data.text);
    } else if (data.type === 'stream') {
      hideTyping();
      let chatEl = document.getElementById('chat');
      let last = chatEl.lastElementChild;
      // If last is a bot bubble, append to it
      if (last && last.dataset.role === 'bot') {
        last.querySelector('.bot-content').innerHTML += data.text;
      } else {
        appendMsg('bot', 'R2', data.text, true);
      }
      chatEl.parentElement.scrollTop = chatEl.parentElement.scrollHeight;
    } else if (data.type === 'done') {
      hideTyping();
      renderMarkdown();
    } else if (data.type === 'image') {
      hideTyping();
      appendMsg('sys', 'SYS', `<b>${data.text}</b><br><img src="${data.url}" alt="Imagem tática">`);
    }
  };

  ws.onclose = () => {
    isConnected = false;
    setStatus(false);
    showToast('Reconectando em 3s...');
    setTimeout(conectarMatriz, 3000);
  };

  ws.onerror = (e) => { console.error('WS error:', e); };
}

function setStatus(online) {
  const dot  = document.getElementById('status-dot');
  const text = document.getElementById('status-text');
  const pill = document.getElementById('status-pill');
  if (online) {
    dot.classList.remove('offline');
    text.textContent = 'ONLINE';
    pill.style.color = 'var(--green)';
    pill.style.background = 'var(--green-dim)';
    pill.style.borderColor = 'rgba(16,185,129,0.25)';
  } else {
    dot.classList.add('offline');
    text.textContent = 'OFFLINE';
    pill.style.color = 'var(--red)';
    pill.style.background = 'rgba(239,68,68,0.08)';
    pill.style.borderColor = 'rgba(239,68,68,0.25)';
  }
}

// ═══════════════════════════════
// TOAST
// ═══════════════════════════════
let toastTimer = null;
function showToast(msg) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => t.classList.remove('show'), 2800);
}

// ═══════════════════════════════
// MESSAGES
// ═══════════════════════════════
function removeBootScreen() {
  const boot = document.getElementById('boot-screen');
  if (boot) boot.remove();
}

function appendMsg(role, sender, text, isStream = false) {
  removeBootScreen();
  const chat = document.getElementById('chat');
  const wrapper = document.createElement('div');
  wrapper.className = `msg ${role}`;
  if (role === 'bot') wrapper.dataset.role = 'bot';

  const avatarText = role === 'user' ? 'TED' : role === 'bot' ? 'R2' : 'SYS';
  const contentClass = role === 'bot' ? 'class="bot-content"' : '';

  wrapper.innerHTML = `
    <div class="msg-avatar">${avatarText}</div>
    <div class="msg-body">
      <div class="msg-sender">${sender}</div>
      <div class="msg-bubble"><div ${contentClass}>${text}</div></div>
    </div>
  `;

  chat.appendChild(wrapper);
  chat.parentElement.scrollTop = chat.parentElement.scrollHeight;
}

function renderMarkdown() {
  const chat = document.getElementById('chat');
  const lastBot = [...chat.children].filter(el => el.dataset.role === 'bot').at(-1);
  if (!lastBot) return;
  const content = lastBot.querySelector('.bot-content');
  if (!content) return;
  try {
    content.innerHTML = marked.parse(content.innerHTML);
    content.querySelectorAll('pre code').forEach(block => hljs.highlightElement(block));
  } catch(e) { console.error(e); }
  chat.parentElement.scrollTop = chat.parentElement.scrollHeight;
}

function showTyping() {
  removeBootScreen();
  if (document.getElementById('typing-row')) return;
  const chat = document.getElementById('chat');
  const row = document.createElement('div');
  row.id = 'typing-row';
  row.className = 'msg bot';
  row.innerHTML = `
    <div class="msg-avatar">R2</div>
    <div class="msg-body">
      <div class="msg-sender">R2</div>
      <div class="msg-bubble">
        <div class="typing-dots"><span></span><span></span><span></span></div>
      </div>
    </div>
  `;
  chat.appendChild(row);
  chat.parentElement.scrollTop = chat.parentElement.scrollHeight;
}

function hideTyping() {
  const t = document.getElementById('typing-row');
  if (t) t.remove();
}

// ═══════════════════════════════
// SEND & COMMANDS
// ═══════════════════════════════
function sendMsg() {
  const box = document.getElementById('msgBox');
  const msg = box.value.trim();
  if (!msg) return;
  if (!ws || ws.readyState !== WebSocket.OPEN) {
    showToast('⚠️ Servidor offline. Aguarde reconexão...');
    return;
  }
  appendMsg('user', 'TEDDY', msg);
  ws.send(msg);
  box.value = '';
  box.style.height = '';
  showTyping();
}

function execCmd(cmd, label) {
  if (!ws || ws.readyState !== WebSocket.OPEN) {
    showToast('⚠️ Servidor offline.');
    return;
  }
  closeSidebar();
  appendMsg('user', 'TEDDY', label);
  ws.send(cmd);
  showTyping();
}

function quickPrompt(text) {
  document.getElementById('msgBox').value = text;
  sendMsg();
}

// ═══════════════════════════════
// SIDEBAR
// ═══════════════════════════════
function toggleSidebar() {
  document.getElementById('sidebar').classList.toggle('open');
  document.getElementById('overlay').classList.toggle('active');
}
function closeSidebar() {
  document.getElementById('sidebar').classList.remove('open');
  document.getElementById('overlay').classList.remove('active');
}

// ═══════════════════════════════
// INPUT RESIZE & KEY
// ═══════════════════════════════
function autoResize(el) {
  el.style.height = '';
  el.style.height = Math.min(el.scrollHeight, 130) + 'px';
}
function handleKey(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMsg();
  }
}

// ═══════════════════════════════
// VIDEO STUDIO
// ═══════════════════════════════
function openStudio() {
  document.getElementById('studio-backdrop').classList.add('open');
  closeSidebar();
}
function closeStudio() {
  document.getElementById('studio-backdrop').classList.remove('open');
}
function closeStudioOnBack(e) {
  if (e.target === document.getElementById('studio-backdrop')) closeStudio();
}

function updatePreview() {
  const sub   = document.getElementById('preview-subtitle');
  const color = document.getElementById('sub-color').value;
  const size  = document.getElementById('sub-size').value;
  const pos   = document.getElementById('sub-pos').value;
  const style = document.getElementById('sub-style').value;

  sub.style.color    = color;
  sub.style.fontSize = size + 'px';
  sub.style.bottom   = pos + '%';

  const styles = {
    outline: { textShadow: '1px 1px 0 #000,-1px -1px 0 #000,1px -1px 0 #000,-1px 1px 0 #000', background: 'transparent', padding: '0' },
    shadow:  { textShadow: '3px 3px 6px rgba(0,0,0,0.9)',                                      background: 'transparent', padding: '0' },
    box:     { textShadow: 'none',                                                               background: 'rgba(0,0,0,0.65)', padding: '3px 10px', borderRadius: '5px' },
    yellow:  { textShadow: '2px 2px 0 #000',                                                   background: 'transparent', padding: '0', color: '#ffff00' },
  };
  const s = styles[style] || styles.outline;
  Object.assign(sub.style, s);
  if (style === 'yellow') sub.style.color = '#ffff00';
  else sub.style.color = color;
}

function startVideoExtraction() {
  const url = document.getElementById('vid-url').value.trim();
  if (!url) { showToast('Insira o link do vídeo alvo!'); return; }

  const config = {
    url,
    active:  document.getElementById('sub-active').checked,
    autoPos: document.getElementById('sub-pos-auto').checked,
    color:   document.getElementById('sub-color').value,
    size:    document.getElementById('sub-size').value,
    style:   document.getElementById('sub-style').value,
    pos:     document.getElementById('sub-pos').value,
  };

  closeStudio();
  execCmd(`/vid extract ${JSON.stringify(config)}`, '🎬 Operação iniciada — IA calculando cortes e enquadramento...');
}

// ═══════════════════════════════
// BOOT
// ═══════════════════════════════
conectarMatriz();
</script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def serve_gui(): return HTML_TEMPLATE

# ==========================================
# 🧠 ROTEADOR LÓGICO (WEBSOCKET)
# ==========================================
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    async def processar_midia(caminho):
        if caminho and os.path.exists(caminho):
            n = f"scan_{int(time.time())}_{os.path.basename(caminho)}"
            shutil.copy(caminho, os.path.join("static/media", n))
            return f"/static/media/{n}"
        return None

    try:
        while True:
            comando = await websocket.receive_text(); cmd_l = comando.lower().strip()

            if cmd_l.startswith("/cmd "):
                sub = cmd_l.replace("/cmd ", "")
                if sub == "pizza" and pizza_ops:
                    st = await asyncio.to_thread(pizza_ops.get_status)
                    if st.get('level', -1) == -1: msg = "❌ Falha ao interceptar a rede PizzINT."
                    else:
                        nivel = st['level']
                        defcon = 5 if nivel < 20 else (4 if nivel < 40 else (3 if nivel < 60 else (2 if nivel < 80 else 1)))
                        msg = f"🍕 **Monitor PizzINT**<br>Pedidos: <b>{nivel:.0f}/h</b><br>🚨 <b>DEFCON: {defcon}</b><br><br><b>Últimas:</b><br>"
                        if st.get('news'):
                            for n in st['news']: msg += f"• <a href='{n['url']}' target='_blank' style='color:#0ea5e9;'>{n['titulo']}</a><br>"
                    await websocket.send_json({"type": "system", "text": msg})
                
                elif sub == "solar" and noaa_ops:
                    await websocket.send_json({"type": "system", "text": "🛰️ Varrendo clima espacial — aguarde telemetria da NASA/NOAA..."})
                    
                    # 1. Busca a inteligência completa (Textos + Alertas + Imagens)
                    intel = await asyncio.to_thread(noaa_ops.get_full_intel)
                    
                    # 2. Envia o painel de texto tático blindado (mesmo que a imagem atrase)
                    painel_html = noaa_ops.gerar_html_painel(intel)
                    await websocket.send_json({"type": "system", "text": painel_html})
                    
                    # 3. Tenta renderizar o mapa D-RAP separadamente
                    drap_path, _ = intel.get("media", {}).get("drap", (None, None))
                    if drap_path:
                        u = await processar_midia(drap_path)
                        if u: 
                            await websocket.send_json({"type": "image", "url": u, "text": "🗺️ Mapa D-RAP (Absorção HF)"})
                            continue

            if cmd_l.startswith("/vid extract"):
                config = json.loads(comando.replace("/vid extract ", ""))
                loop = asyncio.get_event_loop()
                def cb(m): asyncio.run_coroutine_threadsafe(websocket.send_json({"type": "system", "text": m}), loop)
                ctx_rag = await asyncio.to_thread(rag_ops.search, "jornada do herói clímax viral tiktok") if rag_ops else None
                caminho_clip = await asyncio.to_thread(video_ops.processar_alvo, config, ai_brain, cb, ctx_rag)
                if caminho_clip: await websocket.send_json({"type": "system", "text": f"✅ Corte finalizado!<br><video width='100%' controls><source src='{caminho_clip}' type='video/mp4'></video>"})
                continue

            if cmd_l == "/doc sync":
                res = await asyncio.to_thread(rag_ops.sync); await websocket.send_json({"type": "system", "text": res})
                continue
            if cmd_l == "/doc list":
                res = f"📋 **Arquivos:** {', '.join(rag_ops.arquivos_indexados)}" if rag_ops.arquivos_indexados else "⚠️ Nenhum arquivo indexado."
                await websocket.send_json({"type": "system", "text": res}); continue

            if ai_brain:
                memoria_ram.append(f"Teddy: {comando}")
                ctx = await asyncio.to_thread(rag_ops.search, comando)
                prompt = f"<|im_start|>system\nVocê é o R2, IA direta e tática.\n"
                if ctx: prompt += f"\n[RAG PDFs]:\n{ctx}\n"
                prompt += "<|im_end|>\n"
                for m in memoria_ram[-10:-1]: prompt += f"<|im_start|>user\n{m[7:]}<|im_end|>\n" if m.startswith("Teddy: ") else f"<|im_start|>assistant\n{m[4:]}<|im_end|>\n"
                prompt += f"<|im_start|>user\n{comando}<|im_end|>\n<|im_start|>assistant\n"
                
                global STOP_GEN; STOP_GEN = False; resp_completa = ""
                stream = ai_brain(prompt, max_tokens=-1, stop=["<|im_end|>"], stream=True, temperature=0.5)
                for chunk in stream:
                    if STOP_GEN: break
                    token = chunk["choices"][0]["text"]; resp_completa += token
                    await websocket.send_json({"type": "stream", "text": token})
                await websocket.send_json({"type": "done"})
                memoria_ram.append(f"R2: {resp_completa}")
    except WebSocketDisconnect: pass

if __name__ == "__main__": uvicorn.run(app, host="0.0.0.0", port=8000)
