# filename: patch_autoboot.py
import os
import re

FILE_PATH = "main2.py"

def apply_autoboot():
    print("⚙️ Redefinindo a sequência de inicialização do R2...")
    
    if not os.path.exists(FILE_PATH):
        print(f"❌ {FILE_PATH} não encontrado.")
        return

    with open(FILE_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    novo_entrypoint = """# ══════════════════════════════════════════
# ENTRYPOINT (AUTO-BOOT DESKTOP)
# ══════════════════════════════════════════
if __name__ == "__main__":
    import threading
    import webview
    import time
    import os

    def run_server():
        # Roda o servidor invisível na porta 8000
        uvicorn.run(app, host="127.0.0.1", port=8000, log_level="error")

    print("🚀 [BOOT] Ligando turbinas do servidor em segundo plano...")
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    print("🖥️ [BOOT] Desenhando Interface Nativa...")
    janela = webview.create_window(
        'R2 · Ghost Protocol', 
        'http://127.0.0.1:8000',
        width=1280, 
        height=800,
        background_color='#020b14',
        text_select=True
    )
    
    # Trava o script principal mantendo a janela aberta
    webview.start()
    
    # Protocolo de morte instantânea: fechou o app, mata tudo.
    print("🛑 [SHUTDOWN] Janela fechada. Cortando energia do terminal...")
    os._exit(0)"""

    # Localiza o entrypoint antigo e substitui pelo novo com Threading e Webview
    padrao = re.compile(
        r"# ══════════════════════════════════════════\n# ENTRYPOINT\n# ══════════════════════════════════════════\nif __name__ == \"__main__\":\n    uvicorn\.run\(app, host=\"0\.0\.0\.0\", port=8000\)",
        re.DOTALL
    )
    
    match = padrao.search(content)
    if not match:
        print("⚠️ Entrypoint original não encontrado. Talvez já tenha sido modificado.")
        return

    novo_conteudo = content[:match.start()] + novo_entrypoint + content[match.end():]

    with open(FILE_PATH, "w", encoding="utf-8") as f:
        f.write(novo_conteudo)

    print("✅ Auto-Boot injetado! O main2.py agora é um aplicativo autônomo.")
    print("🗑️ (Opcional) Você pode deletar o arquivo r2_desktop.py que criamos antes.")

if __name__ == "__main__":
    apply_autoboot()