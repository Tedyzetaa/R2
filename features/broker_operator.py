# filename: broker_operator.py
import os
import threading
import logging
import base64
import time
import queue
import concurrent.futures
from playwright.sync_api import sync_playwright

from alpha_module import InferenceResult, ScreenState, ActionExecutor

logger = logging.getLogger("BrokerOperator")

class BrokerOperator:
    MAX_CONSECUTIVE_ERRORS = 5

    def __init__(self, alpha_engine):
        self.profile_dir = os.path.abspath("broker10_profile")
        self._page = None
        self._is_running = False
        self.alpha_engine = alpha_engine
        self._browser_thread = None

        self._cmd_queue = queue.Queue()
        self._results = {}

        self.autopilot_delay = 0.5
        self._autopilot_running = False
        self._autopilot_cycle_count = 0
        self._last_autopilot_result = None
        self._autopilot_consecutive_errors = 0
        self._autopilot_stats_lock = threading.Lock()
        self._last_autopilot_time = 0.0

        self._session_lock = threading.Lock()
        self._stop_event = threading.Event()

    def iniciar_sessao(self):
        if self._is_running: 
            return {"ok": True, "msg": "Sessão já ativa."}
        self._is_running = True
        self._stop_event.clear()
        self._browser_thread = threading.Thread(target=self._run_browser, daemon=True, name="BrokerThread")
        self._browser_thread.start()
        return {"ok": True, "msg": "Rampa de lançamento iniciada!"}

    def execute_safe(self, cmd: str, args: dict = None, timeout: float = 15.0) -> dict:
        if not self._is_running:
            return {"ok": False, "error": "Sessão inativa."}

        if cmd in ("AUTOPILOT_START", "AUTOPILOT_STOP"):
            return self._handle_autopilot_cmd(cmd)

        wait_start = time.time()
        while not self._page and (time.time() - wait_start) < 30:
            # [BUG 12] Sinaliza morte prematura da thread aos waiters
            if self._browser_thread and not self._browser_thread.is_alive():
                return {"ok": False, "error": "O navegador abortou a inicialização de forma inesperada."}
            time.sleep(0.2)

        if not self._page:
            return {"ok": False, "error": "Timeout aguardando navegador ficar pronto."}

        cmd_id = id(cmd) + int(time.time() * 1000)
        future = concurrent.futures.Future()
        self._results[cmd_id] = future
        self._cmd_queue.put((cmd_id, cmd, args))

        try:
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            return {"ok": False, "error": f"Timeout ({timeout}s) aguardando resposta da thread gráfica."}
        finally:
            self._results.pop(cmd_id, None)

    def shutdown(self) -> None:
        self._stop_event.set()
        self._is_running = False
        if self._browser_thread and self._browser_thread.is_alive():
            self._browser_thread.join(timeout=5)

    def _handle_autopilot_cmd(self, cmd: str) -> dict:
        if cmd == "AUTOPILOT_START":
            self._autopilot_running = True
            with self._autopilot_stats_lock:
                self._autopilot_cycle_count = 0
                self._autopilot_consecutive_errors = 0
            return {"ok": True, "msg": "Autopilot ativado.", "running": True}

        if cmd == "AUTOPILOT_STOP":
            self._autopilot_running = False
            try: self.alpha_engine.request_stop()
            except: pass
            return {"ok": True, "msg": "Autopilot desativado.", "running": False}

    def _run_browser(self):
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch_persistent_context(
                    self.profile_dir,
                    headless=False,
                    viewport={"width": 1280, "height": 800},
                    args=["--no-sandbox", "--disable-blink-features=AutomationControlled", "--disable-infobars"]
                )
                self._page = browser.pages[0] if browser.pages else browser.new_page()

                def _on_ws(ws):
                    def _on_frame(payload):
                        try:
                            text = payload if isinstance(payload, str) else payload.decode('utf-8', errors='ignore')
                            self.alpha_engine.process_network_packet(text)
                        except: pass
                    ws.on("framereceived", _on_frame)
                
                self._page.on("websocket", _on_ws)

                cookie_file = "trade.broker10.com_cookies.txt"
                if os.path.exists(cookie_file):
                    try:
                        self._page.goto("https://trade.broker10.com", timeout=30000)
                        self._inject_netscape_cookies(cookie_file)
                    except Exception as e:
                        logger.error(f"Erro ao injetar cookies, prosseguindo vazio: {e}")
                
                self.alpha_engine.attach(self._page)
                try:
                    self._page.goto("https://trade.broker10.com/traderoom", timeout=60000, wait_until="commit")
                except: time.sleep(3)

                while self._is_running and not self._stop_event.is_set():
                    try:
                        cmd_id, cmd, args = self._cmd_queue.get(timeout=0.1)
                        result = self._dispatch_cmd(cmd, args)
                        if cmd_id in self._results:
                            self._results[cmd_id].set_result(result)
                    except queue.Empty: pass

                    # [BUG 15] Substituição do sleep fragmentado. Processa os comandos instantaneamente
                    now = time.time()
                    if self._autopilot_running and (now - self._last_autopilot_time) >= self.autopilot_delay:
                        self._run_autopilot_cycle()
                        self._last_autopilot_time = time.time()

        except Exception as e:
            logger.error(f"Erro fatal na thread do browser: {e}")
        finally:
            # [BUG 5] Limpa memory leak cancelando futures órfãos caso o browser crashe
            for cid, fut in list(self._results.items()):
                if not fut.done():
                    fut.set_exception(RuntimeError("Browser thread encerrada abruptamente."))
            self._results.clear()
            self._is_running = False
            self._page = None

    def _inject_netscape_cookies(self, file_path):
        # [BUG 10] Tratamento rigoroso de cookies
        try:
            cookies = []
            with open(file_path, 'r') as f:
                for line in f:
                    if not line.startswith('#') and line.strip():
                        p = line.split('\t')
                        if len(p) >= 7:
                            cookies.append({
                                'name': p[5].strip(), 'value': p[6].strip(),
                                'domain': p[0] if p[0].startswith('.') else '.' + p[0],
                                'path': p[2].strip(), 'expires': int(float(p[4])),
                                'secure': p[3].strip().upper() == 'TRUE', 'httpOnly': False, 'sameSite': 'None'
                            })
            self._page.context.add_cookies(cookies)
            logger.info("Cookies de sessão injetados com sucesso.")
        except Exception as e: 
            logger.error(f"Falha silenciada nos cookies revertida: O ficheiro pode estar corrompido - {e}")

    def _dispatch_cmd(self, cmd: str, args: dict = None) -> dict:
        try:
            if cmd == "ANALYZE": return self.alpha_engine.perceive_and_act()
            elif cmd == "SCREENSHOT": return {"ok": True, "screenshot_b64": base64.b64encode(self._page.screenshot()).decode("utf-8")}
            # [BUG 2] Handler oficial de navegação garantido no dispatcher
            elif cmd == "NAVIGATE":
                url = (args or {}).get("url", "https://trade.broker10.com/traderoom")
                self._page.goto(url, timeout=30000)
                return {"ok": True, "url": self._page.url}
            elif cmd == "OVERRIDE":
                action = (args or {}).get("action", "WAIT")
                fake = InferenceResult(state=ScreenState.UNKNOWN, confidence=1.0, recommended_action=action)
                return {"override_action": action, "result": ActionExecutor(self._page).execute(fake)}
            elif cmd == "CLICK_COORD":
                x, y = (args or {}).get("x"), (args or {}).get("y")
                self._page.mouse.click(x, y)
                return {"ok": True, "screenshot_b64": base64.b64encode(self._page.screenshot()).decode("utf-8"), "coord": [x, y]}
            elif cmd == "DIAGNOSTICO": return {"log": ["Sistema Operacional"]}
            else: return {"ok": False, "error": f"Comando desconhecido: {cmd}"}
        except Exception as e: return {"ok": False, "error": str(e)}

    def _run_autopilot_cycle(self):
        # [BUG 9] Previne falha infinita caso a aba do browser morra subitamente
        if not self._page or self._page.is_closed():
            logger.warning("Autopilot detectou página inativa. Pausando.")
            self._autopilot_running = False
            return

        try:
            result = self.alpha_engine.perceive_and_act()
        except Exception as e:
            with self._autopilot_stats_lock:
                self._autopilot_consecutive_errors += 1
                if self._autopilot_consecutive_errors >= self.MAX_CONSECUTIVE_ERRORS:
                    self._autopilot_running = False
                    self._last_autopilot_result = {"error": str(e), "consecutive_errors": self._autopilot_consecutive_errors}
            return

        with self._autopilot_stats_lock:
            self._autopilot_cycle_count += 1
            self._last_autopilot_result = result
            self._autopilot_consecutive_errors = 0

        state = result.get("state", "UNKNOWN")
        state_str = state.value if hasattr(state, 'value') else str(state)
        # O Bug 3 foi corrigido no alpha_module.py (Enum), agora esta trava funciona!
        if state_str in {"LOGIN_REQUIRED", "RATE_LIMIT"}:
            logger.critical(f"Trava de segurança acionada pelo estado: {state_str}")
            self._autopilot_running = False