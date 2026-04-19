# filename: patch_stop_btn.py
import os

FILE_PATH = "main2.py"

def apply_stop_button():
    print("🛑 Instalando Botão Tático de Abortar Missão (Stop)...")

    if not os.path.exists(FILE_PATH):
        print(f"❌ {FILE_PATH} não encontrado.")
        return

    with open(FILE_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. BACKEND: Nova rota de emergência para parar o Cérebro LLM
    rota_stop = """@app.post("/api/stop")
async def api_stop():
    global STOP_GEN
    STOP_GEN = True
    return {"ok": True}

@app.post("/api/upload_arquivos")"""
    content = content.replace('@app.post("/api/upload_arquivos")', rota_stop)

    # 2. CSS: Estilização do modo de parada (Vermelho)
    css_stop = """#send-btn svg { width: 15px; height: 15px; }

/* BOTAO STOP */
#send-btn.stop-mode {
  background: linear-gradient(135deg, #ef4444, #b91c1c);
  box-shadow: 0 0 15px rgba(239,68,68,0.4);
}
#send-btn.stop-mode:hover {
  background: linear-gradient(135deg, #f87171, #ef4444);
}"""
    content = content.replace('#send-btn svg { width: 15px; height: 15px; }', css_stop)

    # 3. JAVASCRIPT: Lógica de alternância e requisição de parada
    js_vars = """var ws          = null;
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
}"""
    content = content.replace('var ws          = null;\nvar isConnected = false;\nvar toastTimer  = null;', js_vars)

    # 4. JAVASCRIPT HOOKS: Disparadores de mudança de estado do botão
    content = content.replace(
        "    } else if (data.type === 'done') {\n      hideTyping();\n      renderLastBot();", 
        "    } else if (data.type === 'done') {\n      hideTyping();\n      renderLastBot();\n      toggleSendButton(false);"
    )
    
    content = content.replace(
        "  chat.appendChild(row);\n  if (chat.parentElement) chat.parentElement.scrollTop = chat.parentElement.scrollHeight;\n}\nfunction hideTyping() {", 
        "  chat.appendChild(row);\n  if (chat.parentElement) chat.parentElement.scrollTop = chat.parentElement.scrollHeight;\n  toggleSendButton(true);\n}\nfunction hideTyping() {"
    )
    
    content = content.replace(
        "function handleKey(e) { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMsg(); } }", 
        "function handleKey(e) { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); if(!isGenerating) sendMsg(); } }"
    )
    
    content = content.replace(
        "  ws.onclose = function() {\n    isConnected = false;\n    setStatus(false);\n    showToast('Reconectando em 3s...');", 
        "  ws.onclose = function() {\n    isConnected = false;\n    setStatus(false);\n    toggleSendButton(false);\n    showToast('Reconectando em 3s...');"
    )

    with open(FILE_PATH, "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ Atualização concluída! O Botão de Parada de Emergência foi ativado no frontend.")

if __name__ == "__main__":
    apply_stop_button()