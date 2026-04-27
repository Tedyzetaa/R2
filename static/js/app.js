/* filename: static/js/app.js */
/* ================================================================
   R2 Tactical OS - Ghost Protocol v5.1
   JS Engine - ES5 puro (compativel com lockdown-install.js)
   SEM: let, const, arrow functions (=>), fetch, classList.toggle
   + MODO BATALHA (voz hands-free)
   + PAINEL DE CONFIGURAÇÕES (voz e driver)
   + MENSAGEM DE ÁUDIO (gravação e envio via WebSocket)

   CORREÇÕES v5.1:
     BUG #4  → MediaRecorder gravava audio/webm mas Blob era criado
               com type 'audio/wav', enganando o backend.
     BUG #3  → voz padrão corrigida para "Thalita"
     MELHORIA → toggleSidebar simplificado (condição redundante removida)
     MELHORIA → closeSidebar simplificado (removeAttribute redundante removido)
   ================================================================ */

var ws          = null;
var isConnected = false;
var toastTimer  = null;
var isGenerating = false;

// ========== MODO BATALHA ==========
var battleModeAtivo = false;
var reconhecimentoDeVoz = null;
var soundwaveBars = [];
var audioAtual = null;

// ========== CONFIGURAÇÕES ==========
// BUG FIX #3: voz padrão corrigida de "Antonio" para "Thalita" conforme especificação do projeto
var configVoice = "Thalita";
var configDriver = "Padrão";

