import threading
import asyncio
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters

# PROTEÇÃO PARA AMBIENTES SEM INTERFACE (CLOUD)
try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except (ImportError, Exception):
    PYAUTOGUI_AVAILABLE = False
    print("⚠️ [SISTEMA]: PyAutoGUI não disponível. Comandos de Hardware (Print/Volume) desativados.")

class TelegramUplink:
    def __init__(self, token, allowed_user_id, gui_instance):
        self.token = token
        self.allowed_id = int(allowed_user_id)
        self.gui = gui_instance
        self.app = None
        self.loop = None

    def iniciar_sistema(self):
        thread = threading.Thread(target=self._run_async_loop, daemon=True)
        thread.start()

    def _run_async_loop(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.app = ApplicationBuilder().token(self.token).build()

        self.app.add_handler(CommandHandler("start", self.cmd_menu)) 
        self.app.add_handler(CommandHandler("menu", self.cmd_menu))
        self.app.add_handler(CallbackQueryHandler(self.btn_handler))
        self.app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), self.handle_text))
        self.app.add_handler(MessageHandler(filters.Document.ALL, self.handle_document))

        print("📡 [TELEGRAM]: Uplink Total Ativo.")
        try: self.app.run_polling(stop_signals=None)
        except: pass

    def enviar_mensagem_ativa(self, texto):
        if self.app and self.loop:
            asyncio.run_coroutine_threadsafe(self.app.bot.send_message(chat_id=self.allowed_id, text=texto, parse_mode=None), self.loop)

    def enviar_foto_ativa(self, caminho_foto, legenda=""):
        if self.app and self.loop and os.path.exists(caminho_foto):
            asyncio.run_coroutine_threadsafe(self.app.bot.send_photo(chat_id=self.allowed_id, photo=open(caminho_foto, 'rb'), caption=legenda), self.loop)

    async def _check_auth(self, update: Update):
        if update.effective_user.id != self.allowed_id:
            await update.effective_message.reply_text("⛔ ACESSO NEGADO.")
            return False
        return True

    # =========================================================================
    # MENU PRINCIPAL (TODOS OS MÓDULOS)
    # =========================================================================
    async def cmd_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self._check_auth(update): return
        keyboard = [
            # Linha 1: Vigilância (NOVA)
            [InlineKeyboardButton("👁️ SENTINELA", callback_data='acao_cam'),
             InlineKeyboardButton("📶 SCAN REDE", callback_data='acao_netscan')],

            # Linha 2: Informação
            [InlineKeyboardButton("📡 WAR INTEL", callback_data='menu_intel'),
             InlineKeyboardButton("💰 MARKET", callback_data='acao_market')],
            
            # Linha 3: Ambiente & Radar
            [InlineKeyboardButton("🌦️ CLIMA", callback_data='menu_clima'),
             InlineKeyboardButton("✈️ RADAR ADS-B", callback_data='acao_radar')],
            
            # Linha 4: Técnicos
            [InlineKeyboardButton("⚡ SPEEDTEST", callback_data='acao_speed'),
             InlineKeyboardButton("🛰️ ISS ORBIT", callback_data='acao_iss')],
             
            # Linha 5: Controle & Sistema
            [InlineKeyboardButton("🎛️ CONTROLE PC", callback_data='menu_pc'),
             InlineKeyboardButton("📸 PRINT", callback_data='acao_print')]
        ]
        await update.message.reply_text("📟 **COMANDO CENTRAL R2 - DEFCON 1**", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

    async def btn_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        if query.from_user.id != self.allowed_id: return
        data = query.data

        # --- NAVEGAÇÃO ---
        if data == 'menu_main': await self._mostrar_menu_principal(query)
        elif data == 'menu_intel': await self._mostrar_menu_intel(query)
        elif data == 'menu_clima': await self._mostrar_menu_clima(query)
        elif data == 'menu_pc': await self._mostrar_menu_pc(query)

        # --- NOVAS AÇÕES (COMBO TRIPLO) ---
        elif data == 'acao_cam': await self._executar_no_pc("sentinela", query, "👁️ Acessando câmera...")
        elif data == 'acao_netscan': await self._executar_no_pc("escanear rede", query, "📶 Escaneando IPs...")
        elif data == 'acao_speed': await self._executar_no_pc("velocidade", query, "⚡ Testando link (Aguarde 20s)...")

        # --- AÇÕES ANTIGAS ---
        elif data == 'acao_market': await self._executar_no_pc("cotação", query, "💰 Buscando cotações...")
        elif data == 'acao_iss': await self._executar_no_pc("iss", query, "🛰️ Rastreando ISS...")
        elif data == 'acao_radar': await self._executar_no_pc("radar aereo", query, "✈️ Radar ADS-B...")
        elif data == 'acao_print': 
            await query.edit_message_text("📸 Capturando...")
            await self._enviar_print(query)

        # PC Control
        elif data == 'pc_vol_up': await self._executar_no_pc("aumentar volume", query, "🔊 +Volume")
        elif data == 'pc_vol_down': await self._executar_no_pc("baixar volume", query, "🔉 -Volume")
        elif data == 'pc_mute': await self._executar_no_pc("mutar", query, "🔇 Mute")
        elif data == 'pc_off': await self._executar_no_pc("desligar pc", query, "⚠️ Desligando...")
        elif data == 'pc_abort': await self._executar_no_pc("cancelar desligamento", query, "✅ Cancelado.")

        # Clima & Intel
        elif data.startswith('clima_'):
            cidade = data.replace('clima_', '')
            if cidade == 'digitar': await self._executar_no_pc("clima", query, "📡 Digite a cidade...")
            else: await self._executar_no_pc(f"clima {cidade}", query, f"🌤️ Clima: {cidade}...")
        elif data.startswith('intel_'):
            regiao = data.split('_')[1]
            if regiao == "mapa": await self._executar_no_pc("abrir mapa", query, "🗺️ Abrindo mapa...")
            else: await self._executar_no_pc(f"monitorar {regiao}", query, f"🛰️ Intel: {regiao}...")

    # --- MENUS ---
    async def _mostrar_menu_principal(self, query):
        # (Mesma estrutura do cmd_menu)
        keyboard = [
            [InlineKeyboardButton("👁️ SENTINELA", callback_data='acao_cam'), InlineKeyboardButton("📶 SCAN REDE", callback_data='acao_netscan')],
            [InlineKeyboardButton("📡 WAR INTEL", callback_data='menu_intel'), InlineKeyboardButton("💰 MARKET", callback_data='acao_market')],
            [InlineKeyboardButton("🌦️ CLIMA", callback_data='menu_clima'), InlineKeyboardButton("✈️ RADAR ADS-B", callback_data='acao_radar')],
            [InlineKeyboardButton("⚡ SPEEDTEST", callback_data='acao_speed'), InlineKeyboardButton("🛰️ ISS ORBIT", callback_data='acao_iss')],
            [InlineKeyboardButton("🎛️ CONTROLE PC", callback_data='menu_pc'), InlineKeyboardButton("📸 PRINT", callback_data='acao_print')]
        ]
        await query.edit_message_text("📟 **COMANDO CENTRAL R2**", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

    async def _mostrar_menu_pc(self, query):
        keyboard = [
            [InlineKeyboardButton("🔊 +VOL", callback_data='pc_vol_up'), InlineKeyboardButton("🔉 -VOL", callback_data='pc_vol_down'), InlineKeyboardButton("🔇 MUTE", callback_data='pc_mute')],
            [InlineKeyboardButton("⚠️ DESLIGAR PC", callback_data='pc_off')],
            [InlineKeyboardButton("🚫 ABORTAR", callback_data='pc_abort')],
            [InlineKeyboardButton("🔙 VOLTAR", callback_data='menu_main')]
        ]
        await query.edit_message_text("🎛️ **CONTROLE DE HARDWARE**", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

    async def _mostrar_menu_intel(self, query):
        keyboard = [
            [InlineKeyboardButton("🇺🇦 UCRÂNIA", callback_data='intel_ukraine'), InlineKeyboardButton("🇮🇱 ISRAEL", callback_data='intel_israel')],
            [InlineKeyboardButton("🇸🇾 SÍRIA", callback_data='intel_syria'), InlineKeyboardButton("🌍 GLOBAL", callback_data='intel_global')],
            [InlineKeyboardButton("🗺️ MAPA (PC)", callback_data='intel_mapa')],
            [InlineKeyboardButton("🔙 VOLTAR", callback_data='menu_main')]
        ]
        await query.edit_message_text("📡 **INTEL**", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

    async def _mostrar_menu_clima(self, query):
        keyboard = [
            [InlineKeyboardButton("🏡 NOVA ANDRADINA", callback_data='clima_nova andradina')],
            [InlineKeyboardButton("🏙️ CAMPO GRANDE", callback_data='clima_campo grande'), InlineKeyboardButton("🏖️ DOURADOS", callback_data='clima_dourados')],
            [InlineKeyboardButton("📝 DIGITAR OUTRA", callback_data='clima_digitar')],
            [InlineKeyboardButton("🔙 VOLTAR", callback_data='menu_main')]
        ]
        await query.edit_message_text("🌦️ **CLIMA**", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

    async def _executar_no_pc(self, cmd, query, msg):
        self.gui.update_queue.put(lambda: self.gui._executar_comando_remoto(cmd))
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 MENU", callback_data='menu_main')]]))

    async def _enviar_print(self, query):
        if not PYAUTOGUI_AVAILABLE:
            await query.message.reply_text("❌ Função indisponível em ambiente Cloud (Sem monitor detectado).")
            await self._mostrar_menu_principal(query)
            return

        path = "temp_screen.png"
        try:
            pyautogui.screenshot(path)
            await query.message.reply_photo(open(path, 'rb'))
            await self._mostrar_menu_principal(query)
        except: await query.message.reply_text("Erro print.")
        finally: 
            if os.path.exists(path): os.remove(path)

    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self._check_auth(update): return
        self.gui.update_queue.put(lambda: self.gui._executar_comando_remoto(update.message.text))

    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self._check_auth(update): return
        
        doc = update.message.document
        arquivo = await doc.get_file()
        caminho_final = os.path.join(self.gui.dead_drop_path, doc.file_name)
        
        await arquivo.download_to_drive(caminho_final)
        await update.message.reply_text(f"📥 **ARQUIVO RECEBIDO:** {doc.file_name}\nSalvo em: {self.gui.dead_drop_path}")
        self.gui.update_queue.put(lambda: self.gui._print_system_msg(f"📁 Dead Drop: {doc.file_name} recebido."))