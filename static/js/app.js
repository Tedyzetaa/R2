/* filename: static/js/app.js */
/* ================================================================
   R2 Ghost Protocol v12.0 - FULL REFACTOR
   - Corrigido: sidebar com transform, overlay com visibility
   - Unificada notificação, removido showToast
   - Botões do editor conectados, matrix rain responsiva
   - WebSocket com fallback, rate limiting, timeout execução
   ================================================================ */

// ====================== VARIÁVEIS DE MÓDULO ======================
let wsManager = null;
let isGenerating = false;
let toastTimer = null;
let soundwaveInterval = null;
let battleModeAtivo = false;
let reconhecimentoDeVoz = null;
let soundwaveBars = [];
let audioAtual = null;
let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;
let configVoice = "Thalita";
let configDriver = "Padrão";
let filaInterval = null;
let arquivoSelecionado = null;
let picoSelecionado = null;
let codigoBackup = "";
let modoRevisaoAtivo = false;
let dragHandlersBound = false;
let _siloEventsSet = false;           // Melhoria #1
let voiceRetryCount = 0;
let editorTabs = { 'scratchpad.py': '' };
let currentTab = 'scratchpad.py';

// ====================== MATRIX RAIN (RESPONSIVE) ======================
let matrixAnimationId = null;
let matrixCtx = null, matrixCanvas = null;
function initMatrixRain() {
  const canvas = document.getElementById('matrix-canvas');
  if (!canvas) return;
  matrixCanvas = canvas;
  matrixCtx = canvas.getContext('2d');
  let fontSize = 16;
  let alphabet = 'ｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
  
  let drops = [];
  let columns = 0;
  
  function resizeAndReset() {
    matrixCanvas.width = window.innerWidth;
    matrixCanvas.height = window.innerHeight;
    columns = Math.floor(matrixCanvas.width / fontSize);
    drops = new Array(columns);
    for (let i = 0; i < drops.length; i++) {
      drops[i] = Math.random() * -100;
    }
  }
  
  window.addEventListener('resize', resizeAndReset);
  resizeAndReset();
  
  function draw() {
    if (!matrixCtx || !matrixCanvas) return;
    matrixCtx.fillStyle = 'rgba(0, 0, 0, 0.05)';
    matrixCtx.fillRect(0, 0, matrixCanvas.width, matrixCanvas.height);
    matrixCtx.font = `${fontSize}px "Share Tech Mono"`;
    for (let i = 0; i < drops.length; i++) {
      const text = alphabet.charAt(Math.floor(Math.random() * alphabet.length));
      matrixCtx.fillStyle = Math.random() > 0.98 ? '#FFF' : '#00ff41';
      matrixCtx.fillText(text, i * fontSize, drops[i] * fontSize);
      if (drops[i] * fontSize > matrixCanvas.height && Math.random() > 0.975) drops[i] = 0;
      drops[i]++;
    }
    matrixAnimationId = requestAnimationFrame(draw);
  }
  if (matrixAnimationId) cancelAnimationFrame(matrixAnimationId);
  matrixAnimationId = requestAnimationFrame(draw);
}

// ====================== NOTIFICAÇÃO UNIFICADA ======================
function notificar(msg, tipo = 'info') {
  let toastDiv = document.getElementById('toast');
  if (!toastDiv) {
    toastDiv = document.createElement('div');
    toastDiv.id = 'toast';
    document.body.appendChild(toastDiv);
  }
  const notif = document.createElement('div');
  notif.className = `notif-msg${tipo === 'err' ? ' err' : ''}`;
  notif.textContent = msg;
  toastDiv.appendChild(notif);
  setTimeout(() => notif.remove(), 3000);
}