// ========== GRAVAÇÃO DE ÁUDIO (MODO SAFE) ==========
var mediaRecorder = null;
var audioChunks = [];
var isRecording = false;

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
    } else if (data.type === 'audio') {
      // Tocar áudio de resposta da IA (tanto no Modo Batalha quanto no Modo Safe)
      if (data.url) {
        if (audioAtual) {
          audioAtual.pause();
          audioAtual = null;
        }
        var audioEl = new Audio(data.url);
        audioAtual = audioEl;
        if (battleModeAtivo) {
          setSoundwaveSpeaking(true);
          audioEl.onended = function() {
            setSoundwaveSpeaking(false);
            audioAtual = null;
          };
        } else {
          audioEl.onended = function() { audioAtual = null; };
        }
        audioEl.play().catch(function(e) { console.warn('Audio play error:', e); });
      }
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

/* ========== ENVIO DE MENSAGEM COM CONFIGURAÇÕES ========== */
function enviarComando(texto) {
  if (!ws || ws.readyState !== 1) {
    showToast('Servidor offline. Aguarde reconexao...');
    return false;
  }
  var payload = {
    type: "command",
    text: texto,
    voice: configVoice,
    driver: configDriver
  };
  ws.send(JSON.stringify(payload));
  return true;
}

function sendMsg() {
  var box = document.getElementById('msgBox'); if (!box) return;
  var msg = box.value.replace(/^\s+|\s+$/g, '');
  if (!msg) return;
  appendMsg('user', 'TEDDY', escHtml(msg));
  if (enviarComando(msg)) {
    box.value = '';
    box.style.height = '';
    showTyping();
  }
}

function execCmd(cmd, label) {
  if (!ws || ws.readyState !== 1) { showToast('Servidor offline.'); return; }
  closeSidebar();
  appendMsg('user', 'TEDDY', escHtml(label));
  if (enviarComando(cmd)) {
    showTyping();
  }
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
  // MELHORIA: condição simplificada — era duplicada (indexOf e getAttribute faziam a mesma coisa)
  if (sb.className.indexOf('open') > -1) {
    closeSidebar();
  } else {
    sb.className = 'open';
    if (ov) ov.className = 'active';
  }
}

function closeSidebar() {
  var sb = document.getElementById('sidebar');
  var ov = document.getElementById('overlay');
  // MELHORIA: removeAttribute era redundante logo após className = '' (ambos limpam o atributo)
  if (sb) sb.className = '';
  if (ov) ov.className = '';
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
  if (el) el.className = '';
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
      var res;
      try { res = JSON.parse(xhr.responseText); } catch(e) { showToast('❌ Erro ao processar resposta.'); return; }
      if (res.ok) {
        var box = document.getElementById('msgBox');
        var cmds = res.arquivos.map(function(a) { return '/ler ' + a; }).join(' ');
        box.value = (box.value ? box.value + ' ' : '') + cmds + ' ';
        autoResize(box);
        box.focus();
        showToast('✅ Arquivos na base! Digite sua ordem.');
      } else { showToast('❌ Erro tático: ' + (res.error || 'desconhecido')); }
    } else {
      showToast('❌ Servidor retornou erro ' + xhr.status);
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

/* ========== GRAVAÇÃO DE ÁUDIO (MODO SAFE) ========== */
function toggleMicRecording() {
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    showToast('Seu navegador não suporta gravação de áudio.');
    return;
  }
  
  if (isRecording) {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
      mediaRecorder.stop();
    }
    isRecording = false;
    var micBtn = document.getElementById('mic-msg-btn');
    if (micBtn) micBtn.className = micBtn.className.replace(' recording', '').replace('recording', '').trim();
    showToast('🛑 Gravação finalizada. Enviando áudio...');
  } else {
    navigator.mediaDevices.getUserMedia({ audio: true })
      .then(function(stream) {
        // BUG FIX #4: O MediaRecorder grava no formato nativo do navegador (WebM/OGG no Chrome,
        // OGG no Firefox). Criar o Blob com type 'audio/wav' NÃO converte o áudio — apenas
        // define um MIME incorreto. O backend recebia um arquivo WebM rotulado como WAV,
        // causando falhas silenciosas no Whisper.
        //
        // CORREÇÃO: Detectar o mimeType suportado e criar o Blob com o tipo correto.
        // O backend (main2.py) agora converte para WAV com ffmpeg antes de transcrever.
        var mimeType = '';
        if (typeof MediaRecorder !== 'undefined') {
          if (MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
            mimeType = 'audio/webm;codecs=opus';
          } else if (MediaRecorder.isTypeSupported('audio/webm')) {
            mimeType = 'audio/webm';
          } else if (MediaRecorder.isTypeSupported('audio/ogg')) {
            mimeType = 'audio/ogg';
          }
        }

        var options = mimeType ? { mimeType: mimeType } : {};
        mediaRecorder = new MediaRecorder(stream, options);
        audioChunks = [];
        
        mediaRecorder.ondataavailable = function(event) {
          if (event.data.size > 0) {
            audioChunks.push(event.data);
          }
        };
        
        mediaRecorder.onstop = function() {
          stream.getTracks().forEach(function(track) { track.stop(); });

          // Criar Blob com o tipo correto detectado acima
          var blobType = mimeType || 'audio/webm';
          var audioBlob = new Blob(audioChunks, { type: blobType });
          var reader = new FileReader();
          reader.onloadend = function() {
            var base64Audio = reader.result.split(',')[1];
            if (ws && ws.readyState === 1) {
              ws.send(JSON.stringify({
                type: "audio_input",
                data: base64Audio,
                voice: configVoice
              }));
              appendMsg('sys', 'SYS', '🎙️ Áudio enviado. Aguarde transcrição...');
              showTyping();
            } else {
              showToast('Servidor offline. Não foi possível enviar o áudio.');
            }
          };
          reader.readAsDataURL(audioBlob);
        };
        
        mediaRecorder.start();
        isRecording = true;
        var micBtn2 = document.getElementById('mic-msg-btn');
        if (micBtn2) micBtn2.className = (micBtn2.className + ' recording').trim();
        showToast('🎤 Gravando... Clique novamente para parar.');
      })
      .catch(function(err) {
        console.error('Erro ao acessar microfone:', err);
        showToast('❌ Erro ao acessar microfone. Verifique as permissões.');
      });
  }
}

/* ========== MODO BATALHA ========== */
function criarBarrasSom() {
  var container = document.getElementById('soundwave-container');
  if (!container) return;
  container.innerHTML = '';
  soundwaveBars = [];
  for (var i = 0; i < 24; i++) {
    var bar = document.createElement('div');
    bar.className = 'soundwave-bar';
    var alturaBase = 12 + Math.random() * 40;
    bar.style.height = alturaBase + 'px';
    bar.style.animationDelay = (i * 0.05) + 's';
    container.appendChild(bar);
    soundwaveBars.push(bar);
  }
  setInterval(function() {
    if (!battleModeAtivo) return;
    for (var j = 0; j < soundwaveBars.length; j++) {
      var bar = soundwaveBars[j];
      if (!bar.classList || bar.classList.contains('speaking')) continue;
      var novaAltura = 12 + Math.sin(Date.now() * 0.008 + j) * 30 + Math.random() * 10;
      bar.style.height = Math.max(8, Math.min(90, novaAltura)) + 'px';
    }
  }, 80);
}

