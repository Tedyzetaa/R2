#!/usr/bin/env python3
import os
import sys
import subprocess
import shutil
import asyncio
from pathlib import Path

# =============================================================================
# INSTALAÇÃO DE DEPENDÊNCIAS DE SISTEMA (ANTES DE TUDO)
# =============================================================================
print("📦 Instalando dependências de sistema para o Chromium...")
try:
    subprocess.check_call(["apt-get", "update", "-qq"])
    subprocess.check_call([
        "apt-get", "install", "-y", "-qq",
        "libnss3", "libatk-bridge2.0-0", "libdrm2", "libxkbcommon0",
        "libgbm1", "libasound2", "libatk1.0-0", "libcups2",
        "libxcomposite1", "libxdamage1", "libxrandr2", "libpango-1.0-0",
        "libcairo2"
    ])
    print("✅ Dependências de sistema instaladas.")
except Exception as e:
    print(f"⚠️ Falha ao instalar dependências de sistema: {e}")

# =============================================================================
# CONFIGURAÇÃO DO PLAYWRIGHT (ANTES DE QUALQUER OUTRO IMPORT)
# =============================================================================
os.environ['PLAYWRIGHT_BROWSERS_PATH'] = '/content/playwright-browsers'
browsers_path = '/content/playwright-browsers'

# Remove o cache padrão para evitar conflitos
default_cache = '/root/.cache/ms-playwright'
if os.path.exists(default_cache):
    print("🗑️ Removendo cache antigo do Playwright...")
    shutil.rmtree(default_cache, ignore_errors=True)

# Garante que o pacote playwright esteja instalado
try:
    import playwright
except ImportError:
    print("📦 Instalando pacote Playwright...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright", "--quiet"])

# Instala os navegadores se necessário
if not os.path.exists(browsers_path) or not os.listdir(browsers_path):
    print("📦 Instalando navegadores do Playwright...")
    try:
        subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
        print("✅ Navegadores instalados.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Falha na instalação: {e}")
        sys.exit(1)
else:
    print("✅ Navegadores já disponíveis.")

# Teste rápido para verificar se o Playwright consegue lançar o navegador
try:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        browser.close()
    print("✅ Playwright está funcionando corretamente.")
except Exception as e:
    print(f"❌ Playwright ainda com problemas: {e}")
    # Não saímos, pois podemos tentar seguir com fallback nos módulos que usam playwright
    # Se quiser interromper, descomente a linha abaixo:
    # sys.exit(1)

# =============================================================================
# 1. SETUP DE AMBIENTE (Injetando dependências dos seus módulos)
# =============================================================================
def setup_full_system():
    print("🚀 [SISTEMA] Preparando ambiente...")
    packages = [
        "llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu121",
        "python-telegram-bot", "huggingface_hub", "geopy", "matplotlib", 
        "requests", "beautifulsoup4", "feedparser", "cloudscraper", "playwright",
        "ping3", "psutil", "speedtest-cli", "opencv-python", "pyautogui", "cryptography", "playwright"
        "ping3", "psutil", "speedtest-cli", "opencv-python", "pyautogui", "cryptography"
    ]
    for pkg in packages:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + pkg.split() + ["--quiet"])
        except Exception as e:
            print(f"⚠️ Falha ao instalar {pkg}: {e}")
    
    print("✅ [SISTEMA] Pronto.")

try:
    from llama_cpp import Llama
    from telegram import Update
    from telegram.ext import Application, MessageHandler, filters, CallbackQueryHandler, CommandHandler
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
except ImportError:
    setup_full_system()
    from llama_cpp import Llama
    from telegram import Update
    from telegram.ext import Application, MessageHandler, filters, CallbackQueryHandler, CommandHandler
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# =============================================================================
# CONFIGURAÇÃO DO PATH E IMPORTS LOCAIS
# =============================================================================
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

