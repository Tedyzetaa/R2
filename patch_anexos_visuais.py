# filename: patch_anexos_visuais_fix.py
import os
import re

FILE_PATH = "main2.py"

def apply_visual_attachments():
    print("📎 Evoluindo sistema de anexos para Pílulas Visuais Inteligentes...")

    if not os.path.exists(FILE_PATH):
        print(f"❌ {FILE_PATH} não encontrado.")
        return

    with open(FILE_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. HTML: Cria a barra de anexos logo acima da caixa de input
    if '<div id="attachments-bar"></div>' not in content:
        content = content.replace(
            '<footer id="input-wrapper">\n    <div id="input-row">',
            '<footer id="input-wrapper">\n    <div id="attachments-bar"></div>\n    <div id="input-row">'
        )

    # 2. CSS: Estiliza a barra e as pílulas dos anexos
    css_patch = """/* ATTACHMENTS BAR */
#attachments-bar {
  display: flex; gap: 8px; flex-wrap: wrap; max-width: 860px; margin: 0 auto;
}
#attachments-bar:not(:empty) { margin-bottom: 10px; }
.attach-pill {
  display: flex; align-items: center; gap: 6px;
  background: rgba(14,165,233,0.1); border: 1px solid var(--border-hi);
  padding: 5px 10px; border-radius: 8px;
  font-family: 'Share Tech Mono', monospace; font-size: 11px; color: var(--blue);
  animation: fadeUp 0.2s ease;
}
.attach-pill .rm-btn { cursor: pointer; color: var(--text-muted); font-size: 14px; line-height: 1; margin-left: 4px; }
.attach-pill .rm-btn:hover { color: var(--red); }

/* VIDEO STUDIO MODAL */"""
    if "#attachments-bar" not in content:
        content = content.replace("/* VIDEO STUDIO MODAL */", css_patch)

    # 3. JS: Variáveis Globais e Renderização Visual
    js_globals_old = "var isGenerating = false;"
    js_globals_new = """var isGenerating = false;
var pendingAttachments = [];

function renderAttachments() {
  var bar = document.getElementById('attachments-bar');
  if (!bar) return;
  bar.innerHTML = '';
  for (var i=0; i<pendingAttachments.length; i++) {
    var pill = document.createElement('div');
    pill.className = 'attach-pill';
    pill.innerHTML = '📎 ' + escHtml(pendingAttachments[i]) + ' <span class="rm-btn" onclick="removeAttachment(\\'' + pendingAttachments[i] + '\\')">✕</span>';
    bar.appendChild(pill);
  }
}
function removeAttachment(name) {
  pendingAttachments = pendingAttachments.filter(function(a) { return a !== name; });
  renderAttachments();
}"""
    if "pendingAttachments = []" not in content:
        content = content.replace(js_globals_old, js_globals_new)

    # 4. JS: Nova lógica do handleFiles (via Slicing Seguro)
    novo_handle = """function handleFiles(files) {
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
        for (var j=0; j<res.arquivos.length; j++) {
            if (pendingAttachments.indexOf(res.arquivos[j]) === -1) {
                pendingAttachments.push(res.arquivos[j]);
            }
        }
        renderAttachments();
        showToast('✅ Anexado com sucesso!');
      } else { showToast('❌ Erro tático: ' + res.error); }
    }
  };
  xhr.onerror = function() { showToast('❌ Falha na conexão de rede.'); };
  xhr.send(formData);
}"""
    padrao_handle = re.compile(r"function handleFiles\(files\).*?xhr\.send\(formData\);\n\}", re.DOTALL)
    match_handle = padrao_handle.search(content)
    if match_handle:
        content = content[:match_handle.start()] + novo_handle + content[match_handle.end():]

    # 5. JS: Nova lógica de envio (via Slicing Seguro)
    novo_send = r"""function sendMsg() {
  var box = document.getElementById('msgBox'); if (!box) return;
  var msg = box.value.replace(/^\s+|\s+$/g, '');
  if (!msg && pendingAttachments.length === 0) return;
  if (!ws || ws.readyState !== 1) { showToast('Servidor offline...'); return; }
  
  var finalCmd = '';
  var visualHtml = '';
  
  if (pendingAttachments.length > 0) {
      var fileStr = pendingAttachments.map(function(f) { return '/ler ' + f; }).join(' ');
      finalCmd = fileStr + (msg ? ' ' + msg : '');
      
      visualHtml = '<div style="display:flex; gap:6px; flex-wrap:wrap; margin-bottom:8px;">';
      for(var i=0; i<pendingAttachments.length; i++) {
          visualHtml += '<span style="background:rgba(14,165,233,0.1); border:1px solid rgba(14,165,233,0.3); padding:4px 8px; border-radius:6px; font-size:10px; font-family:\'Share Tech Mono\', monospace; color:#0ea5e9;">📎 ' + escHtml(pendingAttachments[i]) + '</span>';
      }
      visualHtml += '</div>';
  } else {
      finalCmd = msg;
  }
  
  var displayMsg = visualHtml + (msg ? escHtml(msg).replace(/\n/g, '<br>') : '<i style="color:var(--text-muted);font-size:12px;">(Arquivos enviados para análise)</i>');
  
  appendMsg('user', 'TEDDY', displayMsg);
  ws.send(finalCmd);
  
  box.value = ''; box.style.height = '';
  pendingAttachments = [];
  renderAttachments();
  showTyping();
}"""
    padrao_send = re.compile(r"function sendMsg\(\) \{.*?showTyping\(\);\n\}", re.DOTALL)
    match_send = padrao_send.search(content)
    if match_send:
        content = content[:match_send.start()] + novo_send + content[match_send.end():]

    with open(FILE_PATH, "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ Mutação de Interface concluída com sucesso!")

if __name__ == "__main__":
    apply_visual_attachments()