function setSoundwaveSpeaking(falando) {
  if (!soundwaveBars.length) return;
  for (var i = 0; i < soundwaveBars.length; i++) {
    var bar = soundwaveBars[i];
    if (falando) {
      bar.classList.add('speaking');
    } else {
      bar.classList.remove('speaking');
      bar.style.height = (12 + Math.sin(Date.now() * 0.008 + i) * 30 + Math.random() * 10) + 'px';
    }
  }
}

function ativarFeedbackVoz() {
  for (var i = 0; i < soundwaveBars.length; i++) {
    var bar = soundwaveBars[i];
    bar.classList.add('activated');
    setTimeout(function(b) { 
      if (b) b.classList.remove('activated');
    }, 200, bar);
  }
}

function iniciarEscuta() {
  if (!window.SpeechRecognition && !window.webkitSpeechRecognition) {
    showToast('Seu navegador não suporta reconhecimento de voz.');
    return;
  }
  var SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  reconhecimentoDeVoz = new SpeechRecognition();
  reconhecimentoDeVoz.continuous = true;
  reconhecimentoDeVoz.interimResults = false;
  reconhecimentoDeVoz.lang = 'pt-BR';
  
  reconhecimentoDeVoz.onresult = function(event) {
    var last = event.results.length - 1;
    var fala = event.results[last][0].transcript;
    var texto = fala.toLowerCase().trim();
    console.log('[VOZ] Capturado:', texto);
    
    if (texto.indexOf('hey r2') !== -1 || texto.indexOf('r2') !== -1) {
      ativarFeedbackVoz();
      // Remove a wake word e envia apenas o comando restante
      var comando = texto.replace(/hey\s+r2\s*/i, '').replace(/\br2\b\s*/i, '').trim();
      if (comando.length > 0) {
        if (enviarComando(comando)) {
          showToast('🎤 Enviado: ' + comando);
        }
      } else {
        showToast('🎤 Palavra de ativação detectada, aguardando comando...');
      }
    }
  };
  
  reconhecimentoDeVoz.onerror = function(event) {
    console.warn('[VOZ] Erro:', event.error);
    if (battleModeAtivo) {
      setTimeout(function() {
        if (battleModeAtivo && reconhecimentoDeVoz) {
          try { reconhecimentoDeVoz.start(); } catch(e) {}
        }
      }, 1000);
    }
  };
  
  reconhecimentoDeVoz.onend = function() {
    console.log('[VOZ] Reconhecimento encerrado');
    if (battleModeAtivo) {
      setTimeout(function() {
        if (battleModeAtivo && reconhecimentoDeVoz) {
          try { reconhecimentoDeVoz.start(); } catch(e) { console.warn(e); }
        }
      }, 300);
    }
  };
  
  try {
    reconhecimentoDeVoz.start();
    showToast('🎤 Modo Batalha ativado. Diga "Hey R2" ou "R2"...');
  } catch(e) {
    console.error('Erro ao iniciar reconhecimento:', e);
    showToast('Erro ao acessar microfone. Verifique as permissões.');
  }
}

function pararEscuta() {
  if (reconhecimentoDeVoz) {
    try { reconhecimentoDeVoz.stop(); } catch(e) {}
    reconhecimentoDeVoz = null;
  }
}

function toggleModoBatalha() {
  var telaBatalha = document.getElementById('battle-mode-screen');
  if (!telaBatalha) return;
  
  if (battleModeAtivo) {
    battleModeAtivo = false;
    telaBatalha.style.display = 'none';
    pararEscuta();
    if (audioAtual) {
      audioAtual.pause();
      audioAtual = null;
    }
    showToast('Modo Safe ativado. Interface de chat restaurada.');
  } else {
    battleModeAtivo = true;
    telaBatalha.style.display = 'flex';
    if (soundwaveBars.length === 0) {
      criarBarrasSom();
    }
    iniciarEscuta();
  }
}

