# filename: broker_operator.py
# ============================================================
# REFATORAÇÃO: Black Ops Final - Correção de Bugs e Melhorias
# ============================================================
# - BUG-F: _at_work resetado se _is_running for False
# - BUG-G: Retorno de executar_ordem com status "ENQUEUED"
# - BUG-H: autopilot_ativo usa alpha_engine como fonte única
# - BUG-J: save_transaction_log chamado ao final de executar_ordem
# - MELHORIA-3: Heartbeat WS (verifica silêncio e reconecta)
# - MELHORIA-4: filtro de active_id no alpha_module (já implementado)
# - Coordenadas de clique corrigidas: (1193,384) e (1211,485)
# ============================================================
# CORREÇÕES APLICADAS:
# - BUG-09: WebSocket reconecta após reload (re-registro do listener)
# - BUG-10: _at_work substituído por threading.Lock()
# - BUG-11: save_transaction_log protegido com lock
# - BUG-12: browser/context fechados no finally
# - BUG-13: rate limiter usando _last_order_time
# - ARQ-08: ENABLE_CLICK_SCREENSHOT
# ============================================================

import os
import threading
import logging
import time
import queue
import json
from datetime import datetime
from playwright.sync_api import sync_playwright

logger = logging.getLogger("BrokerOperator")

