# filename: restaurar_interface_ghost.py
import os
import re

FILE_PATH = "main2.py"

def apply_restoration():
    print("💎 [RESTAURAÇÃO]: Reativando estética original GHOST PROTOCOL...")
    
    if not os.path.exists(FILE_PATH):
        print(f"❌ {FILE_PATH} não encontrado.")
        return

    with open(FILE_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Usamos o prefixo r""" (raw string) para que o Python não tente ler as barras invertidas do JS
    ghost_ui = r'''
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
      --blue: #0ea5e9; --red: #ef4444; --text: #e2e8f0; --text-muted: #94a3b8;
      --glow: 0 0 15px rgba(14,165,233,0.3); --radius: 8px;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0; background: var(--bg); color: var(--text); font-family: 'Rajdhani', sans-serif;
      height: 100vh; display: flex; overflow: hidden;
    }
    
    /* SCANLINE EFFECT */
    body::before {
      content: ""; position: fixed; inset: 0; pointer-events: none;
      background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%), 
                  linear-gradient(90deg, rgba(255, 0, 0, 0.06), rgba(0, 255, 0, 0.02), rgba(0, 0, 255, 0.06));
      background-size: 100% 4px, 3px 100%; z-index: 9999; opacity: 0.12;
    }

    /* SIDEBAR */
    #sidebar {
      width: 300px; background: var(--panel); border-right: 1px solid var(--border);
      display: flex; flex-direction: column; z-index: 1001; transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .sidebar-header { padding: 25px; border-bottom: 1px solid var(--border); font-weight: 700; color: var(--blue); letter-spacing: 3px; font-size: 18px; text-shadow: var(--glow); }
    .sidebar-content { flex: 1; overflow-y: auto; padding: 15px; }
    .sidebar-section { padding: 15px 10px 5px; font-size: 11px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 2px; border-bottom: 1px solid var(--border); margin-bottom: 10px; }
    .menu-item {
      padding: 14px; margin: 6px 0; border-radius: var(--radius); cursor: pointer;
      font-family: 'Share Tech Mono', monospace; font-size: 13px; border: 1px solid transparent; transition: all 0.2s;
    }
    .menu-item:hover { background: rgba(14,165,233,0.08); border-color: var(--border); color: var(--blue); transform: translateX(5px); }

    /* MAIN AREA */
    main { flex: 1; display: flex; flex-direction: column; position: relative; }
    header {
      padding: 15px 30px; border-bottom: 1px solid var(--border); display: flex; 
      justify-content: space-between; align-items: center; background: rgba(2, 11, 20, 0.6); backdrop-filter: blur(10px);
    }
    .status-group { display: flex; align-items: center; gap: 12px; font-family: 'Share Tech Mono', monospace; font-size: 12px; }
    #status-led { width: 10px; height: 10px; border-radius: 50%; box-shadow: 0 0 10px currentColor; }

    /* CHAT */
    #chat-scroll { flex: 1; overflow-y: auto; padding: 30px; scroll-behavior: smooth; }
    #chat-container { max-width: 900px; margin: 0 auto; }
    .msg-row { margin-bottom: 30px; animation: slideUp 0.3s ease-out; }
    .msg-author { font-family: 'Share Tech Mono', monospace; font-size: 11px; color: var(--blue); margin-bottom: 8px; opacity: 0.8; }
    .msg-content { 
      background: rgba(14,165,233,0.02); border: 1px solid var(--border); 
      padding: 18px; border-radius: var(--radius); line-height: 1.7; font-size: 15px;
    }
    .user .msg-content { border-color: rgba(14, 165, 233, 0.4); background: rgba(14,165,233,0.06); }

    /* INPUT TERMINAL */
    #input-wrapper { padding: 25px; background: var(--panel); border-top: 1px solid var(--border); }
    #attachments-bar { display: flex; gap: 10px; flex-wrap: wrap; max-width: 900px; margin: 0 auto; }
    #attachments-bar:not(:empty) { margin-bottom: 15px; }
    .attach-pill {
      display: flex; align-items: center; gap: 8px; background: rgba(14,165,233,0.1);
      border: 1px solid var(--blue); padding: 8px 14px; border-radius: 6px;
      font-family: 'Share Tech Mono', monospace; font-size: 11px; color: var(--blue);
    }
    .rm-btn { cursor: pointer; color: var(--text-muted); font-weight: bold; padding: 0 4px; }
    .rm-btn:hover { color: var(--red); }
    
    #input-row { max-width: 900px; margin: 0 auto; display: flex; gap: 15px; align-items: flex-end; }
    textarea {
      flex: 1; background: var(--bg); border: 1px solid var(--border);
      border-radius: var(--radius); color: var(--text); padding: 15px;
      font-family: 'Rajdhani', sans-serif; font-size: 16px; resize: none; min-height: 54px;
    }
    textarea:focus { outline: none; border-color: var(--blue); box-shadow: var(--glow); }
    
    .btn-action {
      background: var(--blue); border: none; border-radius: var(--radius);
      color: white; height: 54px; padding: 0 25px; cursor: pointer; font-weight: 700;
      display: flex; align-items: center; gap: 10px; transition: 0.3s;
    }
    #upload-btn { background: var(--panel); border: 1px solid var(--border); color: var(--blue); width: 54px; padding: 0; justify-content: center; }
    #send-btn.stop-mode { background: var(--red); box-shadow: 0 0 20px rgba(239, 68, 68, 0.4); }

    /* OVERLAY DRAG DROP */
    body.drag-over::after {
      content: 'SOLTE ARQUIVOS PARA PROCESSAMENTO'; position: fixed; inset: 0;
      background: rgba(2, 11, 20, 0.95); backdrop-filter: blur(10px); z-index: 9999;
      display: flex; align-items: center; justify-content: center; font-size: 20px;
      letter-spacing: 5px; color: var(--blue); border: 2px dashed var(--blue);
    }

    @keyframes slideUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
    @keyframes blink { 50% { opacity: 0; } }
  </style>
</head>
<body>
  <aside id="sidebar">
    <div class="sidebar-header">R2 · COMMANDER</div>
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
      <div style="font-weight:700; letter-spacing:2px; font-family: 'Share Tech Mono'; color: var(--blue);">GHOST_PROTOCOL_V5.0</div>
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
        <button class="btn-action" id="upload-btn" onclick="document.getElementById('file-input').click()">📎</button>
        <input type="file" id="file-input" style="display:none" multiple onchange="handleFiles(this.files); this.value=''">
        <textarea id="msgBox" rows="1" placeholder="Aguardando ordens..." oninput="autoResize(this)" onkeydown="handleKey(event)"></textarea>
        <button class="btn-action" id="send-btn" onclick="sendMsg()">
          <span>Enviar</span>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
        </button>
      </div>
    </footer>
  </main>

  <div id="toast" style="position:fixed; bottom:120px; left:50%; transform:translateX(-50%); background:var(--panel); border:1px solid var(--blue); padding:12px 25px; border-radius:var(--radius); display:none; z-index:10000; font-family:'Share Tech Mono'; font-size:12px; box-shadow: var(--glow);"></div>

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
      el.style.height = (el.scrollHeight > 250 ? 250 : el.scrollHeight) + 'px';
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
      ws.onopen = () => { setStatus(true); showToast('UPLINK ESTABELECIDO'); };
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
      const led = document.getElementById('status-led');
      led.style.background = online ? '#0ea5e9' : '#ef4444';
      led.style.color = online ? '#0ea5e9' : '#ef4444';
      document.getElementById('status-text').textContent = online ? 'SISTEMA ONLINE' : 'OFFLINE';
    }

    function triggerAction(endpoint) {
      showToast('Acessando Módulo...');
      fetch(endpoint).then(r => r.json()).then(data => {
        if(data.ok) appendMsg('bot', 'SISTEMA', data.html || data.text);
      });
    }

    function handleFiles(files) {
      if(!files.length) return;
      showToast('Transmitindo arquivos...');
      const fd = new FormData();
      for(let f of files) fd.append('arquivos', f);
      fetch('/api/upload_arquivos', { method: 'POST', body: fd })
        .then(r => r.json()).then(res => {
          if(res.ok) {
            res.arquivos.forEach(a => { if(!pendingAttachments.includes(a)) pendingAttachments.push(a); });
            renderAttachments();
            showToast('Arquivos integrados à memória flash');
          }
        });
    }

    function renderAttachments() {
      const bar = document.getElementById('attachments-bar');
      bar.innerHTML = '';
      pendingAttachments.forEach(name => {
        const p = document.createElement('div');
        p.className = 'attach-pill';
        p.innerHTML = '📎 ' + name + ' <span class="rm-btn" onclick="removeAttachment(\'' + name + '\')">✕</span>';
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
        visualHtml = '<div style="display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap;">' + 
          pendingAttachments.map(f => '<span style="background:rgba(14,165,233,0.1);border:1px solid var(--blue);padding:4px 10px;border-radius:6px;font-size:11px;font-family:\'Share Tech Mono\';">📎 ' + f + '</span>').join('') + 
          '</div>';
      } else { finalCmd = msg; }

      appendMsg('user', 'TEDDY', visualHtml + msg.split('\n').join('<br>'));
      ws.send(finalCmd);
      box.value = ''; box.style.height = 'auto';
      pendingAttachments = []; renderAttachments();
      showTyping();
    }

    function appendMsg(role, author, text) {
      const container = document.getElementById('chat-container');
      const div = document.createElement('div');
      div.className = 'msg-row ' + role;
      div.innerHTML = '<div class="msg-author">' + author + '</div><div class="msg-content">' + text + '</div>';
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
      div.innerHTML = '<div class="msg-author">R2</div><div class="msg-content"><span id="stream-target"></span><span style="border-right:2px solid var(--blue);animation:blink 0.7s infinite;"></span></div>';
      container.appendChild(div);
      lastContentEl = document.getElementById('stream-target');
      const scroller = document.getElementById('chat-scroll');
      scroller.scrollTop = scroller.scrollHeight;
    }

    function streamBot(t) {
      if(lastContentEl) lastContentEl.innerHTML += t.split('\n').join('<br>');
      const scroller = document.getElementById('chat-scroll');
      scroller.scrollTop = scroller.scrollHeight;
    }

    function hideTyping() {
      const row = document.getElementById('typing-row');
      if(row) row.id = '';
      lastContentEl = null;
    }

    function toggleSendButton(gen) {
      isGenerating = gen;
      const btn = document.getElementById('send-btn');
      btn.className = gen ? 'btn-action stop-mode' : 'btn-action';
      btn.onclick = gen ? stopGen : sendMsg;
      btn.querySelector('span').textContent = gen ? 'Parar' : 'Enviar';
      btn.querySelector('svg').innerHTML = gen ? '<rect x="6" y="6" width="12" height="12" rx="2"></rect>' : '<line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>';
    }

    function stopGen() {
      fetch('/api/stop', {method:'POST'});
      showToast('PROTOCOL_ABORTED');
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

    # Localização do bloco HTML no main2.py
    pattern = re.compile(r'HTML_TEMPLATE\s*=\s*""".*?"""', re.DOTALL)
    if not pattern.search(content):
        # Tenta com aspas simples caso o formato tenha mudado
        pattern = re.compile(r"HTML_TEMPLATE\s*=\s*'''.*?'''", re.DOTALL)

    if not pattern.search(content):
        print("❌ Erro: Não foi possível localizar o bloco HTML_TEMPLATE no seu arquivo main2.py.")
        return

    # Realiza a substituição
    new_content = pattern.sub(ghost_ui.strip(), content)

    with open(FILE_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)

    print("✅ [SUCESSO]: Interface Ghost Protocol restaurada!")
    print("🚀 JavaScript blindado contra erros de escape.")
    print("🔄 Reinicie o R2 (main2.py) para validar a operação.")

if __name__ == "__main__":
    apply_restoration()