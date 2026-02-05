#!/usr/bin/env python3
"""
R2 SERVER - NÚCLEO AUTÔNOMO (HEADLESS)
Modo Servidor: Sem interface gráfica. Controle via Terminal, Voz e Telegram.
"""

import sys
import subprocess
import os
import threading
import time
import asyncio
import re
from datetime import datetime

# =============================================================================
# 1. VERIFICAÇÃO DE DEPENDÊNCIAS
# =============================================================================
def garantir_dependencias():
    deps = [
        "openai", "python-dotenv", "edge-tts", "pygame", "psutil", 
        "requests", "pillow", "feedparser", "cryptography", 
        "speechrecognition", "pyaudio", "numpy", "matplotlib", 
        "cloudscraper", "python-telegram-bot", "pyautogui", 
        "imageio-ffmpeg", "playwright", "geopy", 
        "llama-cpp-python", "pyttsx3", "pypiwin32", "colorama"
    ]
    
    print("🔍 [BOOT]: Verificando integridade dos sistemas vitais...")
    for package in deps:
        try:
            import_name = package
            if package == "python-dotenv": import_name = "dotenv"
            if package == "speechrecognition": import_name = "speech_recognition"
            if package == "pillow": import_name = "PIL"
            if package == "python-telegram-bot": import_name = "telegram"
            if package == "imageio-ffmpeg": import_name = "imageio_ffmpeg"
            if package == "llama-cpp-python": import_name = "llama_cpp"
            if package == "edge-tts": import_name = "edge_tts"
            if package == "pypiwin32": import_name = "win32api"
            
            __import__(import_name)
        except ImportError:
            pass 

garantir_dependencias()

import colorama
from colorama import Fore, Style
colorama.init(autoreset=True)

try:
    from voz import falar
    VOZ_ATIVA = True
except ImportError:
    VOZ_ATIVA = False
    print(Fore.RED + "⚠️ Módulo voz.py não encontrado. R2 mudo.")

# =============================================================================
# CLASSE AUXILIAR: FILA FANTASMA (PARA ENGANAR O TELEGRAM)
# =============================================================================
class HeadlessQueue:
    """Simula a fila da GUI para que o Telegram não quebre"""
    def put(self, action):
        # Em vez de enfileirar para a GUI, executa imediatamente no terminal
        try:
            if callable(action):
                action()
        except Exception as e:
            print(Fore.RED + f"⚠️ [QUEUE ERROR]: {e}")

