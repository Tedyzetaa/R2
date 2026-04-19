# filename: patch_dragdrop.py
import os

FILE_PATH = "main2.py"

def apply_drag_and_drop():
    print("📎 Iniciando instalação do módulo de anexo Drag & Drop...")
    
    if not os.path.exists(FILE_PATH):
        print(f"❌ {FILE_PATH} não encontrado.")
        return

    with open(FILE_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. ROTA PYTHON PARA UPLOAD
    rota_python = """from fastapi import UploadFile, File
from typing import List

@app.post("/api/upload_arquivos")
async def api_upload_arquivos(arquivos: List[UploadFile] = File(...)):
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    salvos = []
    try:
        for arq in arquivos:
            # Sanitiza o nome removendo caracteres estranhos
            safe_name = re.sub(r"[^\w.\-]", "_", os.path.basename(arq.filename))
            caminho = WORKSPACE / safe_name
            with open(caminho, "wb") as f:
                f.write(await arq.read())
            salvos.append(safe_name)
        return {"ok": True, "arquivos": salvos}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.post("/api/execute_code")"""
    content = content.replace('@app.post("/api/execute_code")', rota_python)


    # 2. CSS VISUAL (Botão do clipe e overlay de arrastar)
    bloco_css = """#send-btn svg { width: 15px; height: 15px; }

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
}"""
    content = content.replace('#send-btn svg { width: 15px; height: 15px; }', bloco_css)


    # 3. HTML (Input invisível e botão do clipe)
    bloco_html = """<div id="input-row">
      <button type="button" id="upload-btn" title="Anexar arquivo (ou Arraste para a tela)">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
          <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"></path>
        </svg>
      </button>
      <input type="file" id="file-input" style="display:none" multiple>
      <textarea
        id="msgBox\""""
    content = content.replace('<div id="input-row">\n      <textarea\n        id="msgBox"', bloco_html)


    # 4. JAVASCRIPT (Lógica de intercepção e upload assíncrono)
    bloco_js = """/* DRAG AND DROP & UPLOAD */
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

/* INIT */"""
    content = content.replace("/* INIT */", bloco_js)

    # Inicia as funções no boot do JS
    content = content.replace("(function init() {", "(function init() {\n  setupDragAndDrop();")

    with open(FILE_PATH, "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ Atualização concluída. O R2 agora suporta Drag & Drop e Upload!")

if __name__ == "__main__":
    apply_drag_and_drop()