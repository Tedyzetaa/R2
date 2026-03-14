import sys
import os
import asyncio

# --- 1. PROTOCOLO DE RECONHECIMENTO DE DIRETÓRIOS ---
# Garante que o Python encontre os módulos dentro de /content/R2/features
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# --- 2. IMPORTAÇÕES DE MÓDULOS INTERNOS ---
try:
    from features.image_gen import gerar_imagem
    from features.system_monitor import SystemMonitor
    from features.telegram_uplink import TelegramBotUplink
    # Adicione aqui outros módulos conforme necessário
    print("✅ [SISTEMA]: Todos os módulos de 'features' foram mapeados.")
except ImportError as e:
    print(f"❌ [ERRO DE LIGAÇÃO]: Falha ao importar sub-módulo: {e}")

# --- 3. CONFIGURAÇÃO DE ENTRADA (TOKEN) ---
if len(sys.argv) < 2:
    print("\n" + "="*50)
    print("❌ [ERRO CRÍTICO]: TOKEN DO TELEGRAM NÃO FORNECIDO!")
    print("Execute assim: !python main.py SEU_TOKEN_AQUI")
    print("="*50 + "\n")
    sys.exit(1)

TOKEN_ARG = sys.argv[1]

# --- 4. LÓGICA PRINCIPAL DO R2 ---
class R2Core:
    def __init__(self, token):
        self.token = token
        self.monitor = SystemMonitor(self)
        self.uplink = None

    async def iniciar(self):
        print(f"🚀 R2 SYSTEM ONLINE: Versão Colab-Cloud")
        print(f"📡 Estabelecendo conexão com o Uplink do Telegram...")
        
        try:
            # Inicializa o bot com o token passado pelo argumento
            self.uplink = TelegramBotUplink(self)
            # Nota: Ajuste a classe TelegramBotUplink se ela esperar o token no .env
            # Se ela usar os.getenv, adicione: os.environ["TELEGRAM_TOKEN"] = self.token
            
            os.environ["TELEGRAM_TOKEN"] = self.token
            
            # Aqui entra a lógica de polling ou inicialização do bot
            # Exemplo genérico de inicialização (ajuste conforme seu telegram_uplink.py):
            # await self.uplink.run()
            
            print("🟢 [STATUS]: Link de dados ativo. Aguardando comandos do Operador.")
            
            # Mantém o script vivo no Colab
            while True:
                await asyncio.sleep(3600)
                
        except Exception as e:
            print(f"❌ [ERRO DE NÓ]: Falha na estabilização do sistema: {e}")

def main():
    # Inicializa o loop de eventos assíncronos
    core = R2Core(TOKEN_ARG)
    try:
        asyncio.run(core.iniciar())
    except KeyboardInterrupt:
        print("\n🛑 R2 SYSTEM: Protocolo de desligamento iniciado pelo Operador.")

if __name__ == "__main__":
    main()