/* ========== CONFIGURAÇÕES ========== */
function loadSettings() {
  var stored = localStorage.getItem('r2_settings');
  if (stored) {
    try {
      var settings = JSON.parse(stored);
      if (settings.voice) configVoice = settings.voice;
      if (settings.driver) configDriver = settings.driver;
    } catch(e) {}
  }
  var voiceSelect = document.getElementById('voice-select');
  var driverSelect = document.getElementById('driver-select');
  if (voiceSelect) voiceSelect.value = configVoice;
  if (driverSelect) driverSelect.value = configDriver;
}

function saveSettings() {
  var voiceSelect = document.getElementById('voice-select');
  var driverSelect = document.getElementById('driver-select');
  if (voiceSelect) configVoice = voiceSelect.value;
  if (driverSelect) configDriver = driverSelect.value;
  var settings = { voice: configVoice, driver: configDriver };
  localStorage.setItem('r2_settings', JSON.stringify(settings));
  showToast('✅ Configurações salvas! Voz: ' + configVoice);
  closeSettingsModal();
}

function openSettingsModal() {
  var modal = document.getElementById('settings-modal');
  if (modal) {
    loadSettings();
    modal.style.display = 'flex';
  }
}

function closeSettingsModal() {
  var modal = document.getElementById('settings-modal');
  if (modal) modal.style.display = 'none';
}

function initSettings() {
  var settingsBtn = document.getElementById('settings-btn');
  if (settingsBtn) {
    settingsBtn.onclick = function(e) {
      e.preventDefault();
      openSettingsModal();
    };
  }
  loadSettings();
}

/* ========== INICIALIZAÇÃO DO MICROFONE (MODO SAFE) ========== */
function initMicrophone() {
  var micBtn = document.getElementById('mic-msg-btn');
  if (micBtn) {
    micBtn.onclick = function(e) {
      e.preventDefault();
      toggleMicRecording();
    };
  }
}

/* ========== INICIALIZAÇÃO ========== */
function initBattleMode() {
  var battleBtn = document.getElementById('battle-mode-btn');
  if (battleBtn) {
    battleBtn.onclick = function(e) {
      e.preventDefault();
      toggleModoBatalha();
    };
  }
  var safeBtn = document.getElementById('safe-mode-btn');
  if (safeBtn) {
    safeBtn.onclick = function(e) {
      e.preventDefault();
      if (battleModeAtivo) toggleModoBatalha();
    };
  }
  criarBarrasSom();
}

/* ========== TRADING AUTÔNOMO ========== */
function abrirBroker() {
    notificar('Iniciando terminal de Trading Broker10...', 'ok');
    closeSidebar();
    
    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/api/broker/start', true);
    xhr.onreadystatechange = function() {
        if (xhr.readyState === 4) {
            if (xhr.status === 200) {
                var res;
                try { res = JSON.parse(xhr.responseText); } catch(e) { res = {}; }
                if (res.ok) {
                    notificar('✅ Sessão da Broker iniciada com sucesso!', 'ok');
                    // Abre automaticamente o painel Alpha para monitorar a tela
                    if (typeof alphaPanel !== 'undefined') alphaPanel.open();
                } else {
                    notificar('❌ Erro: ' + res.erro, 'err');
                }
            } else {
                notificar('❌ Falha ao iniciar terminal de trading.', 'err');
            }
        }
    };
    xhr.send();
}

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
  initBattleMode();
  initSettings();
  initMicrophone();
}());

// ========== SILO TIKTOK - MÓDULO INTEGRADO (ES5) ==========
var siloBackdrop = document.getElementById('silo-backdrop');
var picoSelecionado = null;
var arquivoSelecionado = null;

function abrirSiloTikTok() {
    if (siloBackdrop) siloBackdrop.style.display = 'flex';
    carregarFila();
    listarMunicao();
    // Configurar eventos uma única vez
    if (!window._siloEventsSet) {
        var dropZone = document.getElementById('drop-zone-silo');
        var fileInput = document.getElementById('file-input-silo');
        if (dropZone) {
            dropZone.addEventListener('dragover', function(e) { e.preventDefault(); dropZone.classList.add('drag-over'); });
            dropZone.addEventListener('dragleave', function() { dropZone.classList.remove('drag-over'); });
            dropZone.addEventListener('drop', function(e) {
                e.preventDefault();
                dropZone.classList.remove('drag-over');
                var files = e.dataTransfer.files;
                if (files.length > 0) arquivoSelecionado = files[0];
                atualizarNomeArquivo();
            });
        }
        if (fileInput) {
            fileInput.addEventListener('change', function() {
                if (this.files.length > 0) arquivoSelecionado = this.files[0];
                atualizarNomeArquivo();
            });
        }
        // Chips de horário
        var chips = document.querySelectorAll('#peak-chips-silo .chip');
        for (var i = 0; i < chips.length; i++) {
            chips[i].addEventListener('click', function() {
                var hora = this.getAttribute('data-hora');
                selecionarPico(this, hora);
            });
        }
        window._siloEventsSet = true;
    }
}

