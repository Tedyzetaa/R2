# filename: super_patch_frontend.py
import os
import re

FILE_PATH = "main2.py"

def rebuild_frontend():
    print("🛠️ Iniciando Reconstrução Total do Córtex Visual...")
    
    if not os.path.exists(FILE_PATH):
        print(f"❌ {FILE_PATH} não encontrado.")
        return

    with open(FILE_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # O Novo motor JavaScript Completo e Corrigido (V2.2)
    novo_javascript = """
<script>
var ws          = null;
var isConnected = false;
var toastTimer  = null;
var isGenerating = false;
var pendingAttachments = [];

/* UTILITÁRIOS */
function escHtml(t) {
  if (!t) return '';
  return t.toString().replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function showToast(m) {
  var t = document.getElementById('toast');
  if (!t) return;
  t.textContent = m;
  t.className = 'show';
  clearTimeout(toastTimer);
  toastTimer = setTimeout(function(){ t.className = ''; }, 3000);
}

function autoResize(el) {
  el.style.height = 'auto';
  var newH = el.scrollHeight;
  if (newH > 300) newH = 300;
  el.style.height = newH + 'px';
}

/* SIDEBAR */
function toggleSidebar() {
  var sb = document.getElementById('sidebar');
  var ov = document.getElementById('overlay');
  if (!sb) return;
  if (sb.className.indexOf('open') > -1) { closeSidebar(); }
  else { sb.className = 'open'; if (ov) ov.className = 'active'; }
}

function closeSidebar() {
  var sb = document.getElementById('sidebar');
  var ov = document.getElementById('overlay');
  if (sb) sb.removeAttribute('class');
  if (ov) ov.removeAttribute('class');
}

/* STUDIO */
function openStudio() {
  var el = document.getElementById('studio-backdrop');
  if (el) el.className = 'open';
  closeSidebar();
}

function closeStudio() {
  var el = document.getElementById('studio-backdrop');
  if (el) el.removeAttribute('class');
}

function closeStudioOnBack(e) {
  if (e.target === document.getElementById('studio-backdrop')) closeStudio();
}

/* ANEXOS */
function renderAttachments() {
  var bar = document.getElementById('attachments-bar');
  if (!bar) return;
  bar.innerHTML = '';
  for (var i=0; i<pendingAttachments.length; i++) {
    var pill = document.createElement('div');
    pill.className = 'attach-pill';
    pill.innerHTML = '📎 ' + escHtml(pendingAttachments[i]) +
      ' <span class="rm-btn" onclick="removeAttachment(\\'' + pendingAttachments[i] + '\\')">✕</span>';
    bar.appendChild(pill);
  }
}

function removeAttachment(name) {
  pendingAttachments = pendingAttachments.filter(function(a){ return a !== name; });
  renderAttachments();
}

function handleFiles(files) {
  if (!files || !files.length) return;
  showToast('Transmitindo ' + files.length + ' arquivo(s)...');
  var formData = new FormData();
  for (var i=0; i<files.length; i++) { formData.append('arquivos', files[i]); }
  var xhr = new XMLHttpRequest();
  xhr.open('POST', '/api/upload_arquivos', true);
  xhr.onload = function() {
    if (xhr.status === 200) {
      var res = JSON.parse(xhr.responseText);
      if (res.ok) {
        res.arquivos.forEach(function(a){
          if (pendingAttachments.indexOf(a) === -1) pendingAttachments.push(a);
        });
        renderAttachments();
        showToast('✅ Anexado com sucesso!');
      } else { showToast('❌ Erro: ' + res.error); }
    }
  };
  xhr.send(formData);
}

/* WEBSOCKET */
function connect() {
  var proto = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
  ws = new WebSocket(proto + window.location.host + '/ws');
  ws.onopen = function() { isConnected = true; setStatus(true); showToast('SISTEMA ONLINE'); };
  ws.onmessage = function(e) {
    var data = JSON.parse(e.data);
    if (data.type === 'system') { appendMsg('bot', 'SISTEMA', data.text); }
    else if (data.type === 'image') { appendMsg('bot', 'IMAGEM', '<img src="'+data.url+'" style="max-width:100%;border-radius:8px;"><br>'+data.text); }
    else if (data.type === 'stream') { streamBot(data.text); }
    else if (data.type === 'done') { hideTyping(); toggleSendButton(false); }
  };
  ws.onclose = function() {
    isConnected = false; setStatus(false); toggleSendButton(false);
    setTimeout(connect, 3000);
  };
}

/* CHAT */
function sendMsg() {
  var box = document.getElementById('msgBox');
  var msg = box.value.trim();
  if (!msg && pendingAttachments.length === 0) return;
  if (!ws || ws.readyState !== 1) { showToast('⚠️ Sem conexão com o servidor.'); return; }

  var finalCmd = '';
  var visualHtml = '';
  if (pendingAttachments.length > 0) {
    var fileStr = pendingAttachments.map(function(f){ return '/ler ' + f; }).join(' ');
    finalCmd = fileStr + (msg ? ' ' + msg : '');
    visualHtml = '<div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:8px;">';
    pendingAttachments.forEach(function(f){
      visualHtml += '<span style="background:rgba(14,165,233,0.1);border:1px solid rgba(14,165,233,0.3);padding:4px 8px;border-radius:6px;font-size:10px;font-family:\\'Share Tech Mono\\',monospace;color:#0ea5e9;">📎 ' + escHtml(f) + '</span>';
    });
    visualHtml += '</div>';
  } else { finalCmd = msg; }

  var displayMsg = visualHtml + (msg ? escHtml(msg).replace(/\\n/g,'<br>') : '<i style="color:var(--text-muted);font-size:12px;">(Anexos para análise)</i>');
  appendMsg('user', 'TEDDY', displayMsg);
  ws.send(finalCmd);
  box.value = ''; box.style.height = '';
  pendingAttachments = [];
  renderAttachments();
  showTyping();
}

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
  var svg  = btn.querySelector('svg');
  if (generating) {
    btn.className = 'stop-mode';
    span.textContent = 'Parar';
    svg.innerHTML = '<rect x="6" y="6" width="12" height="12" rx="2" ry="2"></rect>';
    btn.onclick = stopGeneration;
  } else {
    btn.className = '';
    btn.disabled = false;
    span.textContent = 'Enviar';
    svg.innerHTML = '<line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>';
    btn.onclick = sendMsg;
  }
}

/* STATUS */
function setStatus(online) {
  var dot = document.getElementById('status-dot');   /* CORRIGIDO: era 'status-led' */
  var txt = document.getElementById('status-text');
  var pill = document.getElementById('status-pill');
  if (dot) {
    dot.className = online ? 'status-dot' : 'status-dot offline';
  }
  if (pill) pill.className = online ? 'status-pill' : 'status-pill offline';
  if (txt)  txt.textContent = online ? 'ONLINE' : 'OFFLINE';
}

/* MENSAGENS */
function appendMsg(role, author, text) {
  var chat = document.getElementById('chat');          /* CORRIGIDO: era 'chat-container' */
  var boot = document.getElementById('boot-screen');
  if (boot) boot.style.display = 'none';

  var row = document.createElement('div');
  row.className = 'msg ' + (role === 'user' ? 'user' : 'bot');
  row.innerHTML =
    '<div class="msg-avatar">' + (role === 'user' ? 'TY' : 'R2') + '</div>' +
    '<div class="msg-bubble"><div class="msg-meta">' + author + '</div><div class="msg-text">' + text + '</div></div>';
  chat.appendChild(row);
  document.getElementById('chat-wrapper').scrollTop = 999999;
  if (role === 'user') toggleSendButton(true);
}

var lastBotContent = null;
function showTyping() {
  var chat = document.getElementById('chat');          /* CORRIGIDO */
  var row = document.createElement('div');
  row.id = 'typing-row';
  row.className = 'msg bot';
  row.innerHTML = '<div class="msg-avatar">R2</div><div class="msg-bubble"><div class="msg-meta">R2</div><div class="msg-text" id="stream-content"><span class="cursor">▋</span></div></div>';
  chat.appendChild(row);
  document.getElementById('chat-wrapper').scrollTop = 999999;
  lastBotContent = document.getElementById('stream-content');
}

function streamBot(t) {
  if (!lastBotContent) return;
  var cursor = lastBotContent.querySelector('.cursor');
  var span = document.createElement('span');
  span.innerHTML = t.replace(/\\n/g, '<br>');
  lastBotContent.insertBefore(span, cursor);
  document.getElementById('chat-wrapper').scrollTop = 999999;  /* CORRIGIDO: era 'chat-scroll' */
}

function hideTyping() {
  var tr = document.getElementById('typing-row');
  if (tr) { tr.removeAttribute('id'); var c = tr.querySelector('.cursor'); if(c) c.remove(); }
  lastBotContent = null;
}

function handleKey(e) {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); if(!isGenerating) sendMsg(); }
}

function quickPrompt(txt) {
  var box = document.getElementById('msgBox');
  if (box) { box.value = txt; box.focus(); }
}

function execCmd(cmd, feedback) {
  if (!ws || ws.readyState !== 1) { showToast('⚠️ Offline'); return; }
  if (feedback) showToast(feedback);
  ws.send(cmd);
  showTyping();
  closeSidebar();
}

function setupDragAndDrop() {
  var ub = document.getElementById('upload-btn');
  var fi = document.getElementById('file-input');
  if (ub && fi) {
    ub.onclick = function(){ fi.click(); };
    fi.onchange = function(e){ handleFiles(e.target.files); fi.value = ''; };
  }
  window.addEventListener('dragover', function(e){ e.preventDefault(); });
  window.addEventListener('drop', function(e){ e.preventDefault(); handleFiles(e.dataTransfer.files); });
}

(function init() {
  connect();
  setupDragAndDrop();

  /* CORRIGIDO: conecta o botão de menu ao toggleSidebar */
  var menuBtn = document.getElementById('menu-btn');
  if (menuBtn) menuBtn.onclick = toggleSidebar;

  /* CORRIGIDO: conecta o botão fechar sidebar */
  var closeBtn = document.querySelector('.sidebar-close');
  if (closeBtn) closeBtn.onclick = closeSidebar;

  /* Overlay fecha sidebar ao clicar fora */
  var ov = document.getElementById('overlay');
  if (ov) ov.onclick = closeSidebar;

  /* Botão enviar */
  var sb = document.getElementById('send-btn');
  if (sb) sb.onclick = sendMsg;

  var mb = document.getElementById('msgBox');
  if(mb) mb.addEventListener('input', function(){ autoResize(this); });
})();
</script>
"""

    # Substituição agressiva: remove tudo entre as tags <script> e </script> e coloca o novo
    padrao_script = re.compile(r"<script>.*?</script>", re.DOTALL)
    
    if not padrao_script.search(content):
        print("⚠️ Bloco <script> original não encontrado.")
        return

    novo_conteudo = padrao_script.sub(novo_javascript, content)

    with open(FILE_PATH, "w", encoding="utf-8") as f:
        f.write(novo_conteudo)

    print("✅ RECONSTRUÇÃO COMPLETA! O frontend foi restaurado ao estado nominal.")
    print("🔄 Reinicie o servidor e faça o Hard Refresh (Ctrl+F5).")

if __name__ == "__main__":
    rebuild_frontend()