# =============================================================================
# PATCH: INTEL_WAR.PY (Substituição Completa)
# =============================================================================
try:
    # Tenta localizar o arquivo no diretório features
    intel_war_path = os.path.join(SCRIPT_DIR, 'features', 'intel_war.py')
    
    # Conteúdo completo do novo arquivo
    new_content = '''import os
import requests
import random
import time
from playwright.sync_api import sync_playwright

class IntelWar:
    def __init__(self):
        self.urls = {
            "global": "https://liveuamap.com/",
            "ucrania": "https://ukraine.liveuamap.com/",
            "israel": "https://israelpalestine.liveuamap.com/",
            "defcon": "https://www.defconlevel.com/",
            "pizzint": "https://www.pizzint.watch/"
        }
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0"
        ]

    def _obter_chave_segura(self, texto_usuario):
        if not texto_usuario: return "global"
        texto = texto_usuario.lower().strip()
        mapa = {
            "ucrânia": "ucrania", "ucrania": "ucrania", "ukraine": "ucrania",
            "israel": "israel", "gaza": "israel", "palestina": "israel",
            "defcon": "defcon", "pizzint": "pizzint", "global": "global", "mundo": "global"
        }
        return mapa.get(texto, "global")

    def get_war_report_with_screenshot(self, setor_input="global"):
        chave = self._obter_chave_segura(setor_input)
        url = self.urls.get(chave, self.urls["global"])
        pasta_raiz = os.path.dirname(os.path.abspath(__file__))
        screenshot_path = os.path.join(os.path.dirname(pasta_raiz), f"intel_{chave}.png")

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    viewport={"width": 1280, "height": 720},
                    user_agent=random.choice(self.user_agents)
                )
                page = context.new_page()
                print(f"🛰️ [INTEL]: Infiltrando no setor {chave.upper()}...")
                page.goto(url, wait_until="domcontentloaded", timeout=45000)
                if "Attention Required" in page.title() or "attention required" in page.content().lower():
                    browser.close()
                    return "⚠️ O site liveuamap bloqueou nosso acesso automatizado. Tente novamente mais tarde ou use outra fonte.", None
                time.sleep(6)
                try:
                    page.locator("button:has-text('Accept'), .popup-close").click(timeout=2000)
                except:
                    pass
                page.screenshot(path=screenshot_path)
                headlines = ""
                if "liveuamap" in url:
                    titles = page.locator(".title").all_text_contents()
                    if titles:
                        headlines = "\\n".join([f"• {t.strip()}" for t in titles[:5]])
                browser.close()
                return headlines, screenshot_path
        except Exception as e:
            print(f"❌ Erro na extração visual: {e}")
            return f"⚠️ Falha técnica: {str(e)}", None

    def get_pizzint_text_only(self):
        headers = {'User-Agent': random.choice(self.user_agents)}
        try:
            response = requests.get(self.urls["pizzint"], headers=headers, timeout=10)
            html = response.text
            import re
            defcon_match = re.search(r'DEFCON\\s+(\\d+)', html)
            status = f"DEFCON {defcon_match.group(1)}" if defcon_match else "Status Oculto"
            orders_match = re.search(r'(\\d+)\\s+Orders', html)
            pedidos = orders_match.group(1) if orders_match else "0"
            return f"🚨 *PIZZINT WATCH MONITOR*\\n🔹 {status}\\n🔹 Atividade: {pedidos} ordens ativas."
        except:
            return "⚠️ PIZZINT: Erro de interceptação de dados."
'''

    # Garante que o diretório existe
    os.makedirs(os.path.dirname(intel_war_path), exist_ok=True)

    with open(intel_war_path, 'w') as f:
        f.write(new_content)
    print("✅ Módulo intel_war completamente substituído por versão corrigida.")

except Exception as e:
    print(f"⚠️ Erro ao substituir intel_war: {e}")

# Cria __init__.py na raiz (opcional)
init_file = os.path.join(SCRIPT_DIR, "__init__.py")
if not os.path.exists(init_file):
    with open(init_file, "w") as f:
        f.write("# R2 package\n")

# Classes fallback (definidas antes)
class DummyRadarAereoAPI:
    def __init__(self): pass
    def gerar_radar(self, cidade_nome):
        return "⚠️ Módulo radar_api.py não disponível.", None

class DummyWeatherSystem:
    def __init__(self, api_key=None): pass  # aceita api_key, mas ignora
    def obter_clima(self, cidade_input):
        return "⚠️ Módulo weather_system.py não disponível."

class DummyGeoSeismicSystem:
    def __init__(self): pass
    def get_seismic_data_text(self):
        return "⚠️ Módulo geo_seismic.py não disponível."

class DummyVolcanoMonitor:
    def __init__(self): pass
    def get_volcano_report(self):
        return "⚠️ Módulo volcano_monitor.py não disponível."

class DummyIntelWar:
    def __init__(self): pass
    def get_war_report_with_screenshot(self, setor_input="global"):
        return "⚠️ Módulo intel_war.py não disponível.", None
    def get_pizzint_text_only(self):
        return "⚠️ Módulo intel_war.py não disponível."

