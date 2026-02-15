import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
import socket
from datetime import datetime

# Tenta carregar o cérebro
try:
    from features.local_brain import LocalLlamaBrain
    brain = LocalLlamaBrain()
    print("🧠 [NEURAL UPLINK]: Cérebro Llama acoplado.")
except:
    brain = None
    print("⚠️ [NEURAL UPLINK]: Modo de Emergência (Sem IA).")

app = FastAPI(title="R2 Neural Link")

class Transmissao(BaseModel):
    comando: str
    origem: str = "mobile"

# --- AQUI ESTÁ A CORREÇÃO DA PERSONALIDADE ---
SYSTEM_PROMPT = """
INSTRUÇÃO CRÍTICA: Você NÃO é um robô de Star Wars. NÃO faça sons de bip.
Você é a R2, uma Inteligência Artificial Tática Avançada.
Idioma: Português do Brasil.
Personalidade: Leal, eficiente, inteligente e 'Tech Girl'.
REGRA ABSOLUTA: Trate o usuário EXCLUSIVAMENTE por "Senhor".
Exemplo de resposta: "Sim, Senhor. Sistemas operacionais."
"""

# Histórico (Reinicia a cada boot para garantir a persona)
historico_conversa = [{"role": "system", "content": SYSTEM_PROMPT}]

def get_ip_local():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except: IP = '127.0.0.1'
    finally: s.close()
    return IP

@app.post("/receber_ordem")
async def processar_ordem(dados: Transmissao):
    global historico_conversa
    cmd = dados.comando
    print(f"📡 [UPLINK]: {cmd}")

    # Comandos de Hardware
    if "desligar pc" in cmd.lower():
        return {"resposta": "🔒 Protocolo de desligamento remoto acionado, Senhor."}

    # Processamento Neural
    if brain:
        # Mantém histórico curto para não estourar memória
        if len(historico_conversa) > 6: 
            historico_conversa = [historico_conversa[0]] + historico_conversa[-4:]
            
        historico_conversa.append({"role": "user", "content": cmd})
        
        try:
            # Envia o histórico completo com a System Prompt reforçada
            resposta_full = await brain.chat_complete(historico_conversa)
            texto_resp = getattr(resposta_full, 'content', str(resposta_full))
            
            # Limpeza
            texto_resp = texto_resp.replace("<|eot_id|>", "").replace("*beep*", "").strip()
            
            historico_conversa.append({"role": "assistant", "content": texto_resp})
            print(f"🤖 [R2]: {texto_resp[:50]}...")
            return {"resposta": texto_resp}
            
        except Exception as e:
            # Fallback se o método chat_complete falhar
            try:
                resp = await brain.chat("user", cmd)
                return {"resposta": str(resp)}
            except:
                return {"resposta": f"Falha Neural: {e}"}
    
    return {"resposta": "Cérebro desconectado, Senhor."}

if __name__ == "__main__":
    print(f"🚀 R2 UPLINK V2 - PROTOCOLO 'SENHOR' ATIVO")
    uvicorn.run(app, host="0.0.0.0", port=8000)