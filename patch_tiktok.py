# filename: patch_tiktok.py
import os

def aplicar_patch():
    print("🚀 [R2] Iniciando integração do Módulo TikTok...")

    # 1. ATUALIZAÇÃO DO MAIN2.PY
    main_path = "main2.py"
    if os.path.exists(main_path):
        with open(main_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Injeção no Lifespan (Inicialização do módulo)
        if 'TikTokCommander' not in content:
            old_lifespan = 'noaa_ops = NOAAService() if NOAAService else None'
            new_lifespan = old_lifespan + '\n\n    global tiktok_ops\n    TikTokCommander = safe_import("tiktok_publisher", "TikTokCommander")\n    tiktok_ops = TikTokCommander() if TikTokCommander else None'
            content = content.replace(old_lifespan, new_lifespan)

        # Injeção das Rotas de API
        if '/api/enfileirar' not in content:
            old_routes = '@app.get("/", response_class=HTMLResponse)'
            new_routes = '''class FilaPayload(BaseModel):
    videos: List[str]

@app.get("/api/cortes")
async def listar_cortes():
    pasta = "static/media/cortes_virais"
    if not os.path.exists(pasta): return {"cortes": []}
    arquivos = [f for f in os.listdir(pasta) if f.endswith(".mp4")]
    arquivos.sort(key=lambda x: os.path.getmtime(os.path.join(pasta, x)), reverse=True)
    return {"cortes": arquivos}

@app.post("/api/enfileirar")
async def enfileirar_tiktok(payload: FilaPayload):
    if not tiktok_ops: return {"ok": False, "msg": "Módulo TikTok offline"}
    for v in payload.videos:
        caminho = os.path.abspath(os.path.join("static/media/cortes_virais", v))
        tiktok_ops.enfileirar(caminho)
    return {"ok": True, "msg": f"{len(payload.videos)} vídeos engatilhados no Silo."}

''' + old_routes
            content = content.replace(old_routes, new_routes)

        # Injeção do Comando no WebSocket
        if 'elif sub == "tiktok":' not in content:
            old_ws = 'elif sub == "astro":'
            new_ws = old_ws + '\n                    await websocket.send_json({"type": "system", "text": "☄️ Módulo de Defesa Planetária não está conectado nesta sessão."})\n                elif sub == "tiktok":\n                    await websocket.send_json({"type": "system", "text": "<button onclick=\'abrirCentralPostagem()\' style=\'background:#0ea5e9;color:white;padding:10px 20px;border:none;border-radius:8px;cursor:pointer;font-weight:bold;margin-top:10px;\'>📱 Abrir Central de Lançamento</button>"})'
            # Removemos a linha original do astro para não duplicar, já que o replace inclui ela corrigida
            content = content.replace('await websocket.send_json({"type": "system", "text": "☄️ Módulo de Defesa Planetária não está conectado nesta sessão."})', '')
            content = content.replace(old_ws, new_ws)

        with open(main_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("✅ main2.py atualizado.")
    else:
        print("❌ Erro: main2.py não encontrado.")

    # 2. ATUALIZAÇÃO DO APP.JS
    js_path = "static/js/app.js"
    if os.path.exists(js_path):
        with open(js_path, "r", encoding="utf-8") as f:
            content_js = f.read()

        if 'abrirCentralPostagem' not in content_js:
            extra_js = '''
/* ========== CENTRAL DE POSTAGEM TIKTOK ========== */
function abrirCentralPostagem() {
  closeSidebar();
  var xhr = new XMLHttpRequest();
  xhr.open('GET', '/api/cortes', true);
  xhr.onload = function() {
    if (xhr.status === 200) {
      var res = JSON.parse(xhr.responseText);
      renderModalTikTok(res.cortes);
    } else {
      showToast('❌ Erro ao buscar cortes.');
    }
  };
  xhr.send();
}

function renderModalTikTok(cortes) {
  var overlay = document.createElement('div');
  overlay.id = 'tiktok-modal-overlay';
  overlay.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.8);z-index:9999;display:flex;align-items:center;justify-content:center;backdrop-filter:blur(5px);';
  var modal = document.createElement('div');
  modal.style.cssText = 'background:#1a1c23;border:1px solid #0ea5e9;border-radius:12px;width:90%;max-width:500px;padding:20px;box-shadow:0 0 20px rgba(14,165,233,0.2);color:#e2e8f0;max-height:80vh;display:flex;flex-direction:column;';
  var header = document.createElement('h2');
  header.innerHTML = '📱 Silo de Lançamento (TikTok)';
  header.style.cssText = 'margin-top:0;color:#0ea5e9;font-size:18px;border-bottom:1px solid #334155;padding-bottom:10px;';
  var listContainer = document.createElement('div');
  listContainer.style.cssText = 'overflow-y:auto;margin:15px 0;flex:1;';
  if (cortes.length === 0) {
    listContainer.innerHTML = '<p style="text-align:center;color:#94a3b8;">Nenhum corte viral encontrado na base.</p>';
  } else {
    cortes.forEach(function(corte) {
      var label = document.createElement('label');
      label.style.cssText = 'display:flex;align-items:center;padding:10px;background:#0f1115;border:1px solid #334155;margin-bottom:8px;border-radius:6px;cursor:pointer;';
      var cb = document.createElement('input');
      cb.type = 'checkbox'; cb.value = corte; cb.className = 'tiktok-checkbox'; cb.style.marginRight = '12px';
      var text = document.createElement('span');
      text.textContent = corte.replace('.mp4', '').replace(/_/g, ' ');
      label.appendChild(cb); label.appendChild(text);
      listContainer.appendChild(label);
    });
  }
  var btnRow = document.createElement('div');
  btnRow.style.cssText = 'display:flex;justify-content:space-between;gap:10px;margin-top:10px;';
  var btnCancel = document.createElement('button');
  btnCancel.textContent = 'Cancelar';
  btnCancel.style.cssText = 'padding:10px;border-radius:6px;border:none;background:#334155;color:#fff;cursor:pointer;flex:1;';
  btnCancel.onclick = function() { document.body.removeChild(overlay); };
  var btnSend = document.createElement('button');
  btnSend.textContent = 'Adicionar à Fila';
  btnSend.style.cssText = 'padding:10px;border-radius:6px;border:none;background:#0ea5e9;color:#fff;cursor:pointer;flex:2;font-weight:bold;';
  btnSend.onclick = function() {
    var selecionados = [];
    var checkboxes = listContainer.querySelectorAll('.tiktok-checkbox:checked');
    for(var i=0; i<checkboxes.length; i++) selecionados.push(checkboxes[i].value);
    if (selecionados.length === 0) { showToast('Selecione um vídeo!'); return; }
    var xhrPost = new XMLHttpRequest();
    xhrPost.open('POST', '/api/enfileirar', true);
    xhrPost.setRequestHeader('Content-Type', 'application/json');
    xhrPost.onload = function() {
      var res = JSON.parse(xhrPost.responseText);
      showToast(res.msg);
      document.body.removeChild(overlay);
    };
    xhrPost.send(JSON.stringify({ videos: selecionados }));
  };
  btnRow.appendChild(btnCancel);
  if (cortes.length > 0) btnRow.appendChild(btnSend);
  modal.appendChild(header); modal.appendChild(listContainer); modal.appendChild(btnRow);
  overlay.appendChild(modal); document.body.appendChild(overlay);
}
'''
            with open(js_path, "a", encoding="utf-8") as f:
                f.write(extra_js)
        print("✅ app.js atualizado.")
    else:
        print("❌ Erro: app.js não encontrado.")

    print("\n🚀 [OPERACIONAL] Reinicie o servidor main2.py para ativar o Silo TikTok!")

if __name__ == "__main__":
    aplicar_patch() 