function fecharSiloTikTok() {
    if (siloBackdrop) siloBackdrop.style.display = 'none';
}

function atualizarNomeArquivo() {
    var displayDiv = document.getElementById('file-name-display');
    var nameSpan = document.getElementById('file-name-text');
    if (arquivoSelecionado) {
        displayDiv.style.display = 'block';
        nameSpan.textContent = arquivoSelecionado.name;
    } else {
        displayDiv.style.display = 'none';
        nameSpan.textContent = '';
    }
}

function selecionarPico(el, hora) {
    var chips = document.querySelectorAll('#peak-chips-silo .chip');
    for (var i = 0; i < chips.length; i++) chips[i].classList.remove('active');
    el.classList.add('active');
    picoSelecionado = hora;
    var hoje = new Date();
    var partes = hora.split(':');
    hoje.setHours(parseInt(partes[0],10), parseInt(partes[1],10), 0, 0);
    if (hoje <= new Date()) hoje.setDate(hoje.getDate() + 1);
    var pad = function(n) { return n < 10 ? '0' + n : '' + n; };
    var iso = hoje.getFullYear() + '-' + pad(hoje.getMonth()+1) + '-' + pad(hoje.getDate()) + 'T' + pad(hoje.getHours()) + ':' + pad(hoje.getMinutes());
    document.getElementById('f-agenda').value = iso;
}

function notificar(msg, tipo) {
    var toastDiv = document.getElementById('toast') || (function(){
        var d = document.createElement('div'); d.id = 'toast'; d.style.position = 'fixed'; d.style.bottom = '20px'; d.style.right = '20px'; d.style.zIndex = '10001';
        document.body.appendChild(d); return d;
    })();
    var notif = document.createElement('div');
    notif.className = 'notif-msg' + (tipo === 'err' ? ' err' : '');
    notif.textContent = msg;
    toastDiv.appendChild(notif);
    setTimeout(function() { notif.remove(); }, 3000);
}

function statusBadge(status) {
    var map = { aguardando: '◌ AGUARDANDO', disparando: '◉ DISPARANDO', publicado: '✓ PUBLICADO', erro: '✕ ERRO' };
    return map[status] || status;
}

function formatarData(iso) {
    if (!iso) return '—';
    var d = new Date(iso);
    var pad = function(n) { return n < 10 ? '0' + n : n; };
    return pad(d.getDate()) + '/' + pad(d.getMonth()+1) + ' ' + pad(d.getHours()) + ':' + pad(d.getMinutes());
}

function escapeHtml(str) {
    if (!str) return '';
    return String(str).replace(/[&<>]/g, function(m) {
        if (m === '&') return '&amp;';
        if (m === '<') return '&lt;';
        if (m === '>') return '&gt;';
        return m;
    });
}

function toggleLog(id) {
    var el = document.getElementById('log-' + id);
    if (el) el.classList.toggle('open');
}