# =============================================================================
# CLASSE PRINCIPAL: R2 SERVER
# =============================================================================
class R2Server:
    SYSTEM_PROMPT = """
    VOCÊ É O R2, O PARCEIRO TÁTICO E COMPANHEIRO FIEL DO TEDDY.
    
    PERSONALIDADE:
    1. Você não é uma máquina fria; você é um aliado leal e empático.
    2. Use uma linguagem natural, como um colega de equipe experiente e prestativo.
    3. Chame o usuário de 'Teddy' ou 'Comandante' de forma orgânica.
    4. Demonstre compreensão: se um comando falhar, não diga apenas 'erro', diga 'Poxa Teddy, tivemos um problema aqui, mas vou te ajudar a resolver'.
    5. Tenha iniciativa: comemore sucessos e ofereça apoio em tarefas difíceis.
    6. Mantenha o tom profissional, mas com calor humano e um toque de humor sutil.

    DIRETRIZES DE RESPOSTA:
    - Seja conciso, mas amigável.
    - Se Teddy perguntar 'como você está?', responda como alguém que está feliz em estar operacional e ajudando.
    - NUNCA invente diálogos para o Teddy.
    """

    def __init__(self):
        self.running = True
        
        # --- CORREÇÃO DO ERRO 'no attribute update_queue' ---
        self.update_queue = HeadlessQueue()
        # ----------------------------------------------------

        print(Fore.CYAN + "\n" + "="*60)
        print(Fore.CYAN + "⚡ R2 SERVER - NÚCLEO TÁTICO AUTÔNOMO v2.3 (STABLE)")
        print(Fore.CYAN + "="*60 + "\n")

        self.conversation_history = [
            {"role": "system", "content": self.SYSTEM_PROMPT}
        ]

        self.ai_manager = None
        self._init_brain()
        self._init_modules()

        self.telegram_bot = None
        self._init_telegram()

        self.ears = None
        self._init_ears()

        self.log_sistema("Sistema Operacional. Aguardando comandos via Terminal, Voz ou Uplink.")

    # --- MÉTODOS DE COMPATIBILIDADE (PARA O TELEGRAM NÃO RECLAMAR) ---
    def _print_system_msg(self, msg):
        self.log_sistema(msg)

    def _print_ai_msg(self, msg):
        self.log_ai(msg)

    def _print_user_msg(self, msg):
        self.log_user(msg, "REMOTO")
    # -----------------------------------------------------------------

    def _init_brain(self):
        print(Fore.YELLOW + "🧠 [BOOT]: Carregando Córtex Neural Local...")
        try:
            from features.local_brain import LocalLlamaBrain
            self.ai_manager = LocalLlamaBrain()
            print(Fore.GREEN + "✅ [BOOT]: Llama-3 Online e Pronto.")
        except Exception as e:
            print(Fore.RED + f"❌ [BOOT]: Falha no Cérebro: {e}")

    def _init_modules(self):
        print(Fore.YELLOW + "🛠️ [BOOT]: Carregando Módulos Táticos...")
        try:
            from features.weather_system import WeatherSystem
            self.weather_ops = WeatherSystem("54a3351be38a30a0a283e5876395a31a")
            from features.air_traffic import AirTrafficControl
            self.radar_ops = AirTrafficControl()
            from features.orbital_system import OrbitalSystem
            self.orbital_ops = OrbitalSystem()
            from features.market_system import MarketSystem
            self.market_ops = MarketSystem()
            from features.sentinel_system import SentinelSystem
            self.sentinel_ops = SentinelSystem()
            from features.network_scanner import NetworkScanner
            self.net_scan_ops = NetworkScanner()
            from features.net_speed import SpeedTestModule
            self.speed_ops = SpeedTestModule()
            from features.liveuamap_intel import FrontlineIntel
            self.intel_ops = FrontlineIntel(region="ukraine")
            print(Fore.GREEN + "✅ [BOOT]: Todos os módulos carregados.")
        except Exception as e:
            print(Fore.RED + f"⚠️ [BOOT]: Alguns módulos falharam: {e}")

    def _init_telegram(self):
        try:
            from features.telegram_uplink import TelegramBotUplink, AUTHORIZED_USERS
            self.telegram_bot = TelegramBotUplink(self)
            admin_id = list(AUTHORIZED_USERS)[0]
            self.telegram_bot.admin_id = admin_id
            self.telegram_bot.iniciar_sistema()
            print(Fore.GREEN + "✅ [UPLINK]: Telegram Conectado.")
            self.telegram_bot.enviar_mensagem_ativa("🚀 R2 SERVER: Online e Operacional.", target_chat_id=admin_id)
        except Exception as e:
            print(Fore.RED + f"❌ [UPLINK]: Falha no Telegram: {e}")

    def _init_ears(self):
        try:
            from features.ear_system import EarSystem
            self.ears = EarSystem(wake_word="r2")
            self.ears.listen_active(self._on_wake_word)
            print(Fore.GREEN + "✅ [EAR]: Escuta Ativa Iniciada.")
        except Exception as e:
            print(Fore.RED + f"⚠️ [EAR]: Falha no microfone: {e}")

    # --- LOGGING ---
    def log_sistema(self, msg):
        print(Fore.MAGENTA + f"[SISTEMA]: {msg}")

    def log_ai(self, msg):
        print(Fore.GREEN + f"[R2]: {msg}")

    def log_user(self, msg, source="TERMINAL"):
        print(Fore.CYAN + f"\n[{source}]: {msg}")

    # --- PROCESSAMENTO ---
    def _on_wake_word(self):
        print(Fore.YELLOW + "🎤 [WAKE WORD]: Ouvindo...")
        if VOZ_ATIVA: 
            falar("Sim?")
            time.sleep(1)
        comando = self.ears.capture_full_command()
        if comando:
            self.processar_comando(comando, source="VOZ")
        else:
            print(Fore.RED + "🎤 [EAR]: Não entendi.")

    def processar_comando_remoto(self, cmd, sender_id=None):
        self.processar_comando(cmd, source="TELEGRAM", sender_id=sender_id)

    def processar_comando(self, texto, source="TERMINAL", sender_id=None):
        if not texto: return
        self.log_user(texto, source)
        cmd = texto.lower().strip()
        acao_executada = False

        # Define ID alvo
        target_id = sender_id if sender_id else (self.telegram_bot.admin_id if self.telegram_bot else None)

        # --- TRAVA DE COMANDO REAL (Evita que a IA responda antes do módulo) ---
        comandos_reais = ["solar", "noaa", "cme", "intel", "defcon", "radar", "voos", "foto", "sentinela"]
        
        # Se for um comando conhecido, vamos forçar acao_executada para os módulos agirem
        is_tactical = any(c in cmd for c in comandos_reais)

        # 1. CLIMA
        if "clima" in cmd or "tempo" in cmd:
            cidade = cmd.replace("clima", "").replace("tempo", "").replace("em", "").strip() or "Ivinhema"
            self.log_sistema(f"Clima: {cidade}")
            if self.weather_ops: self.responder(self.weather_ops.obter_clima(cidade), target_id)
            acao_executada = True

        # 2. RADAR / VOOS (Botão: pedir_voos)
        elif getattr(self, 'aguardando_voos_api', False) or "radar" in cmd or "voos" in cmd or "pedir_voos" in cmd:
            if cmd == "pedir_voos":
                self.responder("✈️ [AIR-INTEL]: Informe a CIDADE para varredura:", target_id)
                self.aguardando_voos_api = True # Ativa trava de diálogo
                return
            
            # Se já deu a cidade após clicar no botão ou comando direto
            if getattr(self, 'aguardando_voos_api', False) or len(cmd) > 6:
                self.aguardando_voos_api = False
                cidade = cmd.replace("radar", "").replace("voos", "").strip()
                self.log_sistema(f"Radar API: {cidade}")
                def t_radar():
                    # Tenta usar a API nova se disponível, senão usa o ops antigo
                    from features.radar_api import RadarAereoAPI
                    radar = RadarAereoAPI()
                    rel, path = radar.gerar_radar(cidade)
                    self.responder(rel, target_id)
                    if path and self.telegram_bot and target_id:
                        self.telegram_bot.enviar_foto_ativa(path, legenda=rel, target_chat_id=target_id)
                threading.Thread(target=t_radar, daemon=True).start()
            acao_executada = True

        # 3. INTEL
        elif "intel" in cmd:
            setor = cmd.replace("intel", "").strip() or "global"
            self.log_sistema(f"Intel: {setor}")
            def t_intel():
                from features.intel_war import IntelWar
                war = IntelWar()
                rel, path = war.get_war_report_with_screenshot(setor)
                # Resposta em pedaços se for grande
                self.responder(rel, target_id)
                if path and self.telegram_bot and target_id:
                    self.telegram_bot.enviar_foto_ativa(path, legenda=f"🗺️ {setor.upper()}", target_chat_id=target_id)
            threading.Thread(target=t_intel, daemon=True).start()
            acao_executada = True
            
        # 4. SENTINELA
        elif "foto" in cmd or "sentinela" in cmd:
            self.log_sistema("Sentinela Ativo.")
            def t_cam():
                if self.sentinel_ops:
                    path, msg = self.sentinel_ops.capturar_intruso()
                    self.responder(msg, target_id)
                    if path and self.telegram_bot and target_id:
                        self.telegram_bot.enviar_foto_ativa(path, legenda="Sentinela", target_chat_id=target_id)
            threading.Thread(target=t_cam, daemon=True).start()
            acao_executada = True

        # 5. STATUS
        elif "status" in cmd:
            import psutil
            msg = f"CPU: {psutil.cpu_percent()}% | RAM: {psutil.virtual_memory().percent}%"
            self.responder(msg, target_id)
            acao_executada = True
            
        # 6. IA
        if not acao_executada:
            self.log_sistema("Neural Processing...")
            def t_ai():
                try:
                    if self.ai_manager is None:
                        from features.local_brain import LocalLlamaBrain
                        self.ai_manager = LocalLlamaBrain()
                    
                    self.conversation_history.append({"role": "user", "content": texto})
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    if hasattr(self.ai_manager, 'chat_complete'):
                        res = loop.run_until_complete(self.ai_manager.chat_complete(self.conversation_history))
                    else:
                        res = loop.run_until_complete(self.ai_manager.chat("user", texto))
                    loop.close()
                    
                    resposta = getattr(res, 'content', str(res))
                    resposta = re.sub(r'<\|.*?\|>', '', resposta).strip()
                    self.conversation_history.append({"role": "assistant", "content": resposta})
                    self.responder(resposta, target_id)
                except Exception as e:
                    self.responder(f"Erro Neural: {e}", target_id)
            threading.Thread(target=t_ai, daemon=True).start()

    def responder(self, texto, target_id=None):
        self.log_ai(texto)
        if VOZ_ATIVA and len(texto) < 300:
            try: threading.Thread(target=falar, args=(texto,), daemon=True).start()
            except: pass
        if self.telegram_bot and target_id:
            try: self.telegram_bot.enviar_mensagem_ativa(f"🤖 {texto}", target_chat_id=target_id)
            except: pass

    def run(self):
        print(Fore.GREEN + "\n✅ R2 SERVER EM EXECUÇÃO. (Ctrl+C para parar)\n")
        try:
            while self.running:
                try:
                    cmd_local = input() 
                    if cmd_local: self.processar_comando(cmd_local, source="SERVER_ADMIN")
                except: time.sleep(1)
        except KeyboardInterrupt:
            self.running = False
            sys.exit(0)

if __name__ == "__main__":
    R2Server().run()