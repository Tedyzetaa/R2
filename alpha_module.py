# filename: alpha_module.py
# ============================================================
# REFATORAÇÃO FINAL: Estratégias Justiceiro + Macro Tendência + Quadrantes Blitz
# - Velas de Comando: suporte/resistência com max 2 toques
# - JUST WIN: momentum híbrido
# - MacroTendenciaEngine: LTA/LTB com warmup de 15min, limite de 3 toques, filtro anti-rompimento
# - QuadranteBlitzEngine: quadrantes de 30s, sinal pela 2ª vela, filtro direcional pela macro
# - Persistência assíncrona em historico_trades_alpha.json
# - Gerenciamento de risco via StrategicManager (sem RiskConfig externo)
# ============================================================
# [RSI ENGINE + CANDLE LOCK + FILTRO DE EXAUSTÃO]
# - RSI clássico de Wilder (14 períodos, overbought=70, oversold=30)
# - Candle Lock: uma operação por timestamp de vela (bloqueio rígido)
# - Filtro RSI: cancela CALL se RSI >= 70, cancela PUT se RSI <= 30
# - Status expõe rsi_atual no painel visual
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

# ==================================================================
# FUNÇÃO DE PERSISTÊNCIA ASSÍNCRONA (JSON raiz)
# ==================================================================
async def salvar_trade_json_raiz(dados_trade: dict):
    """Grava o resultado do trade de forma assíncrona em um arquivo JSON na raiz."""
    log_file = "historico_trades_alpha.json"
    if "timestamp_registro" not in dados_trade:
        dados_trade["timestamp_registro"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        historico = []
        if os.path.exists(log_file):
            async with aiofiles.open(log_file, mode='r', encoding='utf-8') as f:
                conteudo = await f.read()
                if conteudo.strip():
                    historico = json.loads(conteudo)
        historico.append(dados_trade)
        async with aiofiles.open(log_file, mode='w', encoding='utf-8') as f:
            await f.write(json.dumps(historico, indent=4, ensure_ascii=False))
    except Exception as e:
        logger.error(f"Erro ao salvar log do trade: {e}")

# ==================================================================
# JUST WIN ENGINE (momentum) – mantido do original
# ==================================================================
class JustWinEngine:
    def __init__(self, max_history: int = 20):
        self.history = deque(maxlen=max_history)

    def add_candle(self, open_price: float, close_price: float) -> None:
        self.history.append({"open": open_price, "close": close_price})

    def check_signal(self) -> Optional[str]:
        if len(self.history) < 9:
            return None
        close0 = self.history[-1]["close"]
        close2 = self.history[-3]["close"]
        open2  = self.history[-3]["open"]
        close4 = self.history[-5]["close"]
        close8 = self.history[-9]["close"]
        if (close0 > close2) and (close2 > open2) and (close4 > close8):
            return "CALL"
        elif (close0 < close2) and (close2 < open2) and (close4 < close8):
            return "PUT"
        return None

# ==================================================================
# JUSTICEIRO ENGINE (Velas de Comando) – mantido do original
# ==================================================================
class JusticeiroEngine:
    def __init__(self, tolerance: float = 0.0002, max_touches: int = 2):
        self.tolerance = tolerance
        self.max_touches = max_touches
        self.suportes: List[Dict] = []
        self.resistencias: List[Dict] = []

    def process_data(self, ohlc: Dict) -> str:
        o = ohlc.get('open')
        h = ohlc.get('high')
        l = ohlc.get('low')
        c = ohlc.get('close')
        curr = ohlc.get('current', c)
        if o == l and c > o:
            self._add_nivel(self.suportes, o)
            logger.info(f"[JUSTICEIRO] 🛡️ Novo SUPORTE em {o:.5f}")
        elif o == h and c < o:
            self._add_nivel(self.resistencias, o)
            logger.info(f"[JUSTICEIRO] 🔴 Nova RESISTÊNCIA em {o:.5f}")
        if self._check_touches(self.suportes, curr, upper=False):
            return "CALL"
        if self._check_touches(self.resistencias, curr, upper=True):
            return "PUT"
        return "WAIT"

    def _add_nivel(self, lista: List[Dict], price: float) -> None:
        if not any(abs(n['price'] - price) <= self.tolerance for n in lista):
            lista.append({"price": price, "touches": 0, "last_touch_time": 0})

    def _check_touches(self, lista: List[Dict], current_price: float, upper: bool) -> bool:
        agora = time.time()
        for i, nivel in enumerate(lista):
            price = nivel['price']
            if upper:
                if current_price >= price - self.tolerance:
                    ultimo_toque = nivel.get('last_touch_time', 0)
                    if agora - ultimo_toque < 1.0:
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
                        continue
                    nivel['touches'] += 1
                    nivel['last_touch_time'] = agora
                    logger.info(f"[JUSTICEIRO] ⚡ Toque em SUPORTE {price:.5f} (toque #{nivel['touches']}/{self.max_touches})")
                    if nivel['touches'] >= self.max_touches:
                        lista.pop(i)
                    return True
        return False

    def get_current_levels(self) -> Tuple[List[float], List[float]]:
        return ([n['price'] for n in self.suportes], [n['price'] for n in self.resistencias])

    def reset(self):
        self.suportes.clear()
        self.resistencias.clear()

# ==================================================================
# RSI ENGINE (Relative Strength Index) – Wilder Smoothing com deque
# ==================================================================
class RSIEngine:
    def __init__(self, period: int = 14, overbought: float = 80.0, oversold: float = 20.0):
        self.period = period
        self.overbought = overbought
        self.oversold = oversold
        self.prices = deque(maxlen=period + 1)
        self.avg_gain = None
        self.avg_loss = None
        self.current_rsi = None  # Variável nativa adicionada aqui

    def add_price(self, close_price: float) -> Optional[float]:
        self.prices.append(close_price)
        if len(self.prices) < 2:
            self.current_rsi = None
            return None
        
        gain = max(0.0, self.prices[-1] - self.prices[-2])
        loss = max(0.0, self.prices[-2] - self.prices[-1])

        if self.avg_gain is None:
            if len(self.prices) == self.period + 1:
                gains = [max(0.0, self.prices[i] - self.prices[i-1]) for i in range(1, len(self.prices))]
                losses = [max(0.0, self.prices[i-1] - self.prices[i]) for i in range(1, len(self.prices))]
                self.avg_gain = sum(gains) / self.period
                self.avg_loss = sum(losses) / self.period
            else:
                self.current_rsi = None
                return None
        else:
            self.avg_gain = (self.avg_gain * (self.period - 1) + gain) / self.period
            self.avg_loss = (self.avg_loss * (self.period - 1) + loss) / self.period

        if self.avg_loss == 0:
            self.current_rsi = 100.0
            return 100.0
            
        rs = self.avg_gain / self.avg_loss
        rsi_valor = 100.0 - (100.0 / (1.0 + rs))
        
        self.current_rsi = rsi_valor # Salvando o valor a cada tick
        return rsi_valor

    def reset(self):
        self.prices.clear()
        self.avg_gain = None
        self.avg_loss = None

# ==================================================================
# MACRO TENDÊNCIA ENGINE (LTA/LTB)
# ==================================================================
class MacroTendenciaEngine:
    """Linhas de Tendência (LTA - suporte inclinado, LTB - resistência inclinada)
       com warmup de 15 minutos, limite de 3 toques e filtro anti-rompimento."""
    def __init__(self, warmup_seconds: int = 900, max_touches: int = 3):
        self.warmup_seconds = warmup_seconds
        self.max_touches = max_touches
        self.start_time: Optional[float] = None
        self.tops: deque = deque()          # (timestamp, high)
        self.bottoms: deque = deque()       # (timestamp, low)
        self.lta_slope: Optional[float] = None   # linha de alta (suporte)
        self.lta_intercept: Optional[float] = None
        self.ltb_slope: Optional[float] = None   # linha de baixa (resistência)
        self.ltb_intercept: Optional[float] = None
        self.touches_lta: int = 0
        self.touches_ltb: int = 0
        self.history_bodies: deque = deque(maxlen=20)  # Histórico para filtro de exaustão
        self.pending_touch: Optional[Dict] = None   # {"type": "LTA"/"LTB", "candle_count": int, "price": float, "timestamp": float}

    def start_warmup(self, current_time: float) -> None:
        self.start_time = current_time
        self.tops.clear()
        self.bottoms.clear()
        self.lta_slope = self.ltb_slope = None
        self.touches_lta = self.touches_ltb = 0
        self.pending_touch = None
        logger.info("[MACRO] Warmup iniciado por 15 minutos. Coletando extremos M1...")

    def is_warming_up(self, current_time: float) -> bool:
        if self.start_time is None:
            return True
        return (current_time - self.start_time) < self.warmup_seconds

    def add_candle(self, timestamp: float, high: float, low: float, open_p: float = 0, close_p: float = 0) -> None:
        """Adiciona os extremos de um candle M1."""
        self.tops.append((timestamp, high))
        self.bottoms.append((timestamp, low))
        self.history_bodies.append(abs(close_p - open_p))
        if len(self.tops) > 100:
            self.tops.popleft()
        if len(self.bottoms) > 100:
            self.bottoms.popleft()
        self._recalculate_lines()

    def _recalculate_lines(self) -> None:
        """Regressão linear simples sobre fundos (LTA) e topos (LTB)."""
        if len(self.bottoms) >= 3:
            n = len(self.bottoms)
            sum_x = sum(t for t, _ in self.bottoms)
            sum_y = sum(p for _, p in self.bottoms)
            sum_xy = sum(t * p for t, p in self.bottoms)
            sum_x2 = sum(t * t for t, _ in self.bottoms)
            denom = n * sum_x2 - sum_x * sum_x
            if denom != 0:
                slope = (n * sum_xy - sum_x * sum_y) / denom
                intercept = (sum_y - slope * sum_x) / n
                if slope > 0:   # tendência de alta
                    self.lta_slope = slope
                    self.lta_intercept = intercept
        if len(self.tops) >= 3:
            n = len(self.tops)
            sum_x = sum(t for t, _ in self.tops)
            sum_y = sum(p for _, p in self.tops)
            sum_xy = sum(t * p for t, p in self.tops)
            sum_x2 = sum(t * t for t, _ in self.tops)
            denom = n * sum_x2 - sum_x * sum_x
            if denom != 0:
                slope = (n * sum_xy - sum_x * sum_y) / denom
                intercept = (sum_y - slope * sum_x) / n
                if slope < 0:   # tendência de baixa
                    self.ltb_slope = slope
                    self.ltb_intercept = intercept

    def get_line_price(self, timestamp: float, line_type: str) -> Optional[float]:
        if line_type == "LTA" and self.lta_slope is not None and self.lta_intercept is not None:
            return self.lta_slope * timestamp + self.lta_intercept
        if line_type == "LTB" and self.ltb_slope is not None and self.ltb_intercept is not None:
            return self.ltb_slope * timestamp + self.ltb_intercept
        return None

    def check_touch(self, candle: Dict, tolerance: float = 0.0002) -> Optional[str]:
        """
        Verifica se o preço atual toca LTA ou LTB.
        Padronizado para receber o candle (dict) e a tolerância.
        """
        current_price = candle.get('current', candle.get('close'))
        timestamp = candle.get('timestamp', time.time())

        if self.is_warming_up(timestamp):
            return None

        # Filtro de Exaustão: ignora picos de volatilidade perigosos
        if len(self.history_bodies) >= 5:
            medias_corpos = sum(list(self.history_bodies)[-5:]) / 5
            corpo_vela_atual = abs(current_price - candle.get('open', current_price))
            if corpo_vela_atual > (medias_corpos * 2.5):
                logger.info("⚠️ [MACRO] Toque ignorado: Vela de força anormal (Anti-Trator).")
                return None

        # Verifica LTA
        lta_price = self.get_line_price(timestamp, "LTA")
        if lta_price is not None and abs(current_price - lta_price) <= tolerance:
            if self.touches_lta < self.max_touches:
                # Inicia estado pendente para filtro anti-rompimento
                self.pending_touch = {"type": "LTA", "candle_count": 0, "price": current_price, "timestamp": timestamp}
                return "LTA"
        # Verifica LTB
        ltb_price = self.get_line_price(timestamp, "LTB")
        if ltb_price is not None and abs(current_price - ltb_price) <= tolerance:
            if self.touches_ltb < self.max_touches:
                self.pending_touch = {"type": "LTB", "candle_count": 0, "price": current_price, "timestamp": timestamp}
                return "LTB"
        return None

    def update_candle_close(self, close_price: float, timestamp: float, tolerance: float = 0.0002) -> Optional[str]:
        """Atualiza o estado pendente com o fechamento do candle.
           Retorna o tipo de linha ("LTA"/"LTB") se houver confirmação (rejeição),
           ou None se cancelado (lateralização) ou ainda pendente."""
        if self.pending_touch is None:
            return None
        line_type = self.pending_touch["type"]
        line_price = self.get_line_price(timestamp, line_type)
        if line_price is None:
            self.pending_touch = None
            return None
        distance = abs(close_price - line_price)
        # Rejeição: fechou longe da linha (> 2*tolerance)
        if distance > 2 * tolerance:
            # Confirma sinal
            if line_type == "LTA":
                self.touches_lta += 1
            else:
                self.touches_ltb += 1
            logger.info(f"[MACRO] Sinal confirmado: {line_type} (rejeição, distância {distance:.5f})")
            self.pending_touch = None
            return line_type
        # Lateralização: fechou perto da linha
        self.pending_touch["candle_count"] += 1
        if self.pending_touch["candle_count"] >= 2:
            logger.info(f"[MACRO] Toque cancelado em {line_type} devido a lateralização por 2 candles.")
            self.pending_touch = None
        return None

    def get_trend_direction(self) -> Optional[str]:
        """Retorna "UP" se há LTA ativa, "DOWN" se LTB ativa, None caso contrário."""
        if self.lta_slope is not None and self.lta_slope > 0:
            return "UP"
        if self.ltb_slope is not None and self.ltb_slope < 0:
            return "DOWN"
        return None

    def reset(self):
        self.start_time = None
        self.tops.clear()
        self.bottoms.clear()
        self.lta_slope = self.ltb_slope = None
        self.touches_lta = self.touches_ltb = 0
        self.pending_touch = None

# ==================================================================
# QUADRANTE BLITZ ENGINE (30s)
# ==================================================================
class QuadranteBlitzEngine:
    """Estratégia probabilística baseada em quadrantes de 30s.
       Sinal pela 2ª vela do quadrante: se VERDE -> CALL, VERMELHA -> PUT.
       Só executa se alinhado com a macro tendência."""
    def __init__(self, quadrant_duration: float = 30.0):
        self.quadrant_duration = quadrant_duration
        self.current_quadrant_start: Optional[float] = None
        self.candles_in_quadrant: List[Dict] = []   # {"open": o, "close": c}
        self.pending_signal: Optional[Dict] = None  # {"direction": "CALL"/"PUT", "quadrant_end": float}

    def reset(self):
        self.current_quadrant_start = None
        self.candles_in_quadrant.clear()
        self.pending_signal = None

    def add_candle(self, candle: Dict, timestamp: float) -> None:
        """Adiciona um candle de 30 segundos (deve ter 'open' e 'close')."""
        if self.current_quadrant_start is None:
            self.current_quadrant_start = (timestamp // self.quadrant_duration) * self.quadrant_duration
            self.candles_in_quadrant.clear()

        quadrant_end = self.current_quadrant_start + self.quadrant_duration
        if timestamp >= quadrant_end:
            # Mudou de quadrante: mantém o sinal pendente para o próximo
            self.current_quadrant_start = quadrant_end
            self.candles_in_quadrant.clear()

        self.candles_in_quadrant.append(candle)

        # Quando a segunda vela chega, determina a direção
        if len(self.candles_in_quadrant) == 2:
            second = self.candles_in_quadrant[1]
            o_2, c_2 = second['open'], second['close']
            h_2, l_2 = second.get('high', c_2), second.get('low', c_2)
            
            corpo = abs(c_2 - o_2)
            pavio_superior = h_2 - max(o_2, c_2)
            pavio_inferior = min(o_2, c_2) - l_2

            # Se o pavio contra a operação for maior que 80% do corpo, aborta
            if c_2 > o_2 and pavio_superior > (corpo * 0.8):
                logger.info("⚠️ [BLITZ] CALL abortado: Rejeição superior forte.")
                return
            if c_2 < o_2 and pavio_inferior > (corpo * 0.8):
                logger.info("⚠️ [BLITZ] PUT abortado: Rejeição inferior forte.")
                return

            if c_2 > o_2:
                direction = "CALL"
            else:
                direction = "PUT"
            self.pending_signal = {
                "direction": direction,
                "quadrant_end": quadrant_end
            }
            logger.info(f"[QUADRANT] Segunda vela do quadrante fechou em {direction}. Aguardando próximo quadrante.")

    def get_signal(self, current_timestamp: float, macro_trend: Optional[str]) -> Optional[str]:
        """Retorna a direção do sinal se o próximo quadrante já começou e a macro tendência permite."""
        if self.pending_signal is None:
            return None
        if current_timestamp < self.pending_signal["quadrant_end"]:
            return None   # ainda dentro do mesmo quadrante
        direction = self.pending_signal["direction"]
        # Filtro direcional
        if macro_trend == "UP" and direction == "PUT":
            logger.info(f"[QUADRANT] Sinal {direction} bloqueado por macro tendência de alta.")
            self.pending_signal = None
            return None
        if macro_trend == "DOWN" and direction == "CALL":
            logger.info(f"[QUADRANT] Sinal {direction} bloqueado por macro tendência de baixa.")
            self.pending_signal = None
            return None
        logger.info(f"[QUADRANT] Sinal liberado: {direction}")
        self.pending_signal = None
        return direction

# ==================================================================
# FIBONACCI ENGINE
# ==================================================================
class FibonacciEngine:
    def __init__(self, lookback_candles: int = 30):
        self.lookback_candles = lookback_candles
        self.levels = {}
        # Regra do canal: monitorar no máximo 2 toques por nível [00:03:17]
        self.touch_count = {0.236: 0, 0.382: 0, 0.500: 0, 0.618: 0}
        self.current_trend = "NONE"
        self.last_high = 0.0
        self.last_low = 0.0

    def update_levels(self, candles: list, macro_trend: str):
        """
        Calcula as retrações de Fibonacci com base no início e pico da tendência recente [00:01:50].
        """
        if len(candles) < 10:
            return
        
        # Obtém os limites máximos e mínimos dentro da janela lookback
        recent_candles = list(candles)[-self.lookback_candles:]
        highs = [c.get('high', c.get('close')) for c in recent_candles]
        lows = [c.get('low', c.get('close')) for c in recent_candles]
        
        absolute_high = max(highs)
        absolute_low = min(lows)
        
        # Se a estrutura de preço não mudou, mantém os níveis atuais
        if absolute_high == self.last_high and absolute_low == self.last_low:
            return
            
        self.last_high = absolute_high
        self.last_low = absolute_low
        diff = absolute_high - absolute_low
        
        if diff == 0:
            return

        self.current_trend = macro_trend
        # Reseta os toques sempre que uma nova malha/pico de Fibo for recalculada
        self.touch_count = {0.236: 0, 0.382: 0, 0.500: 0, 0.618: 0}
        
        # Traçamento matemático baseado na direção da tendência macro [00:02:02]
        if macro_trend == "ALTA":
            self.levels = {
                0.236: absolute_high - (0.236 * diff),
                0.382: absolute_high - (0.382 * diff),  # Nível Forte
                0.500: absolute_high - (0.500 * diff),
                0.618: absolute_high - (0.618 * diff)   # Nível Forte
            }
        elif macro_trend == "BAIXA":
            self.levels = {
                0.236: absolute_low + (0.236 * diff),
                0.382: absolute_low + (0.382 * diff),   # Nível Forte
                0.500: absolute_low + (0.500 * diff),
                0.618: absolute_low + (0.618 * diff)    # Nível Forte
            }

    def check_signal(self, current_price: float) -> Optional[str]:
        """
        Verifica se o preço atual tocou em uma região válida respeitando o limite de toques.
        """
        if not self.levels or self.current_trend == "NONE":
            return None
            
        # Margem de proximidade em taxa para o par operado (ajustável)
        threshold = 0.00002 
        
        for lvl, price_target in self.levels.items():
            # Aborta se o nível já saturou os 2 toques permitidos [00:03:17]
            if self.touch_count[lvl] >= 2:
                continue
                
            if abs(current_price - price_target) <= threshold:
                self.touch_count[lvl] += 1
                logger.info(f"🎯 [FIBO] Toque detectado no nível {lvl * 100}% (Toque {self.touch_count[lvl]}/2)")
                
                # Retração a favor da macro tendência [00:03:27]
                if self.current_trend == "ALTA":
                    return "CALL"
                elif self.current_trend == "BAIXA":
                    return "PUT"
                    
        return None

# ==================================================================
# CLASSIFICADOR LEGADO (compatibilidade)
# ==================================================================
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

class QuantClassifier:
    def __init__(self, alpha_engine_instance=None, tolerance: float = 0.0002):
        self.pending_signal = None
        self.signal_timeout = 5.0
        self.justiceiro = JusticeiroEngine(tolerance=tolerance)
        self._last_asset_id = 1
        self._last_price = 0.0
        self.alpha_engine_instance = alpha_engine_instance

    def update_market_data(self, ohlc: Dict):
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

# ==================================================================
# ACTION EXECUTOR (desativado, mantido compatibilidade)
# ==================================================================
class ActionExecutor:
    def __init__(self, page, coord_acima=(1221, 375), coord_abaixo=(1208, 483)):
        self.page = page
        self.coord_acima = coord_acima
        self.coord_abaixo = coord_abaixo

    def execute(self, result: InferenceResult):
        logger.warning("ActionExecutor.execute chamado mas está desativado. Use BrokerOperator.")
        return {"ok": False, "action_taken": "DISABLED"}

# ==================================================================
# STRATEGIC MANAGER (gerenciamento de win/loss e stop consecutivo)
# ==================================================================
class StrategicManager:
    def __init__(self):
        self.stop_loss_diario = 2          # número de losses consecutivos para parar
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

# ==================================================================
# ALPHA ENGINE (orquestrador principal com integração das estratégias)
# ==================================================================
class AlphaEngine:
    def __init__(self, tolerance: float = 0.0002, warmup_limit: int = 10, max_trades_session: int = 2):
        # Motores analíticos
        self.classifier = QuantClassifier(self, tolerance=tolerance)
        self.just_win = JustWinEngine()
        self.macro_tendencia = MacroTendenciaEngine(warmup_seconds=900, max_touches=3)
        self.quadrante_blitz = QuadranteBlitzEngine(quadrant_duration=30.0)
        self.fibonacci = FibonacciEngine(lookback_candles=30)
        self.rsi = RSIEngine(period=14, overbought=80.0, oversold=20.0)   # RSI Engine integrada (Ajustado 80/20)

        # Estado interno
        self._active_page = None
        self._cycle_count = 0
        self._last_result = None
        self._cooldown_until = 0.0
        self._stop_requested = False
        self._lock = threading.RLock()
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
        self._candle_history = deque(maxlen=100)

        # Parâmetros configuráveis
        self.warmup_limit = warmup_limit
        self.max_trades_session = max_trades_session
        self.max_trades_simultaneos = 1
        self.trades_ativos = []
        self.target_active_id = 2298
        self._autopilot_start_time = 0
        self.warmup_count = 0
        self.trades_count = 0
        self.timeout_trade = 30

        # Estado dos trades (Telemetria Avançada)
        self._trade_entry_price = 0.0
        self._trade_direction = ""
        self._last_trade_strategy = "unknown"
        self._last_trade_context = {}  # 👈 NOVO: Guarda o raio-X da decisão
        self._trade_asset_id = None
        self._balance_before = 0.0
        
        # 🔒 CANDLE LOCK RÍGIDO (impede múltiplas operações na mesma vela)
        self.ultima_vela_operada = None

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
            self.just_win.history.clear()
            self.classifier.justiceiro.reset()
            self.macro_tendencia.reset()
            self.quadrante_blitz.reset()
            self.fibonacci.levels = {}
            self.rsi.reset()                           # reset do RSI
            self._candle_history.clear()
            self.autopilot_ativo = True
            self._autopilot_start_time = time.time()
            # Limpa o candle lock ao iniciar autopilot
            self.ultima_vela_operada = None
            # Inicia warmup da macro tendência
            self.macro_tendencia.start_warmup(time.time())
            logger.info("🔍 Autopilot ativado. Warmup de 15 min para Macro Tendência...")

    def marcar_conexao_ws(self):
        self._ws_connected_at = time.time()
        self.macro_tendencia.start_warmup(time.time())
        logger.info("[WS] Conexão estabelecida. Warm-up de 15 min para Macro Tendência.")

    def _is_warmup(self) -> bool:
        if self._ws_connected_at is None:
            return True
        return (time.time() - self._ws_connected_at) < 10.0

    def executar_disparo(self, direcao: str, estrategia: str = "unknown", timestamp_vela: Optional[float] = None, contexto: Optional[Dict] = None) -> Optional[str]:
        """Valida se pode operar e dispara a ordem. Aplica cooldown e grava contexto do trade."""
        with self._lock:
            agora = time.time()

            if self.autopilot_ativo and (agora - self._autopilot_start_time) < 300:
                logger.info("⏳ Análise de mercado em curso (5 min). Sinal ignorado.")
                return None
            if agora < self._cooldown_until:
                return None
            if self._is_warmup():
                return None
            if self.trades_count >= self.max_trades_session:
                return None
            if self.is_trading:
                return None
            permitido, motivo = self.manager.check_permitir_operacao()
            if not permitido:
                return None

            # --- TRAVA ANTI-SPAM E TELEMETRIA ---
            self._cooldown_until = time.time() + 10
            self._trade_direction = direcao
            self._last_trade_strategy = estrategia
            self._last_trade_context = contexto or {}  # 👈 Grava as razões da decisão
            
            if timestamp_vela is not None:
                self.ultima_vela_operada = timestamp_vela

            logger.info(f"🎯 Disparo autorizado: {direcao} (estratégia {estrategia}) - Contexto gravado.")
            return direcao

    def _check_composite_signal(self, ohlc: Dict, timestamp: float, is_30s_candle: bool) -> Optional[Tuple[str, str, Dict]]:
        """
        Avalia as estratégias com critérios refinados de confluência e flexibilidade de tempo.
        """
        price = ohlc.get('current', ohlc.get('close'))
        macro_dir = self.macro_tendencia.get_trend_direction() # "UP", "DOWN" ou None

        # 0. Extração do segundo atual da vela para validação cirúrgica de timing
        dt_objeto = datetime.fromtimestamp(timestamp)
        segundo_atual = dt_objeto.second

        # Cálculo do RSI (apenas em candles M1)
        rsi_val = None
        if not is_30s_candle:
            rsi_val = self.rsi.add_price(price)

        if rsi_val is not None:
            logger.info(f"[MÓDULO ALPHA] RSI Atual: {rsi_val:.2f}")

        # 📦 PACOTE DE CONTEXTO DA DECISÃO
        contexto_mercado = {
            "rsi_no_clique": round(rsi_val, 2) if rsi_val is not None else "WARMUP",
            "macro_tendencia": macro_dir or "LATERAL",
            "segundo_da_vela": segundo_atual,
            "preco_captura": price
        }

        # ------------------------------------------------------------------
        # FILTRO CENTRALIZADO ADAPTATIVO (OTIMIZADO PARA OPÇÕES 1 MINUTO)
        # ------------------------------------------------------------------
        def filtrar_sinal_final(direcao: Optional[str], estrategia: str) -> Optional[Tuple[str, str, Dict]]:
            if not direcao:
                return None

            # 1. VALIDAÇÃO DE TIMING FLEXÍVEL (Slippage Zero)
            if segundo_atual > 5 and segundo_atual < 20:
                logger.warning(f"🕒 [FILTRO TEMPO] Sinal {direcao} ({estrategia}) abortado no segundo {segundo_atual} (Zona de Limbo).")
                return None
            if segundo_atual >= 45:
                logger.warning(f"🕒 [FILTRO TEMPO] Sinal {direcao} ({estrategia}) abortado no segundo {segundo_atual} (Risco de Slippage).")
                return None

            # 2. Filtro de Tendência Macro Estrito (A favor da maré)
            if direcao == "CALL" and macro_dir == "DOWN":
                return None
            if direcao == "PUT" and macro_dir == "UP":
                return None

            # 3. FILTRO ANTI-TRATOR GLOBAL (Crucial para OTC)
            corpo_vela = ohlc['close'] - ohlc['open']
            abs_corpo = abs(corpo_vela)
            if len(self._candle_history) > 5:
                historico = list(self._candle_history)
                # Calcula a média dos corpos das últimas 5 velas (excluindo a atual)
                avg_body = sum(abs(c['close'] - c['open']) for c in historico[-6:-1]) / 5
                
                if avg_body > 0 and abs_corpo > (avg_body * 2.5):
                    # Se a vela trator for contra a nossa direção, ABORTA
                    if (direcao == "CALL" and corpo_vela < 0) or (direcao == "PUT" and corpo_vela > 0):
                        logger.warning(f"⚠️ [ANTI-TRATOR] Vela gigante detectada contra a operação. Abortando {estrategia}.")
                        return None

            # 4. Filtros de Momentum RSI (Com respiro 48/52)
            if rsi_val is not None:
                if rsi_val >= self.rsi.overbought or rsi_val <= self.rsi.oversold:
                    logger.warning(f"⚠️ [EXAUSTÃO RSI] Mercado esticado em extremo ({rsi_val:.2f}). Abortando {direcao}.")
                    return None
                
                if direcao == "CALL" and rsi_val < 48.0:
                    return None
                if direcao == "PUT" and rsi_val > 52.0:
                    return None

            return (direcao, estrategia)

        # ------------------------------------------------------------------
        # CAPTURA DOS SINAIS INDIVIDUAIS
        # ------------------------------------------------------------------

        sinal_just = self.classifier.justiceiro.process_data(ohlc)
        sinal_just = sinal_just if sinal_just != "WAIT" else None

        sinal_jw = None
        if not is_30s_candle:
            self.just_win.add_candle(ohlc['open'], ohlc['close'])
            sinal_jw = self.just_win.check_signal()

        sinal_fibo = None
        if macro_dir:
            fibo_trend = "ALTA" if macro_dir == "UP" else "BAIXA"
            if not is_30s_candle:
                self.fibonacci.update_levels(self._candle_history, fibo_trend)
            sinal_fibo = self.fibonacci.check_signal(price)

        # ------------------------------------------------------------------
        # SISTEMA DE CONFLUÊNCIA MATRICIAL (O Segredo para voltar a vencer)
        # ------------------------------------------------------------------
        
        # CASO 1: Confluência Máxima (Fibo + Justiceiro ou Fibo + JustWin) -> ALTA ASSERTIVIDADE
        if sinal_fibo:
            if sinal_fibo == sinal_just:
                logger.info(f"💎 [CONFLUÊNCIA DE OURO] Fibo + Justiceiro apontam {sinal_fibo}.")
                return filtrar_sinal_final(sinal_fibo, "FIBO_JUSTICEIRO_CONF")
            if sinal_fibo == sinal_jw:
                logger.info(f"💎 [CONFLUÊNCIA DE MOMENTUM] Fibo + JustWin apontam {sinal_fibo}.")
                return filtrar_sinal_final(sinal_fibo, "FIBO_JUSTWIN_CONF")

        # CASO 2: Sinais de Quadrante Blitz (30s) combinados com a estrutura de Fibo
        if is_30s_candle:
            self.quadrante_blitz.add_candle(ohlc, timestamp)
            sinal_quadrante = self.quadrante_blitz.get_signal(timestamp, macro_dir)
            if sinal_quadrante and sinal_fibo and sinal_fibo == sinal_quadrante:
                logger.info(f"💎 [CONFLUÊNCIA RAPIDA] Fibo + Quadrante apontam {sinal_quadrante}.")
                return filtrar_sinal_final(sinal_quadrante, "FIBO_QUADRANTE")

        # CASO 3: Filtro Protetivo para Sinais Isolados (Apenas se o segundo for perfeito de abertura)
        if segundo_atual <= 3:
            if sinal_just:
                return filtrar_sinal_final(sinal_just, "JUSTICEIRO_ISOLADO")
            # JustWin Isolado foi REMOVIDO para evitar loss de exaustão em OTC. 
            # Ele agora só serve como confluência forte no CASO 1.

        # Se sobrou apenas sinal isolado de Fibo
        if sinal_fibo:
            return filtrar_sinal_final(sinal_fibo, "FIBONACCI")

        return None

    def registrar_resultado(self, resultado: str, pnl: float = 0.0, trade_id: Any = None, estrategia: str = "unknown"):
        """Registra resultado e persiste de forma assíncrona no JSON raiz."""
        with self._lock:
            trade_removido = False
            if self.trades_ativos:
                if trade_id and trade_id in self.trades_ativos:
                    self.trades_ativos.remove(trade_id)
                    trade_removido = True
                else:
                    self.trades_ativos.pop(0)
                    trade_removido = True

            if not trade_removido:
                logger.warning("[RESULT] Resultado sem trade ativo correspondente. Ignorado.")
                return

            logger.info(f"📊 Resultado: {resultado} (estratégia {estrategia})")
            self.trades_count += 1
            if resultado.lower() == 'win':
                self.manager.registrar_resultado("WIN")
                self._cooldown_until = time.time() + self.COOLDOWN_PADRAO
            elif resultado.lower() == 'loss':
                self.manager.registrar_resultado("LOSS")
                if self.manager.losses_seguidas >= 2:
                    self._cooldown_until = time.time() + self.COOLDOWN_ANTI_TILT
                else:
                    self._cooldown_until = time.time() + self.COOLDOWN_LOSS_SIMPLES
            else:
                self._cooldown_until = time.time() + self.COOLDOWN_PADRAO

            # 📦 DOSSIÊ DO TRADE PARA MINERAÇÃO DE DADOS
            dados_trade = {
                "trade_id": trade_id or f"T_{int(time.time())}",
                "data_hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "estrategia_gatilho": estrategia,
                "direcao": self._trade_direction,
                "resultado": resultado.upper(),
                "lucro_pnl": round(pnl, 2),
                "dados_grafico": {
                    "preco_entrada_robo": self._trade_entry_price,
                    "preco_fechamento_corretora": preco_fechamento,
                    "diferenca_pontos": round(preco_fechamento - self._trade_entry_price, 6)
                },
                "motivo_decisao": getattr(self, '_last_trade_context', {}),
                "estado_sessao": {
                    "placar": f"{self.manager.wins}W - {self.manager.losses}L",
                    "loss_seguidas": self.manager.losses_seguidas
                }
            }

            # Persistência assíncrona
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(salvar_trade_json_raiz(dados_trade))
            except RuntimeError:
                asyncio.run(salvar_trade_json_raiz(dados_trade))
            logger.info(f"💾 Dossiê do trade '{resultado}' salvo com sucesso para análise.")

    def processar_dados(self, data: Dict, is_30s_candle: bool = False) -> Optional[str]:
        """Processa um candle e retorna direção se houver sinal composto válido."""
        if not self.autopilot_ativo:
            self.warmup_count = 0
            return None

        self.warmup_count += 1
        if self.warmup_count <= self.warmup_limit:
            if self.warmup_count % 2 == 0:
                logger.info(f"⏳ Aquecendo: {self.warmup_count}/{self.warmup_limit} candles...")
            return None

        # Valida dados
        required = ['open', 'high', 'low', 'close']
        if not all(k in data for k in required):
            return None
        ohlc = {k: data[k] for k in required}
        ohlc['current'] = data.get('price', data.get('close'))
        timestamp = data.get('timestamp', time.time())

        # 🔒 TRINCO POR ID DE VELA (Candle Lock) – verifica se já operou nesta vela
        if self.ultima_vela_operada == timestamp:
            logger.info(f"🔒 [TRINCO] Sinal abortado: Já operou na vela {timestamp}.")
            return None

        # Histórico para Fibonacci
        self._candle_history.append(ohlc)

        # Alimenta a macro tendência (importante para o filtro de tendência e Fibo)
        if not is_30s_candle:
            self.macro_tendencia.add_candle(timestamp, ohlc['high'], ohlc['low'], ohlc['open'], ohlc['close'])

        sinal = self._check_composite_signal(ohlc, timestamp, is_30s_candle)
        if sinal:
            direcao, estrategia, contexto = sinal
            # 👈 Grava a taxa exata que o robô leu na hora de enviar o clique
            self._trade_entry_price = contexto.get("preco_captura", 0.0) 
            return self.executar_disparo(direcao, estrategia, timestamp_vela=timestamp, contexto=contexto)
        
        return None

    def processar_ws(self, payload: str):
        """Processa mensagens WebSocket (candle-generated e order-closed)."""
        try:
            data = json.loads(payload)
            with self._lock:
                if self._ws_connected_at is None:
                    self.marcar_conexao_ws()

                if data.get("name") == "candle-generated":
                    msg = data.get("msg", {})
                    if msg.get("active_id") != self.target_active_id:
                        return
                    intervalo = msg.get("interval", "M1")
                    is_30s = (intervalo == "M30")
                    telemetria = {
                        "open": msg.get("open"),
                        "high": msg.get("max"),
                        "low": msg.get("min"),
                        "close": msg.get("close"),
                        "price": msg.get("close"),
                        "timestamp": msg.get("timestamp", time.time())
                    }
                    sinal = self.processar_dados(telemetria, is_30s_candle=is_30s)
                    if sinal and self.broker_ops:
                        logger.info(f"[WS] Executando ordem {sinal} via BrokerOperator")
                        res = self.broker_ops.executar_ordem(sinal)
                        if res and res.get("ok") and res.get("status") == "ENQUEUED":
                            trade_id = time.time()
                            self.trades_ativos.append(trade_id)
                            logger.info(f"🚀 Ordem enfileirada. Trade ID: {trade_id}")

                elif data.get("name") == "order-closed":
                    msg_payload = data.get("msg", {})
                    lucro = msg_payload.get("profit", 0)
                    # Busca o preço de fechamento (as chaves comuns são close_price ou value)
                    preco_fechamento = msg_payload.get("close_price", msg_payload.get("value", 0.0))
                    
                    resultado = "win" if lucro > 0 else "loss"
                    self.registrar_resultado(resultado, pnl=lucro, estrategia=self._last_trade_strategy, preco_fechamento=preco_fechamento)

        except Exception as e:
            logger.error(f"[WS] Erro: {e} | Payload: {payload[:200]}")

    def _watchdog_loop(self):
        while True:
            time.sleep(5)
            self.monitorar_estrategia(0.0)

    def monitorar_estrategia(self, preco_atual: float):
        with self._lock:
            if self.trades_count >= self.max_trades_session:
                if not self.is_trading:
                    logger.info(f"🏁 [LIMITE] Máximo de {self.max_trades_session} trades atingido.")
                return
            agora = time.time()
            timeout = getattr(self, 'tempo_expiracao', 60) + 15
            for tid in list(self.trades_ativos):
                if (agora - tid) > timeout:
                    logger.warning(f"⚠️ Timeout do trade {tid}. Forçando reset.")
                    self.registrar_resultado("unknown", trade_id=tid, estrategia=self._last_trade_strategy)

    def get_status(self) -> Dict:
        with self._lock:
            agora = time.time()
            cooldown = max(0, int(self._cooldown_until - agora))
            sups, ress = self.classifier.justiceiro.get_current_levels()
            macro_dir = self.macro_tendencia.get_trend_direction()
            
            # Obtém o valor atual do RSI (se disponível, senão "WARMUP")
            # O último valor calculado está no buffer interno da engine; recuperamos pelo último preço conhecido
            # Como não temos um getter direto, podemos acessar internamente ou calcular sob demanda.
            # Para evitar complexidade, usamos o último preço conhecido para simular um add_price? Melhor: a engine já tem o último RSI?
            # Implementamos um getter simples: se o avg_gain não for None, calculamos com o último preço? Isso é frágil.
            # Uma abordagem mais limpa: armazenar o último rsi calculado como atributo.
            # Vamos modificar o RSIEngine para manter um atributo `current_rsi`.
            # Contudo, para não quebrar a integridade, farei um pequeno ajuste: adicionar um atributo na classe RSIEngine e atualizar no add_price.
            # Como isso é uma refatoração autorizada, incluo essa melhoria.
            # (O código abaixo assume que o RSIEngine agora possui self.current_rsi)
            # Se não existir, retorna "CALCULANDO".
            rsi_value = getattr(self.rsi, 'current_rsi', None)
            if rsi_value is None:
                rsi_display = "WARMUP"
            else:
                rsi_display = f"{rsi_value:.2f}"
            
            return {
                "status": "ACTIVE" if self._ws_connected_at else "IDLE",
                "is_trading": self.is_trading,
                "trades_ativos_count": len(self.trades_ativos),
                "cooldown_restante_s": cooldown,
                "loss_seguidas": self.manager.losses_seguidas,
                "placar": f"{self.manager.wins}W - {self.manager.losses}L",
                "warmup": self._is_warmup(),
                "trades_count": self.trades_count,
                "max_trades": self.max_trades_session,
                "suportes_ativos": sups,
                "resistencias_ativas": ress,
                "fibo_levels": self.fibonacci.levels,
                "macro_tendencia": macro_dir,
                "macro_warmup": self.macro_tendencia.is_warming_up(agora),
                "rsi_atual": rsi_display      # 👈 EXPOSIÇÃO DO RSI NO PAINEL
            }

    def attach(self, page):
        self._active_page = page

    def perceive_and_act(self) -> Dict:
        return {"cycle_id": "0", "state": "IDLE", "recommended_action": "WAIT"}

    def get_balance(self):
        return None

    def request_stop(self):
        with self._lock:
            self._stop_requested = True

    def process_trade_result(self):
        return "UNKNOWN", 0.0

# Instância global
alpha_engine = AlphaEngine(tolerance=0.0002, warmup_limit=10, max_trades_session=999999)