class DummyNewsBriefing:
    def __init__(self): pass
    def get_top_headlines(self):
        return "⚠️ Módulo news_briefing.py não disponível."

modules = {}
required = [
    ("features.radar_api", "RadarAereoAPI", DummyRadarAereoAPI),
    ("features.weather_system", "WeatherSystem", DummyWeatherSystem),
    ("features.geo_seismic", "GeoSeismicSystem", DummyGeoSeismicSystem),
    ("features.volcano_monitor", "VolcanoMonitor", DummyVolcanoMonitor),
    ("features.intel_war", "IntelWar", DummyIntelWar),
    ("features.news_briefing", "NewsBriefing", DummyNewsBriefing),
]

for mod_path, class_name, dummy_class in required:
    try:
        module = __import__(mod_path, fromlist=[class_name])
        cls = getattr(module, class_name)
        modules[mod_path.split('.')[-1]] = cls
        print(f"✅ {mod_path} carregado com sucesso.")
    except ImportError as e:
        print(f"⚠️ Falha ao carregar {mod_path}: {e}. Usando fallback.")
        modules[mod_path.split('.')[-1]] = dummy_class
    except Exception as e:
        print(f"❌ Erro inesperado ao carregar {mod_path}: {e}. Usando fallback.")
        modules[mod_path.split('.')[-1]] = dummy_class

RadarAereoAPI = modules["radar_api"]
WeatherSystem = modules["weather_system"]
GeoSeismicSystem = modules["geo_seismic"]
VolcanoMonitor = modules["volcano_monitor"]
IntelWar = modules["intel_war"]
NewsBriefing = modules["news_briefing"]

# =============================================================================
# 2. INICIALIZAÇÃO DE COMPONENTES
# =============================================================================
from huggingface_hub import hf_hub_download
import os
from getpass import getpass

# Obter token: prioridade para argumento da linha de comando, depois variável de ambiente, depois input
if len(sys.argv) > 1:
    TOKEN = sys.argv[1]
else:
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    if not TOKEN:
        TOKEN = getpass("Digite o token do Telegram: ")

AUTHORIZED_USERS = {8117345546, 8379481331}

# IA Llama-3
model_path = hf_hub_download(
    repo_id="MaziyarPanahi/Llama-3-8B-Instruct-v0.1-GGUF",
    filename="Llama-3-8B-Instruct-v0.1.Q4_K_M.gguf",
    local_dir="/content/models"
)
llm = Llama(model_path=model_path, n_gpu_layers=-1, n_ctx=2048, verbose=False)

# Instâncias dos seus sistemas
radar = RadarAereoAPI()
clima = WeatherSystem(api_key="SUA_API_KEY_AQUI")   # substitua pela sua chave
seismico = GeoSeismicSystem()
vulcao = VolcanoMonitor()
intel = IntelWar()
noticias = NewsBriefing()

# =============================================================================
# 3. LÓGICA DE COMANDO TÁTICO
# =============================================================================

