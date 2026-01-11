import os
import threading
import time
import asyncio
from flask import Flask
from features.telegram_uplink import TelegramUplink

# Servidor Web para manter o Render vivo
app = Flask(__name__)

@app.route('/')
def home():
    return "R2 TACTICAL OS - CLOUD CORE ACTIVE", 200

# Configurações de chaves via Environment Variables (Otimizado para Render)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8346260753:AAHtkB-boAMcnS1t-wedf9NZLwVvOuIl0_Y")
ADMIN_ID = os.environ.get("TELEGRAM_ADMIN_ID", "8117345546")

class R2CloudCore:
    def __init__(self):
        # Passamos None para a GUI, pois o Render não tem tela
        self.telegram_bot = TelegramUplink(TELEGRAM_TOKEN, ADMIN_ID, self)
        self.running = True
        # Cache de dados para simular o que a GUI faria
        self.dados_cpu = 0
        self.dados_ram = 0

    def _print_system_msg(self, msg): print(f"[SISTEMA]: {msg}")
    def _print_ai_msg(self, msg): print(f"[R2]: {msg}")
    def _print_user_msg(self, msg): print(f"[USER]: {msg}")

    def _executar_comando_remoto(self, cmd):
        # Aqui o server processa comandos simples (Clima, News, etc)
        # Como não temos a GUI aqui, ele age como um Bot puro
        print(f"Executando comando remoto: {cmd}")

    def run(self):
        self.telegram_bot.iniciar_sistema()
        self.telegram_bot.enviar_mensagem_ativa("☁️ [R2 CLOUD]: Sistema assumido pelo Render. Operação Remota Ativa.")

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    # 1. Inicia Web Server em Thread separada
    threading.Thread(target=run_web_server, daemon=True).start()
    
    # 2. Inicia o Bot
    r2_cloud = R2CloudCore()
    r2_cloud.run()
    
    # 3. Mantém o processo vivo
    while True:
        time.sleep(10)