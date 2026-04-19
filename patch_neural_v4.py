# filename: patch_neural_v4.py
import os
import re

FILE_PATH = "main2.py"

def apply_neural_patch():
    print("🛠️ [SISTEMA]: Iniciando cirurgia de upgrade: Patch Neural V4...")
    
    if not os.path.exists(FILE_PATH):
        print(f"❌ {FILE_PATH} não encontrado no workspace.")
        return

    with open(FILE_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Adicionar o Lock e Importar a Threading
    content = content.replace(
        "import os, json, datetime, sys, time, asyncio, subprocess, shutil, re, gc",
        "import os, json, datetime, sys, time, asyncio, subprocess, shutil, re, gc\nimport threading"
    )
    
    content = content.replace(
        'os.makedirs("static/logs", exist_ok=True)',
        'os.makedirs("static/logs", exist_ok=True)\nhistorico_lock = threading.Lock()'
    )

    # 2. Blindar o Histórico contra Concorrência (Write-after-Write)
    new_salvar = """def salvar_no_historico_json(usuario, bot):
    interacao = {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "teddy": usuario,
        "r2": bot
    }
    with historico_lock:
        historico = []
        if os.path.exists(LOG_HISTORICO):
            try:
                with open(LOG_HISTORICO, "r", encoding="utf-8") as f:
                    historico = json.load(f)
            except Exception as e:
                print(f"[AVISO] Erro ao ler histórico: {e}")
        historico.append(interacao)
        try:
            with open(LOG_HISTORICO, "w", encoding="utf-8") as f:
                json.dump(historico, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"[AVISO] Erro ao gravar histórico: {e}")
"""
    
    new_carregar = """def carregar_historico_na_ram():
    with historico_lock:
        if os.path.exists(LOG_HISTORICO):
            try:
                with open(LOG_HISTORICO, "r", encoding="utf-8") as f:
                    dados = json.load(f)
                    contexto = []
                    for item in dados[-40:]:
                        contexto.append(f"Teddy: {item['teddy']}")
                        contexto.append(f"R2: {item['r2']}")
                    return contexto
            except Exception as e:
                print(f"[AVISO] Erro ao carregar RAM: {e}")
        return []
"""

    content = re.sub(r'def salvar_no_historico_json\(usuario, bot\):.*?indent=4\)', new_salvar, content, flags=re.DOTALL)
    content = re.sub(r'def carregar_historico_na_ram\(\):.*?return \[\]', new_carregar, content, flags=re.DOTALL)

    # 3. Instanciar a Tesoura Neural V4 e Restringir o CORS
    content = content.replace(
        'NOAAService = safe_import("noaa_service", "NOAAService")',
        'NOAAService = safe_import("noaa_service", "NOAAService")\nVideoSurgeon = safe_import("video_ops", "VideoSurgeon")'
    )
    content = content.replace(
        'noaa_ops = NOAAService() if NOAAService else None',
        'noaa_ops = NOAAService() if NOAAService else None\nvideo_ops = VideoSurgeon() if VideoSurgeon else None'
    )
    content = content.replace(
        'app.add_middleware(CORSMiddleware, allow_origins=["*"])',
        'app.add_middleware(CORSMiddleware, allow_origins=["http://127.0.0.1:8000", "http://localhost:8000"])'
    )

    # 4. Remover a memoria_ram Global
    content = content.replace('memoria_ram = carregar_historico_na_ram()', '')

    # 5. Atualizar o WebSocket (Memória de Sessão e Rota /vid viral)
    content = content.replace(
        'await websocket.accept()\n    sys_prompt = "Você é o R2, IA tática e Mestre Programador. REGRA: A primeira linha do código DEVE ser: # filename: nome.py"',
        'await websocket.accept()\n    sessao_memoria_ram = carregar_historico_na_ram()\n    sys_prompt = "Você é o R2, IA tática e Mestre Programador. REGRA: A primeira linha do código DEVE ser: # filename: nome.py"'
    )

    sync_block = 'if cmd_l == "/doc sync":\n                await websocket.send_json({"type": "system", "text": await asyncio.to_thread(rag_ops.sync)}); continue'
    viral_cmd = sync_block + """

            # ROTA DA TESOURA NEURAL V4
            if cmd_l.startswith("/vid viral "):
                video_alvo = comando.replace("/vid viral ", "").strip()
                await websocket.send_json({"type": "system", "text": f"⏳ Tesoura Neural V4: Analisando {video_alvo}..."})
                
                if video_ops and ai_brain:
                    res = await asyncio.to_thread(video_ops.processar_video_viral, video_alvo, ai_brain)
                    if isinstance(res, list):
                        msg = "✅ **Cortes Virais Extraídos com Sucesso:**\\n"
                        for r in res: msg += f"- `{r}`\\n"
                        await websocket.send_json({"type": "system", "text": msg})
                    else:
                        await websocket.send_json({"type": "system", "text": str(res)})
                else:
                    await websocket.send_json({"type": "system", "text": "❌ Tesoura Neural ou Cérebro LLaMA offline."})
                continue"""
    content = content.replace(sync_block, viral_cmd)

    # Session memory swap no bloco LLaMA
    content = content.replace('memoria_ram.append', 'sessao_memoria_ram.append')
    content = content.replace('for m in memoria_ram[-40:-1]:', 'for m in sessao_memoria_ram[-40:-1]:')

    with open(FILE_PATH, "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ [MISSÃO CUMPRIDA]: Patch Neural V4 aplicado com sucesso!")

if __name__ == "__main__":
    apply_neural_patch()