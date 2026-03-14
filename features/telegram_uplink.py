import os
import asyncio
import threading
import time
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler

# --- 1. CARREGAMENTO AUTOMÁTICO DE CREDENCIAIS (.ENV) ---
# Detecta a pasta raiz (C:\R2) independente de onde o script é chamado
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
env_path = os.path.join(root_dir, '.env')

load_dotenv(env_path)
TOKEN = os.getenv("TELEGRAM_TOKEN")

# --- 2. PROTOCOLO DE SEGURANÇA ---
# Seus IDs autorizados
AUTHORIZED_USERS = {8117345546, 8379481331} 

class TelegramBotUplink:
    def __init__(self, server_ref):
        self.server_ref = server_ref  # Referência ao cérebro (r2_server.py)
        self.core = server_ref         # <--- ESTA LINHA É VITAL! Ela salva o core no objeto.
        self.loop = asyncio.new_event_loop()
        self.thread = None
        self.app = None
        self.token = TOKEN              # Armazena o token globalmente no objeto

        # Verificação de segurança na inicialização
        if not self.token:
            print(f"❌ [ERRO CRÍTICO]: Token não encontrado em {env_path}")
            print("💡 Certifique-se de ter um arquivo .env na pasta raiz (C:\\R2) com a chave TELEGRAM_TOKEN.")
            raise ValueError("Token ausente. Configure o arquivo .env")

        self.update_queue = None

    def iniciar_sistema(self):
        if self.thread and self.thread.is_alive():
            return

        def run_bot():
            asyncio.set_event_loop(self.loop)

            # --- 🛡️ CONFIGURAÇÃO DE ALTA DISPONIBILIDADE ---
            self.app = (
                Application.builder()
                .token(self.token)
                .connect_timeout(30)
                .read_timeout(30)
                .write_timeout(30)
                .pool_timeout(30)
                .build()
            )

            # Handlers (Ouvidos do Bot)
            self.app.add_handler(CommandHandler("start", self.start_command))
            self.app.add_handler(CallbackQueryHandler(self.lidar_com_botoes))
            self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.lidar_com_mensagem))

            # Vincula a fila de updates ao core para evitar o erro de 'update_queue'
            # Isso espelha a fila de updates para o Core, resolvendo o erro de atributo
            self.server_ref.update_queue = self.app.update_queue

            # Tratamento de erros de rede
            self.app.add_error_handler(self.error_handler)

            print("📡 [TELEGRAM]: Uplink Total Ativo com Interface de Botões.")

            # Polling Resiliente (Não para se a internet cair)
            self.loop.run_until_complete(
                self.app.run_polling(
                    drop_pending_updates=True,
                    close_loop=False,
                    stop_signals=None
                )
            )

        self.thread = threading.Thread(target=run_bot, daemon=True)
        self.thread.start()

    # --- GERENCIADOR DE ERROS DE REDE ---
    async def error_handler(self, update, context):
        """Evita que o bot crash por oscilação de internet"""
        print(f"⚠️ [TELEGRAM ERROR]: {context.error}")
        # Ignora erros de conexão passageiros
        if "httpx" in str(context.error) or "Network" in str(context.error):
            pass

    # --- MENU TÁTICO ---
    async def start_command(self, update: Update, context):
        uid = update.effective_user.id
        if uid in AUTHORIZED_USERS:
            # Seus botões personalizados
            keyboard = [
                [InlineKeyboardButton("☀️ RELATÓRIO SOLAR COMPLETO", callback_data='solar')],
                [InlineKeyboardButton("☄️ RASTREADOR DE ASTEROIDES (NASA)", callback_data='asteroides')],
                [InlineKeyboardButton("✈️ RADAR DE VOOS (API 200KM)", callback_data='pedir_voos')],
                [InlineKeyboardButton("⛈️ RADAR DE CHUVA (POR CIDADE)", callback_data='pedir_cidade')],
                [InlineKeyboardButton("☢️ NÍVEL DE ALERTA: DEFCON", callback_data='defcon')],
                [InlineKeyboardButton("🌍 MONITOR SÍSMICO (TERREMOTOS)", callback_data='terremotos')],
                [InlineKeyboardButton("🌋 ALERTA VULCÂNICO (MAGMA)", callback_data='vulcao')],
                [InlineKeyboardButton("🇺🇦 INTEL: FRONT UCRÂNIA", callback_data='intel ucrania')],
                [InlineKeyboardButton("🇮🇱 INTEL: FRONT ISRAEL", callback_data='intel israel')],
                [InlineKeyboardButton("🚨 BREAKING NEWS (CONFLITOS)", callback_data='intel_news')],
                [InlineKeyboardButton("💻 STATUS DO SISTEMA (PC)", callback_data='status')],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                "🤖 *R2 ASSISTANT - CONSOLE DE COMANDO*\nSelecione uma operação tática abaixo:",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text("⛔ ACESSO NEGADO.")

    # --- PROCESSADOR DE BOTÕES ---
    async def lidar_com_botoes(self, update: Update, context):
        query = update.callback_query
        user_id = query.from_user.id
        comando = query.data

        try:
            await query.answer()
        except:
            pass

        if user_id in AUTHORIZED_USERS:
            print(f"🔘 Botão pressionado por {user_id}: {comando}")

            # MODO CORRETO: Enviar dicionário para a fila do loop principal
            # O método put_nowait não pausa e não espera. O Telegram não pode travar.
            self.core.main_loop.call_soon_threadsafe(
                self.core.command_queue.put_nowait,

                lambda: self.server_ref.processar_comando_remoto(comando, sender_id=user_id)
            )
        else:
            try:
                await query.edit_message_text("⛔ Não autorizado.")
            except:
                pass

    # --- PROCESSADOR DE MENSAGENS DE TEXTO ---
    async def lidar_com_mensagem(self, update: Update, context):
        user_id = update.effective_user.id
        if user_id in AUTHORIZED_USERS:
            texto = update.message.text
            # Envia texto para o servidor (ex: nome de cidade)
            # MODO CORRETO: Enviar dicionário para a fila do loop principal
            self.core.main_loop.call_soon_threadsafe(
                self.core.command_queue.put_nowait,
                lambda: self.server_ref.processar_comando_remoto(texto, sender_id=user_id)
            )

    # --- ENVIOS ATIVOS (Server -> Telegram) ---
    def enviar_mensagem_ativa(self, texto, target_chat_id):
        if not self.app:
            return

        async def send():
            try:
                await self.app.bot.send_message(
                    chat_id=target_chat_id,
                    text=texto,
                    parse_mode='Markdown'
                )
            except Exception as e:
                print(f"❌ Erro envio msg: {e}")

        asyncio.run_coroutine_threadsafe(send(), self.loop)

    def enviar_foto_ativa(self, file_path, legenda="", target_chat_id=None):
        if not self.app:
            return

        async def send():
            for tentativa in range(3):
                try:
                    if os.path.exists(file_path):
                        with open(file_path, 'rb') as f:
                            # Detecta se é GIF ou Foto
                            if file_path.lower().endswith('.gif'):
                                await self.app.bot.send_animation(
                                    chat_id=target_chat_id,
                                    animation=f,
                                    caption=legenda
                                )
                            else:
                                await self.app.bot.send_photo(
                                    chat_id=target_chat_id,
                                    photo=f,
                                    caption=legenda
                                )
                        break
                    else:
                        print(f"⚠️ Arquivo sumiu: {file_path}")
                        break
                except PermissionError:
                    await asyncio.sleep(1)
                except Exception as e:
                    print(f"❌ Erro envio mídia: {e}")
                    break

        asyncio.run_coroutine_threadsafe(send(), self.loop)