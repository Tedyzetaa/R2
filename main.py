import os
import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler

# --- IMPORTAÇÃO DOS MÓDULOS TÁTICOS ---
from features.air_traffic import AirTrafficControl
from features.weather_system import WeatherSystem
from features.volcano_monitor import VolcanoMonitor
from features.astro_defense import AstroDefenseSystem
from features.geo_seismic import GeoSeismicSystem
from features.intel_war import IntelWar
from features.market_system import MarketSystem
from features.image_gen import gerar_imagem  # O comando simplificado

# Configuração de Logs
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- CONFIGURAÇÕES ---
AUTHORIZED_USERS = {8117345546, 8379481331}
WEATHER_API_KEY = "8db4b830d939639535698f1211e0e980"

# Inicialização de Instâncias
radar = AirTrafficControl()
clima = WeatherSystem(WEATHER_API_KEY)
volcano = VolcanoMonitor()
astro = AstroDefenseSystem()
geo = GeoSeismicSystem()
intel = IntelWar()
market = MarketSystem()

async def start(update: Update, context):
    if update.effective_user.id not in AUTHORIZED_USERS: return
    
    keyboard = [
        [InlineKeyboardButton("✈️ RADAR AÉREO", callback_data='radar'), InlineKeyboardButton("⛈️ CLIMA MS", callback_data='clima')],
        [InlineKeyboardButton("☄️ ASTRO DEFENSE", callback_data='astro'), InlineKeyboardButton("🌋 VULCÕES", callback_data='volcao')],
        [InlineKeyboardButton("🌍 GEOPOLÍTICA/GUERRA", callback_data='intel'), InlineKeyboardButton("📈 MERCADO", callback_data='market')],
        [InlineKeyboardButton("🆘 STATUS DO SISTEMA", callback_data='status')]
    ]
    
    await update.message.reply_text(
        "--- 🖥️ CONSOLE R2: OPERACIONAL ---\n"
        "Comandos táticos carregados. Use /gerar_imagem para renderização.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_callback(update: Update, context):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if query.data == 'radar':
        await query.edit_message_text("📡 Digite a cidade para varredura de radar:")
        context.user_data['esperando'] = 'radar'
    
    elif query.data == 'clima':
        await query.edit_message_text("🌦️ Digite a cidade para telemetria climática:")
        context.user_data['esperando'] = 'clima'

    elif query.data == 'astro':
        report, target_id, _ = astro.get_asteroid_report()
        await query.message.reply_text(report, parse_mode='Markdown')

    elif query.data == 'volcao':
        res = volcano.get_volcano_report()
        await query.message.reply_text(res, parse_mode='Markdown')

    elif query.data == 'intel':
        msg, img_path = intel.extrair_visual("global") # Padrão global
        if img_path: await query.message.reply_photo(photo=open(img_path, 'rb'), caption=msg)
        else: await query.message.reply_text(msg)

    elif query.data == 'market':
        await query.message.reply_text(market.obter_cotacoes(), parse_mode='Markdown')

async def cmd_gerar_imagem(update: Update, context):
    if update.effective_user.id not in AUTHORIZED_USERS: return
    
    prompt = " ".join(context.args)
    if not prompt:
        await update.message.reply_text("❌ Uso correto: `/gerar_imagem [descrição da foto]`")
        return

    # Adiciona gatilhos de qualidade automaticamente
    prompt_full = f"High quality, realistic, 8k, detailed, {prompt}"
    await update.message.reply_text(f"🎨 **Iniciando renderização:**\n_{prompt}_", parse_mode='Markdown')
    
    try:
        path = gerar_imagem(prompt_full)
        await update.message.reply_photo(photo=open(path, 'rb'), caption=f"✅ Renderização concluída: {prompt}")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Erro no módulo de imagem: {e}")

async def processar_texto(update: Update, context):
    if update.effective_user.id not in AUTHORIZED_USERS: return
    
    esperando = context.user_data.get('esperando')
    texto = update.message.text

    if esperando == 'radar':
        path, _, msg = radar.radar_scan(texto)
        if path: await update.message.reply_photo(photo=open(path, 'rb'), caption=msg)
        else: await update.message.reply_text(msg)
        context.user_data['esperando'] = None
    
    elif esperando == 'clima':
        res = clima._gerar_tentativas(texto)
        await update.message.reply_text(res)
        context.user_data['esperando'] = None

# --- MAIN ---
def main():
    token = "TEU_TOKEN_AQUI"
    app = Application.builder().token(token).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("gerar_imagem", cmd_gerar_imagem))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, processar_texto))
    
    print("🚀 R2 SYSTEM ONLINE: Todos os módulos integrados.")
    app.run_polling()

if __name__ == "__main__":
    main()
