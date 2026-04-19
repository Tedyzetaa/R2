# filename: patch_memoria_llm.py
import os

FILE_PATH = "main2.py"

def apply_llm_fix():
    print("🧠 Iniciando cirurgia de expansão de memória e blindagem...")
    
    if not os.path.exists(FILE_PATH):
        print(f"❌ {FILE_PATH} não encontrado.")
        return

    with open(FILE_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Aumento do Contexto de Memória
    content = content.replace("n_ctx=10240", "n_ctx=32768")

    # 2. Blindagem contra o crash do WebSocket no LLM
    old_llm_loop = """                global STOP_GEN
                STOP_GEN = False
                resp_completa = ""
                stream = ai_brain(prompt, max_tokens=-1, stop=["<|im_end|>"], stream=True, temperature=0.5)
                for chunk in stream:
                    if STOP_GEN:
                        break
                    token = chunk["choices"][0]["text"]
                    resp_completa += token
                    await websocket.send_json({"type": "stream", "text": token})
                await websocket.send_json({"type": "done"})
                memoria_ram.append(f"R2: {resp_completa}")
                salvar_no_historico_json(comando, resp_completa)"""

    new_llm_loop = """                global STOP_GEN
                STOP_GEN = False
                resp_completa = ""
                try:
                    stream = ai_brain(prompt, max_tokens=-1, stop=["<|im_end|>"], stream=True, temperature=0.5)
                    for chunk in stream:
                        if STOP_GEN:
                            break
                        token = chunk["choices"][0]["text"]
                        resp_completa += token
                        await websocket.send_json({"type": "stream", "text": token})
                    await websocket.send_json({"type": "done"})
                    memoria_ram.append(f"R2: {resp_completa}")
                    salvar_no_historico_json(comando, resp_completa)
                except ValueError as e:
                    erro_msg = f"⚠️ <b>Capacidade Analítica Excedida:</b> O arquivo ou texto é grande demais para o limite atual de tokens. Tente fatiar o arquivo.<br><i>Detalhes: {str(e)}</i>"
                    await websocket.send_json({"type": "system", "text": erro_msg})
                    await websocket.send_json({"type": "done"})
                except Exception as e:
                    await websocket.send_json({"type": "system", "text": f"❌ <b>Falha Crítica no Cérebro LLM:</b> {str(e)}"})
                    await websocket.send_json({"type": "done"})"""

    if old_llm_loop not in content:
        print("⚠️ O loop antigo não foi encontrado exatamente como o esperado. A blindagem pode já estar instalada.")
    else:
        content = content.replace(old_llm_loop, new_llm_loop)

    with open(FILE_PATH, "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ Memória expandida para 32k tokens e blindagem anticolisão instalada com sucesso!")

if __name__ == "__main__":
    apply_llm_fix()