class BrokerOperator:
    def __init__(self, alpha_engine):
        self.profile_dir = os.path.abspath("r2_tactical_session")
        self.cookies_txt = "trade.broker10.com_cookies.txt"
        self._page = None
        self._is_running = False
        self.alpha_engine = alpha_engine
        self._browser_thread = None
        self._cmd_queue = queue.Queue()
        self._work_lock = threading.Lock()          # BUG-10
        self._log_lock = threading.Lock()           # BUG-11
        self._stop_event = threading.Event()
        self._last_order_time = 0.0
        self._last_ws_msg_time = 0.0
        
        # ARQ-08: captura de tela opcional no clique
        self.enable_click_screenshot = os.environ.get("ENABLE_CLICK_SCREENSHOT", "false").lower() == "true"

    def iniciar_sessao(self):
        if self._is_running:
            return {"ok": True, "msg": "Sessão Sniper já ativa."}

        self._is_running = True
        self._stop_event.clear()
        self.alpha_engine.ligar_autopilot()
        self._browser_thread = threading.Thread(target=self._browser_loop, daemon=True)
        self._browser_thread.start()
        return {"ok": True, "msg": "Protocolo Sniper Iniciado."}

    def carregar_cookies_netscape(self, page):
        if not os.path.exists(self.cookies_txt):
            logger.warning("⚠️ Arquivo de cookies TXT não encontrado na raiz.")
            return

        cookies = []
        try:
            with open(self.cookies_txt, 'r') as f:
                for line in f:
                    if line.startswith('#') or not line.strip():
                        continue
                    parts = line.strip().split('\t')
                    if len(parts) < 7:
                        continue
                    cookie = {
                        'name': parts[5],
                        'value': parts[6],
                        'domain': parts[0] if parts[0].startswith('.') else parts[0],
                        'path': parts[2],
                        'secure': parts[3].upper() == 'TRUE',
                        'expires': int(parts[4]) if int(parts[4]) > 0 else -1
                    }
                    cookies.append(cookie)
            page.context.add_cookies(cookies)
            logger.info(f"🧬 [TRANSPLANTE] {len(cookies)} cookies injetados.")
        except Exception as e:
            logger.error(f"❌ Erro ao converter cookies TXT: {e}")

    def _configurar_grampo(self, ws):
        self._last_ws_msg_time = time.time()

        def on_frame(payload):
            self._last_ws_msg_time = time.time()
            self.alpha_engine.processar_ws(payload)

        ws.on("framereceived", on_frame)

    def parar_sessao(self):
        self._is_running = False
        self.alpha_engine.autopilot_ativo = False
        self._cmd_queue.put("STOP")
        if self._browser_thread:
            self._browser_thread.join(timeout=5)
        return {"ok": True, "msg": "Sessão Encerrada."}

    def _browser_loop(self):
        browser = None
        context = None
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False, args=["--window-size=1280,720"])
                context = browser.new_context(viewport={'width': 1280, 'height': 720}, device_scale_factor=1)
                self._page = context.new_page()
                self.carregar_cookies_netscape(self._page)
                self._page.on("websocket", self._configurar_grampo)

                try:
                    logger.info("📡 Navegando para a sala de trade...")
                    self._page.goto("https://trade.broker10.com/traderoom", wait_until="domcontentloaded")
                    self._page.wait_for_selector("#glcanvas", state="attached", timeout=60000)
                    logger.info("✅ Gráfico detectado. Interceptador ativo.")
                except Exception as e:
                    logger.warning(f"⚠️ Aviso no carregamento: {e}")

                last_heartbeat_check = time.time()
                while self._is_running:
                    try:
                        if self._page and self._page.is_closed():
                            logger.info("🚪 Navegador fechado pelo usuário.")
                            break

                        try:
                            cmd = self._cmd_queue.get(timeout=0.5)
                            if cmd == "STOP":
                                break
                            if cmd in ["CALL", "PUT", "CLICK_ACIMA", "CLICK_ABAIXO"]:
                                self._executar_na_pagina(cmd)
                        except queue.Empty:
                            pass

                        agora = time.time()
                        if agora - last_heartbeat_check >= 30:
                            last_heartbeat_check = agora
                            if self._last_ws_msg_time > 0 and (agora - self._last_ws_msg_time) > 60:
                                logger.warning("[ALERT] WebSocket silencioso há mais de 60s. Recarregando página...")
                                try:
                                    self._page.reload()
                                    # BUG-09: re-registrar o listener de WebSocket
                                    self._page.on("websocket", self._configurar_grampo)
                                    time.sleep(5)
                                    self._last_ws_msg_time = agora
                                except Exception as e:
                                    logger.error(f"Falha ao recarregar: {e}")

                        if self._page:
                            self._page.wait_for_timeout(100)
                    except Exception as e:
                        logger.error(f"Erro no loop do navegador: {e}")
                        break

        except Exception as e:
            logger.critical(f"Falha fatal no navegador: {str(e)}")
        finally:
            # BUG-12: fechamento seguro
            if context:
                context.close()
            if browser:
                browser.close()
            self._is_running = False

    def _executar_na_pagina(self, direcao: str):
        """Executa clique por coordenadas (thread do navegador)."""
        try:
            if direcao in ("CALL", "CLICK_ACIMA"):
                self._page.mouse.click(1193, 384)
                logger.info("🔥 [CLIQUE] Coordenada ACIMA executada.")
            else:
                self._page.mouse.click(1211, 485)
                logger.info("🔥 [CLIQUE] Coordenada ABAIXO executada.")
            self._last_order_time = time.time()
            
            # ARQ-08: screenshot opcional
            if self.enable_click_screenshot:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_path = f"click_{direcao}_{timestamp}.png"
                self._page.screenshot(path=screenshot_path)
                logger.info(f"📸 Screenshot salvo: {screenshot_path}")
            
            self.save_transaction_log({"direcao": direcao, "status": "EXECUTED"})
        except Exception as e:
            logger.error(f"❌ Falha ao clicar: {e}")
        finally:
            self._work_lock.release()   # BUG-10

    def executar_ordem(self, direcao: str):
        """Enfileira a ordem para execução na thread do navegador."""
        # BUG-13: rate limiter
        now = time.time()
        if now - self._last_order_time < 2.0:
            logger.warning("⏱️ Rate limit: aguarde antes de enviar nova ordem.")
            return {"ok": False, "error": "Rate limit"}

        if not self._is_running or not self._page:
            return {"ok": False, "error": "Browser thread não está rodando"}

        if not self.alpha_engine.autopilot_ativo:
            logger.info(f"🚫 [BLOQUEIO] Sinal de {direcao} ignorado (Autopilot OFF).")
            return {"ok": False, "error": "Autopilot desativado"}

        # BUG-10: lock não-bloqueante
        if not self._work_lock.acquire(blocking=False):
            logger.warning("⚠️ Já existe uma ordem sendo executada. Aguarde.")
            return {"ok": False, "error": "Já em execução"}

        try:
            self._cmd_queue.put(direcao)
            logger.info(f"📥 [FILA] Ordem de {direcao} agendada.")
            self._last_order_time = now   # atualiza após enfileirar
            return {"ok": True, "status": "ENQUEUED", "action_taken": f"{direcao}_ENQUEUED"}
        except Exception as e:
            self._work_lock.release()
            logger.error(f"❌ Erro ao enfileirar ordem: {e}")
            return {"ok": False, "error": str(e)}

    def save_transaction_log(self, data):
        log_file = "trade_history.json"
        log_entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "direcao": data.get("direcao"),
            "resultado": data.get("status")
        }
        # BUG-11: lock na escrita do JSON
        with self._log_lock:
            try:
                history = []
                if os.path.exists(log_file):
                    with open(log_file, 'r', encoding='utf-8') as f:
                        history = json.load(f)
                history.append(log_entry)
                with open(log_file, 'w', encoding='utf-8') as f:
                    json.dump(history, f, indent=4)
                logger.info(f"📝 Transação registrada: {log_entry}")
            except Exception as e:
                logger.error(f"Erro ao salvar log: {e}")