# filename: nuclear_fix_r2.py
import os

FILE_PATH = "main2.py"

def apply_nuclear_fix():
    print("☢️ [ALERTA]: Iniciando Reconstrução Nuclear da Interface...")
    
    if not os.path.exists(FILE_PATH):
        print(f"❌ {FILE_PATH} não encontrado.")
        return

    with open(FILE_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # O Novo Template de HTML/CSS/JS (Garantido sem erros de aspas)
    new_template = r'''
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
  <meta charset="UTF-8">
  <title>R2 · GHOST PROTOCOL</title>
  <link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@400;700&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #020b14; --panel: #061221; --border: #0ea5e933; --border-hi: #0ea5e9;
      --blue: #0ea5e9; --text: #e2e8f0; --text-muted: #94a3b8; --red: #ef4444; --radius: 12px;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0; background: var(--bg); color: var(--text);
      font-family: 'Rajdhani', sans-serif; height: 100vh; overflow: hidden; display: flex;
    }

    /* SIDEBAR */
    #sidebar {
      width: 280px; background: var(--panel); border-right: 1px solid var(--border);
      display: flex; flex-direction: column; transition: transform 0.3s ease;
      z-index: 1000;
    }
    .sidebar-header { padding: 20px; border-bottom: 1px solid var(--border); font-weight: 700; color: var(--blue); letter-spacing: 2px; }
    .sidebar-content { flex: 1; overflow-y: auto; padding: 10px; }
    .sidebar-section { padding: 15px 10px 5px; font-size: 11px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 1px; }
    .menu-item {
      padding: 12px; margin: 4px 0; border-radius: 8px; cursor: pointer;
      font-family: 'Share Tech Mono', monospace; font-size: 13px; transition: 0.2s;
    }
    .menu-item:hover { background: rgba(14,165,233,0.1); color: var(--blue); }

    /* MAIN CONTENT */
    main { flex: 1; display: flex; flex-direction: column; position: relative; }
    header {
      padding: 15px 25px; border-bottom: 1px solid var(--border);
      display: flex; justify-content: space-between; align-items: center;
      background: rgba(2, 11, 20, 0.8); backdrop-filter: blur(10px);
    }
    .status-group { display: flex; align-items: center; gap: 10px; font-family: 'Share Tech Mono', monospace; font-size: 12px; }
    #status-led { width: 8px; height: 8px; border-radius: 50%; background: var(--red); box-shadow: 0 0 10px var(--red); }

    /* CHAT */
    #chat-scroll { flex: 1; overflow-y: auto; padding: 20px; }
    #chat-container { max-width: 900px; margin: 0 auto; }
    .msg-row { margin-bottom: 25px; animation: fadeIn 0.3s ease; }
    .msg-author { font-family: 'Share Tech Mono', monospace; font-size: 11px; color: var(--blue); margin-bottom: 6px; }
    .msg-content { background: rgba(14,165,233,0.03); border: 1px solid var(--border); padding: 15px; border-radius: var(--radius); line-height: 1.6; }
    .user .msg-content { border-color: rgba(14,165,233,0.2); background: rgba(14,165,233,0.05); }

    /* INPUT AREA */
    #input-wrapper { padding: 20px; background: var(--panel); border-top: 1px solid var(--border); }
    #attachments-bar { display: flex; gap: 8px; flex-wrap: wrap; max-width: 860px; margin: 0 auto; }
    #attachments-bar:not(:empty) { margin-bottom: 12px; }
    .attach-pill {
      display: flex; align-items: center; gap: 8px; background: rgba(14,165,233,0.1);
      border: 1px solid var(--blue); padding: 6px 12px; border-radius: 8px;
      font-family: 'Share Tech Mono', monospace; font-size: 11px; color: var(--blue);
    }
    .rm-btn { cursor: pointer; color: var(--text-muted); font-weight: bold; }
    .rm-btn:hover { color: var(--red); }
    
    #input-row { max-width: 900px; margin: 0 auto; display: flex; gap: 12px; align-items: flex-end; }
    textarea {
      flex: 1; background: var(--bg); border: 1px solid var(--border);
      border-radius: var(--radius); color: var(--text); padding: 12px 15px;
      font-family: 'Rajdhani', sans-serif; font-size: 15px; resize: none; max-height: 200px;
    }
    textarea:focus { outline: none; border-color: var(--blue); box-shadow: 0 0 15px rgba(14,165,233,0.1); }
    
    button {
      background: var(--blue); border: none; border-radius: var(--radius);
      color: white; padding: 12px 20px; cursor: pointer; font-weight: 700;
      display: flex; align-items: center; gap: 8px; transition: 0.2s;
    }
    #upload-btn { background: var(--panel); border: 1px solid var(--border); color: var(--blue); }
    #send-btn.stop-mode { background: var(--red); }

    /* OVERLAY DRAG DROP */
    body.drag-over::after {
      content: 'SOLTE ARQUIVOS PARA ANALISAR'; position: fixed; inset: 0;
      background: rgba(2, 11, 20, 0.9); z-index: 9999; display: flex;
      align-items: center; justify-content: center; font-size: 24px;
      font-weight: 700; color: var(--blue); border: 4px dashed var(--blue);
    }

    @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
  </style>
</head>
<body>
  <aside id="sidebar">
    <div class="sidebar-header">R2 COMMANDER</div>
    <div class="sidebar-content">
      <div class="sidebar-section">VIGILÂNCIA</div>
      <div class="menu-item" onclick="triggerAction('/api/sentinel')">👁️ SENTINELA (CÂMERA)</div>
      <div class="menu-item" onclick="triggerAction('/api/net_scan')">📶 SCANNER DE REDE</div>
      
      <div class="sidebar-section">INTEL GLOBAL</div>
      <div class="menu-item" onclick="triggerAction('/api/defcon')">🍕 RADAR GEOPOLÍTICO</div>
      <div class="menu-item" onclick="triggerAction('/api/market')">💰 MARKET INTEL</div>
      
      <div class="sidebar-section">SENSORES</div>
      <div class="menu-item" onclick="triggerAction('/api/geo_seismic')">🌋 MONITOR SÍSMICO</div>
      <div class="menu-item" onclick="triggerAction('/api/orbital')">🛰️ TELEMETRIA ISS</div>
    </div>
  </aside>

  <main>
    <header>
      <div style="font-weight:700; letter-spacing:1px;">GHOST PROTOCOL <span style="color:var(--text-muted); font-weight:400; font-size:12px;">v5.0</span></div>
      <div class="status-group">
        <div id="status-led"></div>
        <div id="status-text">OFFLINE</div>
      </div>
    </header>

    <div id="chat-scroll">
      <div id="chat-container"></div>
    </div>

    <footer id="input-wrapper">
      <div id="attachments-bar"></div>
      <div id="input-row">
        <button id="upload-btn" onclick="document.getElementById('file-input').click()">📎</button>
        <input type="file" id="file-input" style="display:none" multiple onchange="handleFiles(this.files); this.value=''">
        <textarea id="msgBox" rows="1" placeholder="Digite sua ordem tática..." oninput="autoResize(this)" onkeydown="handleKey(event)"></textarea>
        <button id="send-btn" onclick="sendMsg()">
          <span>Enviar</span>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
        </button>
      </div>
    </footer>
  </main>

  <div id="toast" style="position:fixed; bottom:100px; left:50%; transform:translateX(-50%); background:var(--panel); border:1px solid var(--blue); padding:10px 20px; border-radius:8px; display:none; z-index:10000;"></div>

  <script>
    var ws = null;
    var isConnected = false;
    var isGenerating = false;
    var pendingAttachments = [];

    function showToast(m) {
      const t = document.getElementById('toast');
      t.textContent = m; t.style.display = 'block';
      setTimeout(() => t.style.display = 'none', 3000);
    }

    function autoResize(el) {
      el.style.height = 'auto';
      el.style.height = (el.scrollHeight > 200 ? 200 : el.scrollHeight) + 'px';
    }

    function handleKey(e) {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        if(!isGenerating) sendMsg();
      }
    }

    function connect() {
      const proto = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
      ws = new WebSocket(proto + window.location.host + '/ws');
      ws.onopen = () => { setStatus(true); showToast('SISTEMA ONLINE'); };
      ws.onmessage = (e) => {
        const data = JSON.parse(e.data);
        if (data.type === 'system') appendMsg('bot', 'SISTEMA', data.text);
        else if (data.type === 'stream') streamBot(data.text);
        else if (data.type === 'done') { hideTyping(); toggleSendButton(false); }
      };
      ws.onclose = () => { setStatus(false); toggleSendButton(false); setTimeout(connect, 3000); };
    }

    function setStatus(online) {
      isConnected = online;
      document.getElementById('status-led').style.background = online ? '#0ea5e9' : '#ef4444';
      document.getElementById('status-led').style.boxShadow = online ? '0 0 10px #0ea5e9' : '0 0 10px #ef4444';
      document.getElementById('status-text').textContent = online ? 'SISTEMA ONLINE' : 'OFFLINE';
    }

    function triggerAction(endpoint) {
      showToast('Disparando Protocolo...');
      fetch(endpoint).then(r => r.json()).then(data => {
        if(data.ok) appendMsg('bot', 'SISTEMA', data.html || data.text);
      });
    }

    function handleFiles(files) {
      if(!files.length) return;
      showToast('Enviando arquivos...');
      const fd = new FormData();
      for(let f of files) fd.append('arquivos', f);
      fetch('/api/upload_arquivos', { method: 'POST', body: fd })
        .then(r => r.json()).then(res => {
          if(res.ok) {
            res.arquivos.forEach(a => { if(!pendingAttachments.includes(a)) pendingAttachments.push(a); });
            renderAttachments();
            showToast('Arquivos prontos para análise');
          }
        });
    }

    function renderAttachments() {
      const bar = document.getElementById('attachments-bar');
      bar.innerHTML = '';
      pendingAttachments.forEach(name => {
        const p = document.createElement('div');
        p.className = 'attach-pill';
        p.innerHTML = `📎 ${name} <span class="rm-btn" onclick="removeAttachment('${name}')">✕</span>`;
        bar.appendChild(p);
      });
    }

    function removeAttachment(n) {
      pendingAttachments = pendingAttachments.filter(a => a !== n);
      renderAttachments();
    }

    function sendMsg() {
      const box = document.getElementById('msgBox');
      const msg = box.value.trim();
      if(!msg && !pendingAttachments.length) return;
      
      let finalCmd = '';
      let visualHtml = '';
      
      if(pendingAttachments.length > 0) {
        finalCmd = pendingAttachments.map(f => '/ler ' + f).join(' ') + ' ' + msg;
        visualHtml = '<div style="display:flex;gap:5px;margin-bottom:8px;">' + 
          pendingAttachments.map(f => `<span style="background:rgba(14,165,233,0.1);border:1px solid var(--blue);padding:3px 8px;border-radius:5px;font-size:10px;">📎 ${f}</span>`).join('') + 
          '</div>';
      } else { finalCmd = msg; }

      appendMsg('user', 'TEDDY', visualHtml + msg.replace(/\n/g, '<br>'));
      ws.send(finalCmd);
      box.value = ''; box.style.height = 'auto';
      pendingAttachments = []; renderAttachments();
      showTyping();
    }

    function appendMsg(role, author, text) {
      const container = document.getElementById('chat-container');
      const div = document.createElement('div');
      div.className = `msg-row ${role}`;
      div.innerHTML = `<div class="msg-author">${author}</div><div class="msg-content">${text}</div>`;
      container.appendChild(div);
      const scroller = document.getElementById('chat-scroll');
      scroller.scrollTop = scroller.scrollHeight;
      if(role === 'user') toggleSendButton(true);
    }

    let lastContentEl = null;
    function showTyping() {
      const container = document.getElementById('chat-container');
      const div = document.createElement('div');
      div.id = 'typing-row'; div.className = 'msg-row bot';
      div.innerHTML = `<div class="msg-author">R2</div><div class="msg-content"><span id="stream-target"></span><span class="cursor">|</span></div>`;
      container.appendChild(div);
      lastContentEl = document.getElementById('stream-target');
      const scroller = document.getElementById('chat-scroll');
      scroller.scrollTop = scroller.scrollHeight;
    }

    function streamBot(t) {
      if(lastContentEl) lastContentEl.innerHTML += t.replace(/\n/g, '<br>');
      const scroller = document.getElementById('chat-scroll');
      scroller.scrollTop = scroller.scrollHeight;
    }

    function hideTyping() {
      const row = document.getElementById('typing-row');
      if(row) { row.id = ''; const c = row.querySelector('.cursor'); if(c) c.remove(); }
      lastContentEl = null;
    }

    function toggleSendButton(gen) {
      isGenerating = gen;
      const btn = document.getElementById('send-btn');
      btn.className = gen ? 'stop-mode' : '';
      btn.onclick = gen ? stopGen : sendMsg;
      btn.querySelector('span').textContent = gen ? 'Parar' : 'Enviar';
    }

    function stopGen() {
      fetch('/api/stop', {method:'POST'});
      showToast('Abortando missão...');
    }

    window.addEventListener('dragover', (e) => { e.preventDefault(); document.body.classList.add('drag-over'); });
    window.addEventListener('dragleave', () => document.body.classList.remove('drag-over'));
    window.addEventListener('drop', (e) => { e.preventDefault(); document.body.classList.remove('drag-over'); handleFiles(e.dataTransfer.files); });

    connect();
  </script>
</body>
</html>
"""
'''

    # Identifica o início e o fim da variável HTML_TEMPLATE no main2.py
    try:
        start_marker = 'HTML_TEMPLATE = """'
        end_marker = '"""'
        
        start_idx = content.find(start_marker)
        if start_idx == -1:
            print("❌ Não foi possível localizar o início do HTML_TEMPLATE.")
            return

        # Encontra o fim do bloco de aspas triplas após o início
        end_idx = content.find(end_marker, start_idx + len(start_marker))
        if end_idx == -1:
            print("❌ Não foi possível localizar o fechamento do HTML_TEMPLATE.")
            return
            
        # Adiciona o comprimento das aspas triplas de fechamento
        end_idx += len(end_marker)

        # Monta o novo conteúdo do arquivo
        final_content = content[:start_idx] + new_template.strip() + content[end_idx:]

        with open(FILE_PATH, "w", encoding="utf-8") as f:
            f.write(final_content)
        
        print("✅ RECONSTRUÇÃO NUCLEAR CONCLUÍDA!")
        print("🚀 A interface foi resetada para um estado estável com todos os recursos.")
        print("🔄 Por favor, feche o R2 e abra novamente.")

    except Exception as e:
        print(f"❌ Falha crítica durante a reconstrução: {e}")

if __name__ == "__main__":
    apply_nuclear_fix()