# filename: alpha_module.py
# ============================================================
# REFATORAÇÃO: Unificação Estratégias Justiceiro + JUST WIN
# - Velas de Comando: suporte/resistência com max 2 toques
# - JUST WIN: momentum baseado em close[2], open[2], close[4], close[8]
# - Sem regras extras de risco (take profit, stop loss, etc.)
# ============================================================

import os
import time
import logging
import threading
import json
import asyncio
import aiofiles
from collections import deque
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum
from datetime import datetime

logger = logging.getLogger("ModuloAlpha")

async def salvar_trade_json_raiz(dados_trade: dict):
    """
    Grava o resultado do trade de forma assíncrona em um arquivo JSON na pasta raiz.
    Garante que escritas simultâneas não corrompam o arquivo.
    """
    log_file = "historico_trades_alpha.json"
    
    # Injeta um timestamp legível se não existir
    if "timestamp_registro" not in dados_trade:
        dados_trade["timestamp_registro"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
    try:
        historico = []
        # Se o arquivo já existir, lê o conteúdo atual de forma assíncrona
        if os.path.exists(log_file):
            async with aiofiles.open(log_file, mode='r', encoding='utf-8') as f:
                conteudo = await f.read()
                if conteudo.strip():
                    historico = json.loads(conteudo)
        
        # Adiciona o novo trade ao histórico
        historico.append(dados_trade)
        
        # Grava de volta na raiz de forma assíncrona e formatada
        async with aiofiles.open(log_file, mode='w', encoding='utf-8') as f:
            await f.write(json.dumps(historico, indent=4, ensure_ascii=False))
            
    except Exception as e:
        # Evita derrubar o sistema analítico por falha de I/O
        print(f"❌ Erro crítico ao salvar log do trade no JSON raiz: {e}")

# ====================================================================
# CONFIGURAÇÃO DE RISCO (apenas PnL diário, sem contador de losses)
# ====================================================================
@dataclass
class RiskConfig:
    daily_loss_limit: float = 100.0
    daily_profit_target: float = 300.0
    base_risk_per_trade: float = 10.0
    recovery_factor_soros: float = 0.5
    max_consecutive_losses_before_reduce: int = 2
    min_risk_per_trade: float = 2.0

    def __post_init__(self):
        self._daily_pnl = 0.0
        logger.info(f"[RiskConfig] Limite diário={self.daily_loss_limit}, Meta={self.daily_profit_target}")

    def reset_daily(self):
        self._daily_pnl = 0.0

    def update_result(self, pnl: float):
        self._daily_pnl += pnl

    def get_position_size_multiplier(self) -> float:
        return 1.0

    def is_daily_stopped(self) -> bool:
        return self._daily_pnl <= -self.daily_loss_limit or self._daily_pnl >= self.daily_profit_target

# ====================================================================
# JUST WIN ENGINE (Momentum Híbrido)
# ====================================================================
class JustWinEngine:
    """
    Implementa a lógica do script JUSTWIN.txt:
    - CALL: (close > close[2]) and (close[2] > open[2]) and (close[4] > close[8])
    - PUT:  (close < close[2]) and (close[2] < open[2]) and (close[4] < close[8])
    """
    def __init__(self, max_history: int = 20):
        self.history = deque(maxlen=max_history)   # cada elemento = {"open": o, "close": c}
        self.last_signal = None
        self.last_signal_time = 0.0

    def add_candle(self, open_price: float, close_price: float) -> None:
        """Adiciona uma nova vela ao histórico."""
        self.history.append({"open": open_price, "close": close_price})

    def check_signal(self) -> Optional[str]:
        """
        Verifica as condições de JUST WIN com base no histórico atual.
        Retorna "CALL", "PUT" ou None.
        """
        if len(self.history) < 9:
            return None   # precisa de pelo menos 9 velas (índices 0..8)

        # indices: 0 = vela atual (mais recente), 1 = anterior, etc.
        # close[0] é a última adicionada, close[2] é duas atrás, etc.
        close0 = self.history[-1]["close"]
        close2 = self.history[-3]["close"]   # índice -3 = 2 velas atrás
        open2  = self.history[-3]["open"]
        close4 = self.history[-5]["close"]   # 4 velas atrás
        close8 = self.history[-9]["close"]   # 8 velas atrás

        # Condição de CALL
        if (close0 > close2) and (close2 > open2) and (close4 > close8):
            return "CALL"
        # Condição de PUT
        elif (close0 < close2) and (close2 < open2) and (close4 < close8):
            return "PUT"
        return None

# ====================================================================
# JUSTICEIRO ENGINE (Velas de Comando com limite de 2 toques)
# ====================================================================
class JusticeiroEngine:
    """
    Implementa a lógica "Velas de Comando":
      - bull_command: open == low e close > open -> define SUPORTE = open
      - bear_command: open == high e close < open -> define RESISTÊNCIA = open
    Cada nível só pode ser tocado no máximo 2 vezes, depois é descartado.
    Gatilho: preço atual <= suporte (tolerância) -> CALL
             preço atual >= resistência (tolerância) -> PUT
    """
    def __init__(self, tolerance: float = 0.0002, max_touches: int = 2):
        self.tolerance = tolerance
        self.max_touches = max_touches
        # Cada nível armazenado com contador de toques: { "price": float, "touches": int }
        self.suportes: List[Dict] = []   # de bull_command
        self.resistencias: List[Dict] = []  # de bear_command

    def process_data(self, ohlc: Dict) -> str:
        """
        Processa uma nova vela. Retorna:
          "CALL" se tocou um suporte,
          "PUT" se tocou uma resistência,
          "WAIT" caso contrário.
        Além disso, adiciona novos níveis se for uma vela de comando.
        """
        o = ohlc.get('open')
        h = ohlc.get('high')
        l = ohlc.get('low')
        c = ohlc.get('close')
        curr = ohlc.get('current', c)

        # 1. Detectar vela de comando e adicionar novo nível
        if o == l and c > o:   # bull_command
            self._add_nivel(self.suportes, o)
            logger.info(f"[JUSTICEIRO] 🛡️ Novo SUPORTE em {o:.5f}")
        elif o == h and c < o: # bear_command
            self._add_nivel(self.resistencias, o)
            logger.info(f"[JUSTICEIRO] 🔴 Nova RESISTÊNCIA em {o:.5f}")

        # 2. Verificar toques em suportes (CALL)
        signal = self._check_touches(self.suportes, curr, upper=False)  # preço <= nivel
        if signal:
            return "CALL"

        # 3. Verificar toques em resistências (PUT)
        signal = self._check_touches(self.resistencias, curr, upper=True)  # preço >= nivel
        if signal:
            return "PUT"

        return "WAIT"

    def _add_nivel(self, lista: List[Dict], price: float) -> None:
        """Adiciona um novo nível se não existir exatamente igual dentro da tolerância."""
        if not any(abs(n['price'] - price) <= self.tolerance for n in lista):
            lista.append({"price": price, "touches": 0, "last_touch_time": 0})
            logger.info(f"[JUSTICEIRO] Novo nível em {price:.5f} adicionado.")
        else:
            logger.debug(f"[JUSTICEIRO] Nível {price:.5f} já existe. Ignorado.")

    def _check_touches(self, lista: List[Dict], current_price: float, upper: bool) -> bool:
        """
        Verifica se o preço atual toca algum nível da lista.
        upper=True: toque por cima (current >= price - tolerance)
        upper=False: toque por baixo (current <= price + tolerance)
        Se tocar, incrementa o contador; se atingir max_touches, remove o nível.
        Retorna True se houve toque (sinal gerado), False caso contrário.
        """
        agora = time.time()
        for i, nivel in enumerate(lista):
            price = nivel['price']
            if upper:
                if current_price >= price - self.tolerance:
                    # Verifica se já tocou neste segundo
                    ultimo_toque = nivel.get('last_touch_time', 0)
                    if agora - ultimo_toque < 1.0:
                        logger.debug(f"[JUSTICEIRO] Toque em RESISTÊNCIA {price:.5f} ignorado (menos de 1s desde o último).")
                        continue
                    nivel['touches'] += 1
                    nivel['last_touch_time'] = agora
                    logger.info(f"[JUSTICEIRO] ⚡ Toque em RESISTÊNCIA {price:.5f} (toque #{nivel['touches']}/{self.max_touches})")
                    if nivel['touches'] >= self.max_touches:
                        lista.pop(i)
                    return True
            else:
                if current_price <= price + self.tolerance:
                    ultimo_toque = nivel.get('last_touch_time', 0)
                    if agora - ultimo_toque < 1.0:
                        logger.debug(f"[JUSTICEIRO] Toque em SUPORTE {price:.5f} ignorado (menos de 1s desde o último).")
                        continue
                    nivel['touches'] += 1
                    nivel['last_touch_time'] = agora
                    logger.info(f"[JUSTICEIRO] ⚡ Toque em SUPORTE {price:.5f} (toque #{nivel['touches']}/{self.max_touches})")
                    if nivel['touches'] >= self.max_touches:
                        lista.pop(i)
                    return True
        return False

    def get_current_levels(self) -> Tuple[List[float], List[float]]:
        """Retorna listas de preços de suportes e resistências ativos."""
        return ([n['price'] for n in self.suportes], [n['price'] for n in self.resistencias])

    def reset(self):
        self.suportes.clear()
        self.resistencias.clear()

# ====================================================================
# ESTADOS E RESULTADOS (mantidos do original)
# ====================================================================
class ScreenState(str, Enum):
    IDLE = "IDLE"
    WAITING_SIGNAL = "WAITING_SIGNAL"
    GATINHO_CALL = "GATINHO_CALL"
    GATINHO_PUT = "GATINHO_PUT"
    POSITION_OPEN = "POSITION_OPEN"
    COOLDOWN = "COOLDOWN"
    ARMED = "ARMED"
    UNKNOWN = "UNKNOWN"

@dataclass
class InferenceResult:
    state: str = ScreenState.UNKNOWN
    confidence: float = 0.0
    recommended_action: str = "WAIT"
    details: dict = field(default_factory=dict)

# ====================================================================
# GERENCIADOR ESTRATÉGICO (Placar - fonte única de wins/losses)
# ====================================================================
class StrategicManager:
    def __init__(self):
        self.stop_loss_diario = 2
        self.meta_diaria = 999999
        self.wins = 0
        self.losses = 0
        self.losses_seguidas = 0

    def registrar_resultado(self, resultado: str):
        if resultado.upper() == "WIN":
            self.wins += 1
            self.losses_seguidas = 0
        else:
            self.losses += 1
            self.losses_seguidas += 1

    def check_permitir_operacao(self):
        if self.losses_seguidas >= self.stop_loss_diario:
            return False, "STOP_LOSS_CONSECUTIVO"
        return True, "OK"

def atualizar_painel_visual(manager):
    placar_str = f"STRIKE: {manager.wins}W - {manager.losses}L"
    print(f"\n[HUD UPDATE] {placar_str} | Sequência Loss: {manager.losses_seguidas}")

# ====================================================================
# CLASSIFICADOR LEGADO (não usado no fluxo principal, mantido compatibilidade)
# ====================================================================
class QuantClassifier:
    def __init__(self, alpha_engine_instance=None, tolerance: float = 0.0002):
        self.pending_signal = None
        self.signal_timeout = 5.0
        self.justiceiro = JusticeiroEngine(tolerance=tolerance)
        self._last_asset_id = 1
        self._last_price = 0.0
        self.alpha_engine_instance = alpha_engine_instance
        self.risk_config = RiskConfig()

    def update_market_data(self, ohlc: Dict):
        # O método process_data agora já lida com toques e gera "CALL"/"PUT"
        signal = self.justiceiro.process_data(ohlc)
        self._last_price = ohlc.get('close', 0.0)
        if signal != "WAIT":
            logger.info(f"[CLASSIFIER] Sinal gerado: {signal}")
            self.pending_signal = {
                "asset_id": self._last_asset_id,
                "direction": signal,
                "timestamp": time.time()
            }

    def classify(self, page=None) -> InferenceResult:
        """[LEGADO] Mantido para compatibilidade."""
        if self.pending_signal:
            elapsed = time.time() - self.pending_signal["timestamp"]
            if elapsed <= self.signal_timeout:
                direction = self.pending_signal["direction"]
                asset_id = self.pending_signal["asset_id"]
                entry_price = self._last_price
                self.pending_signal = None
                if direction == "CALL":
                    return InferenceResult(state=ScreenState.GATINHO_CALL, confidence=1.0,
                                           recommended_action="CLICK_ACIMA",
                                           details={"asset_id": asset_id, "entry_price": entry_price})
                else:
                    return InferenceResult(state=ScreenState.GATINHO_PUT, confidence=1.0,
                                           recommended_action="CLICK_ABAIXO",
                                           details={"asset_id": asset_id, "entry_price": entry_price})
            else:
                self.pending_signal = None
        return InferenceResult(state=ScreenState.WAITING_SIGNAL, confidence=1.0, recommended_action="WAIT")

    def _detect_posicao_aberta(self, html_str: str) -> bool:
        return False

# ====================================================================
# EXECUTOR DE AÇÕES (desativado)
# ====================================================================
class ActionExecutor:
    def __init__(self, page, coord_acima=(1221, 375), coord_abaixo=(1208, 483)):
        self.page = page
        self.coord_acima = coord_acima
        self.coord_abaixo = coord_abaixo

    def execute(self, result: InferenceResult):
        logger.warning("ActionExecutor.execute chamado mas está desativado. Use BrokerOperator.")
        return {"ok": False, "action_taken": "DISABLED"}

# ====================================================================
# ALPHA ENGINE (orquestrador principal)
# ====================================================================
class AlphaEngine:
    def __init__(self, tolerance: float = 0.0002, warmup_limit: int = 10, max_trades_session: int = 2):
        self.classifier = QuantClassifier(self, tolerance=tolerance)
        self.just_win = JustWinEngine()            # NOVO: engine JUST WIN
        self.candle_history = deque(maxlen=20)     # histórico para JUST WIN
        self._active_page = None
        self._cycle_count = 0
        self._last_result = None
        self._cooldown_until = 0.0
        self._stop_requested = False
        self._lock = threading.RLock()
        self.risk = RiskConfig()
        self.manager = StrategicManager()
        self.broker_ops = None
        self.autopilot_ativo = False

        # Configurações de tempo
        self.COOLDOWN_PADRAO = 1
        self.COOLDOWN_LOSS_SIMPLES = 5
        self.COOLDOWN_ANTI_TILT = 15

        # Estado do robô
        self.start_time = time.time()
        self._ws_connected_at: Optional[float] = None
        self.tempo_expiracao = 60

        # Parâmetros configuráveis
        self.warmup_limit = warmup_limit
        self.max_trades_session = 999999
        self.max_trades_simultaneos = 1
        self.trades_ativos = []
        self.target_active_id = 2298
        self._autopilot_start_time = 0
        self.warmup_count = 0
        self.trades_count = 0
        self.timeout_trade = 30

        # Estado dos trades
        self._trade_entry_price = 0.0
        self._trade_direction = ""
        self._trade_asset_id = None
        self._balance_before = 0.0

        # Telemetria
        self._suporte = None
        self._resistencia = None
        self.server_time = None

        # Thread watchdog
        self._watchdog_thread = threading.Thread(target=self._watchdog_loop, daemon=True)
        self._watchdog_thread.start()

    @property
    def is_trading(self) -> bool:
        with self._lock:
            return len(self.trades_ativos) >= self.max_trades_simultaneos

    def ligar_autopilot(self):
        with self._lock:
            # Limpeza dos buffers para evitar processamento de velas antigas
            self.just_win.history.clear()
            self.classifier.justiceiro.reset()
            logger.info("🧹 Buffers das estratégias (Just Win e Justiceiro) limpos.")

            self.autopilot_ativo = True
            self._autopilot_start_time = time.time()
            logger.info("🔍 Autopilot ativado. Analisando mercado por 5 minutos antes de operar...")

    def marcar_conexao_ws(self):
        self._ws_connected_at = time.time()
        logger.info("[WS] Conexão estabelecida. Warm-up ativado por 10 segundos.")

    def _is_warmup(self) -> bool:
        if self._ws_connected_at is None:
            return True
        return (time.time() - self._ws_connected_at) < 10.0

    def registrar_resultado(self, resultado: str, pnl: float = 0.0, trade_id: Any = None):
        with self._lock:
            trade_removido = False
            if self.trades_ativos:
                if trade_id and trade_id in self.trades_ativos:
                    self.trades_ativos.remove(trade_id)
                    trade_removido = True
                else:
                    self.trades_ativos.pop(0)
                    trade_removido = True

            # ✅ FIX: só conta se realmente havia um trade ativo para encerrar
            if not trade_removido:
                logger.warning("[RESULT] Resultado recebido sem trade ativo correspondente. Ignorado.")
                return

            logger.info(f"📊 Resultado: {resultado}. Slots ocupados: {len(self.trades_ativos)}/2")
            self.trades_count += 1
            if resultado.lower() == 'win':
                self.manager.registrar_resultado("WIN")
                self._cooldown_until = time.time() + self.COOLDOWN_PADRAO
                logger.info(f"[RESULT] WIN registrado. Cooldown de {self.COOLDOWN_PADRAO}s.")
            elif resultado.lower() == 'loss':
                self.manager.registrar_resultado("LOSS")
                if self.manager.losses_seguidas >= 2:
                    self._cooldown_until = time.time() + self.COOLDOWN_ANTI_TILT
                    logger.warning(f"[RESULT] LOSS consecutivo (#{self.manager.losses_seguidas}). Cooldown anti-tilt de {self.COOLDOWN_ANTI_TILT}s.")
                else:
                    self._cooldown_until = time.time() + self.COOLDOWN_LOSS_SIMPLES
                    logger.info(f"[RESULT] LOSS registrado. Cooldown de {self.COOLDOWN_LOSS_SIMPLES}s.")
            else:
                self._cooldown_until = time.time() + self.COOLDOWN_PADRAO
                logger.warning(f"[RESULT] Resultado desconhecido (timeout). Cooldown de {self.COOLDOWN_PADRAO}s.")
            self.risk.update_result(pnl)

            # Persistência Assíncrona no JSON Raiz
            dados_para_salvar = {
                "trade_id": trade_id or f"T_{int(time.time())}",
                "timestamp_epoch": time.time(),
                "resultado": resultado,
                "pnl": pnl,
                "placar_momento": f"{self.manager.wins}W - {self.manager.losses}L",
                "loss_seguidas": self.manager.losses_seguidas,
                "total_trades_sessao": self.trades_count,
                "max_trades_limite": self.max_trades_session
            }

            try:
                loop = asyncio.get_running_loop()
                loop.create_task(salvar_trade_json_raiz(dados_para_salvar))
            except RuntimeError:
                asyncio.run(salvar_trade_json_raiz(dados_para_salvar))

            logger.info(f"💾 [ALPHA] Resultado '{resultado}' enviado para a fila de persistência JSON raiz.")
            logger.info(json.dumps({
                "event": "TRADE_RESULT",
                "resultado": resultado,
                "wins": self.manager.wins,
                "losses": self.manager.losses,
                "losses_seguidas": self.manager.losses_seguidas,
                "cooldown_ate": self._cooldown_until,
                "timestamp": datetime.now().isoformat()
            }))

    def executar_disparo(self, direcao: str) -> Optional[str]:
        with self._lock:
            agora = time.time()

            # Bloqueia durante o período de análise
            tempo_passado = agora - self._autopilot_start_time
            tempo_analise = 300  # 5 minutos
            if self.autopilot_ativo and tempo_passado < tempo_analise:
                restante = int(tempo_analise - tempo_passado)
                logger.info(f"⏳ Análise de mercado em curso: {restante}s restantes. Sinal ignorado.")
                return None

            if agora < self._cooldown_until:
                restante = int(self._cooldown_until - agora)
                logger.info(f"⏳ Cooldown ativo: {restante}s restantes. Sinal ignorado.")
                return None
            if self._is_warmup():
                logger.info("⏳ Warm-up ativo (10s após conexão). Sinal ignorado.")
                return None

            if self.trades_count >= self.max_trades_session:
                logger.info(f"🏁 Sessão encerrada: {self.trades_count}/{self.max_trades_session} trades concluídos.")
                return None

            if self.is_trading:
                logger.info(f"⚠️ {len(self.trades_ativos)} trade(s) em aberto. Aguardando resultado.")
                return None

            permitido, motivo = self.manager.check_permitir_operacao()
            if not permitido:
                logger.warning(f"Operação bloqueada: {motivo}")
                return None

            # --- ANTI-SPAM DE TICK: cooldown imediato de 10 segundos ---
            self._cooldown_until = time.time() + 10
            self._trade_direction = direcao
            logger.info(f"🎯 Disparo autorizado: {direcao} (cooldown de 10s ativado)")
            return direcao

    def processar_dados(self, data: Dict) -> Optional[str]:
        """Processa um conjunto de dados OHLC e retorna direção se houver sinal (Justiceiro ou JUST WIN)."""
        if not self.autopilot_ativo:
            self.warmup_count = 0
            return None

        self.warmup_count += 1
        if self.warmup_count <= self.warmup_limit:
            if self.warmup_count % 2 == 0:
                logger.info(f"⏳ Aquecendo: {self.warmup_count}/{self.warmup_limit} sinais recebidos...")
            return None

        price = data.get("price")
        o = data.get("open")
        h = data.get("high")
        l = data.get("low")
        c = data.get("close")
        if any(v is None for v in [price, o, h, l, c]):
            return None

        ohlc = {"open": o, "high": h, "low": l, "close": c, "current": price}

        # 1. Estratégia Velas de Comando (Justiceiro)
        sinal_just = self.classifier.justiceiro.process_data(ohlc)
        if sinal_just != "WAIT":
            return self.executar_disparo(sinal_just)

        # 2. Estratégia JUST WIN (momentum)
        # Adiciona a vela atual ao histórico e verifica condição
        self.just_win.add_candle(o, c)
        sinal_jw = self.just_win.check_signal()
        if sinal_jw:
            logger.info(f"[JUST WIN] Sinal detectado: {sinal_jw}")
            return self.executar_disparo(sinal_jw)

        return None

    def processar_ws(self, payload: str):
        try:
            data = json.loads(payload)
            with self._lock:
                if self._ws_connected_at is None:
                    self.marcar_conexao_ws()

                if data.get("name") == "candle-generated":
                    msg = data.get("msg", {})
                    active_id = msg.get("active_id")
                    if active_id != self.target_active_id:
                        logger.debug(f"[WS] Candle de ativo {active_id} ignorado.")
                        return

                    preco_atual = msg.get("close")
                    if preco_atual is None:
                        return
                    telemetria = {
                        "price": preco_atual,
                        "open": msg.get("open"),
                        "high": msg.get("max"),
                        "low": msg.get("min"),
                        "close": preco_atual
                    }
                    sinal = self.processar_dados(telemetria)
                    if sinal and self.broker_ops:
                        logger.info(f"[WS] Executando ordem {sinal} via BrokerOperator")
                        res = self.broker_ops.executar_ordem(sinal)
                        if res and res.get("ok") and res.get("status") == "ENQUEUED":
                            trade_id = time.time()
                            with self._lock:
                                self.trades_ativos.append(trade_id)
                            logger.info(f"🚀 Ordem enfileirada. Bloqueando por {self.tempo_expiracao}s...")

                elif data.get("name") == "order-closed":
                    lucro = data.get("msg", {}).get("profit", 0)
                    resultado = "win" if lucro > 0 else "loss"
                    self.registrar_resultado(resultado, pnl=lucro)

                elif data.get("name") == "timeSync":
                    self.server_time = data.get("msg")

        except Exception as e:
            logger.error(f"[WS] Erro ao processar payload: {e}\nPayload: {payload[:200]}")

    def _watchdog_loop(self):
        while True:
            time.sleep(5)
            self.monitorar_estrategia(0.0)

    def monitorar_estrategia(self, preco_atual: float):
        with self._lock:
            if self.trades_count >= self.max_trades_session:
                if not self.is_trading:
                    logger.info(f"🏁 [LIMITE] Máximo de {self.max_trades_session} trades atingido. Aguardando reset.")
                return

            agora = time.time()
            tempo_maximo_espera = getattr(self, 'tempo_expiracao', 60) + 15
            for tid in list(self.trades_ativos):
                if (agora - tid) > tempo_maximo_espera:
                    logger.warning(f"⚠️ [SAFETY] Timeout de {tempo_maximo_espera}s para trade {tid}. Forçando reset.")
                    self.registrar_resultado("unknown", trade_id=tid)

    # ========== Métodos de compatibilidade ==========
    def get_status(self) -> Dict:
        with self._lock:
            agora = time.time()
            cooldown_restante = max(0, int(self._cooldown_until - agora))
            suportes, resistencias = self.classifier.justiceiro.get_current_levels()
            return {
                "status": "ACTIVE" if self._ws_connected_at else "IDLE",
                "is_trading": self.is_trading,
                "trades_ativos_count": len(self.trades_ativos),
                "cooldown_restante_s": cooldown_restante,
                "loss_seguidas": self.manager.losses_seguidas,
                "placar": f"{self.manager.wins}W - {self.manager.losses}L",
                "warmup": self._is_warmup(),
                "trades_count": self.trades_count,
                "max_trades": self.max_trades_session,
                "suportes_ativos": suportes,
                "resistencias_ativas": resistencias
            }

    def attach(self, page):
        self._active_page = page

    def perceive_and_act(self) -> Dict:
        return {"cycle_id": "0", "state": ScreenState.IDLE, "recommended_action": "WAIT"}

    def get_balance(self):
        return None

    def request_stop(self):
        with self._lock:
            self._stop_requested = True

    def process_trade_result(self):
        return "UNKNOWN", 0.0

# Instância global
alpha_engine = AlphaEngine(tolerance=0.0002, warmup_limit=10, max_trades_session=999999)