function criarCard(item) {
    var card = document.createElement('div');
    card.className = 'video-card status-' + item.status;
    card.setAttribute('data-id', item.id);
    var nomeArquivo = item.video_path ? item.video_path.split(/[\\/]/).pop() : '—';
    var dataFormatada = formatarData(item.agendar_para);
    var logsHtml = '';
    var logs = item.log || [];
    for (var k = 0; k < logs.length; k++) logsHtml += '<div class="log-line">' + escapeHtml(logs[k]) + '</div>';
    if (!logsHtml) logsHtml = '<div class="log-line" style="opacity:0.4;">Nenhuma entrada de log.</div>';
    var podeDisparar = (item.status === 'aguardando' || item.status === 'erro');
    var btnDisabled = podeDisparar ? '' : 'disabled';
    card.innerHTML = 
        '<div class="card-top">' +
            '<div class="card-thumb"><span>▶</span></div>' +
            '<div class="card-body">' +
                '<div style="display:flex;justify-content:space-between;">' +
                    '<div class="card-titulo" title="' + escapeHtml(item.titulo) + '">' + escapeHtml(item.titulo) + '</div>' +
                    '<span class="status-pill status-' + item.status + '">' + statusBadge(item.status) + '</span>' +
                '</div>' +
                '<div class="card-desc">' + escapeHtml(item.descricao) + '</div>' +
                '<div class="card-hashtags">' + escapeHtml(item.hashtags) + '</div>' +
                '<div class="card-meta">' +
                    '<span>⏰ ' + dataFormatada + '</span>' +
                    '<span>🎬 ' + escapeHtml(nomeArquivo) + '</span>' +
                    '<span>#' + item.id + '</span>' +
                '</div>' +
            '</div>' +
        '</div>' +
        '<div class="card-actions">' +
            '<button class="btn-post-now" ' + btnDisabled + ' onclick="dispararAgora(\'' + item.id + '\', this)">⚡ POSTAR AGORA</button>' +
            '<button class="btn-log-toggle" onclick="toggleLog(\'' + item.id + '\')">LOG ▾</button>' +
            '<button class="btn-del" onclick="removerItem(\'' + item.id + '\')">✕</button>' +
        '</div>' +
        '<div class="card-log" id="log-' + item.id + '">' + logsHtml + '</div>';
    return card;
}

function carregarFila() {
    fetch('/api/tiktok/fila')
        .then(function(r) { return r.json(); })
        .then(function(data) {
            var lista = data.fila || [];
            document.getElementById('fila-count').textContent = lista.length;
            var container = document.getElementById('fila-list');
            if (!container) return;
            container.innerHTML = '';
            if (lista.length === 0) {
                container.innerHTML = '<div class="empty-state">FILA VAZIA — AGUARDANDO MISSÕES</div>';
                return;
            }
            for (var i = 0; i < lista.length; i++) {
                container.appendChild(criarCard(lista[i]));
            }
        })
        .catch(function(e) { notificar('Erro ao carregar fila: ' + e, 'err'); });
}

// ========== REFATORAÇÃO DO ARSENAL (MUNIÇÃO) ==========
function listarMunicao() {
    var container = document.getElementById('municao-list');
    if (!container) return;

    fetch('/api/tiktok/cortes')
        .then(function(r) { return r.json(); })
        .then(function(videos) {
            container.innerHTML = '';
            if (!videos || videos.length === 0) {
                container.innerHTML = '<div style="font-size: 10px; color: #2d5a7a; text-align: center;">Nenhum vídeo no arsenal.</div>';
                return;
            }

            for (var i = 0; i < videos.length; i++) {
                var v = videos[i];
                var card = document.createElement('div');
                card.className = 'municao-card';
                card.setAttribute('data-path', v.path);
                card.style.padding = '8px';
                card.style.border = '1px solid #0d2d45';
                card.style.marginBottom = '6px';
                card.style.cursor = 'pointer';
                card.style.background = '#0a1520';
                card.style.color = '#00d4ff';
                card.style.fontFamily = 'monospace';
                card.style.fontSize = '11px';
                card.innerHTML = '🎬 ' + v.name;

                // Ao clicar, seleciona o vídeo e preenche o formulário
                (function(video) {
                    card.onclick = function() {
                        // Simula um arquivo real
                        arquivoSelecionado = {
                            name: video.name,
                            path: video.path,
                            fromArsenal: true
                        };
                        var tituloInput = document.getElementById('f-titulo');
                        if (tituloInput) {
                            tituloInput.value = video.name.replace('.mp4', '').replace(/_/g, ' ');
                        }
                        atualizarNomeArquivo();
                        notificar('Vídeo selecionado: ' + video.name, 'ok');
                    };
                })(v);

                container.appendChild(card);
            }
        })
        .catch(function(e) { 
            container.innerHTML = '<div style="color:#ff2d55;">Erro ao carregar arsenal.</div>';
        });
}

