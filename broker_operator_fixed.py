# filename: broker_operator_fixed.py
"""
BrokerOperator – VERSÃO CORRIGIDA
Gerencia navegador Playwright, intercepta WebSocket e executa ordens.
Loop isolado com fila de comandos, autopilot automático e logging robusto.
"""
import asyncio
import base64
import logging
import os
import time
import uuid
from typing import Optional, Dict, Any

from playwright.async_api import async_playwright, Page, BrowserContext

logger = logging.getLogger("BrokerOperator")


class BrokerOperator:
    MAX_CONSECUTIVE_ERRORS = 5
    CMD_TIMEOUTS = {"ANALYZE": 3.0, "SCREENSHOT": 5.0, "NAVIGATE": 30.0}

    def __init__(self, alpha_engine):
        self.profile_dir = os.path.abspath("broker10_profile")
        self.alpha_engine = alpha_engine
        self.alpha_engine.broker_ops = self
        self._browser: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self._is_running = False
        self._browser_task: Optional[asyncio.Task] = None
        self._cmd_queue = None
        self._results: Dict[str, asyncio.Future] = {}
        self.autopilot_delay = 1.0
        self._autopilot_running = False
        self._autopilot_cycle_count = 0
        self._autopilot_consecutive_errors = 0
        self._last_autopilot_time = 0.0
        self._stop_event = None

    async def iniciar_sessao(self):
        """Inicia a sessão do navegador em background."""
        if self._is_running:
            return {"ok": True, "msg": "Sessão já ativa."}
        self._is_running = True
        self._cmd_queue = asyncio.Queue()
        self._stop_event = asyncio.Event()
        self._stop_event.clear()
        self._browser_task = asyncio.create_task(self._run_browser())
        logger.info("[BrokerOperator] 🚀 Sessão inicializada em background")
        return {"ok": True, "msg": "Sessão iniciada."}

    async def execute_safe(self, cmd: str, args: dict = None, timeout: float = None) -> dict:
        """Envia comando para o loop do navegador e aguarda resposta."""
        if not self._is_running:
            logger.error("[BrokerOperator] ❌ Sessão inativa ao tentar executar: " + cmd)
            return {"ok": False, "error": "Sessão inativa."}
        if cmd in ("AUTOPILOT_START", "AUTOPILOT_STOP"):
            return await self._handle_autopilot_cmd(cmd)

        if timeout is None:
            timeout = self.CMD_TIMEOUTS.get(cmd, 15.0)
            
        cmd_id = uuid.uuid4().hex
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        self._results[cmd_id] = future
        await self._cmd_queue.put((cmd_id, cmd, args or {}))
        logger.debug(f"[BrokerOperator] Comando enfileirado: {cmd}")
        try:
            result = await asyncio.wait_for(future, timeout=timeout)
            logger.debug(f"[BrokerOperator] Comando completado: {cmd}")
            return result
        except asyncio.TimeoutError:
            logger.warning(f"[BrokerOperator] ⏱️ Timeout ({timeout}s) no comando {cmd}")
            return {"ok": False, "error": f"Timeout ({timeout}s) no comando {cmd}"}
        finally:
            self._results.pop(cmd_id, None)

    async def _handle_autopilot_cmd(self, cmd: str) -> dict:
        if cmd == "AUTOPILOT_START":
            self._autopilot_running = True
            self._autopilot_consecutive_errors = 0
            logger.info("[BrokerOperator] 🤖 Autopilot ATIVADO manualmente")
            return {"ok": True, "msg": "Autopilot ativado."}
        else:
            self._autopilot_running = False
            logger.info("[BrokerOperator] 🛑 Autopilot DESATIVADO manualmente")
            return {"ok": True, "msg": "Autopilot desativado."}

    async def _run_browser(self):
        """Loop principal do navegador: gerencia página, WebSocket capture e comandos."""
        try:
            async with async_playwright() as p:
                logger.info("[BrokerOperator] 📂 Lançando Playwright...")
                self._browser = await p.chromium.launch_persistent_context(
                    self.profile_dir,
                    headless=False,
                    args=["--no-sandbox", "--disable-blink-features=AutomationControlled"]
                )
                self._page = self._browser.pages[0] if self._browser.pages else await self._browser.new_page()
                logger.info("[BrokerOperator] ✅ Navegador lançado com sucesso")

                # Injeção de script para capturar mensagens WebSocket
                js_intercept = """
                window.__r2_queue = [];
                const _WS = window.WebSocket;
                window.WebSocket = function(u, p) {
                    const ws = p ? new _WS(u, p) : new _WS(u);
                    ws.addEventListener('message', e => {
                        if (typeof e.data === 'string' && window.__r2_queue.length < 500)
                            window.__r2_queue.push(e.data);
                    });
                    return ws;
                };
                Object.assign(window.WebSocket, {
                    prototype: _WS.prototype,
                    CONNECTING: _WS.CONNECTING,
                    OPEN: _WS.OPEN,
                    CLOSING: _WS.CLOSING,
                    CLOSED: _WS.CLOSED
                });
                """
                await self._page.add_init_script(js_intercept)
                logger.info("[BrokerOperator] 🔌 WebSocket interception injetado")
                
                await self._page.goto("https://trade.broker10.com/traderoom", wait_until="domcontentloaded", timeout=30000)
                logger.info("[BrokerOperator] 📍 Navegado para broker10")
                
                self.alpha_engine.attach(self._page)
                logger.info("[BrokerOperator] 🧠 AlphaEngine anexado à página")

                # ✅ CORREÇÃO #1: Ativar autopilot automaticamente após inicializar
                self._autopilot_running = True
                self._autopilot_consecutive_errors = 0
                logger.info("[BrokerOperator] 🤖 Autopilot AUTOMÁTICO ATIVADO ao iniciar")

                # Health check: a cada 30s verifica se a página ainda responde
                last_health = time.time()
                loop_iterations = 0
                
                while not self._stop_event.is_set():
                    loop_iterations += 1
                    
                    # Processar comandos da fila
                    try:
                        cmd_id, cmd, args = self._cmd_queue.get_nowait()
                        logger.debug(f"[BrokerOperator] ▶️ Processando comando: {cmd}")
                        res = await self._dispatch_cmd(cmd, args)
                        if cmd_id in self._results:
                            fut = self._results[cmd_id]
                            if not fut.done():
                                fut.set_result(res)
                                logger.debug(f"[BrokerOperator] ✅ Resposta retornada para {cmd}")
                    except asyncio.QueueEmpty:
                        pass
                    except Exception as e:
                        logger.error(f"[BrokerOperator] ❌ Erro ao processar comando: {e}")

                    # Coletar pacotes WebSocket da página
                    try:
                        packets = await self._page.evaluate("() => window.__r2_queue.splice(0, 50)")
                        if packets:
                            logger.debug(f"[BrokerOperator] 📡 {len(packets)} pacotes WebSocket capturados")
                            for p in packets:
                                self.alpha_engine.process_network_packet(p)
                    except Exception as e:
                        logger.warning(f"[BrokerOperator] ⚠️ Erro ao capturar WebSocket: {e}")

                    # Ciclo de autopilot
                    if self._autopilot_running and (time.time() - self._last_autopilot_time >= self.autopilot_delay):
                        await self._run_autopilot_cycle()
                        self._last_autopilot_time = time.time()

                    # Health check periódico
                    if time.time() - last_health > 30:
                        try:
                            await self._page.evaluate("1")
                            logger.debug("[BrokerOperator] 💚 Health check OK")
                        except Exception as e:
                            logger.warning(f"[BrokerOperator] ⚠️ Página travada ({e}), recarregando...")
                            await self._page.reload()
                        last_health = time.time()

                    await asyncio.sleep(0.05)  # ✅ CORREÇÃO #2: Reduzir delay para 50ms para mais responsividade
                    
        except Exception as e:
            logger.error(f"[BrokerOperator] 💥 Loop do navegador finalizado com erro: {e}")
        finally:
            self._is_running = False
            if self._browser:
                try:
                    await self._browser.close()
                    logger.info("[BrokerOperator] 🔒 Navegador encerrado")
                except Exception as e:
                    logger.error(f"[BrokerOperator] ❌ Erro ao fechar navegador: {e}")

    async def _run_autopilot_cycle(self):
        """Executa um ciclo do autopilot: análise e possível ordem."""
        try:
            res = await self.alpha_engine.perceive_and_act()
            state = res.get("state")
            action = res.get("recommended_action")
            confidence = res.get("confidence", 0.0)
            details = res.get("details", {})
            
            logger.debug(f"[Autopilot] Estado: {state} | Ação: {action} | Confiança: {confidence*100:.1f}%")
            
            threshold = self.alpha_engine.config.signal_score_threshold / 100.0

            if action in ("CLICK_ACIMA", "CLICK_ABAIXO") and confidence >= threshold:
                cmd = "CALL" if action == "CLICK_ACIMA" else "PUT"
                logger.info(f"[Autopilot] 🎯 SINAL EXECUTÁVEL: {cmd} (conf={confidence*100:.1f}%)")
                await self.executar_comando_broker(cmd)
                
                with self.alpha_engine._lock:
                    self.alpha_engine._trade_in_progress = True
                    self.alpha_engine._trade_start_time = time.time()
                    self.alpha_engine._trade_direction = cmd
                    self.alpha_engine._trade_entry_price = details.get("entry_price", 0.0)
                    self.alpha_engine._trade_signal_name = details.get("signal_name", "OCR")
                    self.alpha_engine._last_trade_time = time.time()
                
                self._autopilot_cycle_count += 1
                logger.info(f"[Autopilot] ✅ Trade #{self._autopilot_cycle_count} registrado")
            else:
                if action == "WAIT":
                    logger.debug(f"[Autopilot] ⏳ Aguardando sinal (estado: {state})")
                
            self._autopilot_consecutive_errors = 0
        except Exception as e:
            self._autopilot_consecutive_errors += 1
            logger.error(f"[Autopilot] ❌ Erro no ciclo ({self._autopilot_consecutive_errors}/{self.MAX_CONSECUTIVE_ERRORS}): {e}")
            if self._autopilot_consecutive_errors >= self.MAX_CONSECUTIVE_ERRORS:
                self._autopilot_running = False
                logger.critical("[Autopilot] 🛑 Desativado por excesso de erros")

    async def executar_comando_broker(self, cmd: str):
        """Executa clique no botão de CALL ou PUT."""
        size = self._page.viewport_size or {'width': 1280, 'height': 800}
        if cmd == "CALL":
            x = int(size['width'] * 0.93)
            y = int(size['height'] * 0.45)
        else:
            x = int(size['width'] * 0.93)
            y = int(size['height'] * 0.60)
        
        logger.info(f"[Broker] 🖱️ Clicando {cmd} em ({x}, {y})")
        await self._page.mouse.click(x, y)
        logger.info(f"[Broker] ✅ Ordem {cmd} executada")

    def save_transaction_log(self, data: dict):
        """Salva o histórico de trades em um arquivo JSON local."""
        log_file = "trade_history.json"
        try:
            history = []
            if os.path.exists(log_file):
                with open(log_file, "r") as f:
                    history = json.load(f)
            data["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
            history.append(data)
            with open(log_file, "w") as f:
                json.dump(history[-1000:], f, indent=4)
            logger.info(f"[Broker] Log de transação salvo para trade {data.get('status')}")
        except Exception as e:
            logger.error(f"[Broker] Erro ao salvar log de transação: {e}")

    async def _dispatch_cmd(self, cmd: str, args: dict) -> dict:
        """Executa comandos síncronos solicitados via API."""
        logger.debug(f"[Dispatch] Processando: {cmd} com args: {args}")
        
        if cmd == "SCREENSHOT":
            try:
                img = await self._page.screenshot()
                b64 = base64.b64encode(img).decode()
                logger.debug(f"[Dispatch] Screenshot capturado ({len(img)} bytes)")
                return {"ok": True, "screenshot_b64": b64}
            except Exception as e:
                logger.error(f"[Dispatch] Erro ao capturar screenshot: {e}")
                return {"ok": False, "error": str(e)}
        
        if cmd == "NAVIGATE":
            try:
                url = args.get("url", "https://trade.broker10.com/traderoom")
                logger.info(f"[Dispatch] 🌐 Navegando para: {url}")
                await self._page.goto(url, timeout=30000, wait_until="domcontentloaded")
                logger.info(f"[Dispatch] ✅ Navegação concluída")
                return {"ok": True}
            except Exception as e:
                logger.error(f"[Dispatch] Erro de navegação: {e}")
                return {"ok": False, "error": str(e)}
        
        if cmd == "ANALYZE":
            try:
                res = await self.alpha_engine.perceive_and_act()
                logger.debug(f"[Dispatch] Análise completada: {res}")
                return {"ok": True, "result": res}
            except Exception as e:
                logger.error(f"[Dispatch] Erro na análise: {e}")
                return {"ok": False, "error": str(e)}
        
        if cmd == "OVERRIDE":
            action = args.get("action")
            logger.warning(f"[Dispatch] ⚡ Override recebido: {action}")
            return {"ok": True, "msg": f"Override {action} recebido"}
        
        if cmd == "CLICK_COORD":
            try:
                x, y = args.get("x"), args.get("y")
                logger.info(f"[Dispatch] 🖱️ Clique em ({x}, {y})")
                await self._page.mouse.click(x, y)
                img = await self._page.screenshot()
                b64 = base64.b64encode(img).decode()
                return {"ok": True, "coord": [x, y], "screenshot_b64": b64}
            except Exception as e:
                logger.error(f"[Dispatch] Erro ao clicar: {e}")
                return {"ok": False, "error": str(e)}
        
        if cmd == "DIAGNOSTICO":
            return {
                "ok": True,
                "url": self._page.url,
                "autopilot_running": self._autopilot_running,
                "autopilot_cycles": self._autopilot_cycle_count,
                "consecutive_errors": self._autopilot_consecutive_errors
            }
        
        logger.warning(f"[Dispatch] ⚠️ Comando desconhecido: {cmd}")
        return {"ok": False, "error": f"Comando desconhecido: {cmd}"}

    async def close(self):
        """Encerra o navegador e tasks."""
        logger.info("[BrokerOperator] Encerrando...")
        self._stop_event.set()
        if self._browser_task:
            await self._browser_task
        logger.info("[BrokerOperator] ✅ Encerrado")