// ====================== API UTILITY ======================
async function apiPost(url, body) {
  try {
    const response = await fetch(url, {
      method: 'POST',
      body: body
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return await response.json();
  } catch (e) {
    notificar(`Erro de API: ${e.message}`, 'err');
    throw e;
  }
}

// ====================== LOGGING ======================
function r2Log(level, context, msg, data) {
  const timestamp = new Date().toISOString();
  const logMsg = `[${timestamp}] [${context}] ${msg}`;
  console[level](logMsg, data || '');
}

// ====================== WEBSOCKET MANAGER ======================
class WebSocketManager {
  constructor() {
    this.ws = null;
    this.isConnected = false;
    this.reconnectAttempts = 0;
    this._processingSem = null; // será criado por conexão
  }

  connect() {
    const proto = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
    const url = proto + window.location.host + '/ws';
    console.log('[WS] Conectando a', url);
    this.setStatus(false, "CONECTANDO...");
    try {
      this.ws = new WebSocket(url);
      this.ws.onopen = () => this.onOpen();
      this.ws.onclose = (ev) => this.onClose(ev);
      this.ws.onmessage = (ev) => this.onMessage(ev);
      this.ws.onerror = (err) => console.error('[WS] Erro', err);
    } catch(e) {
      console.error('[WS] Falha', e);
      setTimeout(() => this.connect(), 3000);
    }
  }

  onOpen() {
    this.isConnected = true;
    this.reconnectAttempts = 0;
    this.setStatus(true, "ONLINE");
    notificar('Conexão estabelecida');
  }

  onClose(event) {
    this.isConnected = false;
    this.setStatus(false, `RECONECTANDO (${this.reconnectAttempts + 1}/10)`);
    notificar('Reconectando...');
    if (this.reconnectAttempts < 10) {
      const delay = Math.min(30000, 1000 * Math.pow(2, this.reconnectAttempts));
      this.reconnectAttempts++;
      setTimeout(() => this.connect(), delay);
    }
  }

  onMessage(evt) {
    try {
      const data = JSON.parse(evt.data);
      this.handleMessage(data);
    } catch(e) {
      r2Log('error', 'WS', 'JSON inválido', { data: evt.data, error: e });
    }
  }

  handleMessage(data) {
    if (data.type === 'system') {
      hideTyping();
      appendMsg('sys', 'SYS', data.text);
    } else if (data.type === 'stream') {
      hideTyping();
      const chatEl = document.getElementById('chat');
      if (!chatEl) return;
      const last = chatEl.lastElementChild;
      if (last && last.getAttribute('data-role') === 'bot') {
        const raw = last.querySelector('.bot-raw');
        if (raw) raw.textContent += data.text;
      } else {
        appendMsg('bot', 'R2', data.text);
      }
      scrollChatToBottom();
    } else if (data.type === 'done') {
      hideTyping();
      renderLastBot();
      toggleSendButton(false);
      scrollChatToBottom();
    } else if (data.type === 'image') {
      hideTyping();
      appendMsg('sys', 'SYS', `<b>${escHtml(data.text)}</b><br><img src="${escHtml(data.url)}">`);
      scrollChatToBottom();
    } else if (data.type === 'audio') {
      if (data.url) {
        if (audioAtual) audioAtual.pause();
        const audioEl = new Audio(data.url);
        audioAtual = audioEl;
        if (battleModeAtivo) {
          setSoundwaveSpeaking(true);
          audioEl.onended = () => setSoundwaveSpeaking(false);
        }
        audioEl.play().catch(e => console.warn(e));
      }
    } else if (data.type === 'speaking_start') { // [FIXED: batalha-3.1]
      // R2 começou a falar — para o microfone e anima o soundwave
      if (reconhecimentoDeVoz) {
        try { reconhecimentoDeVoz.stop(); } catch(e) {}
      }
      setSoundwaveSpeaking(true);

    } else if (data.type === 'speaking_end') { // [FIXED: batalha-3.1]
      // R2 terminou de falar — para animação e retoma escuta após margem
      setSoundwaveSpeaking(false);
      if (battleModeAtivo) {
        setTimeout(function() {
          if (!reconhecimentoDeVoz) return;
          try { reconhecimentoDeVoz.start(); } catch(e) {}
        }, 600); // 600ms de margem para o áudio dissipar no ambiente
      }
    } else if (data.type === 'alpha_log') {
      const terminal = document.getElementById('alpha-terminal');
      if (!terminal) return;
      const line = document.createElement('div');
      line.className = 'alpha-log-line';

      // Colorir baseado no conteúdo
      if (data.text.includes('SINAL') || data.text.includes('DETECTADO') || data.text.includes('⚡')) {
        line.style.color = '#00ff41';
        line.style.fontWeight = 'bold';
      }
      if (data.text.includes('ERRO') || data.text.includes('❌') || data.text.includes('Falha'))
        line.classList.add('alpha-log-error');
      if (data.text.includes('WIN'))
        line.classList.add('alpha-log-ok');
      if (data.text.includes('LOSS'))
        line.classList.add('alpha-log-warn');
      if (data.text.includes('FLASH'))
        line.classList.add('alpha-highlight');

      line.textContent = `[${new Date().toLocaleTimeString()}] ${data.text}`;
      terminal.appendChild(line);
      terminal.scrollTop = terminal.scrollHeight; // Auto-scroll
    }
  }

  sendCommand(text, voice = configVoice, driver = configDriver) {
    if (!this.ws || this.ws.readyState !== 1) {
      notificar('Servidor offline. Mensagem não enviada.', 'err');
      return false;
    }
    this.ws.send(JSON.stringify({ type: "command", text, voice, driver }));
    return true;
  }

  sendAudio(base64Audio) {
    if (!this.ws || this.ws.readyState !== 1) {
      notificar('Servidor offline.', 'err');
      return false;
    }
    this.ws.send(JSON.stringify({ type: "audio_input", data: base64Audio, voice: configVoice }));
    return true;
  }

  setStatus(online, label) {
    const dot = document.getElementById('status-dot');
    const txt = document.getElementById('status-text');
    if (dot) dot.classList.toggle('offline', !online);
    if (txt) txt.textContent = label;
  }
}

// ====================== AUXILIARES ======================
function escHtml(s) {
  return String(s || '').replace(/[&<>]/g, (m) => {
    if (m === '&') return '&amp;';
    if (m === '<') return '&lt;';
    if (m === '>') return '&gt;';
    return m;
  }).replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

function autoResize(el) {
  if (!el) return;
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 130) + 'px';
}

function scrollChatToBottom() {
  const wrapper = document.getElementById('chat-wrapper');
  if (wrapper) wrapper.scrollTop = wrapper.scrollHeight;
}

function removeBootScreen() {
  const boot = document.getElementById('boot-screen');
  if (boot) {
    boot.style.display = 'none';
  }
}

function updateUploadBadge(count, name) {
  const btn = document.getElementById('upload-btn');
  if (!btn) return;
  let badge = btn.querySelector('.upload-badge');
  if (!badge) {
    badge = document.createElement('span');
    badge.className = 'upload-badge';
    badge.style.position = 'absolute';
    badge.style.top = '-5px';
    badge.style.right = '-5px';
    badge.style.background = 'var(--red)';
    badge.style.color = '#fff';
    badge.style.borderRadius = '50%';
    badge.style.width = '18px';
    badge.style.height = '18px';
    badge.style.fontSize = '10px';
    badge.style.display = 'flex';
    badge.style.alignItems = 'center';
    badge.style.justifyContent = 'center';
    badge.style.fontWeight = 'bold';
    btn.style.position = 'relative';
    btn.appendChild(badge);
  }
  badge.textContent = count;
  // Show name below textarea
  const hint = document.querySelector('.input-hint');
  if (hint) {
    hint.innerHTML = `Arquivo: ${name} | Enter: Enviar | Shift+Enter: Nova Linha | ROOT ACCESS GRANTED`;
  }
}
function appendMsg(role, sender, text) {
  removeBootScreen();
  const chat = document.getElementById('chat');
  if (!chat) return;
  const wrapper = document.createElement('div');
  wrapper.className = `msg ${role}`;
  if (role === 'bot') {
    wrapper.setAttribute('data-role', 'bot');
    const avatar = document.createElement('div'); avatar.className = 'msg-avatar'; avatar.textContent = 'R2';
    const body = document.createElement('div'); body.className = 'msg-body';
    const senderDiv = document.createElement('div'); senderDiv.className = 'msg-sender'; senderDiv.textContent = 'R2';
    const bubble = document.createElement('div'); bubble.className = 'msg-bubble';
    const rawSpan = document.createElement('span'); rawSpan.className = 'bot-raw'; rawSpan.style.display = 'none'; rawSpan.textContent = text || '';
    const contentDiv = document.createElement('div'); contentDiv.className = 'bot-content';
    bubble.appendChild(rawSpan); bubble.appendChild(contentDiv);
    body.appendChild(senderDiv); body.appendChild(bubble);
    wrapper.appendChild(avatar); wrapper.appendChild(body);
  } else {
    const avatar = document.createElement('div'); avatar.className = 'msg-avatar'; avatar.textContent = (role === 'user') ? 'TED' : 'SYS';
    const body = document.createElement('div'); body.className = 'msg-body';
    const senderDiv = document.createElement('div'); senderDiv.className = 'msg-sender'; senderDiv.textContent = sender;
    const bubble = document.createElement('div'); bubble.className = 'msg-bubble'; bubble.innerHTML = text;
    body.appendChild(senderDiv); body.appendChild(bubble);
    wrapper.appendChild(avatar); wrapper.appendChild(body);
  }
  chat.appendChild(wrapper);
  scrollChatToBottom();
}

function renderLastBot() {
  const chat = document.getElementById('chat');
  if (!chat) return;
  const bots = Array.from(chat.children).filter(c => c.getAttribute('data-role') === 'bot');
  const lastBot = bots[bots.length - 1];
  if (!lastBot) return;
  const rawEl = lastBot.querySelector('.bot-raw');
  const ctEl = lastBot.querySelector('.bot-content');
  if (!rawEl || !ctEl) return;
  const rawText = rawEl.textContent;
  rawEl.style.display = 'none';
  if (typeof marked !== 'undefined') {
    try { ctEl.innerHTML = marked.parse(rawText); } catch(e) { ctEl.textContent = rawText; }
  } else {
    ctEl.textContent = rawText;
  }
  const blocks = ctEl.querySelectorAll('pre code');
  blocks.forEach(block => injectCodeCard(block));
  scrollChatToBottom();
}

function showTyping() {
  removeBootScreen();
  if (document.getElementById('typing-row')) return;
  const chat = document.getElementById('chat');
  if (!chat) return;
  const row = document.createElement('div'); row.id = 'typing-row'; row.className = 'msg bot';
  const av = document.createElement('div'); av.className = 'msg-avatar'; av.textContent = 'R2';
  const bd = document.createElement('div'); bd.className = 'msg-body';
  const sn = document.createElement('div'); sn.className = 'msg-sender'; sn.textContent = 'R2';
  const bu = document.createElement('div'); bu.className = 'msg-bubble';
  const dt = document.createElement('div'); dt.className = 'typing-dots'; dt.innerHTML = '<span></span><span></span><span></span>';
  bu.appendChild(dt); bd.appendChild(sn); bd.appendChild(bu); row.appendChild(av); row.appendChild(bd);
  chat.appendChild(row);
  scrollChatToBottom();
  toggleSendButton(true);
}

function hideTyping() {
  const t = document.getElementById('typing-row');
  if (t && t.parentNode) t.parentNode.removeChild(t);
}

function toggleSendButton(generating) {
  isGenerating = generating;
  const app = document.getElementById('app');
  if (generating) {
    if (app) app.classList.add('generating');
  } else {
    if (app) app.classList.remove('generating');
  }
  const btn = document.getElementById('send-btn');
  if (!btn) return;
  if (generating) {
    btn.classList.add('stop-mode');
    btn.textContent = 'PARAR';
  } else {
    btn.classList.remove('stop-mode');
    btn.textContent = 'EXECUTAR';
  }
}

function stopGeneration() {
  const xhr = new XMLHttpRequest();
  xhr.open('POST', '/api/stop', true);
  xhr.send();
  toggleSendButton(false);
}

function sendMsg() {
  const box = document.getElementById('msgBox');
  if (!box) return;
  const msg = box.value.trim();
  if (!msg) {
    notificar('Digite uma mensagem antes de enviar.');
    return;
  }
  // Verifica conectividade antes de adicionar no chat (Melhoria #7)
  if (!wsManager || !wsManager.isConnected) {
    notificar('Servidor offline. Reconectando...', 'err');
    return;
  }
  appendMsg('user', 'TEDDY', escHtml(msg));
  if (wsManager.sendCommand(msg)) {
    box.value = '';
    box.style.height = 'auto';
    showTyping();
  }
}

function execCmd(cmd, label) {
  if (!wsManager || !wsManager.isConnected) {
    notificar('Servidor offline.', 'err');
    return;
  }
  closeSidebar();
  appendMsg('user', 'TEDDY', escHtml(label));
  wsManager.sendCommand(cmd);
  showTyping();
}

function quickPrompt(text) {
  const box = document.getElementById('msgBox');
  if (box) box.value = text;
  sendMsg();
}

function clearChat() {
  if (confirm('CONFIRMAR: Apagar todo o histórico visível?')) {
    const chat = document.getElementById('chat');
    if (chat) chat.innerHTML = '';
    notificar('Chat limpo.');
  }
}

// ====================== SIDEBAR ======================
function closeSidebar() {
  const sb = document.getElementById('sidebar');
  const ov = document.getElementById('overlay');
  if (sb) sb.classList.remove('open');
  if (ov) ov.classList.remove('active');
}
function toggleSidebar() {
  const sb = document.getElementById('sidebar');
  const ov = document.getElementById('overlay');
  if (!sb) return;
  if (sb.classList.contains('open')) {
    closeSidebar();
  } else {
    sb.classList.add('open');
    ov.classList.add('active');
  }
}

// ====================== DRAG & DROP ======================
function setupUnifiedDragDrop() {
  if (dragHandlersBound) return;
  dragHandlersBound = true;
  window.addEventListener('dragover', (e) => { e.preventDefault(); document.body.classList.add('drag-over'); });
  window.addEventListener('dragleave', () => { document.body.classList.remove('drag-over'); });
  window.addEventListener('drop', (e) => {
    e.preventDefault();
    document.body.classList.remove('drag-over');
    const files = e.dataTransfer.files;
    if (!files.length) return;
    let shouldOpenEditor = false;
    for (let i = 0; i < files.length; i++) {
      const name = files[i].name.toLowerCase();
      if (name.endsWith('.py') || name.endsWith('.js') || name.endsWith('.txt')) {
        shouldOpenEditor = true;
        break;
      }
    }
    if (shouldOpenEditor) {
      const file = files[0];
      const reader = new FileReader();
      reader.onload = (ev) => {
        abrirEditor();
        adicionarArquivoAoPainel(file.name, ev.target.result);
        appendMsg('sys', 'SYS', `Arquivo '${file.name}' carregado no editor.`);
      };
      reader.readAsText(file);
    } else {
      handleFiles(files);
    }
  });
}

async function handleFiles(files) {
  if (!files || !files.length) return;
  notificar(`Enviando ${files.length} arquivo(s)...`);
  const formData = new FormData();
  for (let i = 0; i < files.length; i++) formData.append('arquivos', files[i]);
  try {
    const res = await apiPost('/api/upload_arquivos', formData);
    if (res.ok) {
      const box = document.getElementById('msgBox');
      const cmds = res.arquivos.map(a => `/ler ${a}`).join(' ');
      box.value = (box.value ? box.value + ' ' : '') + cmds + ' ';
      autoResize(box);
      box.focus();
      notificar('Arquivos na base!');
    } else {
      notificar(`Erro: ${res.error || 'desconhecido'}`, 'err');
    }
  } catch (e) {
    notificar('Falha de rede.', 'err');
  }
}

// ====================== EDITOR LATERAL ======================
function adicionarArquivoAoPainel(nomeArquivo, conteudo) {
  const tabs = document.getElementById('file-list-tabs');
  if (!tabs) return;
  Array.from(tabs.children).forEach(c => c.classList.remove('active'));
  const novaAba = document.createElement('div');
  novaAba.className = 'code-tab active';
  novaAba.textContent = nomeArquivo;
  novaAba.onclick = () => {
    Array.from(tabs.children).forEach(c => c.classList.remove('active'));
    novaAba.classList.add('active');
  };
  tabs.appendChild(novaAba);
  const editor = document.getElementById('code-editor');
  if (editor) editor.value = conteudo;
  abrirEditor();
}
function copiarCodigoEditor() {
  const editor = document.getElementById('code-editor');
  if (!editor) return;
  const codigo = editor.value;
  if (!codigo.trim()) { notificar('Nada para copiar'); return; }
  navigator.clipboard.writeText(codigo).then(() => notificar('Código copiado'))
    .catch(() => {
      const ta = document.createElement('textarea');
      ta.value = codigo;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      document.body.removeChild(ta);
      notificar('Código copiado (fallback)');
    });
}
function executarCodigoEditor() {
  const editor = document.getElementById('code-editor');
  if (!editor) return;
  const codigo = editor.value;
  if (!codigo.trim()) { notificar('Digite um código.'); return; }
  const output = document.getElementById('code-output');
  if (!output) return;
  output.innerHTML = '<div style="color:#f59e0b;">Executando...</div>';
  const xhr = new XMLHttpRequest();
  xhr.open('POST', '/api/execute_code', true);
  xhr.setRequestHeader('Content-Type', 'application/json');
  xhr.onload = () => {
    let data;
    try { data = JSON.parse(xhr.responseText); } catch(e) { data = { ok: false, error: 'Resposta inválida' }; }
    if (data.ok) {
      output.innerHTML = `<div style="color:#10b981;">▶ SAÍDA:</div><pre>${escHtml(data.output || '✔️ Sem saída.')}</pre>`;
    } else {
      output.innerHTML = `<div style="color:#ef4444;">⛔ ERRO:</div><pre>${escHtml(data.error)}</pre>`;
    }
  };
  xhr.onerror = () => output.innerHTML = '<div style="color:#ef4444;">❌ Falha na comunicação.</div>';
  xhr.send(JSON.stringify({ filename: 'editor_code.py', content: codigo }));
}
function expandirEditor() {
  const panel = document.getElementById('code-panel');
  if (!panel) return;
  panel.classList.toggle('expanded');
  notificar(panel.classList.contains('expanded') ? 'Modo tela cheia' : 'Editor recolhido');
}
function fecharEditor() {
  const panel = document.getElementById('code-panel');
  if (panel) {
    const editor = document.getElementById('code-editor');
    if (editor) {
      editorTabs[currentTab] = editor.value;
      if (editor.value.trim()) {
        sessionStorage.setItem('r2_editor_content', editor.value);
        notificar('Conteúdo do editor preservado.');
      }
    }
    panel.classList.add('closed');
  }
}
function abrirEditor() {
  const panel = document.getElementById('code-panel');
  if (panel) {
    panel.classList.remove('closed');
    const editor = document.getElementById('code-editor');
    if (editor) {
      const saved = sessionStorage.getItem('r2_editor_content');
      if (saved && !editorTabs[currentTab]) editorTabs[currentTab] = saved;
      editor.value = editorTabs[currentTab] || '';
    }
  }
}
function toggleEditorPanel() {
  const panel = document.getElementById('code-panel');
  if (!panel) return;
  panel.classList.toggle('closed');
}
function analisarCodigoTatico() {
  const editor = document.getElementById('code-editor');
  if (!editor) return;
  const code = editor.value;
  if (!code.trim()) return;
  // Melhoria #2: não fechar o editor
  enviarComando(`Analise o código:\n\`\`\`\n${code}\n\`\`\``);
}
function iniciarRefatoracao() {
  const editor = document.getElementById('code-editor');
  if (!editor) return;
  const code = editor.value;
  if (!code.trim()) return;
  codigoBackup = code;
  modoRevisaoAtivo = true;
  const controls = document.getElementById('diff-controls');
  if (controls) controls.style.display = 'inline-block';
  enviarComando(`Refatore o código abaixo retornando APENAS o código corrigido:\n\`\`\`\n${code}\n\`\`\``);
}
function aceitarRefatoracao() {
  const controls = document.getElementById('diff-controls');
  if (controls) controls.style.display = 'none';
  modoRevisaoAtivo = false;
  notificar("Otimização Aplicada");
}
function rejeitarRefatoracao() {
  const editor = document.getElementById('code-editor');
  if (editor && codigoBackup) editor.value = codigoBackup;
  const controls = document.getElementById('diff-controls');
  if (controls) controls.style.display = 'none';
  modoRevisaoAtivo = false;
  notificar("Alterações Descartadas");
}

function enviarComando(texto) {
  if (wsManager && wsManager.isConnected) {
    wsManager.sendCommand(texto);
    return true;
  }
  notificar('Servidor offline.', 'err');
  return false;
}

// ====================== VOZ E MODO BATALHA ======================
function toggleMicRecording() {
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    notificar('Navegador não suporta gravação.', 'err');
    return;
  }
  if (isRecording) {
    if (mediaRecorder && mediaRecorder.state === 'recording') mediaRecorder.stop();
    isRecording = false;
    const micBtn = document.getElementById('mic-msg-btn');
    if (micBtn) micBtn.classList.remove('recording');
    notificar('Gravação finalizada. Enviando...');
  } else {
    navigator.mediaDevices.getUserMedia({ audio: true })
      .then(stream => {
        let mimeType = '';
        if (MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) mimeType = 'audio/webm;codecs=opus';
        else if (MediaRecorder.isTypeSupported('audio/webm')) mimeType = 'audio/webm';
        mediaRecorder = new MediaRecorder(stream, mimeType ? { mimeType } : {});
        audioChunks = [];
        mediaRecorder.ondataavailable = event => { if (event.data.size) audioChunks.push(event.data); };
        mediaRecorder.onstop = () => {
          stream.getTracks().forEach(track => track.stop());
          const blobType = mimeType || 'audio/webm';
          const audioBlob = new Blob(audioChunks, { type: blobType });
          const reader = new FileReader();
          reader.onloadend = () => {
            const base64Audio = reader.result.split(',')[1];
            if (wsManager.sendAudio(base64Audio)) {
              appendMsg('sys', 'SYS', '🎙️ Áudio enviado. Aguarde...');
              showTyping();
            }
          };
          reader.readAsDataURL(audioBlob);
        };
        mediaRecorder.start();
        isRecording = true;
        const micBtn = document.getElementById('mic-msg-btn');
        if (micBtn) micBtn.classList.add('recording');
        notificar('🎤 Gravando... Clique novamente para parar.');
      })
      .catch(err => notificar('Erro no microfone.', 'err'));
  }
}

function criarBarrasSom() {
  const container = document.getElementById('soundwave-container');
  if (!container) return;
  container.innerHTML = '';
  soundwaveBars = [];
  for (let i = 0; i < 24; i++) {
    const bar = document.createElement('div');
    bar.className = 'soundwave-bar';
    bar.style.height = (12 + Math.random() * 40) + 'px';
    bar.style.animationDelay = (i * 0.05) + 's';
    container.appendChild(bar);
    soundwaveBars.push(bar);
  }
  if (soundwaveInterval) clearInterval(soundwaveInterval);
  soundwaveInterval = setInterval(() => {
    if (!battleModeAtivo) return;
    for (let j = 0; j < soundwaveBars.length; j++) {
      const bar = soundwaveBars[j];
      if (!bar.classList || bar.classList.contains('speaking')) continue;
      const novaAltura = 12 + Math.sin(Date.now() * 0.008 + j) * 30 + Math.random() * 10;
      bar.style.height = Math.max(8, Math.min(90, novaAltura)) + 'px';
    }
  }, 80);
}
function setSoundwaveSpeaking(falando) {
  if (!soundwaveBars.length) return;
  soundwaveBars.forEach(bar => {
    if (falando) bar.classList.add('speaking');
    else bar.classList.remove('speaking');
  });
}
function iniciarEscuta() {
  if (!window.SpeechRecognition && !window.webkitSpeechRecognition) {
    notificar('Navegador não suporta voz.', 'err');
    return;
  }
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  reconhecimentoDeVoz = new SpeechRecognition();
  reconhecimentoDeVoz.continuous = true;
  reconhecimentoDeVoz.interimResults = false;
  reconhecimentoDeVoz.lang = 'pt-BR';

  var tentativasErro = 0; // [FIXED: batalha-3.2]
  var MAX_TENTATIVAS = 5; // [FIXED: batalha-3.2]

  reconhecimentoDeVoz.onresult = (event) => {
    tentativasErro = 0; // [FIXED: batalha-3.2]
    const last = event.results.length - 1;
    const fala = event.results[last][0].transcript;
    const texto = fala.toLowerCase().trim();
    if (texto.includes('hey r2') || texto.includes('r2')) {
      // [FIXED: batalha-3.2] Regex aprimorada para não destruir "r2" no meio da frase
      var comando = texto.replace(/^.*?(?:hey\s+r2|r2)\s*/i, '').trim();
      if (comando.length) {
        if (enviarComando(comando)) notificar(`🎤 Enviado: ${comando}`);
      } else notificar('Palavra de ativação detectada.');
    }
  };
  reconhecimentoDeVoz.onerror = (e) => { // [FIXED: batalha-3.2]
    tentativasErro++;
    if (tentativasErro >= MAX_TENTATIVAS) {
      notificar('❌ Microfone com falha persistente. Modo Batalha encerrado.', 'err');
      toggleModoBatalha(); // desativa o modo batalha
      return;
    }
    if (battleModeAtivo) setTimeout(() => { try { reconhecimentoDeVoz.start(); } catch(e) {} }, 1000); 
  };
  reconhecimentoDeVoz.onend = () => { 
    // Só reinicia se não estiver no meio de uma fala do R2
    // (speaking_start/end controlam isso via stop/start explícitos)
    if (battleModeAtivo) setTimeout(() => { try { reconhecimentoDeVoz.start(); } catch(e) {} }, 300); 
  };
  try {
    reconhecimentoDeVoz.start();
    notificar('Modo Batalha ativado. Diga "Hey R2"...');
  } catch(e) { notificar('Erro microfone.', 'err'); }
}
function pararEscuta() {
  if (reconhecimentoDeVoz) {
    try { reconhecimentoDeVoz.stop(); } catch(e) {}
    reconhecimentoDeVoz = null;
  }
}
function toggleModoBatalha() {
  const tela = document.getElementById('battle-mode-screen');
  if (!tela) return;
  if (battleModeAtivo) {
    battleModeAtivo = false;
    tela.style.display = 'none';
    pararEscuta();
    if (audioAtual) { audioAtual.pause(); audioAtual = null; }
    notificar('Modo Safe ativado.');
  } else {
    battleModeAtivo = true;
    tela.style.display = 'flex';
    if (soundwaveBars.length === 0) criarBarrasSom();
    iniciarEscuta();
  }
}

// ====================== SETTINGS ======================
function loadSettings() {
  const stored = localStorage.getItem('r2_settings');
  if (stored) {
    try {
      const settings = JSON.parse(stored);
      if (settings.voice) configVoice = settings.voice;
      if (settings.driver) configDriver = settings.driver;
    } catch(e) {}
  }
  const voiceSelect = document.getElementById('voice-select');
  const driverSelect = document.getElementById('driver-select');
  if (voiceSelect) voiceSelect.value = configVoice;
  if (driverSelect) driverSelect.value = configDriver;
}
function saveSettings() {
  const voiceSelect = document.getElementById('voice-select');
  const driverSelect = document.getElementById('driver-select');
  if (voiceSelect) configVoice = voiceSelect.value;
  if (driverSelect) configDriver = driverSelect.value;
  localStorage.setItem('r2_settings', JSON.stringify({ voice: configVoice, driver: configDriver }));
  notificar('Configurações salvas!');
  closeSettingsModal();
}
function openSettingsModal() {
  const modal = document.getElementById('settings-modal');
  if (modal) {
    loadSettings();
    modal.style.display = 'flex';
  }
}
function closeSettingsModal() {
  const modal = document.getElementById('settings-modal');
  if (modal) modal.style.display = 'none';
}
function initSettings() {
  const settingsBtn = document.getElementById('settings-btn');
  if (settingsBtn) settingsBtn.onclick = openSettingsModal;
  loadSettings();
}
function initMicrophone() {
  const micBtn = document.getElementById('mic-msg-btn');
  if (micBtn) micBtn.onclick = (e) => { e.preventDefault(); toggleMicRecording(); };
}

// ====================== BROKER ======================
function abrirBroker() {
  notificar('Iniciando terminal de Trading Broker10...');
  closeSidebar();
  const xhr = new XMLHttpRequest();
  xhr.open('POST', '/api/broker/start', true);
  xhr.onreadystatechange = () => {
    if (xhr.readyState === 4) {
      if (xhr.status === 200) {
        let res;
        try { res = JSON.parse(xhr.responseText); } catch(e) { res = {}; }
        if (res.ok) {
          notificar('✅ Sessão Broker10 iniciada!');
          updateBrokerStatus(true);
          updateAlphaStatus(true);
          alphaPanel.open();
        } else {
          notificar(`❌ Erro ao iniciar: ${res.erro || res.detail}`, 'err');
        }
      } else {
        notificar('❌ Falha ao iniciar terminal de trading.', 'err');
      }
    }
  };
  xhr.send();
}

// ====================== SILO TIKTOK ======================
function abrirSiloTikTok() {
  const silo = document.getElementById('silo-backdrop');
  if (silo) silo.style.display = 'flex';
  carregarFila();
  listarMunicao();
  if (filaInterval === null) filaInterval = setInterval(carregarFila, 8000);
  if (!_siloEventsSet) {
    const dropZone = document.getElementById('drop-zone-silo');
    const fileInput = document.getElementById('file-input-silo');
    if (dropZone) {
      dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.classList.add('drag-over'); });
      dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));
      dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('drag-over');
        const files = e.dataTransfer.files;
        if (files.length) arquivoSelecionado = files[0];
        atualizarNomeArquivo();
      });
    }
    if (fileInput) fileInput.addEventListener('change', () => {
      if (fileInput.files.length) arquivoSelecionado = fileInput.files[0];
      atualizarNomeArquivo();
    });
    const chips = document.querySelectorAll('#peak-chips-silo .chip');
    chips.forEach(chip => chip.addEventListener('click', function() {
      const hora = this.getAttribute('data-hora');
      selecionarPico(this, hora);
    }));
    _siloEventsSet = true;
  }
}
function fecharSiloTikTok() {
  const silo = document.getElementById('silo-backdrop');
  if (silo) silo.style.display = 'none';
  if (filaInterval) { clearInterval(filaInterval); filaInterval = null; }
}
function atualizarNomeArquivo() {
  const display = document.getElementById('file-name-display');
  const nameSpan = document.getElementById('file-name-text');
  if (arquivoSelecionado) {
    display.style.display = 'block';
    nameSpan.textContent = arquivoSelecionado.name;
  } else {
    display.style.display = 'none';
  }
}
function selecionarPico(el, hora) {
  const chips = document.querySelectorAll('#peak-chips-silo .chip');
  chips.forEach(c => c.classList.remove('active'));
  el.classList.add('active');
  picoSelecionado = hora;
  const hoje = new Date();
  const [hh, mm] = hora.split(':');
  hoje.setHours(parseInt(hh), parseInt(mm), 0, 0);
  if (hoje <= new Date()) hoje.setDate(hoje.getDate() + 1);
  const pad = n => n < 10 ? '0' + n : '' + n;
  const iso = `${hoje.getFullYear()}-${pad(hoje.getMonth()+1)}-${pad(hoje.getDate())}T${pad(hoje.getHours())}:${pad(hoje.getMinutes())}`;
  document.getElementById('f-agenda').value = iso;
}
function adicionarFila() {
  if (!arquivoSelecionado) { notificar('Selecione um vídeo.', 'err'); return; }
  const titulo = document.getElementById('f-titulo').value.trim();
  if (!titulo) {
    const field = document.getElementById('f-titulo');
    field.style.borderColor = 'var(--red)';
    notificar('Título obrigatório.', 'err');
    field.focus();
    return;
  }
  const fd = new FormData();
  if (arquivoSelecionado.fromArsenal) {
    fd.append('video_path_arsenal', arquivoSelecionado.path);
  } else {
    fd.append('video', arquivoSelecionado);
  }
  fd.append('titulo', titulo);
  fd.append('descricao', document.getElementById('f-desc').value);
  fd.append('hashtags', document.getElementById('f-tags').value);
  fd.append('agendar_para', document.getElementById('f-agenda').value);
  fetch('/api/tiktok/add', { method: 'POST', body: fd })
    .then(r => r.json())
    .then(data => {
      if (data.ok) {
        notificar(`Missão adicionada: ${data.item.id}`);
        arquivoSelecionado = null;
        document.getElementById('file-input-silo').value = '';
        atualizarNomeArquivo();
        document.getElementById('f-titulo').value = '';
        document.getElementById('f-titulo').style.borderColor = '';
        document.getElementById('f-desc').value = '';
        document.getElementById('f-tags').value = '';
        document.getElementById('f-agenda').value = '';
        carregarFila();
      } else notificar(`Erro: ${JSON.stringify(data)}`, 'err');
    })
    .catch(e => notificar(`Erro de rede: ${e}`, 'err'));
}
function carregarFila() {
  fetch('/api/tiktok/fila')
    .then(r => r.json())
    .then(data => {
      const lista = data.fila || [];
      document.getElementById('fila-count').textContent = lista.length;
      const container = document.getElementById('fila-list');
      if (!container) return;
      container.innerHTML = '';
      if (!lista.length) { container.innerHTML = '<div class="empty-state">FILA VAZIA</div>'; return; }
      lista.forEach(item => container.appendChild(criarCard(item)));
    })
    .catch(e => notificar(`Erro carregar fila: ${e}`, 'err'));
}
function criarCard(item) {
  // função extensa mantida igual à versão anterior
  const card = document.createElement('div');
  card.className = `video-card status-${escHtml(item.status)}`;
  card.setAttribute('data-id', escHtml(item.id));
  const nomeArquivo = item.video_path ? item.video_path.split(/[\\/]/).pop() : '—';
  const dataFormatada = formatarData(item.agendar_para);
  let logsHtml = '';
  const logs = item.log || [];
  logs.forEach(log => logsHtml += `<div class="log-line">${escHtml(log)}</div>`);
  if (!logsHtml) logsHtml = '<div class="log-line">Nenhum log.</div>';
  const podeDisparar = (item.status === 'aguardando' || item.status === 'erro');
  const btnDisabled = podeDisparar ? '' : 'disabled';
  
  // Create elements instead of innerHTML for security
  const cardTop = document.createElement('div');
  cardTop.className = 'card-top';
  const cardThumb = document.createElement('div');
  cardThumb.className = 'card-thumb';
  cardThumb.innerHTML = '<span>▶</span>';
  const cardBody = document.createElement('div');
  cardBody.className = 'card-body';
  const titleRow = document.createElement('div');
  titleRow.style.display = 'flex';
  titleRow.style.justifyContent = 'space-between';
  const cardTitulo = document.createElement('div');
  cardTitulo.className = 'card-titulo';
  cardTitulo.title = escHtml(item.titulo);
  cardTitulo.textContent = escHtml(item.titulo);
  const statusPill = document.createElement('span');
  statusPill.className = `status-pill status-${escHtml(item.status)}`;
  statusPill.textContent = statusBadge(item.status);
  titleRow.appendChild(cardTitulo);
  titleRow.appendChild(statusPill);
  const cardDesc = document.createElement('div');
  cardDesc.className = 'card-desc';
  cardDesc.textContent = escHtml(item.descricao);
  const cardHashtags = document.createElement('div');
  cardHashtags.className = 'card-hashtags';
  cardHashtags.textContent = escHtml(item.hashtags);
  const cardMeta = document.createElement('div');
  cardMeta.className = 'card-meta';
  cardMeta.innerHTML = `<span>⏰ ${dataFormatada}</span><span>🎬 ${escHtml(nomeArquivo)}</span><span>#${escHtml(item.id)}</span>`;
  cardBody.appendChild(titleRow);
  cardBody.appendChild(cardDesc);
  cardBody.appendChild(cardHashtags);
  cardBody.appendChild(cardMeta);
  cardTop.appendChild(cardThumb);
  cardTop.appendChild(cardBody);
  
  const cardActions = document.createElement('div');
  cardActions.className = 'card-actions';
  const btnPostNow = document.createElement('button');
  btnPostNow.className = 'btn-post-now';
  if (!podeDisparar) btnPostNow.disabled = true;
  btnPostNow.textContent = '⚡ POSTAR AGORA';
  btnPostNow.addEventListener('click', () => dispararAgora(item.id, btnPostNow));
  const btnLogToggle = document.createElement('button');
  btnLogToggle.className = 'btn-log-toggle';
  btnLogToggle.textContent = 'LOG ▾';
  btnLogToggle.addEventListener('click', () => toggleLog(item.id));
  const btnDel = document.createElement('button');
  btnDel.className = 'btn-del';
  btnDel.textContent = '✕';
  btnDel.addEventListener('click', () => removerItem(item.id));
  cardActions.appendChild(btnPostNow);
  cardActions.appendChild(btnLogToggle);
  cardActions.appendChild(btnDel);
  
  const cardLog = document.createElement('div');
  cardLog.className = 'card-log';
  cardLog.id = `log-${escHtml(item.id)}`;
  cardLog.innerHTML = logsHtml;
  
  card.appendChild(cardTop);
  card.appendChild(cardActions);
  card.appendChild(cardLog);
  
  return card;
}
function toggleLog(id) {
  const el = document.getElementById(`log-${id}`);
  if (el) el.classList.toggle('open');
}
function statusBadge(status) {
  const map = { aguardando: '◌ AGUARDANDO', disparando: '◉ DISPARANDO', publicado: '✓ PUBLICADO', erro: '✕ ERRO' };
  return map[status] || status;
}
function formatarData(iso) {
  if (!iso) return '—';
  const d = new Date(iso);
  const pad = n => n < 10 ? '0' + n : n;
  return `${pad(d.getDate())}/${pad(d.getMonth()+1)} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}
function listarMunicao() {
  const container = document.getElementById('municao-list');
  if (!container) return;
  fetch('/api/tiktok/cortes')
    .then(r => r.json())
    .then(videos => {
      container.innerHTML = '';
      if (!videos || videos.length === 0) { container.innerHTML = '<div>Nenhum vídeo no arsenal.</div>'; return; }
      videos.forEach(v => {
        const card = document.createElement('div');
        card.className = 'municao-card';
        card.setAttribute('data-path', v.path);
        card.style.cssText = 'padding:8px;border:1px solid #0d2d45;margin-bottom:6px;cursor:pointer;background:#0a1520;color:#00d4ff;font-family:monospace;font-size:11px;';
        card.innerHTML = `🎬 ${escHtml(v.name)}`;
        card.onclick = () => {
          arquivoSelecionado = { name: v.name, path: v.path, fromArsenal: true };
          const tituloInput = document.getElementById('f-titulo');
          if (tituloInput) tituloInput.value = v.name.replace('.mp4', '').replace(/_/g, ' ');
          atualizarNomeArquivo();
          notificar(`Vídeo selecionado: ${v.name}`);
        };
        container.appendChild(card);
      });
    });
}
function dispararAgora(id, btn) {
  btn.disabled = true;
  btn.textContent = '⏳ DISPARANDO...';
  fetch(`/api/tiktok/post_now/${id}`, { method: 'POST' })
    .then(r => r.json())
    .then(data => {
      if (data.ok) { notificar(`Disparo iniciado: ${id}`); setTimeout(carregarFila, 1500); }
      else { notificar(`Erro: ${data.erro}`, 'err'); btn.disabled = false; btn.textContent = '⚡ POSTAR AGORA'; }
    })
    .catch(e => { notificar(`Erro rede: ${e}`, 'err'); btn.disabled = false; btn.textContent = '⚡ POSTAR AGORA'; });
}
function removerItem(id) {
  fetch(`/api/tiktok/remover/${id}`, { method: 'DELETE' })
    .then(r => r.json())
    .then(data => { if (data.ok) { notificar('Item removido.'); carregarFila(); } })
    .catch(e => notificar(`Erro: ${e}`, 'err'));
}

// ====================== ALPHA PANEL ======================
class AlphaPanel {
  constructor() {
    this._isOpen = false;
    this._pollTimer = null;
    this._autopilotOn = false;
  }
  _el(id) { return document.getElementById(id); }
  _log(msg, type = 'info') {
    const terminal = this._el("alpha-terminal");
    if (!terminal) return;
    const line = document.createElement("div");
    line.className = `alpha-log-line alpha-log-${type}`;
    line.innerHTML = `[${new Date().toTimeString().substr(0,8)}] ${msg}`;
    terminal.appendChild(line);
    terminal.scrollTop = terminal.scrollHeight;
  }
  _renderState(data) {
    const state = data.state || data.last_state || "IDLE";
    const conf = data.confidence || data.last_confidence || 0;
    const action = data.recommended_action || data.last_action || "--";
    const cycles = data.cycles || 0;
    if (this._el("alpha-state-name")) this._el("alpha-state-name").textContent = state;
    if (this._el("alpha-state-action")) this._el("alpha-state-action").textContent = action;
    if (this._el("alpha-confidence-bar")) this._el("alpha-confidence-bar").style.width = Math.round(conf * 100) + "%";
    if (this._el("alpha-confidence-label")) this._el("alpha-confidence-label").textContent = `Confiança: ${Math.round(conf * 100)}%`;
    if (this._el("alpha-cycle-count")) this._el("alpha-cycle-count").textContent = cycles;
  }
  _fetchStatus = () => {
    fetch('/api/alpha/status')
      .then(r => r.json())
      .then(data => {
        this._renderState(data);
        updateAlphaStatus(true);
      })
      .catch(() => updateAlphaStatus(false));
  }
  _startPolling() {
    if (this._pollTimer) return;
    this._pollTimer = setInterval(this._fetchStatus, 3000);
  }
  _stopPolling() {
    if (this._pollTimer) {
      clearInterval(this._pollTimer);
      this._pollTimer = null;
    }
  }
  open() {
    const modal = this._el("modal-alpha");
    if (modal) modal.style.display = "flex";
    this._isOpen = true;
    this._log("Painel Alpha ativado.", "sys");
    this._startPolling();
    this._fetchStatus();
  }
  close() {
    const modal = this._el("modal-alpha");
    if (modal) modal.style.display = "none";
    this._isOpen = false;
    this._stopPolling();
  }
  analyze() {
    this._log("Iniciando ciclo Neural...", "sys");
    fetch('/api/alpha/analyze', { method: 'POST' })
      .then(r => r.json())
      .then(data => {
        this._renderState(data);
        this._log(`Estado: ${data.state} | Ação: ${data.recommended_action}`, "state");
      });
  }
  toggleAutopilot() {
    const btn = this._el("btn-autopilot");
    if (!this._autopilotOn) {
      this._autopilotOn = true;
      if (btn) {
        btn.innerHTML = '<span class="alpha-btn-icon">⏸</span> Parar Autopilot';
        btn.className = "alpha-btn alpha-btn-autopilot running";
      }
      this._log("AUTOPILOT ATIVADO", "warn");
      fetch('/api/alpha/autopilot', { method: 'POST' }).catch(() => this._log("Erro autopilot", "error"));
    } else {
      this._autopilotOn = false;
      if (btn) {
        btn.innerHTML = '<span class="alpha-btn-icon">▶</span> Ativar Autopilot';
        btn.className = "alpha-btn alpha-btn-autopilot";
      }
      this._log("Parando autopilot...", "warn");
      fetch('/api/broker/stop_autopilot', { method: 'POST' })
        .then(r => r.json())
        .then(data => this._log(`Autopilot parado. Ciclos: ${data.total_cycles || "--"}`, "warn"));
    }
  }
  screenshot() {
    this._log("Capturando frame...", "sys");
    fetch('/api/alpha/screenshot')
      .then(r => r.json())
      .then(data => {
        if (data.screenshot_b64) {
          const img = this._el("alpha-screenshot-img");
          if (img) img.src = `data:image/png;base64,${data.screenshot_b64}`;
          const wrap = this._el("alpha-screenshot-wrap");
          if (wrap) wrap.style.display = "block";
          this._log("Frame capturado.", "ok");
        }
      });
  }
  override(action) {
    this._log(`Override: ${action}`, "warn");
    fetch('/api/alpha/override', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action })
    });
  }
  clearLog() {
    const terminal = this._el("alpha-terminal");
    if (terminal) terminal.innerHTML = "";
    this._log("Log limpo.", "sys");
  }
}

const alphaPanel = new AlphaPanel();

function updateAlphaStatus(state) {
  const el = document.getElementById('alpha-status');
  if (el) {
    el.textContent = state ? 'ONLINE' : 'OFFLINE';
    el.className = `status-value ${state ? 'online' : 'offline'}`;
  }
}
function updateBrokerStatus(state) {
  const el = document.getElementById('broker-status');
  if (el) {
    el.textContent = state ? 'ONLINE' : 'OFFLINE';
    el.className = `status-value ${state ? 'online' : 'offline'}`;
  }
}
function updateTikTokStatus(state) {
  const el = document.getElementById('tiktok-status');
  if (el) {
    el.textContent = state ? 'ONLINE' : 'OFFLINE';
    el.className = `status-value ${state ? 'online' : 'offline'}`;
  }
}

// ====================== ESTÚDIO DE CORTES ======================
function openStudio() {
  const el = document.getElementById('studio-backdrop');
  if (el) el.style.display = 'flex';
  closeSidebar();
}
function closeStudio() {
  const el = document.getElementById('studio-backdrop');
  if (el) el.style.display = 'none';
}
function startVideoExtraction() {
  const urlEl = document.getElementById('vid-url');
  if (!urlEl) return;
  const url = urlEl.value.trim();
  if (!url) { notificar('Insira o link do vídeo alvo!', 'err'); return; }
  const config = { url };
  closeStudio();
  execCmd(`/vid extract ${JSON.stringify(config)}`, 'Operação iniciada...');
}

// ====================== INJECT CODE CARD ======================
function injectCodeCard(block) {
  const codeText = block.textContent || '';
  const lines = codeText.split('\n');
  const firstLine = (lines[0] || '').trim();
  const m = firstLine.match(/(?:#|\/\/|<!--)\s*filename:\s*(\S+)/i);
  const filename = m ? m[1].replace(/-->$/, '').trim() : `node_temp_${Date.now()}.py`;
  let pre = block.parentNode;
  while (pre && pre.tagName !== 'PRE') pre = pre.parentNode;
  if (!pre || !pre.parentNode) return;
  let nxt = pre.nextSibling;
  while (nxt && nxt.nodeType === 3) nxt = nxt.nextSibling;
  if (nxt && nxt.className === 'code-action-bar') return;
  pre.style.marginBottom = '0';
  pre.style.borderBottom = 'none';
  const fnSpan = document.createElement('span');
  fnSpan.className = 'code-filename';
  fnSpan.innerHTML = `📂 ${escHtml(filename)}`;
  const actDiv = document.createElement('div');
  actDiv.className = 'code-actions';
  const execBtn = document.createElement('button');
  execBtn.type = 'button';
  execBtn.className = 'code-btn exec';
  execBtn.innerHTML = '▶ EXECUTAR';
  execBtn.onclick = () => executeCode(execBtn, filename, codeText);
  actDiv.appendChild(execBtn);
  const vsBtn = document.createElement('button');
  vsBtn.type = 'button';
  vsBtn.className = 'code-btn vscode';
  vsBtn.innerHTML = '⚡ ABRIR NO VS CODE';
  vsBtn.onclick = () => openVSCode(vsBtn, filename, codeText);
  actDiv.appendChild(vsBtn);
  const bar = document.createElement('div');
  bar.className = 'code-action-bar';
  bar.appendChild(fnSpan);
  bar.appendChild(actDiv);
  const term = document.createElement('div');
  term.className = 'exec-terminal';
  pre.parentNode.insertBefore(bar, pre.nextSibling);
  bar.parentNode.insertBefore(term, bar.nextSibling);
}
async function openVSCode(btn, filename, content) {
  btn.disabled = true;
  btn.textContent = 'INJETANDO...';
  try {
    const data = await apiPost('/api/open_vscode', JSON.stringify({ filename, content }));
    if (data.ok) {
      btn.textContent = 'CONECTADO!';
      setTimeout(() => { btn.innerHTML = '⚡ ABRIR NO VS CODE'; btn.disabled = false; }, 2500);
      notificar(`IDE Acionada: ${filename}`);
    } else {
      btn.textContent = 'FALHA';
      setTimeout(() => { btn.innerHTML = '⚡ ABRIR NO VS CODE'; btn.disabled = false; }, 2500);
    }
  } catch (e) {
    btn.textContent = 'FALHA';
    setTimeout(() => { btn.innerHTML = '⚡ ABRIR NO VS CODE'; btn.disabled = false; }, 2500);
  }
}

async function executeCode(btn, filename, content) {
  btn.disabled = true;
  btn.textContent = 'Executando...';
  let bar = btn.parentNode ? btn.parentNode.parentNode : null;
  let term = bar ? bar.nextSibling : null;
  while (term && term.nodeType === 3) term = term.nextSibling;
  if (term && term.className.indexOf('exec-terminal') > -1) {
    term.className = 'exec-terminal visible';
    term.textContent = 'Aguarde...';
  }
  try {
    const data = await apiPost('/api/execute_code', JSON.stringify({ filename, content }));
    if (term && term.className.indexOf('exec-terminal') > -1) {
      if (data.ok) {
        term.textContent = data.output || 'Executado sem saída.';
      } else {
        term.innerHTML = `<span class="err">ERRO: ${escHtml(data.error || 'desconhecido')}</span>`;
      }
    }
  } catch (e) {
    if (term) term.textContent = 'Falha.';
  }
  btn.textContent = 'Executar';
  btn.disabled = false;
}

// ====================== EVENTOS GLOBAIS ======================
function setupEvents() {
  const sendBtn = document.getElementById('send-btn');
  const msgBox = document.getElementById('msgBox');
  const menuBtn = document.getElementById('menu-btn');
  const overlay = document.getElementById('overlay');
  const closeBtn = document.querySelector('.sidebar-close');
  const toggleEditor = document.getElementById('toggle-editor-btn');
  const copyBtn = document.getElementById('copyCodeBtn');
  const execBtn = document.getElementById('code-execute-btn');
  const expandBtn = document.getElementById('code-expand-btn');
  const closeCodeBtn = document.getElementById('closeCodeBtn');

  if (sendBtn) sendBtn.addEventListener('click', (e) => { e.preventDefault(); if (isGenerating) stopGeneration(); else sendMsg(); });
  if (msgBox) {
    msgBox.addEventListener('keydown', (e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); if (isGenerating) stopGeneration(); else sendMsg(); } });
    msgBox.addEventListener('input', function() { autoResize(this); });
  }
  if (menuBtn) menuBtn.addEventListener('click', (e) => { e.preventDefault(); toggleSidebar(); });
  if (overlay) overlay.addEventListener('click', closeSidebar);
  if (closeBtn) closeBtn.addEventListener('click', closeSidebar);
  if (toggleEditor) toggleEditor.addEventListener('click', toggleEditorPanel);
  if (copyBtn) copyBtn.addEventListener('click', copiarCodigoEditor);
  if (execBtn) execBtn.addEventListener('click', executarCodigoEditor);
  if (expandBtn) expandBtn.addEventListener('click', expandirEditor);
  if (closeCodeBtn) closeCodeBtn.addEventListener('click', fecharEditor);
  
  const safeModeBtn = document.getElementById('safe-mode-btn');
  if (safeModeBtn) safeModeBtn.addEventListener('click', toggleModoBatalha);
}

// ====================== INICIALIZAÇÃO ======================
function init() {
  console.log('[R2] Iniciando Ghost Protocol v12.0');
  initMatrixRain();
  setupUnifiedDragDrop();
  setupEvents();
  wsManager = new WebSocketManager();
  wsManager.connect();
  initSettings();
  initMicrophone();

  // File input handler for upload button
  const fileInput = document.getElementById('file-input');
  if (fileInput) {
    fileInput.addEventListener('change', (e) => {
      const files = e.target.files;
      if (files && files.length) {
        handleFiles(files);
        updateUploadBadge(files.length, files[0].name);
      }
    });
  }

  setInterval(() => {
    const el = document.getElementById('system-time');
    if (el) {
      const now = new Date();
      const pad = n => n < 10 ? '0' + n : '' + n;
      el.textContent = `${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`;
    }
  }, 1000);

  setTimeout(() => {
    const splash = document.getElementById('tactical-splash');
    if (splash) {
      splash.style.opacity = '0';
      splash.style.pointerEvents = 'none';
      setTimeout(() => splash.style.display = 'none', 800);
    }
  }, 4000);
}

// Exposição global para funções chamadas via HTML inline
window.closeSidebar = closeSidebar;
window.toggleSidebar = toggleSidebar;
window.execCmd = execCmd;
window.openStudio = openStudio;
window.closeStudio = closeStudio;
window.startVideoExtraction = startVideoExtraction;
window.adicionarFila = adicionarFila;
window.toggleLog = toggleLog;
window.dispararAgora = dispararAgora;
window.removerItem = removerItem;
window.abrirBroker = abrirBroker;
window.abrirSiloTikTok = abrirSiloTikTok;
window.fecharSiloTikTok = fecharSiloTikTok;
window.alphaPanel = alphaPanel;
window.clearChat = clearChat;
window.quickPrompt = quickPrompt;
window.toggleModoBatalha = toggleModoBatalha;
window.saveSettings = saveSettings;
window.closeSettingsModal = closeSettingsModal;
window.analisarCodigoTatico = analisarCodigoTatico;
window.iniciarRefatoracao = iniciarRefatoracao;
window.aceitarRefatoracao = aceitarRefatoracao;
window.rejeitarRefatoracao = rejeitarRefatoracao;
window.copiarCodigoEditor = copiarCodigoEditor;
window.executarCodigoEditor = executarCodigoEditor;
window.expandirEditor = expandirEditor;
window.fecharEditor = fecharEditor;
window.autoResize = autoResize;

document.addEventListener('DOMContentLoaded', init);