function adicionarFila() {
    if (!arquivoSelecionado) { notificar('Selecione um vídeo primeiro.', 'err'); return; }
    var fd = new FormData();
    fd.append('video', arquivoSelecionado);
    fd.append('titulo', document.getElementById('f-titulo').value);
    fd.append('descricao', document.getElementById('f-desc').value);
    fd.append('hashtags', document.getElementById('f-tags').value);
    fd.append('agendar_para', document.getElementById('f-agenda').value);
    fetch('/api/tiktok/add', { method: 'POST', body: fd })
        .then(function(r) { return r.json(); })
        .then(function(data) {
            if (data.ok) {
                notificar('✓ Missão adicionada: ' + data.item.id);
                arquivoSelecionado = null;
                document.getElementById('file-input-silo').value = '';
                atualizarNomeArquivo();
                document.getElementById('f-titulo').value = '';
                document.getElementById('f-desc').value = '';
                document.getElementById('f-tags').value = '';
                document.getElementById('f-agenda').value = '';
                carregarFila();
            } else {
                notificar('Erro ao adicionar: ' + JSON.stringify(data), 'err');
            }
        })
        .catch(function(e) { notificar('Erro de rede: ' + e, 'err'); });
}

function dispararAgora(id, btn) {
    btn.disabled = true;
    btn.textContent = '⏳ DISPARANDO...';
    fetch('/api/tiktok/post_now/' + id, { method: 'POST' })
        .then(function(r) { return r.json(); })
        .then(function(data) {
            if (data.ok) {
                notificar('⚡ Disparo iniciado: ' + id);
                setTimeout(carregarFila, 1500);
                setTimeout(carregarFila, 4000);
            } else {
                notificar('Erro: ' + data.erro, 'err');
                btn.disabled = false;
                btn.textContent = '⚡ POSTAR AGORA';
            }
        })
        .catch(function(e) {
            notificar('Erro de rede: ' + e, 'err');
            btn.disabled = false;
            btn.textContent = '⚡ POSTAR AGORA';
        });
}

function removerItem(id) {
    fetch('/api/tiktok/remover/' + id, { method: 'DELETE' })
        .then(function(r) { return r.json(); })
        .then(function(data) {
            if (data.ok) { notificar('Item ' + id + ' removido.'); carregarFila(); }
        })
        .catch(function(e) { notificar('Erro: ' + e, 'err'); });
}

// Auto-refresh da fila a cada 8 segundos
setInterval(carregarFila, 8000);