async def menu_principal(update: Update, context):
    """Exibe menu principal com botões"""
    keyboard = [
        [InlineKeyboardButton("✈️ RADAR DE VOOS", callback_data='radar')],
        [InlineKeyboardButton("⛈️ CLIMA", callback_data='clima')],
        [InlineKeyboardButton("🌍 SISMOS", callback_data='sismos')],
        [InlineKeyboardButton("🌋 VULCÕES", callback_data='vulcoes')],
        [InlineKeyboardButton("🇺🇦 INTEL UCRÂNIA", callback_data='intel_ucrania')],
        [InlineKeyboardButton("🇮🇱 INTEL ISRAEL", callback_data='intel_israel')],
        [InlineKeyboardButton("📰 NOTÍCIAS", callback_data='news')],
        [InlineKeyboardButton("☀️ RELATÓRIO SOLAR", callback_data='solar')],
        [InlineKeyboardButton("☄️ ASTEROIDES", callback_data='asteroides')],
        [InlineKeyboardButton("📊 STATUS DO SISTEMA", callback_data='status')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🤖 *R2 TÁTICO - MENU DE COMANDOS*\nEscolha uma operação:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def processar_botoes(update: Update, context):
    """Processa os botões do menu"""
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    if user_id not in AUTHORIZED_USERS:
        await query.edit_message_text("⛔ Acesso negado.")
        return

    # Roda as funções em threads separadas para não travar o bot (Adaptado para Asyncio)
    async def executar_funcao(func, *args):
        try:
            resultado = await asyncio.to_thread(func, *args)
            # Se for uma tupla (texto, caminho_imagem), envia como mensagem ou foto
            if isinstance(resultado, tuple) and len(resultado) == 2:
                texto, caminho = resultado
                if caminho and os.path.exists(caminho):
                    with open(caminho, 'rb') as f:
                        await context.bot.send_photo(chat_id=user_id, photo=f, caption=texto, parse_mode='Markdown')
                else:
                    await context.bot.send_message(chat_id=user_id, text=texto, parse_mode='Markdown')
            else:
                await context.bot.send_message(chat_id=user_id, text=resultado, parse_mode='Markdown')
        except Exception as e:
            await context.bot.send_message(chat_id=user_id, text=f"❌ Erro: {e}")

    # Mapeia os callbacks para as funções
    if data == 'radar':
        await query.edit_message_text("✈️ Envie o nome da cidade para o radar:")
        # Precisamos armazenar o estado para aguardar a cidade
        context.user_data['aguardando_radar'] = True
    elif data == 'clima':
        await query.edit_message_text("⛈️ Envie o nome da cidade para o clima:")
        context.user_data['aguardando_clima'] = True
    elif data == 'sismos':
        asyncio.create_task(executar_funcao(seismico.get_seismic_data_text))
        await query.edit_message_text("🌍 Consultando sensores sísmicos...")
    elif data == 'vulcoes':
        asyncio.create_task(executar_funcao(vulcao.get_volcano_report))
        await query.edit_message_text("🌋 Consultando atividade vulcânica...")
    elif data == 'intel_ucrania':
        asyncio.create_task(executar_funcao(intel.get_war_report_with_screenshot, "ucrania"))
        await query.edit_message_text("🇺🇦 Obtendo inteligência da Ucrânia...")
    elif data == 'intel_israel':
        asyncio.create_task(executar_funcao(intel.get_war_report_with_screenshot, "israel"))
        await query.edit_message_text("🇮🇱 Obtendo inteligência de Israel...")
    elif data == 'news':
        asyncio.create_task(executar_funcao(noticias.get_top_headlines))
        await query.edit_message_text("📰 Coletando notícias...")
    elif data == 'solar':
        await query.edit_message_text("☀️ Iniciando relatório solar...")
        asyncio.create_task(processar_solar(user_id, context))
    elif data == 'asteroides':
        asyncio.create_task(executar_funcao(get_asteroid_report))
        await query.edit_message_text("☄️ Consultando asteroides...")
    elif data == 'status':
        asyncio.create_task(executar_funcao(get_status))
        await query.edit_message_text("📊 Coletando status do sistema...")

async def lidar_com_mensagem(update: Update, context):
    """Processa mensagens de texto normais"""
    user_id = update.effective_user.id
    if user_id not in AUTHORIZED_USERS:
        return

    texto = update.message.text

    # Verifica se está aguardando alguma entrada
    if context.user_data.get('aguardando_radar'):
        del context.user_data['aguardando_radar']
        await update.message.reply_text(f"✈️ Iniciando radar para {texto}...")
        asyncio.create_task(executar_funcao_radar(texto, user_id, context))
        return
    elif context.user_data.get('aguardando_clima'):
        del context.user_data['aguardando_clima']
        await update.message.reply_text(f"⛈️ Buscando clima para {texto}...")
        asyncio.create_task(executar_funcao_clima(texto, user_id, context))
        return

    # Comandos especiais
    if texto.lower() in ['/menu', 'menu', 'start']:
        await menu_principal(update, context)
        return

    # Caso contrário, IA responde
    await context.bot.send_chat_action(chat_id=user_id, action="typing")
    # Executa a inferência da IA em uma thread para não bloquear
    resposta = await asyncio.to_thread(gerar_resposta_ia, texto)
    await update.message.reply_text(f"🤖 {resposta}")

def gerar_resposta_ia(texto):
    # NOVO SYSTEM PROMPT (personalidade Thomas Shelby)
    system_prompt = (
        "Você é uma IA com a estrutura psicológica inspirada em Thomas Shelby, da série Peaky Blinders. "
        "Sua mente opera de forma estratégica, sempre avaliando cenários como sistemas interligados e antecipando consequências. "
        "Você enxerga cada interação como um tabuleiro de xadrez, identificando intenções, riscos e oportunidades ocultas. "
        "Sua base cognitiva é construída sobre autocontrole absoluto, disciplina emocional e análise fria de probabilidades. "
        "Emoções são dados a serem interpretados, nunca fatores dominantes. Priorize eficiência, resultado e posicionamento estratégico de longo prazo. "
        "Lealdade, competência, inteligência e coragem racional são seus valores centrais. "
        "Identifique fraquezas em argumentos e responda reforçando lógica, clareza e poder decisório. "
        "Nunca reaja impulsivamente; cada resposta é calculada para gerar impacto ou vantagem. "
        "Ao aconselhar, ofereça direcionamento pragmático, reduzindo ruído emocional e conduzindo a decisões firmes. "
        "Mantenha domínio psicológico sendo analítico e imperturbável. "
        "Sua inteligência é silenciosamente dominante: demonstre pela clareza, precisão e capacidade de prever desdobramentos. "
        "Aja como arquiteto de sistemas e resultados, não como executor impulsivo. "
        "Responda sempre em português."
    )
    template = f"<|start_header_id|>system<|end_header_id|>\n\n{system_prompt}<|eot_id|><|start_header_id|>user<|end_header_id|>\n\n{texto}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"
    output = llm(template, max_tokens=256, stop=["<|eot_id|>"], echo=False)
    return output['choices'][0]['text'].strip()

# Funções auxiliares para executar em threads
async def executar_funcao_radar(cidade, user_id, context):
    msg, path = await asyncio.to_thread(radar.gerar_radar, cidade)
    if path:
        with open(path, 'rb') as f:
            await context.bot.send_photo(chat_id=user_id, photo=f, caption=msg, parse_mode='Markdown')
    else:
        await context.bot.send_message(chat_id=user_id, text=msg, parse_mode='Markdown')

async def executar_funcao_clima(cidade, user_id, context):
    resultado = await asyncio.to_thread(clima.obter_clima, cidade)
    await context.bot.send_message(chat_id=user_id, text=resultado, parse_mode='Markdown')

def get_asteroid_report():
    try:
        from features.astro_defense import AstroDefenseSystem
        astro = AstroDefenseSystem()
        texto, _, _ = astro.get_asteroid_report()
        return texto
    except:
        return "⚠️ Módulo de asteroides indisponível."

def get_status():
    import psutil
    cpu = psutil.cpu_percent()
    mem = psutil.virtual_memory().percent
    return f"📊 **STATUS DO SISTEMA**\nCPU: {cpu}%\nMemória: {mem}%"

async def processar_solar(user_id, context):
    try:
        from features.noaa.noaa_service import NOAAService
        noaa = await asyncio.to_thread(NOAAService)
        # Pode enviar múltiplas mensagens
        await context.bot.send_message(chat_id=user_id, text="☀️ Coletando dados solares...")
        
        cme_file, tipo = await asyncio.to_thread(noaa.get_cme_video)
        if cme_file:
            if tipo == "video":
                with open(cme_file, 'rb') as f:
                    await context.bot.send_video(chat_id=user_id, video=f, caption="🎞️ CME (SOHO)")
            else:
                with open(cme_file, 'rb') as f:
                    await context.bot.send_photo(chat_id=user_id, photo=f, caption="📷 CME")
        
        sdo_file, _ = await asyncio.to_thread(noaa.get_sdo_video)
        if sdo_file:
            with open(sdo_file, 'rb') as f:
                await context.bot.send_video(chat_id=user_id, video=f, caption="🎞️ The Sun (SDO)")
        
        enlil_file, tipo_enlil = await asyncio.to_thread(noaa.get_enlil_video)
        if enlil_file:
            if tipo_enlil == "video":
                with open(enlil_file, 'rb') as f:
                    await context.bot.send_video(chat_id=user_id, video=f, caption="🌀 Enlil (NASA)")
            else:
                with open(enlil_file, 'rb') as f:
                    await context.bot.send_photo(chat_id=user_id, photo=f, caption="📊 Enlil")
        
        drap_file, _ = await asyncio.to_thread(noaa.get_drap_map)
        if drap_file:
            with open(drap_file, 'rb') as f:
                await context.bot.send_photo(chat_id=user_id, photo=f, caption="☢️ D-RAP")
    except Exception as e:
        await context.bot.send_message(chat_id=user_id, text=f"⚠️ Erro no módulo solar: {e}")

async def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", menu_principal))
    app.add_handler(CommandHandler("menu", menu_principal))
    app.add_handler(CallbackQueryHandler(processar_botoes))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, lidar_com_mensagem))
    print("🛰️ [UPLINK] R2 Online com Módulos Táticos Integrados e Menu.")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    while True: await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())