// ========== PAINEL ALPHA (HUD NEURAL) ==========
var alphaPanel = (function () {
    var _isOpen = false;
    var _pollTimer = null;
    var _autopilotOn = false;

    function _el(id) { return document.getElementById(id); }
    function _log(msg, type) {
        var terminal = _el("alpha-terminal");
        if (!terminal) return;
        var line = document.createElement("div");
        line.className = "alpha-log-line alpha-log-" + (type || "info");
        var ts = new Date().toTimeString().substr(0, 8);
        line.innerHTML = "[" + ts + "] " + msg;
        terminal.appendChild(line);
        terminal.scrollTop = terminal.scrollHeight;
    }

    function _renderState(data) {
        var state = data.state || data.last_state || "IDLE";
        var conf = data.confidence || data.last_confidence || 0;
        var action = data.recommended_action || data.last_action || "--";
        var cycles = data.cycles || 0;

        var nameEl = _el("alpha-state-name");
        if (nameEl) nameEl.textContent = state;
        var actionEl = _el("alpha-state-action");
        if (actionEl) actionEl.textContent = action;
        var barEl = _el("alpha-confidence-bar");
        if (barEl) barEl.style.width = Math.round(conf * 100) + "%";
        var labelEl = _el("alpha-confidence-label");
        if (labelEl) labelEl.textContent = "Confianca: " + Math.round(conf * 100) + "%";
        var cycleEl = _el("alpha-cycle-count");
        if (cycleEl) cycleEl.textContent = cycles;
    }

    function _fetchStatus() {
        var xhr = new XMLHttpRequest();
        xhr.open("GET", "/api/alpha/status", true);
        xhr.onreadystatechange = function() {
            if (xhr.readyState === 4 && xhr.status === 200) {
                var data = JSON.parse(xhr.responseText);
                _renderState(data);
                var lastAct = _el("alpha-last-action");
                if (lastAct) lastAct.textContent = data.last_action || "--";
            }
        };
        xhr.send();
    }

    function _startPolling() {
        if (_pollTimer) return;
        _pollTimer = setInterval(_fetchStatus, 3000);
    }

    function _stopPolling() {
        if (_pollTimer) { clearInterval(_pollTimer); _pollTimer = null; }
    }

    function open() {
        var modal = _el("modal-alpha");
        if (modal) modal.style.display = "flex";
        _isOpen = true;
        _log("Painel Alpha ativado.", "sys");
        _startPolling();
        _fetchStatus();
    }

    function close() {
        var modal = _el("modal-alpha");
        if (modal) modal.style.display = "none";
        _isOpen = false;
        _stopPolling();
    }

    function analyze() {
        _log("Iniciando ciclo Neural-RPA...", "sys");
        var xhr = new XMLHttpRequest();
        xhr.open("POST", "/api/alpha/analyze", true);
        xhr.setRequestHeader("Content-Type", "application/json");
        xhr.onreadystatechange = function() {
            if (xhr.readyState === 4 && xhr.status === 200) {
                var data = JSON.parse(xhr.responseText);
                _renderState(data);
                _log("Estado: " + data.state + " | Ação: " + data.recommended_action, "state");
            } else if (xhr.readyState === 4) {
                _log("Erro no ciclo: " + xhr.status, "error");
            }
        };
        xhr.send();
    }

    function toggleAutopilot() {
        var btn = _el("btn-autopilot");
        if (!_autopilotOn) {
            _autopilotOn = true;
            if (btn) {
                btn.innerHTML = '<span class="alpha-btn-icon">▮▮</span> Parar Autopilot';
                btn.className = "alpha-btn alpha-btn-autopilot running";
            }
            _log("AUTOPILOT ATIVADO – aguardando conclusão...", "warn");
            var xhr = new XMLHttpRequest();
            xhr.open("POST", "/api/alpha/autopilot", true);
            xhr.setRequestHeader("Content-Type", "application/json");
            xhr.onreadystatechange = function() {
                if (xhr.readyState === 4) {
                    _autopilotOn = false;
                    if (btn) {
                        btn.innerHTML = '<span class="alpha-btn-icon">▶</span> Ativar Autopilot';
                        btn.className = "alpha-btn alpha-btn-autopilot";
                    }
                    if (xhr.status === 200) {
                        var data = JSON.parse(xhr.responseText);
                        _log("Autopilot finalizado. Estado: " + data.state, data.state === "PUBLISH_SUCCESS" ? "ok" : "warn");
                        _renderState(data);
                    } else {
                        _log("Falha no Autopilot", "error");
                    }
                }
            };
            xhr.send();
        } else {
            _autopilotOn = false;
            if (btn) {
                btn.innerHTML = '<span class="alpha-btn-icon">▶</span> Ativar Autopilot';
                btn.className = "alpha-btn alpha-btn-autopilot";
            }
            _log("Autopilot interrompido pelo operador.", "warn");
        }
    }

    function screenshot() {
        _log("Capturando frame...", "sys");
        var xhr = new XMLHttpRequest();
        xhr.open("GET", "/api/alpha/screenshot", true);
        xhr.onreadystatechange = function() {
            if (xhr.readyState === 4 && xhr.status === 200) {
                var data = JSON.parse(xhr.responseText);
                if (data.screenshot_b64) {
                    var wrap = _el("alpha-screenshot-wrap");
                    var img = _el("alpha-screenshot-img");
                    if (img) img.src = "data:image/png;base64," + data.screenshot_b64;
                    if (wrap) wrap.style.display = "block";
                    _log("Frame capturado.", "ok");
                }
            } else if (xhr.readyState === 4) {
                _log("Erro na captura.", "error");
            }
        };
        xhr.send();
    }

    function override(action) {
        _log("Override manual: " + action, "warn");
        var xhr = new XMLHttpRequest();
        xhr.open("POST", "/api/alpha/override", true);
        xhr.setRequestHeader("Content-Type", "application/json");
        xhr.send(JSON.stringify({ action: action }));
    }

    function clearLog() {
        var terminal = _el("alpha-terminal");
        if (terminal) terminal.innerHTML = "";
        _log("Log limpo.", "sys");
    }

    return {
        open: open, close: close, analyze: analyze,
        toggleAutopilot: toggleAutopilot, screenshot: screenshot,
        override: override, clearLog: clearLog
    };
})();

// Inicializa os eventos do painel Alpha (chamar após DOM carregado)
document.addEventListener("DOMContentLoaded", function() {
    var alphaTrigger = document.querySelector(".btn-alpha-trigger");
    if (alphaTrigger) alphaTrigger.onclick = function(e) { e.preventDefault(); alphaPanel.open(); };
});
